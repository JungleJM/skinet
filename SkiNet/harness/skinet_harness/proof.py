from __future__ import annotations

import platform
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .models import CommandEvidence, ProofEvidence, ProofRunnerProbeEvidence, utc_now
from .preview import classify_preview_url


SANDBOX_FAILURE_PATTERNS = (
    "listen EPERM",
    "operation not permitted 127.0.0.1",
    "MachPortRendezvousServer",
    "bootstrap_check_in",
    "Permission denied (1100)",
    "browserType.launch",
)


@dataclass(frozen=True)
class ProofCommand:
    label: str
    command: str


@dataclass(frozen=True)
class RunProofRequest:
    run_id: str
    repo: Path
    preview_url: str | None
    safe_command: ProofCommand
    elevated_command: ProofCommand | None = None
    allow_elevated: bool = False


@dataclass(frozen=True)
class ProbeProofRunnerRequest:
    run_id: str
    repo: Path
    preview_url: str | None
    probe_command: ProofCommand


def classify_failure(stdout: str, stderr: str) -> str:
    combined = f"{stdout}\n{stderr}"
    if any(pattern in combined for pattern in SANDBOX_FAILURE_PATTERNS):
        return "proof_runner_sandbox_blocked"
    return "proof_failed"


def render_command(command: str, repo: Path, preview_url: str | None) -> str:
    return command.format(
        repo=shlex.quote(str(repo)),
        preview_url=shlex.quote(preview_url or ""),
    )


def execute_command(proof_command: ProofCommand, repo: Path, preview_url: str | None) -> CommandEvidence:
    command = render_command(proof_command.command, repo, preview_url)
    started_at = utc_now()
    completed = subprocess.run(
        command,
        cwd=repo,
        shell=True,
        text=True,
        capture_output=True,
        check=False,
    )
    completed_at = utc_now()
    failure_category = None
    if completed.returncode != 0:
        failure_category = classify_failure(completed.stdout, completed.stderr)

    return CommandEvidence(
        label=proof_command.label,
        command=command,
        cwd=str(repo),
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        started_at=started_at,
        completed_at=completed_at,
        failure_category=failure_category,
    )


def run_proof(request: RunProofRequest) -> ProofEvidence:
    preview = classify_preview_url(request.preview_url)
    attempts = [execute_command(request.safe_command, request.repo, request.preview_url)]

    if attempts[0].passed:
        return proof_evidence(
            request=request,
            attempts=attempts,
            status="passed",
            recommended_next_action="record_proof_passed",
        )

    safe_failure = attempts[0].failure_category
    may_escalate = (
        safe_failure == "proof_runner_sandbox_blocked"
        and request.allow_elevated
        and request.elevated_command is not None
    )

    if may_escalate:
        attempts.append(execute_command(request.elevated_command, request.repo, request.preview_url))
        return proof_evidence(
            request=request,
            attempts=attempts,
            status="passed" if attempts[-1].passed else "failed",
            recommended_next_action=(
                "record_proof_passed_with_elevated_runner"
                if attempts[-1].passed
                else "create_harness_fix_issue"
            ),
        )

    return proof_evidence(
        request=request,
        attempts=attempts,
        status="failed",
        recommended_next_action=(
            "authorize_elevated_proof_runner"
            if safe_failure == "proof_runner_sandbox_blocked"
            else "route_to_product_or_test_failure"
        ),
    )


def probe_proof_runner(request: ProbeProofRunnerRequest) -> ProofRunnerProbeEvidence:
    attempt = execute_command(request.probe_command, request.repo, request.preview_url)
    sandbox_blocked = attempt.failure_category == "proof_runner_sandbox_blocked"
    status = "passed" if attempt.passed else "failed"
    return ProofRunnerProbeEvidence(
        run_id=request.run_id,
        status=status,
        preview=classify_preview_url(request.preview_url),
        proof_runner={
            "host": platform.node(),
            "os": platform.platform(),
            "probe_label": request.probe_command.label,
        },
        attempt=attempt,
        capabilities={
            "can_run_probe_command": attempt.passed,
            "safe_mode_sandbox_blocked": sandbox_blocked,
            "requires_elevated_sandbox_for_browser": sandbox_blocked,
        },
        recommended_next_action=(
            "use_safe_proof_runner"
            if attempt.passed
            else (
                "authorize_elevated_proof_runner"
                if sandbox_blocked
                else "inspect_probe_failure"
            )
        ),
    )


def proof_evidence(
    request: RunProofRequest,
    attempts: list[CommandEvidence],
    status: str,
    recommended_next_action: str,
) -> ProofEvidence:
    return ProofEvidence(
        run_id=request.run_id,
        status=status,
        preview=classify_preview_url(request.preview_url),
        proof_runner={
            "host": platform.node(),
            "os": platform.platform(),
            "safe_label": request.safe_command.label,
            "elevated_label": request.elevated_command.label if request.elevated_command else None,
            "elevated_allowed": request.allow_elevated,
            "elevated_used": len(attempts) > 1,
        },
        attempts=attempts,
        recommended_next_action=recommended_next_action,
    )

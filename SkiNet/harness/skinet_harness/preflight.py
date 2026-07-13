from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .models import CommandEvidence, PreflightEvidence, utc_now


@dataclass(frozen=True)
class PreflightCommand:
    label: str
    command: str


@dataclass(frozen=True)
class RunPreflightRequest:
    run_id: str
    repo: Path
    commands: list[PreflightCommand]
    stop_on_failure: bool = True


def execute_preflight_command(command: PreflightCommand, repo: Path) -> CommandEvidence:
    started_at = utc_now()
    completed = subprocess.run(
        command.command,
        cwd=repo,
        shell=True,
        text=True,
        capture_output=True,
        check=False,
    )
    completed_at = utc_now()
    return CommandEvidence(
        label=command.label,
        command=command.command,
        cwd=str(repo),
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        started_at=started_at,
        completed_at=completed_at,
        failure_category=None if completed.returncode == 0 else "preflight_command_failed",
    )


def run_preflight(request: RunPreflightRequest) -> PreflightEvidence:
    command_evidence: list[CommandEvidence] = []
    for command in request.commands:
        evidence = execute_preflight_command(command, request.repo)
        command_evidence.append(evidence)
        if request.stop_on_failure and not evidence.passed:
            break

    status = "passed" if command_evidence and all(command.passed for command in command_evidence) else "failed"
    return PreflightEvidence(
        run_id=request.run_id,
        status=status,
        repo=str(request.repo),
        commands=command_evidence,
        recommended_next_action=(
            "record_preflight_passed" if status == "passed" else "route_to_product_test_or_harness_failure"
        ),
    )


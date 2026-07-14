from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .models import CommandEvidence, StartDevEvidence, TddGateEvidence, utc_now


@dataclass(frozen=True)
class TddCommand:
    label: str
    command: str


@dataclass(frozen=True)
class RunTddGateRequest:
    run_id: str
    repo: Path
    commands: list[TddCommand]
    run_dir: Path
    expected_failure_texts: list[str] | None = None
    stop_on_failure: bool = True


@dataclass(frozen=True)
class StartDevRequest:
    run_id: str
    run_dir: Path


def command_signature(commands: list[str]) -> str:
    payload = json.dumps(commands, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def execute_tdd_command(command: TddCommand, repo: Path) -> CommandEvidence:
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
    )


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def run_red_gate(request: RunTddGateRequest) -> TddGateEvidence:
    expected_failure_texts = request.expected_failure_texts or []
    command_evidence: list[CommandEvidence] = []
    saw_failure = False
    failure_category: str | None = None

    for command in request.commands:
        evidence = execute_tdd_command(command, request.repo)
        command_evidence.append(evidence)
        if not evidence.passed:
            saw_failure = True
            if expected_failure_texts:
                combined_output = f"{evidence.stdout}\n{evidence.stderr}"
                if not any(text in combined_output for text in expected_failure_texts):
                    failure_category = "tdd_wrong_failure_reason"
                    break
            if request.stop_on_failure:
                break

    if failure_category is None and not saw_failure:
        failure_category = "tdd_red_not_observed"

    status = "passed" if failure_category is None else "failed"
    return TddGateEvidence(
        run_id=request.run_id,
        gate="red",
        status=status,
        repo=str(request.repo),
        commands=command_evidence,
        command_signature=command_signature([command.command for command in request.commands]),
        expected_failure_texts=expected_failure_texts,
        dependency_paths={},
        failure_category=failure_category,
        recommended_next_action=(
            "allow_start_dev" if status == "passed" else "fix_red_test_or_contract"
        ),
    )


def start_dev(request: StartDevRequest) -> StartDevEvidence:
    red_path = request.run_dir / "gate" / "tdd-red.json"
    red = read_json(red_path)
    if red is None:
        return StartDevEvidence(
            run_id=request.run_id,
            status="failed",
            run_dir=str(request.run_dir),
            red_gate_path=str(red_path),
            red_gate_status="missing",
            failure_category="tdd_red_missing",
            recommended_next_action="run_red_gate_first",
        )
    if red.get("status") != "passed":
        return StartDevEvidence(
            run_id=request.run_id,
            status="failed",
            run_dir=str(request.run_dir),
            red_gate_path=str(red_path),
            red_gate_status=str(red.get("status")),
            failure_category="tdd_red_not_passed",
            recommended_next_action="fix_red_test_or_contract",
        )

    return StartDevEvidence(
        run_id=request.run_id,
        status="passed",
        run_dir=str(request.run_dir),
        red_gate_path=str(red_path),
        red_gate_status="passed",
        failure_category=None,
        recommended_next_action="start_execution_provider_job",
    )


def run_green_gate(request: RunTddGateRequest) -> TddGateEvidence:
    red_path = request.run_dir / "gate" / "tdd-red.json"
    start_dev_path = request.run_dir / "gate" / "start-dev.json"
    red = read_json(red_path)
    start_dev_evidence = read_json(start_dev_path)

    dependency_paths = {
        "red_gate": str(red_path),
        "start_dev": str(start_dev_path),
    }
    requested_signature = command_signature([command.command for command in request.commands])

    if red is None:
        return TddGateEvidence(
            run_id=request.run_id,
            gate="green",
            status="failed",
            repo=str(request.repo),
            commands=[],
            command_signature=requested_signature,
            expected_failure_texts=[],
            dependency_paths=dependency_paths,
            failure_category="tdd_red_missing",
            recommended_next_action="run_red_gate_first",
        )
    if red.get("status") != "passed":
        return TddGateEvidence(
            run_id=request.run_id,
            gate="green",
            status="failed",
            repo=str(request.repo),
            commands=[],
            command_signature=requested_signature,
            expected_failure_texts=[],
            dependency_paths=dependency_paths,
            failure_category="tdd_red_not_passed",
            recommended_next_action="fix_red_test_or_contract",
        )
    if start_dev_evidence is None or start_dev_evidence.get("status") != "passed":
        return TddGateEvidence(
            run_id=request.run_id,
            gate="green",
            status="failed",
            repo=str(request.repo),
            commands=[],
            command_signature=requested_signature,
            expected_failure_texts=[],
            dependency_paths=dependency_paths,
            failure_category="start_dev_not_authorized",
            recommended_next_action="run_start_dev_after_red",
        )
    if red.get("command_signature") != requested_signature:
        return TddGateEvidence(
            run_id=request.run_id,
            gate="green",
            status="failed",
            repo=str(request.repo),
            commands=[],
            command_signature=requested_signature,
            expected_failure_texts=[],
            dependency_paths=dependency_paths,
            failure_category="tdd_command_mismatch",
            recommended_next_action="rerun_green_with_red_command_set",
        )

    command_evidence: list[CommandEvidence] = []
    failure_category: str | None = None
    for command in request.commands:
        evidence = execute_tdd_command(command, request.repo)
        command_evidence.append(evidence)
        if not evidence.passed:
            failure_category = "tdd_green_failed"
            if request.stop_on_failure:
                break

    status = "passed" if failure_category is None and command_evidence else "failed"
    return TddGateEvidence(
        run_id=request.run_id,
        gate="green",
        status=status,
        repo=str(request.repo),
        commands=command_evidence,
        command_signature=requested_signature,
        expected_failure_texts=[],
        dependency_paths=dependency_paths,
        failure_category=failure_category,
        recommended_next_action=(
            "record_green_passed" if status == "passed" else "finish_minimal_implementation"
        ),
    )

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class PreviewRef:
    url: str | None
    kind: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "kind": self.kind,
        }


@dataclass(frozen=True)
class CommandEvidence:
    label: str
    command: str
    cwd: str
    exit_code: int
    stdout: str
    stderr: str
    started_at: str
    completed_at: str
    failure_category: str | None = None

    @property
    def passed(self) -> bool:
        return self.exit_code == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "command": self.command,
            "cwd": self.cwd,
            "exit_code": self.exit_code,
            "passed": self.passed,
            "failure_category": self.failure_category,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass(frozen=True)
class RunMetadata:
    run_id: str
    repo: str
    contract_ref: str | None
    branch: str | None
    commit: str | None
    run_dir: str
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "skinet.run_metadata.v0",
            "run_id": self.run_id,
            "created_at": self.created_at,
            "repo": self.repo,
            "contract_ref": self.contract_ref,
            "implementation_ref": {
                "branch": self.branch,
                "commit": self.commit,
            },
            "run_dir": self.run_dir,
        }


@dataclass(frozen=True)
class PreflightEvidence:
    run_id: str
    status: str
    repo: str
    commands: list[CommandEvidence] = field(default_factory=list)
    artifact_checks: list[dict[str, Any]] = field(default_factory=list)
    recommended_next_action: str | None = None
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "skinet.preflight_evidence.v0",
            "run_id": self.run_id,
            "status": self.status,
            "created_at": self.created_at,
            "repo": self.repo,
            "artifact_checks": self.artifact_checks,
            "commands": [command.to_dict() for command in self.commands],
            "recommended_next_action": self.recommended_next_action,
        }


@dataclass(frozen=True)
class ProofEvidence:
    run_id: str
    status: str
    preview: PreviewRef
    proof_runner: dict[str, Any]
    attempts: list[CommandEvidence] = field(default_factory=list)
    recommended_next_action: str | None = None
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "skinet.proof_evidence.v0",
            "run_id": self.run_id,
            "status": self.status,
            "created_at": self.created_at,
            "preview": self.preview.to_dict(),
            "proof_runner": self.proof_runner,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "recommended_next_action": self.recommended_next_action,
        }


@dataclass(frozen=True)
class ProofRunnerProbeEvidence:
    run_id: str
    status: str
    preview: PreviewRef
    proof_runner: dict[str, Any]
    attempt: CommandEvidence
    capabilities: dict[str, Any]
    recommended_next_action: str
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "skinet.proof_runner_probe.v0",
            "run_id": self.run_id,
            "status": self.status,
            "created_at": self.created_at,
            "preview": self.preview.to_dict(),
            "proof_runner": self.proof_runner,
            "attempt": self.attempt.to_dict(),
            "capabilities": self.capabilities,
            "recommended_next_action": self.recommended_next_action,
        }


@dataclass(frozen=True)
class TddGateEvidence:
    run_id: str
    gate: str
    status: str
    repo: str
    commands: list[CommandEvidence] = field(default_factory=list)
    command_signature: str = ""
    expected_failure_texts: list[str] = field(default_factory=list)
    dependency_paths: dict[str, str] = field(default_factory=dict)
    failure_category: str | None = None
    recommended_next_action: str | None = None
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "skinet.tdd_gate_evidence.v0",
            "run_id": self.run_id,
            "gate": self.gate,
            "status": self.status,
            "created_at": self.created_at,
            "repo": self.repo,
            "command_signature": self.command_signature,
            "expected_failure_texts": self.expected_failure_texts,
            "dependency_paths": self.dependency_paths,
            "failure_category": self.failure_category,
            "commands": [command.to_dict() for command in self.commands],
            "recommended_next_action": self.recommended_next_action,
        }


@dataclass(frozen=True)
class StartDevEvidence:
    run_id: str
    status: str
    run_dir: str
    red_gate_path: str
    red_gate_status: str
    failure_category: str | None = None
    recommended_next_action: str | None = None
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "skinet.start_dev_evidence.v0",
            "run_id": self.run_id,
            "status": self.status,
            "created_at": self.created_at,
            "run_dir": self.run_dir,
            "red_gate_path": self.red_gate_path,
            "red_gate_status": self.red_gate_status,
            "failure_category": self.failure_category,
            "recommended_next_action": self.recommended_next_action,
        }


@dataclass(frozen=True)
class EvidenceBundle:
    run_id: str
    status: str
    contract_ref: str | None
    run_metadata: dict[str, Any] | None
    implementation_ref: dict[str, Any]
    artifacts: dict[str, Any]
    recommended_next_action: str
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "skinet.evidence_bundle.v0",
            "run_id": self.run_id,
            "status": self.status,
            "created_at": self.created_at,
            "contract_ref": self.contract_ref,
            "run_metadata": self.run_metadata,
            "implementation_ref": self.implementation_ref,
            "artifacts": self.artifacts,
            "recommended_next_action": self.recommended_next_action,
        }

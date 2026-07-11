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
class EvidenceBundle:
    run_id: str
    status: str
    contract_ref: str | None
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
            "implementation_ref": self.implementation_ref,
            "artifacts": self.artifacts,
            "recommended_next_action": self.recommended_next_action,
        }

from __future__ import annotations

import json
from pathlib import Path

from .models import EvidenceBundle


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_first_json(paths: list[Path]) -> tuple[dict | None, Path]:
    for path in paths:
        content = read_json(path)
        if content is not None:
            return content, path
    return None, paths[0]


def build_evidence_bundle(
    run_id: str,
    evidence_dir: Path,
    contract_ref: str | None,
    branch: str | None,
    commit: str | None,
) -> EvidenceBundle:
    metadata_path = evidence_dir / "run.json"
    preflight, preflight_path = read_first_json(
        [
            evidence_dir / "gate" / "preflight.json",
            evidence_dir / "preflight.json",
        ]
    )
    probe, probe_path = read_first_json(
        [
            evidence_dir / "proof" / "proof-runner-probe.json",
            evidence_dir / "proof-runner-probe.json",
        ]
    )
    proof, proof_path = read_first_json(
        [
            evidence_dir / "proof" / "proof.json",
            evidence_dir / "proof.json",
        ]
    )
    metadata = read_json(metadata_path)

    statuses = [
        artifact.get("status")
        for artifact in (preflight, probe, proof)
        if artifact is not None and artifact.get("status")
    ]
    if not statuses:
        status = "incomplete"
    elif any(value == "failed" for value in statuses):
        status = "failed"
    elif all(value == "passed" for value in statuses):
        status = "passed"
    else:
        status = "incomplete"

    if preflight and preflight.get("status") == "failed" and preflight.get("recommended_next_action"):
        recommended_next_action = preflight["recommended_next_action"]
    elif proof and proof.get("status") == "failed" and proof.get("recommended_next_action"):
        recommended_next_action = proof["recommended_next_action"]
    elif proof and proof.get("recommended_next_action"):
        recommended_next_action = proof["recommended_next_action"]
    elif preflight and preflight.get("recommended_next_action"):
        recommended_next_action = preflight["recommended_next_action"]
    elif probe and probe.get("recommended_next_action"):
        recommended_next_action = probe["recommended_next_action"]
    else:
        recommended_next_action = "collect_missing_evidence"

    return EvidenceBundle(
        run_id=run_id,
        status=status,
        contract_ref=contract_ref or (metadata.get("contract_ref") if metadata else None),
        run_metadata=metadata,
        implementation_ref={
            "branch": branch
            or (
                metadata.get("implementation_ref", {}).get("branch")
                if metadata
                else None
            ),
            "commit": commit
            or (
                metadata.get("implementation_ref", {}).get("commit")
                if metadata
                else None
            ),
        },
        artifacts={
            "run_metadata": {
                "path": str(metadata_path),
                "status": "present" if metadata else "missing",
            },
            "preflight": {
                "path": str(preflight_path),
                "status": preflight.get("status") if preflight else "missing",
            },
            "proof_runner_probe": {
                "path": str(probe_path),
                "status": probe.get("status") if probe else "missing",
            },
            "proof": {
                "path": str(proof_path),
                "status": proof.get("status") if proof else "missing",
            },
        },
        recommended_next_action=recommended_next_action,
    )

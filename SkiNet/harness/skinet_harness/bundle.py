from __future__ import annotations

import json
from pathlib import Path

from .models import EvidenceBundle


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_evidence_bundle(
    run_id: str,
    evidence_dir: Path,
    contract_ref: str | None,
    branch: str | None,
    commit: str | None,
) -> EvidenceBundle:
    probe_path = evidence_dir / "proof-runner-probe.json"
    proof_path = evidence_dir / "proof.json"
    probe = read_json(probe_path)
    proof = read_json(proof_path)

    statuses = [
        artifact.get("status")
        for artifact in (probe, proof)
        if artifact is not None and artifact.get("status")
    ]
    status = "passed" if statuses and all(value == "passed" for value in statuses) else "incomplete"

    if proof and proof.get("recommended_next_action"):
        recommended_next_action = proof["recommended_next_action"]
    elif probe and probe.get("recommended_next_action"):
        recommended_next_action = probe["recommended_next_action"]
    else:
        recommended_next_action = "collect_missing_evidence"

    return EvidenceBundle(
        run_id=run_id,
        status=status,
        contract_ref=contract_ref,
        implementation_ref={
            "branch": branch,
            "commit": commit,
        },
        artifacts={
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

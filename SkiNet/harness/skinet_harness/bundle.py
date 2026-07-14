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
    tdd_red, tdd_red_path = read_first_json(
        [
            evidence_dir / "gate" / "tdd-red.json",
            evidence_dir / "tdd-red.json",
        ]
    )
    start_dev, start_dev_path = read_first_json(
        [
            evidence_dir / "gate" / "start-dev.json",
            evidence_dir / "start-dev.json",
        ]
    )
    tdd_green, tdd_green_path = read_first_json(
        [
            evidence_dir / "gate" / "tdd-green.json",
            evidence_dir / "tdd-green.json",
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

    chronology_invalid = False
    if tdd_green is not None:
        if tdd_red is None or tdd_red.get("status") != "passed":
            chronology_invalid = True
        elif start_dev is None or start_dev.get("status") != "passed":
            chronology_invalid = True
        elif tdd_green.get("command_signature") != tdd_red.get("command_signature"):
            chronology_invalid = True

    statuses = [
        artifact.get("status")
        for artifact in (tdd_red, start_dev, tdd_green, preflight, probe, proof)
        if artifact is not None and artifact.get("status")
    ]
    if chronology_invalid:
        status = "failed"
    elif not statuses:
        status = "incomplete"
    elif any(value == "failed" for value in statuses):
        status = "failed"
    elif all(value == "passed" for value in statuses):
        status = "passed"
    else:
        status = "incomplete"

    if chronology_invalid:
        recommended_next_action = "route_to_tdd_chronology_failure"
    elif tdd_green and tdd_green.get("status") == "failed" and tdd_green.get("recommended_next_action"):
        recommended_next_action = tdd_green["recommended_next_action"]
    elif start_dev and start_dev.get("status") == "failed" and start_dev.get("recommended_next_action"):
        recommended_next_action = start_dev["recommended_next_action"]
    elif tdd_red and tdd_red.get("status") == "failed" and tdd_red.get("recommended_next_action"):
        recommended_next_action = tdd_red["recommended_next_action"]
    elif preflight and preflight.get("status") == "failed" and preflight.get("recommended_next_action"):
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
            "tdd_red": {
                "path": str(tdd_red_path),
                "status": tdd_red.get("status") if tdd_red else "missing",
            },
            "start_dev": {
                "path": str(start_dev_path),
                "status": start_dev.get("status") if start_dev else "missing",
            },
            "tdd_green": {
                "path": str(tdd_green_path),
                "status": tdd_green.get("status") if tdd_green else "missing",
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

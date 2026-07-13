from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .evidence import write_evidence
from .models import RunMetadata


DEFAULT_RUN_ROOT = Path("SkiNet/runs")


@dataclass(frozen=True)
class InitRunRequest:
    run_id: str
    repo: Path
    run_root: Path = DEFAULT_RUN_ROOT
    contract_ref: str | None = None
    branch: str | None = None
    commit: str | None = None


def run_dir(run_root: Path, run_id: str) -> Path:
    return run_root / run_id


def default_evidence_dir(run_root: Path, run_id: str, evidence_kind: str) -> Path:
    if evidence_kind == "proof":
        return run_dir(run_root, run_id) / "proof"
    if evidence_kind == "gate":
        return run_dir(run_root, run_id) / "gate"
    return run_dir(run_root, run_id)


def init_run(request: InitRunRequest) -> RunMetadata:
    directory = run_dir(request.run_root, request.run_id)
    metadata = RunMetadata(
        run_id=request.run_id,
        repo=str(request.repo),
        contract_ref=request.contract_ref,
        branch=request.branch,
        commit=request.commit,
        run_dir=str(directory),
    )
    write_evidence(metadata, directory / "run.json")
    (directory / "gate").mkdir(parents=True, exist_ok=True)
    (directory / "proof").mkdir(parents=True, exist_ok=True)
    return metadata


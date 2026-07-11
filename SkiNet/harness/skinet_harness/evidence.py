from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol


class JsonEvidence(Protocol):
    def to_dict(self) -> dict:
        raise NotImplementedError


def write_evidence(evidence: JsonEvidence, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(evidence.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

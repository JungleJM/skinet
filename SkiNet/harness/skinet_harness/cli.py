from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bundle import build_evidence_bundle
from .evidence import write_evidence
from .proof import (
    ProbeProofRunnerRequest,
    ProofCommand,
    RunProofRequest,
    probe_proof_runner,
    run_proof,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harnessctl")
    subcommands = parser.add_subparsers(dest="command", required=True)

    run_proof_parser = subcommands.add_parser(
        "run-proof",
        help="Run a proof command with safe-mode first and optional elevated retry.",
    )
    run_proof_parser.add_argument("--run-id", required=True)
    run_proof_parser.add_argument("--repo", required=True)
    run_proof_parser.add_argument("--safe-command", required=True)
    run_proof_parser.add_argument("--safe-label", default="safe")
    run_proof_parser.add_argument("--preview-url")
    run_proof_parser.add_argument("--elevated-command")
    run_proof_parser.add_argument("--elevated-label", default="elevated")
    run_proof_parser.add_argument("--allow-elevated", action="store_true")
    run_proof_parser.add_argument("--out")
    run_proof_parser.add_argument("--evidence-dir")

    probe_parser = subcommands.add_parser(
        "probe-proof-runner",
        help="Probe whether the safe proof runner can execute browser proof on this host.",
    )
    probe_parser.add_argument("--run-id", required=True)
    probe_parser.add_argument("--repo", required=True)
    probe_parser.add_argument("--probe-command", required=True)
    probe_parser.add_argument("--probe-label", default="safe-probe")
    probe_parser.add_argument("--preview-url")
    probe_parser.add_argument("--out")
    probe_parser.add_argument("--evidence-dir")

    bundle_parser = subcommands.add_parser(
        "bundle-evidence",
        help="Create a run-level evidence bundle from collected evidence files.",
    )
    bundle_parser.add_argument("--run-id", required=True)
    bundle_parser.add_argument("--evidence-dir", required=True)
    bundle_parser.add_argument("--contract-ref")
    bundle_parser.add_argument("--branch")
    bundle_parser.add_argument("--commit")
    bundle_parser.add_argument("--out")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run-proof":
        request = RunProofRequest(
            run_id=args.run_id,
            repo=Path(args.repo),
            preview_url=args.preview_url,
            safe_command=ProofCommand(label=args.safe_label, command=args.safe_command),
            elevated_command=(
                ProofCommand(label=args.elevated_label, command=args.elevated_command)
                if args.elevated_command
                else None
            ),
            allow_elevated=args.allow_elevated,
        )
        evidence = run_proof(request)
        emit_evidence(evidence, args.out, args.evidence_dir, "proof.json")
        return 0 if evidence.status == "passed" else 1

    if args.command == "probe-proof-runner":
        request = ProbeProofRunnerRequest(
            run_id=args.run_id,
            repo=Path(args.repo),
            preview_url=args.preview_url,
            probe_command=ProofCommand(label=args.probe_label, command=args.probe_command),
        )
        evidence = probe_proof_runner(request)
        emit_evidence(evidence, args.out, args.evidence_dir, "proof-runner-probe.json")
        return 0 if evidence.status == "passed" else 1

    if args.command == "bundle-evidence":
        evidence = build_evidence_bundle(
            run_id=args.run_id,
            evidence_dir=Path(args.evidence_dir),
            contract_ref=args.contract_ref,
            branch=args.branch,
            commit=args.commit,
        )
        emit_evidence(evidence, args.out, args.evidence_dir, "evidence-bundle.json")
        return 0 if evidence.status == "passed" else 1

    parser.error(f"unknown command: {args.command}")
    return 2


def emit_evidence(evidence, out: str | None, evidence_dir: str | None, filename: str) -> None:
    output = json.dumps(evidence.to_dict(), indent=2, sort_keys=True)
    if out:
        write_evidence(evidence, Path(out))
    elif evidence_dir:
        write_evidence(evidence, Path(evidence_dir) / filename)
    else:
        print(output)

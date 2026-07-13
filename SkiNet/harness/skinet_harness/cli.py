from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bundle import build_evidence_bundle
from .evidence import write_evidence
from .preflight import PreflightCommand, RunPreflightRequest, run_preflight
from .proof import (
    ProbeProofRunnerRequest,
    ProofCommand,
    RunProofRequest,
    probe_proof_runner,
    run_proof,
)
from .runs import DEFAULT_RUN_ROOT, InitRunRequest, default_evidence_dir, init_run, run_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harnessctl")
    subcommands = parser.add_subparsers(dest="command", required=True)

    init_parser = subcommands.add_parser(
        "init-run",
        help="Create a durable controller run directory and run metadata.",
    )
    init_parser.add_argument("--run-id", required=True)
    init_parser.add_argument("--repo", required=True)
    init_parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    init_parser.add_argument("--contract-ref")
    init_parser.add_argument("--branch")
    init_parser.add_argument("--commit")
    init_parser.add_argument("--out")

    preflight_parser = subcommands.add_parser(
        "run-preflight",
        help="Run deterministic preflight commands and record structured evidence.",
    )
    preflight_parser.add_argument("--run-id", required=True)
    preflight_parser.add_argument("--repo", required=True)
    preflight_parser.add_argument("--command", action="append", dest="commands", required=True)
    preflight_parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    preflight_parser.add_argument("--keep-going", action="store_true")
    preflight_parser.add_argument("--out")
    preflight_parser.add_argument("--evidence-dir")

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
    run_proof_parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
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
    probe_parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    probe_parser.add_argument("--out")
    probe_parser.add_argument("--evidence-dir")

    bundle_parser = subcommands.add_parser(
        "bundle-evidence",
        help="Create a run-level evidence bundle from collected evidence files.",
    )
    bundle_parser.add_argument("--run-id", required=True)
    bundle_parser.add_argument("--evidence-dir")
    bundle_parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    bundle_parser.add_argument("--contract-ref")
    bundle_parser.add_argument("--branch")
    bundle_parser.add_argument("--commit")
    bundle_parser.add_argument("--out")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-run":
        evidence = init_run(
            InitRunRequest(
                run_id=args.run_id,
                repo=Path(args.repo),
                run_root=Path(args.run_root),
                contract_ref=args.contract_ref,
                branch=args.branch,
                commit=args.commit,
            )
        )
        emit_evidence(evidence, args.out, None, "run.json")
        return 0

    if args.command == "run-preflight":
        commands = [
            PreflightCommand(label=f"command-{index}", command=command)
            for index, command in enumerate(args.commands, start=1)
        ]
        evidence = run_preflight(
            RunPreflightRequest(
                run_id=args.run_id,
                repo=Path(args.repo),
                commands=commands,
                stop_on_failure=not args.keep_going,
            )
        )
        emit_evidence(
            evidence,
            args.out,
            resolve_evidence_dir(args.evidence_dir, args.run_root, args.run_id, "gate"),
            "preflight.json",
        )
        return 0 if evidence.status == "passed" else 1

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
        emit_evidence(
            evidence,
            args.out,
            resolve_evidence_dir(args.evidence_dir, args.run_root, args.run_id, "proof"),
            "proof.json",
        )
        return 0 if evidence.status == "passed" else 1

    if args.command == "probe-proof-runner":
        request = ProbeProofRunnerRequest(
            run_id=args.run_id,
            repo=Path(args.repo),
            preview_url=args.preview_url,
            probe_command=ProofCommand(label=args.probe_label, command=args.probe_command),
        )
        evidence = probe_proof_runner(request)
        emit_evidence(
            evidence,
            args.out,
            resolve_evidence_dir(args.evidence_dir, args.run_root, args.run_id, "proof"),
            "proof-runner-probe.json",
        )
        return 0 if evidence.status == "passed" else 1

    if args.command == "bundle-evidence":
        evidence_dir = Path(args.evidence_dir) if args.evidence_dir else run_dir(Path(args.run_root), args.run_id)
        evidence = build_evidence_bundle(
            run_id=args.run_id,
            evidence_dir=evidence_dir,
            contract_ref=args.contract_ref,
            branch=args.branch,
            commit=args.commit,
        )
        emit_evidence(evidence, args.out, str(evidence_dir), "evidence-bundle.json")
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


def resolve_evidence_dir(
    evidence_dir: str | None,
    run_root: str,
    run_id: str,
    evidence_kind: str,
) -> str:
    if evidence_dir:
        return evidence_dir
    return str(default_evidence_dir(Path(run_root), run_id, evidence_kind))

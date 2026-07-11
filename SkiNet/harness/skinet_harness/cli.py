from __future__ import annotations

import argparse
import json
from pathlib import Path

from .proof import ProofCommand, RunProofRequest, run_proof


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
        output = json.dumps(evidence.to_dict(), indent=2, sort_keys=True)
        if args.out:
            Path(args.out).write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
        return 0 if evidence.status == "passed" else 1

    parser.error(f"unknown command: {args.command}")
    return 2

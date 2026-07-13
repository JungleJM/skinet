from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skinet_harness.bundle import build_evidence_bundle
from skinet_harness.cli import main
from skinet_harness.evidence import write_evidence
from skinet_harness.preflight import PreflightCommand, RunPreflightRequest, run_preflight
from skinet_harness.preview import classify_preview_url
from skinet_harness.proof import (
    ProbeProofRunnerRequest,
    ProofCommand,
    RunProofRequest,
    classify_failure,
    probe_proof_runner,
    run_proof,
)
from skinet_harness.runs import InitRunRequest, init_run, run_dir


class PreviewClassificationTest(unittest.TestCase):
    def test_classifies_localhost(self) -> None:
        self.assertEqual(classify_preview_url("http://127.0.0.1:5173").kind, "localhost")

    def test_classifies_tailnet(self) -> None:
        self.assertEqual(classify_preview_url("http://100.114.175.52:5173").kind, "tailnet")
        self.assertEqual(classify_preview_url("https://app.tail90eacc.ts.net").kind, "tailnet")


class FailureClassificationTest(unittest.TestCase):
    def test_classifies_chromium_mach_port_failure_as_sandbox_blocked(self) -> None:
        stderr = "bootstrap_check_in org.chromium.Chromium.MachPortRendezvousServer Permission denied (1100)"
        self.assertEqual(classify_failure("", stderr), "proof_runner_sandbox_blocked")

    def test_classifies_listener_eperm_as_sandbox_blocked(self) -> None:
        self.assertEqual(classify_failure("listen EPERM 127.0.0.1:5173", ""), "proof_runner_sandbox_blocked")

    def test_unmatched_failure_is_plain_proof_failure(self) -> None:
        self.assertEqual(classify_failure("expected heading not found", ""), "proof_failed")


class RunProofTest(unittest.TestCase):
    def test_safe_success_does_not_use_elevated_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence = run_proof(
                RunProofRequest(
                    run_id="run-1",
                    repo=Path(tmp),
                    preview_url="http://127.0.0.1:5173",
                    safe_command=ProofCommand("safe", "true"),
                    elevated_command=ProofCommand("elevated", "false"),
                    allow_elevated=True,
                )
            )

        self.assertEqual(evidence.status, "passed")
        self.assertEqual(len(evidence.attempts), 1)
        self.assertFalse(evidence.proof_runner["elevated_used"])

    def test_sandbox_failure_escalates_when_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence = run_proof(
                RunProofRequest(
                    run_id="run-2",
                    repo=Path(tmp),
                    preview_url="http://127.0.0.1:5173",
                    safe_command=ProofCommand(
                        "safe",
                        "printf 'listen EPERM 127.0.0.1:5173' && exit 1",
                    ),
                    elevated_command=ProofCommand("elevated", "true"),
                    allow_elevated=True,
                )
            )

        self.assertEqual(evidence.status, "passed")
        self.assertEqual(len(evidence.attempts), 2)
        self.assertTrue(evidence.proof_runner["elevated_used"])
        self.assertEqual(evidence.recommended_next_action, "record_proof_passed_with_elevated_runner")

    def test_product_failure_does_not_escalate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence = run_proof(
                RunProofRequest(
                    run_id="run-3",
                    repo=Path(tmp),
                    preview_url=None,
                    safe_command=ProofCommand("safe", "printf 'assertion failed' && exit 1"),
                    elevated_command=ProofCommand("elevated", "true"),
                    allow_elevated=True,
                )
            )

        self.assertEqual(evidence.status, "failed")
        self.assertEqual(len(evidence.attempts), 1)
        self.assertEqual(evidence.recommended_next_action, "route_to_product_or_test_failure")


class ProbeProofRunnerTest(unittest.TestCase):
    def test_probe_success_recommends_safe_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence = probe_proof_runner(
                ProbeProofRunnerRequest(
                    run_id="probe-1",
                    repo=Path(tmp),
                    preview_url="http://127.0.0.1:5173",
                    probe_command=ProofCommand("safe-probe", "true"),
                )
            )

        self.assertEqual(evidence.status, "passed")
        self.assertTrue(evidence.capabilities["can_run_probe_command"])
        self.assertFalse(evidence.capabilities["requires_elevated_sandbox_for_browser"])
        self.assertEqual(evidence.recommended_next_action, "use_safe_proof_runner")

    def test_probe_sandbox_failure_recommends_elevated_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence = probe_proof_runner(
                ProbeProofRunnerRequest(
                    run_id="probe-2",
                    repo=Path(tmp),
                    preview_url=None,
                    probe_command=ProofCommand(
                        "safe-probe",
                        "printf 'MachPortRendezvousServer Permission denied (1100)' && exit 1",
                    ),
                )
            )

        self.assertEqual(evidence.status, "failed")
        self.assertTrue(evidence.capabilities["safe_mode_sandbox_blocked"])
        self.assertTrue(evidence.capabilities["requires_elevated_sandbox_for_browser"])
        self.assertEqual(evidence.recommended_next_action, "authorize_elevated_proof_runner")


class EvidenceBundleTest(unittest.TestCase):
    def test_bundle_passes_when_probe_and_proof_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence_dir = Path(tmp)
            probe = probe_proof_runner(
                ProbeProofRunnerRequest(
                    run_id="bundle-1",
                    repo=evidence_dir,
                    preview_url=None,
                    probe_command=ProofCommand("safe-probe", "true"),
                )
            )
            proof = run_proof(
                RunProofRequest(
                    run_id="bundle-1",
                    repo=evidence_dir,
                    preview_url=None,
                    safe_command=ProofCommand("safe", "true"),
                )
            )
            write_evidence(probe, evidence_dir / "proof-runner-probe.json")
            write_evidence(proof, evidence_dir / "proof.json")

            bundle = build_evidence_bundle(
                run_id="bundle-1",
                evidence_dir=evidence_dir,
                contract_ref="docs/agent-issues/ISSUE-1.v1.md",
                branch="agent/issue-1",
                commit="abc123",
            )

        self.assertEqual(bundle.status, "passed")
        self.assertEqual(bundle.contract_ref, "docs/agent-issues/ISSUE-1.v1.md")
        self.assertEqual(bundle.implementation_ref["branch"], "agent/issue-1")
        self.assertEqual(bundle.artifacts["proof"]["status"], "passed")

    def test_bundle_is_incomplete_when_evidence_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = build_evidence_bundle(
                run_id="bundle-2",
                evidence_dir=Path(tmp),
                contract_ref=None,
                branch=None,
                commit=None,
            )

        self.assertEqual(bundle.status, "incomplete")
        self.assertEqual(bundle.artifacts["proof"]["status"], "missing")
        self.assertEqual(bundle.recommended_next_action, "collect_missing_evidence")


class RunLedgerTest(unittest.TestCase):
    def test_init_run_writes_metadata_and_evidence_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            metadata = init_run(
                InitRunRequest(
                    run_id="issue-1-attempt-001",
                    repo=Path(tmp),
                    run_root=root,
                    contract_ref="docs/agent-issues/ISSUE-1.v1.md",
                    branch="agent/issue-1",
                    commit="abc123",
                )
            )
            directory = run_dir(root, "issue-1-attempt-001")

            self.assertEqual(metadata.run_dir, str(directory))
            self.assertTrue((directory / "run.json").exists())
            self.assertTrue((directory / "gate").is_dir())
            self.assertTrue((directory / "proof").is_dir())


class PreflightTest(unittest.TestCase):
    def test_preflight_passes_when_all_commands_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence = run_preflight(
                RunPreflightRequest(
                    run_id="preflight-1",
                    repo=Path(tmp),
                    commands=[
                        PreflightCommand("one", "true"),
                        PreflightCommand("two", "printf ok"),
                    ],
                )
            )

        self.assertEqual(evidence.status, "passed")
        self.assertEqual(len(evidence.commands), 2)
        self.assertEqual(evidence.recommended_next_action, "record_preflight_passed")

    def test_preflight_stops_on_first_failure_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence = run_preflight(
                RunPreflightRequest(
                    run_id="preflight-2",
                    repo=Path(tmp),
                    commands=[
                        PreflightCommand("fail", "printf bad && exit 1"),
                        PreflightCommand("skip", "true"),
                    ],
                )
            )

        self.assertEqual(evidence.status, "failed")
        self.assertEqual(len(evidence.commands), 1)
        self.assertEqual(evidence.commands[0].failure_category, "preflight_command_failed")
        self.assertEqual(evidence.recommended_next_action, "route_to_product_test_or_harness_failure")

    def test_preflight_can_keep_going_after_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence = run_preflight(
                RunPreflightRequest(
                    run_id="preflight-3",
                    repo=Path(tmp),
                    commands=[
                        PreflightCommand("fail", "false"),
                        PreflightCommand("pass", "true"),
                    ],
                    stop_on_failure=False,
                )
            )

        self.assertEqual(evidence.status, "failed")
        self.assertEqual(len(evidence.commands), 2)
        self.assertFalse(evidence.commands[0].passed)
        self.assertTrue(evidence.commands[1].passed)

    def test_cli_run_preflight_accepts_repeated_command_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            exit_code = main(
                [
                    "run-preflight",
                    "--run-id",
                    "cli-preflight",
                    "--repo",
                    tmp,
                    "--run-root",
                    str(root),
                    "--command",
                    "true",
                    "--command",
                    "printf ok",
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue((root / "cli-preflight" / "gate" / "preflight.json").exists())


class EvidenceBundleWithPreflightTest(unittest.TestCase):
    def test_bundle_reads_run_directory_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            run_id = "bundle-run-1"
            metadata = init_run(
                InitRunRequest(
                    run_id=run_id,
                    repo=Path(tmp),
                    run_root=root,
                    contract_ref="docs/agent-issues/ISSUE-1.v1.md",
                    branch="agent/issue-1",
                    commit="abc123",
                )
            )
            directory = Path(metadata.run_dir)
            preflight = run_preflight(
                RunPreflightRequest(
                    run_id=run_id,
                    repo=Path(tmp),
                    commands=[PreflightCommand("one", "true")],
                )
            )
            proof = run_proof(
                RunProofRequest(
                    run_id=run_id,
                    repo=Path(tmp),
                    preview_url=None,
                    safe_command=ProofCommand("safe", "true"),
                )
            )
            write_evidence(preflight, directory / "gate" / "preflight.json")
            write_evidence(proof, directory / "proof" / "proof.json")

            bundle = build_evidence_bundle(
                run_id=run_id,
                evidence_dir=directory,
                contract_ref=None,
                branch=None,
                commit=None,
            )

        self.assertEqual(bundle.status, "passed")
        self.assertEqual(bundle.contract_ref, "docs/agent-issues/ISSUE-1.v1.md")
        self.assertEqual(bundle.artifacts["run_metadata"]["status"], "present")
        self.assertEqual(bundle.artifacts["preflight"]["status"], "passed")
        self.assertEqual(bundle.artifacts["proof"]["status"], "passed")

    def test_bundle_fails_when_preflight_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            run_id = "bundle-run-2"
            metadata = init_run(
                InitRunRequest(
                    run_id=run_id,
                    repo=Path(tmp),
                    run_root=root,
                )
            )
            directory = Path(metadata.run_dir)
            preflight = run_preflight(
                RunPreflightRequest(
                    run_id=run_id,
                    repo=Path(tmp),
                    commands=[PreflightCommand("fail", "false")],
                )
            )
            write_evidence(preflight, directory / "gate" / "preflight.json")

            bundle = build_evidence_bundle(
                run_id=run_id,
                evidence_dir=directory,
                contract_ref=None,
                branch=None,
                commit=None,
            )

        self.assertEqual(bundle.status, "failed")
        self.assertEqual(bundle.artifacts["preflight"]["status"], "failed")
        self.assertEqual(bundle.recommended_next_action, "route_to_product_test_or_harness_failure")


if __name__ == "__main__":
    unittest.main()

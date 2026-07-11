from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skinet_harness.preview import classify_preview_url
from skinet_harness.proof import (
    ProofCommand,
    RunProofRequest,
    classify_failure,
    run_proof,
)


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


if __name__ == "__main__":
    unittest.main()

# SkiNet Harness Controller Spike

This directory contains the first production-oriented controller slice for SkiNet.

Current scope:

- record typed proof evidence;
- classify preview URLs without hard-coding Tailscale;
- probe proof-runner capability before deciding whether elevated mode is needed;
- run browser proof in safe mode first;
- retry with an explicitly authorized elevated proof runner only when the safe-mode failure matches a known sandbox/browser/runtime signature.

This is intentionally small and dependency-free while the controller domain model settles.

Example:

```bash
python3 SkiNet/harness/harnessctl.py probe-proof-runner \
  --run-id issue-2-attempt-001 \
  --repo /Users/jmath/Documents/code/skinet-test-tracer \
  --probe-command 'npm run test:e2e' \
  --evidence-dir /tmp/issue-2-attempt-001

python3 SkiNet/harness/harnessctl.py run-proof \
  --run-id issue-2-attempt-001 \
  --repo /Users/jmath/Documents/code/skinet-test-tracer \
  --preview-url http://100.114.175.52:5173 \
  --safe-command 'E2E_BASE_URL={preview_url} npm run test:e2e' \
  --elevated-command 'codex exec --cd {repo} --sandbox danger-full-access "E2E_BASE_URL={preview_url} npm run test:e2e"' \
  --allow-elevated \
  --evidence-dir /tmp/issue-2-attempt-001

python3 SkiNet/harness/harnessctl.py bundle-evidence \
  --run-id issue-2-attempt-001 \
  --evidence-dir /tmp/issue-2-attempt-001 \
  --contract-ref docs/agent-issues/ISSUE-2.v1.md \
  --branch agent/issue-2-fixture-board-shell \
  --commit HEAD
```

If the safe command passes, elevated mode is not used.
If the safe command fails for an unclassified product/test reason, elevated mode is not used.
If the safe command fails with a known sandbox/browser/listener signature and `--allow-elevated` is set, the elevated command is tried once and both attempts are recorded.

Evidence files:

- `proof-runner-probe.json`
- `proof.json`
- `evidence-bundle.json`

# SkiNet Next Steps

Intent: build the controller in small testable milestones. Each milestone should leave a usable CLI state, not only design notes.

## Milestone 1: Run Ledger + Preflight Gate

- Status: built
- Goal: make `harnessctl` produce durable run state and deterministic preflight evidence.
- Add controller-owned run directories.
- Add run metadata file.
- Add `run-preflight`.
- Run required commands in order.
- Record each command:
  - command
  - cwd
  - exit code
  - stdout/stderr
  - timestamps
  - failure category when known
- Stop/fail clearly on command failure.
- Extend `bundle-evidence` to include preflight.
- Keep existing proof probe/proof behavior working.
- Test against `skinet-test-tracer`.
- No Tenet job start yet.
- No Gitea write adapter yet.

Done when:

- A run has a durable directory.
- Preflight evidence is written there.
- Bundle can summarize preflight + proof evidence.
- Unit tests cover pass/fail/missing evidence.
- You can run the milestone manually against the practice repo.

### Manual Test: Success Path

Run from this repo:

```bash
cd /Users/jmath/Documents/code/skinet

PYTHONPATH=SkiNet/harness python3 SkiNet/harness/harnessctl.py init-run \
  --run-id issue-2-attempt-m1 \
  --repo /Users/jmath/Documents/code/skinet-test-tracer \
  --contract-ref docs/agent-issues/ISSUE-2.v1.md \
  --branch agent/issue-2-fixture-board-shell

PYTHONPATH=SkiNet/harness python3 SkiNet/harness/harnessctl.py run-preflight \
  --run-id issue-2-attempt-m1 \
  --repo /Users/jmath/Documents/code/skinet-test-tracer \
  --command 'npm run build' \
  --command 'npm test' \
  --command 'npm run test:e2e'

PYTHONPATH=SkiNet/harness python3 SkiNet/harness/harnessctl.py run-proof \
  --run-id issue-2-attempt-m1 \
  --repo /Users/jmath/Documents/code/skinet-test-tracer \
  --safe-command 'npm run test:e2e'

PYTHONPATH=SkiNet/harness python3 SkiNet/harness/harnessctl.py bundle-evidence \
  --run-id issue-2-attempt-m1
```

Success conditions:

- Each command exits `0`.
- These files exist:
  - `SkiNet/runs/issue-2-attempt-m1/run.json`
  - `SkiNet/runs/issue-2-attempt-m1/gate/preflight.json`
  - `SkiNet/runs/issue-2-attempt-m1/proof/proof.json`
  - `SkiNet/runs/issue-2-attempt-m1/evidence-bundle.json`
- `preflight.json` has `"status": "passed"`.
- `proof.json` has `"status": "passed"`.
- `evidence-bundle.json` has `"status": "passed"`.
- `evidence-bundle.json` lists the contract ref and branch from `run.json`.

### Manual Test: Preflight Failure Path

Run:

```bash
cd /Users/jmath/Documents/code/skinet

PYTHONPATH=SkiNet/harness python3 SkiNet/harness/harnessctl.py init-run \
  --run-id issue-2-attempt-m1-fail \
  --repo /Users/jmath/Documents/code/skinet-test-tracer \
  --contract-ref docs/agent-issues/ISSUE-2.v1.md \
  --branch agent/issue-2-fixture-board-shell

PYTHONPATH=SkiNet/harness python3 SkiNet/harness/harnessctl.py run-preflight \
  --run-id issue-2-attempt-m1-fail \
  --repo /Users/jmath/Documents/code/skinet-test-tracer \
  --command 'npm run build' \
  --command 'false' \
  --command 'npm test'
```

Expected failure conditions:

- `run-preflight` exits non-zero.
- `SkiNet/runs/issue-2-attempt-m1-fail/gate/preflight.json` exists.
- `preflight.json` has `"status": "failed"`.
- The failed command has `"failure_category": "preflight_command_failed"`.
- The third command was not run, because preflight stops on first failure by default.
- Recommended next action is `route_to_product_test_or_harness_failure`.

### Manual Test: Keep-Going Failure Path

Run:

```bash
cd /Users/jmath/Documents/code/skinet

PYTHONPATH=SkiNet/harness python3 SkiNet/harness/harnessctl.py run-preflight \
  --run-id issue-2-attempt-m1-fail \
  --repo /Users/jmath/Documents/code/skinet-test-tracer \
  --keep-going \
  --command 'false' \
  --command 'npm test'
```

Expected failure conditions:

- Command exits non-zero.
- `preflight.json` has `"status": "failed"`.
- Both commands are recorded.
- First command failed.
- Second command ran.

### Developer Test

Run:

```bash
cd /Users/jmath/Documents/code/skinet
PYTHONPATH=SkiNet/harness python3 -m unittest discover -s SkiNet/harness/tests -v
```

Success condition:

- All harness tests pass.

## Milestone 2: Tenet Shim Artifact Generation

- Status: planned
- Goal: prepare Tenet-compatible files from one frozen tracer without starting Tenet.
- Generate:
  - `spec.md`
  - `scenarios.md`
  - `harness.md`
  - `decomposition.md`
- Ensure `decomposition.md` is one-node only.
- Treat these as compatibility shims, not canonical truth.
- Validate exact paths.
- Validate forbidden paths and required commands are present.

Done when:

- One frozen agent issue can produce a complete `.tenet/runs/<run>/` shim set.
- Controller can reject stale/missing/invalid artifact inputs.

## Milestone 3: Tenet Execution Adapter

- Status: planned
- Goal: make Tenet the first `ExecutionProvider`.
- Register exactly one Tenet dev job.
- Start the job.
- Collect job result/log refs as evidence.
- Keep Tenet from re-planning or creating a multi-job feature DAG.
- Keep Tenet internal retries subordinate to controller retry budget.

Done when:

- One frozen tracer can be handed to Tenet through controller-owned artifacts.
- Result evidence is collected without changing authority-provider state directly.

## Milestone 4: Gitea Authority Adapter

- Status: planned
- Goal: make private Gitea the first `AuthorityProvider`.
- Read feature/tracer issues.
- Normalize labels, issue body fields, dependencies, PR refs, and comments.
- Write status labels and audit comments through controller-approved transitions.
- Keep controller policy provider-neutral.

Done when:

- Controller can inspect/select eligible Gitea tracer issues.
- State updates are visible in Gitea.
- Local files and adapter logs are not treated as canonical state.

## Milestone 5: PR + Merge Policy

- Status: planned
- Goal: close the loop from passed evidence to PR and safe feature-branch merge.
- Create PR only after required gates/critics pass.
- Target feature branch only.
- Include evidence links in PR body.
- Auto-merge only low-risk eligible PRs into feature branch.
- Never auto-merge to main.
- Unblock dependents only after confirmed feature-branch merge.

Done when:

- A successful tracer can become a Gitea PR with full evidence.
- Low-risk approved tracer can merge to feature branch by policy.
- Risky/manual-review work stops at `awaiting_human_review`.

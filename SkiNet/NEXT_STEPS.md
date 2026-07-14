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

## Priority Feature: TDD RED/GREEN Gates

- Status: next
- Goal: enforce TDD chronology before any execution provider writes implementation code.
- Add `run-red-gate`.
- Add `run-green-gate`.
- Write `gate/tdd-red.json`.
- Write `gate/tdd-green.json`.
- Refuse `start-dev` unless RED passed for the current snapshot.
- Treat missing, post-hoc, or wrong-failure RED evidence as `tdd_chronology_gap`.
- Require GREEN to run against the same focused tracer command/proof set as RED.
- Bundle RED/GREEN evidence into `evidence-bundle.json`.
- Prove the behavior against `skinet-test-tracer` before implementing broader Tenet execution.

Done when:

- A tracer can prove expected RED failure before implementation.
- The controller blocks development when RED is missing or invalid.
- The same tracer can prove GREEN success after implementation.
- Unit tests cover RED pass/fail, wrong-failure RED, missing RED before start, and mismatched GREEN.
- The trial repo rerun has committed artifacts showing RED before dev, GREEN after dev, and preflight/proof evidence.

### Trial Rerun Plan

- Repo: `/Users/jmath/Documents/code/skinet-test-tracer`
- Remote: `ssh://git@appliedsci.tail90eacc.ts.net:411/gitea_admin/skinet-test-tracer.git`
- Shared PRD input: `docs/prd/vikunja-kanban-viewer.md`
- Archived prior attempt:
  - `docs/prior-attempts/issue-2-attempt-001/agent-issues/ISSUE-2.v1.md`
  - `docs/prior-attempts/issue-2-attempt-001/tenet/run/`
  - `docs/prior-attempts/issue-2-attempt-001/tenet/project/`
  - `docs/prior-attempts/issue-2-attempt-001/tenet/status/`

Rerun strategy:

- Start from the same PRD, not from the previous implementation.
- Prefer re-generating tracer bullets from `docs/prd/vikunja-kanban-viewer.md` so the harness proves the planning-to-development path.
- Build the new tracer split using the `to-tickets` vertical-slice rules as the primary rubric:
  - each slice must cut a narrow but complete path through every relevant layer;
  - each slice must be demoable or verifiable on its own;
  - each slice must fit in a single fresh context window;
  - any prefactoring must be sequenced first rather than hidden inside the slice.
- Use the archived `ISSUE-2.v1.md` only as secondary comparison evidence: did the new tracer split preserve the old fixture-backed board shell boundary, acceptance criteria, proof requirements, and non-goals where that older split was already sensible?
- If tracer generation is not ready, fall back to reusing the archived tracer contract as the frozen input and prove only tracer-to-development automation.
- In either path, require `run-red-gate` before any implementation change and `run-green-gate` after implementation.

Proof to produce:

- A blocked `start-dev` attempt when `gate/tdd-red.json` is missing.
- `gate/tdd-red.json` showing expected behavior failure before implementation.
- Development artifacts or diff created only after RED passes.
- `gate/tdd-green.json` showing the same focused contract passes after implementation.
- `gate/preflight.json`, proof JSON, and `evidence-bundle.json` showing the final deterministic evidence.
- A short rubric review of the new slice against the `to-tickets` vertical-slice rules.
- A short comparison against `docs/prior-attempts/issue-2-attempt-001/agent-issues/ISSUE-2.v1.md` explaining where the new split agrees with, improves on, or intentionally diverges from the older tracer.

## Milestone 2: Tenet Shim Artifact Generation

- Status: planned
- Goal: prepare Tenet-compatible files from one frozen tracer without starting Tenet.
- Generate:
  - `spec.md`
  - `scenarios.md`
  - `harness.md`
  - `decomposition.md`
  - `gate/tdd-red-plan.md`
- Ensure `decomposition.md` is one-node only.
- Treat these as compatibility shims, not canonical truth.
- Validate exact paths.
- Validate forbidden paths and required commands are present.
- Validate that the RED plan maps to the tracer acceptance criteria and proof expectations.

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

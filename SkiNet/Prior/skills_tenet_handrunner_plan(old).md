# Skills + Tenet Runner/Harness Build Plan

## Purpose

This document defines a gradual build-out of a development harness over:

- **Skills** for idea interrogation, PRD creation, tracer-bullet issue decomposition, and later respec workflows.
- **Tenet** for agent execution and evaluation.
- **Gitea** as the canonical source of truth.
- **A repo-local runner/wrapper** for work selection, dependency analysis, policy checks, preflight, proof, status updates, PR creation, and feature-branch auto-merge.
- **Codex/Claude first**, with local LLMs introduced only after the workflow itself is reliable.

The main goal is to avoid building a fragile multi-agent system too early. Each stage adds one layer of complexity only after the prior layer works manually.

**Tenet compatibility revision:** this version explicitly separates Skills/Gitea speccing from Tenet execution so the harness remains compatible with Tenet's artifact/job model without allowing Tenet's own interview/spec/decomposition phases to create a second source of truth. The runner will generate Tenet-compatible shim artifacts from the frozen agent issue, then register a one-job Tenet dev DAG with exact artifact paths.

---

## Core Architecture

### Source-of-truth rule

Do **not** let truth migrate from PRD to Markdown to PR to Tenet run artifacts.

Instead:

```text
Gitea issue = canonical intent and state
docs/agent-issues/ISSUE-N.vX.md = frozen execution snapshot for one attempt/spec version
.tenet/runs/<run>/ = implementation attempt and evidence
Gitea PR = proposed code merge
feature branch = auto-merge target after gates pass
main = human-only merge target
```

### Artifact roles

| Artifact | Role | Authority |
|---|---|---|
| Gitea epic / PRD issue | Feature-level context and intent | Canonical planning context |
| Gitea tracer issue | One vertical slice to build | Canonical implementation intent |
| `docs/agent-issues/ISSUE-N.vX.md` | Frozen execution contract generated from Gitea | Authority for one Tenet attempt |
| `.tenet/runs/<run>/spec.md` | Tenet-compatible export of the frozen agent issue | Compatibility shim, not canonical truth |
| `.tenet/runs/<run>/scenarios.md` | Acceptance criteria, anti-scenarios, proof expectations | Compatibility shim, not canonical truth |
| `.tenet/runs/<run>/harness.md` | Required commands, forbidden paths, gates, merge policy | Compatibility shim, not canonical truth |
| `.tenet/runs/<run>/decomposition.md` | One-node Tenet DAG for the current tracer | Compatibility shim, not cross-issue planning |
| `.tenet/runs/<run>/` | Run logs, proof, preflight, critic results | Evidence only |
| Gitea PR | Proposed code change | Merge vehicle |
| `docs/features/<feature>.md` | Completed feature summary | Historical summary |

### Default merge policy

- Auto-merge is allowed only into a **feature branch**.
- Merge to `main` is always manual.
- Risky issues can pass Tenet but still require human feature-branch merge.
- Dependent issues remain blocked until their blockers are actually merged into the feature branch.

### Ownership boundary

This is the most important Tenet compatibility rule.

```text
Skills = interview, PRD creation, tracer decomposition, respec
Gitea = canonical planning state and cross-issue dependency graph
agent-issue snapshot = frozen execution contract for one attempt
Tenet = execute one frozen contract and evaluate the result
Runner = create Tenet-compatible shim artifacts, call Tenet primitives, gate, PR, update Gitea
```

Once a Skills-generated Gitea tracer issue exists, **do not invoke Tenet through its normal interview/spec/decomposition skill flow** for that work. Tenet should not re-interview, re-spec, or re-decompose a feature that Skills/Gitea already decomposed.

For this harness, Tenet's internal job DAG should be deliberately trivial:

```text
one Gitea tracer issue = one frozen agent-issue snapshot = one Tenet registered dev job
```

Gitea owns all cross-issue dependency logic through `blocked_by` and `blocks`. Tenet owns only the execution/evaluation state for the single current attempt.

---

## Canonical Issue State Model

Use these issue states in Gitea labels for mutable status. Static fields such as `blocked_by`, proof requirements, forbidden paths, and acceptance criteria can live in issue body sections or generated snapshots, but the frequently changing status should be a native Gitea label to avoid fragile issue-body rewrites.

```yaml
agent_status:
  - ready
  - running
  - passed_preflight
  - failed_retryable
  - blocked
  - needs_respec
  - awaiting_human_review
  - budget_exceeded
  - passed_critics
  - pr_created
  - merged_feature
  - superseded
  - abandoned
```

### State flow

```text
ready
  ↓
running
  ↓
passed_preflight
  ↓
passed_critics
  ↓
pr_created
  ↓
merged_feature
```

### Failure states

```text
failed_retryable
needs_respec
blocked
awaiting_human_review
budget_exceeded
superseded
abandoned
```

Do not use a separate `needs_human` state. Use `awaiting_human_review` everywhere.

A failed implementation does not replace the issue. It creates a failed attempt under `.tenet/runs`.

Example:

```text
Gitea Issue #123 = canonical tracer
  ├── docs/agent-issues/ISSUE-123.v1.md
  ├── .tenet/runs/issue-123-attempt-001 = failed run
  ├── .tenet/runs/issue-123-attempt-002 = failed run
  └── .tenet/runs/issue-123-attempt-003 = passed run → PR → merge to feature
```

---

## Standard Agent-Issue YAML

Every generated `docs/agent-issues/ISSUE-N.vX.md` should start with strict frontmatter.

```yaml
canonical_issue: gitea://gitea.local/owner/repo/issues/123
parent_prd: gitea://gitea.local/owner/repo/issues/100

status: ready
authority: execution_contract
snapshot_version: 1

feature: login
feature_branch: feature/login
agent_branch: agent/issue-123-login-form
run_slug: issue-123-attempt-001
run_path: .tenet/runs/issue-123-attempt-001

model_tier: codex_first
risk_level: low

auto_merge_to_feature: true
manual_review_required: false

runner_retry_budget: 2
tenet_internal_max_retries: 0
tenet_invocation_mode: direct_registered_job

tenet_artifact_paths:
  spec: .tenet/runs/issue-123-attempt-001/spec.md
  scenarios: .tenet/runs/issue-123-attempt-001/scenarios.md
  harness: .tenet/runs/issue-123-attempt-001/harness.md
  decomposition: .tenet/runs/issue-123-attempt-001/decomposition.md
  interview: null

blocked_by:
  - 121
blocks:
  - 124
  - 125

proof_required: true
proof_type: playwright
e2e_surface: web_ui
playwright_layer1_required: true
playwright_layer2_required: true

forbidden_paths:
  - .env
  - infra/prod/**
  - migrations/**
  - secrets/**

required_commands:
  - pnpm lint
  - pnpm typecheck
  - pnpm test
  - npx playwright test
```

### Authority rule for agents

Include this in every agent-facing work order:

```text
If the parent PRD conflicts with the current tracer issue, obey the tracer issue.
If the tracer issue conflicts with .tenet/project architecture/testing doctrine, stop and report a scope conflict.
If generated run artifacts conflict with the canonical issue, obey the canonical issue and regenerate artifacts.
The PRD is planning context. The tracer issue and agent-issue snapshot are implementation authority.
```

---

## Tenet Compatibility Contract

This section exists specifically to make the harness compatible with Tenet's spec/artifact/job system while preventing Tenet from becoming a second planner.

### Rule: bypass Tenet's planning phases after Skills decomposition

After Skills creates the PRD and Gitea tracer issues, do not use Tenet's normal feature-planning flow for implementation work. In practical terms:

- Do not ask Tenet to interview the idea again.
- Do not ask Tenet to generate a second feature spec.
- Do not ask Tenet to decompose the feature into its own multi-job DAG.
- Do not use Tenet Full/Standard/Quick modes as the implementation path once a frozen Skills/Gitea tracer exists.

Instead, use Tenet's lower-level job primitives directly:

```text
tenet_register_jobs
  → one dev job
  → depends_on: []
  → exact artifact_paths
tenet_start_job
tenet_job_result
manual or runner preflight/proof
tenet_start_eval
```

### Tenet-compatible shim artifacts

Tenet workers and critics need artifact paths. To satisfy that design without letting Tenet rewrite the plan, the runner creates shim artifacts from the frozen agent issue.

```text
.tenet/runs/issue-123-attempt-001/
  spec.md
  scenarios.md
  harness.md
  decomposition.md
  journal/
  proof/
  gate/
```

Mapping:

```text
spec.md
  Generated from docs/agent-issues/ISSUE-123.v1.md.
  Contains the current tracer issue, relevant PRD context, and authority rules.

scenarios.md
  Contains acceptance criteria, anti-scenarios, proof expectations, and examples.

harness.md
  Contains required commands, forbidden paths, testing doctrine, merge policy, and budget rules.

decomposition.md
  Contains a one-node Tenet DAG for this tracer only.
  It must not include sibling Gitea issues or cross-issue dependency planning.
```

### One-job DAG example

```yaml
jobs:
  - id: issue-123
    name: Implement Gitea issue 123
    type: dev
    depends_on: []
    artifact_paths:
      spec: .tenet/runs/issue-123-attempt-001/spec.md
      scenarios: .tenet/runs/issue-123-attempt-001/scenarios.md
      harness: .tenet/runs/issue-123-attempt-001/harness.md
      decomposition: .tenet/runs/issue-123-attempt-001/decomposition.md
      interview: null
```

### Retry ownership

Tenet may have its own internal retry mechanism. The harness should not let Tenet retries and runner retries compound.

Default policy:

```yaml
tenet_internal_max_retries: 0
runner_retry_budget: 2
```

You can later raise `tenet_internal_max_retries` to `1`, but the runner's retry budget should remain the meaningful product decision-maker.

---

## Failure Categories and Routing

Tenet critics should produce structured finding categories where possible. The runner should route deterministic facts itself and use a dedicated classifier or triage skill for ambiguous semantic failures.

| Failure category | Primary source | Meaning | Runner action |
|---|---|---|---|
| `product_bug` | Tenet critic or failure classifier | Implementation does not match the spec | Retry same issue with critic findings included |
| `test_bug` | Tenet critic or failure classifier | Test asserts wrong behavior or misses intent | Mark `needs_respec` or create test-fix issue |
| `harness_bug` | Preflight/proof/critic/classifier | Build/test/proof infrastructure is broken | Mark `blocked`; create harness-fix issue |
| `evidence_mismatch` | Preflight/proof/critic/classifier | Report claims success but fresh evidence disagrees | Retry proof/preflight once; repeated failure → `awaiting_human_review` |
| `contention` | Failure classifier | Parallel/sibling jobs likely interfered | Retry later after conflicting work settles |
| `scope_conflict` | Tenet critic or failure classifier | Job changed out-of-scope files or violated doctrine | Stop; mark `needs_respec` or `awaiting_human_review` |
| `forbidden_path_changed` | Preflight script | Preflight found restricted file changes | Stop; mark `awaiting_human_review` |
| `missing_proof` | Proof script | Required proof artifact missing | Retry if likely forgotten; otherwise `needs_respec` |
| `dependency_blocked` | Runner dependency graph | Required predecessor not merged | Do not run; keep `blocked` |
| `budget_exceeded` | Runner budget gate | Retry/time/cost budget exceeded | Stop; mark `budget_exceeded` and require human review |

### Failure classification rule

Do not assume Tenet's raw critic text will naturally map into the full taxonomy. Deterministic categories should be assigned by scripts. Ambiguous categories should be assigned by either:

1. a dedicated failure-classifier prompt immediately after critic failure, or
2. the Stage 18 `triage-tenet-failure` Skill.

Until that classifier exists, use a smaller manual taxonomy: `product_bug`, `test_bug`, `harness_bug`, `scope_conflict`, and `awaiting_human_review`.

---

## Dependency Blocking Example

Suppose:

```yaml
Issue 123:
  title: Add auth schema
  auto_merge_to_feature: false
  manual_review_required: true
  blocks:
    - 124
    - 125

Issue 124:
  title: Add login API
  blocked_by:
    - 123

Issue 125:
  title: Add login UI
  blocked_by:
    - 123
```

If Issue 123 passes Tenet but requires manual review:

```text
Issue 123: passed_critics → pr_created → awaiting_human_review
Issue 124: remains blocked
Issue 125: remains blocked
```

The runner must not start Issues 124 or 125 until Issue 123 is manually merged into `feature/login`.

After human merge:

```text
Issue 123: merged_feature
Issue 124: ready
Issue 125: ready
```

This prevents later tracer bullets from being built on unreviewed risky work.

---

# Sequential Build Plan

## Stage 1 — Install and test Skills and Tenet separately

### Goal

Confirm both tools work independently before combining them.

### Additions

None. This is a baseline setup stage.

### What changes from previous stage

Nothing yet. No runner. No Gitea automation. No auto-merge. No local LLMs.

### Steps

1. Install Skills.
2. Install Tenet.
3. Run a simple Skills command in a toy repo.
4. Run a simple Tenet dev/eval flow in a toy repo.
5. Verify Tenet can run with Codex or Claude.
6. Confirm Tenet can see the project and create run artifacts.
7. Confirm Skills can generate useful PRD/issue-style output.

### Exit criteria

- Skills can generate useful planning artifacts.
- Tenet can run a basic development job.
- Tenet can run its evaluation critics.
- You know where Tenet stores run/job outputs.

---

## Stage 2 — Run Skills on a small project idea

### Goal

Use Skills to turn a real but small idea into a PRD and tracer-bullet breakdown.

### Additions

- First real PRD draft.
- First real tracer bullet list.

### What changes from Stage 1

Skills is now used on an actual feature idea, not just a toy test.

### Steps

1. Discuss the feature with Codex/Claude.
2. Use Skills to interrogate the idea.
3. Generate a PRD.
4. Use Skills to decompose the PRD into vertical tracer bullets.
5. Keep the feature intentionally small.

### Output

```text
docs/prd/<feature>.md
```

or a Gitea epic issue if you are ready to use Gitea immediately.

### Exit criteria

- One PRD exists.
- Two to five tracer bullets are identified.
- Each tracer is narrow, demoable, and independently testable.

---

## Stage 3 — Create one Gitea epic and two or three tracer issues

### Goal

Make Gitea the canonical source of truth early.

### Additions

- Gitea epic / PRD issue.
- Gitea tracer issues.
- Basic dependency links.

### What changes from Stage 2

The PRD/tracers stop being only local planning text. They become canonical Gitea issues.

### Steps

1. Create one Gitea epic issue for the feature.
2. Create two or three Gitea tracer issues.
3. Link each tracer to the epic.
4. Add blocker relationships manually if Gitea supports them.
5. If native blocker relationships are unavailable, use body sections:

```markdown
## Parent

gitea://gitea.local/owner/repo/issues/100

## Blocked by

- gitea://gitea.local/owner/repo/issues/121
```

### Exit criteria

- Gitea contains the canonical feature epic.
- Gitea contains canonical tracer issues.
- Dependencies are visible to a human.

---

## Stage 4 — Manually create one `docs/agent-issues/ISSUE-N.v1.md`

### Goal

Create the first frozen execution snapshot by hand.

### Additions

- `docs/agent-issues/`
- One agent-issue Markdown file.
- Strict YAML frontmatter.

### What changes from Stage 3

Gitea still owns truth, but Tenet will receive a frozen local execution contract.

### Steps

1. Pick one unblocked tracer issue.
2. Create:

```text
docs/agent-issues/ISSUE-123.v1.md
```

3. Copy the Gitea issue intent into the file.
4. Add YAML fields for:
   - canonical issue
   - feature branch
   - agent branch
   - blocked_by / blocks
   - proof requirements
   - required commands
   - auto-merge policy
   - forbidden paths

### Exit criteria

- One agent-issue file exists.
- It is clear that Gitea is canonical and the file is a snapshot.
- A human could hand this file to Tenet/Codex and know what to build.

---

## Stage 5 — Run one Tenet dev job with Codex or Claude

### Goal

Prove Tenet can implement one frozen tracer snapshot **without using Tenet's own interview/spec/decomposition path**.

This stage is where the plan is modified for compatibility with Tenet's spec/artifact system. Tenet still receives `spec`, `scenarios`, `harness`, and `decomposition` artifacts, but those files are generated from the Skills/Gitea agent issue. They are compatibility shims, not a second canonical spec.

### Additions

- First Tenet dev job against an agent-issue file.
- First `.tenet/runs/<run>/` attempt for a real tracer.
- First Tenet-compatible shim artifact set:
  - `spec.md`
  - `scenarios.md`
  - `harness.md`
  - `decomposition.md`
- One-job Tenet DAG.

### What changes from Stage 4

Tenet is now used for implementation, but everything around it is still manual. The important difference is that Tenet is invoked through direct job registration, not through its feature-planning skill flow.

### Non-negotiable rule

Do not run Tenet in a way that lets it re-interview, re-spec, or re-decompose the feature after Skills/Gitea have already produced the tracer issue.

Use:

```text
tenet_register_jobs → tenet_start_job → tenet_job_result → tenet_start_eval
```

Do not use:

```text
Tenet Full mode
Tenet Standard mode
Tenet Quick mode as a planning/spec route
any Tenet flow that generates a new multi-job feature DAG
```

### Steps

1. Pick the frozen snapshot:

```text
docs/agent-issues/ISSUE-123.v1.md
```

2. Create the run directory:

```text
.tenet/runs/issue-123-attempt-001/
  spec.md
  scenarios.md
  harness.md
  decomposition.md
  journal/
  proof/
  gate/
```

3. Generate `spec.md` from the agent issue and relevant PRD context.
4. Generate `scenarios.md` from acceptance criteria, anti-scenarios, and proof requirements.
5. Generate `harness.md` from required commands, forbidden paths, testing doctrine, merge policy, and budget rules.
6. Generate `decomposition.md` as a one-node DAG for only this tracer issue.
7. Set Tenet internal retries low:

```yaml
tenet_internal_max_retries: 0
```

8. Register exactly one Tenet `dev` job with exact artifact paths.
9. Start the Tenet job.
10. Use Codex or Claude only.
11. Do not auto-merge.
12. Do not introduce local models.

### Example direct registration shape

```json
{
  "feature": "login",
  "run_slug": "issue-123-attempt-001",
  "run_path": ".tenet/runs/issue-123-attempt-001",
  "artifact_paths": {
    "spec": ".tenet/runs/issue-123-attempt-001/spec.md",
    "scenarios": ".tenet/runs/issue-123-attempt-001/scenarios.md",
    "harness": ".tenet/runs/issue-123-attempt-001/harness.md",
    "decomposition": ".tenet/runs/issue-123-attempt-001/decomposition.md",
    "interview": null
  },
  "jobs": [
    {
      "id": "issue-123",
      "name": "Implement Gitea issue 123",
      "type": "dev",
      "depends_on": [],
      "prompt": "Implement only the frozen execution contract in docs/agent-issues/ISSUE-123.v1.md. Do not expand scope. Do not edit forbidden paths. If the contract is insufficient or conflicts with project doctrine, stop and report scope_conflict."
    }
  ]
}
```

### Exit criteria

- Tenet produces an implementation attempt.
- Tenet did not create a competing feature spec or multi-job decomposition.
- `.tenet/runs/<run>/` contains useful evidence/logs.
- The run contains Tenet-compatible shim artifacts generated from the frozen agent issue.
- The working tree contains a proposed code change.

---

## Stage 6 — Manually run lint, tests, and Playwright proof

### Goal

Learn the mechanical checks before automating them.

### Additions

- Manual preflight ritual.
- Manual proof ritual.
- First proof artifacts.

### What changes from Stage 5

The code is not judged only by Tenet output. You manually verify deterministic facts.

### Steps

Run the commands listed in the agent-issue YAML:

```bash
pnpm lint
pnpm typecheck
pnpm test
npx playwright test
```

If proof is required, manually save evidence:

```text
.tenet/runs/<run>/proof/
  playwright-report/
  screenshots/
  trace.zip
```

### Exit criteria

- You know which commands are realistic for your repo.
- Proof artifacts are produced when required.
- You know what should later be checked by `merge-preflight`.

---

## Stage 7 — Run Tenet eval critics

### Goal

Use Tenet critics after mechanical checks pass.

### Additions

- Tenet `start_eval` step.
- Critic results for the real tracer.

### What changes from Stage 6

Mechanical checks happen first. Tenet critics are then used for semantic review.

### Steps

1. If manual lint/tests/proof fail, do not start eval.
2. If manual checks pass, run Tenet evaluation.
3. Review:
   - code critic
   - test critic
   - interaction/e2e critic
4. Record critic findings.

### Exit criteria

- You know what Tenet catches.
- You know what Tenet misses.
- You have at least one passed or usefully failed eval.

---

## Stage 8 — Manually create a PR

### Goal

Turn a passed attempt into a normal code-review object.

### Additions

- First Gitea PR linked to a tracer issue.

### What changes from Stage 7

A passed implementation becomes a proposed merge, not just local code.

### Steps

1. Create a branch:

```text
agent/issue-123-login-form
```

2. Push the branch.
3. Create a Gitea PR into the feature branch:

```text
feature/login
```

4. Link the PR to the canonical issue.
5. Include:
   - Tenet run path
   - proof artifact path
   - critic summary
   - commands run

### Exit criteria

- Gitea PR exists.
- PR clearly links to issue and run evidence.
- Human can review the change.

---

## Stage 9 — Manually merge to feature branch if good

### Goal

Prove the feature-branch-only merge model.

### Additions

- Manual merge into feature branch.
- Closed or updated tracer issue.

### What changes from Stage 8

The code enters the feature branch only after human approval.

### Steps

1. Confirm PR targets the feature branch, not main.
2. Manually review.
3. Merge if acceptable.
4. Update Gitea issue to `merged_feature`.
5. Unblock dependent issues manually.

### Exit criteria

- One tracer is merged into a feature branch.
- Dependent issues are manually unblocked.
- Main remains untouched.

---

## Stage 10 — Write `docs/agents/runner-plan.md`

### Goal

Document the manual ritual before converting it into code.

### Additions

- Human-readable runner plan.

### What changes from Stage 9

No new automation yet. The manual process becomes explicit and repeatable.

### File

```text
docs/agents/runner-plan.md
```

### Contents

```markdown
# Runner Plan

1. Find next unblocked Gitea tracer issue.
2. Generate or refresh agent-issue snapshot.
3. Generate Tenet-compatible shim artifacts:
   - .tenet/runs/<run>/spec.md
   - .tenet/runs/<run>/scenarios.md
   - .tenet/runs/<run>/harness.md
   - .tenet/runs/<run>/decomposition.md
4. Register exactly one Tenet dev job with exact artifact paths.
5. Ensure Tenet's own interview/spec/decomposition route is not used for this tracer.
6. Run Tenet dev job.
7. Run mechanical preflight.
8. Run Playwright proof if required.
9. Start Tenet eval only if preflight/proof pass.
10. Classify failures into the runner taxonomy.
11. Create PR if critics pass.
12. Auto-merge only if policy allows.
13. Update Gitea state.
```

### Exit criteria

- The manual process is clear enough that Codex could implement it.
- Ambiguities are written down.
- Known failure cases are listed.

---

## Stage 11 — Build minimal runner: issue selection, agent-issue generation, Tenet call

### Goal

Automate issue selection, agent-issue generation, Tenet-compatible shim generation, and direct Tenet job registration.

### Additions

- `agent-runner` command.
- Gitea issue query.
- Dependency-aware issue selection.
- Agent-issue generation.
- Tenet shim artifact generation.
- Tenet direct registered-job call.

### What changes from Stage 10

A script now chooses work and starts Tenet, but it does not yet enforce full policy. The runner also becomes responsible for protecting the Skills/Gitea spec from Tenet re-planning.

### Minimum command

```bash
agent-runner run-next --feature login
```

### Responsibilities

1. Query Gitea for open issues labeled:
   - `agent-tracer`
   - `feature:login`
   - not `blocked`
   - not `running`
2. Build dependency graph from `blocked_by`.
3. Pick the next unblocked issue.
4. Generate:

```text
docs/agent-issues/ISSUE-123.v1.md
```

5. Generate:

```text
.tenet/runs/issue-123-attempt-001/spec.md
.tenet/runs/issue-123-attempt-001/scenarios.md
.tenet/runs/issue-123-attempt-001/harness.md
.tenet/runs/issue-123-attempt-001/decomposition.md
```

6. Register exactly one Tenet `dev` job with exact artifact paths.
7. Ensure Tenet job dependencies are empty inside Tenet:

```yaml
depends_on: []
```

8. Start or continue Tenet.
9. Do not call a Tenet mode that generates a new spec or multi-job DAG.

### Selection algorithm

```text
1. Exclude closed, superseded, blocked, running issues.
2. Prefer retryable failed issues that block other work.
3. Prefer issues that unblock the most future issues.
4. Prefer high priority.
5. Prefer lower risk when priorities are equal.
6. Skip issues over retry budget.
7. Stop issues that exceed time/cost/attempt budget as budget_exceeded.
```

### Exit criteria

- Runner can pick the same issue a human would pick.
- Runner can generate an agent-issue snapshot.
- Runner can generate Tenet-compatible shim artifacts.
- Runner can call Tenet without patching Tenet.
- Tenet does not create a competing spec/decomposition.

---

## Stage 12 — Add `merge-preflight.json`

### Goal

Add deterministic policy enforcement before Tenet critics.

### Additions

- `scripts/agent/merge-preflight.ts`
- `.tenet/runs/<run>/gate/merge-preflight.json`

### What changes from Stage 11

The runner no longer blindly proceeds after development. It checks eligibility first.

### Preflight output

```json
{
  "passed": true,
  "issue": "gitea://gitea.local/owner/repo/issues/123",
  "branch": "agent/issue-123-login-form",
  "run_path": ".tenet/runs/issue-123-attempt-001",
  "attempt": 1,
  "runner_retry_budget": 2,
  "budget_remaining": 1,
  "checks": {
    "canonical_issue_found": true,
    "agent_issue_contract_found": true,
    "tenet_spec_shim_found": true,
    "tenet_scenarios_shim_found": true,
    "tenet_harness_shim_found": true,
    "tenet_decomposition_is_one_node": true,
    "acceptance_criteria_present": true,
    "required_commands_present": true,
    "forbidden_paths_unchanged": true,
    "no_secret_leaks_detected": true,
    "worktree_clean_except_expected": true,
    "budget_not_exceeded": true
  },
  "blocking_findings": []
}
```

### Checks

- Canonical Gitea issue exists.
- Agent-issue snapshot exists.
- Tenet shim artifacts exist.
- Tenet decomposition shim is a one-node DAG.
- Acceptance criteria exist.
- Required commands are declared.
- Forbidden paths were not touched.
- Obvious secrets were not introduced.
- Branch name matches policy.
- Issue state allows execution.
- Dependencies are merged or not required.
- Retry/time/cost budget has not been exceeded.

### Exit criteria

- Preflight can fail fast before critics.
- A failed preflight updates state rather than getting Tenet stuck.
- Tenet itself remains unmodified.

---

## Stage 13 — Add Playwright proof JSON

### Goal

Make proof requirements deterministic before the E2E critic runs.

### Additions

- `scripts/agent/playwright-proof.ts`
- `.tenet/runs/<run>/gate/playwright-proof.json`

### What changes from Stage 12

The runner now enforces declared proof before semantic E2E review.

### Proof output

```json
{
  "passed": true,
  "proof_type": "playwright",
  "surface": "web_ui",
  "artifacts": {
    "report": ".tenet/runs/issue-123-attempt-001/proof/playwright-report",
    "trace": ".tenet/runs/issue-123-attempt-001/proof/trace.zip",
    "screenshots": [
      ".tenet/runs/issue-123-attempt-001/proof/dashboard.png"
    ]
  },
  "blocking_findings": []
}
```

### Rule

If the YAML says:

```yaml
proof_required: true
proof_type: playwright
```

then the runner must produce proof before calling Tenet E2E eval.

### Exit criteria

- Required proof is present before E2E critic.
- Missing proof creates a clear failure state.
- Tenet critics receive cleaner evidence.

---

## Stage 14 — Add Gitea status updates

### Goal

Make Gitea reflect runner/Tenet state.

### Additions

- `scripts/agent/gitea.ts`
- Status labels/comments on issues.

### What changes from Stage 13

The runner now reports its decisions back to the source of truth.

### Gitea update mechanism

Mutable state should be represented as Gitea labels, not repeatedly rewritten YAML frontmatter in the issue body.

Use labels such as:

```text
agent_status:ready
agent_status:running
agent_status:passed_preflight
agent_status:failed_retryable
agent_status:blocked
agent_status:needs_respec
agent_status:awaiting_human_review
agent_status:budget_exceeded
agent_status:passed_critics
agent_status:pr_created
agent_status:merged_feature
agent_status:superseded
agent_status:abandoned
```

The runner should remove the previous `agent_status:*` label before adding the new one. Issue body YAML/comments should remain mostly static and should hold contract data, dependency references, proof requirements, and links to generated run artifacts.

### Status updates

| Event | Gitea update |
|---|---|
| Runner selects issue | `agent_status: running` |
| Preflight passes | `passed_preflight` |
| Preflight fails | `failed_retryable`, `blocked`, `needs_respec`, `awaiting_human_review`, or `budget_exceeded` |
| Proof fails | `failed_retryable`, `needs_respec`, or `budget_exceeded` |
| Critics fail | category-based state |
| Critics pass | `passed_critics` |
| PR created | `pr_created` |
| Auto-merge blocked by policy | `awaiting_human_review` |
| Feature merge complete | `merged_feature` |

### Exit criteria

- A human can open Gitea and see the true state.
- The runner can resume after failure without guessing.
- Repeated failures are visible.

---

## Stage 15 — Add PR creation

### Goal

Let the runner create PRs after all gates pass.

### Additions

- Automated branch push.
- Automated Gitea PR creation.
- PR body template.

### What changes from Stage 14

Passed work becomes a PR automatically.

### PR body should include

```markdown
## Canonical issue

Closes or implements gitea://gitea.local/owner/repo/issues/123

## Agent issue snapshot

docs/agent-issues/ISSUE-123.v1.md

## Tenet run

.tenet/runs/issue-123-attempt-001

## Mechanical checks

- lint: pass
- typecheck: pass
- tests: pass
- preflight: pass
- proof: pass

## Critics

- code_critic: pass
- test_critic: pass
- interaction_e2e: pass
```

### Exit criteria

- PR is created only after preflight/proof/critics pass.
- PR links back to canonical issue.
- PR targets feature branch, not main.

---

## Stage 16 — Add feature-branch auto-merge

### Goal

Allow safe tracer PRs to merge into feature branches automatically.

### Additions

- Auto-merge policy enforcement.
- Feature-branch merge.
- Dependent issue unblocking.

### What changes from Stage 15

The runner can complete low-risk tracer bullets without human intervention.

### Auto-merge conditions

All must be true:

```yaml
auto_merge_to_feature: true
manual_review_required: false
risk_level: low
```

And:

```text
preflight passed
proof passed or not required
Tenet critics passed
PR target is feature branch
no forbidden paths changed
no dependency is unmerged
retry/time/cost budget not exceeded
Tenet did not generate a competing spec or multi-job DAG
```

### Never auto-merge to feature if issue touches

- auth/security-sensitive changes
- production infra
- secrets/config
- migrations
- permissions
- billing/payment
- destructive data paths
- large dependency upgrades

### Exit criteria

- Low-risk PRs can merge to feature branch.
- Risky PRs stop at `awaiting_human_review`.
- Main remains manual-only.

---

## Stage 17 — Test failure states deliberately

### Goal

Prove the runner handles failure cleanly, including Tenet compatibility failures.

### Additions

- Failure test matrix.
- Runner retry budget.
- Tenet internal retry limit.
- Failure prioritization.
- Budget gate.
- Failure classifier step.

### What changes from Stage 16

The system is tested for bad paths, not only happy paths. This stage also confirms that the runner, not Tenet, owns retry policy and cross-issue scheduling.

### Deliberate failure tests

Create or simulate:

1. Missing proof.
2. Broken test.
3. Wrong implementation.
4. Forbidden path change.
5. Blocked dependency.
6. Critic failure.
7. Scope conflict.
8. Manual-review-required blocker.
9. Repeated failed retry.
10. Superseded issue.
11. Budget exceeded.
12. Tenet shim artifact missing.
13. Tenet decomposition accidentally contains more than one job.
14. Tenet attempts to follow stale or fallback artifacts instead of exact artifact paths.

### Retry policy

```yaml
runner_retry_budget: 2
tenet_internal_max_retries: 0
```

Routing:

```text
failed_retryable and retry_count < runner_retry_budget → retry
failed_retryable and retry_count >= runner_retry_budget → budget_exceeded
budget_exceeded → awaiting_human_review after comment/update
scope_conflict → needs_respec or awaiting_human_review
forbidden_path_changed → awaiting_human_review
dependency_blocked → blocked
missing Tenet shim artifact → harness_bug
Tenet multi-job DAG detected → harness_bug
```

### Failure priority

```text
1. Blockers preventing future work
2. Harness failures that affect all future Tenet jobs
3. Retryable failures under retry budget
4. High-priority ready issues
5. Low-risk new issues
6. Isolated non-blocking failures
7. Budget-exceeded issues waiting for human review
```

### Failure classifier

Before fully automating category routing, add a deliberate classifier step that reads:

```text
Gitea issue
agent-issue snapshot
Tenet shim artifacts
merge-preflight.json
playwright-proof.json
Tenet critic findings
run logs
changed files
```

It must output exactly one primary category from the failure taxonomy plus a recommended next status.

### Exit criteria

- Runner does not get stuck.
- Failed issues do not disappear.
- Blockers actually block dependents.
- Repeated failures become human-visible.
- Tenet internal retries do not compound with runner retries.
- Tenet compatibility failures are detected as harness failures, not mistaken for product bugs.

---

## Stage 18 — Add respec Skills

### Goal

Create a clean path for bad tracer bullets.

### Additions

Custom Skills:

```text
skills/engineering/to-agent-issue/SKILL.md
skills/engineering/triage-tenet-failure/SKILL.md
skills/engineering/to-respec-issue/SKILL.md
```

### What changes from Stage 17

The system can now repair bad specs, not just retry bad implementations. It can also distinguish product failures from Tenet compatibility/harness failures such as missing shim artifacts, bad artifact paths, nested retries, or accidental multi-job Tenet decomposition.

### Skill roles

#### `to-agent-issue`

Generates `docs/agent-issues/ISSUE-N.vX.md` from the current Gitea issue. Later, this Skill should also generate the Tenet-compatible shim artifacts for the selected attempt:

```text
.tenet/runs/<run>/spec.md
.tenet/runs/<run>/scenarios.md
.tenet/runs/<run>/harness.md
.tenet/runs/<run>/decomposition.md
```

The generated `decomposition.md` must remain a one-node DAG for the current tracer.

#### `triage-tenet-failure`

Reads:

```text
Gitea issue
agent-issue snapshot
merge-preflight.json
playwright-proof.json
Tenet critic findings
run logs
```

Then emits:

```yaml
primary_failure_category: product_bug | test_bug | harness_bug | evidence_mismatch | contention | scope_conflict | forbidden_path_changed | missing_proof | dependency_blocked | budget_exceeded
recommended_status: failed_retryable | blocked | needs_respec | awaiting_human_review | budget_exceeded | superseded | abandoned
recommended_action: retry_same_issue | create_test_fix_issue | create_harness_fix_issue | create_blocker_issue | supersede_issue | stop_for_human
```

#### `to-respec-issue`

Used when the tracer itself is wrong.

Actions:

```text
1. Mark old issue superseded.
2. Create replacement issue(s).
3. Link replacement back to original.
4. Update dependent issues to point to replacements.
5. Generate new agent-issue snapshots.
```

### Respec example

```text
Issue #123 fails twice with scope_conflict.
triage-tenet-failure says the issue combines schema + UI + auth policy.
to-respec-issue marks #123 superseded.
New issues created:
  #130 Add auth schema
  #131 Add login API
  #132 Add login UI
Dependents now block on #130/#131/#132 instead of #123.
```

### Exit criteria

- Bad tracer bullets can be repaired without corrupting history.
- Superseded issues remain auditable.
- Replacement issues become the new canonical work.

---

## Stage 19 — Introduce local LLMs

### Goal

After the workflow works with Codex/Claude, replace selected roles with local models.

### Additions

- Local model routing.
- Model-tier policy.
- Optional multi-machine execution later.

### What changes from Stage 18

The workflow is stable enough that model quality becomes the variable under test.

### Start simple

Do not begin with all four computers.

First local model experiment:

```yaml
model_tier: local_dev_frontier_review
dev_agent: local_qwen_or_devstral
code_critic: codex_or_claude
test_critic: codex_or_claude
interaction_e2e: codex_or_claude
pr_critic_frontier: codex_or_claude
```

### Suggested progression

1. Local model does development only.
2. Frontier model remains critic.
3. Local model adds secondary PR review.
4. Local model handles low-risk retryable fixes.
5. Local model handles test critic.
6. Only later, distribute work across multiple machines.

### Multi-machine warning

Do not introduce four-machine orchestration until the single-machine local model loop works.

Eventually:

```text
Bluefin = cockpit/control surface
Oracle or denbuntu = main Tenet/OpenCode/local model worker
jmapple = optional review or backup worker
n8n = notification/trigger layer, not source of truth
Gitea = canonical state
```

### Exit criteria

- Local model can complete low-risk issues.
- Frontier critics catch local model mistakes.
- Failure states still work.
- Auto-merge remains restricted to feature branches.
- Main remains human-only.

---

# Final Target Workflow

After Stage 19, the desired command is:

```bash
agent-runner run-next --feature login
```

It should:

```text
1. Query Gitea for open tracer issues.
2. Build dependency graph.
3. Select next unblocked issue.
4. Generate or refresh agent-issue snapshot.
5. Generate Tenet-compatible shim artifacts from the snapshot.
6. Register exactly one Tenet dev job with exact artifact paths.
7. Confirm Tenet's own planning/spec/decomposition flow is not used.
8. Run Tenet development.
9. Run mechanical preflight.
10. Run Playwright proof if required.
11. Run Tenet critics if preflight/proof pass.
12. Classify failures by category.
13. Create PR if all gates pass.
14. Auto-merge to feature branch only if policy allows.
15. Update Gitea issue state.
16. Unblock dependent issues after merge.
17. Leave main for human review.
```

---

# Completed Feature Finalization

When the whole feature branch is done and manually merged to main:

1. Generate a summary:

```text
docs/features/<feature-slug>.md
```

2. Include:

```yaml
status: completed
authority: historical_summary
canonical_epic: gitea://gitea.local/owner/repo/issues/100
feature_branch: feature/login
merged_to_main_pr: gitea://gitea.local/owner/repo/pulls/500
tracer_issues:
  - gitea://gitea.local/owner/repo/issues/123
  - gitea://gitea.local/owner/repo/issues/124
  - gitea://gitea.local/owner/repo/issues/125
```

3. Archive or remove active planning files:

```text
docs/prd/<feature>.md
docs/agent-issues/ISSUE-*.md
.tenet/runs/<feature>/*
```

4. Keep Gitea as the full audit trail.
5. Keep the feature summary in the repo so future agents know where to look.

---

# Design Principles

1. **Do not patch Tenet until necessary.**  
   Use repo-local scripts and supported Tenet interfaces first.

2. **Do not let Tenet guess context.**  
   Always pass exact artifact paths.

3. **Do not let Tenet re-plan Skills/Gitea work.**  
   After a tracer issue exists, use direct registered-job mode with one job and one frozen snapshot.

4. **Do not let Tenet's DAG compete with Gitea.**  
   Gitea owns cross-issue dependencies. Tenet gets a one-node DAG for the current attempt.

5. **Do not let retry systems compound.**  
   Keep Tenet internal retries at `0` or `1`; let the runner's retry budget own the product decision.

6. **Do not make n8n source of truth.**  
   It can trigger and notify, but Gitea owns state.

7. **Do not make failed runs disappear.**  
   They are evidence.

8. **Do not auto-merge risky work.**  
   Passing critics is not the same as being safe to merge.

9. **Do not introduce local LLMs early.**  
   First prove the workflow with Codex/Claude.

10. **Do not build distributed orchestration first.**  
    One reliable worker beats four unreliable ones.

11. **Do not treat the PRD as implementation authority after decomposition.**  
    The PRD is context. The tracer issue is authority.

12. **Do not let stale files confuse agents.**  
    After feature completion, replace active PRD/agent-issue clutter with a feature summary pointing to Gitea.

13. **Prefer boring deterministic gates before LLM critics.**  
    Scripts verify facts. Critics judge meaning.






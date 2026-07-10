# Skills + Tenet + LocalAGI Harness Build Plan

## Purpose

This document defines a gradual build-out of a development harness over:

- **Skills** for idea interrogation, PRD creation, tracer-bullet issue decomposition, and later respec workflows.
- **Gitea** as the canonical source of truth for feature intent, tracer state, dependencies, and merge history.
- **A thin deterministic harness controller** for work eligibility, state transitions, Tenet artifact preparation, policy checks, proof gates, PR authorization, and safe merge decisions.
- **Tenet** for implementation and semantic evaluation of one frozen tracer contract at a time.
- **LocalAGI** for the reusable agent runtime: agent definitions, tool calling, Skills access, MCP connections, execution loops, status streaming, and operator UI.
- **LocalAI** for later local-model serving and role-based model routing across Oracle, Denbuntu, JMapple, or other workers.
- **LocalRecall** only as an optional advisory knowledge and memory layer, never as the source of current issue state or execution authority.
- **Codex/Claude first**, with local LLMs introduced only after the workflow itself is reliable.

The main goal is to avoid building a custom multi-agent platform when an established runtime can provide that commodity layer, while retaining strict ownership of the parts that determine safety and correctness.

The harness must therefore separate:

```text
agent reasoning and tool orchestration
from
deterministic workflow policy and project authority
```

Each stage adds one layer of complexity only after the prior layer works manually.

**Tenet compatibility revision:** Skills/Gitea own specification and decomposition. The controller generates Tenet-compatible shim artifacts from a frozen agent issue and registers exactly one Tenet development job with exact artifact paths. Tenet must not re-interview, re-spec, or create a competing cross-issue DAG.

**LocalAGI integration revision:** LocalAGI replaces the custom agent-loop, tool-registry, model-provider, skill-delivery, and runtime-observability work that would otherwise accumulate inside the runner. It does not replace Gitea authority, deterministic dependency resolution, gate scripts, retry budgets, or merge policy.

**IaC handoff goal:** the architecture and stages are written so an infrastructure-as-code system can later map each service, configuration, secret, volume, network path, model endpoint, health check, and deployment dependency into reproducible infrastructure.

---

## Core Architecture

### Control-plane architecture

The final architecture has separate planes with deliberately narrow responsibilities:

```text
Planning plane
  Skills + frontier model
        ↓
Authority plane
  Gitea epic/tracer issues and feature branches
        ↓
Policy plane
  harness-controller / harnessctl
        ↓
Agent control plane
  LocalAGI agents, Skills, MCP tools, runtime UI
        ↓
Execution and evaluation plane
  Tenet one-job run + deterministic gates + Tenet critics
        ↓
Inference plane
  frontier APIs initially; LocalAI endpoints later
        ↓
Advisory knowledge plane
  LocalRecall for documentation and historical retrieval only
```

The key operational rule is:

```text
LocalAGI may request actions.
The harness controller decides whether those actions are valid.
Gitea records the canonical result.
```

LocalAGI should normally call the controller through a narrow MCP or REST interface. The same controller operations should remain available through a CLI so every action can be tested without an agent.

### Component responsibility map

| Component | Primary responsibility | Must not become |
|---|---|---|
| Skills | Interview, PRD, tracer decomposition, respec | Mutable runtime state store |
| Gitea | Canonical intent, status, dependencies, PRs, merge history | Agent scratchpad |
| `harness-controller` | Eligibility, state machine, gates, authorization, audit links | General-purpose LLM framework |
| LocalAGI | Agent loops, tools, Skills access, MCP, runtime UI, model assignment | Canonical workflow state or policy authority |
| Tenet | Execute/evaluate one frozen tracer attempt | Feature planner or cross-issue scheduler |
| LocalAI | Serve local models behind stable APIs | Workflow state manager |
| LocalRecall | Search documentation and historical context | Source of current issue/spec truth |
| n8n | Triggers, notifications, external workflow glue | Canonical scheduler or merge authority |

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
| LocalAGI conversation/state | Runtime context and operator visibility | Advisory/transient only |
| LocalRecall collections | Searchable doctrine and historical summaries | Advisory only |

### Default merge policy

- Auto-merge is allowed only into a **feature branch**.
- Merge to `main` is always manual.
- Risky issues can pass Tenet but still require human feature-branch merge.
- Dependent issues remain blocked until their blockers are actually merged into the feature branch.

### Ownership boundary

This is the most important compatibility and safety rule.

```text
Skills = interview, PRD creation, tracer decomposition, respec
Gitea = canonical planning state and cross-issue dependency graph
agent-issue snapshot = frozen execution contract for one attempt
harness-controller = state machine, policy, exact artifact generation, gates, authorization
LocalAGI = agent runtime that requests controller operations through narrow tools
Tenet = execute one frozen contract and evaluate the result
LocalAI = model-serving layer selected by agent role
LocalRecall = optional advisory retrieval over stable documentation and history
```

Once a Skills-generated Gitea tracer issue exists:

- Tenet must not re-interview, re-spec, or re-decompose it.
- LocalAGI memory must not be used to infer current issue status.
- LocalRecall must not be used to locate a likely execution contract when an exact path exists.
- The agent must query Gitea or the controller for current state before every state-changing action.
- The controller must reject actions that are invalid for the current state, even if an agent requests them.

For this harness, Tenet's internal job DAG remains deliberately trivial:

```text
one Gitea tracer issue = one frozen agent-issue snapshot = one Tenet registered dev job
```

Gitea owns all cross-issue dependencies through `blocked_by` and `blocks`. Tenet owns only the execution/evaluation state for the single current attempt. LocalAGI owns neither.

### Deterministic controller contract

The controller should be implemented as a small reusable service and CLI, not as a hidden set of prompts.

Recommended interfaces:

```text
CLI:
  harnessctl inspect-feature
  harnessctl prepare-next
  harnessctl start-dev
  harnessctl run-preflight
  harnessctl run-proof
  harnessctl start-eval
  harnessctl classify
  harnessctl create-pr
  harnessctl merge-if-allowed

MCP or REST:
  inspect_feature
  prepare_next
  get_run_state
  start_tenet_dev
  run_preflight
  run_proof
  start_tenet_eval
  classify_run
  create_pr_if_allowed
  merge_pr_if_policy_allows
```

Every mutating operation should:

1. Read fresh canonical state.
2. Validate the requested transition.
3. Perform only the narrow operation requested.
4. Emit structured JSON.
5. Persist an audit link or comment in Gitea when state changes.
6. Be idempotent where practical.

Example policy rejections:

```text
start_tenet_eval before preflight passed → INVALID_STATE
retry after retry budget exhausted → BUDGET_EXCEEDED
merge before required critics passed → POLICY_DENIED
merge into main through automation → POLICY_DENIED
use stale snapshot version → STALE_CONTRACT
```

### LocalAGI tool boundary

LocalAGI agents should receive narrow, capability-limited tools. Avoid exposing unrestricted shell, unrestricted Gitea administration, or a raw merge command to the main operator agent.

Prefer:

```text
merge_pr_if_policy_allows(run_id)
```

over:

```text
merge_pr(repo, branch, force, bypass_checks)
```

Recommended initial agents:

```yaml
harness_operator:
  purpose: advance one run through allowed state transitions
  tools:
    - inspect_feature
    - prepare_next
    - get_run_state
    - start_tenet_dev
  merge_permission: none

failure_triage:
  purpose: interpret structured failures and recommend routing
  tools:
    - read_run_evidence
    - classify_run
  state_write_permission: recommendation_only

pr_reviewer:
  purpose: secondary semantic review against contract and evidence
  tools:
    - read_contract
    - read_diff
    - read_gate_results
  merge_permission: none
```

Later, the operator may receive `create_pr_if_allowed` and `merge_pr_if_policy_allows`, but the controller remains the final authorization point.

### LocalAI boundary

LocalAI should be introduced as an inference service, not as a new workflow manager.

Recommended deployment model:

```text
LocalAGI agent role → logical model profile → LocalAI endpoint/model
```

Prefer job-level routing across machines:

```text
Oracle LocalAI endpoint = development models
Denbuntu LocalAI endpoint = test/review models
JMapple LocalAI endpoint = overflow or specialized models
frontier provider = final or high-risk critic
```

Do not begin with distributed model sharding across all machines. First prove that each role can call one stable endpoint and that failures are visible and recoverable.

### LocalRecall boundary

Good LocalRecall collections include:

- project architecture and testing doctrine
- coding standards
- stable framework documentation
- completed feature summaries
- selected historical failure reports
- operational runbooks

Do not use LocalRecall for:

- current Gitea issue state
- current dependency eligibility
- selecting the active snapshot version
- retrieving acceptance criteria when an exact frozen contract exists
- deciding whether a PR is safe to merge

Exact execution paths must be injected directly into the LocalAGI task and Tenet job.

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

## Stage 10 — Define the controller and agent integration contract

### Goal

Document the manual ritual as explicit state transitions and typed operations before implementing automation.

### Additions

- `docs/agents/harness-controller-contract.md`
- State-transition table.
- CLI command schemas.
- MCP or REST tool schemas for LocalAGI.
- Permission boundaries and structured error categories.

### What changes from Stage 9

No autonomous loop is added yet. The workflow becomes precise enough to implement and test without an LLM.

### Required contents

```markdown
# Harness Controller Contract

## Canonical inputs
- Gitea epic/tracer issue
- frozen agent-issue snapshot
- exact Tenet run path

## Valid transitions
- ready → running
- running → passed_preflight
- passed_preflight → passed_critics
- passed_critics → pr_created
- pr_created → merged_feature

## Controller operations
- inspect_feature
- prepare_next
- start_tenet_dev
- run_preflight
- run_proof
- start_tenet_eval
- classify_run
- create_pr_if_allowed
- merge_pr_if_policy_allows

## Policy denials
- invalid state
- stale contract
- dependency blocked
- budget exceeded
- manual review required
- forbidden target branch
```

### Exit criteria

- Each operation has defined inputs, outputs, side effects, and rejection conditions.
- A human could execute the entire workflow using only the planned CLI.
- LocalAGI can later consume the same operations without owning policy.

---

## Stage 11 — Build the minimal deterministic harness controller

### Goal

Automate issue selection, snapshot generation, Tenet-compatible shim generation, and direct Tenet job registration without creating a custom agent framework.

### Additions

- `harnessctl` or `agent-harness` CLI.
- Gitea adapter.
- Dependency-aware issue selection.
- Agent-issue snapshot generator.
- Tenet shim artifact generator.
- Direct Tenet registered-job adapter.
- Structured JSON outputs.

### What changes from Stage 10

The workflow now has executable policy code, but no LocalAGI autonomy yet.

### Minimum commands

```bash
harnessctl inspect-feature --feature login
harnessctl prepare-next --feature login
harnessctl start-dev --run issue-123-attempt-001
harnessctl get-run-state --run issue-123-attempt-001
```

### Responsibilities

1. Query Gitea for candidate tracer issues.
2. Build the dependency graph from canonical issue data.
3. Select only an eligible issue.
4. Generate the frozen snapshot.
5. Generate exact Tenet shim artifacts.
6. Validate that `decomposition.md` contains one job only.
7. Register exactly one Tenet `dev` job with exact paths.
8. Persist the selected run slug and snapshot version.
9. Reject stale, blocked, or over-budget work.

### Selection algorithm

```text
1. Exclude closed, superseded, abandoned, running, and blocked issues.
2. Require all blocked_by issues to be merged_feature.
3. Prefer retryable blockers still within budget.
4. Prefer work that unblocks the most downstream issues.
5. Prefer higher priority.
6. Prefer lower risk when priorities are equal.
7. Stop over-budget issues as budget_exceeded.
```

### Exit criteria

- The CLI selects the same issue a careful human would select.
- It generates a valid frozen contract and exact Tenet artifacts.
- Tenet does not create a competing spec or multi-job DAG.
- All outputs are machine-readable enough for LocalAGI and IaC health tests.

---

## Stage 12 — Deploy LocalAGI as the agent control plane

### Goal

Use LocalAGI for the agent loop and tool orchestration instead of implementing those capabilities inside the controller.

### Additions

- One LocalAGI deployment.
- One `harness_operator` agent.
- MCP or REST connection to the controller.
- Git-synchronized engineering Skills where compatible.
- Runtime status/streaming available to the operator.

### What changes from Stage 11

The controller remains deterministic, but a LocalAGI agent can now request its safe operations.

### Initial permission set

The first agent should receive only:

```text
inspect_feature
prepare_next
get_run_state
start_tenet_dev
```

It should not initially receive:

```text
create_pr
merge_pr
raw shell
unrestricted Gitea write
secret access
IaC deployment credentials
```

### Agent authority statement

Include in the LocalAGI system instructions:

```text
Your memory and conversation history are advisory only.
Query the harness controller for current state before every action.
Use only the exact execution-contract and run paths returned by the controller.
Do not reinterpret eligibility, retry, proof, PR, or merge policy.
When the controller rejects an operation, report the rejection rather than bypassing it.
```

### Compatibility test for Skills

Test one existing `SKILL.md` package for:

- metadata parsing
- directory layout
- progressive disclosure
- referenced scripts/resources
- Git synchronization
- usability by both frontier planning agents and LocalAGI agents

### Exit criteria

- LocalAGI can prepare and start one real Tenet job through the controller.
- The same operation still works manually through CLI.
- LocalAGI cannot bypass dependency or state policy.
- Runtime UI/state is useful but clearly non-canonical.

---

## Stage 13 — Add deterministic merge preflight

### Goal

Enforce mechanical facts before any semantic critic or PR action.

### Additions

- `scripts/agent/merge-preflight.ts`
- `.tenet/runs/<run>/gate/merge-preflight.json`
- Controller operation `run_preflight`.
- LocalAGI tool wrapper that returns the controller's result unchanged.

### Preflight checks

- Canonical issue exists.
- Correct snapshot version exists.
- Exact Tenet shim artifacts exist.
- Tenet decomposition contains exactly one job.
- Acceptance criteria and required commands are present.
- Dependencies are merged.
- Branch naming policy is satisfied.
- Forbidden paths are unchanged.
- Secret scan passes.
- Worktree state is expected.
- Retry/time/cost budget is available.

### Example output

```json
{
  "passed": false,
  "run": "issue-123-attempt-001",
  "primary_category": "forbidden_path_changed",
  "checks": {
    "canonical_issue_found": true,
    "snapshot_current": true,
    "tenet_decomposition_is_one_node": true,
    "forbidden_paths_unchanged": false
  },
  "blocking_findings": [
    "migrations/0042_users.sql was modified"
  ]
}
```

### Exit criteria

- Preflight fails fast and deterministically.
- LocalAGI cannot reinterpret a failed preflight as a pass.
- The controller updates or recommends the correct Gitea failure state.

---

## Stage 14 — Add Playwright and other declared proof gates

### Goal

Produce deterministic evidence before the E2E critic runs.

### Additions

- `scripts/agent/playwright-proof.ts`
- `.tenet/runs/<run>/gate/playwright-proof.json`
- Controller operation `run_proof`.
- Storage rules for reports, traces, screenshots, or other proof artifacts.

### Rule

When the snapshot declares:

```yaml
proof_required: true
proof_type: playwright
```

proof must pass before Tenet E2E evaluation or PR creation.

### Exit criteria

- Required proof is generated at exact recorded paths.
- Missing proof receives a structured category.
- IaC can provision any browser/runtime dependencies reproducibly.

---

## Stage 15 — Add Tenet evaluation and structured failure classification

### Goal

Run semantic critics only after deterministic gates pass and normalize their findings into the harness taxonomy.

### Additions

- Controller operation `start_tenet_eval`.
- `failure_triage` agent, dedicated classifier prompt, or CLI-invoked classifier.
- Structured classification schema.
- Clear distinction between deterministic facts and semantic recommendations.

### Classification inputs

```text
canonical Gitea issue
frozen snapshot
Tenet shim artifacts
merge-preflight.json
proof JSON
Tenet critic findings
run logs
changed files
```

### Classification output

```yaml
primary_failure_category: product_bug | test_bug | harness_bug | evidence_mismatch | contention | scope_conflict | forbidden_path_changed | missing_proof | dependency_blocked | budget_exceeded
recommended_status: failed_retryable | blocked | needs_respec | awaiting_human_review | budget_exceeded | superseded | abandoned
recommended_action: retry_same_issue | create_test_fix_issue | create_harness_fix_issue | create_blocker_issue | supersede_issue | stop_for_human
```

The controller owns the final allowed state transition. The classifier supplies the semantic recommendation.

### Exit criteria

- Critics run only after gates pass.
- Deterministic failure categories cannot be overridden by the classifier.
- Ambiguous failures receive one normalized primary category.

---

## Stage 16 — Add Gitea state updates and audit links

### Goal

Make Gitea reflect the authoritative harness state while preserving LocalAGI and Tenet logs as supporting evidence.

### Additions

- Gitea adapter write operations.
- Native `agent_status:*` labels.
- Comments linking issue, snapshot, run, gate results, proof, and critic summary.
- Idempotent update behavior.

### State updates

| Event | Gitea state |
|---|---|
| Controller selects issue | `running` |
| Preflight passes | `passed_preflight` |
| Gate/critic failure | category-based failure state |
| All critics pass | `passed_critics` |
| PR created | `pr_created` |
| Merge policy requires human | `awaiting_human_review` |
| Feature merge completes | `merged_feature` |

### Exit criteria

- Gitea alone shows the current canonical state.
- LocalAGI restart or memory loss does not impair resumption.
- Every run is traceable from its issue and every issue links to its runs.

---

## Stage 17 — Add policy-controlled PR creation

### Goal

Create a PR only after deterministic gates and required semantic critics pass.

### Additions

- Controller operation `create_pr_if_allowed`.
- Branch push and Gitea PR adapter.
- PR body template with complete evidence links.
- LocalAGI access to the policy-wrapped operation, not raw PR administration.

### PR evidence

The PR body should include:

```text
canonical issue
snapshot path and version
Tenet run path
changed scope summary
required commands and results
preflight result
proof artifact paths
critic results
failure/retry history if relevant
```

### Exit criteria

- PR creation is rejected unless all required conditions pass.
- PR targets the feature branch, never main.
- The action is idempotent and does not create duplicate PRs on retry.

---

## Stage 18 — Add feature-branch auto-merge and deliberate failure testing

### Goal

Allow safe low-risk tracer PRs to merge into feature branches while proving that all important bad paths stop correctly.

### Additions

- Controller operation `merge_pr_if_policy_allows`.
- Auto-merge policy engine.
- Dependent-issue unblocking after confirmed merge.
- Failure test matrix.
- Runner retry budget and Tenet internal retry limit.

### Auto-merge requirements

All must be true:

```yaml
auto_merge_to_feature: true
manual_review_required: false
risk_level: low
```

And:

```text
preflight passed
proof passed or was not required
required Tenet critics passed
PR target is the feature branch
no forbidden paths changed
all dependencies are actually merged
budget remains available
one-job Tenet contract remained intact
```

Never auto-merge changes involving security/auth policy, production infrastructure, secrets, migrations, permissions, billing, destructive data paths, or major dependency upgrades.

### Deliberate failure tests

Test at least:

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
12. Missing Tenet shim artifact.
13. Multi-job Tenet decomposition.
14. Stale snapshot version.
15. LocalAGI requests an invalid transition.
16. LocalAGI requests raw merge bypass.
17. LocalAGI or controller restarts mid-run.
18. Gitea or Tenet is temporarily unavailable.

### Retry policy

```yaml
runner_retry_budget: 2
tenet_internal_max_retries: 0
```

### Exit criteria

- Policy-wrapped auto-merge works for low-risk feature-branch PRs.
- Invalid agent requests are rejected safely.
- Restart and service-unavailability behavior is understood.
- Main remains human-only.

---

## Stage 19 — Add respec and specialized Skills

### Goal

Repair bad tracer specifications and add reusable semantic workflows without moving authority into agent memory.

### Additions

```text
skills/engineering/to-agent-issue/SKILL.md
skills/engineering/triage-tenet-failure/SKILL.md
skills/engineering/to-respec-issue/SKILL.md
skills/engineering/review-run-evidence/SKILL.md
```

### Skill roles

#### `to-agent-issue`

Generates the frozen snapshot and proposed Tenet shims from the current canonical issue. The controller validates and commits the exact output paths and version.

#### `triage-tenet-failure`

Produces the structured semantic failure recommendation. It cannot directly overwrite deterministic gate categories.

#### `to-respec-issue`

Proposes replacement issues when the tracer itself is wrong. The controller/Gitea adapter performs the canonical supersede and dependency rewiring operations.

#### `review-run-evidence`

Summarizes contract compliance, changed scope, tests, proof, critic output, and unresolved risks for a human or final frontier critic.

### Exit criteria

- Bad tracer bullets can be superseded without corrupting history.
- Skills are reusable through frontier planning workflows, CLI/controller execution, and LocalAGI only where compatible without changing the canonical format.
- Agent-generated proposals are validated before becoming canonical Gitea changes.

---

## Stage 20 — Introduce LocalAI, role-based local models, and optional LocalRecall

### Goal

Replace selected frontier roles with local models only after the controller, LocalAGI integration, gates, and failure handling are reliable.

### Additions

- LocalAI endpoint inventory.
- Logical model profiles by role.
- Agent-to-endpoint routing.
- Health checks, fallback policy, and resource limits.
- Optional LocalRecall collections for stable documentation and history.

### Initial routing

```yaml
harness_operator:
  model: frontier_or_small_reliable_model

tenet_developer:
  endpoint: localai-oracle
  model: local_coder

failure_triage:
  model: frontier_reviewer

pr_reviewer:
  model: frontier_reviewer
```

### Suggested progression

1. LocalAI on one machine for development only.
2. Frontier models remain critics.
3. Add a local secondary PR reviewer.
4. Move low-risk retry fixes to a local model.
5. Add a local test critic on Denbuntu.
6. Add role-based routing across machines.
7. Add fallbacks for endpoint outage or model failure.
8. Evaluate LocalRecall for architecture docs and historical summaries.

### LocalRecall rules

Index only stable/advisory material at first:

```text
project doctrine
architecture documentation
testing standards
completed feature summaries
selected historical failure reports
operational runbooks
```

Never use it to infer active issue status, dependency eligibility, snapshot version, or merge authorization.

### Multi-machine warning

Do not begin with distributed model sharding. Prefer independent LocalAI services with explicit job-level routing and observable health.

### Exit criteria

- A local development model completes low-risk work through the unchanged controller contract.
- Frontier critics catch local mistakes.
- Endpoint failures do not corrupt workflow state.
- LocalRecall remains advisory.
- Auto-merge restrictions and human-only main merge remain unchanged.

# IaC Integration Contract

The IaC system should treat this harness as several deployable services with explicit ownership and dependencies, not one opaque application.

## Deployable units

```text
gitea
harness-controller
localagi
localai-oracle
localai-denbuntu
localai-jmapple          # optional
localrecall              # optional/later
n8n                      # triggers/notifications only
tenet worker environment # may be colocated with controller or dev worker initially
```

## Configuration categories

The IaC analysis should account for:

- service images or reproducible installation versions
- service users and filesystem ownership
- persistent volumes and backup requirements
- exact repository/worktree locations
- Gitea URL, repository identity, labels, and API credentials
- LocalAGI agent definitions and enabled Skills repositories
- controller MCP/REST endpoint and authentication
- Tenet binary/version and run-root paths
- LocalAI endpoint inventory and logical model profiles
- model storage paths and download provenance
- GPU device exposure and runtime-specific configuration
- Tailscale addressing, ACL tags, and firewall policy
- TLS/reverse-proxy requirements if any
- secret injection and rotation
- health checks and readiness ordering
- resource limits and concurrency caps
- logs, metrics, and retention
- backup/restore tests
- upgrade and rollback strategy

## Secret boundary

Recommended secret ownership:

```text
harness-controller:
  Gitea token with only required repository permissions
  Tenet/runtime credentials if required

LocalAGI:
  controller access token
  model-provider keys for assigned agents
  no unrestricted Gitea admin token
  no production deployment credentials
  no unique workflow secrets that are unavailable to the CLI/controller path

LocalAI:
  normally no Gitea credentials
  model registry credentials only if required

LocalRecall:
  database credentials
  no merge or Gitea write credentials
```

## Network boundary

Prefer allowlisted communication:

```text
LocalAGI → harness-controller, when enabled
harness-controller → Gitea
harness-controller → Tenet worker/runtime
LocalAGI → LocalAI endpoint(s), when enabled
LocalAGI → LocalRecall, when enabled
n8n → harness-controller trigger endpoint
```

LocalAI and LocalRecall should not need direct write access to Gitea.

## Health and readiness

At minimum, IaC should be able to verify:

```text
Gitea API reachable and authenticated
controller can read repository state
controller CLI/MCP schema version matches expected version
LocalAGI can list the allowed controller tools
Tenet can execute a no-op or toy registered job
LocalAI endpoint can load and answer with the configured model
LocalRecall can write/read a test document when enabled
persistent paths have correct ownership and free space
```

## Portability rule

Agent definitions, Skills, controller schemas, policy files, and model-routing profiles should live in Git wherever practical. Secrets, large model weights, transient run logs, and generated proof artifacts should not be embedded in IaC source.

---

# Final Target Workflow

After Stage 20, the desired human command is:

```bash
harnessctl run-next --feature login
```

The actual safe workflow is:

```text
1. Human, n8n, or LocalAGI requests the next run.
2. Controller queries fresh Gitea state.
3. Controller builds the dependency graph and selects eligible work.
4. Controller generates/version-checks the frozen agent-issue snapshot.
5. Controller generates exact Tenet-compatible shim artifacts.
6. Controller registers exactly one Tenet dev job.
7. LocalAGI orchestrates allowed calls and reports runtime progress.
8. Tenet performs development using the assigned frontier or LocalAI-backed model.
9. Controller runs deterministic preflight.
10. Controller runs required proof.
11. Tenet critics and optional secondary reviewers run only after gates pass.
12. Failure classifier recommends semantic routing; controller enforces valid state.
13. Controller creates a feature-branch PR if all requirements pass.
14. Controller auto-merges only when explicit low-risk policy allows.
15. Gitea records the canonical state and audit links.
16. Dependents unblock only after confirmed feature-branch merge.
17. Main remains human-reviewed and human-merged.
```

The operational shorthand is:

```text
LocalAGI requests.
The controller validates.
Tenet executes and evaluates.
LocalAI serves selected models.
Gitea records truth.
```

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

1. **Do not build a custom multi-agent runtime when LocalAGI can supply the commodity layer.**  
   Keep custom work focused on policy, evidence, state, and project-specific integration.

2. **Do not make LocalAGI a source of truth.**  
   Its conversations, summaries, schedules, and runtime state are advisory and operational only.

3. **Keep a CLI beneath every agent tool.**  
   The workflow must remain testable and recoverable without an LLM.

4. **Use capability-limited tools.**  
   Expose policy-wrapped operations such as `merge_pr_if_policy_allows`, not unrestricted merge or shell access.

5. **Do not patch Tenet until necessary.**  
   Use supported job primitives and repo-local adapters first.

6. **Do not let Tenet guess context.**  
   Always pass exact artifact paths.

7. **Do not let Tenet re-plan Skills/Gitea work.**  
   After a tracer exists, use one frozen snapshot and one registered Tenet job.

8. **Do not let Tenet's DAG compete with Gitea.**  
   Gitea owns cross-issue dependencies; Tenet receives a one-node DAG.

9. **Do not let retry systems compound.**  
   Keep Tenet internal retries at `0` or `1`; let the controller own the product retry budget.

10. **Prefer deterministic gates before LLM critics.**  
    Scripts verify facts; critics judge meaning.

11. **Do not let semantic agents override deterministic failures.**  
    A failed forbidden-path, proof, dependency, or budget check remains failed.

12. **Do not make LocalRecall authoritative.**  
    Use it for stable doctrine and history, never current issue state or exact contract selection.

13. **Treat LocalAI as inference infrastructure.**  
    It serves models; it does not own workflow state or merge decisions.

14. **Prefer job-level routing before distributed model sharding.**  
    One reliable endpoint per role is easier to debug and automate.

15. **Do not make n8n source of truth.**  
    It may trigger and notify, but Gitea and the controller own state.

16. **Do not make failed runs disappear.**  
    They are evidence and should remain linked to the canonical issue.

17. **Do not auto-merge risky work.**  
    Passing critics is not the same as being safe to merge.

18. **Do not introduce local LLMs early.**  
    First prove the workflow with frontier models through the same controller contract.

19. **Do not introduce multi-machine orchestration first.**  
    One reliable LocalAI worker beats several unreliable endpoints.

20. **Do not treat the PRD as implementation authority after decomposition.**  
    The tracer issue and frozen snapshot govern the attempt.

21. **Do not let stale files or memories confuse agents.**  
    Version snapshots, inject exact paths, and archive completed feature planning artifacts.

22. **Make infrastructure boundaries explicit.**  
    Services, secrets, volumes, health checks, network access, and upgrade paths should be reproducible through IaC.

23. **Keep main human-controlled.**  
    Automation may merge eligible low-risk work only into feature branches.

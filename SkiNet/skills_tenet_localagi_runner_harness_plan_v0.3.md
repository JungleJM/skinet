# Skills + Provider-Neutral Harness Build Plan v0.3

## Purpose

This document defines a gradual build-out of a development harness over:

- **Skills** for idea interrogation, PRD creation, tracer-bullet issue decomposition, and later respec workflows.
- **An authority provider** as the canonical source of truth for feature intent, tracer state, dependencies, PRs, and merge history. The first adapter is Gitea/Forgejo-compatible; GitHub should be possible later without changing controller policy.
- **A thin deterministic harness controller** for work eligibility, state transitions, execution artifact preparation, policy checks, proof gates, PR authorization, and safe merge decisions.
- **An execution provider** for implementation and semantic evaluation of one frozen tracer contract at a time. The first adapter is Tenet; a future guarded development/review engine should be swappable behind the same controller-owned run contract.
- **LocalAGI** only as an optional operator surface and agent adapter when it makes the workflow easier. The harness must not be built to LocalAGI's internal specs.
- **LocalAI** for later local-model serving and role-based model routing across Oracle, Denbuntu, JMapple, or other workers.
- **LocalRecall** only as an optional advisory knowledge and memory layer, never as the source of current issue state or execution authority.
- **Codex/Claude first**, with local LLMs introduced only after the workflow itself is reliable.

The main goal is to build the smallest deterministic harness that can run without any agent platform, while leaving a narrow optional adapter for LocalAGI or another runtime to request the same operations.

The harness must therefore separate:

```text
agent reasoning and tool orchestration
from
deterministic workflow policy and project authority
```

Each stage adds one layer of complexity only after the prior layer works manually.

**Authority-provider revision:** the controller must not hard-code Gitea as the domain model. It should speak in provider-neutral concepts such as feature issue, tracer issue, labels/status, dependency edges, branch, PR, comments, and audit links. Gitea/Forgejo is the first adapter because it is what the local environment uses. GitHub or another forge should require an adapter and field-mapping change, not a workflow-policy rewrite.

**Execution-provider revision:** the controller must not hard-code Tenet as the domain model. It should speak in provider-neutral concepts such as frozen contract, run, development job, evaluation job, artifact bundle, proof bundle, critic result, and retry budget. Tenet is the first adapter because it provides useful job/artifact/eval primitives. A future execution engine with strong guardrails and critics should be able to replace Tenet if it can consume the same frozen contract and return the same structured run evidence.

**v0.3 replaceability revision:** provider replacement is now an explicit design goal, not just a desirable side effect. Authority-provider replacement means Gitea/Forgejo, GitHub, or another forge can back the same `AuthorityProvider` interface. Execution-provider replacement means Tenet, or a future guarded development/review engine, can back the same `ExecutionProvider` interface. The controller owns workflow policy; providers own translation to concrete APIs, artifact formats, and result schemas.

**Tenet compatibility revision:** Skills plus the authority provider own specification and decomposition. The controller generates Tenet-compatible shim artifacts from a frozen agent issue and registers exactly one Tenet development job with exact artifact paths. Tenet must not re-interview, re-spec, or create a competing cross-issue DAG.

**LocalAGI optional-adapter revision:** LocalAGI may provide a convenient UI, agent loop, MCP client, status view, and model/tool orchestration. It must not define controller schemas, run state, workflow semantics, artifact formats, retry behavior, or merge policy. If LocalAGI is deleted, the CLI and controller must still complete the same workflow.

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
  authority provider: Gitea/Forgejo first; GitHub or another forge later
        ↓
Policy and operation plane
  harness-controller / harnessctl
        ↓
Optional operator adapter
  LocalAGI agents, MCP tools, runtime UI, or any later equivalent
        ↓
Execution and evaluation plane
  execution provider: Tenet first; another guarded dev/eval engine later
        ↓
Inference plane
  frontier APIs initially; LocalAI endpoints later
        ↓
Advisory knowledge plane
  LocalRecall for documentation and historical retrieval only
```

The key operational rule is:

```text
Humans, scripts, n8n, LocalAGI, or another adapter may request actions.
The harness controller decides whether those actions are valid.
The authority provider records the canonical result.
```

The CLI is the primary interface. LocalAGI, if used, calls the controller through a thin MCP or REST adapter that maps one-for-one onto CLI/controller operations. No workflow behavior should exist only inside LocalAGI agent definitions, conversations, or memory.

### Component responsibility map

| Component | Primary responsibility | Must not become |
|---|---|---|
| Skills | Interview, PRD, tracer decomposition, respec | Mutable runtime state store |
| Authority provider | Canonical intent, status, dependencies, PRs, merge history | Agent scratchpad or provider-specific policy engine |
| Gitea/Forgejo adapter | First authority-provider implementation | Controller domain model |
| GitHub adapter | Possible later authority-provider implementation | Reason to rewrite workflow policy |
| `harness-controller` | Eligibility, state machine, gates, authorization, audit links | General-purpose LLM framework |
| LocalAGI | Optional agent/operator UI over controller operations | Required dependency, canonical workflow state, artifact format owner, or policy authority |
| Execution provider | Execute/evaluate one frozen tracer attempt | Feature planner or cross-issue scheduler |
| Tenet adapter | First execution-provider implementation | Controller domain model |
| LocalAI | Serve local models behind stable APIs | Workflow state manager |
| LocalRecall | Search documentation and historical context | Source of current issue/spec truth |
| n8n | Triggers, notifications, external workflow glue | Canonical scheduler or merge authority |

### Provider-neutral domain model

Use provider-neutral names inside controller schemas, run ledgers, frozen snapshots, and policy code.

| Controller concept | Gitea/Forgejo adapter | GitHub adapter | Notes |
|---|---|---|---|
| feature issue | Gitea issue | GitHub issue | Planning context / epic-like issue |
| tracer issue | Gitea issue | GitHub issue | One vertical implementation slice |
| issue key | `{provider, owner, repo, number}` | `{provider, owner, repo, number}` | Never parse provider URLs for core logic |
| status | labels such as `agent_status/ready` | labels such as `agent_status/ready` | Use a configured status-label mapping |
| dependency edge | issue dependency or markdown fallback | issue relationship/sub-issue/blocking fallback | Adapter normalizes to `blocked_by` / `blocks` |
| PR | Gitea pull request | GitHub pull request | Controller policy owns target branch validation |
| audit link | issue comment | issue comment | Adapter writes controller-owned structured summaries |
| branch | Git branch | Git branch | Git operations can remain provider-neutral where possible |

Provider URLs such as `gitea://...` or GitHub issue URLs are external references. They should be stored for audit and operator convenience, but controller logic should use normalized issue keys.

Recommended normalized issue key:

```json
{
  "provider": "gitea",
  "host": "https://gitea.local",
  "owner": "owner",
  "repo": "repo",
  "number": 123
}
```

### AuthorityProvider interface

The controller should depend on one deep authority interface, with Gitea/Forgejo and GitHub as adapters behind it.

Minimum interface:

```text
AuthorityProvider
  get_feature(feature_ref) -> FeatureRecord
  list_tracers(feature_ref) -> TracerRecord[]
  get_tracer(issue_key) -> TracerRecord
  list_dependencies(issue_key) -> DependencyGraph
  set_status(issue_key, status, audit) -> ProviderMutationResult
  create_or_update_snapshot_ref(issue_key, snapshot_ref, audit) -> ProviderMutationResult
  create_pr(run_id, source_branch, target_branch, body) -> PullRequestRecord
  merge_pr_if_provider_checks_allow(pr_key) -> ProviderMutationResult
  add_audit_comment(target_key, structured_summary) -> ProviderMutationResult
```

The interface owns provider differences:

- Gitea/Forgejo native issue dependencies versus markdown fallback.
- GitHub labels, linked issues, sub-issues, task lists, or markdown fallback.
- Label IDs versus label names.
- PR terminology and merge APIs.
- URL formats and authentication.

The controller owns workflow policy:

- which statuses are valid
- whether an issue is eligible
- whether a dependency counts as satisfied
- whether a PR target is allowed
- whether a merge is allowed
- how stale snapshots are rejected

### ExecutionProvider interface

The controller should depend on one deep execution interface, with Tenet as the first adapter behind it.

Minimum interface:

```text
ExecutionProvider
  prepare_artifacts(run_contract) -> ArtifactBundle
  register_dev_job(run_contract, artifact_bundle) -> ExecutionJob
  start_dev_job(job_key) -> ExecutionStartResult
  get_job_result(job_key) -> ExecutionResult
  start_eval(run_contract, artifact_bundle, implementation_ref) -> EvaluationJob
  get_eval_result(eval_key) -> EvaluationResult
```

The interface owns execution-engine differences:

- Tenet job primitives and artifact path requirements.
- A future engine's work-order format.
- A future engine's critic/evaluation result format.
- Engine-specific retry knobs.
- Engine-specific log locations.

The controller owns run policy:

- one frozen tracer contract per run
- retry budget
- required proof gates
- state transitions
- branch and merge policy
- failure classification after structured evidence exists

If a future execution engine cannot accept an externally frozen contract, exact paths, forbidden paths, required commands, and a one-tracer work order, it is not a drop-in execution provider. It may still be useful behind a custom adapter, but the adapter must prove it preserves the same controller contract.

### Source-of-truth rule

Do **not** let truth migrate from PRD to Markdown to PR to execution run artifacts.

Instead:

```text
authority-provider issue = canonical intent and state
docs/agent-issues/ISSUE-N.vX.md = frozen execution snapshot for one attempt/spec version
execution-provider run directory = implementation attempt and evidence
authority-provider PR = proposed code merge
feature branch = auto-merge target after gates pass
main = human-only merge target
```

For the first adapter set, this concretely means:

```text
Gitea/Forgejo issue = canonical intent and state
.tenet/runs/<run>/ = Tenet implementation attempt and evidence
Gitea/Forgejo PR = proposed code merge
```

### Portable configuration ownership

Keep portable system definition in your own Git-controlled formats:

| Configuration | Owner |
|---|---|
| Prompts and role instructions | Git-controlled harness config |
| Skills and referenced resources | Git-controlled Skill packages |
| Agent profiles | Git-controlled adapter-neutral YAML/JSON |
| Model-routing rules | Git-controlled model profile config |
| Controller schemas and policy rules | Git-controlled controller config |
| MCP/REST tool schemas | Generated from or versioned with controller schemas |
| Permissions and capability manifests | Git-controlled least-privilege manifests |
| Workflow state | Authority-provider labels/comments plus controller run ledger |
| Secrets | Secret manager or environment injection, never Git |
| LocalAGI UI state/conversations | Noncanonical convenience state |
| LocalRecall indexes | Rebuildable advisory cache |

If a prompt, profile, permission, routing rule, or state transition exists only inside LocalAGI's UI, the design is not portable yet.

### Artifact roles

| Artifact | Role | Authority |
|---|---|---|
| Authority-provider feature issue | Feature-level context and intent | Canonical planning context |
| Authority-provider tracer issue | One vertical slice to build | Canonical implementation intent |
| `docs/agent-issues/ISSUE-N.vX.md` | Frozen execution contract generated from the authority provider | Authority for one execution attempt |
| Execution-provider artifacts | Engine-specific export of the frozen agent issue | Compatibility shim, not canonical truth |
| Execution-provider run path | Run logs, proof, preflight, critic results | Evidence only |
| Authority-provider PR | Proposed code change | Merge vehicle |
| `docs/features/<feature>.md` | Completed feature summary | Historical summary |
| LocalAGI conversation/state | Runtime context and operator visibility | Advisory/transient only |
| LocalRecall collections | Searchable doctrine and historical summaries | Advisory only |

For the first Tenet adapter, execution-provider artifacts are:

| Tenet artifact | Role | Authority |
|---|---|---|
| `.tenet/runs/<run>/spec.md` | Tenet-compatible export of the frozen agent issue | Compatibility shim, not canonical truth |
| `.tenet/runs/<run>/scenarios.md` | Acceptance criteria, anti-scenarios, proof expectations | Compatibility shim, not canonical truth |
| `.tenet/runs/<run>/harness.md` | Required commands, forbidden paths, gates, merge policy | Compatibility shim, not canonical truth |
| `.tenet/runs/<run>/decomposition.md` | One-node Tenet DAG for the current tracer | Compatibility shim, not cross-issue planning |
| `.tenet/runs/<run>/` | Run logs, proof, preflight, critic results | Evidence only |

### Default merge policy

- Auto-merge is allowed only into a **feature branch**.
- Merge to `main` is always manual.
- Risky issues can pass Tenet but still require human feature-branch merge.
- Dependent issues remain blocked until their blockers are actually merged into the feature branch.

### Ownership boundary

This is the most important compatibility and safety rule.

```text
Skills = interview, PRD creation, tracer decomposition, respec
authority provider = canonical planning state and cross-issue dependency graph
Gitea/Forgejo adapter = first authority-provider implementation
agent-issue snapshot = frozen execution contract for one attempt
harness-controller = state machine, policy, exact artifact generation, gates, authorization
CLI = primary human and automation interface to the controller
LocalAGI = optional adapter that requests controller operations through narrow tools
execution provider = execute one frozen contract and evaluate the result
Tenet adapter = first execution-provider implementation
LocalAI = model-serving layer selected by agent role
LocalRecall = optional advisory retrieval over stable documentation and history
```

Once a Skills-generated tracer issue exists in the authority provider:

- Tenet must not re-interview, re-spec, or re-decompose it.
- LocalAGI memory must not be used to infer current issue status.
- LocalAGI agent definitions must not contain workflow rules that are absent from the controller contract.
- LocalRecall must not be used to locate a likely execution contract when an exact path exists.
- The agent must query the authority provider through the controller for current state before every state-changing action.
- The controller must reject actions that are invalid for the current state, even if an agent requests them.

For the first Tenet adapter, Tenet's internal job DAG remains deliberately trivial:

```text
one authority-provider tracer issue = one frozen agent-issue snapshot = one Tenet registered dev job
```

The authority provider owns all cross-issue dependencies through normalized `blocked_by` and `blocks` edges. Tenet owns only the execution/evaluation state for the single current attempt. LocalAGI owns neither.

### LocalAGI deletion test

Before any LocalAGI integration is considered accepted, the workflow must pass this test:

```text
Stop LocalAGI.
Disable the LocalAGI adapter.
Run the same feature workflow through harnessctl.
Confirm issue selection, snapshot generation, Tenet registration, gates, PR creation, and state updates still work.
```

If this test fails, the design has accidentally made LocalAGI part of the harness instead of an optional operator surface.

### Boring Bridge strategy

Every external runtime should cross the same boring bridge:

```text
agent/runtime/client -> MCP or REST adapter -> harness-controller -> structured controller JSON
```

LocalAGI is one possible client of this bridge. LangGraph, PydanticAI, Codex, Claude, a small custom loop, n8n, or a plain shell script should be able to call the same controller operations without changing the controller policy, frozen snapshots, run contracts, PR bodies, or merge policy. Swapping Gitea for GitHub or Tenet for another execution engine should happen behind provider adapters.

The bridge rules are:

1. The controller owns business logic and workflow state.
2. MCP or REST tools are thin pass-through wrappers.
3. Tools do not interpret policy, maintain hidden state, or rewrite controller decisions.
4. Tools return controller-owned structured results, not agent-specific state.
5. Adapter prompts may explain how to use the tools, but they must not define workflow semantics.

Recommended tool response shape:

```json
{
  "operation": "run_preflight",
  "status": "policy_denied",
  "exit_code": 1,
  "run_id": "issue-123-attempt-001",
  "controller_state": "running",
  "policy_denial": {
    "code": "STALE_CONTRACT",
    "message": "Snapshot v1 is stale; current snapshot is v2."
  },
  "stdout": "",
  "stderr": "",
  "artifacts": []
}
```

Avoid returning only free-form raw output. Agents can summarize raw text, but they should not have to infer canonical state from it.

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
  start_dev
  run_preflight
  run_proof
  start_eval
  classify_run
  create_pr_if_allowed
  merge_pr_if_policy_allows
```

Every mutating operation should:

1. Read fresh canonical state.
2. Validate the requested transition.
3. Perform only the narrow operation requested.
4. Emit structured JSON.
5. Persist an audit link or comment through the authority provider when state changes.
6. Be idempotent where practical.

Example policy rejections:

```text
start_eval before preflight passed → INVALID_STATE
retry after retry budget exhausted → BUDGET_EXCEEDED
merge before required critics passed → POLICY_DENIED
merge into main through automation → POLICY_DENIED
use stale snapshot version → STALE_CONTRACT
```

### Optional LocalAGI adapter boundary

If LocalAGI is used, agents should receive narrow, capability-limited tools. Avoid exposing unrestricted shell, unrestricted authority-provider administration, raw execution-provider job primitives, or a raw merge command to the main operator agent.

The LocalAGI adapter should be deliberately boring:

```text
LocalAGI tool call -> controller operation -> structured controller JSON
```

Do not translate controller state into a LocalAGI-specific state machine. Do not require LocalAGI-specific metadata in authority-provider issues, agent-issue snapshots, execution artifacts, PR bodies, feature summaries, prompts, or agent profiles.

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
    - start_dev
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

LocalAI should be introduced as an inference service behind a model gateway, not as a new workflow manager.

The harness should route through its own model profile contract:

```text
agent role -> logical model profile -> model gateway -> provider adapter
```

The first gateway implementation can be simple and OpenAI-compatible:

```text
/v1/chat/completions or /v1/responses
```

But the controller and snapshots should record logical profiles, not hard-code LocalAI internals. The same profile should be swappable between LocalAI, a frontier provider, Codex, Claude, or another OpenAI-compatible server if the run policy allows it.

Prefer job-level routing across machines:

```text
Oracle LocalAI endpoint = development models
Denbuntu LocalAI endpoint = test/review models
JMapple LocalAI endpoint = overflow or specialized models
frontier provider = final or high-risk critic
```

Do not begin with distributed model sharding across all machines. First prove that each role can call one stable endpoint and that failures are visible and recoverable.

### Provider adapter boundary

Provider adapters are internal controller dependencies. Optional operator adapters such as LocalAGI, REST, MCP, n8n, or shell scripts must not call provider adapters directly.

```text
operator/client -> controller operation -> AuthorityProvider / ExecutionProvider adapters
```

Avoid:

```text
LocalAGI -> Gitea API
LocalAGI -> Tenet job primitive
n8n -> raw merge endpoint
agent -> provider-specific issue mutation
```

Prefer:

```text
LocalAGI -> prepare_next
LocalAGI -> start_dev
n8n -> run_next
agent -> create_pr_if_allowed
```

This keeps the controller interface deep: callers learn a small set of workflow operations, while provider complexity stays local to adapter implementations.

### Provider replaceability contract

Provider adapters are replaceable only if the controller contract remains unchanged.

An authority provider replacement is acceptable when the same controller test suite can run against a fake provider plus the real adapter and prove:

- feature issue lookup returns the same normalized `FeatureRecord`
- tracer issue lookup returns the same normalized `TracerRecord`
- mutable status maps to the configured `agent_status/*` vocabulary
- dependency edges normalize to `blocked_by` and `blocks`
- issue comments can store controller-owned audit summaries
- PR creation is idempotent for the same run
- PR target branch validation is controller-owned, not provider-owned
- provider URLs are treated as audit refs, while normalized issue keys drive policy

An execution provider replacement is acceptable when the same controller test suite can run against a fake provider plus the real adapter and prove:

- a frozen contract can be registered without re-planning
- the provider accepts exact required commands
- the provider accepts exact forbidden paths
- one controller run maps to one tracer attempt
- provider-internal retries are capped by controller policy
- development output returns structured evidence
- evaluation/critic output returns structured findings or can be normalized by the adapter
- provider logs and artifacts are linked from the controller run ledger

Provider replacement is not acceptable if swapping providers requires changes to:

- issue eligibility policy
- dependency-blocking policy
- snapshot authority rules
- proof-gate requirements
- PR target policy
- merge policy
- retry-budget ownership
- controller state transitions

The replacement test is:

```text
Run the same frozen tracer through:
  1. fake authority provider + fake execution provider
  2. Gitea/Forgejo authority adapter + fake execution provider
  3. fake authority provider + Tenet execution adapter in no-op mode
  4. the real first-adapter stack

The controller decisions and state transitions must match. Provider-specific URLs, artifact paths, and raw logs may differ.
```

### LocalRecall boundary

LocalRecall should be treated as an optional project RAG/index service, not as a strategic memory layer. Its job is to make stable project material easier to search. It should remain replaceable by markdown search, a repo-local index, SQLite/vector search, Postgres-backed RAG, or another retrieval service.

Good LocalRecall collections include:

- project architecture and testing doctrine
- coding standards
- stable framework documentation
- completed feature summaries
- selected historical failure reports
- operational runbooks

Do not use LocalRecall for:

- current authority-provider issue state
- current dependency eligibility
- selecting the active snapshot version
- retrieving acceptance criteria when an exact frozen contract exists
- deciding whether a PR is safe to merge

Exact execution paths must be injected directly into the task and execution job.

If LocalRecall is unavailable, the harness should continue using exact paths, authority-provider state, frozen snapshots, and normal repository search. Loss of LocalRecall may reduce convenience, but it must not block execution or change authority.

---

## Canonical Issue State Model

Use these issue states through the authority provider for mutable status. In the first Gitea/Forgejo adapter, they are labels. Static fields such as `blocked_by`, proof requirements, forbidden paths, and acceptance criteria can live in issue body sections or generated snapshots, but the frequently changing status should use the provider's native label/status mechanism where possible to avoid fragile issue-body rewrites.

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

authority_provider: gitea
canonical_issue_key:
  provider: gitea
  host: https://gitea.local
  owner: owner
  repo: repo
  number: 123
parent_prd_key:
  provider: gitea
  host: https://gitea.local
  owner: owner
  repo: repo
  number: 100

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
execution_provider: tenet
provider_internal_max_retries: 0
execution_invocation_mode: direct_registered_job

execution_artifact_paths:
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

This is the first `ExecutionProvider` adapter contract, not the controller's permanent execution model.

### How much Tenet can be abstracted

The controller can abstract most of Tenet if it treats Tenet as an execution adapter.

Provider-neutral concepts that should not mention Tenet in controller policy:

- frozen contract
- run id / run slug
- artifact bundle
- development job
- evaluation job
- required commands
- forbidden paths
- proof artifacts
- critic findings
- structured execution result
- retry budget
- failure category

Tenet-specific concepts that should stay inside the Tenet adapter:

- Tenet job registration primitive names
- Tenet artifact path field names
- `.tenet/runs/<run>/` layout
- `spec.md`, `scenarios.md`, `harness.md`, and `decomposition.md` as Tenet shim names
- Tenet internal retry flags
- Tenet critic invocation and raw critic result format
- Tenet's one-node DAG compatibility requirements

The controller should store a provider-neutral run contract and let the Tenet adapter render that contract into Tenet's required artifacts.

Recommended controller-owned run contract shape:

```yaml
run_id: issue-123-attempt-001
execution_provider: tenet
contract_ref: docs/agent-issues/ISSUE-123.v1.md
authority_issue:
  provider: gitea
  host: https://gitea.local
  owner: owner
  repo: repo
  number: 123
feature_branch: feature/login
agent_branch: agent/issue-123-login-form
required_commands:
  - pnpm lint
  - pnpm test
forbidden_paths:
  - .env
  - secrets/**
proof:
  required: true
  type: playwright
retry_policy:
  runner_retry_budget: 2
  provider_internal_max_retries: 0
```

Tenet adapter output from that contract:

```text
.tenet/runs/<run>/spec.md
.tenet/runs/<run>/scenarios.md
.tenet/runs/<run>/harness.md
.tenet/runs/<run>/decomposition.md
```

A future execution provider can be swapped in if it satisfies the same provider-neutral contract:

1. accepts an externally frozen contract
2. accepts exact required commands and forbidden paths
3. accepts one tracer at a time
4. can return structured development result evidence
5. can run or expose semantic critics/review
6. can keep provider-internal retries subordinate to the controller retry budget
7. does not create a competing feature plan or cross-issue scheduler

If a future engine has stronger guardrails but a different artifact layout, only the execution adapter should change. If it requires redefining issue eligibility, snapshot authority, dependency blocking, PR policy, or merge policy, it is not a clean replacement.

### Rule: bypass Tenet's planning phases after Skills decomposition

After Skills creates the PRD and authority-provider tracer issues, do not use Tenet's normal feature-planning flow for implementation work. In practical terms:

- Do not ask Tenet to interview the idea again.
- Do not ask Tenet to generate a second feature spec.
- Do not ask Tenet to decompose the feature into its own multi-job DAG.
- Do not use Tenet Full/Standard/Quick modes as the implementation path once a frozen Skills/authority-provider tracer exists.

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

This stage is where the plan is modified for compatibility with Tenet's spec/artifact system. Tenet still receives `spec`, `scenarios`, `harness`, and `decomposition` artifacts, but those files are generated from the Skills/authority-provider agent issue. They are compatibility shims, not a second canonical spec.

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

Do not run Tenet in a way that lets it re-interview, re-spec, or re-decompose the feature after Skills and the authority provider have already produced the tracer issue.

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
- Optional MCP or REST adapter schemas that any agent runtime, including LocalAGI, can call.
- Permission boundaries and structured error categories.

### What changes from Stage 9

No autonomous loop is added yet. The workflow becomes precise enough to implement and test without an LLM.

### Required contents

```markdown
# Harness Controller Contract

## Canonical inputs
- authority-provider feature/tracer issue
- frozen agent-issue snapshot
- exact execution-provider run path

## Valid transitions
- ready → running
- running → passed_preflight
- passed_preflight → passed_critics
- passed_critics → pr_created
- pr_created → merged_feature

## Controller operations
- inspect_feature
- prepare_next
- start_dev
- run_preflight
- run_proof
- start_eval
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
- Optional agent adapters can later consume the same operations without owning policy.

---

## Stage 11 — Build the minimal deterministic harness controller

### Goal

Automate issue selection, snapshot generation, execution-provider artifact generation, and development job registration without creating a custom agent framework.

### Additions

- `harnessctl` or `agent-harness` CLI.
- `AuthorityProvider` interface.
- Gitea/Forgejo authority adapter.
- Dependency-aware issue selection.
- Agent-issue snapshot generator.
- `ExecutionProvider` interface.
- Tenet execution adapter.
- Tenet shim artifact generator behind the Tenet adapter.
- Structured JSON outputs.

### What changes from Stage 10

The workflow now has executable policy code, with no dependency on LocalAGI or any other agent runtime.

### Minimum commands

```bash
harnessctl inspect-feature --feature login
harnessctl prepare-next --feature login
harnessctl start-dev --run issue-123-attempt-001
harnessctl get-run-state --run issue-123-attempt-001
```

### Responsibilities

1. Query the authority provider for candidate tracer issues.
2. Build the dependency graph from canonical issue data.
3. Select only an eligible issue.
4. Generate the frozen snapshot.
5. Generate exact execution-provider artifacts.
6. For the first Tenet adapter, validate that `decomposition.md` contains one job only.
7. Register exactly one execution-provider development job with exact paths.
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
- It generates a valid frozen contract and exact execution-provider artifacts.
- Tenet does not create a competing spec or multi-job DAG.
- All outputs are machine-readable enough for optional adapters and IaC health tests.

---

## Stage 12 — Add an optional LocalAGI adapter

### Goal

Expose the controller to LocalAGI only as a convenience layer. The controller and CLI remain the system of record and the primary workflow surface.

### Additions

- Optional LocalAGI deployment.
- One optional `harness_operator` agent.
- Thin MCP or REST adapter to the controller.
- Runtime status/streaming available to the operator, if useful.
- A required deletion test proving the workflow still works with LocalAGI stopped.

### What changes from Stage 11

Nothing about workflow semantics changes. A LocalAGI agent can request the same safe operations a human can run through `harnessctl`.

### Initial permission set

The first agent should receive only:

```text
inspect_feature
prepare_next
get_run_state
start_dev
```

It should not initially receive:

```text
create_pr
merge_pr
raw shell
unrestricted authority-provider write
raw execution-provider job primitive
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
If this agent is removed, the harnessctl workflow remains authoritative and complete.
```

### Compatibility test for Skills

If LocalAGI will run engineering Skills directly, test one existing `SKILL.md` package for:

- metadata parsing
- directory layout
- progressive disclosure
- referenced scripts/resources
- Git synchronization
- usability by both frontier planning agents and LocalAGI agents

If compatibility requires changing the canonical Skill format, do not do it. Add a small adapter or skip direct LocalAGI Skill execution.

### Deletion test

Run at least one end-to-end toy tracer with LocalAGI disabled:

```bash
harnessctl inspect-feature --feature login
harnessctl prepare-next --feature login
harnessctl start-dev --run issue-123-attempt-001
harnessctl run-preflight --run issue-123-attempt-001
harnessctl run-proof --run issue-123-attempt-001
harnessctl start-eval --run issue-123-attempt-001
harnessctl create-pr-if-allowed --run issue-123-attempt-001
```

The result must match the LocalAGI-mediated path except for LocalAGI-only UI/conversation logs.

### Exit criteria

- The CLI path remains complete and documented.
- LocalAGI can prepare and start one real execution-provider job through the controller, if enabled.
- LocalAGI cannot bypass dependency or state policy.
- Runtime UI/state is useful but clearly non-canonical.
- Removing LocalAGI does not require changing authority-provider issues, agent-issue snapshots, execution artifacts, controller state, PR bodies, or feature summaries.
- Prompts, agent profiles, model profiles, and permissions used by LocalAGI are recoverable from Git-controlled config.

---

## Stage 13 — Add deterministic merge preflight

### Goal

Enforce mechanical facts before any semantic critic or PR action.

### Additions

- `scripts/agent/merge-preflight.ts`
- `.tenet/runs/<run>/gate/merge-preflight.json`
- Controller operation `run_preflight`.
- Optional LocalAGI tool wrapper that returns the controller's result unchanged.

### Preflight checks

- Canonical issue exists.
- Correct snapshot version exists.
- Exact execution-provider artifacts exist.
- For the first Tenet adapter, Tenet shim artifacts exist.
- For the first Tenet adapter, Tenet decomposition contains exactly one job.
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
    "execution_artifacts_found": true,
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
- No adapter, including LocalAGI, can reinterpret a failed preflight as a pass.
- The controller updates or recommends the correct authority-provider failure state.

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

proof must pass before execution-provider E2E evaluation or PR creation.

### Exit criteria

- Required proof is generated at exact recorded paths.
- Missing proof receives a structured category.
- IaC can provision any browser/runtime dependencies reproducibly.

---

## Stage 15 — Add execution-provider evaluation and structured failure classification

### Goal

Run semantic critics only after deterministic gates pass and normalize their findings into the harness taxonomy.

### Additions

- Controller operation `start_eval`.
- `failure_triage` agent, dedicated classifier prompt, or CLI-invoked classifier.
- Structured classification schema.
- Clear distinction between deterministic facts and semantic recommendations.

### Classification inputs

```text
canonical authority-provider issue
frozen snapshot
execution-provider artifacts
merge-preflight.json
proof JSON
execution-provider critic findings
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

## Stage 16 — Add authority-provider state updates and audit links

### Goal

Make the authority provider reflect the authoritative harness state while preserving execution-provider logs and any optional adapter logs as supporting evidence.

### Additions

- AuthorityProvider write operations.
- Native or mapped `agent_status:*` labels.
- Comments linking issue, snapshot, run, gate results, proof, and critic summary.
- Idempotent update behavior.

### State updates

| Event | Authority-provider state |
|---|---|
| Controller selects issue | `running` |
| Preflight passes | `passed_preflight` |
| Gate/critic failure | category-based failure state |
| All critics pass | `passed_critics` |
| PR created | `pr_created` |
| Merge policy requires human | `awaiting_human_review` |
| Feature merge completes | `merged_feature` |

### Exit criteria

- The authority provider alone shows the current canonical state.
- LocalAGI restart, removal, or memory loss does not impair resumption.
- Every run is traceable from its issue and every issue links to its runs.

---

## Stage 17 — Add policy-controlled PR creation

### Goal

Create a PR only after deterministic gates and required semantic critics pass.

### Additions

- Controller operation `create_pr_if_allowed`.
- Branch push and authority-provider PR adapter.
- PR body template with complete evidence links.
- Optional LocalAGI access to the policy-wrapped operation, not raw PR administration.

### PR evidence

The PR body should include:

```text
canonical issue
snapshot path and version
execution run path
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
- Runner retry budget and provider-internal retry limit.

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
required execution-provider critics passed
PR target is the feature branch
no forbidden paths changed
all dependencies are actually merged
budget remains available
one-job execution contract remained intact
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
12. Missing execution-provider artifact.
13. Multi-job execution-provider decomposition, or multi-job Tenet decomposition for the first Tenet adapter.
14. Stale snapshot version.
15. An adapter requests an invalid transition.
16. An adapter requests raw merge bypass.
17. LocalAGI is deleted or the controller restarts mid-run.
18. Authority provider or execution provider is temporarily unavailable.

### Retry policy

```yaml
runner_retry_budget: 2
provider_internal_max_retries: 0
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
skills/engineering/triage-execution-failure/SKILL.md
skills/engineering/to-respec-issue/SKILL.md
skills/engineering/review-run-evidence/SKILL.md
```

### Skill roles

#### `to-agent-issue`

Generates the frozen snapshot and proposed execution-provider artifacts from the current canonical issue. The controller validates and commits the exact output paths and version. With the first Tenet adapter, those artifacts are Tenet shims.

#### `triage-tenet-failure`

Tenet-specific semantic failure recommendation skill for the first execution adapter.

#### `triage-execution-failure`

Provider-neutral semantic failure recommendation skill. It cannot directly overwrite deterministic gate categories.

#### `to-respec-issue`

Proposes replacement issues when the tracer itself is wrong. The controller and authority-provider adapter perform the canonical supersede and dependency rewiring operations.

#### `review-run-evidence`

Summarizes contract compliance, changed scope, tests, proof, critic output, and unresolved risks for a human or final frontier critic.

### Exit criteria

- Bad tracer bullets can be superseded without corrupting history.
- Skills are reusable through frontier planning workflows, CLI/controller execution, and LocalAGI only where compatible without changing the canonical format.
- Agent-generated proposals are validated before becoming canonical authority-provider changes.

---

## Stage 20 — Introduce LocalAI, role-based local models, and optional LocalRecall

### Goal

Replace selected frontier roles with local models only after the controller, CLI path, gates, and failure handling are reliable. LocalAGI integration is not a prerequisite.

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
authority-provider instance  # Gitea/Forgejo first; GitHub SaaS or another forge later
harness-controller
localagi-adapter          # optional convenience surface; not required for core workflow
localai-oracle
localai-denbuntu
localai-jmapple          # optional
localrecall              # optional/later
n8n                      # triggers/notifications only
execution-provider environment # Tenet worker first; may be colocated with controller or dev worker initially
```

## Configuration categories

The IaC analysis should account for:

- service images or reproducible installation versions
- service users and filesystem ownership
- persistent volumes and backup requirements
- exact repository/worktree locations
- authority provider type, URL, repository identity, labels/status mapping, dependency mapping, and API credentials
- optional LocalAGI agent definitions and enabled Skills repositories
- controller MCP/REST endpoint and authentication
- execution provider type, binary/version or endpoint, run-root paths, artifact schema, and eval/critic capabilities
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
  authority-provider token with only required repository permissions
  execution-provider credentials if required

LocalAGI:
  controller access token
  model-provider keys for assigned agents
  no unrestricted authority-provider admin token
  no production deployment credentials
  no unique workflow secrets that are unavailable to the CLI/controller path

LocalAI:
  normally no authority-provider credentials
  model registry credentials only if required

LocalRecall:
  database credentials
  no merge or authority-provider write credentials
```

## Network boundary

Prefer allowlisted communication:

```text
LocalAGI → harness-controller, when enabled
harness-controller → authority provider
harness-controller → execution provider
LocalAGI → LocalAI endpoint(s), when enabled
LocalAGI → LocalRecall, when enabled
n8n → harness-controller trigger endpoint
```

LocalAI and LocalRecall should not need direct write access to the authority provider.
The controller must not require inbound traffic from LocalAGI to operate.

## Health and readiness

At minimum, IaC should be able to verify:

```text
authority provider reachable and authenticated
controller can read repository state
controller CLI/MCP schema version matches expected version
optional LocalAGI adapter can list the allowed controller tools
core workflow still passes with LocalAGI disabled
execution provider can execute a no-op or toy registered job
LocalAI endpoint can load and answer with the configured model
LocalRecall can write/read a test document when enabled
persistent paths have correct ownership and free space
```

## Portability and swap tests

Run these tests before treating the architecture as portable:

```text
LocalAGI off:
  harnessctl can complete inspect, prepare, execution job registration, gates, PR creation, and authority-provider state updates.

LocalRecall off:
  exact contracts, authority-provider state, and repo-local search still let the run proceed.

LocalAI swapped:
  the same logical model profile can route to LocalAI, a frontier provider, or another OpenAI-compatible endpoint without changing the run contract.

MCP adapter replaced:
  a REST client or direct CLI invocation can call the same controller operations with equivalent structured results.

Prompt/profile restore:
  a fresh LocalAGI install can recreate agent behavior from Git-controlled prompts, profiles, model routing, and permission manifests.

Authority provider swapped:
  a fixture-backed adapter test can run the same controller workflow against Gitea/Forgejo and GitHub-style issue/PR semantics without changing controller policy.

Execution provider swapped:
  a fixture-backed adapter test can register a frozen contract, execute a no-op development job, return structured evidence, and run or simulate critics without changing controller policy.
```

These are not performance tests. They prove that the Local Stack is an implementation choice, not the foundation of the harness.

## Portability rule

Agent definitions, Skills, controller schemas, policy files, and model-routing profiles should live in Git wherever practical. LocalAGI-specific agent definitions are adapter configuration, not canonical harness configuration. Secrets, large model weights, transient run logs, and generated proof artifacts should not be embedded in IaC source.

---

# Final Target Workflow

After Stage 20, the desired human command is:

```bash
harnessctl run-next --feature login
```

The actual safe workflow is:

```text
1. Human, n8n, LocalAGI, or another optional adapter requests the next run.
2. Controller queries fresh authority-provider state.
3. Controller builds the dependency graph and selects eligible work.
4. Controller generates/version-checks the frozen agent-issue snapshot.
5. Controller generates exact execution-provider artifacts.
6. Controller registers exactly one development job.
7. The CLI/controller path advances the run; LocalAGI may report runtime progress if enabled.
8. The execution provider performs development using the assigned frontier or LocalAI-backed model.
9. Controller runs deterministic preflight.
10. Controller runs required proof.
11. Execution-provider critics and optional secondary reviewers run only after gates pass.
12. Failure classifier recommends semantic routing; controller enforces valid state.
13. Controller creates a feature-branch PR if all requirements pass.
14. Controller auto-merges only when explicit low-risk policy allows.
15. The authority provider records the canonical state and audit links.
16. Dependents unblock only after confirmed feature-branch merge.
17. Main remains human-reviewed and human-merged.
```

The operational shorthand is:

```text
Humans, scripts, or optional adapters request.
The controller validates.
The execution provider executes and evaluates.
LocalAI serves selected models.
The authority provider records truth.
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
canonical_epic:
  provider: gitea
  host: https://gitea.local
  owner: owner
  repo: repo
  number: 100
feature_branch: feature/login
merged_to_main_pr:
  provider: gitea
  host: https://gitea.local
  owner: owner
  repo: repo
  number: 500
tracer_issues:
  - provider: gitea
    host: https://gitea.local
    owner: owner
    repo: repo
    number: 123
  - provider: gitea
    host: https://gitea.local
    owner: owner
    repo: repo
    number: 124
external_refs:
  canonical_epic_url: gitea://gitea.local/owner/repo/issues/100
  merged_to_main_pr_url: gitea://gitea.local/owner/repo/pulls/500
```

3. Archive or remove active planning files:

```text
docs/prd/<feature>.md
docs/agent-issues/ISSUE-*.md
.tenet/runs/<feature>/*
```

4. Keep the authority provider as the full audit trail.
5. Keep the feature summary in the repo so future agents know where to look.

---

# Design Principles

1. **Build the controller and CLI first.**
   The harness must be useful, testable, and complete before any agent platform is attached.

2. **Treat LocalAGI as an optional adapter, not a platform dependency.**
   Its conversations, summaries, schedules, and runtime state are advisory and operational only. Deleting it must not change the workflow.

3. **Keep a CLI beneath every adapter tool.**
   The workflow must remain testable and recoverable without an LLM.

4. **Use the Boring Bridge.**
   LocalAGI, LangGraph, Codex, Claude, n8n, or a custom loop should all call the same MCP/REST/CLI-backed controller operations.

5. **Keep tools dumb and controller-owned.**
   Adapter tools pass requests to the controller and return structured controller results. They do not own policy, state, retries, or merge decisions.

6. **Keep portable configuration in Git.**
   Prompts, Skills, agent profiles, model-routing rules, controller schemas, and permission manifests should be recoverable without LocalAGI.

7. **Use capability-limited tools.**
   Expose policy-wrapped operations such as `merge_pr_if_policy_allows`, not unrestricted merge or shell access.

8. **Make provider replacement a controller test, not a rewrite.**
   Gitea/Forgejo, GitHub, Tenet, or a future execution engine should be proven through adapter tests against the same controller contract.

9. **Do not patch Tenet until necessary.**
   Use supported job primitives and a Tenet execution adapter first.

10. **Do not let the execution provider guess context.**
   Always pass exact artifact paths.

11. **Do not let the execution provider re-plan Skills/authority-provider work.**
   After a tracer exists, use one frozen snapshot and one registered execution job.

12. **Do not let the execution provider's DAG compete with the authority provider.**
   The authority provider owns cross-issue dependencies; the first Tenet adapter receives a one-node DAG.

13. **Do not let retry systems compound.**
   Keep provider-internal retries at `0` or `1`; let the controller own the product retry budget.

14. **Prefer deterministic gates before LLM critics.**
    Scripts verify facts; critics judge meaning.

15. **Do not let semantic agents override deterministic failures.**
    A failed forbidden-path, proof, dependency, or budget check remains failed.

16. **Do not make LocalRecall authoritative.**
    Use it as optional project RAG over stable doctrine and history, never current issue state or exact contract selection.

17. **Put LocalAI behind a model gateway.**
    Route by logical model profile, not by hard-coded LocalAI internals. LocalAI serves models; it does not own workflow state or merge decisions.

18. **Prefer job-level routing before distributed model sharding.**
    One reliable endpoint per role is easier to debug and automate.

19. **Do not make n8n source of truth.**
    It may trigger and notify, but the authority provider and the controller own state.

20. **Do not make failed runs disappear.**
    They are evidence and should remain linked to the canonical issue.

21. **Do not auto-merge risky work.**
    Passing critics is not the same as being safe to merge.

22. **Do not introduce local LLMs early.**
    First prove the workflow with frontier models through the same controller contract.

23. **Do not introduce multi-machine orchestration first.**
    One reliable LocalAI worker beats several unreliable endpoints.

24. **Do not treat the PRD as implementation authority after decomposition.**
    The tracer issue and frozen snapshot govern the attempt.

25. **Do not let stale files or memories confuse agents.**
    Version snapshots, inject exact paths, and archive completed feature planning artifacts.

26. **Make infrastructure boundaries explicit.**
    Services, secrets, volumes, health checks, network access, and upgrade paths should be reproducible through IaC.

27. **Keep main human-controlled.**
    Automation may merge eligible low-risk work only into feature branches.

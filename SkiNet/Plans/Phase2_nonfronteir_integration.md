# Local Model and Node Routing Framework

## Purpose

This document sketches a future routing layer for assigning tracer-bullet implementation tasks to local models and machines.

It is intentionally not part of the first build of the Skills + Tenet runner. The current plan remains:

```text
Skills/Gitea planning -> frozen agent issue -> Tenet one-job execution -> Codex/Claude first
```

Local model routing should be introduced only after the runner can reliably:

- create frozen agent-issue snapshots
- generate Tenet-compatible shim artifacts
- run one Tenet job from a snapshot
- run preflight/proof/critic gates
- create PRs and update Gitea state

The routing layer should then decide:

```text
Given this tracer issue, which model on which node should attempt it?
```

The model choice should be recorded in the agent-issue snapshot so each attempt is reproducible.

---

## Core Principle

Do not route by model hype. Route by task shape, risk, and required proof.

A model assignment should be based on:

- what kind of work the tracer actually requires
- how much ambiguity remains
- how risky failure would be
- whether the task needs broad reasoning, precise code edits, UI judgment, data correctness, or exhaustive testing
- which node can run the model locally without hidden LM Link spillover

The runner should treat local models as specialized workers, not as interchangeable generic agents.

---

## Snapshot Fields to Add Later

The existing agent-issue frontmatter already has `model_tier` and `risk_level`. When local model routing is introduced, add fields like:

```yaml
model_tier: local
risk_level: medium

task_profile:
  primary_domain: ui_state
  secondary_domains:
    - accessibility
    - local_storage
  complexity: small
  ambiguity: low
  blast_radius: low
  proof_surface: web_ui

model_routing:
  developer:
    node: oracle
    provider: lmstudio-oracle
    model: mistralai/devstral-small-2-2512
    profile: devstral
  reviewer:
    node: oracle
    provider: lmstudio-oracle
    model: qwen3-coder-30b-a3b-instruct
    profile: coder
  final_critic:
    node: frontier
    provider: codex
    model: codex
    required: false

local_model_policy:
  max_developer_attempts: 1
  allow_revised_spec_retry: true
  require_mechanical_gates_before_review: true
  require_final_human_review: false
```

The runner can initially fill these fields manually. Later it can classify automatically.

---

## Task Profiles

Use a small controlled vocabulary. Avoid one-off labels that become impossible to automate.

### `ui_static`

Mostly markup, layout, styling, simple display states.

Examples:

- settings page layout
- static dashboard cards
- responsive table shell
- empty/loading/error states

Good developer candidates:

- Devstral for simple UI with explicit acceptance criteria.
- Qwen3.6 for higher-polish single-screen UI where slower output is acceptable.
- Codex/frontier if the visual design is ambiguous or needs product taste.

Preferred critics:

- Qwen3-Coder for spec conformance.
- Playwright/e2e critic for actual rendered behavior.
- Frontier critic for high-polish product surfaces.

### `ui_state`

Interactive UI with client-side state, form validation, persistence, or event handling.

Examples:

- localStorage Kanban board
- multi-step form
- filter/search/sort UI
- settings editor

Observed model behavior:

- Qwen3.6 produced stronger static implementation quality but was slow.
- Devstral produced usable code faster but can make behavioral mistakes.
- Both need mechanical and e2e checks.

Good developer candidates:

- Devstral for small, explicit tracer bullets.
- Qwen3.6 for overnight quality pass when the UI state machine is important.
- Codex if the user will interactively iterate.

Required gates:

- JS/TS syntax
- banned API scan when applicable
- browser smoke
- Playwright interaction path
- event wiring checks if feasible

### `ux_product`

Work where user experience, product language, visual hierarchy, onboarding, or workflow ergonomics matter more than raw code manipulation.

Examples:

- redesigning a workflow
- improving copy and empty states
- first-run experience
- app navigation model

Good developer candidates:

- Frontier model first.
- Qwen3.6 only after a frontier model produces a precise spec and visual direction.
- Avoid Devstral as primary designer unless the UX requirements are already concrete.

Preferred critics:

- Frontier final critic.
- Playwright visual/e2e critic.

Routing rule:

Do not send ambiguous product design work directly to local models. Use local models for implementation after the design has been crystallized.

### `api_contract`

Backend routes, request/response behavior, auth boundaries, error envelopes, and integration contracts.

Examples:

- add endpoint
- enforce authorization rule
- update OpenAPI schema
- wire service method to route

Good developer candidates:

- Devstral for simple endpoints with clear tests.
- Qwen3.6 if the contract is subtle and enough time is available.
- Codex/frontier for auth/security-sensitive work.

Required gates:

- unit/integration tests
- schema validation
- negative tests
- auth boundary tests
- no silent success on malformed input

Preferred critics:

- Qwen3-Coder for implementation review.
- Test critic focused on oracle-leakage and missing negative cases.
- Frontier critic for public API/security-sensitive changes.

### `data_db`

Database schema, migrations, persistence invariants, data repair, concurrency, transactions.

Examples:

- migration
- index changes
- data backfill
- transaction boundary
- uniqueness/integrity enforcement

Good developer candidates:

- Codex/frontier for first implementation unless the task is very small.
- Devstral only for tightly constrained non-destructive changes.
- Qwen3.6 only overnight, with strong tests and review.

Required gates:

- migration dry run
- rollback story
- fixture tests
- integrity checks
- idempotency checks
- human review if production data is touched

Routing rule:

Local models should not be allowed to auto-merge database-affecting work without a final frontier or human review.

### `math_logic`

Algorithms, numeric correctness, parsing, ranking, scheduling, geometry, statistics, or any task where a small logical error can be hard to see.

Examples:

- recurrence/scheduler logic
- scoring function
- parser
- calculator
- route optimizer

Good developer candidates:

- Qwen3.6 if local-only and tests are strong.
- Codex/frontier for high-stakes or ambiguous logic.
- Devstral only when examples and expected outputs are explicit.

Required gates:

- golden examples
- property tests where possible
- edge cases
- boundary tests
- independent critic review

Preferred critics:

- Qwen3-Coder for code review.
- Frontier critic for mathematical reasoning.

### `refactor_mechanical`

Low-semantic, high-volume code movement with clear before/after constraints.

Examples:

- rename a public type
- move module
- split file
- update imports
- replace deprecated API

Good developer candidates:

- Devstral for small refactors.
- Qwen3-Coder as developer candidate worth testing.
- Codex if repo-wide safety is important.

Required gates:

- typecheck
- test suite
- diff-size gate
- forbidden path gate

Routing rule:

Prefer faster models when the compiler/test suite can strongly verify correctness.

### `test_harness`

Adding or strengthening tests, Playwright flows, CI commands, harness scripts, or proof artifacts.

Examples:

- add Playwright test
- add API integration test
- add runner preflight
- improve Tenet harness file generation

Good developer candidates:

- Qwen3-Coder.
- Codex/frontier for complex harness architecture.
- Devstral for simple test additions.

Required gates:

- run the new test and ensure it fails against broken behavior if possible
- check tests assert outcomes, not implementation
- avoid tautological tests

Preferred critics:

- Qwen3-Coder test critic.
- Frontier critic when tests are the main safety mechanism.

### `infra_ops`

Containers, systemd, networking, secrets handling, deployment, machine config.

Examples:

- docker-compose service
- systemd timer
- reverse proxy
- SSH key provisioning
- LM Studio node setup

Good developer candidates:

- Codex/frontier or human-guided Codex first.
- Local models only for low-risk docs or generated config after review.

Required gates:

- dry run
- idempotency check
- no secret exposure
- explicit rollback
- human review for destructive changes

Routing rule:

Do not let local models auto-apply infrastructure changes until the harness has mature safety gates.

### `docs_planning`

PRDs, issue decomposition, architecture notes, runbooks, respecs, summaries.

Good developer candidates:

- Frontier model.
- Qwen3-Coder for concise code-adjacent review.
- Devstral only for simple generated summaries.

Routing rule:

Planning truth should stay in Skills/Gitea. Local models can critique or summarize but should not become the source of truth.

---

## Complexity Buckets

Every tracer issue should receive a complexity bucket before routing.

### `tiny`

Expected effort:

- one file or one narrow surface
- no schema changes
- no new dependency
- easy mechanical proof

Local routing:

- Devstral is acceptable.
- Qwen3-Coder as developer is worth testing.
- Qwen3.6 is usually too slow unless quality matters more than throughput.

### `small`

Expected effort:

- one vertical slice
- two to five files
- clear tests/proof
- no broad architecture decisions

Local routing:

- Devstral developer + Qwen3-Coder reviewer is the default local-throughput option.
- Qwen3.6 developer + Qwen3-Coder reviewer is the quality option.

### `medium`

Expected effort:

- multiple modules
- integration behavior
- nontrivial user flow
- meaningful failure modes

Local routing:

- Split into smaller tracer bullets if possible.
- If not split, use Codex/frontier as developer or supervisor.
- Local models may implement sub-pieces only.

### `large`

Expected effort:

- broad feature
- architecture decisions
- uncertain spec
- data/security/infra risk

Local routing:

- Do not assign directly to local developer.
- Use Skills/frontier to decompose into smaller issues first.

---

## Risk Buckets

Risk is separate from complexity. A tiny migration can be high-risk.

### `low`

Safe to run local model with normal gates.

Examples:

- UI copy
- isolated form validation
- simple non-prod script

### `medium`

Local model may run, but final critic is required.

Examples:

- public API behavior
- business logic
- nontrivial UI state

### `high`

Local model may propose changes but should not auto-merge.

Examples:

- auth
- database migrations
- production infrastructure
- secrets
- billing
- destructive operations

---

## Current Model/Node Routing Defaults

These defaults are based on the `qwen36-task-eval` trials and should be treated as provisional.

### jmapple

Best current role:

- high-quality overnight local worker
- fast local reviewer when using Qwen3-Coder

Recommended assignments:

```yaml
jmapple_qwen36_quality_dev:
  node: jmapple
  model: qwen3.6-27b-ud-mlx
  best_for:
    - ui_state
    - small product-facing artifacts
    - quality-biased overnight runs
  avoid_for:
    - tight retry loops
    - broad ambiguous features
```

```yaml
jmapple_qwen3coder_reviewer:
  node: jmapple
  model: qwen3-coder-30b-a3b-instruct
  best_for:
    - review
    - spec tightening
    - final critic
    - test/harness critique
  candidate_for_future_test:
    - tiny developer tasks
    - refactor_mechanical
```

### oracle

Best current role:

- self-contained overnight worker candidate
- Devstral developer plus Qwen3-Coder reviewer
- slow quality-biased Qwen3.6 developer when jobs are very small and format gates are enforced

Recommended assignments:

```yaml
oracle_devstral_throughput_dev:
  node: oracle
  model: mistralai/devstral-small-2-2512
  best_for:
    - tiny
    - small
    - ui_static
    - ui_state with strong gates
    - simple api_contract
    - refactor_mechanical
  requires:
    - banned_api_scan
    - syntax_check
    - behavior_test_or_smoke
    - final_qwen3coder_review
  avoid_for:
    - high-risk database work
    - ambiguous UX/product design
    - auth/security without frontier review
```

```yaml
oracle_qwen3coder_reviewer:
  node: oracle
  model: qwen3-coder-30b-a3b-instruct
  best_for:
    - self-contained Oracle review loop
    - code critic
    - test critic
    - spec refinement
```

```yaml
oracle_qwen3coder_next_retired:
  node: oracle
  model: qwen/qwen3-coder-next
  profile: removed
  observed_result:
    trial: qwen36-task-eval/oracle-qwen36-coder-next-review
    mode: reviewer_only
    context: 8192
    gpu: off
    ram_used: about_45_gib
    review_time: 84.3s
    regular_qwen3coder_review_time: 53.5s
  current_status:
    - experimental
    - not_default_reviewer
  reason:
    - slower_than_regular_qwen3coder
    - not_clearly_better_on_bug_detection
    - produced_false_positives
  follow_up_results:
    qwen36_developer_task:
      elapsed: 270.0s
      result: rejected_by_gates
      issues:
        - used_confirm
        - missing_aria
        - missing_modal
        - missing_debounce
        - weaker_innerhtml_inline_onclick_rendering
    calcom_14943_reviewer_fixture:
      elapsed: 61.0s
      golden_recall: 2_of_2
      comparison: regular_qwen3coder_caught_2_of_2_in_11.1s
      verdict: regular_qwen3coder_remains_better_default
  current_status:
    - retired_from_oracle
    - deleted_from_lmstudio_models
    - do_not_route
  replacement:
    primary_reviewer: oracle_qwen3coder_reviewer
    backup_reviewer: oracle_devstral_throughput_dev
  avoid_for:
    - all_default_routing
    - routine_review
    - fast_tenet_inner_loop
    - default_developer
  redownload_only_if:
    - new_quant_or_harness_changes_expected_behavior
    - explicit_benchmark_retest_requested
```

```yaml
oracle_qwen36_quality_dev:
  node: oracle
  model: qwen3.6-27b@iq4_xs
  profile: qwen-fast
  preferred_reviewer: oracle_qwen3coder_reviewer
  backup_or_diversity_reviewer: oracle_devstral_throughput_dev
  best_for:
    - tiny
    - small
    - ui_state
    - quality-biased overnight attempts
    - local-only runs where jmapple should not be used
  observed_result:
    trial: qwen36-task-eval/oracle-only-qwen36-qwen3coder
    total_loop_time: 2019.6s
    first_pass: complete_raw_html_js_valid
    review_pass: 53.5s
    second_pass: js_valid_but_markdown_fenced_html
  requires:
    - output_format_check
    - syntax_check
    - browser_smoke_after_fence_cleanup_or_rejection
    - state_machine_review
    - final_qwen3coder_or_frontier_review
  avoid_for:
    - interactive_retry_loops
    - medium_or_large_features
    - tasks_without_clear_acceptance_criteria
```

```yaml
oracle_glm45_air_experimental:
  node: oracle
  model: glm-4.5-air
  profile: glm-air
  status:
    - downloaded
    - registered_in_lmstudio
    - unbenchmarked
  load_estimate:
    context: 8192
    gpu: off
    total_memory: about_55_84_gib
  intended_test_role:
    - ram_heavy_quality_experiment
    - possible_developer_or_deep_critic
  avoid_for:
    - default_routing_until_benchmarked
    - fast_inner_loop
```

### bluefin

Best current role:

- OpenCode control plane
- runner host
- source-of-truth coordinator

Recommended assignments:

```yaml
bluefin_runner:
  node: bluefin
  role:
    - opencode_web
    - tenet_runner
    - gitea_orchestration_client
    - lmstudio_endpoint_registry
  avoid_for:
    - heavy local model generation unless specifically tested
```

### denbuntu

Current role:

- pending fuller model tests
- likely useful for ROCm experiments once stable

Recommended assignments:

```yaml
denbuntu_candidate:
  node: denbuntu
  role:
    - future local model worker
  required_before_routing:
    - confirm ROCm acceleration
    - benchmark qwen/devstral/glm equivalents
    - add model-specific profiles
```

---

## Routing Matrix

| Task profile | Default local developer | Reviewer | Final critic | Notes |
| --- | --- | --- | --- | --- |
| `ui_static` | Devstral | Qwen3-Coder | Optional frontier | Good local target if spec is concrete. |
| `ui_state` | Devstral or Qwen3.6 | Qwen3-Coder | Frontier for complex UX | Devstral for throughput; Qwen3.6 for slow overnight quality only. Needs browser/e2e proof. |
| `ux_product` | Frontier/Codex | Qwen3-Coder | Frontier | Do not start local-only if product direction is unclear. |
| `api_contract` | Devstral for simple cases | Qwen3-Coder | Frontier for auth/public API | Needs negative tests. |
| `data_db` | Codex/frontier | Qwen3-Coder | Human/frontier | High-risk local-only should be blocked. |
| `math_logic` | Qwen3.6 or frontier | Qwen3-Coder | Frontier | Needs examples/property tests. |
| `refactor_mechanical` | Devstral or Qwen3-Coder | Qwen3-Coder | Optional | Compiler/test suite can carry proof. |
| `test_harness` | Qwen3-Coder | Qwen3-Coder | Frontier if safety-critical | Watch for tautological tests. Qwen3-Coder-Next is retired on Oracle; regular Qwen3-Coder is the local review baseline. |
| `infra_ops` | Codex/frontier | Qwen3-Coder | Human | No auto-apply for destructive changes. |
| `docs_planning` | Frontier | Qwen3-Coder | Human optional | Gitea remains source of truth. |

---

## Decision Algorithm

The runner can eventually implement a simple routing function:

```text
1. Read frozen agent issue.
2. Classify task_profile.primary_domain.
3. Assign complexity: tiny/small/medium/large.
4. Assign risk: low/medium/high.
5. Check proof surface and required commands.
6. If complexity is large, reject local routing and require respec/decomposition.
7. If risk is high, require frontier or human final review.
8. Pick developer model from routing matrix.
9. Pick reviewer model.
10. Record selected node/model/profile in snapshot frontmatter.
11. Run preflight confirming selected node is online and model profile loads.
```

Suggested pseudocode:

```python
def choose_route(issue):
    profile = classify_task_profile(issue)
    complexity = classify_complexity(issue)
    risk = classify_risk(issue)

    if complexity == "large":
        return "needs_respec_decompose"

    if profile in {"infra_ops", "data_db"} and risk != "low":
        return route(
            developer="codex_or_frontier",
            reviewer="qwen3coder",
            final_critic="human_or_frontier",
            auto_merge=False,
        )

    if profile == "ux_product" and issue.ambiguity != "low":
        return route(
            developer="frontier",
            reviewer="qwen3coder",
            final_critic="frontier",
            auto_merge=False,
        )

    if complexity in {"tiny", "small"} and risk == "low":
        return route(
            developer="oracle_devstral",
            reviewer="oracle_or_jmapple_qwen3coder",
            final_critic="qwen3coder",
            auto_merge=True,
        )

    if profile in {"math_logic", "ui_state"} and issue.quality_priority == "high":
        return route(
            developer="jmapple_qwen36",
            reviewer="jmapple_qwen3coder",
            final_critic="qwen3coder_or_frontier",
            auto_merge=False,
        )

    return route(
        developer="codex",
        reviewer="qwen3coder",
        final_critic="frontier_if_needed",
        auto_merge=False,
    )
```

---

## Required Gates by Route

Every local-model route needs cheap deterministic gates before expensive reviewer passes.

### Universal gates

- syntax/typecheck
- changed-file list
- forbidden-path scan
- required-command execution
- no secret diff
- proof artifact existence

### UI gates

- browser smoke
- Playwright happy path
- console error scan
- screenshot on desktop and mobile
- banned browser API scan when specified

### API gates

- route smoke
- negative request tests
- response body assertions
- auth/permission tests when relevant

### DB gates

- migration dry run
- rollback or forward-only decision recorded
- seed/fixture validation
- destructive-operation scan

### Local model specific gates

Based on current observations:

```yaml
devstral:
  required_gates:
    - banned_api_scan
    - event_wiring_smoke
    - escaping_rendering_check

qwen36:
  required_gates:
    - output_format_check
    - markdown_fence_rejection_or_cleanup
    - state_machine_review
    - second_pass_bug_review

glm47_flash:
  required_gates:
    - visible_content_check
  routing_status: disabled_until_content_output_fixed
```

---

## Attempt Strategy

Avoid unbounded local retry loops.

Recommended policy:

```yaml
local_attempt_policy:
  first_attempt:
    developer: selected_local_dev
    reviewer: selected_local_reviewer
  retry_1:
    if_failure: structural_or_spec_miss
    action: revised_spec_retry
  retry_2:
    if_failure: repeated_same_category
    action: needs_respec_or_frontier
```

In plain language:

- One local implementation attempt is normal.
- One revised-spec retry is acceptable.
- Repeated failure should become `needs_respec`, `awaiting_human_review`, or route to Codex/frontier.

Do not let a slow local model burn an entire night retrying the same misunderstanding.

---

## How This Fits the Existing Build Plan

This document belongs conceptually after the current Codex/Claude-first stages.

Local routing should be introduced only after:

1. agent-issue snapshots are stable
2. Tenet direct registered jobs work
3. runner preflight/proof gates work
4. Gitea status updates work
5. PR creation works
6. failure taxonomy and retry budget work

When introduced, the local model layer should not change source-of-truth rules.

The Gitea tracer remains canonical. The model routing fields only describe who attempts the frozen work.

---

## Open Questions

- Can Qwen3-Coder act as a sufficiently good developer for tiny/refactor tasks?
- Can Oracle Qwen3-Coder Next outperform Devstral or regular Qwen3-Coder enough to justify its size and CPU/RAM latency?
- Can GLM be configured to emit visible `content` reliably?
- Does Denbuntu ROCm make any of these models materially faster?
- Should the runner support parallel local critics on separate nodes, or keep critics sequential to avoid confusing evidence?
- How should model routing be updated over time as benchmark results accumulate?

---

## Near-Term Recommendation

For now, keep using Codex as the default developer while the harness is being built.

When local routing becomes useful, start with one conservative route:

```yaml
route_name: oracle_local_small_tracer
developer: oracle_devstral
reviewer: oracle_qwen3coder
final_critic: qwen3coder
allowed_profiles:
  - ui_static
  - simple_ui_state
  - simple_api_contract
  - refactor_mechanical
allowed_complexity:
  - tiny
  - small
allowed_risk:
  - low
requires:
  - mechanical_gates
  - final_review
auto_merge_to_feature: false_initially
```

Once that route succeeds repeatedly, add the slower quality-biased route:

```yaml
route_name: jmapple_quality_tracer
developer: jmapple_qwen36
reviewer: jmapple_qwen3coder
allowed_profiles:
  - ui_state
  - math_logic_with_strong_tests
  - small_product_artifact
allowed_complexity:
  - tiny
  - small
allowed_risk:
  - low
  - medium_with_frontier_final_review
auto_merge_to_feature: false
```

Then add an Oracle-only quality route only for cases where the work must stay on Oracle:

```yaml
route_name: oracle_qwen36_quality_tracer
developer: oracle_qwen36
reviewer: oracle_qwen3coder
allowed_profiles:
  - ui_state
  - math_logic_with_strong_tests
  - small_product_artifact
allowed_complexity:
  - tiny
  - small
allowed_risk:
  - low
  - medium_with_frontier_final_review
requires:
  - output_format_check
  - markdown_fence_rejection_or_cleanup
  - mechanical_gates
  - final_review
expected_loop_time: "about 34 minutes for the current synthetic UI task"
auto_merge_to_feature: false
```

Only after these conservative routes are reliable should the runner become a general local-model scheduler.

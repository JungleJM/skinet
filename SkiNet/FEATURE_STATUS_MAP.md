# SkiNet Feature Status Map

Source plan: `SkiNet/skills_tenet_localagi_runner_harness_plan_v0.3.md`

Status terms:

- `done`: implemented or manually proven enough to rely on for the next slice
- `building`: partially implemented; active controller work
- `manual proven`: proven manually; not automated in controller yet
- `next`: agreed next implementation milestone
- `planned`: in v0.3 plan; not implemented yet
- `later`: explicitly deferred in v0.3

## 0. System Goal

- Status: `building`
- Build a deterministic harness for agent-built software.
- Skills plan and review.
- Authority provider stores canonical issue/PR state.
- Controller owns workflow policy.
- Execution provider builds/evaluates one frozen tracer at a time.
- Gitea/Forgejo first authority adapter.
- Tenet first execution adapter.
- LocalAGI optional UI/agent surface only.
- LocalAI later model-serving layer.
- LocalRecall later advisory search/memory only.
- CLI must work without LocalAGI.

## 1. Planning / Ideation

- Status: `manual proven`
- Start with human idea.
- Use `/grill-me` when no existing docs/domain model.
- Use `/grill-with-docs` when existing docs/domain model should be maintained.
- Use Skills to clarify:
  - actor
  - problem
  - goals
  - non-goals
  - first tracer boundary
  - proof expectations
  - risks
- Output is planning material, not executable truth yet.

## 2. PRD / Feature Spec

- Status: `manual proven`
- Use `/to-spec`.
- Produce PRD/spec.
- Current first practice feature:
  - read-only Vikunja kanban viewer
  - fixture-backed first tracer
  - live Vikunja later
- PRD can live first as local markdown.
- Then copy/publish into Gitea epic issue.
- PRD is planning context.
- PRD stops being implementation authority after tracer issue/snapshot exists.

## 3. Tracer Bullet Decomposition

- Status: `manual proven`
- Use `/to-tickets`.
- Break PRD into small vertical tracer issues.
- Each tracer:
  - demoable
  - independently testable
  - has acceptance criteria
  - has proof requirements
  - has blockers/blocks edges
  - has risk/model hints
- Example practice tracers:
  - fixture-backed board shell
  - empty/loading/error states
  - live Vikunja read-only fetch

## 4. Authority Provider Canonical State

- Status: `planned`
- Authority provider stores mutable truth.
- First authority provider: private Gitea/Forgejo.
- Gitea canonical for:
  - feature epic issue
  - tracer issues
  - current tracer status
  - dependency edges
  - PRs
  - audit comments
  - merge history
- Controller domain model stays provider-neutral:
  - feature issue
  - tracer issue
  - issue key
  - status
  - dependency edge
  - PR
  - audit link
  - branch
- Gitea adapter maps Gitea labels/body/comments/PRs into domain records.

## 5. Issue State Vocabulary

- Status: `planned`
- Mutable status names:
  - `ready`
  - `running`
  - `passed_preflight`
  - `failed_retryable`
  - `blocked`
  - `needs_respec`
  - `awaiting_human_review`
  - `budget_exceeded`
  - `passed_critics`
  - `pr_created`
  - `merged_feature`
  - `superseded`
  - `abandoned`
- First Gitea mapping: labels like `agent_status/ready`.
- Happy path:
  - `ready`
  - `running`
  - `passed_preflight`
  - `passed_critics`
  - `pr_created`
  - `merged_feature`

## 6. Frozen Agent-Issue Snapshot

- Status: `manual proven`
- Snapshot path:
  - `docs/agent-issues/ISSUE-N.vX.md`
- Snapshot is execution contract for one attempt/spec version.
- Generated from authority-provider tracer issue.
- Contains strict frontmatter:
  - canonical issue key
  - parent PRD key
  - feature branch
  - agent branch
  - run slug/path
  - model tier
  - risk level
  - retry budget
  - execution provider
  - artifact paths
  - blocked_by / blocks
  - proof requirements
  - forbidden paths
  - required commands
- Authority rule:
  - tracer issue beats PRD
  - snapshot freezes one attempt
  - stale snapshots rejected

## 7. Controller / CLI

- Status: `building`
- CLI name: `harnessctl`.
- Controller owns:
  - eligibility
  - state transitions
  - run IDs
  - snapshot/version checks
  - proof gates
  - preflight gates
  - retry budget
  - PR policy
  - merge policy
  - structured evidence
- Current implemented commands:
  - `init-run`
  - `run-preflight`
  - `probe-proof-runner`
  - `run-proof`
  - `bundle-evidence`
- Planned commands:
  - `inspect-feature`
  - `prepare-next`
  - `start-dev`
  - `get-run-state`
  - `start-eval`
  - `run-code-review`
  - `review-evidence`
  - `classify`
  - `create-pr`
  - `merge-if-allowed`
  - final shorthand: `run-next`

## 8. Run Ledger / Storage

- Status: `done`
- Controller-owned durable run directory.
- Current role:
  - store run metadata
  - store preflight gate evidence
  - store proof evidence
  - store evidence bundle
  - make attempts inspectable/replayable
- Default path:
  - `SkiNet/runs/<run-id>/`
- Current layout:
  - `run.json`
  - `gate/preflight.json`
  - `proof/proof-runner-probe.json`
  - `proof/proof.json`
  - `evidence-bundle.json`
- Legacy explicit `--evidence-dir` still supported.

## 9. Work Selection / Queue

- Status: `planned`
- Controller selects eligible tracer.
- Selection rules:
  - exclude closed/superseded/abandoned/running/blocked
  - require all `blocked_by` issues to be `merged_feature`
  - prefer retryable issues still within budget
  - prefer work that unblocks most downstream issues
  - prefer higher priority
  - prefer lower risk when tied
  - mark over-budget as `budget_exceeded`
- Parallelism:
  - independent ready tracers can run in parallel
  - blocked tracers wait for blockers merged to feature branch
  - risky/manual-review blockers keep dependents blocked until merge
  - contention failures retry later

## 10. TDD / Test Expectations

- Status: `planned`
- Skills may use `/tdd`.
- Tracer contract should declare required tests/proof.
- Desired discipline:
  - RED: failing test/proof describes required behavior
  - GREEN: implementation passes required checks
  - REFACTOR: only after behavior/proof holds
- Controller does not trust claims.
- Controller runs declared commands and records evidence.

## 11. Preflight Gate

- Status: `building`
- Current command: `harnessctl run-preflight`.
- Current behavior:
  - runs supplied commands in order
  - records command/cwd/exit/stdout/stderr/timestamps
  - fails on first failed command by default
  - supports `--keep-going`
  - writes `gate/preflight.json`
  - evidence bundle reads preflight status
- Planned richer checks include:
  - canonical issue exists
  - snapshot current
  - execution artifacts exist
  - Tenet shim artifacts exist for Tenet adapter
  - Tenet decomposition is one node
  - acceptance criteria present
  - required commands present
  - dependencies merged
  - branch naming valid
  - forbidden paths unchanged
  - secret scan passes
  - worktree expected
  - retry/time/cost budget remains
  - required build/test/typecheck commands pass
- Output: structured JSON preflight evidence.
- Failure cannot be reinterpreted by agent adapter.

## 12. Preview Provider

- Status: `planned`
- PreviewProvider creates or locates URL for UI proof.
- Supported concepts:
  - localhost
  - tailnet/Tailscale
  - LAN
  - deployment preview
  - static preview/other configured provider
- Tailscale is operator convenience, not core dependency.
- Localhost remains default portable path.

## 13. Proof Runner

- Status: `building`
- ProofRunner runs Playwright or other proof tool.
- Current implemented:
  - preview URL classification
  - proof-runner probe
  - safe proof first
  - elevated retry only when allowed and sandbox failure classified
  - JSON evidence
- Planned:
  - cache capabilities by host/OS/runner image/Codex/Tenet/browser version
  - exact proof artifact paths
  - reports/traces/screenshots
  - richer proof bundle integration
- Security rule:
  - use safest runner first
  - elevated browser proof only after classified safe-mode failure
  - record both safe and elevated attempts

## 14. Tenet Handoff

- Status: `planned`
- Tenet is first execution provider.
- Tenet does implementation/eval for one frozen tracer attempt.
- Tenet does not:
  - re-interview
  - re-spec
  - re-decompose feature
  - create competing cross-issue DAG
- Controller prepares Tenet-compatible shim artifacts:
  - `.tenet/runs/<run>/spec.md`
  - `.tenet/runs/<run>/scenarios.md`
  - `.tenet/runs/<run>/harness.md`
  - `.tenet/runs/<run>/decomposition.md`
- Shim meanings:
  - `spec.md`: frozen issue plus PRD context and authority rules
  - `scenarios.md`: acceptance criteria, anti-scenarios, proof expectations
  - `harness.md`: commands, forbidden paths, testing doctrine, merge/budget policy
  - `decomposition.md`: one-node Tenet DAG only
- Controller registers exactly one Tenet dev job.
- Use low Tenet internal retries:
  - default `provider_internal_max_retries: 0`
- Controller owns product retry budget.

## 15. Tenet Development Stage

- Status: `planned`
- Controller calls ExecutionProvider.
- First adapter calls Tenet primitives:
  - register dev job
  - start dev job
  - get job result
- Tenet produces implementation attempt.
- Output is evidence/proposed code, not canonical state.
- Working tree/branch contains proposed change.
- Stop before eval if deterministic preflight/proof fails.

## 16. Tenet Evaluation / Critics

- Status: `planned`
- Critics run after deterministic gates pass.
- First execution-provider critics: Tenet eval.
- Critic types in plan:
  - code critic
  - test critic
  - interaction/e2e critic
- Critic output normalized into structured evidence.
- Critics are semantic signals, not final authority.

## 17. Upstream Code Review Skill

- Status: `planned`
- Use upstream `/code-review`.
- Role:
  - Standards review
  - Spec review
- Not full acceptance gate.
- Feeds evidence bundle.
- SkiNet acceptance also requires:
  - preflight
  - proof
  - execution-provider critics
  - PR/authority-provider interop
  - controller state transition

## 18. PR Agent / Secondary Review

- Status: `planned`
- PR Agent optional evidence producer.
- May review:
  - PR description quality
  - changed-file summary
  - labels
  - reviewer comments
  - provider interoperability
- Must not own:
  - merge policy
  - canonical state
  - status transition

## 19. Evidence Bundle

- Status: `building`
- Current bundle includes:
  - proof-runner probe status
  - proof status
  - contract ref
  - branch/commit ref
  - recommended next action
- Planned bundle includes:
  - preflight
  - proof
  - execution-provider critics
  - `/code-review`
  - PR Agent / PR interop
  - failure classification
  - unresolved risks
  - recommended controller state
- Controller state changes based on typed evidence fields, not prose.

## 20. Failure Categories

- Status: `planned`
- Planned taxonomy:
  - `product_bug`
  - `test_bug`
  - `harness_bug`
  - `evidence_mismatch`
  - `contention`
  - `scope_conflict`
  - `forbidden_path_changed`
  - `missing_proof`
  - `dependency_blocked`
  - `budget_exceeded`
- Deterministic failures assigned by scripts.
- Ambiguous semantic failures assigned by classifier or triage skill.
- Until classifier exists, smaller manual taxonomy:
  - `product_bug`
  - `test_bug`
  - `harness_bug`
  - `scope_conflict`
  - `awaiting_human_review`

## 21. Failure Routing / Respec

- Status: `planned`
- If product bug:
  - retry same issue with critic findings, if budget remains
- If test bug:
  - mark `needs_respec` or create test-fix issue
- If harness bug:
  - mark `blocked`
  - create harness-fix issue
- If evidence mismatch:
  - retry proof/preflight once
  - repeated mismatch -> `awaiting_human_review`
- If contention:
  - retry later after conflicting work settles
- If scope conflict:
  - stop
  - mark `needs_respec` or `awaiting_human_review`
- If forbidden path changed:
  - stop
  - mark `awaiting_human_review`
- If missing proof:
  - retry if likely forgotten
  - otherwise `needs_respec`
- If dependency blocked:
  - do not run
  - keep `blocked`
- If budget exceeded:
  - stop
  - mark `budget_exceeded`
- Respec flow:
  - wrapper skill proposes replacement issue
  - controller validates
  - authority provider supersedes old issue
  - dependencies rewired
  - new issue enters production queue according to blockers/priority/risk

## 22. SkiNet Wrapper Skills

- Status: `planned`
- Planned wrapper skills:
  - `to-agent-issue`
  - `prepare-execution`
  - `start-execution`
  - `triage-tenet-failure`
  - `triage-execution-failure`
  - `to-respec-issue`
  - `review-run-evidence`
- Purpose:
  - surround upstream Skills
  - translate outputs into contracts/evidence/recommendations
  - keep upstream Pocock Skills Tenet/Gitea/SkiNet agnostic
- Controller validates before canonical changes.

## 23. PR Creation

- Status: `planned`
- Controller operation: `create_pr_if_allowed`.
- Creates PR only after required gates/critics pass.
- PR target: feature branch only, never `main`.
- PR body includes:
  - canonical issue
  - snapshot path/version
  - execution run path
  - changed scope summary
  - commands/results
  - preflight result
  - proof artifact paths
  - critic results
  - failure/retry history
- Idempotent: retry does not create duplicate PRs.

## 24. Merge Policy

- Status: `planned`
- Auto-merge only into feature branch.
- Main is always human-only merge.
- Auto-merge requirements:
  - `auto_merge_to_feature: true`
  - `manual_review_required: false`
  - `risk_level: low`
  - preflight passed
  - proof passed or not required
  - required critics passed
  - PR targets feature branch
  - forbidden paths unchanged
  - dependencies merged
  - budget remains
  - one-job execution contract intact
- Never auto-merge:
  - security/auth policy
  - production infra
  - secrets
  - migrations
  - permissions
  - billing
  - destructive data paths
  - major dependency upgrades

## 25. Success Path Back To Gitea

- Status: `planned`
- Authority provider updated with canonical state.
- Issue comments link:
  - issue
  - snapshot
  - run
  - gate results
  - proof
  - critics
  - PR
  - audit summary
- State updates:
  - selected -> `running`
  - preflight passed -> `passed_preflight`
  - critics passed -> `passed_critics`
  - PR created -> `pr_created`
  - manual review needed -> `awaiting_human_review`
  - feature merge confirmed -> `merged_feature`
- Dependents unblock only after confirmed feature-branch merge.
- If builder/human wants change:
  - change request becomes issue update, respec proposal, or new tracer
  - controller validates allowed state transition
  - authority provider records canonical change

## 26. Completed Feature Finalization

- Status: `planned`
- After whole feature branch manually merges to main:
  - generate `docs/features/<feature-slug>.md`
  - include canonical epic, feature branch, main PR, tracer issues
  - archive/remove active planning files as appropriate
  - keep Gitea as full audit trail
  - keep repo feature summary for future agents

## 27. Optional LocalAGI Adapter

- Status: `later`
- Thin MCP/REST adapter over controller.
- LocalAGI may request controller operations.
- LocalAGI must not own:
  - policy
  - state
  - artifact format
  - retry behavior
  - merge authority
- Initial tools only:
  - `inspect_feature`
  - `prepare_next`
  - `get_run_state`
  - `start_dev`
- Deletion test required:
  - same workflow passes with LocalAGI disabled.

## 28. LocalAI / Local Models

- Status: `later`
- Introduce only after controller/gates/failures reliable.
- LocalAI serves models behind logical profiles.
- Route by task shape/risk/proof surface.
- Frontier critics remain initially.
- Local models may handle low-risk work later.
- Endpoint failure must not corrupt state.
- No distributed model sharding first.

## 29. LocalRecall

- Status: `later`
- Advisory search/memory only.
- Good collections:
  - architecture docs
  - testing doctrine
  - coding standards
  - completed feature summaries
  - selected historical failures
  - runbooks
- Never source of truth for:
  - current issue state
  - dependency eligibility
  - snapshot version
  - acceptance criteria when exact contract exists
  - merge authorization

## 30. n8n / External Triggers

- Status: `later`
- Triggers/notifications only.
- May call controller.
- Must not own scheduler truth, state, or merge authority.

## 31. IaC / Deployment Boundary

- Status: `later`
- Treat harness as deployable units:
  - authority provider
  - harness controller
  - optional LocalAGI adapter
  - LocalAI nodes
  - optional LocalRecall
  - n8n
  - execution-provider environment
- Git-controlled config:
  - prompts
  - Skills
  - agent profiles
  - model profiles
  - controller schemas
  - policy rules
  - permission manifests
- Secrets outside Git.
- Health checks prove:
  - authority reachable
  - controller can read repo state
  - schema versions match
  - execution provider can run no-op job
  - LocalAGI-off path works
  - optional services are advisory.

## 32. Current Concrete Practice Target

- Status: `done for first tracer`
- Repo: `/Users/jmath/Documents/code/skinet-test-tracer`
- Feature: fixture-backed read-only Vikunja-style kanban board viewer.
- Branch: `agent/issue-2-fixture-board-shell`
- Implemented behavior:
  - project title from fixtures
  - three columns
  - cards
  - optional assignee/due date
  - no Vikunja/API calls
  - mobile horizontal reachability
  - desktop non-overlap
- Proof passed per `PROGRESS.md`:
  - `npm run build`
  - `npm test`
  - `npm run test:e2e`

## 33. Current Implemented Harness Slice

- Status: `done`
- Files under `SkiNet/harness/`.
- Commands:
  - `init-run`
  - `run-preflight`
  - `probe-proof-runner`
  - `run-proof`
  - `bundle-evidence`
- Tests:
  - run metadata/directory creation
  - preflight pass/fail/keep-going behavior
  - proof classification
  - preview classification
  - safe/elevated proof behavior
  - probe behavior
  - bundle pass/incomplete/run-directory behavior
- Known scope:
  - local controller run ledger
  - preflight command runner
  - proof/evidence
  - no Tenet adapter yet
  - no Gitea adapter yet

## 34. Next Milestone

- Status: `next`
- Name: Tenet Shim Artifact Generation.
- Build:
  - generate `.tenet/runs/<run>/spec.md`
  - generate `.tenet/runs/<run>/scenarios.md`
  - generate `.tenet/runs/<run>/harness.md`
  - generate `.tenet/runs/<run>/decomposition.md`
  - validate one-node decomposition
  - keep artifacts as Tenet compatibility shims
- Not included yet:
  - Gitea write adapter
  - Tenet job start
  - PR creation
  - auto-merge
  - LocalAGI
  - LocalAI

# Stage 1-5 Manual Runbook

This runbook turns the first part of `skills_tenet_localagi_runner_harness_plan_v2.md` into a concrete manual path.

Scope:

- Use Matt Pocock Skills for planning.
- Use the self-hosted Gitea repository as canonical issue state.
- Use a small practice project in a separate repository.
- Prepare Tenet-compatible run artifacts.
- Stop before starting the Tenet development job.

Out of scope for this pass:

- No LocalAGI.
- No LocalAI.
- No LocalRecall.
- No controller implementation.
- No automation around Gitea state.
- No Tenet job execution yet.

## Decisions

### Where Skills run

Run the Matt Pocock Skills from this planning repository:

```bash
cd /Users/jmath/Documents/code/skinet
```

Reason: this repository contains the installed Skills package:

```text
.agents/skills/
skills-lock.json
```

The practice app repository is only the target project for the generated PRD, tracer issue snapshots, Tenet artifacts, and eventual code. It does not need its own copy of the Skills package for this first manual pass.

Current repo reality:

- `skinet` is the planning and harness-design repository.
- `skinet` currently has no application code for the Vikunja practice app.
- The meaningful local content here is the Skills installation, Tenet MCP config, and SkiNet planning docs.
- `skinet-test-tracer` is the separate practice app repository where the PRD and later code will live.

Use this Skills sequence:

```text
/grill-me
/to-spec
/to-tickets
```

Why this sequence:

- `/ask-matt` is only a router. Its installed guidance says the "idea -> ship" flow starts with `/grill-me` when there is no codebase.
- `/grill-with-docs` is not the right first step here because there is no existing application codebase or domain docs to maintain for the Vikunja app yet.
- `/to-spec` turns the conversation into the PRD/spec after the idea has been sharpened.
- `/to-tickets` breaks that spec into tracer-bullet tickets with blocking edges.
- `/implement` is not part of this Stage 1-5 planning pass. It belongs later, when a single approved tracer is ready to build.

Do not expect these Skills to run as shell commands. Invoke them in the Codex/agent chat while the active workspace is `/Users/jmath/Documents/code/skinet`.

### Practice repository

Use the Gitea test repository as a separate practice project:

```text
ssh://git@appliedsci.tail90eacc.ts.net:411/gitea_admin/skinet-test-tracer.git
```

Keep it outside this planning repo, for example:

```bash
cd /Users/jmath/Documents/code
git clone ssh://git@appliedsci.tail90eacc.ts.net:411/gitea_admin/skinet-test-tracer.git
cd skinet-test-tracer
```

If the repository has no default branch yet, bootstrap it:

```bash
printf '# skinet-test-tracer\n' > README.md
git add README.md
git commit -m 'Initialize practice tracer repo'
git branch -M main
git push -u origin main
```

Reason: this keeps Tenet practice artifacts, branches, and experimental app code out of the harness-planning repository while still using your real Gitea instance.

### First feature

Use a read-only Vikunja kanban board viewer as the first feature.

Reason: Vikunja's API shape should be easier to constrain into two or three tracer bullets than a CalDAV calendar. CalDAV quickly introduces discovery, XML, auth variations, recurrence, timezone handling, and sync semantics. Those are useful later, but they are too noisy for the first Skills/Gitea/Tenet compatibility trial.

Initial feature:

```text
Display one configured Vikunja project as a read-only kanban board.
```

Keep credentials and live API calls out of the first tracer if possible. Start with a tiny fixture-backed UI, then add the real API as a later tracer.

### PRD location

Create the first PRD as a local file first:

```text
docs/prd/vikunja-kanban-viewer.md
```

Then copy the accepted PRD into the Gitea epic issue in Stage 3.

### Gitea label namespace

Use slash-prefixed status labels:

```text
agent_status/ready
agent_status/running
agent_status/passed_preflight
agent_status/failed_retryable
agent_status/blocked
agent_status/needs_respec
agent_status/awaiting_human_review
agent_status/budget_exceeded
agent_status/passed_critics
agent_status/pr_created
agent_status/merged_feature
agent_status/superseded
agent_status/abandoned
```

Also create these initial labels:

```text
agent/type/epic
agent/type/tracer
risk/low
risk/medium
risk/high
model_tier/codex_first
```

### Feature branch

Create the feature branch before making the first tracer issue executable:

```text
feature/vikunja-kanban-viewer
```

## Stage 1 - Verify Skills And Tenet Separately

Goal: prove the planning skillchain and Tenet installation work independently.

### 1. Verify Matt Pocock skills are installed

In the planning repo:

```bash
cd /Users/jmath/Documents/code/skinet
test -f skills-lock.json
test -f .agents/skills/to-spec/SKILL.md
test -f .agents/skills/to-tickets/SKILL.md
test -f .agents/skills/grill-me/SKILL.md
```

Expected result: all files exist.

### 2. Verify Tenet is installed

```bash
tenet --help
tenet serve --help
```

Expected result: both commands print help or usage output.

### 3. Verify the configured Tenet MCP command

The planning repo currently contains:

```json
{
  "mcp": {
    "tenet": {
      "type": "local",
      "command": ["tenet", "serve"]
    }
  }
}
```

Start only a smoke test. Do not run a real Tenet development job yet:

```bash
tenet serve
```

Expected result: the server starts without crashing. Stop it after confirming startup.

### 4. Create or clone the practice repo

```bash
cd /Users/jmath/Documents/code
git clone ssh://git@appliedsci.tail90eacc.ts.net:411/gitea_admin/skinet-test-tracer.git
cd skinet-test-tracer
```

If clone succeeds but the repo is empty, bootstrap `main` using the commands in "Practice repository".

### 5. Do a tiny non-Tenet sanity change

```bash
mkdir -p docs
printf '# Notes\n' > docs/notes.md
git add docs/notes.md
git commit -m 'Add practice notes'
git push
```

Expected result: SSH push to Gitea works.

### Stage 1 exit criteria

- Matt Pocock Skills are present in the planning repo.
- `tenet` is installed and can start its server.
- The practice Gitea repo can be cloned and pushed.
- No Tenet development job has been started.

## Stage 2 - Use Skills On The Small Feature

Goal: create a real PRD and tracer-bullet breakdown for the Vikunja board viewer.

Run the Skills conversation from the planning repo:

```bash
cd /Users/jmath/Documents/code/skinet
```

### 1. Sharpen the idea with `/grill-me`

Invoke:

```text
/grill-me
```

Use this as the starting feature statement:

```text
I want a small practice feature for the SkiNet harness. Build a read-only web app that displays one configured Vikunja project as a kanban board. The first implementation should be fixture-backed so the harness can prove UI behavior without requiring live credentials. Later tracer bullets can add live Vikunja API loading. There is no existing app code yet; this is a new tiny practice app in a separate Gitea repo.
```

Answer the grilling questions until the shape is clear enough to write a PRD. Keep steering toward a small first tracer, not a complete Vikunja client.

### 2. Convert the conversation into a PRD with `/to-spec`

Invoke:

```text
/to-spec
```

Important adjustment for this manual pass:

- The installed `/to-spec` skill says it publishes to the configured project issue tracker.
- For Stage 2, do not require automatic publishing.
- Ask it to produce the spec content for a local file first.
- The file will be created in the practice repo as `docs/prd/vikunja-kanban-viewer.md`.

Use this instruction with `/to-spec`:

```text
Produce the PRD/spec content only. Do not publish to an issue tracker yet. This repo is the Skills/harness planning repo, not the app repo. The output will be saved manually into /Users/jmath/Documents/code/skinet-test-tracer/docs/prd/vikunja-kanban-viewer.md.
```

### PRD constraints

The PRD should explicitly say:

- The app is read-only.
- The first tracer uses checked-in fixture data.
- No secrets are committed.
- No writes are made to Vikunja.
- The UI shows columns and cards from one project.
- The feature is complete only when a human can see a board-like view and a test can verify the rendered columns/cards.

### 3. Break the PRD into tracer tickets with `/to-tickets`

Invoke:

```text
/to-tickets
```

Important adjustment for this manual pass:

- The installed `/to-tickets` skill can publish either local markdown files or real tracker issues, depending on setup.
- For Stage 2, ask for the proposed ticket breakdown only.
- In Stage 3, manually create the Gitea epic and tracer issues from the approved breakdown.

Use this instruction with `/to-tickets`:

```text
Break the Vikunja kanban viewer PRD into two or three tracer-bullet tickets. Do not publish them yet. Show the ticket titles, blocking edges, delivered behavior, and acceptance criteria so I can manually create the Gitea issues in Stage 3.
```

Suggested tracer bullets if the skill output needs steering:

Create two or three tracers, not more:

```text
1. Fixture-backed board shell
   Render a configured project board from checked-in fixture JSON.

2. Empty, loading, and error states
   Add explicit display states around board loading without calling Vikunja yet.

3. Live Vikunja read-only fetch
   Load the configured project from Vikunja using environment-injected credentials.
```

The first Tenet preparation should use tracer 1 only.

### 4. Save the PRD into the practice repo

After `/to-spec` output is accepted, switch to the practice repo:

```bash
cd /Users/jmath/Documents/code/skinet-test-tracer
mkdir -p docs/prd
```

Create:

```text
docs/prd/vikunja-kanban-viewer.md
```

Suggested sections:

```markdown
# Vikunja Kanban Viewer PRD

## Problem
## Goals
## Non-Goals
## User Flow
## Tracer Bullets
## Acceptance Criteria
## Risks
## Proof Plan
```

Commit the PRD:

```bash
git add docs/prd/vikunja-kanban-viewer.md
git commit -m 'Add Vikunja kanban viewer PRD'
git push
```

### Stage 2 exit criteria

- `docs/prd/vikunja-kanban-viewer.md` exists.
- It contains two or three tracer bullets.
- The first tracer is fixture-backed, narrow, demoable, and independently testable.
- The tracer breakdown came from the installed Matt Pocock Skills flow: `/grill-me`, `/to-spec`, then `/to-tickets`.

## Stage 3 - Promote PRD And Tracers Into Gitea

Goal: make Gitea the canonical source of truth.

### 1. Create the feature branch

In the practice repo:

```bash
git checkout main
git pull --ff-only
git checkout -b feature/vikunja-kanban-viewer
git push -u origin feature/vikunja-kanban-viewer
git checkout main
```

### 2. Create labels

In Gitea, create the labels listed in "Gitea label namespace".

At minimum, create:

```text
agent_status/ready
agent_status/blocked
agent_status/merged_feature
agent/type/epic
agent/type/tracer
risk/low
model_tier/codex_first
```

### 3. Check whether issue dependencies are enabled

Gitea supports issue dependencies when the instance/repository has dependencies enabled.

Things to check in the Gitea UI:

- Open or create a test issue.
- Look for a Dependencies section in the issue sidebar.
- Try adding another issue as a blocker or dependency.

Instance config flags to check on the server if the UI does not show dependencies:

```ini
[repository]
DEFAULT_ENABLE_DEPENDENCIES = true
ALLOW_CROSS_REPOSITORY_DEPENDENCIES = true
```

If you can access the repository settings UI, also check whether issue dependencies can be enabled per repository.

Acceptance rule for this project:

- Prefer native Gitea dependencies if available.
- If native dependencies are not visible or not convenient, use the markdown fallback below.
- Even if native dependencies work, also include the markdown sections during this early manual phase so the future controller has stable text to parse.

### 4. Create the epic issue

Create one Gitea issue:

```text
Title: Epic: Vikunja kanban viewer
Labels: agent/type/epic
```

Issue body:

```markdown
## PRD

Paste or summarize docs/prd/vikunja-kanban-viewer.md.

## Feature branch

feature/vikunja-kanban-viewer

## Tracers

- Fixture-backed board shell
- Empty, loading, and error states
- Live Vikunja read-only fetch
```

Record the issue number. The examples below assume it is `#1`.

### 5. Create two or three tracer issues

Tracer 1:

```text
Title: Fixture-backed board shell
Labels: agent/type/tracer, agent_status/ready, risk/low, model_tier/codex_first
```

Body:

```markdown
## Parent

gitea://appliedsci.tail90eacc.ts.net/gitea_admin/skinet-test-tracer/issues/1

## Feature branch

feature/vikunja-kanban-viewer

## Intent

Render a read-only kanban board from checked-in fixture JSON.

## Acceptance criteria

- The app displays at least three columns from fixture data.
- Each column displays its cards from fixture data.
- The UI can be run locally without Vikunja credentials.
- No live Vikunja API request is made.

## Proof

- A browser or Playwright check can verify that expected column and card text is visible.

## Blocked by

None.

## Blocks

- Empty, loading, and error states
- Live Vikunja read-only fetch
```

Tracer 2:

```text
Title: Empty, loading, and error states
Labels: agent/type/tracer, agent_status/blocked, risk/low, model_tier/codex_first
```

Body:

```markdown
## Parent

gitea://appliedsci.tail90eacc.ts.net/gitea_admin/skinet-test-tracer/issues/1

## Feature branch

feature/vikunja-kanban-viewer

## Intent

Add explicit empty, loading, and error states around board loading.

## Acceptance criteria

- Empty fixture data renders a clear empty board state.
- Loading state is represented in the UI.
- Error state is represented in the UI.

## Blocked by

- Fixture-backed board shell
```

Tracer 3:

```text
Title: Live Vikunja read-only fetch
Labels: agent/type/tracer, agent_status/blocked, risk/medium, model_tier/codex_first
```

Body:

```markdown
## Parent

gitea://appliedsci.tail90eacc.ts.net/gitea_admin/skinet-test-tracer/issues/1

## Feature branch

feature/vikunja-kanban-viewer

## Intent

Load a configured Vikunja project through a read-only API path using environment-injected credentials.

## Acceptance criteria

- Credentials are read only from environment or local ignored config.
- No credentials are committed.
- The app makes no write requests to Vikunja.
- Failure to reach Vikunja displays the error state from the previous tracer.

## Blocked by

- Fixture-backed board shell
- Empty, loading, and error states
```

### Stage 3 exit criteria

- Gitea has one epic issue.
- Gitea has two or three tracer issues.
- Tracer 1 is labeled `agent_status/ready`.
- Later tracers are blocked visibly, either by native dependency links, markdown sections, or both.
- `feature/vikunja-kanban-viewer` exists on the remote.

## Stage 4 - Create The First Frozen Agent Issue

Goal: manually create the execution contract for tracer 1.

In the practice repo:

```bash
mkdir -p docs/agent-issues
```

Create:

```text
docs/agent-issues/ISSUE-N.v1.md
```

Replace `N` with the real Gitea issue number for "Fixture-backed board shell".

Template:

```markdown
---
canonical_issue: gitea://appliedsci.tail90eacc.ts.net/gitea_admin/skinet-test-tracer/issues/N
parent_prd: gitea://appliedsci.tail90eacc.ts.net/gitea_admin/skinet-test-tracer/issues/1

status: ready
authority: execution_contract
snapshot_version: 1

feature: vikunja-kanban-viewer
feature_branch: feature/vikunja-kanban-viewer
agent_branch: agent/issue-N-fixture-board-shell
run_slug: issue-N-attempt-001
run_path: .tenet/runs/issue-N-attempt-001

model_tier: codex_first
risk_level: low

auto_merge_to_feature: false
manual_review_required: true

runner_retry_budget: 2
tenet_internal_max_retries: 0
tenet_invocation_mode: direct_registered_job

tenet_artifact_paths:
  spec: .tenet/runs/issue-N-attempt-001/spec.md
  scenarios: .tenet/runs/issue-N-attempt-001/scenarios.md
  harness: .tenet/runs/issue-N-attempt-001/harness.md
  decomposition: .tenet/runs/issue-N-attempt-001/decomposition.md
  interview: null

blocked_by: []
blocks: []

proof_required: true
proof_type: playwright
e2e_surface: web_ui
playwright_layer1_required: true
playwright_layer2_required: false

forbidden_paths:
  - .env
  - .env.*
  - secrets/**
  - infra/prod/**

required_commands:
  - npm test
  - npx playwright test
---

# Fixture-backed board shell

## Authority

If the parent PRD conflicts with this tracer issue, obey this tracer issue.
If this tracer issue conflicts with project architecture or testing doctrine, stop and report `scope_conflict`.
If generated Tenet run artifacts conflict with this file, obey this file and regenerate artifacts.

## Intent

Render a read-only kanban board from checked-in fixture JSON.

## Acceptance Criteria

- The app displays at least three columns from fixture data.
- Each column displays its cards from fixture data.
- The UI can be run locally without Vikunja credentials.
- No live Vikunja API request is made.

## Non-Goals

- No Vikunja API integration.
- No card editing.
- No drag and drop.
- No authentication flow.

## Proof Expectations

- A browser or Playwright check verifies expected column and card text is visible.
- The implementation does not require any secret or live service.
```

Commit this snapshot only after checking that it matches the Gitea issue:

```bash
git checkout -b agent/issue-N-fixture-board-shell
git add docs/agent-issues/ISSUE-N.v1.md
git commit -m 'Add frozen agent issue for fixture board shell'
git push -u origin agent/issue-N-fixture-board-shell
```

### Stage 4 exit criteria

- The frozen agent issue exists in the practice repo.
- Its frontmatter names exact future Tenet artifact paths.
- Gitea remains canonical; the local file is a snapshot.
- No Tenet job has been started.

## Stage 5 - Prepare Tenet Artifacts But Do Not Start Tenet

Goal: prove the exact Tenet-compatible artifact layout without invoking implementation.

In the practice repo:

```bash
mkdir -p .tenet/runs/issue-N-attempt-001/journal
mkdir -p .tenet/runs/issue-N-attempt-001/proof
mkdir -p .tenet/runs/issue-N-attempt-001/gate
```

Create these files:

```text
.tenet/runs/issue-N-attempt-001/spec.md
.tenet/runs/issue-N-attempt-001/scenarios.md
.tenet/runs/issue-N-attempt-001/harness.md
.tenet/runs/issue-N-attempt-001/decomposition.md
```

### spec.md

```markdown
# Spec

Generated from `docs/agent-issues/ISSUE-N.v1.md`.

Implement only the fixture-backed board shell.

The canonical issue is:

gitea://appliedsci.tail90eacc.ts.net/gitea_admin/skinet-test-tracer/issues/N

The parent PRD is planning context only.
The frozen agent issue is the execution contract for this attempt.
```

### scenarios.md

```markdown
# Scenarios

## Acceptance scenarios

- Given checked-in board fixture data, when the app loads, then at least three board columns are visible.
- Given a column with cards, when the board renders, then the card titles are visible under the correct column.
- Given no Vikunja credentials, when the app runs, then the fixture-backed board still renders.

## Anti-scenarios

- The app must not call the live Vikunja API.
- The app must not require secrets.
- The app must not implement drag and drop or mutation behavior.
```

### harness.md

````markdown
# Harness

## Required commands

```bash
npm test
npx playwright test
```

## Forbidden paths

- `.env`
- `.env.*`
- `secrets/**`
- `infra/prod/**`

## Merge policy

- Do not merge to `main`.
- Do not auto-merge.
- Target branch after review is `feature/vikunja-kanban-viewer`.

## Retry policy

- `tenet_internal_max_retries: 0`
- `runner_retry_budget: 2`
````

### decomposition.md

```yaml
jobs:
  - id: issue-N
    name: Implement Gitea issue N
    type: dev
    depends_on: []
    artifact_paths:
      spec: .tenet/runs/issue-N-attempt-001/spec.md
      scenarios: .tenet/runs/issue-N-attempt-001/scenarios.md
      harness: .tenet/runs/issue-N-attempt-001/harness.md
      decomposition: .tenet/runs/issue-N-attempt-001/decomposition.md
      interview: null
```

### Registration payload draft

Create a draft payload but do not submit it:

```text
.tenet/runs/issue-N-attempt-001/register-job-draft.json
```

```json
{
  "feature": "vikunja-kanban-viewer",
  "run_slug": "issue-N-attempt-001",
  "run_path": ".tenet/runs/issue-N-attempt-001",
  "artifact_paths": {
    "spec": ".tenet/runs/issue-N-attempt-001/spec.md",
    "scenarios": ".tenet/runs/issue-N-attempt-001/scenarios.md",
    "harness": ".tenet/runs/issue-N-attempt-001/harness.md",
    "decomposition": ".tenet/runs/issue-N-attempt-001/decomposition.md",
    "interview": null
  },
  "jobs": [
    {
      "id": "issue-N",
      "name": "Implement Gitea issue N",
      "type": "dev",
      "depends_on": [],
      "prompt": "Implement only the frozen execution contract in docs/agent-issues/ISSUE-N.v1.md. Do not expand scope. Do not edit forbidden paths. If the contract is insufficient or conflicts with project doctrine, stop and report scope_conflict."
    }
  ]
}
```

Commit the prepared artifacts:

```bash
git add docs/agent-issues/ISSUE-N.v1.md .tenet/runs/issue-N-attempt-001
git commit -m 'Prepare Tenet artifacts for fixture board shell'
git push
```

### Stage 5 exit criteria

- The Tenet run directory exists.
- The shim artifacts exist.
- `decomposition.md` contains exactly one job.
- `register-job-draft.json` exists but has not been submitted.
- Tenet has not started implementation.

## Stop Point

Stop here before running Tenet.

The next decision is whether to:

- manually submit the one-job Tenet registration payload,
- first inspect Tenet's actual job registration interface,
- or tighten the frozen issue format before the first run.

## Notes On Gitea Dependencies

Gitea's documentation describes issue dependencies and repository-level defaults for enabling them. The relevant config options are:

```ini
[repository]
DEFAULT_ENABLE_DEPENDENCIES = true
ALLOW_CROSS_REPOSITORY_DEPENDENCIES = true
```

For this project, native Gitea dependencies are preferred, but the markdown `## Blocked by` and `## Blocks` sections should still be included during the early manual stages. That gives the future controller a stable fallback even if native dependencies are disabled, unavailable through the API, or awkward to query.

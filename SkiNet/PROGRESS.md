# SkiNet Progress Handoff

Last updated: 2026-07-11

## Purpose

SkiNet is a harness around planning skills, an authority provider, an execution provider, deterministic proof, evidence review, and controlled merge policy.

The current design goal is to keep these boundaries replaceable:

- Matt Pocock Skills stay upstream-compatible and do not learn SkiNet/Tenet details.
- SkiNet wrapper/controller code translates skill output into frozen contracts, proof evidence, and state recommendations.
- Gitea/Forgejo is the first authority-provider adapter, not the controller domain model.
- Tenet is the first execution-provider adapter, not the controller domain model.
- Tailscale is an operator preview-provider option, not a core harness dependency.

Primary design document:

- `SkiNet/skills_tenet_localagi_runner_harness_plan_v0.3.md`

Older plans:

- `SkiNet/Prior/skills_tenet_localagi_runner_harness_plan_v0.1.md`
- `SkiNet/Prior/skills_tenet_localagi_runner_harness_plan_v0.2.md`
- `SkiNet/Prior/skills_tenet_runner_harness_plan_v0.0.md`

Manual spike runbook:

- `SkiNet/Plans/stage-1-to-5-manual-runbook.md`

## Repositories

Planning and harness repo:

```text
/Users/jmath/Documents/code/skinet
branch: main
latest relevant commit: b37bccb Add initial proof runner controller slice
```

Practice tracer repo:

```text
/Users/jmath/Documents/code/skinet-test-tracer
branch: agent/issue-2-fixture-board-shell
latest relevant commit: b61c5c2 Add proof runner probe-before-escalation rule
remote PR URL suggested by Gitea:
https://appliedsci.tail90eacc.ts.net:3000/gitea_admin/skinet-test-tracer/pulls/new/agent/issue-2-fixture-board-shell
```

Both repos were clean after the latest commits.

## What Has Been Built

The first real controller slice now exists under:

```text
SkiNet/harness/
```

Files:

- `SkiNet/harness/harnessctl.py`
- `SkiNet/harness/skinet_harness/cli.py`
- `SkiNet/harness/skinet_harness/evidence.py`
- `SkiNet/harness/skinet_harness/models.py`
- `SkiNet/harness/skinet_harness/preview.py`
- `SkiNet/harness/skinet_harness/proof.py`
- `SkiNet/harness/tests/test_proof.py`

Current capabilities:

- classify preview URLs as localhost, tailnet, LAN, deployment preview, remote, or proof-managed localhost;
- classify known sandbox/browser/listener failures;
- run proof in safe mode first;
- retry elevated proof only when explicitly allowed and the safe failure is a classified sandbox/browser/listener failure;
- write durable JSON evidence:
  - `proof-runner-probe.json`
  - `proof.json`
  - `evidence-bundle.json`

Current commands:

```bash
PYTHONPATH=SkiNet/harness python3 SkiNet/harness/harnessctl.py probe-proof-runner \
  --run-id issue-2-attempt-001 \
  --repo /Users/jmath/Documents/code/skinet-test-tracer \
  --probe-command 'npm run test:e2e' \
  --evidence-dir /tmp/skinet-issue-2-controller-evidence

PYTHONPATH=SkiNet/harness python3 SkiNet/harness/harnessctl.py run-proof \
  --run-id issue-2-attempt-001 \
  --repo /Users/jmath/Documents/code/skinet-test-tracer \
  --safe-command 'npm run test:e2e' \
  --evidence-dir /tmp/skinet-issue-2-controller-evidence

PYTHONPATH=SkiNet/harness python3 SkiNet/harness/harnessctl.py bundle-evidence \
  --run-id issue-2-attempt-001 \
  --evidence-dir /tmp/skinet-issue-2-controller-evidence \
  --contract-ref docs/agent-issues/ISSUE-2.v1.md \
  --branch agent/issue-2-fixture-board-shell \
  --commit b61c5c2
```

Verification performed:

```bash
PYTHONPATH=SkiNet/harness python3 -m unittest discover -s SkiNet/harness/tests -v
```

Result: 10 tests passed.

The split probe/proof flow also passed against the real tracer repo. Both commands produced JSON evidence under:

```text
/tmp/skinet-issue-2-controller-evidence/
```

The bundle step is now available but still only summarizes proof-runner and proof evidence. Execution-provider critics, code review, PR interop, and authority-provider state are planned bundle inputs.

## Practice Feature State

The practice feature is a fixture-backed read-only Vikunja-style kanban board viewer.

Tracer repo branch:

```text
agent/issue-2-fixture-board-shell
```

Implemented behavior:

- renders project title from fixture data;
- renders three columns;
- renders cards, optional assignee metadata, and due dates;
- makes no Vikunja/API calls;
- keeps mobile columns horizontally reachable;
- keeps desktop columns separated without overlap;
- preserves baseline smoke semantics.

Local proof passed:

```bash
npm run build
npm test
npm run test:e2e
```

## Lessons Learned

### Tenet planning boundary

Once Pocock Skills and the authority provider produce a frozen tracer issue, do not ask Tenet to re-interview, re-spec, or build its own multi-issue DAG. Generate Tenet-compatible shim artifacts and register exactly one Tenet dev job for one frozen tracer attempt.

### Code review and acceptance boundary

Pocock `/code-review` remains a Standards and Spec review signal. SkiNet acceptance is broader:

- deterministic preflight;
- required UX proof;
- execution-provider critics;
- upstream code review signal;
- PR/authority-provider interoperability;
- evidence aggregation;
- controller state transition.

### Browser proof and sandboxing

The manual spike found three distinct facts:

- Tenet/Codex default `workspace-write` sandbox on this macOS host could not bind local preview servers or launch Chromium reliably.
- Codex `danger-full-access` can run full Playwright proof, including the ordinary localhost path where Playwright starts Vite itself.
- The new controller proof path, running from the normal shell, can run the tracer Playwright suite in safe/default mode on this host.

Policy encoded in v0.3 and the controller:

- do not default to elevated proof mode;
- probe each proof-runner host/image first;
- use safe mode when it works;
- escalate only for classified browser/listener sandbox failures and only when explicitly authorized;
- record both safe and elevated attempts when escalation happens.

### Preview URLs

Tailscale is useful for this operator's headless and remote testing model. It must remain an adapter option. The harness must still support localhost and later deployment-preview URLs.

Near-term assumption:

- continue using Tailscale-based URLs when convenient;
- keep localhost as the default portable path;
- expect full Playwright E2E evidence for web UI tracers.

### Volatile Tenet status files

`.tenet/status/job-queue.md` and `.tenet/status/status.md` are tracked but behave like local run ledgers. They were discarded after the spike and should not be committed as durable evidence unless the project explicitly changes that policy. Durable evidence belongs under run artifacts or controller evidence bundles.

## Next Build Path

The natural next step is to broaden the current proof-runner slice into full controller behavior:

1. Add run-directory storage conventions under a controller-owned path, rather than temp-only output.
2. Add capability caching keyed by host identity, OS, runner image, Codex/Tenet version, and Playwright browser version.
3. Add `harnessctl run-preflight`.
4. Add the first Tenet adapter wrapper:
   - prepare Tenet shim artifacts from a frozen issue;
   - register/start one Tenet dev job;
   - collect dev/eval output as evidence only.
5. Extend `evidence-bundle.json` to include:
   - execution-provider critic results;
   - code review results;
   - PR/authority-provider interop;
   - recommended controller state.
6. Add authority-provider adapter work after the evidence path is stable:
   - Gitea/Forgejo first;
   - GitHub later behind the same controller concepts.

## Suggested Skills for Next Agent

Use these installed skills as needed:

- `implement`: for the next concrete harness implementation slice.
- `code-review`: after non-trivial controller changes.
- `grill-me` or `grill-with-docs`: before changing controller policy or provider boundaries.
- `to-spec` / `to-tickets`: when converting the next controller feature into durable issues.
- `tenet:diagnose`: only if Tenet job state or `.tenet/.state` behavior needs investigation.

## Important Constraints

- Do not modify upstream Pocock Skills to add SkiNet/Tenet-specific behavior.
- Do not hard-code Gitea/Forgejo outside authority-provider adapter code.
- Do not hard-code Tenet outside execution-provider adapter code.
- Do not hard-code Tailscale as required infrastructure.
- Do not treat LocalAGI as canonical state.
- Do not commit secrets, `.env`, or live service credentials.
- Do not let elevated browser proof become the default without a failed safe-mode probe.

# Executable Enforcement Review

Date: 2026-07-13

Scope: primary source inspection of:

- `/tmp/agent-review/superpowers-main`
- `/tmp/agent-review/tenet-main`
- `/tmp/agent-review/skills-main`

Question: which repo has executable enforcement, not just prompt instructions, for TDD, proof/verification, and PR-agent-style review?

## Bottom Line

`tenet-main` is the only inspected repo with substantial executable enforcement for proof/verification and PR-agent-style review. It also has executable test-sufficiency enforcement through runtime eval critics, but it does not literally enforce red-before-green TDD ordering in code.

`superpowers-main` and `skills-main` mostly encode these practices as skills, prompts, hooks that inject instructions, and test suites for their own packaging/runtime. I did not find source code in either repo that inspects a user's implementation history and rejects work for violating TDD order, missing proof, or failing a PR-agent-style review gate.

| Repo | TDD enforcement | Proof / verification enforcement | PR-agent-style review enforcement |
| --- | --- | --- | --- |
| `tenet-main` | Partial executable enforcement: test critic checks behavioral test sufficiency, but not red-before-green chronology | Yes: readiness gates, eval critics, interaction e2e, CI quality gate, deliverable checks | Yes: executable `docs-review` spawns reviewer agents, normalizes findings, can exit nonzero |
| `superpowers-main` | Prompt instruction only for user work; repo has its own tests | Prompt instruction only for user work; session hook injects skill context | Prompt/subagent workflow only |
| `skills-main` | Prompt instruction only | Prompt instruction only | Prompt/subagent workflow only |

## Tenet Evidence

### Runtime eval critics

`tenet-main` defines a configurable critic roster with three built-ins: `code_critic`, `test_critic`, and `interaction_e2e`. The defaults are executable data consumed by the runtime, not just documentation: `/tmp/agent-review/tenet-main/src/core/critic-roster.ts:19`, `/tmp/agent-review/tenet-main/src/core/critic-roster.ts:21`, `/tmp/agent-review/tenet-main/src/core/critic-roster.ts:112`.

`tenet_start_eval` registers an MCP tool that dispatches those critics as jobs and says all must pass. It builds real dispatch jobs from the roster and starts them either in parallel or sequentially: `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-start-eval.ts:359`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-start-eval.ts:374`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-start-eval.ts:466`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-start-eval.ts:471`.

The test critic is executable enforcement of test sufficiency. Its prompt requires behavioral tests and says missing tests are automatic failure: `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-start-eval.ts:187`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-start-eval.ts:220`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-start-eval.ts:226`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-start-eval.ts:230`.

The interaction e2e critic is executable proof/verification. It directs an agent to exercise browser, CLI, API, or library surfaces and report structured pass/fail output: `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-start-eval.ts:85`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-start-eval.ts:98`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-start-eval.ts:133`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-start-eval.ts:142`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-start-eval.ts:174`.

`JobManager` grants interaction-e2e jobs Playwright MCP tool access, which makes that critic operational rather than purely textual: `/tmp/agent-review/tenet-main/src/core/job-manager.ts:695`, `/tmp/agent-review/tenet-main/src/core/job-manager.ts:698`, `/tmp/agent-review/tenet-main/src/core/job-manager.ts:701`.

### Readiness and proof gates

`tenet_validate_readiness` is a hard pre-decomposition gate. It checks implementation readiness, including test strategy and testable surfaces, and dispatches an eval job if deterministic preflight checks pass: `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-validate-readiness.ts:18`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-validate-readiness.ts:67`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-validate-readiness.ts:96`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-validate-readiness.ts:407`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-validate-readiness.ts:478`.

It also has deterministic preflight failure paths that create a completed failure job without dispatching a model when the spec has hard-gate failures: `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-validate-readiness.ts:145`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-validate-readiness.ts:354`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-validate-readiness.ts:379`, `/tmp/agent-review/tenet-main/src/mcp/tools/tenet-validate-readiness.ts:437`.

`JobManager` checks that dev jobs actually produce file changes before accepting success: `/tmp/agent-review/tenet-main/src/core/job-manager.ts:508`, `/tmp/agent-review/tenet-main/src/core/job-manager.ts:510`, `/tmp/agent-review/tenet-main/src/core/job-manager.ts:912`, `/tmp/agent-review/tenet-main/src/core/job-manager.ts:930`.

The repo also has executable CI quality gates: package scripts define `test`, `typecheck`, `lint`, and `build` at `/tmp/agent-review/tenet-main/package.json:36`; CI runs typecheck, lint, test, and build on PRs/pushes at `/tmp/agent-review/tenet-main/.github/workflows/ci.yml:35`, `/tmp/agent-review/tenet-main/.github/workflows/ci.yml:38`, `/tmp/agent-review/tenet-main/.github/workflows/ci.yml:41`, `/tmp/agent-review/tenet-main/.github/workflows/ci.yml:44`.

### PR-agent-style review

`scripts/docs-review.mjs` is an executable review agent harness. It validates agents, extracts code facts, builds a reviewer prompt, invokes Claude/Codex/OpenCode, parses JSON findings, synthesizes issues, writes reports, and exits nonzero based on findings.

Concrete evidence:

- Reviewer schema: `/tmp/agent-review/tenet-main/scripts/docs-review.mjs:22`
- Valid reviewer agents: `/tmp/agent-review/tenet-main/scripts/docs-review.mjs:8`, `/tmp/agent-review/tenet-main/scripts/docs-review.mjs:10`
- Code fact extraction: `/tmp/agent-review/tenet-main/scripts/docs-review.mjs:322`
- Reviewer prompt builder: `/tmp/agent-review/tenet-main/scripts/docs-review.mjs:396`
- Read-only Codex invocation: `/tmp/agent-review/tenet-main/scripts/docs-review.mjs:597`
- Reviewer invocation: `/tmp/agent-review/tenet-main/scripts/docs-review.mjs:614`
- Finding normalization: `/tmp/agent-review/tenet-main/scripts/docs-review.mjs:797`
- Fail decision: `/tmp/agent-review/tenet-main/scripts/docs-review.mjs:1276`
- Nonzero exit behavior: `/tmp/agent-review/tenet-main/scripts/docs-review.mjs:1435`, `/tmp/agent-review/tenet-main/scripts/docs-review.mjs:1466`

The Makefile exposes that review as a runnable target: `/tmp/agent-review/tenet-main/Makefile:39`, `/tmp/agent-review/tenet-main/Makefile:43`.

## Superpowers Evidence

`superpowers-main` has strong prompt instructions for TDD, verification, and review, but I found no executable gate that validates user work against those rules.

TDD is instruction text. The skill says "NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST" and tells the agent to run tests, but this is not backed by code that audits chronology: `/tmp/agent-review/superpowers-main/skills/test-driven-development/SKILL.md:31`, `/tmp/agent-review/superpowers-main/skills/test-driven-development/SKILL.md:113`, `/tmp/agent-review/superpowers-main/skills/test-driven-development/SKILL.md:168`.

Verification is also instruction text. The skill says no completion claims without fresh evidence and describes a gate function, but the "gate" is a prompt procedure, not executable enforcement: `/tmp/agent-review/superpowers-main/skills/verification-before-completion/SKILL.md:16`, `/tmp/agent-review/superpowers-main/skills/verification-before-completion/SKILL.md:24`, `/tmp/agent-review/superpowers-main/skills/verification-before-completion/SKILL.md:117`.

Review is a subagent workflow. `requesting-code-review` tells the agent to dispatch a reviewer subagent and act on findings: `/tmp/agent-review/superpowers-main/skills/requesting-code-review/SKILL.md:12`, `/tmp/agent-review/superpowers-main/skills/requesting-code-review/SKILL.md:24`, `/tmp/agent-review/superpowers-main/skills/requesting-code-review/SKILL.md:42`.

The real executable hook I found is session-start context injection. It reads `using-superpowers/SKILL.md` and emits additional context JSON: `/tmp/agent-review/superpowers-main/hooks/hooks.json:2`, `/tmp/agent-review/superpowers-main/hooks/session-start:10`, `/tmp/agent-review/superpowers-main/hooks/session-start:27`, `/tmp/agent-review/superpowers-main/hooks/session-start:29`. That enforces skill availability/context injection, not TDD/proof/review outcomes.

The repo has package/test infrastructure for itself, such as package metadata and pre-commit checks for `evals/` Python files: `/tmp/agent-review/superpowers-main/package.json:1`, `/tmp/agent-review/superpowers-main/.pre-commit-config.yaml:1`. I did not find a code path in those files that blocks user implementation work for missing TDD chronology, missing verification evidence, or failed PR-style review.

## Skills Evidence

`skills-main` is also primarily prompt/instruction content.

The TDD skill describes the loop and rules, but as a skill document: `/tmp/agent-review/skills-main/skills/engineering/tdd/SKILL.md:1`, `/tmp/agent-review/skills-main/skills/engineering/tdd/SKILL.md:32`.

The `implement` skill tells the agent to use TDD, run checks, use code review, and commit: `/tmp/agent-review/skills-main/skills/engineering/implement/SKILL.md:7`, `/tmp/agent-review/skills-main/skills/engineering/implement/SKILL.md:9`, `/tmp/agent-review/skills-main/skills/engineering/implement/SKILL.md:11`, `/tmp/agent-review/skills-main/skills/engineering/implement/SKILL.md:13`.

The `code-review` skill defines a two-axis review and says to spawn parallel subagents, but it is a procedural skill, not an executable review harness: `/tmp/agent-review/skills-main/skills/engineering/code-review/SKILL.md:6`, `/tmp/agent-review/skills-main/skills/engineering/code-review/SKILL.md:11`, `/tmp/agent-review/skills-main/skills/engineering/code-review/SKILL.md:58`, `/tmp/agent-review/skills-main/skills/engineering/code-review/SKILL.md:76`.

The executable project files I found are release/versioning support, not engineering enforcement. `package.json` has only `changeset` and `version` scripts: `/tmp/agent-review/skills-main/package.json:11`. The GitHub workflow creates version PRs/tags: `/tmp/agent-review/skills-main/.github/workflows/release.yml:29`. The only script under `skills/` found by source inspection was an in-progress wizard template, not an enforcement gate.

## Conclusion

Use `tenet-main` as the example of executable enforcement. Its runtime starts evaluator jobs, persists readiness/eval decisions, runs interaction checks with tool access, exposes a docs-review runner, and has CI gates.

Use `superpowers-main` and `skills-main` as examples of prompt-level governance. They are valuable behavioral systems, but in the inspected source they rely on the agent following instructions rather than executable code rejecting noncompliant work.

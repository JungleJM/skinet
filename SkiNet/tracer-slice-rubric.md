# Tracer Slice Rubric

Use this rubric when creating, reviewing, or revising tracer-bullet slices in SkiNet.

This is the operational standard. External source notes live in `SkiNet/Research/tracer-bullets-sources.md`.

## Core Rule

A tracer slice is the smallest production-intent, end-to-end path that proves a real capability through the relevant layers and can be verified independently.

## Required Checks

### 1. Vertical, not horizontal

The slice must cut through the relevant layers of the system. It must not be only:

- schema work;
- API work;
- UI work;
- test work;
- infrastructure work.

If it only completes one layer, it is not a tracer slice.

### 2. Narrow but complete

The slice should be as small as possible, but still complete enough to prove one real path end to end.

Good sign:

- one concrete capability works all the way through.

Bad sign:

- many adjacent capabilities are bundled together "while we're here".

### 3. Independently demoable or verifiable

A finished slice must have a clear proof target.

Acceptable proof:

- automated test;
- browser proof;
- CLI/API verification;
- another deterministic check that demonstrates the slice works.

If the slice cannot be verified on its own, it is too broad or too vague.

### 4. Sized for one fresh context window

The slice should be small enough that one focused implementation session can carry it end to end without relying on hidden continuity or broad cross-cutting memory.

Signals that it is too large:

- too many moving parts to describe cleanly;
- too many acceptance criteria;
- many unrelated files or surfaces must change together;
- review requires reconstructing several separate ideas at once.

### 5. Production-intent code

Tracer code is not disposable prototype code.

The slice may be incomplete in scope, but the code should still be:

- structurally sound;
- maintainable enough to extend;
- aligned with the repo's real patterns and constraints.

### 6. Proof target declared up front

Each slice should state:

- what behavior it delivers;
- how that behavior will be proven;
- what the explicit non-goals are.

If the proof target is unclear, the slice is not ready.

### 7. Non-goals are explicit

A good tracer slice says what it is not doing. This is necessary to keep agents from overbuilding.

Missing non-goals usually causes:

- scope creep;
- accidental horizontal layering;
- implementation of adjacent features before the core path is proven.

### 8. Prefactoring comes first

If the current codebase shape makes the easy slice hard to land, split out prefactoring first.

Examples:

- extracting a seam;
- normalizing a shared type;
- introducing a compatibility adapter;
- expand-contract work for a wide refactor.

Do not hide required prefactoring inside the tracer slice if it can stand alone.

## Rating Guide

When reviewing a slice, rate each category:

- `pass`: clearly satisfies the rule
- `borderline`: usable, but weak or underspecified
- `fail`: violates the rule and should be split or rewritten

Minimum bar for acceptance:

- no `fail` ratings on the required checks;
- at most two `borderline` ratings;
- a concrete proof target exists.

## Comparison Rule

When a prior slice already exists:

1. judge the new slice against this rubric first;
2. then compare it to the historical slice;
3. treat differences as either:
   - preserved intent,
   - improvement,
   - regression,
   - intentional divergence.

The historical slice is evidence, not the governing standard.

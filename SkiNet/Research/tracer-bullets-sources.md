# Tracer Bullets Sources

Date: 2026-07-13

Purpose: collect source-based notes that inform how SkiNet should design, judge, and revise tracer-bullet slices.

## Sources

- AI Hero: `https://www.aihero.dev/tracer-bullets`
- Between Commits: `https://betweencommits.substack.com/p/how-ai-is-changing-my-job-as-a-staff`
- Ant Janus: `https://dev.to/antjanus/prototypes-dont-get-thrown-out----write-tracer-bullet-code-instead-2ncn`
- C2 Wiki: `https://wiki.c2.com/?TracerBullets`
- Local repo guidance: `.agents/skills/to-tickets/SKILL.md`

## Distillation

### 1. Tracer bullets are integration-first

The strongest common thread is that tracer bullets are not about showing a mockup, proving a broad idea, or filling out one technical layer at a time. They are about verifying that a narrow end-to-end path through the system actually works.

This is the key distinction:

- tracer bullets optimize for stack integration;
- proofs of concept optimize for feasibility;
- prototypes optimize for visualization.

This framing appears most clearly in Between Commits and AI Hero, and it matches the local `to-tickets` rule that slices should be vertical rather than horizontal.

### 2. The slice must be small enough to validate assumptions early

AI Hero is the clearest modern statement of the failure mode: the agent "outruns its headlights" by building large horizontal layers in the dark. The corrective is to force a tiny slice, test it immediately, get feedback, and only then extend the system.

Operationally, this means:

- do not build all endpoints, all UI surfaces, or all infrastructure at once;
- wire one real path through the system first;
- stop and evaluate before expanding coverage.

### 3. Tracer code is for keeps

Ant Janus is the strongest source on this point. A tracer is not disposable prototype code. It should be written with production intent, real interfaces, and normal error-checking discipline. It may be incomplete, but it should not be junk that needs to be thrown away.

That matters for SkiNet because our slices should be:

- minimal in scope;
- but still suitable to evolve forward;
- without assuming a rewrite after learning.

### 4. Vertical completeness matters more than local completeness

The local `to-tickets` skill sharpens the practical rule:

- each slice must cut a narrow but complete path through the relevant layers;
- each slice must be demoable or verifiable on its own;
- each slice must fit inside a single fresh context window;
- prefactoring should happen first when needed.

This is a better execution rule than vague "small tasks". A slice that fully completes only the backend or only the UI is not a tracer bullet.

### 5. Tracer bullets need explicit proof targets

AI-assisted work makes this more important, not less. If the slice does not define:

- what is the narrow end-to-end path;
- what test or proof demonstrates it;
- what non-goals are intentionally excluded;

then the agent will drift into overbuilding.

SkiNet should therefore treat proof expectations as part of slice definition, not an afterthought.

### 6. Similarity to an older slice is only a secondary signal

When re-running a slicing pass, the primary question is not whether the new slices exactly match an earlier human-authored split. The primary question is whether the new split satisfies the tracer-bullet rules above.

Historical comparison is still useful for:

- checking that important acceptance criteria were not dropped;
- spotting accidental scope inflation;
- spotting opportunities where the new split is actually better than the older one.

But the older split is evidence, not authority.

## SkiNet Implications

These sources point toward a stable SkiNet slicing standard:

- a slice must be vertical;
- a slice must be independently verifiable;
- a slice must be the smallest production-intent path that proves the architecture;
- a slice must declare non-goals so it does not absorb adjacent work;
- a slice must include its proof target up front;
- a slice that cannot fit into one fresh context window is too large;
- if prefactoring is required to make the slice easy, that prefactoring should be split out first.

The operational version of this lives in `SkiNet/tracer-slice-rubric.md`.

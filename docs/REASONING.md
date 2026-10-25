# CogA 2 reasoning

## Requests

Every request is a `coga.request` v1 object, validated against
`src/blux_coga/reason/schemas/<capability>.request.v1.json` before anything is computed. Unknown fields are
rejected: a request cannot smuggle in extra data. Ids are ASCII (`[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}`), so
homoglyph ids cannot impersonate each other. Duplicate ids, references to unknown ids, NaN or Infinity,
duplicate JSON keys, and lists over their limit are all errors. The request size limit is 2 MiB.

```json
{"contract": "coga.request", "version": 1, "question": "optional, carried verbatim",
 "evidence": [{"id": "E1", "claim": "text", "kind": "measurement", "reliability": 0.9,
               "source": {"uri": "...", "sha256": "...", "dataset": {"dataset_id": "...", "version": "...", "record_id": "..."}}}],
 ...capability fields...}
```

`kind` sets a default reliability when none is given:

| kind | default reliability |
|---|---|
| measurement | 0.9 |
| observation | 0.8 |
| dataset | 0.8 |
| document | 0.7 |
| testimony | 0.5 |
| assumption | 0.3 |

## Artifacts

```json
{"contract": "coga.artifact", "version": 1,
 "engine": {"name": "coga", "version": "2.0.0", "algorithm": "reason.compare/1", "deterministic": true},
 "capability": "reason.compare", "input_sha256": "…", "artifact_id": "…", "question": "…",
 "result": {...}, "evidence_refs": ["E1"],
 "confidence": {"value": 0.8, "basis": "how this value was computed"},
 "uncertainty": {"level": "low|medium|high", "sources": [{"code", "message", "refs"}]},
 "findings": [{"code", "message", "refs", "severity"}],
 "dataset": [{"dataset_id", "version", "record_id", "evidence_id", "sha256"?}],
 "replay": {"engine_version", "algorithm", "input_sha256", "artifact_id", "deterministic": true, "command"},
 "linkage": null | {"operation_id", "parent_operation_id", "session_id", "project_id", "capability_id", "system"}}
```

- `artifact_id` is the SHA-256 of the canonical artifact *without* `artifact_id`, `replay` and `linkage`.
  The same request on the same algorithm version always gives the same id, wherever it ran.
- `input_sha256` is the SHA-256 of the canonical request.
- `dataset` lists the dataset records behind the evidence the result actually uses.
- `uncertainty.level` is `low` when confidence ≥ 0.7 with at most one uncertainty source, `medium` when
  confidence ≥ 0.4, and `high` otherwise.
- The algorithm version (`reason.x/N`) changes whenever a result for the same input would change.
  `engine.version` is the package's engine version.

Output schemas: `<capability>.artifact.v1.json` and the generic `artifact.v1.json`.

## Determinism

- Lists are processed in id order. The order of request lists never matters (property-tested).
- Only `+ − × ÷` are used: no `log`, `exp` or `pow`, whose last bits can differ between C libraries.
- Floats in artifacts are rounded to 6 decimals, and `-0.0` is written `0.0`.
- Canonical JSON uses sorted keys, compact separators and UTF-8.
- No clock, randomness, environment, network, process or model access. Tests enforce this by inspecting
  imports.

## Algorithms

### reason.analyze/1

- `support` is the noisy-OR of supporting reliabilities: 1 − Π(1 − rᵢ). `against` is the same over
  contradicting evidence.
- `effective_support` = support × the minimum effective support of every claim this one `depends_on`. The
  dependency graph must be acyclic (`DEPENDENCY_CYCLE` otherwise).
- `status` is one of:
  - `unsupported`: no evidence either way;
  - `contested`: effective support ≥ .5 and against ≥ .5;
  - `supported`: effective support ≥ .5;
  - `refuted`: against ≥ .5;
  - `weak`: anything else.
- Claim confidence is |effective − against|. Artifact confidence is the mean over claims.
- Uncertainty sources: `no-evidence`, `assumption-only`, `single-source`, `contested`.
- Findings: `unused-evidence`.

### reason.plan/1

- Kahn order: among ready tasks, the smallest id goes first. A task's stage is 1 + the deepest dependency
  stage.
- Missing effort defaults to 1 and is reported as `default-effort`.
- Schedule: earliest start/finish, latest start, slack. The critical path is the longest effort path; ties
  go to smaller ids.
- `max_parallel` adds a list schedule: ready tasks start by earliest start, then id, giving its makespan.
- Confidence: the share of tasks with an explicit effort.

### reason.compare/1

- Each criterion is min–max normalized over the options that have a value, and inverted for `min`. A
  criterion where every value is equal normalizes to 1 and is reported as `criterion-not-discriminating`.
- Score = Σ wᶜ·nᶜ / Σ wᶜ over the criteria the option has. `coverage` is that weight's share of the total.
- Ranking is dense (equal scores share a rank).
- Option A dominates B when both have every value, A is at least as good everywhere and better somewhere.
  The Pareto front is everything not dominated.
- Sensitivity: each weight is multiplied by 0.5 and 1.5 in turn. Any change of leader is listed in
  `flips`, and `stable` is true only when there are none.
- Confidence = min(1, margin / 0.25) × the leader's coverage.

### reason.decompose/1

- `parent` links form a tree (cycles are errors), and roots hang off the goal.
- Reported: depth, leaves, and work packages (connected components over parent and dependency links).
- Each acceptance criterion is covered by the items it names. Items unrelated to any covering item are
  `untraced`.
- Confidence: the share of acceptance criteria covered.

### reason.critique/1

Exact rules, reported with severity and the ids involved. Cycles are findings here, not errors.

| rule | code | severity | fires when |
|---|---|---|---|
| CR001 | unsupported-claim | high | a claim has no supporting evidence |
| CR002 | assumption-only | high | all support is `kind: assumption` |
| CR003 | single-source | medium | all support comes from one source (`uri`, or one evidence item) |
| CR004 | contradicted | high | the most reliable contradiction is at least as reliable as the most reliable support |
| CR005 | circular-claims | high | claims depend on each other in a cycle |
| CR006 | low-reliability | medium | every supporting source has reliability < 0.5 |
| CR007 | unused-evidence | low | evidence nothing refers to |
| CR008 | too-few-options | medium | fewer than two options |
| CR009 | missing-values | medium | an option lacks a value for a criterion |
| CR010 | task-cycle | high | tasks depend on each other in a cycle |
| CR011 | unverified-dataset | low | dataset evidence without a content hash |
| CR012 | duplicate-statement | low | two claims with the same normalized statement |
| CR013 | depends-on-weak-claim | medium | a claim depends on one that is unsupported, weak, refuted or contested |

Confidence is 1, because the rules are exact. A critique judges the structure, never whether a conclusion is
true.

### reason.rank/1

- **Scores mode:** descending, with equal scores sharing a rank.
- **Pairwise mode:** a pair's net preference weight decides it (win 1, tie 0.5).
  - The Copeland score is the sum. Ties go to net weight, then id.
  - Preference cycles and items never compared are reported.
- Giving both modes in one request is an error.

### reason.risk/1

- Score = likelihood (0–1) × impact (0–5).
- Residual = the likelihood and impact each scaled by Π(1 − reduction) of their mitigations.
- Bands: low < 1 ≤ medium < 2 ≤ high < 3.5 ≤ critical.
- `over_appetite` lists residuals above `appetite` (default 2).
- Confidence: the share of risks whose likelihood cites evidence.
- Uncertainty sources: `unsupported-likelihood`, `unverified-mitigation`.

## What CogA does not do

- It does not read or store model reasoning. There is no field for it, and a test fails if an artifact ever
  has a key that looks like one (`thought`, `chain`, `hidden`, `scratchpad` …).
- It does not tell anyone what to do. Results are measurements of the structure you supplied; `leaders` is
  a fact about scores, not a recommendation.
- It does not execute, fetch or remember anything. Each request stands alone.

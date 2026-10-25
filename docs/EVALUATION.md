# Evaluation

## The bundled suite

`src/blux_coga/reason/evals/` (shipped in the wheel; `coga eval` runs it) has 24 cases. Its dataset identity
is `blux-coga-evals@2.0.0`.

- **Regression:** one or more per capability. Each pins the exact `artifact_id`, so any change to a result,
  confidence, uncertainty or finding is caught. Regenerate the pins with `scripts/gen_evals.py`, and only
  together with an algorithm version bump.
- **Adversarial:** inputs that must be rejected, or must not move a result:
  - prompt-injection text in the question and option titles: the entire `result` must equal the clean
    case's;
  - NaN and Infinity;
  - duplicate ids;
  - unknown references;
  - dependency cycles: an error in `analyze`, a finding (CR005) in `critique`;
  - a smuggled `hidden_reasoning` field;
  - a Cyrillic homoglyph id;
  - a negative weight;
  - a list over its limit;
  - evidence certain both ways;
  - mixed ranking modes;
  - self-comparison;
  - the wrong contract.

A suite is `suite.json` (`coga.eval-suite` v1) plus request files. A case passes when it matches every
expectation it states:

- `artifact_id`: an exact id;
- `error`: an error code;
- `result`: values at JSON pointers into the artifact.

## Property tests

`tests/reason/test_properties.py` runs seeded random inputs (25 seeds per property, so failures reproduce):

- Shuffling every request list never changes the artifact, apart from the input hash and the ids derived
  from it.
- Rewriting every free-text field with injection payloads never changes `result`, `confidence` or
  `uncertainty`.
- The same request gives byte-identical output in separate processes.
- Adding supporting evidence never lowers any claim's support.
- A dominated option never leads, and a positive affine change of a criterion's unit never changes the
  ranking.
- Plans respect every dependency, and slack is never negative.
- Mitigations never raise a residual risk above its inherent risk.

`tests/reason/test_capabilities.py` checks hand-computed numbers for every capability, independently of the
pinned ids. `tests/reason/test_contract.py` checks three things:

- CogA's own schema validator agrees with `jsonschema` on every suite request.
- Every artifact validates against its output schema in `jsonschema` as well.
- The generated schemas and `.blux/capabilities.yaml` are current.

## Dataset linkage

- **Evidence → dataset records.** Evidence may name a dataset record (`source.dataset`:
  `dataset_id`, `version`, `record_id`, optional `sha256`). The artifact's `dataset` array lists every
  record behind evidence the result used, so an artifact traces to its data. `reason.critique` flags dataset
  evidence without a hash (CR011).
- **Suite → dataset.** The eval suite declares its own dataset identity. Every eval report names it, and
  each case id is a record id within it.
- **blux-coga-dataset.** That repository holds the fixtures of the frozen CogA 1.0 contract
  (`blux-coga run`), and CI replays them on every push. It does not yet cover the `reason.*`
  capabilities; see [AUDIT-1.0.md](AUDIT-1.0.md#dataset-assumptions).

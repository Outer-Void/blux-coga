## Acceptance harness

The acceptance harness replays `ProblemSpec` fixtures, validates input and
output schemas, writes per-fixture artifacts, and emits a deterministic
`report.json` summary.

This harness is an internal module API (`blux_coga.io.acceptance.run_acceptance`)
used by tests and CI checks. It is not a second public CLI contract.

### Dataset-facing fixture freeze

This repository now ships a frozen replay set under:

- `tests/fixtures/live_dataset_cases/*.json` (input `ProblemSpec` fixtures)
- `tests/fixtures/live_dataset_cases_expected/<case>/*.json` (canonical outputs)

The fixture families cover representative live-harness mismatch classes:

- ambiguous
- assumptions
- contradiction
- options
- comparison
- unclear minimal delta
- non-directive regression
- stop/freeze
- tie breaker

`tests/test_live_dataset_alignment.py` replays these fixtures through the live
contract processor and asserts exact match with frozen expected
`thought_artifact.json` and `reasoning_verdict.json` outputs.

### Canonical interface alignment

All fixture execution is anchored to the same canonical contract artifacts:

- input shape: `schemas/problem.schema.json`
- output shapes: `schemas/thought_artifact.schema.json`,
  `schemas/reasoning_verdict.schema.json`
- canonical external invocation: `blux-coga run --input ... --output-dir ...`

### Output layout

The output directory contains:

- `report.json`
- `<fixture-stem>/thought_artifact.json`
- `<fixture-stem>/reasoning_verdict.json`

### Report metadata

`report.json` records:

- `contract_version`
- `model_version`
- `reasoning_pack_id`
- `reasoning_pack_version`
- `schema_version`
- per-fixture `input_hash`
- per-fixture verdict `status`
- schema validation results
- deterministic comparisons with expected outputs when fixture subdirectories
  contain frozen expected artifacts

## Contract

The frozen release is package `blux-coga` 1.0.0 with runtime identity
`CogA-1.0-pro`.

The contract surface is:

- one canonical execution command: `blux-coga run --input <problem.json> --output-dir <out-dir>`
- one acceptance command: `blux-coga accept --fixtures <fixtures-dir> --output-dir <out-dir>`
- one input schema: `ProblemSpec`
- two output schemas: `ThoughtArtifact` and `ReasoningVerdict`

### Input: `ProblemSpec`

Location: `schemas/problem.schema.json`

Required top-level fields:

- `user_input`
- `session`

Required `session` fields:

- `history`
- `last_user_utterances`
- `last_intent`
- `extracted_intent`
- `extracted_constraints`
- `stopped`
- `frozen`

No undocumented top-level or `session` fields are accepted.

### Output: `ThoughtArtifact`

Location: `schemas/thought_artifact.schema.json`

Required fields:

- `run_header`
- `reflection`
- `clarifications`
- `observations`
- `flags`
- `contradiction`
- `options`
- `comparison`
- `acknowledgment`
- `summary`
- `response_text`

No additional fields are emitted.

### Output: `ReasoningVerdict`

Location: `schemas/reasoning_verdict.schema.json`

Required fields:

- `run_header`
- `status`
- `checks`
- `delta`
- `refusal`

Allowed `status` values:

- `COMPLETE`
- `UNCLEAR`
- `REFUSE`

No additional fields are emitted.

### Frozen run-header metadata

Current outputs record these run-header fields:

- `input_hash`
- `contract_version`
- `model_version`
- `reasoning_pack_id`
- `reasoning_pack_version`
- `schema_version`
- optional `profile_id`
- optional `profile_version`

`profile_id` and `profile_version` are omitted when no profile is selected.

### Stable field rules

- `checks` is emitted in stable order.
- `delta` is always present in the JSON object shape; it is an object for
  `UNCLEAR`, may be an object for `REFUSE`, and is otherwise `null`.
- `refusal` is always present in the JSON object shape; it is an object for
  `REFUSE` and otherwise `null`.
- Schema, model code, canonical CLI file mode, and acceptance outputs are
  expected to match this contract exactly in the frozen release.

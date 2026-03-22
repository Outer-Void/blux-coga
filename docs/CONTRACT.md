## Contract

Package release `blux-coga` 1.0.0 ships the engine identity `CogA-1.0-pro`.
The contract consists of one input schema (`ProblemSpec`) and two emitted
artifact schemas (`ThoughtArtifact` and `ReasoningVerdict`).

### Input: ProblemSpec

- Location: `schemas/problem.schema.json`
- Required top-level fields: `user_input`, `session`
- Session fields: `history`, `last_user_utterances`, `last_intent`,
  `extracted_intent`, `extracted_constraints`, `stopped`, `frozen`

### Output: ThoughtArtifact

- Location: `schemas/thought_artifact.schema.json`
- Required fields:
  - `run_header`
  - `reflection`
  - `clarifications[]`
  - `observations[]`
  - `flags`
  - `contradiction`
  - `options[]`
  - `comparison`
  - `acknowledgment`
  - `summary`
  - `response_text`
- `run_header` always includes:
  - `input_hash`
  - `contract_version`
  - `model_version`
  - `reasoning_pack_id`
  - `reasoning_pack_version`
  - `schema_version`
- `run_header` additionally includes `profile_id` and `profile_version` only
  when a profile is selected.

### Output: ReasoningVerdict

- Location: `schemas/reasoning_verdict.schema.json`
- Required fields:
  - `run_header`
  - `status`
  - `checks[]`
  - `delta`
  - `refusal`
- Status values:
  - `COMPLETE`
  - `UNCLEAR`
  - `REFUSE`
- `checks[]` is emitted in stable order.
- `delta` is required for `UNCLEAR`, optional for `REFUSE`, and otherwise null.
- `refusal` is required for `REFUSE` and otherwise null.

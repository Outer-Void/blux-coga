## CogA Contract (Phase 10)

CogA-1.0 produces deterministic, schema-validated artifacts for each turn. The
contract consists of a single input type (`ProblemSpec`) and two output types:
`ThoughtArtifact` and `ReasoningVerdict`.

### Input: ProblemSpec

- Location: `schemas/problem.schema.json`
- Payload: user input plus session state (history, intents, flags).

### Output: ThoughtArtifact

- Location: `schemas/thought_artifact.schema.json`
- Includes reflection, clarifications, observations, flags, contradiction
  context, option artifacts, and the final response text.
- Contains a `run_header` with:
  - `input_hash`
  - `contract_version`
  - `model_version`
  - `reasoning_pack_id`
  - `reasoning_pack_version`
  - `schema_version`
- Multi-option reasoning:
  - `options[]` includes `{id, title, pros[], cons[], risks[], unknowns[]}`.
  - `comparison` is optional (nullable) and includes `criteria[]` and `rows[]`
    keyed by `option_id`.

### Output: ReasoningVerdict

- Location: `schemas/reasoning_verdict.schema.json`
- Status grammar:
  - `COMPLETE`
  - `UNCLEAR`
  - `REFUSE`
- The `checks` list is stable-ordered.
- `delta` is required for `UNCLEAR` and provides a minimal change needed to
  move forward using a deterministic, structured prompt.
- `refusal` is required for `REFUSE` and records a structured refusal category
  and detail. `delta` only appears for `REFUSE` when a resolution path exists.

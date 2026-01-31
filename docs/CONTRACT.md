## CogA Contract (Phase 1)

CogA-0.1 produces deterministic, schema-validated artifacts for each turn. The
contract consists of a single input type (`ProblemSpec`) and two output types:
`ThoughtArtifact` and `ReasoningVerdict`.

### Input: ProblemSpec

- Location: `schemas/problem.schema.json`
- Payload: user input plus session state (history, intents, flags).

### Output: ThoughtArtifact

- Location: `schemas/thought_artifact.schema.json`
- Includes reflection, clarifications, observations, flags, and the final
  response text.
- Contains a `run_header` with:
  - `input_hash`
  - `contract_version`
  - `model_version`

### Output: ReasoningVerdict

- Location: `schemas/reasoning_verdict.schema.json`
- Status grammar:
  - `COMPLETE`
  - `UNCLEAR`
  - `REFUSE`
- The `checks` list is stable-ordered.
- `delta` is required for `UNCLEAR`/`REFUSE` and provides a minimal change
  needed to move forward.

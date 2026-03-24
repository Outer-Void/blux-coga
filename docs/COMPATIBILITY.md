## Compatibility

### Frozen compatibility surface

The frozen support promise is intentionally narrow:

- canonical execution command: `blux-coga run --input <problem.json> --output-dir <out-dir>`
- runner scripts that forward only to that exact command form
- the internal Python `CogAThinker` wrapper for repository tests and embedded
  callers, with no additional compatibility promise beyond the documented
  contract processor output schema
- reading older run headers by backfilling missing `run_hash` from
  `input_hash`, and missing `reasoning_pack_id`, `reasoning_pack_version`, and
  `schema_version` as `unknown`
- leaving legacy profile metadata absent when an older header did not record it

Anything else is outside the frozen support promise unless it is explicitly
documented in this repository.

### Removed accidental interface surface

The frozen release does not support the following former conveniences:

- top-level implicit run invocation such as `blux-coga --input ...`
- `--in` / `--out` aliases
- `accept` as a public CLI command
- interactive CLI mode

These were removed so dataset and harness integrations depend on one explicit,
stable interface.

### Current run-header fields

Current outputs include:

- `input_hash`
- `run_hash`
- `contract_version`
- `model_version`
- `reasoning_pack_id`
- `reasoning_pack_version`
- `schema_version`
- optional `profile_id`
- optional `profile_version`

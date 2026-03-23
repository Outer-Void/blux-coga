## Compatibility

### Frozen compatibility surface

The frozen support promise is intentionally narrow:

- canonical execution command: `blux-coga run --input <problem.json> --output-dir <out-dir>`
- canonical acceptance command: `blux-coga accept --fixtures <fixtures-dir> --output-dir <out-dir>`
- runner scripts that forward to those exact command forms
- reading older run headers by backfilling missing `reasoning_pack_id`,
  `reasoning_pack_version`, and `schema_version` as `unknown`
- leaving legacy profile metadata absent when an older header did not record it

Anything else is outside the frozen support promise unless it is explicitly
documented in this repository.

### Removed accidental interface surface

The frozen release does not support the following former conveniences:

- top-level implicit run invocation such as `blux-coga --input ...`
- `--in` / `--out` aliases
- interactive CLI mode

These were removed so dataset and harness integrations depend on one explicit,
stable interface.

### Current run-header fields

Current outputs include:

- `input_hash`
- `contract_version`
- `model_version`
- `reasoning_pack_id`
- `reasoning_pack_version`
- `schema_version`
- optional `profile_id`
- optional `profile_version`

### Current compatibility rules

- `delta` is always emitted; it is an object for `UNCLEAR` and otherwise `null`
  unless a structured refusal delta is intentionally added later
- `refusal` is always emitted; it is an object for `REFUSE` and otherwise `null`
- missing profile metadata means no profile was recorded for that run
- undocumented alternate filenames, undocumented alternate CLI forms, and
  undocumented hidden metadata are not part of the compatibility contract

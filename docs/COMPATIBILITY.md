## Compatibility

### Frozen compatibility surface

The supported legacy surface is intentionally limited to:

- the top-level CLI alias `blux-coga --input ... --output-dir ...`, which maps
  directly to `blux-coga run ...`
- runner-script argument aliases `--in` and `--out`
- acceptance-harness alias `--out` for `--output-dir`
- reading older run headers by backfilling missing `reasoning_pack_id`,
  `reasoning_pack_version`, and `schema_version` as `unknown`
- leaving legacy profile metadata absent when an older header did not record it

Anything else is outside the frozen support promise unless it is explicitly
documented in this repository.

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

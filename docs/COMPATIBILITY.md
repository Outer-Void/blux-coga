## Compatibility

### Frozen compatibility decision

The supported legacy surface is intentionally limited to:

- the legacy top-level CLI alias `blux-coga --input ... --output-dir ...`
  which maps directly to `blux-coga run ...`
- the runner-script argument aliases `--in` and `--out`
- reading older run headers by backfilling missing `reasoning_pack_*`,
  `schema_version`, and profile metadata as unknown or absent

Anything else is outside the frozen support promise unless it is documented in
this repo.

### Current run-header fields

Current outputs include these run-header fields:

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
  unless a structured refusal delta is explicitly added in the future
- `refusal` is always emitted; it is an object for `REFUSE` and otherwise `null`
- missing optional profile metadata means no profile was recorded
- schema changes should remain additive unless a major contract change is made

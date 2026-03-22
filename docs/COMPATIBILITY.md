## Compatibility

Current outputs include these run-header fields:

- `input_hash`
- `contract_version`
- `model_version`
- `reasoning_pack_id`
- `reasoning_pack_version`
- `schema_version`
- optional `profile_id`
- optional `profile_version`

Consumers reading older artifacts may backfill missing `reasoning_pack_*`,
`schema_version`, and profile fields as unknown or absent legacy metadata.

Current compatibility rules:

- `delta` is mandatory for `UNCLEAR`
- `refusal` is mandatory for `REFUSE`
- missing optional profile metadata means no profile was recorded
- schema changes should remain additive unless a major contract change is made

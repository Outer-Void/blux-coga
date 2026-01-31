## Compatibility

CogA outputs include header fields that enable compatibility checks:

- `contract_version`
- `model_version`
- `reasoning_pack_id`
- `reasoning_pack_version`
- `schema_version`

Consumers should treat missing fields as legacy outputs and backfill defaults
when reading older artifacts. Schema upgrades remain additive and avoid breaking
changes to existing output shapes.

### Legacy handling

- Missing reasoning pack or schema fields are treated as `unknown`.
- `delta` is mandatory only for `UNCLEAR` verdicts.
- `refusal` is mandatory only for `REFUSE` verdicts.

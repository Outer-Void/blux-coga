## Reasoning packs

Reasoning packs are local JSON descriptors stored in `reasoning_packs/`.

The frozen release loads `reasoning_packs/default.json` and records its
`reasoning_pack_id` and `reasoning_pack_version` in every emitted `run_header`.

### Frozen default pack

- id: `default`
- version: `1.0`
- description: `Deterministic baseline reasoning pack for CogA.`

The pack records deterministic run provenance. It does not change schema shape,
output filenames, or the canonical CLI.

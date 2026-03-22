## Reasoning packs

Reasoning packs are local JSON descriptors stored in `reasoning_packs/`.
The current release loads `reasoning_packs/default.json` and records its
`reasoning_pack_id` and `reasoning_pack_version` in every `run_header`.

Current default pack:

- id: `default`
- version: `1.0`
- purpose: deterministic baseline reasoning metadata for CogA contract runs

A reasoning pack does not change schema shape by itself; it only records which
local pack metadata was used for the run.

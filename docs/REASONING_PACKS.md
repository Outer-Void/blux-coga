## Reasoning Packs (Phase 5)

Reasoning packs are local, deterministic bundles that label the reasoning
configuration used to generate each verdict. Packs are stored in
`reasoning_packs/` and loaded offline by id and version. The selected pack id
and version are recorded in each `run_header`.

### Tag notes (model stepping)

- **CogA-0.3-mini**: Added the multi-option schema surface (`options[]`) and
  deterministic ordering guarantees for option artifacts.
- **CogA-0.3**: Added optional comparison matrices (`comparison`) aligned to
  option ordering with stable criteria and rows.
- **CogA-0.4-mini**: Introduced deterministic, structured UNCLEAR deltas and
  acceptance fixture scaffolding.
- **CogA-0.4**: Finalized the acceptance harness outputs and determinism tests.
- **CogA-0.5-mini**: Added deterministic reasoning pack identifiers.
- **CogA-0.5**: Recorded pack id/version in `run_header`.
- **CogA-0.6-mini**: Introduced bounded depth and deterministic tie-breaking.
- **CogA-0.6**: Stabilized minimal clarification selection for UNCLEAR deltas.
- **CogA-0.7-mini**: Added compatibility headers.
- **CogA-0.7**: Added compatibility docs and tests.
- **CogA-0.8-mini**: Integrated dataset coupling hooks in the acceptance harness.
- **CogA-0.8**: Documented fixture update discipline for version bumps.
- **CogA-0.9-mini**: Added release documentation scaffolding.
- **CogA-0.9**: Documented platform runbooks.
- **CogA-1.0-mini**: Locked schema/contract headers.
- **CogA-1.0**: Finalized determinism and compatibility matrices.
- **CogA-1.0-pro**: Added PRO capability notes.

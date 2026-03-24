# blux-coga

`blux-coga` 1.0.0 is the frozen BLUX CogA engine package. It ships the runtime
identity `CogA-1.0-pro` as a deterministic, contract-first, file-first
processor that turns one `ProblemSpec` JSON input into two canonical JSON
outputs.

## Frozen identity

- package name: `blux-coga`
- package version: `1.0.0`
- runtime identity (`run_header.model_version`): `CogA-1.0-pro`
- contract version: `1.0`
- schema version: `1.0`
- default reasoning pack: `default` version `1.0`
- built-in profiles: `cpu` version `1.0`, `gpu` version `1.0`

## Canonical interface

The frozen dataset, harness, and export interface is deterministic file mode:

```bash
blux-coga run --input path/to/problem.json --output-dir out
```

That command writes exactly:

- `out/thought_artifact.json`
- `out/reasoning_verdict.json`

The canonical input shape is `schemas/problem.schema.json`. The canonical output
shapes are `schemas/thought_artifact.schema.json` and
`schemas/reasoning_verdict.schema.json`.

### Acceptance harness

The frozen acceptance interface is:

```bash
blux-coga accept --fixtures path/to/fixtures --output-dir out
```

It writes `report.json` plus one canonical artifact/verdict pair per fixture.

## Removed non-canonical surface

This freeze removes accidental or legacy CLI surface so dataset repositories can
rely on one explicit command form:

- removed top-level implicit run invocation such as `blux-coga --input ...`
- removed `--in` and `--out` aliases
- removed interactive CLI mode from the public interface

Runner scripts now forward directly to the same canonical CLI contract.

## Retained non-canonical internals (not freeze contract)

The Python stateful wrapper (`CogAThinker`) remains available for internal
tests and embedding. It uses the same contract processor but is not a frozen
dataset/export integration surface. Freeze-sensitive integrations should use
only the canonical file-mode CLI.

## Deterministic metadata emitted on every run

Both output files include `run_header` metadata with:

- `input_hash`
- `contract_version`
- `model_version`
- `reasoning_pack_id`
- `reasoning_pack_version`
- `schema_version`
- `profile_id` and `profile_version` when a profile is explicitly selected

## Behavior guarantees

- Same `ProblemSpec` + same reasoning pack + same profile yields byte-identical
  canonical JSON.
- `COMPLETE`, `UNCLEAR`, and `REFUSE` are emitted as structured verdicts.
- Non-directive enforcement applies across all user-visible artifact and verdict
  fields.
- Acceptance harness reports are serialized with the same stable JSON rules.

## Installation and local verification

```bash
python -m pip install -e .
pytest
```

## Documentation

- `docs/CONTRACT.md`
- `docs/DETERMINISM.md`
- `docs/BOUNDARIES.md`
- `docs/REASONING_PACKS.md`
- `docs/ACCEPTANCE.md`
- `docs/COMPATIBILITY.md`
- `docs/DEPRECATION.md`
- `docs/RUNBOOK.md`
- `docs/PRO_NOTES.md`
- `docs/PLATFORMS.md`

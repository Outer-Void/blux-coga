# blux-coga

`blux-coga` 1.0.0 is the frozen BLUX CogA engine package. It ships runtime
identity `CogA-1.0-pro` as a deterministic, contract-first, file-in/file-out
processor.

## Frozen identity

- package name: `blux-coga`
- package version: `1.0.0`
- runtime identity (`run_header.model_version`): `CogA-1.0-pro`
- contract version: `1.0`
- schema version: `1.0`
- default reasoning pack: `default` version `1.0`
- built-in profiles: `cpu` version `1.0`, `gpu` version `1.0`

## Canonical interface (single supported invocation)

```bash
blux-coga run --input path/to/problem.json --output-dir out
```

That command writes exactly:

- `out/thought_artifact.json`
- `out/reasoning_verdict.json`

The canonical input shape is `schemas/problem.schema.json`. The canonical output
shapes are `schemas/thought_artifact.schema.json` and
`schemas/reasoning_verdict.schema.json`.

## Removed non-canonical surface

This freeze removes accidental or legacy CLI surface so dataset repositories can
rely on one explicit command form:

- removed top-level implicit run invocation such as `blux-coga --input ...`
- removed `--in` and `--out` aliases
- removed `accept` as a public CLI command
- removed interactive CLI mode from the public interface

Runner scripts now enforce and forward only the canonical run command.

## Deterministic metadata emitted on every run

Both output files include `run_header` metadata with:

- `model_version`
- `contract_version`
- `reasoning_pack_id`
- `profile_id` (optional when unset)
- `input_hash`
- `run_hash`
- `reasoning_pack_version`
- `schema_version`
- `profile_version` (optional when unset)

## Behavior guarantees

- Same `ProblemSpec` + same reasoning pack + same profile yields byte-identical
  canonical JSON.
- `COMPLETE`, `UNCLEAR`, and `REFUSE` are emitted as structured verdicts.
- Non-directive enforcement applies across all user-visible artifact and verdict
  fields.

## Installation and local verification

```bash
python -m pip install -e .
pytest
```

Representative dataset-facing replay parity is covered by:

```bash
pytest tests/test_live_dataset_alignment.py
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

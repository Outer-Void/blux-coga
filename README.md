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

The canonical harness, dataset-alignment, export-preparation, and training
handoff path is deterministic file mode:

```bash
blux-coga run --input path/to/problem.json --output-dir out
```

That command writes exactly:

- `out/thought_artifact.json`
- `out/reasoning_verdict.json`

The canonical input shape is `schemas/problem.schema.json`. The canonical output
shapes are `schemas/thought_artifact.schema.json` and
`schemas/reasoning_verdict.schema.json`.

### Intentional compatibility aliases

These compatibility entrypoints remain supported and resolve to the same
runtime behavior:

```bash
blux-coga --input path/to/problem.json --output-dir out
./CogA.sh run --in path/to/problem.json --out out
```

### Optional interactive inspection mode

Interactive mode exists for manual local inspection only:

```bash
blux-coga run --interactive --output-dir out
```

It reuses the same contract engine and canonical filenames, but it is not the
canonical harness surface. Each later turn overwrites the same two files in the
selected output directory.

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

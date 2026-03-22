# blux-coga

`blux-coga` 1.0.0 packages the frozen BLUX CogA runtime identity
`CogA-1.0-pro` as a deterministic, file-first contract processor. It reads a
`ProblemSpec` JSON input, applies the non-directive contract, and writes stable
JSON artifacts that are ready for harness use, dataset export, and training
preparation.

## Frozen runtime identity

- package name: `blux-coga`
- package version: `1.0.0`
- runtime identity (`run_header.model_version`): `CogA-1.0-pro`
- contract version: `1.0`
- schema version: `1.0`
- default reasoning pack: `default` version `1.0`

## Canonical usage

The canonical harness and dataset path is file-based execution:

```bash
blux-coga run --input path/to/problem.json --output-dir out
```

Canonical file mode writes exactly:

- `out/thought_artifact.json`
- `out/reasoning_verdict.json`

Intentional compatibility aliases remain available and map to the same `run`
behavior:

```bash
blux-coga --input path/to/problem.json --output-dir out
./CogA.sh --in path/to/problem.json --out out
```

Optional deterministic profile selection:

```bash
blux-coga run --profile cpu --input path/to/problem.json --output-dir out
```

Optional interactive mode exists only for manual local inspection. A single
interactive turn reuses the same contract engine and output filenames, but the
REPL is not the canonical harness surface and later turns overwrite the same
output files:

```bash
blux-coga run --interactive --output-dir out
```

## Enforced behavior

- Deterministic hashing of normalized `ProblemSpec` payloads.
- Stable JSON serialization for all emitted artifacts and acceptance reports.
- Non-directive boundary enforcement across all user-visible artifact and
  verdict fields.
- Structured `COMPLETE`, `UNCLEAR`, and `REFUSE` verdicts.
- Deterministic run headers containing contract, schema, reasoning-pack, and
  optional profile metadata.

## Support policy

The frozen compatibility surface is intentionally narrow:

- Supported: canonical `run` and `accept` subcommands.
- Supported: the legacy top-level `blux-coga --input ...` alias for `run`.
- Supported: reading older run headers by backfilling missing pack/schema
  metadata as unknown.
- Not promised: older undocumented CLI shapes, alternate output filenames,
  or hidden compatibility fields.

## Development

```bash
python -m pip install -e .
pytest
```

## Documentation

- `docs/CONTRACT.md`
- `docs/DETERMINISM.md`
- `docs/BOUNDARIES.md`
- `docs/PLATFORMS.md`
- `docs/REASONING_PACKS.md`
- `docs/ACCEPTANCE.md`
- `docs/COMPATIBILITY.md`
- `docs/DEPRECATION.md`
- `docs/RUNBOOK.md`
- `docs/PRO_NOTES.md`

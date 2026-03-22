# blux-coga

`blux-coga` 1.0.0 packages the BLUX CogA engine `CogA-1.0-pro` as a
deterministic, file-first contract processor. It reads a `ProblemSpec` JSON
input, applies the non-directive contract, and writes stable JSON artifacts.

## Canonical usage

The canonical harness path is file-based execution:

```bash
blux-coga run --input path/to/problem.json --output-dir out
```

Compatibility aliases remain available:

```bash
blux-coga --input path/to/problem.json --output-dir out
./CogA.sh --in path/to/problem.json --out out
```

File mode writes exactly:

- `out/thought_artifact.json`
- `out/reasoning_verdict.json`

Optional deterministic profile selection:

```bash
blux-coga run --profile cpu --input path/to/problem.json --output-dir out
```

Optional interactive mode exists for manual local use. It reuses the same
artifact filenames in the selected output directory, but it is not the
canonical harness path:

```bash
blux-coga run --interactive --output-dir out
```

## Enforced behavior

- Deterministic hashing of normalized `ProblemSpec` payloads.
- Stable JSON serialization for all emitted artifacts and reports.
- Non-directive boundary enforcement across all user-visible artifact fields.
- Structured `COMPLETE`, `UNCLEAR`, and `REFUSE` verdicts.
- Deterministic run headers containing contract, schema, reasoning-pack, and
  optional profile metadata.

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

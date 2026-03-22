## Acceptance harness

The acceptance harness replays `ProblemSpec` fixtures, validates the input and
output schemas, writes per-fixture artifacts, and emits a deterministic
`report.json` summary.

This repo does not ship a permanent fixture corpus. The harness expects a
fixture directory provided at runtime.

### CLI

```bash
blux-coga accept --fixtures path/to/fixtures --out path/to/out
```

### Outputs

The output directory contains:

- `report.json`
- `<fixture-stem>/thought_artifact.json`
- `<fixture-stem>/reasoning_verdict.json`

The report records:

- release metadata (`contract_version`, `model_version`, reasoning-pack
  metadata, `schema_version`)
- per-fixture input hash and verdict status
- schema validation results
- deterministic comparisons with expected artifacts when fixture
  subdirectories contain expected outputs

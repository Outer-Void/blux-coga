## Acceptance harness

The acceptance harness replays `ProblemSpec` fixtures, validates the input and
output schemas, writes per-fixture artifacts, and emits a deterministic
`report.json` summary.

This repository does not ship a permanent fixture corpus. Provide a fixture
directory at runtime.

### CLI

```bash
blux-coga accept --fixtures path/to/fixtures --output-dir path/to/out
```

`--out` remains an intentional alias for `--output-dir`.

### Output layout

The output directory contains:

- `report.json`
- `<fixture-stem>/thought_artifact.json`
- `<fixture-stem>/reasoning_verdict.json`

### Report metadata

`report.json` records:

- `contract_version`
- `model_version`
- `reasoning_pack_id`
- `reasoning_pack_version`
- `schema_version`
- per-fixture `input_hash`
- per-fixture verdict `status`
- schema validation results
- deterministic comparisons with expected outputs when fixture subdirectories
  contain frozen expected artifacts

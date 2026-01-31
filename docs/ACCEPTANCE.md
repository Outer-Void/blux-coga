## Acceptance Harness

The acceptance harness replays deterministic fixtures and emits a stable report
alongside per-fixture artifacts.

### CLI

```bash
blux-coga accept --fixtures path/to/fixtures --out path/to/out
```

### Outputs

The output directory contains:

- `report.json`: deterministic summary of all fixtures.
- `<fixture-stem>/thought_artifact.json`
- `<fixture-stem>/reasoning_verdict.json`

The report lists fixture names, hashes, and verdict status, plus a stable
summary of counts by status.

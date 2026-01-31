## Acceptance Harness

The acceptance harness replays deterministic fixtures, validates schemas, and
emits a stable report alongside per-fixture artifacts.

### CLI

```bash
blux-coga accept --fixtures path/to/fixtures --out path/to/out
```

### Outputs

The output directory contains:

- `report.json`: deterministic summary of all fixtures.
- `<fixture-stem>/thought_artifact.json`
- `<fixture-stem>/reasoning_verdict.json`

The report lists fixture names, hashes, verdict status, and header metadata,
plus a stable summary of counts by status. When a fixture directory contains
expected artifacts (stored under a subdirectory matching the fixture stem), the
harness records deterministic match results for comparisons.

### Fixture dataset coupling

The harness is designed to interoperate with blux-coga-dataset fixtures. Fixture
updates for intentional version bumps should include refreshed expected outputs
and updated compatibility notes in the dataset release log.

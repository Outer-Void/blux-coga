# blux-coga

BLUX-CogA is a contract-driven reasoning scaffold that focuses on non-directive
boundary enforcement. Inputs are normalized and hashed deterministically, and
outputs are emitted as structured JSON artifacts rather than free-form text.

## Behavior overview

- **Contract-driven outputs:** JSON artifacts are emitted for thought artifacts
  and reasoning verdicts.
- **Determinism + hashing:** Normalized `ProblemSpec` inputs are hashed to ensure
  deterministic, replayable outputs for the same input.
- **Non-directive boundaries:** Output avoids prescriptive language ("you should",
  "best approach", etc.).
- **Stop / freeze:** Entering `stop` halts the session; entering `freeze` halts and
  freezes intent state for the remainder of the session.
- **CLI harness:** File-based input/output is the default; interactive REPL mode
  is optional.

## Usage

Create a JSON `ProblemSpec` (see `schemas/problem.schema.json`) and run:

```bash
blux-coga --input path/to/problem.json --output-dir out
```

This writes:

- `out/thought_artifact.json`
- `out/reasoning_verdict.json`

For interactive mode:

```bash
blux-coga --interactive
```

## Development

```bash
pytest
```

## Documentation

- `docs/CONTRACT.md`
- `docs/DETERMINISM.md`
- `docs/BOUNDARIES.md`
- `docs/PLATFORMS.md`

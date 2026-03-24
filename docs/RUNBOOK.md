## Runbook

### Local setup (Linux/macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
pytest
```

### Canonical file-mode run

```bash
blux-coga run --input path/to/problem.json --output-dir out
```

### Freeze anchoring note

- Treat `blux-coga run --input ... --output-dir ...` as the authoritative
  integration path for datasets/exports/training anchors.
- Use `run_header.input_hash` and `run_header.run_hash` when anchoring
  manifests; emitted output JSON is byte-stable for identical input/profile/pack.

### Dataset replay verification

Run the representative live dataset fixture replay:

```bash
pytest tests/test_live_dataset_alignment.py
```

This replays frozen fixture families and checks exact parity against
`tests/fixtures/live_dataset_cases_expected/`.

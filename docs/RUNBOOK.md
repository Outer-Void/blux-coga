## Runbook

### Local setup (Linux/macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
pytest
```

### Termux (native)

```bash
pkg install python3
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
pytest
```

### Termux + proot Debian

Run the following inside the Debian shell:

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
pytest
```

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
pytest
```

### Canonical file-mode run

```bash
blux-coga run --input path/to/problem.json --output-dir out
```

### Acceptance harness

```bash
blux-coga accept --fixtures path/to/fixtures --output-dir out
```

### Freeze anchoring note

- Treat `blux-coga run --input ... --output-dir ...` as the authoritative
  integration path for datasets/exports.
- Use `run_header.input_hash` plus optional SHA-256 of emitted canonical output
  files when anchoring training/export manifests.

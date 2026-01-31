## Runbook

### Local setup (Linux/macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pytest
```

### Termux (native)

```bash
pkg update
pkg install python3 git
python -m venv .venv
source .venv/bin/activate
pip install -e .
pytest
```

### Termux + proot Debian

```bash
pkg update
pkg install proot-distro
proot-distro install debian
proot-distro login debian
sudo apt update
sudo apt install -y python3 python3-venv git
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pytest
```

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
pytest
```

### Acceptance harness

```bash
blux-coga accept --fixtures path/to/fixtures --out out
```

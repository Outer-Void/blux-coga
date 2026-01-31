## Platforms

### Termux (native)

```bash
pkg update
pkg install python git
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
apt update
apt install -y python3 python3-venv git
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pytest
```

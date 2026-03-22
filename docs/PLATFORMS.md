## Platforms

### Termux (native)

Install Python with Termux packages, then use the Termux runner:

```bash
pkg update
pkg install python3 git
./CogA_mux.sh --in path/to/problem.json --out out/
```

### Termux + proot Debian

Install and enter Debian from Termux, then run the Debian runner inside the
Debian environment:

```bash
pkg update
pkg install proot-distro
proot-distro install debian
proot-distro login debian
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
./CogA_proot.sh --in path/to/problem.json --out out/
```

### Linux (Debian/Ubuntu)

```bash
./CogA.sh --in path/to/problem.json --out out/
```

### macOS

```bash
./CogA.sh --in path/to/problem.json --out out/
```

### Windows (PowerShell)

```powershell
.\CogA.ps1 --in path\to\problem.json --out out\
```

Across platforms, the canonical CLI form remains:

```bash
blux-coga run --input path/to/problem.json --output-dir out
```

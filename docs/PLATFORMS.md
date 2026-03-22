## Platforms

### Termux (native)

Install Python natively in Termux, then run the Termux wrapper:

```bash
pkg install python3
./CogA_mux.sh run --in path/to/problem.json --out out/
```

### Termux + proot Debian

Inside the Debian shell started from Termux, install dependencies with apt, then
run the Debian wrapper:

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git
./CogA_proot.sh run --in path/to/problem.json --out out/
```

### Linux (Debian/Ubuntu)

```bash
./CogA.sh run --in path/to/problem.json --out out/
```

### macOS

```bash
./CogA.sh run --in path/to/problem.json --out out/
```

### Windows (PowerShell)

```powershell
.\CogA.ps1 run --in path\to\problem.json --out out\
```

Across platforms, the canonical CLI form remains:

```bash
blux-coga run --input path/to/problem.json --output-dir out
```

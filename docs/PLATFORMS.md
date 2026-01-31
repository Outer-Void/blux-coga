## Platforms

### Termux (native)

```bash
./CogA_mux.sh --in path/to/problem.json --out out/
```

### Termux + proot Debian

```bash
pkg update
pkg install proot-distro
proot-distro install debian
proot-distro login debian
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

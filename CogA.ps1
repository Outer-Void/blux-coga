param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

if ($Args.Count -eq 0) {
    Write-Host "Usage: .\\CogA.ps1 --in <problem.json> --out <out_dir> [--profile <id>|--profile-file <path>] [--interactive]"
    exit 1
}

$pythonCmd = if (Get-Command py -ErrorAction SilentlyContinue) { @("py", "-3") } else { @("python") }

if (-not (Test-Path ".venv")) {
    & $pythonCmd -m venv .venv
}

$venvPython = Join-Path ".venv" "Scripts\python.exe"

$profileCheck = @'
from pathlib import Path
import tomllib
data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
extras = data.get("project", {}).get("optional-dependencies", {})
raise SystemExit(0 if "dev" in extras else 1)
'@

& $venvPython -c $profileCheck

$installTarget = if ($LASTEXITCODE -eq 0) { ".[dev]" } else { "." }

& $venvPython -m pip install -e $installTarget
& $venvPython -m blux_coga @Args

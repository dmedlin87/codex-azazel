# PowerShell start script for Codex Azazel / BCE CLI
# Usage examples:
#   ./start.ps1 character david
#   ./start.ps1 event exodus

# Activate local virtual environment if present
$venvActivate = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
}

# Run the BCE CLI, forwarding all arguments
python -m bce.cli @Args

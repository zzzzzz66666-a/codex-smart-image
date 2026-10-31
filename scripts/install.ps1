param(
    [string]$PythonPath,
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA 'CodexSmartImage\marketplace'),
    [switch]$PrepareOnly
)
$ErrorActionPreference = 'Stop'
if (-not $PythonPath) {
    $runtime = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $runtime) { $PythonPath = $runtime }
    else {
        $found = Get-Command python -ErrorAction SilentlyContinue
        if ($found) { $PythonPath = $found.Source }
        else { throw 'Python 3.11+ not found. Pass -PythonPath with an absolute python.exe path.' }
    }
}
if (-not (Test-Path -LiteralPath $PythonPath)) { throw 'Python executable not found.' }
& $PythonPath (Join-Path $PSScriptRoot 'prepare_install.py') --destination $InstallRoot
if ($LASTEXITCODE -ne 0) { throw 'Preparing the local marketplace failed.' }
if ($PrepareOnly) { Write-Output 'Marketplace prepared; Codex configuration was not changed.'; return }
$codexCommand = Get-Command codex -ErrorAction Stop
& $codexCommand.Source plugin marketplace add $InstallRoot --json
if ($LASTEXITCODE -ne 0) { throw 'Registering the local marketplace failed.' }
& $codexCommand.Source plugin add 'smart-image@smart-image-local' --json
if ($LASTEXITCODE -ne 0) { throw 'Installing the plugin failed.' }
Write-Output 'Installed. Configure your API key locally, then open a new Codex chat to load the plugin.'

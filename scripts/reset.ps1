param([string]$PythonPath, [switch]$ConfirmReset, [switch]$Reconfigure)
$ErrorActionPreference = 'Stop'
$runtimeRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if (-not $PythonPath) {
    $candidate = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $candidate -PathType Leaf) { $PythonPath = $candidate }
    else {
        $command = Get-Command python -ErrorAction SilentlyContinue
        if ($command) { $PythonPath = $command.Source }
    }
}
if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw 'Python 3.11+ not found. Pass -PythonPath with your actual python.exe.'
}
Push-Location -LiteralPath $runtimeRoot
try {
    # Keep the original path until all its ancestors have been checked for redirection.
    # default_home() resolves a custom home too early for this safety preflight.
    # JSON escaping keeps non-ASCII paths safe in Windows PowerShell 5.1 pipes.
    $homeCode = @(
        'import json, os',
        'from pathlib import Path',
        "value=os.environ.get('CODEX_SMART_IMAGE_HOME')",
        "home=Path(value).expanduser() if value else Path(os.environ.get('LOCALAPPDATA',Path.home()/'.local'/'share'))/'CodexSmartImage'",
        "if '..' in home.parts: raise ValueError('Reset requires a normalized data-home path')",
        'print(json.dumps(str(home.absolute())))'
    ) -join "`n"
    $homeJson = & $PythonPath -c $homeCode
    if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve the plugin data directory.' }
    $resetRoot = [IO.Path]::GetFullPath(($homeJson | ConvertFrom-Json)).TrimEnd('\')
    $protected = @([IO.Path]::GetPathRoot($resetRoot), $runtimeRoot, $env:USERPROFILE, $env:LOCALAPPDATA, $env:APPDATA, $env:WINDIR)
    foreach ($path in $protected) {
        if ($path -and $resetRoot -eq [IO.Path]::GetFullPath($path).TrimEnd('\')) {
            throw 'Refusing to reset a broad system, profile or runtime directory.'
        }
    }
    $ancestor = $resetRoot
    while ($ancestor) {
        if ((Test-Path -LiteralPath $ancestor) -and
            ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw 'Refusing a redirected data directory or ancestor.'
        }
        $parent = [IO.Directory]::GetParent($ancestor)
        if (-not $parent) { break }
        $ancestor = $parent.FullName
    }
    $targets = @()
    foreach ($name in @('config.json','api-key.dpapi','requests','logs')) {
        $path = [IO.Path]::GetFullPath((Join-Path $resetRoot $name))
        if (-not $path.StartsWith($resetRoot + '\',[StringComparison]::OrdinalIgnoreCase)) {
            throw 'Reset target escaped the verified data directory.'
        }
        if (Test-Path -LiteralPath $path) { $targets += Get-Item -LiteralPath $path -Force }
    }
    if (Test-Path -LiteralPath $resetRoot -PathType Container) {
        $targets += @(Get-ChildItem -LiteralPath $resetRoot -Force -File | Where-Object {
            $_.Name -like '.writing-*' -or $_.Name -like 'config.json.*' -or $_.Name -like 'api-key.dpapi.*' -or $_.Extension -eq '.log'
        })
    }
    # Complete redirection validation before deleting any selected entry.
    foreach ($item in $targets) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Refusing a redirected reset entry.' }
        if ($item.PSIsContainer -and @(Get-ChildItem -LiteralPath $item.FullName -Recurse -Force -Attributes ReparsePoint).Count) {
            throw 'Refusing a record directory containing redirected entries.'
        }
    }
    if (-not $ConfirmReset) {
        [pscustomobject]@{reset_performed=$false; confirmation_required=$true; entries_selected=$targets.Count;
            message='Pass -ConfirmReset to delete local configuration, encrypted key, requests and logs. Images and plugin files are retained.'} | ConvertTo-Json
        return
    }
    if ($env:CODEX_SMART_IMAGE_API_KEY) {
        throw 'An environment API key is active. Remove it in your own terminal/settings before resetting; no files were deleted.'
    }
    $removedFiles = 0
    foreach ($item in $targets) {
        $target = [IO.Path]::GetFullPath($item.FullName)
        if (-not $target.StartsWith($resetRoot + '\',[StringComparison]::OrdinalIgnoreCase) -or
            $target.StartsWith((Join-Path $resetRoot 'marketplace') + '\',[StringComparison]::OrdinalIgnoreCase)) {
            throw 'Final reset path validation failed.'
        }
        if ($item.PSIsContainer) {
            $removedFiles += @(Get-ChildItem -LiteralPath $target -File -Recurse -Force).Count
            Remove-Item -LiteralPath $target -Recurse -Force
        } else {
            $removedFiles++
            Remove-Item -LiteralPath $target -Force
        }
        if (Test-Path -LiteralPath $target) { throw 'Selected local state was not removed.' }
    }
    $statusText = & $PythonPath '.\scripts\run.py' status
    if ($LASTEXITCODE -ne 0) { throw 'Post-reset verification failed.' }
    $status = $statusText | ConvertFrom-Json
    if ($status.provider_configured -or $status.key_configured -or $status.ready) { throw 'Old configuration is still active.' }
    [pscustomobject]@{reset_performed=$true; removed_files=$removedFiles; provider_configured=$false;
        key_configured=$false; ready=$false; plugin_retained=$true; images_changed=$false} | ConvertTo-Json
    if ($Reconfigure) { & (Join-Path $PSScriptRoot 'configure.ps1') -PythonPath $PythonPath }
} finally { Pop-Location }

param([string]$PythonPath, [switch]$CheckOnly, [switch]$ReplaceKey)
$ErrorActionPreference = 'Stop'
$setupRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if (-not (Test-Path -LiteralPath (Join-Path $setupRoot 'smart_image\cli.py') -PathType Leaf)) {
    throw 'Plugin runtime missing beside this configuration script.'
}
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

# A relative entry point avoids carrying quoted user-profile paths into Python.
Push-Location -LiteralPath $setupRoot
try {
    $setupHelp = & $PythonPath '.\scripts\run.py' --help
    if ($LASTEXITCODE -ne 0 -or ([string]$setupHelp -notmatch 'configure')) {
        throw 'The plugin entry point could not start.'
    }
    if ($CheckOnly) {
        [pscustomobject]@{runtime_found=$true; entry_point_started=$true; configuration_changed=$false} | ConvertTo-Json
        return
    }
    if ($ReplaceKey -and $env:CODEX_SMART_IMAGE_API_KEY) {
        throw 'An environment API key overrides the encrypted local key. Remove or update that environment setting before -ReplaceKey; no settings were changed.'
    }
    $setupStatusText = & $PythonPath '.\scripts\run.py' status
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read existing configuration. No settings were changed.' }
    $setupStatus = $setupStatusText | ConvertFrom-Json
    $setupApiBase = (Read-Host 'API Base URL (usually ends with /v1; Enter keeps existing)').Trim()
    if ([string]::IsNullOrWhiteSpace($setupApiBase)) { $setupApiBase = [string]$setupStatus.base_url }
    if ([string]::IsNullOrWhiteSpace($setupApiBase)) { throw 'API Base URL is required.' }
    $setupModel = (Read-Host 'Model ID (Enter keeps existing/default)').Trim()
    if ([string]::IsNullOrWhiteSpace($setupModel)) { $setupModel = [string]$setupStatus.model }
    if ([string]::IsNullOrWhiteSpace($setupModel)) { $setupModel = 'gpt-image-2' }

    # Never ask for a key at an ordinary, visible Read-Host selection prompt.
    if ($ReplaceKey -or -not $setupStatus.key_configured) {
        Write-Host 'Next: enter your API Key and press Enter. Input is hidden.'
        $setupResult = & $PythonPath '.\scripts\run.py' configure --base-url $setupApiBase --model $setupModel
    } else {
        Write-Host 'Keeping the existing encrypted key. Use -ReplaceKey to enter a new key.'
        $setupResult = & $PythonPath '.\scripts\run.py' configure --base-url $setupApiBase --model $setupModel --keep-key
    }
    if ($LASTEXITCODE -ne 0) { throw 'Configuration failed. Review the preceding error.' }
    $setupResult | ConvertFrom-Json | Select-Object provider_configured,key_configured,ready
    Write-Host 'Local configuration saved. No image generation was requested.'
} finally { Pop-Location }

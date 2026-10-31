param()
$ErrorActionPreference = 'Stop'
$codexCommand = Get-Command codex -ErrorAction Stop
& $codexCommand.Source plugin remove 'smart-image@smart-image-local'
if ($LASTEXITCODE -ne 0) { throw 'Removing the plugin failed; local data was preserved.' }
Write-Output 'Plugin removed. API configuration, encrypted key, request history, marketplace files and project images were preserved.'

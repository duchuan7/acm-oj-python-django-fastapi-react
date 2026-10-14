$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$ownedRoot = (Get-Item -LiteralPath $PWD).FullName
foreach($name in @('web','judge','api')) {
    $pidFile = Join-Path $ownedRoot ".runtime\$name.pid"
    if(-not (Test-Path -LiteralPath $pidFile)){continue}
    $processId = [int](Get-Content -LiteralPath $pidFile)
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $processId"
    if($process) {
        if(-not $process.CommandLine.Contains($ownedRoot)){throw "PID $processId no longer belongs to this checkout; refusing to stop it."}
        Stop-Process -Id $processId
    }
    Remove-Item -LiteralPath $pidFile
}
Write-Output 'Stopped checkout-owned app processes. Database, queue, cache and their data are kept.'


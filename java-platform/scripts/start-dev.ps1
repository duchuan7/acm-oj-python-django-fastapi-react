param(
    [string]$JavaHome = $env:JAVA_HOME,
    [switch]$SkipBuild,
    [switch]$SkipSandboxBuild,
    [switch]$NoWeb
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
& "$PSScriptRoot\setup.ps1"
foreach ($line in Get-Content -LiteralPath '.env') {
    if ($line -match '^([A-Z_]+)=(.*)$') { [Environment]::SetEnvironmentVariable($Matches[1],$Matches[2],'Process') }
}
if (-not $JavaHome) { throw 'Pass -JavaHome with a JDK 21 directory, or set JAVA_HOME.' }
$javaExe = Join-Path $JavaHome 'bin\java.exe'
$version = & $javaExe -version 2>&1 | Out-String
if ($version -notmatch 'version "21\.') { throw 'JDK 21 is required.' }
$env:JAVA_HOME = $JavaHome
$env:Path = (Join-Path $JavaHome 'bin') + ';' + $env:Path
$env:SMTP_PORT = '1026'
$env:OJ_MODE = 'api'
$env:SPRING_PROFILES_ACTIVE = ''
New-Item -ItemType Directory -Path '.runtime' -Force | Out-Null
foreach($name in @('api','judge','web')) {
    $pidFile = Join-Path $PWD ".runtime\$name.pid"
    if((Test-Path -LiteralPath $pidFile) -and (Get-Process -Id ([int](Get-Content -LiteralPath $pidFile)) -ErrorAction SilentlyContinue)) {
        throw "$name is already running. Run scripts/stop-dev.ps1 before building or restarting."
    }
}
$ports = if($NoWeb){ @(8088) }else{ @(8088,5175) }
foreach($port in $ports){
    if(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue){
        throw "Port $port is already in use. Stop the existing app stack before starting development processes."
    }
}
docker compose up -d --wait mysql redis rabbit mailpit
if ($LASTEXITCODE -ne 0) { throw 'Dependency startup failed.' }
if (-not $SkipSandboxBuild) {
    docker compose build sandbox
    if ($LASTEXITCODE -ne 0) { throw 'Sandbox build failed.' }
}
if (-not $SkipBuild) {
    Push-Location backend
    try { mvn.cmd -B -ntp verify; if ($LASTEXITCODE -ne 0) { throw 'Maven verification failed.' } }
    finally { Pop-Location }
}
$jarPath = Join-Path $PWD 'backend\target\oj-1.0.0.jar'
function Start-OwnedProcess([string]$name,[string]$executable,[string[]]$arguments) {
    $pidFile = Join-Path $PWD ".runtime\$name.pid"
    if (Test-Path -LiteralPath $pidFile) {
        $existing = Get-Process -Id ([int](Get-Content -LiteralPath $pidFile)) -ErrorAction SilentlyContinue
        if ($existing) { throw "$name is already running; use stop-dev.ps1 before restarting." }
    }
    $process = Start-Process -FilePath $executable -ArgumentList $arguments -WorkingDirectory $PWD -WindowStyle Hidden -PassThru -RedirectStandardOutput ".runtime\$name.out.log" -RedirectStandardError ".runtime\$name.err.log"
    Set-Content -LiteralPath $pidFile -Value $process.Id
}
Start-OwnedProcess 'api' $javaExe @('-jar',('"' + $jarPath + '"'))
$ready = $false
for ($attempt=0; $attempt -lt 60; $attempt++) {
    try { $health=Invoke-RestMethod 'http://127.0.0.1:8088/actuator/health' -TimeoutSec 10 -NoProxy; if($health.status -eq 'UP'){$ready=$true;break} } catch {}
    Start-Sleep -Seconds 1
}
if (-not $ready) { throw 'API readiness failed; inspect .runtime/api.out.log and api.err.log.' }
$env:OJ_MODE = 'judge'
$env:SPRING_PROFILES_ACTIVE = 'judge'
Start-OwnedProcess 'judge' $javaExe @('-jar',('"' + $jarPath + '"'))
if (-not $NoWeb) {
    Push-Location frontend
    try { if (-not (Test-Path node_modules)) { npm.cmd ci; if($LASTEXITCODE -ne 0){throw 'npm ci failed'} } }
    finally { Pop-Location }
    $vite = Join-Path $PWD 'frontend\node_modules\vite\bin\vite.js'
    $viteConfig = Join-Path $PWD 'frontend\vite.config.js'
    Start-OwnedProcess 'web' (Get-Command node.exe).Source @(('"' + $vite + '"'),'--config',('"' + $viteConfig + '"'),'--host','127.0.0.1','--port','5175','--strictPort')
}
Write-Output 'API: http://127.0.0.1:8088/api | Web: http://127.0.0.1:5175 | Test mailbox: http://127.0.0.1:8026'

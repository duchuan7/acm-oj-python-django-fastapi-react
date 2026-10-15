param([string]$JavaHome=$env:JAVA_HOME,[switch]$Check)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
if(-not $JavaHome){throw 'Set JAVA_HOME to JDK 21, or pass -JavaHome.'}
$javaName=if($IsWindows){'java.exe'}else{'java'}
$javaExe=Join-Path $JavaHome ("bin/"+$javaName)
$toolDirectory=Join-Path $projectRoot '.runtime/tools'
New-Item -ItemType Directory -Force -Path $toolDirectory | Out-Null
$jarPath=Join-Path $toolDirectory 'google-java-format-1.28.0.jar'
$expected='32342E7C1B4600F80DF3471DA46AEE8012D3E1445D5EA1BE1FB71289B07CC735'
if(-not (Test-Path -LiteralPath $jarPath)){
    Invoke-WebRequest 'https://repo.maven.apache.org/maven2/com/google/googlejavaformat/google-java-format/1.28.0/google-java-format-1.28.0-all-deps.jar' -OutFile $jarPath
}
if((Get-FileHash -LiteralPath $jarPath -Algorithm SHA256).Hash -ne $expected){throw 'Formatter SHA-256 mismatch.'}
Push-Location (Join-Path $projectRoot 'backend')
try {
    $javaFiles=@(Get-ChildItem -LiteralPath src -Filter '*.java' -Recurse -File | Select-Object -ExpandProperty FullName)
    if($Check){ & $javaExe -jar $jarPath --aosp --dry-run --set-exit-if-changed $javaFiles }
    else { & $javaExe -jar $jarPath --aosp --replace $javaFiles }
    if($LASTEXITCODE -ne 0){throw 'Java formatting check failed.'}
} finally {Pop-Location}

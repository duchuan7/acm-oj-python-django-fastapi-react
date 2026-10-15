$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (Test-Path -LiteralPath '.env') {
    Write-Output '.env already exists; kept existing secrets.'
    exit 0
}
function New-Secret { [Convert]::ToHexString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLowerInvariant() }
$lines = @(
    'DB_PASSWORD=' + (New-Secret)
    'MYSQL_ROOT_PASSWORD=' + (New-Secret)
    'RABBIT_PASSWORD=' + (New-Secret)
    'JWT_SECRET=' + (New-Secret)
    'ADMIN_USERNAME=admin'
    'ADMIN_PASSWORD=' + (New-Secret)
    'SEED_DEMO=true'
)
[System.IO.File]::WriteAllLines((Join-Path $PWD '.env'), $lines, [System.Text.UTF8Encoding]::new($false))
Write-Output 'Created .env with random secrets. Read ADMIN_USERNAME and ADMIN_PASSWORD locally to sign in.'

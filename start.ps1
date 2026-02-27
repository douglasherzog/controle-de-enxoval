$ErrorActionPreference = "Stop"

$envFile = Join-Path $PSScriptRoot ".env"
$envExample = Join-Path $PSScriptRoot ".env.example"

if (-not (Test-Path $envFile)) {
    if (-not (Test-Path $envExample)) {
        Write-Error "Arquivo .env.example não encontrado."
    }
    Copy-Item $envExample $envFile
    Write-Host "Criado .env a partir de .env.example"
}

docker compose up -d --build

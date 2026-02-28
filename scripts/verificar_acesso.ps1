$ErrorActionPreference = "Stop"

Write-Host "🔎 Verificação de acesso externo (Tailscale + Docker)" -ForegroundColor Cyan
Write-Host "====================================================="

function Resolve-TailscalePath {
    $cmd = Get-Command tailscale.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Path
    }

    $candidates = @(
        "$env:ProgramFiles\Tailscale\tailscale.exe",
        "$env:LOCALAPPDATA\Tailscale\tailscale.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Show-Section($title) {
    Write-Host "" 
    Write-Host $title -ForegroundColor Yellow
    Write-Host ("-" * $title.Length)
}

$tailscalePath = Resolve-TailscalePath

Show-Section "1) Tailscale"
if (-not $tailscalePath) {
    Write-Host "❌ Tailscale não encontrado no PATH." -ForegroundColor Red
    Write-Host "   Instale ou abra o aplicativo e tente novamente." -ForegroundColor DarkGray
} else {
    Write-Host "✅ Executável: $tailscalePath" -ForegroundColor Green

    try {
        $status = & $tailscalePath status 2>$null
        if (-not $status) {
            throw "Sem saída do comando tailscale status"
        }

        $ip = & $tailscalePath ip -4 2>$null
        $hostname = & $tailscalePath status --json 2>$null | ConvertFrom-Json | Select-Object -ExpandProperty Self -ErrorAction SilentlyContinue | Select-Object -ExpandProperty DNSName -ErrorAction SilentlyContinue

        Write-Host "✅ tailscale status: OK" -ForegroundColor Green
        if ($ip) {
            Write-Host "🌐 IP Tailscale: $ip"
        }
        if ($hostname) {
            Write-Host "🏷️  Hostname: $hostname"
        }

        if ($ip) {
            Write-Host "➡️  URL externo: http://$ip:5000" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "❌ Falha ao executar tailscale." -ForegroundColor Red
        Write-Host "   $_" -ForegroundColor DarkGray
    }
}

Show-Section "2) Docker Compose"
try {
    $composeVersion = docker compose version 2>$null
    if (-not $composeVersion) {
        throw "docker compose não disponível"
    }

    Write-Host "✅ $composeVersion" -ForegroundColor Green
    $ps = docker compose ps 2>$null
    if ($ps) {
        Write-Host "📦 Containers:" 
        Write-Host $ps
    } else {
        Write-Host "⚠️  docker compose ps sem saída." -ForegroundColor DarkYellow
    }
} catch {
    Write-Host "❌ Docker Compose não disponível." -ForegroundColor Red
    Write-Host "   Instale o Docker Desktop e tente novamente." -ForegroundColor DarkGray
}

Show-Section "3) Teste local (HTTP)"
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:5000" -Method GET -TimeoutSec 5
    Write-Host "✅ HTTP local: $($resp.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ Falha ao acessar http://localhost:5000" -ForegroundColor Red
    Write-Host "   Verifique se o container web está rodando." -ForegroundColor DarkGray
}

Write-Host "" 
Write-Host "✅ Verificação concluída." -ForegroundColor Green

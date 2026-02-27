# Controle de Enxoval

Projeto inicial em Flask + Postgres para cadastro de enxoval e rastreabilidade.

## Documentação simples

- Manual do usuário: `docs/manual.md`
- Registro do que foi feito: `docs/status.md`

## Como subir (Docker Compose)

### Opção rápida (Windows)

```powershell
./start.ps1
```

### Manual

1. Copie o `.env.example` para `.env`.
2. Rode:

```bash
docker compose up -d --build
```

Acesse: <http://localhost:5000>

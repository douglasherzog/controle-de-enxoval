# Manual simples – Controle de Enxoval

Este guia explica **como usar o sistema** e **o que cada tela faz**.

## 1) Como iniciar o sistema

**Opção rápida (Windows)**
```
./start.ps1
```

**Opção manual**
1. Copie `.env.example` para `.env`.
2. Rode:
```
docker compose up -d --build
```

Acesse: <http://localhost:5000>

---

## 2) Fluxo do dia a dia (passo a passo)

### Passo 1 – Cadastrar peças
- Preencha o formulário “Cadastrar peça”.
- Use um **código único** (ex.: `MO-0001`).
- **RFID** é opcional, mas recomendado.
- Informe tamanho, colaborador e setor quando souber.

### Passo 2 – Registrar movimentações
- Sempre que a peça **mudar de local** (estoque → entregue → em lavagem), atualize o status.
- Isso gera um **histórico automático**.

### Passo 3 – Acompanhar pendências
- O painel mostra peças pendentes, extraviadas e estoque atual.

---

## 3) Importação em lote (CSV)

Quando tiver muitas peças, use o **Importar CSV** no painel.

Arquivos disponíveis no repositório:
- `docs/modelo-importacao-enxoval.csv` (exemplo preenchido)
- `docs/modelo-importacao-enxoval-vazio.csv` (somente cabeçalho)
- `docs/enxoval-1400-pratico.csv` (1400 linhas geradas)

Campos obrigatórios no CSV:
- `nome`, `codigo`, `tamanho`

Status válidos:
- `estoque`, `entregue`, `em_uso`, `em_lavagem`, `disponivel`, `extraviado`

---

## 4) Gerador automático de CSV

Script para gerar arquivos grandes automaticamente:
```
python scripts/gerar_csv.py --modo pratico --total 1400 --saida docs/enxoval-1400-pratico.csv
```

Modos disponíveis:
- `pratico` (frigorífico – recomendado)
- `equilibrado`
- `personalizado` (usa `docs/config-geracao-exemplo.json`)

---

## 5) Histórico por peça

Clique em **“Ver histórico”** para ver todas as movimentações da peça.

---

## 6) Relatórios do painel

- **Inventário por tipo** (quantidade por item)
- **Inventário por setor** (onde as peças estão)
- **Pendências e extravios**

---

## 7) Testes (validação rápida)

Rodar testes básicos:
```
python -m unittest discover -s tests
```

---

## 8) O que já foi implementado

- Cadastro completo de peças (RFID, tamanho, colaborador, setor)
- Movimentações e histórico por peça
- Relatórios iniciais
- Importação CSV (painel e script)
- Gerador automático de CSV

---

## 9) O que pode melhorar (próximos passos)

- Alertas automáticos de atraso/devolução
- Painel por setor com SLA de retorno
- Integração direta com leitores RFID
- Dashboard com gráficos
- Controle de custos por peça/setor

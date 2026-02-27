import csv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.models import EnxovalItem, Movimentacao, db

STATUS_OPTIONS = {
    "estoque",
    "entregue",
    "em_uso",
    "em_lavagem",
    "disponivel",
    "extraviado",
}


def criar_item(*, linha: dict[str, str]) -> None:
    nome = (linha.get("nome") or "").strip()
    codigo = (linha.get("codigo") or "").strip().upper()
    tag_rfid = (linha.get("tag_rfid") or "").strip().upper() or None
    tamanho = (linha.get("tamanho") or "").strip().upper()
    tamanho_customizado = (linha.get("tamanho_customizado") or "").strip() or None
    descricao = (linha.get("descricao") or "").strip() or None
    colaborador = (linha.get("colaborador") or "").strip() or None
    setor = (linha.get("setor") or "").strip() or None
    status = (linha.get("status") or "").strip().lower() or "estoque"
    observacao = (linha.get("observacao") or "").strip() or "Importacao CSV"

    if not nome or not codigo or not tamanho:
        return
    if status not in STATUS_OPTIONS:
        status = "estoque"

    item = EnxovalItem(
        nome=nome,
        codigo=codigo,
        tag_rfid=tag_rfid,
        tamanho=tamanho,
        tamanho_customizado=tamanho_customizado,
        descricao=descricao,
        colaborador=colaborador,
        setor=setor,
        status=status,
    )
    db.session.add(item)
    db.session.add(
        Movimentacao(
            item=item,
            status=status,
            colaborador=colaborador,
            setor=setor,
            observacao=observacao,
        )
    )


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Uso: python scripts/import_csv.py caminho/arquivo.csv")

    caminho = Path(sys.argv[1])
    if not caminho.exists():
        raise SystemExit("Arquivo CSV nao encontrado.")

    app = create_app()
    with app.app_context():
        with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
            leitor = csv.DictReader(arquivo)
            for linha in leitor:
                criar_item(linha=linha)
        db.session.commit()


if __name__ == "__main__":
    main()

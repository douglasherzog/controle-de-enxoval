import csv
from io import StringIO

from flask import Blueprint, redirect, render_template, request, url_for
from sqlalchemy import func

from .models import EnxovalItem, Movimentacao, db


STATUS_OPTIONS = [
    "estoque",
    "entregue",
    "em_uso",
    "em_lavagem",
    "disponivel",
    "extraviado",
]


main_bp = Blueprint("main", __name__)


def _criar_item(
    *,
    nome: str,
    codigo: str,
    tag_rfid: str | None,
    tamanho: str,
    tamanho_customizado: str | None,
    descricao: str | None,
    colaborador: str | None,
    setor: str | None,
    status: str,
    observacao: str,
) -> None:
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


@main_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        codigo = (request.form.get("codigo") or "").strip().upper()
        tag_rfid = (request.form.get("tag_rfid") or "").strip().upper() or None
        tamanho = (request.form.get("tamanho") or "").strip().upper()
        tamanho_customizado = (request.form.get("tamanho_customizado") or "").strip() or None
        descricao = (request.form.get("descricao") or "").strip() or None
        colaborador = (request.form.get("colaborador") or "").strip() or None
        setor = (request.form.get("setor") or "").strip() or None

        if nome and codigo and tamanho:
            _criar_item(
                nome=nome,
                codigo=codigo,
                tag_rfid=tag_rfid,
                tamanho=tamanho,
                tamanho_customizado=tamanho_customizado,
                descricao=descricao,
                colaborador=colaborador,
                setor=setor,
                status="estoque",
                observacao="Cadastro inicial",
            )
            db.session.commit()
        return redirect(url_for("main.index"))


    itens = EnxovalItem.query.order_by(EnxovalItem.id.desc()).all()
    status_counts = dict(
        db.session.query(EnxovalItem.status, func.count(EnxovalItem.id))
        .group_by(EnxovalItem.status)
        .all()
    )
    pendentes_status = {"entregue", "em_uso", "em_lavagem"}
    pendentes = sum(status_counts.get(status, 0) for status in pendentes_status)
    extraviados = status_counts.get("extraviado", 0)
    total_ativos = (
        db.session.query(func.count(EnxovalItem.id))
        .filter(EnxovalItem.ativo.is_(True))
        .scalar()
        or 0
    )
    por_tipo = (
        db.session.query(EnxovalItem.nome, func.count(EnxovalItem.id))
        .filter(EnxovalItem.ativo.is_(True))
        .group_by(EnxovalItem.nome)
        .order_by(EnxovalItem.nome.asc())
        .all()
    )
    por_setor = (
        db.session.query(EnxovalItem.setor, func.count(EnxovalItem.id))
        .filter(EnxovalItem.ativo.is_(True))
        .group_by(EnxovalItem.setor)
        .order_by(EnxovalItem.setor.asc())
        .all()
    )
    return render_template(
        "index.html",
        itens=itens,
        status_options=STATUS_OPTIONS,
        status_counts=status_counts,
        pendentes=pendentes,
        extraviados=extraviados,
        total_ativos=total_ativos,
        por_tipo=por_tipo,
        por_setor=por_setor,
    )


@main_bp.route("/item/<int:item_id>")
def item_detalhe(item_id: int):
    item = db.session.get(EnxovalItem, item_id)
    if not item:
        return redirect(url_for("main.index"))

    movimentacoes = (
        Movimentacao.query.filter_by(item_id=item_id)
        .order_by(Movimentacao.created_at.desc())
        .all()
    )
    return render_template("item.html", item=item, movimentacoes=movimentacoes)


@main_bp.route("/importar", methods=["POST"])
def importar_csv():
    arquivo = request.files.get("arquivo")
    if not arquivo or not arquivo.filename:
        return redirect(url_for("main.index"))

    conteudo = arquivo.stream.read().decode("utf-8-sig")
    leitor = csv.DictReader(StringIO(conteudo))
    for linha in leitor:
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
            continue
        if status not in STATUS_OPTIONS:
            status = "estoque"

        _criar_item(
            nome=nome,
            codigo=codigo,
            tag_rfid=tag_rfid,
            tamanho=tamanho,
            tamanho_customizado=tamanho_customizado,
            descricao=descricao,
            colaborador=colaborador,
            setor=setor,
            status=status,
            observacao=observacao,
        )

    db.session.commit()
    return redirect(url_for("main.index"))


@main_bp.route("/inativar/<int:item_id>", methods=["POST"])
def inativar_item(item_id: int):
    item = db.session.get(EnxovalItem, item_id)
    if item:
        item.ativo = False
        db.session.add(item)
        db.session.commit()
    return redirect(url_for("main.index"))


@main_bp.route("/movimentar/<int:item_id>", methods=["POST"])
def movimentar_item(item_id: int):
    item = db.session.get(EnxovalItem, item_id)
    if not item:
        return redirect(url_for("main.index"))

    status = (request.form.get("status") or "").strip()
    colaborador = (request.form.get("colaborador") or "").strip() or None
    setor = (request.form.get("setor") or "").strip() or None
    observacao = (request.form.get("observacao") or "").strip() or None

    if status in STATUS_OPTIONS:
        item.status = status
        item.colaborador = colaborador
        item.setor = setor
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
        db.session.commit()

    return redirect(url_for("main.index"))

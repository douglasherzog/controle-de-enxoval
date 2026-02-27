import csv
from datetime import datetime, timezone
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
ALERT_STATUS = {"entregue", "em_uso"}
ALERT_ATENCAO_DIAS = 2
ALERT_CRITICO_DIAS = 4
STATUS_COLORS = {
    "estoque": "#2d6a4f",
    "entregue": "#d97706",
    "em_uso": "#2563eb",
    "em_lavagem": "#0ea5e9",
    "disponivel": "#14b8a6",
    "extraviado": "#dc2626",
}


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

    ultima_mov_subquery = (
        db.session.query(
            Movimentacao.item_id,
            func.max(Movimentacao.created_at).label("ultima_mov"),
        )
        .group_by(Movimentacao.item_id)
        .subquery()
    )
    itens_alerta = (
        db.session.query(EnxovalItem, ultima_mov_subquery.c.ultima_mov)
        .join(ultima_mov_subquery, EnxovalItem.id == ultima_mov_subquery.c.item_id)
        .filter(EnxovalItem.ativo.is_(True), EnxovalItem.status.in_(ALERT_STATUS))
        .all()
    )
    agora = datetime.now(timezone.utc)
    alerta_total = {"atencao": 0, "critico": 0}
    alerta_por_setor: dict[str, dict[str, int]] = {}
    alerta_por_colaborador: dict[str, dict[str, int]] = {}

    for item, ultima_mov in itens_alerta:
        if not ultima_mov:
            continue
        if ultima_mov.tzinfo is None:
            ultima_mov = ultima_mov.replace(tzinfo=timezone.utc)
        dias = (agora - ultima_mov).days
        nivel = None
        if dias > ALERT_CRITICO_DIAS:
            nivel = "critico"
        elif dias > ALERT_ATENCAO_DIAS:
            nivel = "atencao"
        if not nivel:
            continue

        alerta_total[nivel] += 1
        setor = item.setor or "Sem setor"
        colaborador = item.colaborador or "Sem colaborador"
        alerta_por_setor.setdefault(setor, {"atencao": 0, "critico": 0})[nivel] += 1
        alerta_por_colaborador.setdefault(colaborador, {"atencao": 0, "critico": 0})[nivel] += 1

    def _ordenar_alertas(dados: dict[str, dict[str, int]]) -> list[tuple[str, int, int, int]]:
        resultado = []
        for chave, valores in dados.items():
            atencao = valores.get("atencao", 0)
            critico = valores.get("critico", 0)
            resultado.append((chave, atencao, critico, atencao + critico))
        return sorted(resultado, key=lambda item: item[3], reverse=True)

    alertas_setor = _ordenar_alertas(alerta_por_setor)
    alertas_colaborador = _ordenar_alertas(alerta_por_colaborador)

    status_chart = []
    total_status = sum(status_counts.values()) or 1
    acumulado = 0.0
    segmentos = []
    for status in STATUS_OPTIONS:
        quantidade = status_counts.get(status, 0)
        if quantidade == 0:
            continue
        percentual = (quantidade / total_status) * 100
        status_chart.append(
            {
                "status": status,
                "quantidade": quantidade,
                "percentual": percentual,
                "color": STATUS_COLORS.get(status, "#94a3b8"),
            }
        )
        inicio = acumulado
        fim = acumulado + percentual
        segmentos.append(
            f"{STATUS_COLORS.get(status, '#94a3b8')} {inicio:.2f}% {fim:.2f}%"
        )
        acumulado = fim
    status_conic = (
        f"conic-gradient({', '.join(segmentos)})" if segmentos else "conic-gradient(#e2e8f0 0% 100%)"
    )
    max_tipo = max((total for _, total in por_tipo), default=1)
    max_setor = max((total for _, total in por_setor), default=1)
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
        alerta_total=alerta_total,
        alertas_setor=alertas_setor,
        alertas_colaborador=alertas_colaborador,
        status_chart=status_chart,
        status_conic=status_conic,
        max_tipo=max_tipo,
        max_setor=max_setor,
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

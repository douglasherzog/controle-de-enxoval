import csv
from datetime import UTC, datetime
from io import StringIO

from flask import Blueprint, redirect, render_template, request, url_for
from sqlalchemy import func, or_

from .models import Colaborador, EnxovalItem, Movimentacao, Setor, TipoPeca, db

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
        novo_setor_nome = (request.form.get("novo_setor_nome") or "").strip()
        novo_tipo_nome = (request.form.get("novo_tipo_nome") or "").strip()
        novo_colaborador_nome = (request.form.get("novo_colaborador_nome") or "").strip()

        # Handle new tipo peca creation
        if nome == "__novo__" and novo_tipo_nome:
            existente = TipoPeca.query.filter(
                func.lower(TipoPeca.nome) == novo_tipo_nome.lower()
            ).one_or_none()
            if existente:
                if not existente.ativo:
                    existente.ativo = True
                    db.session.add(existente)
                    db.session.commit()
                nome = existente.nome
            else:
                novo_tipo = TipoPeca(nome=novo_tipo_nome)
                db.session.add(novo_tipo)
                db.session.commit()
                nome = novo_tipo.nome

        # Handle new colaborador creation
        if colaborador == "__novo__" and novo_colaborador_nome:
            novo_colaborador_telefone = (
                request.form.get("novo_colaborador_telefone") or ""
            ).strip() or None
            existente = Colaborador.query.filter(
                func.lower(Colaborador.nome) == novo_colaborador_nome.lower()
            ).one_or_none()
            if existente:
                if not existente.ativo:
                    existente.ativo = True
                    existente.telefone = novo_colaborador_telefone or existente.telefone
                    db.session.add(existente)
                    db.session.commit()
                colaborador = existente.nome
            else:
                novo_colaborador = Colaborador(
                    nome=novo_colaborador_nome,
                    telefone=novo_colaborador_telefone,
                )
                db.session.add(novo_colaborador)
                db.session.commit()
                colaborador = novo_colaborador.nome

        # Handle new sector creation
        if setor == "__novo__" and novo_setor_nome:
            existente = Setor.query.filter(
                func.lower(Setor.nome) == novo_setor_nome.lower()
            ).one_or_none()
            if existente:
                if not existente.ativo:
                    existente.ativo = True
                    db.session.add(existente)
                    db.session.commit()
                setor = existente.nome
            else:
                novo_setor = Setor(nome=novo_setor_nome)
                db.session.add(novo_setor)
                db.session.commit()
                setor = novo_setor.nome

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

    busca = (request.args.get("busca") or "").strip()
    filtro_status = (request.args.get("status") or "").strip()
    filtro_setor = (request.args.get("setor") or "").strip()
    filtro_colaborador = (request.args.get("colaborador") or "").strip()
    apenas_ativos = request.args.get("ativos", "1") == "1"
    try:
        pagina = max(int(request.args.get("pagina", "1")), 1)
    except ValueError:
        pagina = 1
    try:
        por_pagina = max(int(request.args.get("por_pagina", "25")), 5)
    except ValueError:
        por_pagina = 25

    itens_query = EnxovalItem.query
    if apenas_ativos:
        itens_query = itens_query.filter(EnxovalItem.ativo.is_(True))
    if busca:
        termo = f"%{busca}%"
        itens_query = itens_query.filter(
            (EnxovalItem.nome.ilike(termo)) | (EnxovalItem.codigo.ilike(termo))
        )
    if filtro_status:
        itens_query = itens_query.filter(EnxovalItem.status == filtro_status)
    if filtro_setor:
        if filtro_setor == "__sem__":
            itens_query = itens_query.filter(
                or_(EnxovalItem.setor.is_(None), EnxovalItem.setor == "")
            )
        else:
            itens_query = itens_query.filter(EnxovalItem.setor == filtro_setor)
    if filtro_colaborador:
        itens_query = itens_query.filter(
            EnxovalItem.colaborador.ilike(f"%{filtro_colaborador}%")
        )

    total_itens = itens_query.count()
    total_paginas = max((total_itens + por_pagina - 1) // por_pagina, 1)
    if pagina > total_paginas:
        pagina = total_paginas
    offset = (pagina - 1) * por_pagina
    itens = (
        itens_query.order_by(EnxovalItem.id.desc())
        .offset(offset)
        .limit(por_pagina)
        .all()
    )
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
    # Query para contar peças por tipo (todos os tipos existentes nas peças)
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
    agora = datetime.now(UTC)
    alerta_total = {"atencao": 0, "critico": 0}
    alerta_por_setor: dict[str, dict[str, int]] = {}
    alerta_por_colaborador: dict[str, dict[str, int]] = {}

    for item, ultima_mov in itens_alerta:
        if not ultima_mov:
            continue
        if ultima_mov.tzinfo is None:
            ultima_mov = ultima_mov.replace(tzinfo=UTC)
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
        f"conic-gradient({', '.join(segmentos)})"
        if segmentos
        else "conic-gradient(#e2e8f0 0% 100%)"
    )
    max_tipo = max((total for _, total in por_tipo), default=1)
    max_setor = max((total for _, total in por_setor), default=1)
    tipos_peca_ativos = TipoPeca.query.filter_by(
        ativo=True
    ).order_by(TipoPeca.nome.asc()).all()
    colaboradores_ativos = Colaborador.query.filter_by(
        ativo=True
    ).order_by(Colaborador.nome.asc()).all()
    setores_ativos = Setor.query.filter_by(ativo=True).order_by(Setor.nome.asc()).all()
    setores = Setor.query.order_by(Setor.nome.asc()).all()
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
        tipos_peca_ativos=tipos_peca_ativos,
        colaboradores_ativos=colaboradores_ativos,
        setores=setores,
        setores_ativos=setores_ativos,
        busca=busca,
        filtro_status=filtro_status,
        filtro_setor=filtro_setor,
        filtro_colaborador=filtro_colaborador,
        apenas_ativos=apenas_ativos,
        pagina=pagina,
        por_pagina=por_pagina,
        total_itens=total_itens,
        total_paginas=total_paginas,
        offset=offset,
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


@main_bp.route("/setores", methods=["POST"])
def criar_setor():
    nome = (request.form.get("nome") or "").strip()
    if not nome:
        return redirect(url_for("main.index"))

    existente = (
        Setor.query.filter(func.lower(Setor.nome) == nome.lower()).one_or_none()
    )
    if existente:
        if not existente.ativo:
            existente.ativo = True
            db.session.add(existente)
            db.session.commit()
        return redirect(url_for("main.index"))

    setor = Setor(nome=nome)
    db.session.add(setor)
    db.session.commit()
    return redirect(url_for("main.index"))


@main_bp.route("/setores/<int:setor_id>/inativar", methods=["POST"])
def inativar_setor(setor_id: int):
    setor = db.session.get(Setor, setor_id)
    if setor:
        setor.ativo = False
        db.session.add(setor)
        db.session.commit()
    return redirect(url_for("main.index"))


@main_bp.route("/tipos-peca", methods=["POST"])
def criar_tipo_peca():
    nome = (request.form.get("nome") or "").strip()
    if not nome:
        return redirect(url_for("main.index"))

    existente = (
        TipoPeca.query.filter(func.lower(TipoPeca.nome) == nome.lower()).one_or_none()
    )
    if existente:
        if not existente.ativo:
            existente.ativo = True
            db.session.add(existente)
            db.session.commit()
        return redirect(url_for("main.index"))

    tipo_peca = TipoPeca(nome=nome)
    db.session.add(tipo_peca)
    db.session.commit()
    return redirect(url_for("main.index"))


@main_bp.route("/tipos-peca/<int:tipo_id>/inativar", methods=["POST"])
def inativar_tipo_peca(tipo_id: int):
    tipo_peca = db.session.get(TipoPeca, tipo_id)
    if tipo_peca:
        tipo_peca.ativo = False
        db.session.add(tipo_peca)
        db.session.commit()
    return redirect(url_for("main.index"))


@main_bp.route("/colaboradores", methods=["POST"])
def criar_colaborador():
    nome = (request.form.get("nome") or "").strip()
    if not nome:
        return redirect(url_for("main.index"))

    existente = (
        Colaborador.query.filter(func.lower(Colaborador.nome) == nome.lower()).one_or_none()
    )
    if existente:
        if not existente.ativo:
            existente.ativo = True
            db.session.add(existente)
            db.session.commit()
        return redirect(url_for("main.index"))

    colaborador = Colaborador(nome=nome)
    db.session.add(colaborador)
    db.session.commit()
    return redirect(url_for("main.index"))


@main_bp.route("/colaboradores/<int:colaborador_id>/inativar", methods=["POST"])
def inativar_colaborador(colaborador_id: int):
    colaborador = db.session.get(Colaborador, colaborador_id)
    if colaborador:
        colaborador.ativo = False
        db.session.add(colaborador)
        db.session.commit()
    return redirect(url_for("main.index"))


def seed_tipos_peca():
    """Pré-cadastra os tipos de peças padrão do frigorífico."""
    tipos_padrao = [
        "Moletons",
        "Calças brancas",
        "Calças NR10",
        "Calças térmicas",
        "Camisas NR10",
        "Camisetas com capuz acoplado",
        "Capuz",
        "Capuz térmico",
        "Jaquetas térmicas",
        "Batas manga curta branca",
        "Batas manga longa branca",
        "Batas manga curta azul",
        "Batas manga longa cinza",
        "Calças azuis",
        "Calças cinzas",
    ]

    for tipo_nome in tipos_padrao:
        existente = TipoPeca.query.filter(
            func.lower(TipoPeca.nome) == tipo_nome.lower()
        ).one_or_none()
        if not existente:
            novo_tipo = TipoPeca(nome=tipo_nome, ativo=True)
            db.session.add(novo_tipo)

    db.session.commit()

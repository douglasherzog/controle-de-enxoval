"""Módulo para integração com leitores RFID.

Este módulo fornece endpoints e utilitários para integração
com leitores de RFID, permitindo movimentação automatizada
de peças através de scans.
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from .models import EnxovalItem, Movimentacao, db

rfid_bp = Blueprint("rfid", __name__, url_prefix="/api/rfid")


@rfid_bp.route("/scan", methods=["POST"])
def processar_scan():
    """Processa uma leitura de RFID.

    Espera JSON com:
    - tag_rfid: Código da tag RFID lida
    - status: Novo status da peça (opcional, padrão: 'em_uso')
    - setor: Setor de destino (opcional)
    - colaborador: Colaborador responsável (opcional)
    - observacao: Observação da movimentação (opcional)

    Retorna:
    - sucesso: True/False
    - mensagem: Descrição do resultado
    - item: Dados da peça (se encontrada)
    """
    dados = request.get_json()
    if not dados:
        return jsonify({
            "sucesso": False,
            "mensagem": "Dados JSON não fornecidos"
        }), 400

    tag_rfid = dados.get("tag_rfid", "").strip().upper()
    if not tag_rfid:
        return jsonify({
            "sucesso": False,
            "mensagem": "Tag RFID não fornecida"
        }), 400

    # Buscar peça pelo RFID
    item = EnxovalItem.query.filter(
        func.upper(EnxovalItem.tag_rfid) == tag_rfid,
        EnxovalItem.ativo.is_(True)
    ).first()

    if not item:
        return jsonify({
            "sucesso": False,
            "mensagem": f"Peça com RFID '{tag_rfid}' não encontrada"
        }), 404

    # Atualizar status
    novo_status = dados.get("status", "em_uso").strip().lower()
    setor = dados.get("setor", "").strip() or None
    colaborador = dados.get("colaborador", "").strip() or None
    observacao = dados.get("observacao", "").strip() or f"Scan RFID: {tag_rfid}"

    # Validar status
    status_validos = ["estoque", "entregue", "em_uso", "em_lavagem", "disponivel"]
    if novo_status not in status_validos:
        novo_status = "em_uso"

    # Atualizar peça
    item.status = novo_status
    if setor:
        item.setor = setor
    if colaborador:
        item.colaborador = colaborador

    # Registrar movimentação
    movimentacao = Movimentacao(
        item=item,
        status=novo_status,
        colaborador=colaborador or item.colaborador,
        setor=setor or item.setor,
        observacao=observacao,
    )

    db.session.add(item)
    db.session.add(movimentacao)
    db.session.commit()

    return jsonify({
        "sucesso": True,
        "mensagem": f"Peça {item.codigo} atualizada para '{novo_status}'",
        "item": {
            "id": item.id,
            "codigo": item.codigo,
            "nome": item.nome,
            "tamanho": item.tamanho,
            "status": item.status,
            "setor": item.setor,
            "colaborador": item.colaborador,
            "tag_rfid": item.tag_rfid,
        }
    })


@rfid_bp.route("/buscar/<tag_rfid>")
def buscar_por_rfid(tag_rfid: str):
    """Busca uma peça pelo código RFID.

    Útil para verificar se uma tag está cadastrada
    antes de processar o scan.
    """
    item = EnxovalItem.query.filter(
        func.upper(EnxovalItem.tag_rfid) == tag_rfid.upper(),
        EnxovalItem.ativo.is_(True)
    ).first()

    if not item:
        return jsonify({
            "encontrado": False,
            "mensagem": f"Peça com RFID '{tag_rfid}' não encontrada"
        }), 404

    return jsonify({
        "encontrado": True,
        "item": {
            "id": item.id,
            "codigo": item.codigo,
            "nome": item.nome,
            "tamanho": item.tamanho,
            "status": item.status,
            "setor": item.setor,
            "colaborador": item.colaborador,
            "tag_rfid": item.tag_rfid,
        }
    })


@rfid_bp.route("/tags")
def listar_tags():
    """Lista todas as tags RFID cadastradas.

    Útil para sincronização com leitores externos.
    """
    itens = EnxovalItem.query.filter(
        EnxovalItem.tag_rfid.isnot(None),
        EnxovalItem.ativo.is_(True)
    ).all()

    return jsonify({
        "total": len(itens),
        "tags": [
            {
                "tag_rfid": item.tag_rfid,
                "codigo": item.codigo,
                "nome": item.nome,
                "tamanho": item.tamanho,
                "status": item.status,
            }
            for item in itens
        ]
    })


@rfid_bp.route("/status", methods=["GET"])
def status_rfid():
    """Retorna status da integração RFID.

    Endpoint para verificar se a API está funcionando
    e obter estatísticas de uso.
    """
    total_com_rfid = EnxovalItem.query.filter(
        EnxovalItem.tag_rfid.isnot(None),
        EnxovalItem.ativo.is_(True)
    ).count()

    total_sem_rfid = EnxovalItem.query.filter(
        EnxovalItem.tag_rfid.is_(None),
        EnxovalItem.ativo.is_(True)
    ).count()

    return jsonify({
        "status": "online",
        "estatisticas": {
            "total_com_rfid": total_com_rfid,
            "total_sem_rfid": total_sem_rfid,
            "total_ativos": total_com_rfid + total_sem_rfid,
        }
    })

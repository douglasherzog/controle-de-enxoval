#!/usr/bin/env python3
"""Verificar tipos de peça cadastrados no banco."""

import sys
sys.path.insert(0, '/app')

from app import create_app
from app.models import EnxovalItem, TipoPeca, db
from sqlalchemy import func

app = create_app()

with app.app_context():
    print("=== TIPOS DE PEÇA CADASTRADOS ===\n")
    
    # Todos os tipos cadastrados na tabela TipoPeca
    tipos_cadastrados = TipoPeca.query.order_by(TipoPeca.nome.asc()).all()
    print(f"Tipos na tabela TipoPeca ({len(tipos_cadastrados)}):")
    for t in tipos_cadastrados:
        print(f"  - '{t.nome}' (ativo={t.ativo})")
    
    print("\n=== TIPOS USADOS NOS ITENS ===\n")
    
    # Todos os nomes usados nos itens (com contagem)
    tipos_usados = db.session.query(
        EnxovalItem.nome,
        func.count(EnxovalItem.id)
    ).filter(
        EnxovalItem.ativo.is_(True)
    ).group_by(EnxovalItem.nome).order_by(EnxovalItem.nome.asc()).all()
    
    print(f"Tipos usados nos itens ativos ({len(tipos_usados)}):")
    for nome, count in tipos_usados:
        # Verifica se existe na tabela TipoPeca
        existe = TipoPeca.query.filter_by(nome=nome).first()
        status = "✓" if existe else "✗ (NÃO CADASTRADO)"
        print(f"  - '{nome}': {count} {status}")
    
    # Verificar especificamente os que têm "Bata" no nome
    print("\n=== ITENS COM 'BATA' ===\n")
    batas = db.session.query(
        EnxovalItem.nome,
        func.count(EnxovalItem.id)
    ).filter(
        EnxovalItem.ativo.is_(True),
        EnxovalItem.nome.ilike('%bata%')
    ).group_by(EnxovalItem.nome).all()
    
    for nome, count in batas:
        print(f"  '{nome}': {count}")

    print("\n=== FIM ===")

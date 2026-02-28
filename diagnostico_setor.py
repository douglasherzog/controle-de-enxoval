#!/usr/bin/env python3
"""Script para diagnosticar o problema de contagem por setor."""

import sys
sys.path.insert(0, '/app')

from app import create_app
from app.models import EnxovalItem, db
from sqlalchemy import func

app = create_app()

with app.app_context():
    print("=== DIAGNÓSTICO DE CONTAGEM POR SETOR ===\n")
    
    # Contagem total de ativos
    total_ativos = db.session.query(func.count(EnxovalItem.id)).filter(
        EnxovalItem.ativo.is_(True)
    ).scalar()
    print(f"Total de peças ativas: {total_ativos}")
    
    # Contagem agrupada por setor (raw)
    print("\n--- Contagem por setor (valores brutos) ---")
    raw_counts = db.session.query(
        EnxovalItem.setor, 
        func.count(EnxovalItem.id)
    ).filter(
        EnxovalItem.ativo.is_(True)
    ).group_by(EnxovalItem.setor).all()
    
    for setor, count in raw_counts:
        display = f"'{setor}'" if setor else "NULL"
        print(f"  {display}: {count}")
    
    # Contagem com COALESCE
    print("\n--- Contagem por setor (com COALESCE) ---")
    setor_expr = func.coalesce(func.nullif(EnxovalItem.setor, ""), "Sem setor")
    coalesce_counts = db.session.query(
        setor_expr.label("setor"),
        func.count(EnxovalItem.id)
    ).filter(
        EnxovalItem.ativo.is_(True)
    ).group_by(setor_expr).all()
    
    for setor, count in coalesce_counts:
        print(f"  {setor}: {count}")
    
    # Verificar itens na DESOSSA
    print("\n--- Verificando itens na DESOSSA ---")
    desossa_items = db.session.query(EnxovalItem).filter(
        EnxovalItem.ativo.is_(True),
        EnxovalItem.setor.ilike('desossa')
    ).all()
    
    print(f"Itens encontrados em 'DESOSSA': {len(desossa_items)}")
    for item in desossa_items[:5]:  # Mostra até 5
        print(f"  - ID: {item.id}, Código: {item.codigo}, Setor: '{item.setor}', Ativo: {item.ativo}")
    
    # Verificar a soma das contagens
    print("\n--- Verificação da soma ---")
    soma_coalesce = sum(count for _, count in coalesce_counts)
    print(f"Soma das contagens COALESCE: {soma_coalesce}")
    print(f"Total ativos: {total_ativos}")
    print(f"Diferença: {total_ativos - soma_coalesce}")
    
    print("\n=== FIM DO DIAGNÓSTICO ===")

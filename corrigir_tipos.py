#!/usr/bin/env python3
"""Corrigir nomes de tipos de peça para singular no banco."""

import sys
sys.path.insert(0, '/app')

from app import create_app
from app.models import EnxovalItem, TipoPeca, db
from sqlalchemy import func

app = create_app()

# Mapeamento: plural -> singular
CORRECOES = {
    'Batas manga curta azul': 'Bata manga curta azul',
    'Batas manga curta branca': 'Bata manga curta branca',
    'Batas manga longa branca': 'Bata manga longa branca',
    'Batas manga longa cinza': 'Bata manga longa cinza',
    'Calças azuis': 'Calça azul',
    'Calças brancas': 'Calça branca',
    'Calças cinzas': 'Calça cinza',
    'Calças NR10': 'Calça NR10',
    'Calças térmicas': 'Calça térmica',
    'Camisas NR10': 'Camisa NR10',
    'Camisetas com capuz acoplado': 'Camiseta com capuz',
    'Jaquetas térmicas': 'Jaqueta térmica',
    'Moletons': 'Moletom',
}

with app.app_context():
    print("=== CORREÇÃO DE NOMES DE TIPOS ===\n")
    
    # 1. Atualizar nomes na tabela TipoPeca
    print("1. Atualizando tipos cadastrados...")
    for plural, singular in CORRECOES.items():
        tipo = TipoPeca.query.filter_by(nome=plural).first()
        if tipo:
            tipo.nome = singular
            db.session.add(tipo)
            print(f"   '{plural}' -> '{singular}'")
    
    db.session.commit()
    print("   ✓ Tipos cadastrados atualizados\n")
    
    # 2. Atualizar nomes nos itens do enxoval (os que estão no plural)
    print("2. Atualizando itens do enxoval...")
    
    # Corrigir o item "Batas manga curta azul" -> "Bata manga curta azul"
    itens_batas = EnxovalItem.query.filter_by(nome='Batas manga curta azul').all()
    for item in itens_batas:
        item.nome = 'Bata manga curta azul'
        db.session.add(item)
    print(f"   'Batas manga curta azul' -> 'Bata manga curta azul' ({len(itens_batas)} itens)")
    
    db.session.commit()
    print("   ✓ Itens do enxoval atualizados\n")
    
    # Verificar resultado
    print("=== VERIFICAÇÃO ===\n")
    tipos_final = TipoPeca.query.order_by(TipoPeca.nome.asc()).all()
    print(f"Tipos cadastrados ({len(tipos_final)}):")
    for t in tipos_final:
        print(f"  - '{t.nome}'")
    
    print("\n=== FIM ===")

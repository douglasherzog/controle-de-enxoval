#!/usr/bin/env python3
"""Script para execução automática de smoke tests.

Este script executa todos os smoke tests e gera um relatório.
Pode ser configurado para rodar via cron ou CI/CD.
"""

import subprocess
import sys
from datetime import datetime


def run_smoke_tests():
    """Executa os smoke tests e retorna o resultado."""
    print("🧪 Iniciando Smoke Tests...")
    print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    # Executa os smoke tests
    result = subprocess.run(
        [sys.executable, "-m", "tests.smoke_tests"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    # Imprime saída
    print(result.stdout)
    if result.stderr:
        print("⚠️  STDERR:", result.stderr)

    print("-" * 60)

    if result.returncode == 0:
        print("✅ SMOKE TESTS: SUCESSO")
        return True
    else:
        print("❌ SMOKE TESTS: FALHA")
        return False


def run_unit_tests():
    """Executa os testes unitários padrão."""
    print("\n🧪 Iniciando Testes Unitários...")
    print("-" * 60)

    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    print(result.stdout)
    if result.stderr:
        print("⚠️  STDERR:", result.stderr)

    print("-" * 60)

    if result.returncode == 0:
        print("✅ TESTES UNITÁRIOS: SUCESSO")
        return True
    else:
        print("❌ TESTES UNITÁRIOS: FALHA")
        return False


def check_code_quality():
    """Verifica a qualidade do código com Ruff."""
    print("\n🔍 Verificando qualidade do código...")
    print("-" * 60)

    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "app/", "tests/"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("⚠️  STDERR:", result.stderr)

    print("-" * 60)

    if result.returncode == 0:
        print("✅ QUALIDADE DO CÓDIGO: APROVADA")
        return True
    else:
        print("⚠️  QUALIDADE DO CÓDIGO: PROBLEMAS ENCONTRADOS")
        # Não falha o build por problemas de qualidade, apenas alerta
        return True


def main():
    """Função principal do script de testes."""
    print("=" * 60)
    print("🚀 EXECUÇÃO AUTOMATIZADA DE TESTES")
    print("   Controle de Enxoval")
    print("=" * 60)

    # Executa todos os tipos de testes
    smoke_ok = run_smoke_tests()
    unit_ok = run_unit_tests()
    quality_ok = check_code_quality()

    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    print(f"Smoke Tests:     {'✅ PASSOU' if smoke_ok else '❌ FALHOU'}")
    print(f"Testes Unitários: {'✅ PASSOU' if unit_ok else '❌ FALHOU'}")
    print(f"Qualidade Código: {'✅ APROVADA' if quality_ok else '⚠️  ALERTAS'}")
    print("=" * 60)

    # Retorna código de saída apropriado
    if smoke_ok and unit_ok:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        return 0
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM - VERIFICAR LOGS")
        return 1


if __name__ == "__main__":
    sys.exit(main())

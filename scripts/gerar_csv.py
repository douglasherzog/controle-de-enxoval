import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

ITEMS = [
    ("Moletom", "MO"),
    ("Calça branca", "CB"),
    ("Calça NR10", "CN"),
    ("Calça térmica", "CT"),
    ("Camisa NR10", "CAM"),
    ("Camiseta com capuz", "CC"),
    ("Capuz", "CP"),
    ("Capuz térmico", "CPT"),
    ("Jaqueta térmica", "JT"),
    ("Bata manga curta branca", "BMCB"),
    ("Bata manga longa branca", "BMLB"),
    ("Bata manga curta azul", "BMCA"),
    ("Bata manga longa cinza", "BMLC"),
    ("Calça azul", "CA"),
    ("Calça cinza", "CCZ"),
]

DEFAULT_SIZE_PERCENTAGES = {
    "P": 0.10,
    "M": 0.35,
    "G": 0.40,
    "GG": 0.15,
}


def distribuir(total: int, pesos: dict[str, float]) -> dict[str, int]:
    soma = sum(pesos.values())
    if soma <= 0:
        raise ValueError("Soma de pesos deve ser positiva.")

    base = {chave: int(total * peso / soma) for chave, peso in pesos.items()}
    restante = total - sum(base.values())
    ordenados = sorted(pesos.items(), key=lambda item: item[1], reverse=True)
    indice = 0
    while restante > 0:
        chave = ordenados[indice % len(ordenados)][0]
        base[chave] += 1
        restante -= 1
        indice += 1
    return base


def distribuicao_pratica() -> dict[str, int]:
    pesos = {}
    essenciais = {
        "Calça branca",
        "Calça azul",
        "Calça cinza",
        "Bata manga curta branca",
        "Bata manga longa branca",
        "Bata manga curta azul",
        "Bata manga longa cinza",
        "Camiseta com capuz",
    }
    for nome, _ in ITEMS:
        pesos[nome] = 2 if nome in essenciais else 1
    return pesos


def distribuicao_equilibrada() -> dict[str, int]:
    return {nome: 1 for nome, _ in ITEMS}


def carregar_personalizado(config_path: Path) -> tuple[dict[str, int], dict[str, float], dict[str, str]]:
    dados = json.loads(config_path.read_text(encoding="utf-8"))
    itens = dados.get("itens", [])
    if not itens:
        raise ValueError("Config personalizado precisa de itens.")

    pesos: dict[str, int] = {}
    prefixos: dict[str, str] = {}
    for item in itens:
        nome = item.get("nome")
        prefixo = item.get("prefixo")
        peso = item.get("peso", 1)
        if not nome or not prefixo:
            raise ValueError("Cada item precisa de nome e prefixo.")
        pesos[nome] = peso
        prefixos[nome] = prefixo

    tamanhos = dados.get("tamanhos", DEFAULT_SIZE_PERCENTAGES)
    return pesos, tamanhos, prefixos


def gerar_csv(
    *,
    total: int,
    modo: str,
    saida: Path,
    setor_padrao: str | None,
    config_path: Path | None,
) -> None:
    if modo == "personalizado":
        if not config_path:
            raise ValueError("Modo personalizado requer --config")
        pesos, tamanhos, prefixos_custom = carregar_personalizado(config_path)
        itens = [(nome, prefixos_custom[nome]) for nome in pesos.keys()]
    else:
        tamanhos = DEFAULT_SIZE_PERCENTAGES
        itens = ITEMS
        pesos = distribuicao_pratica() if modo == "pratico" else distribuicao_equilibrada()

    total_por_item = distribuir(total, pesos)
    total_por_tamanho = distribuir(total, tamanhos)

    tamanhos_pool: list[str] = []
    for tamanho, quantidade in total_por_tamanho.items():
        tamanhos_pool.extend([tamanho] * quantidade)

    registros = []
    sequencia_por_prefixo = defaultdict(int)
    tamanho_index = 0
    for nome, prefixo in itens:
        quantidade = total_por_item.get(nome, 0)
        for _ in range(quantidade):
            sequencia_por_prefixo[prefixo] += 1
            codigo = f"{prefixo}-{sequencia_por_prefixo[prefixo]:04d}"
            tamanho = tamanhos_pool[tamanho_index % len(tamanhos_pool)]
            tamanho_index += 1
            registros.append(
                {
                    "nome": nome,
                    "codigo": codigo,
                    "tag_rfid": "",
                    "tamanho": tamanho,
                    "tamanho_customizado": "",
                    "descricao": "",
                    "colaborador": "",
                    "setor": setor_padrao or "",
                    "status": "estoque",
                    "observacao": f"Geracao {modo}",
                }
            )

    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(registros[0].keys()))
        escritor.writeheader()
        escritor.writerows(registros)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gerar CSV de enxoval")
    parser.add_argument("--modo", choices=["pratico", "equilibrado", "personalizado"], required=True)
    parser.add_argument("--total", type=int, default=1400)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--setor", default=None)
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args()

    gerar_csv(
        total=args.total,
        modo=args.modo,
        saida=args.saida,
        setor_padrao=args.setor,
        config_path=args.config,
    )


if __name__ == "__main__":
    main()

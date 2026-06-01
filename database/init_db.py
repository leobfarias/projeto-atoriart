"""Cria (ou recria) o banco SQLite em database/atoriart.sqlite3.

Uso (da raiz do projeto):
    python database/init_db.py                  # banco VAZIO (só a estrutura)
    python database/init_db.py --com-exemplos   # banco + dados de exemplo

ATENÇÃO: roda DROP TABLE antes de criar. Se você já tinha dados, eles
serão apagados. É o esperado nesta fase de desenvolvimento.
"""
import argparse
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DATABASE_DIR = Path(__file__).resolve().parent     # .../database
DB_PATH = DATABASE_DIR / "atoriart.sqlite3"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"


def main(com_exemplos: bool = False):
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print(f"Criando schema em {DB_PATH} ...")
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())

    if com_exemplos:
        print("Inserindo dados de exemplo ...")
        inserir_dados_exemplo(conn)
    else:
        print("Banco vazio — nenhum dado de exemplo inserido.")

    conn.commit()
    conn.close()
    print("Pronto. Banco criado com sucesso.")


def inserir_dados_exemplo(conn):
    # Datas relativas a hoje, pra ficarem sempre dentro dos últimos 30 dias.
    # Definido no topo porque produções, vendas, despesas E compras de
    # material usam essa helper.
    hoje = date.today()

    def dia(dias_atras):
        return (hoje - timedelta(days=dias_atras)).isoformat()

    # --- Materiais ---
    # (nome, unidade, valor_unitario, quantidade_estoque, estoque_minimo, preco_total_lote)
    # Pingente folha e Miçanga olho grego ficam DE PROPÓSITO abaixo do mínimo
    # para exibir o alerta na página de Matéria-prima.
    # preco_total_lote = valor_unitario × quantidade comprada originalmente (antes do consumo)
    materiais = [
        ("Linha encerada verde", "m",  0.40, 50, 20,  40.00),
        ("Argola dourada 10mm",  "un", 0.80, 24, 10,  20.00),
        ("Pingente folha",       "un", 1.50,  6, 10,  15.00),   # alerta
        ("Pedra de quartzo",     "un", 6.00,  8,  5,  60.00),
        ("Cordão de algodão",    "m",  0.30, 30, 15,  15.00),
        ("Fecho de pressão",     "un", 1.20, 12,  8,  18.00),
        ("Argola chaveiro",      "un", 0.70, 28, 10,  22.40),
        ("Miçanga olho grego",   "un", 0.50, 30, 40,  25.00),   # alerta
    ]
    conn.executemany(
        "INSERT INTO material "
        "(nome, unidade, valor_unitario, quantidade_estoque, estoque_minimo) "
        "VALUES (?, ?, ?, ?, ?)",
        [(m[0], m[1], m[2], m[3], m[4]) for m in materiais],
    )

    # Registra a compra inicial de cada material (distribuída nos últimos 30 dias)
    compras_materiais = [
        (i + 1, dia(28 - i * 3), m[3], m[5])
        for i, m in enumerate(materiais)
    ]
    conn.executemany(
        "INSERT INTO compra_material (material_id, data, quantidade, preco_total) "
        "VALUES (?, ?, ?, ?)",
        compras_materiais,
    )

    # --- Peças ---
    # (nome, preco_venda, quantidade_estoque)
    # O custo de produção NÃO é semeado: a view vw_peca_custo calcula
    # a partir dos materiais ligados em peca_material logo abaixo.
    # Os preços de venda ficam acima do custo dos materiais (lucro).
    pecas = [
        ("Brinco Folha em Macramê", 18.00,  8),
        ("Colar Macramê Sol",       32.00,  3),
        ("Pulseira Trançada",       12.00, 15),
        ("Chaveiro Olho Grego",      9.00, 22),
    ]
    conn.executemany(
        "INSERT INTO peca (nome, preco_venda, quantidade_estoque) VALUES (?, ?, ?)",
        pecas,
    )

    # --- Materiais usados em cada peça ---
    # (peca_id, material_id, quantidade)
    peca_materiais = [
        (1, 1, 2.0),   # Brinco Folha: 2 m de linha
        (1, 2, 2),     # Brinco Folha: 2 argolas
        (1, 3, 2),     # Brinco Folha: 2 pingentes
        (2, 1, 8.0),   # Colar Sol: 8 m de linha
        (2, 4, 1),     # Colar Sol: 1 pedra
        (3, 5, 1.5),   # Pulseira: 1,5 m de cordão
        (3, 6, 1),     # Pulseira: 1 fecho
        (4, 7, 1),     # Chaveiro: 1 argola
        (4, 8, 4),     # Chaveiro: 4 miçangas
    ]
    conn.executemany(
        "INSERT INTO peca_material (peca_id, material_id, quantidade) "
        "VALUES (?, ?, ?)",
        peca_materiais,
    )

    # --- Produções ---
    # (peca_id, quantidade, data, observacao)
    producoes = [
        (1,  5, dia(1),  None),
        (3,  3, dia(2),  None),
        (4,  8, dia(4),  "Amostra para feira"),
        (1,  4, dia(6),  None),
        (2,  2, dia(9),  "Cliente Maria"),
        (3,  6, dia(13), None),
        (4, 10, dia(18), "Pedido especial"),
    ]
    conn.executemany(
        "INSERT INTO producao (peca_id, quantidade, data, observacao) "
        "VALUES (?, ?, ?, ?)",
        producoes,
    )

    # --- Vendas ---
    # (peca_id, quantidade, valor_total, data, forma_pagamento)
    vendas = [
        (1, 1,  40.00, dia(1),  "PIX"),
        (4, 2,  36.00, dia(2),  "PIX"),
        (3, 1,  28.00, dia(3),  "Dinheiro"),
        (2, 1,  85.00, dia(4),  "Cartão crédito"),
        (1, 3, 120.00, dia(5),  "PIX"),
        (3, 1,  25.00, dia(7),  "Dinheiro"),
        (1, 1,  35.00, dia(10), "PIX"),
        (4, 2,  36.00, dia(12), "Dinheiro"),
        (4, 4,  72.00, dia(15), "Cartão débito"),
        (2, 1,  90.00, dia(18), "PIX"),
        (3, 2,  56.00, dia(22), "PIX"),
        (1, 1,  38.00, dia(26), "PIX"),
    ]
    conn.executemany(
        "INSERT INTO venda "
        "(peca_id, quantidade, valor_total, data, forma_pagamento) "
        "VALUES (?, ?, ?, ?, ?)",
        vendas,
    )

    # --- Despesas ---
    # (descricao, categoria, valor, data)
    # Só custos operacionais/fixos — fora do escopo de produto. A
    # matéria-prima da produção fica no próprio módulo (/materiais/).
    # Categorias seguem a lista fixa em despesas_service.CATEGORIAS.
    despesas = [
        ("Aluguel do ateliê",              "Aluguel",                    600.00, dia(2)),
        ("Conta de luz",                   "Contas e utilidades",         95.40, dia(5)),
        ("Caixinhas e sacos para entrega", "Embalagem",                   42.50, dia(8)),
        ("Impulsionamento no Instagram",   "Marketing",                   30.00, dia(11)),
        ("Alicate de bico novo",           "Ferramentas e equipamentos",  27.90, dia(16)),
        ("Frete dos Correios do mês",      "Transporte e frete",          54.30, dia(21)),
        ("Taxa da maquininha de cartão",   "Taxas e tarifas",             18.70, dia(27)),
    ]
    conn.executemany(
        "INSERT INTO despesa (descricao, categoria, valor, data) "
        "VALUES (?, ?, ?, ?)",
        despesas,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cria (ou recria) o banco SQLite do AtoriArt."
    )
    parser.add_argument(
        "--com-exemplos",
        action="store_true",
        help="Popula o banco com dados de exemplo (materiais, peças, "
             "produções e vendas fictícias). Sem esta flag, o banco fica vazio.",
    )
    args = parser.parse_args()
    main(com_exemplos=args.com_exemplos)

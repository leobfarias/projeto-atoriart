"""Cria (ou recria) o banco SQLite em database/atoriart.sqlite3.

Uso (da raiz do projeto):
    python database/init_db.py

ATENÇÃO: roda DROP TABLE antes de criar. Se você já tinha dados, eles
serão apagados. É o esperado nesta fase de desenvolvimento.
"""
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DATABASE_DIR = Path(__file__).resolve().parent     # .../database
DB_PATH = DATABASE_DIR / "atoriart.sqlite3"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"


def main():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print(f"Criando schema em {DB_PATH} ...")
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())

    print("Inserindo dados de exemplo ...")
    inserir_dados_exemplo(conn)

    conn.commit()
    conn.close()
    print("Pronto. Banco criado com sucesso.")


def inserir_dados_exemplo(conn):
    # --- Materiais ---
    # (nome, unidade, valor_unitario, quantidade_estoque, estoque_minimo)
    # Pingente folha e Miçanga olho grego ficam DE PROPÓSITO abaixo do mínimo
    # para exibir o alerta na página de Matéria-prima.
    materiais = [
        ("Linha encerada verde", "m",  0.40, 50, 20),
        ("Argola dourada 10mm",  "un", 0.80, 24, 10),
        ("Pingente folha",       "un", 1.50,  6, 10),   # alerta
        ("Pedra de quartzo",     "un", 6.00,  8,  5),
        ("Cordão de algodão",    "m",  0.30, 30, 15),
        ("Fecho de pressão",     "un", 1.20, 12,  8),
        ("Argola chaveiro",      "un", 0.70, 28, 10),
        ("Miçanga olho grego",   "un", 0.50, 30, 40),   # alerta
    ]
    conn.executemany(
        "INSERT INTO material "
        "(nome, unidade, valor_unitario, quantidade_estoque, estoque_minimo) "
        "VALUES (?, ?, ?, ?, ?)",
        materiais,
    )

    # --- Peças ---
    pecas = [
        # (nome, custo_producao, quantidade_estoque)
        ("Brinco Folha em Macramê", 12.50,  8),
        ("Colar Macramê Sol",       28.00,  3),
        ("Pulseira Trançada",        9.80, 15),
        ("Chaveiro Olho Grego",      6.40, 22),
    ]
    conn.executemany(
        "INSERT INTO peca (nome, custo_producao, quantidade_estoque) VALUES (?, ?, ?)",
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
    # Datas relativas a hoje, pra ficarem sempre dentro dos últimos 30 dias.
    hoje = date.today()

    def dia(dias_atras):
        return (hoje - timedelta(days=dias_atras)).isoformat()

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


if __name__ == "__main__":
    main()

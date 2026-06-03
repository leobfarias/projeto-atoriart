"""Gera o banco de dados fictício para teste de backup/restauração.

Cria: database/banco_exemplo_teste.sqlite3

Os dados são completamente diferentes do banco principal (atoriart.sqlite3)
para que a alternância entre os dois seja visualmente óbvia na interface.

Uso (da raiz do projeto):
    python database/gerar_banco_teste.py

A senha do admin neste banco é a mesma do seu .env (lida na hora da geração).
"""
import os
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_DIR = Path(__file__).resolve().parent
DB_PATH      = DATABASE_DIR / "banco_exemplo_teste.sqlite3"
SCHEMA_PATH  = DATABASE_DIR / "schema.sql"


def main():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print(f"Aplicando schema em {DB_PATH} ...")
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())

    print("Inserindo dados de teste ...")
    _seed(conn)

    conn.commit()
    conn.close()
    print("Pronto! Banco de teste criado com sucesso.")
    print(f"  → {DB_PATH}")
    print("  → Para testar: acesse /configuracoes/ e use 'Restaurar banco'")
    print("     selecionando este arquivo. Depois restaure o banco original")
    print("     fazendo o mesmo com o backup baixado antes.")


def _seed(conn):
    hoje = date.today()

    def dia(n):
        return (hoje - timedelta(days=n)).isoformat()

    # ------------------------------------------------------------------ #
    # Credencial — mesma senha do .env para não precisar trocar ao testar #
    # ------------------------------------------------------------------ #
    password_hash = os.environ.get("ADMIN_PASSWORD_HASH", "")
    username      = os.environ.get("ADMIN_USERNAME", "admin")
    if not password_hash:
        # Fallback: gera hash de "teste12345" se não houver .env disponível.
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash("teste12345")
        print("  AVISO: ADMIN_PASSWORD_HASH não encontrado no .env.")
        print("         Senha deste banco de teste: teste12345")

    conn.execute(
        "INSERT INTO admin_credencial (username, password_hash, atualizado_em) "
        "VALUES (?, ?, datetime('now'))",
        (username, password_hash),
    )

    # ------------------------------------------------------------------ #
    # Materiais (completamente diferentes do banco principal)              #
    # ------------------------------------------------------------------ #
    # (nome, unidade, valor_unitario, quantidade_estoque, estoque_minimo)
    materiais = [
        ("Fio de náilon 0.5mm",    "m",  0.25, 100, 30),
        ("Cristal swarovski 6mm",  "un", 2.50,  40, 15),
        ("Couro natural marrom",   "cm", 0.60,  80, 20),
        ("Entremeio prata 925",    "un", 3.20,  25, 10),
        ("Resina epóxi bicompon.", "ml", 0.18, 200, 50),
        ("Corante em pó dourado",  "g",  0.90,  15,  8),
        ("Fecho de gancho prata",  "un", 1.10,  35, 12),
        ("Anel de solda 8mm",      "un", 0.35,  60, 20),
    ]
    conn.executemany(
        "INSERT INTO material "
        "(nome, unidade, valor_unitario, quantidade_estoque, estoque_minimo) "
        "VALUES (?, ?, ?, ?, ?)",
        [(m[0], m[1], m[2], m[3], m[4]) for m in materiais],
    )

    # Compras de cada material (histórico)
    compras = [
        (1, dia(25), 150, 37.50),
        (2, dia(22),  60, 150.00),
        (3, dia(20), 120,  72.00),
        (4, dia(18),  40, 128.00),
        (5, dia(15), 300,  54.00),
        (6, dia(12),  20,  18.00),
        (7, dia(10),  50,  55.00),
        (8, dia(7),  100,  35.00),
    ]
    conn.executemany(
        "INSERT INTO compra_material (material_id, data, quantidade, preco_total) "
        "VALUES (?, ?, ?, ?)",
        compras,
    )

    # ------------------------------------------------------------------ #
    # Peças                                                                #
    # ------------------------------------------------------------------ #
    # (nome, preco_venda, quantidade_estoque)
    pecas = [
        ("Colar de Cristal Elegance",  65.00, 10),
        ("Brinco Resina Dourada",      38.00, 18),
        ("Pulseira Couro e Prata",     55.00,  7),
        ("Anel Ajustável Fio Náilon",  22.00, 25),
    ]
    conn.executemany(
        "INSERT INTO peca (nome, preco_venda, quantidade_estoque) VALUES (?, ?, ?)",
        pecas,
    )

    # Materiais de cada peça
    # (peca_id, material_id, quantidade)
    peca_materiais = [
        (1, 1, 30.0),  # Colar Cristal: 30 cm de fio
        (1, 2,  8),    # Colar Cristal: 8 cristais
        (1, 7,  2),    # Colar Cristal: 2 fechos
        (2, 5, 15.0),  # Brinco Resina: 15 ml de resina
        (2, 6,  2.0),  # Brinco Resina: 2 g de corante
        (2, 8,  4),    # Brinco Resina: 4 anéis de solda
        (3, 3, 20.0),  # Pulseira Couro: 20 cm de couro
        (3, 4,  3),    # Pulseira Couro: 3 entremeios
        (3, 8,  6),    # Pulseira Couro: 6 anéis de solda
        (4, 1, 50.0),  # Anel Fio: 50 cm de náilon
        (4, 8,  2),    # Anel Fio: 2 anéis de solda
    ]
    conn.executemany(
        "INSERT INTO peca_material (peca_id, material_id, quantidade) "
        "VALUES (?, ?, ?)",
        peca_materiais,
    )

    # ------------------------------------------------------------------ #
    # Produções (custo_unitario = 0; view vw_peca_custo calcula o real)   #
    # ------------------------------------------------------------------ #
    # (peca_id, quantidade, custo_unitario, data, observacao)
    producoes = [
        (1,  6, 0, dia(2),  "Coleção verão"),
        (2, 10, 0, dia(3),  None),
        (3,  4, 0, dia(5),  "Encomenda especial"),
        (4, 15, 0, dia(8),  None),
        (1,  5, 0, dia(12), None),
        (2,  8, 0, dia(16), "Feira de artesanato"),
        (3,  4, 0, dia(20), None),
        (4, 10, 0, dia(24), None),
    ]
    conn.executemany(
        "INSERT INTO producao (peca_id, quantidade, custo_unitario, data, observacao) "
        "VALUES (?, ?, ?, ?, ?)",
        producoes,
    )

    # ------------------------------------------------------------------ #
    # Vendas                                                               #
    # ------------------------------------------------------------------ #
    # (peca_id, quantidade, valor_total, data, forma_pagamento)
    vendas = [
        (2,  2,  76.00, dia(1),  "PIX"),
        (4,  3,  66.00, dia(2),  "Dinheiro"),
        (1,  1,  65.00, dia(3),  "Cartão crédito"),
        (3,  2, 110.00, dia(4),  "PIX"),
        (2,  4, 152.00, dia(6),  "PIX"),
        (4,  5, 110.00, dia(8),  "Cartão débito"),
        (1,  2, 130.00, dia(10), "PIX"),
        (3,  1,  55.00, dia(13), "Dinheiro"),
        (2,  3, 114.00, dia(17), "PIX"),
        (4,  4,  88.00, dia(20), "Dinheiro"),
        (1,  3, 195.00, dia(23), "Cartão crédito"),
        (3,  2, 110.00, dia(27), "PIX"),
    ]
    conn.executemany(
        "INSERT INTO venda "
        "(peca_id, quantidade, valor_total, data, forma_pagamento) "
        "VALUES (?, ?, ?, ?, ?)",
        vendas,
    )

    # ------------------------------------------------------------------ #
    # Despesas                                                             #
    # ------------------------------------------------------------------ #
    # (descricao, categoria, valor, data)
    despesas = [
        ("Aluguel do espaço compartilhado", "Aluguel",                    450.00, dia(1)),
        ("Internet e telefone",             "Contas e utilidades",          89.90, dia(4)),
        ("Caixas rígidas para joias",       "Embalagem",                    63.00, dia(7)),
        ("Anúncio patrocinado no Facebook", "Marketing",                    50.00, dia(10)),
        ("Kit de ferramentas de joalheria", "Ferramentas e equipamentos",  138.00, dia(14)),
        ("Correio — remessas do mês",       "Transporte e frete",           47.60, dia(18)),
        ("Anuidade marketplace artesanato", "Taxas e tarifas",              29.90, dia(24)),
    ]
    conn.executemany(
        "INSERT INTO despesa (descricao, categoria, valor, data) "
        "VALUES (?, ?, ?, ?)",
        despesas,
    )


if __name__ == "__main__":
    main()

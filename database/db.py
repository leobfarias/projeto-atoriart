"""Conexão com o SQLite.

Usa o objeto `g` do Flask para guardar a conexão durante o request atual.
Ao fim do request, a conexão é fechada automaticamente.

Para criar (ou recriar) o arquivo do banco, rode na raiz do projeto:
    python database/init_db.py
"""
import sqlite3

from flask import current_app, g


def get_db():
    """Retorna a conexão SQLite do request atual (abre se ainda não existe)."""
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE_PATH"])
        # Permite acessar colunas por nome: row["nome"]
        conn.row_factory = sqlite3.Row
        # Liga checagem de chaves estrangeiras (SQLite vem desligado por padrão)
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(error=None):
    """Fecha a conexão ao final do request."""
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_app(app):
    """Registra o fechamento automático da conexão na app Flask."""
    app.teardown_appcontext(close_db)
    _apply_migrations(app)


def _apply_migrations(app):
    """Aplica migrações incrementais sem recriar o banco (preserva dados)."""
    conn = sqlite3.connect(app.config["DATABASE_PATH"])

    # Etapa 11.2 — coluna foto na tabela peca
    colunas_peca = [row[1] for row in conn.execute("PRAGMA table_info(peca)").fetchall()]
    if "foto" not in colunas_peca:
        conn.execute("ALTER TABLE peca ADD COLUMN foto TEXT")
        conn.commit()

    # ADR-013 — snapshot de custo na tabela producao
    # Registros existentes recebem o custo atual da view como aproximação.
    colunas_prod = [row[1] for row in conn.execute("PRAGMA table_info(producao)").fetchall()]
    if "custo_unitario" not in colunas_prod:
        conn.execute("ALTER TABLE producao ADD COLUMN custo_unitario REAL NOT NULL DEFAULT 0")
        conn.execute("""
            UPDATE producao
            SET custo_unitario = (
                SELECT COALESCE(vpc.custo_producao, 0)
                FROM vw_peca_custo vpc
                WHERE vpc.peca_id = producao.peca_id
            )
            WHERE custo_unitario = 0
        """)
        conn.commit()

    conn.close()

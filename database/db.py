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

"""Repositório de despesas.

Contrato público:
    list_despesas(desde=None)      -> list[Despesa]
        `desde` filtra por data ('YYYY-MM-DD'); None traz todas.
    get_despesa(despesa_id)        -> Despesa | None
    criar(descricao, valor, data,
          categoria)               -> int (novo id)
    apagar(despesa_id)             -> None

A despesa é um registro puro: nenhuma escrita aqui tem efeito colateral
em estoque ou em outra tabela (não há FK).
"""
from database.db import get_db
from backend.models.despesa import Despesa


# ---------- Leitura ----------

def list_despesas(desde=None):
    db = get_db()
    sql = "SELECT id, descricao, categoria, valor, data FROM despesa"
    params = ()
    if desde:
        sql += " WHERE data >= ?"
        params = (desde,)
    sql += " ORDER BY data DESC, id DESC"

    rows = db.execute(sql, params).fetchall()
    return [_row_to_despesa(r) for r in rows]


def get_despesa(despesa_id):
    db = get_db()
    r = db.execute(
        "SELECT id, descricao, categoria, valor, data "
        "FROM despesa WHERE id = ?",
        (despesa_id,),
    ).fetchone()
    return _row_to_despesa(r) if r is not None else None


# ---------- Escrita ----------

def criar(descricao, valor, data, categoria):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO despesa (descricao, categoria, valor, data) "
        "VALUES (?, ?, ?, ?)",
        (descricao, categoria, valor, data),
    )
    db.commit()
    return cursor.lastrowid


def apagar(despesa_id):
    db = get_db()
    db.execute("DELETE FROM despesa WHERE id = ?", (despesa_id,))
    db.commit()


# ---------- Helper ----------

def _row_to_despesa(r):
    return Despesa(
        id=r["id"],
        descricao=r["descricao"],
        categoria=r["categoria"],
        valor=r["valor"],
        data=r["data"],
    )

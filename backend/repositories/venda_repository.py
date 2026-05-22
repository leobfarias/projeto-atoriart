"""Repositório de vendas.

Contrato público:
    list_vendas(desde=None)        -> list[Venda]
    get_venda(venda_id)            -> Venda | None
    criar(peca_id, quantidade,
          valor_total, data,
          forma_pagamento)         -> int
        Insere a venda E subtrai a quantidade do estoque da peça,
        tudo numa transação.
    apagar(venda_id, peca_id,
           quantidade)              -> None
        Apaga a venda E devolve a quantidade ao estoque da peça.
"""
from database.db import get_db
from backend.models.venda import Venda


# ---------- Leitura ----------

def list_vendas(desde=None):
    db = get_db()
    sql = (
        "SELECT v.id, v.peca_id, v.quantidade, v.valor_total, "
        "       v.data, v.forma_pagamento, "
        "       pe.nome AS peca_nome, "
        "       COALESCE(vpc.custo_producao, 0) AS peca_custo "
        "FROM venda v "
        "JOIN peca pe ON pe.id = v.peca_id "
        "LEFT JOIN vw_peca_custo vpc ON vpc.peca_id = pe.id"
    )
    params = ()
    if desde:
        sql += " WHERE v.data >= ?"
        params = (desde,)
    sql += " ORDER BY v.data DESC, v.id DESC"

    rows = db.execute(sql, params).fetchall()
    return [_row_to_venda(r) for r in rows]


def get_venda(venda_id):
    db = get_db()
    r = db.execute(
        "SELECT v.id, v.peca_id, v.quantidade, v.valor_total, "
        "       v.data, v.forma_pagamento, "
        "       pe.nome AS peca_nome, "
        "       COALESCE(vpc.custo_producao, 0) AS peca_custo "
        "FROM venda v "
        "JOIN peca pe ON pe.id = v.peca_id "
        "LEFT JOIN vw_peca_custo vpc ON vpc.peca_id = pe.id "
        "WHERE v.id = ?",
        (venda_id,),
    ).fetchone()
    return _row_to_venda(r) if r is not None else None


# ---------- Escrita (com efeito no estoque) ----------

def criar(peca_id, quantidade, valor_total, data, forma_pagamento):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO venda "
        "(peca_id, quantidade, valor_total, data, forma_pagamento) "
        "VALUES (?, ?, ?, ?, ?)",
        (peca_id, quantidade, valor_total, data, forma_pagamento),
    )
    db.execute(
        "UPDATE peca SET quantidade_estoque = quantidade_estoque - ? "
        "WHERE id = ?",
        (quantidade, peca_id),
    )
    db.commit()
    return cursor.lastrowid


def apagar(venda_id, peca_id, quantidade):
    db = get_db()
    db.execute("DELETE FROM venda WHERE id = ?", (venda_id,))
    db.execute(
        "UPDATE peca SET quantidade_estoque = quantidade_estoque + ? "
        "WHERE id = ?",
        (quantidade, peca_id),
    )
    db.commit()


# ---------- Helper ----------

def _row_to_venda(r):
    return Venda(
        id=r["id"],
        peca_id=r["peca_id"],
        peca_nome=r["peca_nome"],
        peca_custo=r["peca_custo"],
        quantidade=r["quantidade"],
        valor_total=r["valor_total"],
        data=r["data"],
        forma_pagamento=r["forma_pagamento"],
    )

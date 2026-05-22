"""Repositório de produções.

Contrato público:
    list_producoes(desde=None)        -> list[Producao]
    get_producao(producao_id)         -> Producao | None
    criar(peca_id, quantidade,
          data, observacao)           -> int
        Insere a produção E soma a quantidade no estoque da peça,
        tudo numa transação.
    apagar(producao_id)               -> None
        Apaga a produção E subtrai a quantidade do estoque da peça.
        Quem garante que não vai dar negativo é o service.
"""
from database.db import get_db
from backend.models.producao import Producao


# ---------- Leitura ----------

def list_producoes(desde=None):
    db = get_db()
    sql = (
        "SELECT p.id, p.peca_id, p.quantidade, p.data, p.observacao, "
        "       pe.nome AS peca_nome, "
        "       COALESCE(vpc.custo_producao, 0) AS peca_custo "
        "FROM producao p "
        "JOIN peca pe ON pe.id = p.peca_id "
        "LEFT JOIN vw_peca_custo vpc ON vpc.peca_id = pe.id"
    )
    params = ()
    if desde:
        sql += " WHERE p.data >= ?"
        params = (desde,)
    sql += " ORDER BY p.data DESC, p.id DESC"

    rows = db.execute(sql, params).fetchall()
    return [_row_to_producao(r) for r in rows]


def get_producao(producao_id):
    db = get_db()
    r = db.execute(
        "SELECT p.id, p.peca_id, p.quantidade, p.data, p.observacao, "
        "       pe.nome AS peca_nome, "
        "       COALESCE(vpc.custo_producao, 0) AS peca_custo "
        "FROM producao p "
        "JOIN peca pe ON pe.id = p.peca_id "
        "LEFT JOIN vw_peca_custo vpc ON vpc.peca_id = pe.id "
        "WHERE p.id = ?",
        (producao_id,),
    ).fetchone()
    return _row_to_producao(r) if r is not None else None


# ---------- Escrita (com efeito no estoque) ----------

def criar(peca_id, quantidade, data, observacao):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO producao (peca_id, quantidade, data, observacao) "
        "VALUES (?, ?, ?, ?)",
        (peca_id, quantidade, data, observacao),
    )
    db.execute(
        "UPDATE peca SET quantidade_estoque = quantidade_estoque + ? "
        "WHERE id = ?",
        (quantidade, peca_id),
    )
    db.commit()
    return cursor.lastrowid


def apagar(producao_id, peca_id, quantidade):
    db = get_db()
    db.execute("DELETE FROM producao WHERE id = ?", (producao_id,))
    db.execute(
        "UPDATE peca SET quantidade_estoque = quantidade_estoque - ? "
        "WHERE id = ?",
        (quantidade, peca_id),
    )
    db.commit()


# ---------- Helper ----------

def _row_to_producao(r):
    return Producao(
        id=r["id"],
        peca_id=r["peca_id"],
        peca_nome=r["peca_nome"],
        peca_custo=r["peca_custo"],
        quantidade=r["quantidade"],
        data=r["data"],
        observacao=r["observacao"],
    )

"""Repositório de produções.

Contrato público:
    list_producoes(desde=None)        -> list[Producao]
    get_producao(producao_id)         -> Producao | None
    criar(peca_id, quantidade,
          data, observacao)           -> int
        Insere a produção, SOMA a quantidade no estoque da peça E
        DEBITA os materiais consumidos (qty × material_qty), tudo
        numa única transação SQLite.
    apagar(producao_id, peca_id,
           quantidade)                -> None
        Apaga a produção e SUBTRAI a quantidade do estoque da peça.
        A matéria-prima NÃO volta: já foi consumida fisicamente.
        Quem garante que o estoque da peça não vai ficar negativo é
        o service.
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
    _debitar_materiais(db, peca_id, quantidade)
    db.commit()
    return cursor.lastrowid


def apagar(producao_id, peca_id, quantidade):
    """Apaga a produção e retira as peças do estoque.

    A matéria-prima consumida **não retorna** ao estoque: como o material
    já foi fisicamente usado, apagar o registro não restaura o insumo.
    O efeito é assimétrico em relação a `criar`, de propósito.
    """
    db = get_db()
    db.execute("DELETE FROM producao WHERE id = ?", (producao_id,))
    db.execute(
        "UPDATE peca SET quantidade_estoque = quantidade_estoque - ? "
        "WHERE id = ?",
        (quantidade, peca_id),
    )
    db.commit()


def _debitar_materiais(db, peca_id, quantidade_producao):
    """Subtrai (quantidade_producao × qtd_material) do estoque de cada
    material da receita ATUAL da peça. Chamado apenas em `criar`.

    Não há contrapartida ao apagar: matéria-prima consumida é fisicamente
    perdida — não dá pra "des-produzir" e recuperar insumo.
    """
    rows = db.execute(
        "SELECT material_id, quantidade FROM peca_material WHERE peca_id = ?",
        (peca_id,),
    ).fetchall()
    if not rows:
        return
    updates = [
        (quantidade_producao * r["quantidade"], r["material_id"])
        for r in rows
    ]
    db.executemany(
        "UPDATE material SET quantidade_estoque = quantidade_estoque - ? "
        "WHERE id = ?",
        updates,
    )


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

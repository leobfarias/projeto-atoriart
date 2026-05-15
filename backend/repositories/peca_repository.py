"""Repositório de peças.

Contrato público:
    list_pecas()                        -> list[Peca]
    get_peca(peca_id)                   -> Peca | None
    criar(nome, custo, estoque,
          materiais: dict[int, float])  -> int (novo id)
        `materiais` é {material_id: quantidade}.
    atualizar(peca_id, nome, custo,
              estoque, materiais)       -> None
    apagar(peca_id)                     -> None
        ON DELETE CASCADE cuida das linhas em peca_material.
        ON DELETE RESTRICT em venda → pode falhar com IntegrityError.
    tem_vendas(peca_id)                 -> bool
"""
from database.db import get_db
from backend.models.peca import ItemMaterial, Material, Peca


# ---------- Leitura ----------

def list_pecas(apenas_em_estoque=False):
    db = get_db()
    sql = (
        "SELECT id, nome, custo_producao, quantidade_estoque "
        "FROM peca "
    )
    if apenas_em_estoque:
        sql += "WHERE quantidade_estoque > 0 "
    sql += "ORDER BY nome COLLATE NOCASE"
    rows = db.execute(sql).fetchall()
    pecas = []
    for r in rows:
        pecas.append(Peca(
            id=r["id"],
            nome=r["nome"],
            custo_producao=r["custo_producao"],
            quantidade_estoque=r["quantidade_estoque"],
            materiais=_materiais_da_peca(db, r["id"]),
        ))
    return pecas


def get_peca(peca_id):
    db = get_db()
    r = db.execute(
        "SELECT id, nome, custo_producao, quantidade_estoque "
        "FROM peca WHERE id = ?",
        (peca_id,),
    ).fetchone()
    if r is None:
        return None
    return Peca(
        id=r["id"], nome=r["nome"],
        custo_producao=r["custo_producao"],
        quantidade_estoque=r["quantidade_estoque"],
        materiais=_materiais_da_peca(db, r["id"]),
    )


# ---------- Escrita ----------

def criar(nome, custo_producao, quantidade_estoque, materiais):
    """Cria peça e os vínculos em peca_material numa só transação."""
    db = get_db()
    cursor = db.execute(
        "INSERT INTO peca (nome, custo_producao, quantidade_estoque) "
        "VALUES (?, ?, ?)",
        (nome, custo_producao, quantidade_estoque),
    )
    peca_id = cursor.lastrowid
    _gravar_materiais(db, peca_id, materiais)
    db.commit()
    return peca_id


def atualizar(peca_id, nome, custo_producao, quantidade_estoque, materiais):
    """Atualiza peça e refaz a lista de materiais (apaga + reinsere)."""
    db = get_db()
    db.execute(
        "UPDATE peca SET nome = ?, custo_producao = ?, quantidade_estoque = ? "
        "WHERE id = ?",
        (nome, custo_producao, quantidade_estoque, peca_id),
    )
    db.execute("DELETE FROM peca_material WHERE peca_id = ?", (peca_id,))
    _gravar_materiais(db, peca_id, materiais)
    db.commit()


def apagar(peca_id):
    db = get_db()
    db.execute("DELETE FROM peca WHERE id = ?", (peca_id,))
    db.commit()


def tem_vendas(peca_id):
    db = get_db()
    r = db.execute(
        "SELECT 1 FROM venda WHERE peca_id = ? LIMIT 1",
        (peca_id,),
    ).fetchone()
    return r is not None


# ---------- Helpers privados ----------

def _materiais_da_peca(db, peca_id):
    rows = db.execute(
        "SELECT m.id, m.nome, m.unidade, m.valor_unitario, "
        "       m.quantidade_estoque, m.estoque_minimo, pm.quantidade "
        "FROM peca_material pm "
        "JOIN material m ON m.id = pm.material_id "
        "WHERE pm.peca_id = ? "
        "ORDER BY m.nome COLLATE NOCASE",
        (peca_id,),
    ).fetchall()
    return [
        ItemMaterial(
            material=Material(
                id=r["id"], nome=r["nome"], unidade=r["unidade"],
                valor_unitario=r["valor_unitario"],
                quantidade_estoque=r["quantidade_estoque"],
                estoque_minimo=r["estoque_minimo"],
            ),
            quantidade=r["quantidade"],
        )
        for r in rows
    ]


def _gravar_materiais(db, peca_id, materiais):
    """Insere as linhas em peca_material. `materiais` = {id: quantidade}."""
    if not materiais:
        return
    db.executemany(
        "INSERT INTO peca_material (peca_id, material_id, quantidade) "
        "VALUES (?, ?, ?)",
        [(peca_id, mid, qtd) for mid, qtd in materiais.items()],
    )

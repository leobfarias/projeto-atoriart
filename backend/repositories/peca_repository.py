"""Repositório de peças.

Contrato público:
    list_pecas(apenas_em_estoque=False) -> list[Peca]
    get_peca(peca_id)                   -> Peca | None
    criar(nome, preco_venda, estoque,
          materiais: dict[int, float])  -> int (novo id)
        `materiais` é {material_id: quantidade}.
    atualizar(peca_id, nome, preco_venda,
              estoque, materiais)       -> None
    apagar(peca_id)                     -> None
        ON DELETE CASCADE cuida das linhas em peca_material.
        ON DELETE RESTRICT em venda → pode falhar com IntegrityError.
    tem_vendas(peca_id)                 -> bool

O `custo_producao` da peça NÃO é coluna: vem da view `vw_peca_custo`
(soma dos materiais). As leituras fazem LEFT JOIN com ela; peças sem
material nenhum caem no COALESCE(..., 0).
"""
from database.db import get_db
from backend.models.peca import ItemMaterial, Material, Peca


# ---------- Leitura ----------

# SELECT reaproveitado por list_pecas e get_peca: traz, junto da peça,
# o custo de produção calculado pela view vw_peca_custo.
_SELECT_PECA = (
    "SELECT pe.id, pe.nome, pe.preco_venda, pe.quantidade_estoque, "
    "       COALESCE(vpc.custo_producao, 0) AS custo_producao "
    "FROM peca pe "
    "LEFT JOIN vw_peca_custo vpc ON vpc.peca_id = pe.id "
)


def list_pecas(apenas_em_estoque=False):
    db = get_db()
    sql = _SELECT_PECA
    if apenas_em_estoque:
        sql += "WHERE pe.quantidade_estoque > 0 "
    sql += "ORDER BY pe.nome COLLATE NOCASE"
    rows = db.execute(sql).fetchall()
    return [_row_to_peca(db, r) for r in rows]


def get_peca(peca_id):
    db = get_db()
    r = db.execute(
        _SELECT_PECA + "WHERE pe.id = ?",
        (peca_id,),
    ).fetchone()
    return _row_to_peca(db, r) if r is not None else None


# ---------- Escrita ----------

def criar(nome, preco_venda, quantidade_estoque, materiais):
    """Cria peça e os vínculos em peca_material numa só transação."""
    db = get_db()
    cursor = db.execute(
        "INSERT INTO peca (nome, preco_venda, quantidade_estoque) "
        "VALUES (?, ?, ?)",
        (nome, preco_venda, quantidade_estoque),
    )
    peca_id = cursor.lastrowid
    _gravar_materiais(db, peca_id, materiais)
    db.commit()
    return peca_id


def atualizar(peca_id, nome, preco_venda, quantidade_estoque, materiais):
    """Atualiza peça e refaz a lista de materiais (apaga + reinsere)."""
    db = get_db()
    db.execute(
        "UPDATE peca SET nome = ?, preco_venda = ?, quantidade_estoque = ? "
        "WHERE id = ?",
        (nome, preco_venda, quantidade_estoque, peca_id),
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

def _row_to_peca(db, r):
    return Peca(
        id=r["id"],
        nome=r["nome"],
        preco_venda=r["preco_venda"],
        quantidade_estoque=r["quantidade_estoque"],
        custo_producao=r["custo_producao"],
        materiais=_materiais_da_peca(db, r["id"]),
    )


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

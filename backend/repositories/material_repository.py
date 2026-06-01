"""Repositório de materiais (matéria-prima).

Funções públicas:
    list_materiais()                       -> list[Material]
    get_material(material_id)              -> Material | None
    criar(nome, unidade, valor_unitario,
          quantidade_estoque, estoque_minimo) -> int (novo id)
    atualizar(material_id, **campos)       -> None
    apagar(material_id)                    -> None
        Lança sqlite3.IntegrityError se o material está em uso
        em alguma peça (FK com ON DELETE RESTRICT).

    em_uso(material_id)                    -> bool
        True se este material está em pelo menos uma peça.
"""
import sqlite3

from database.db import get_db
from backend.models.material import Material


def list_materiais():
    db = get_db()
    rows = db.execute(
        "SELECT id, nome, unidade, valor_unitario, "
        "       quantidade_estoque, estoque_minimo "
        "FROM material "
        "ORDER BY nome COLLATE NOCASE"
    ).fetchall()
    return [_row_to_material(r) for r in rows]


def get_material(material_id):
    db = get_db()
    r = db.execute(
        "SELECT id, nome, unidade, valor_unitario, "
        "       quantidade_estoque, estoque_minimo "
        "FROM material WHERE id = ?",
        (material_id,),
    ).fetchone()
    return _row_to_material(r) if r is not None else None


def criar(nome, unidade, valor_unitario, quantidade_estoque, estoque_minimo,
          preco_total):
    from datetime import date
    db = get_db()
    cursor = db.execute(
        "INSERT INTO material "
        "(nome, unidade, valor_unitario, quantidade_estoque, estoque_minimo) "
        "VALUES (?, ?, ?, ?, ?)",
        (nome, unidade, valor_unitario, quantidade_estoque, estoque_minimo),
    )
    db.execute(
        "INSERT INTO compra_material (material_id, data, quantidade, preco_total) "
        "VALUES (?, ?, ?, ?)",
        (cursor.lastrowid, date.today().isoformat(), quantidade_estoque, preco_total),
    )
    db.commit()
    return cursor.lastrowid


def gasto_periodo(desde, ate=None):
    """Soma dos preços pagos em compras de matéria-prima a partir de `desde` (inclusive)."""
    db = get_db()
    sql = "SELECT COALESCE(SUM(preco_total), 0) FROM compra_material WHERE data >= ?"
    params = [desde]
    if ate:
        sql += " AND data <= ?"
        params.append(ate)
    r = db.execute(sql, params).fetchone()
    return r[0]


def atualizar(material_id, nome, unidade, valor_unitario,
              quantidade_estoque, estoque_minimo):
    db = get_db()
    db.execute(
        "UPDATE material SET nome = ?, unidade = ?, valor_unitario = ?, "
        "    quantidade_estoque = ?, estoque_minimo = ? "
        "WHERE id = ?",
        (nome, unidade, valor_unitario, quantidade_estoque,
         estoque_minimo, material_id),
    )
    db.commit()


def apagar(material_id):
    """Apaga o material. Pode lançar IntegrityError se está em uso."""
    db = get_db()
    db.execute("DELETE FROM material WHERE id = ?", (material_id,))
    db.commit()


def em_uso(material_id):
    """True se o material está em peca_material de alguma peça."""
    db = get_db()
    r = db.execute(
        "SELECT 1 FROM peca_material WHERE material_id = ? LIMIT 1",
        (material_id,),
    ).fetchone()
    return r is not None


def _row_to_material(r):
    return Material(
        id=r["id"],
        nome=r["nome"],
        unidade=r["unidade"],
        valor_unitario=r["valor_unitario"],
        quantidade_estoque=r["quantidade_estoque"],
        estoque_minimo=r["estoque_minimo"],
    )

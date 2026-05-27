"""Regra de negócio da página de Relatórios.

Lê as vendas dos últimos 30 dias e agrega de várias formas:

- KPIs gerais: faturamento, custo, lucro, margem%
- Ranking de peças por lucro (lista completa, ordenada)
- Distribuição por forma de pagamento (com % do faturamento)
- Detalhamento por peça (mesmo ranking, exibido como tabela)

Filtros disponíveis (retornam dados_filtro para o template):
- dados_por_materia_prima(material_id)
- dados_por_forma_pagamento_especifica(forma)
- dados_por_peca_detalhe(peca_id)

Esta página NÃO tem repositório próprio: consome `venda_repository` para
o consolidado e `get_db()` diretamente para as queries de filtro (joins
específicos de relatório que não pertencem a nenhum repositório geral).
"""
from datetime import date, timedelta

from database.db import get_db
from backend.repositories import venda_repository

JANELA_DIAS = 30


def dados_relatorio():
    desde = (date.today() - timedelta(days=JANELA_DIAS)).isoformat()
    vendas = venda_repository.list_vendas(desde=desde)

    faturamento = sum(v.valor_total for v in vendas)
    custo_total = sum(v.custo_total for v in vendas)
    lucro = faturamento - custo_total
    margem = (lucro / faturamento * 100) if faturamento else 0.0

    pecas_ranking = _ranking_por_peca(vendas)
    formas_pagamento = _distribuicao_por_pagamento(vendas, faturamento)

    return {
        "janela_dias": JANELA_DIAS,
        "total_vendas": len(vendas),
        "faturamento": faturamento,
        "custo_total": custo_total,
        "lucro": lucro,
        "margem": margem,
        "top_pecas": pecas_ranking[:5],
        "pecas_detalhe": pecas_ranking,
        "formas_pagamento": formas_pagamento,
    }


def formas_pagamento_disponiveis():
    """Lista todas as formas de pagamento distintas já registradas."""
    db = get_db()
    rows = db.execute(
        "SELECT DISTINCT COALESCE(forma_pagamento, 'Não informado') AS forma "
        "FROM venda ORDER BY forma COLLATE NOCASE"
    ).fetchall()
    return [r["forma"] for r in rows]


def dados_por_materia_prima(material_id):
    """Relatório filtrado por matéria-prima nos últimos JANELA_DIAS dias."""
    desde = (date.today() - timedelta(days=JANELA_DIAS)).isoformat()
    db = get_db()

    mat = db.execute(
        "SELECT id, nome, unidade, valor_unitario FROM material WHERE id = ?",
        (material_id,),
    ).fetchone()
    if not mat:
        return None

    pecas_rows = db.execute(
        "SELECT pe.id, pe.nome, pm.quantidade AS qtd_por_peca "
        "FROM peca_material pm "
        "JOIN peca pe ON pe.id = pm.peca_id "
        "WHERE pm.material_id = ? "
        "ORDER BY pe.nome COLLATE NOCASE",
        (material_id,),
    ).fetchall()

    vendas_rows = db.execute(
        "SELECT v.peca_id, pe.nome AS peca_nome, "
        "       SUM(v.quantidade) AS total_qtd, "
        "       SUM(v.valor_total) AS total_fat, "
        "       COUNT(v.id) AS total_vendas "
        "FROM venda v "
        "JOIN peca_material pm ON pm.peca_id = v.peca_id "
        "JOIN peca pe ON pe.id = v.peca_id "
        "WHERE pm.material_id = ? AND v.data >= ? "
        "GROUP BY v.peca_id, pe.nome "
        "ORDER BY total_fat DESC",
        (material_id, desde),
    ).fetchall()

    # Custo gasto com este material via produções no período (preço atual × qtd consumida)
    custo_row = db.execute(
        "SELECT COALESCE(SUM(pr.quantidade * pm.quantidade * m.valor_unitario), 0) AS custo "
        "FROM producao pr "
        "JOIN peca_material pm ON pm.peca_id = pr.peca_id "
        "JOIN material m ON m.id = pm.material_id "
        "WHERE pm.material_id = ? AND pr.data >= ?",
        (material_id, desde),
    ).fetchone()

    total_receita = sum(r["total_fat"] for r in vendas_rows)
    total_qtd_vendida = sum(r["total_qtd"] for r in vendas_rows)

    return {
        "tipo": "materia_prima",
        "material_id": material_id,
        "material_nome": mat["nome"],
        "material_unidade": mat["unidade"],
        "material_valor_unitario": mat["valor_unitario"],
        "pecas_que_usam": [dict(r) for r in pecas_rows],
        "vendas_por_peca": [dict(r) for r in vendas_rows],
        "custo_gasto": custo_row["custo"],
        "total_receita": total_receita,
        "total_qtd_vendida": total_qtd_vendida,
    }


def dados_por_forma_pagamento_especifica(forma):
    """Relatório filtrado por forma de pagamento nos últimos JANELA_DIAS dias."""
    desde = (date.today() - timedelta(days=JANELA_DIAS)).isoformat()
    db = get_db()

    total_row = db.execute(
        "SELECT COALESCE(SUM(valor_total), 0) AS total, "
        "       COUNT(id) AS qtd_vendas, "
        "       COALESCE(SUM(quantidade), 0) AS total_itens "
        "FROM venda "
        "WHERE COALESCE(forma_pagamento, 'Não informado') = ? AND data >= ?",
        (forma, desde),
    ).fetchone()

    pecas_rows = db.execute(
        "SELECT v.peca_id, pe.nome AS peca_nome, "
        "       SUM(v.quantidade) AS total_qtd, "
        "       SUM(v.valor_total) AS total_fat, "
        "       COUNT(v.id) AS total_vendas "
        "FROM venda v "
        "JOIN peca pe ON pe.id = v.peca_id "
        "WHERE COALESCE(v.forma_pagamento, 'Não informado') = ? AND v.data >= ? "
        "GROUP BY v.peca_id, pe.nome "
        "ORDER BY total_fat DESC",
        (forma, desde),
    ).fetchall()

    qtd = total_row["qtd_vendas"]
    return {
        "tipo": "forma_pagamento",
        "forma": forma,
        "total_recebido": total_row["total"],
        "qtd_vendas": qtd,
        "total_itens": total_row["total_itens"],
        "media_por_venda": (total_row["total"] / qtd) if qtd else 0.0,
        "pecas": [dict(r) for r in pecas_rows],
    }


def dados_por_peca_detalhe(peca_id):
    """Relatório filtrado por peça nos últimos JANELA_DIAS dias."""
    desde = (date.today() - timedelta(days=JANELA_DIAS)).isoformat()
    db = get_db()

    peca = db.execute(
        "SELECT pe.id, pe.nome, pe.preco_venda, pe.quantidade_estoque, "
        "       COALESCE(vpc.custo_producao, 0) AS custo_producao "
        "FROM peca pe "
        "LEFT JOIN vw_peca_custo vpc ON vpc.peca_id = pe.id "
        "WHERE pe.id = ?",
        (peca_id,),
    ).fetchone()
    if not peca:
        return None

    materiais_rows = db.execute(
        "SELECT m.nome, m.unidade, pm.quantidade, m.valor_unitario, "
        "       pm.quantidade * m.valor_unitario AS custo_parcial "
        "FROM peca_material pm "
        "JOIN material m ON m.id = pm.material_id "
        "WHERE pm.peca_id = ? "
        "ORDER BY custo_parcial DESC",
        (peca_id,),
    ).fetchall()

    prod_row = db.execute(
        "SELECT COALESCE(SUM(quantidade), 0) AS total_produzido, "
        "       COALESCE(SUM(quantidade * custo_unitario), 0) AS custo_investido "
        "FROM producao WHERE peca_id = ? AND data >= ?",
        (peca_id, desde),
    ).fetchone()

    vendas_por_forma = db.execute(
        "SELECT COALESCE(forma_pagamento, 'Não informado') AS forma, "
        "       SUM(valor_total) AS total, "
        "       SUM(quantidade) AS qtd, "
        "       COUNT(id) AS vendas "
        "FROM venda "
        "WHERE peca_id = ? AND data >= ? "
        "GROUP BY forma ORDER BY total DESC",
        (peca_id, desde),
    ).fetchall()

    total_row = db.execute(
        "SELECT COALESCE(SUM(valor_total), 0) AS total_fat, "
        "       COALESCE(SUM(quantidade), 0) AS total_qtd, "
        "       COUNT(id) AS total_vendas "
        "FROM venda WHERE peca_id = ? AND data >= ?",
        (peca_id, desde),
    ).fetchone()

    return {
        "tipo": "peca",
        "peca_id": peca_id,
        "peca_nome": peca["nome"],
        "peca_preco_venda": peca["preco_venda"],
        "peca_estoque": peca["quantidade_estoque"],
        "custo_producao_atual": peca["custo_producao"],
        "materiais": [dict(r) for r in materiais_rows],
        "total_produzido": prod_row["total_produzido"],
        "custo_investido": prod_row["custo_investido"],
        "vendas_por_forma": [dict(r) for r in vendas_por_forma],
        "total_faturamento": total_row["total_fat"],
        "total_qtd_vendida": total_row["total_qtd"],
        "total_vendas": total_row["total_vendas"],
    }


def _ranking_por_peca(vendas):
    """Agrupa vendas por peça e calcula totais. Ordena por lucro desc."""
    por_peca = {}
    for v in vendas:
        d = por_peca.setdefault(v.peca_id, {
            "peca_id": v.peca_id,
            "peca_nome": v.peca_nome,
            "vendas": 0,
            "quantidade": 0,
            "faturamento": 0.0,
            "custo": 0.0,
        })
        d["vendas"] += 1
        d["quantidade"] += v.quantidade
        d["faturamento"] += v.valor_total
        d["custo"] += v.custo_total

    for d in por_peca.values():
        d["lucro"] = d["faturamento"] - d["custo"]
        d["margem"] = (d["lucro"] / d["faturamento"] * 100) if d["faturamento"] else 0.0

    return sorted(por_peca.values(), key=lambda x: x["lucro"], reverse=True)


def _distribuicao_por_pagamento(vendas, faturamento):
    """Soma valor_total por forma de pagamento e calcula % do faturamento."""
    por_forma = {}
    for v in vendas:
        chave = v.forma_pagamento or "Não informado"
        por_forma[chave] = por_forma.get(chave, 0.0) + v.valor_total

    resultado = [
        {
            "forma": forma,
            "valor": valor,
            "pct": (valor / faturamento * 100) if faturamento else 0.0,
        }
        for forma, valor in por_forma.items()
    ]
    resultado.sort(key=lambda x: x["valor"], reverse=True)
    return resultado

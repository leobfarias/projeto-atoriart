"""Regra de negócio da página de Relatórios.

Agrega vendas e despesas em duas dimensões:

- **Período** (`mes` opcional). Sem parâmetro: últimos 30 dias. Com
  parâmetro 'YYYY-MM': aquele mês inteiro (ex.: '2026-05' → todo o
  mês de maio de 2026).
- **Recorte** (filtro opcional via `dados_por_*`): matéria-prima,
  forma de pagamento ou peça específica.

Os dois se compõem — `?mes=2026-05&filtro=peca&peca_id=3` mostra a
peça 3 só com dados de maio/2026.

KPIs centrais no consolidado:
- Faturamento, Custo de produção, Lucro bruto, **Lucro líquido**
  (= faturamento − custo − despesas do mesmo período).

Esta página NÃO tem repositório próprio: consome
`venda_repository` / `despesa_repository` para o consolidado e
`get_db()` diretamente para as queries de filtro (joins específicos
de relatório que não pertencem a nenhum repositório geral).
"""
from datetime import date, timedelta

from database.db import get_db
from backend.repositories import despesa_repository, venda_repository

JANELA_DIAS = 30

NOMES_MESES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


# ---------- Período (mês específico OU últimos 30 dias) ----------

def _periodo(mes):
    """Devolve `(desde, ate, label)` a partir de `mes` ('YYYY-MM' ou None).

    `desde` e `ate` são strings ISO ('YYYY-MM-DD') prontas pra alimentar
    os repositórios e SQL inline. `label` é o texto exibido no template.
    """
    if mes:
        ano_str, mes_str = mes.split("-")
        ano, m = int(ano_str), int(mes_str)
        primeiro = date(ano, m, 1)
        if m == 12:
            proximo = date(ano + 1, 1, 1)
        else:
            proximo = date(ano, m + 1, 1)
        ultimo = proximo - timedelta(days=1)
        return primeiro.isoformat(), ultimo.isoformat(), f"{NOMES_MESES[m]}/{ano}"
    # Default: janela rolante.
    ate = date.today()
    desde = ate - timedelta(days=JANELA_DIAS)
    return desde.isoformat(), ate.isoformat(), f"últimos {JANELA_DIAS} dias"


def meses_disponiveis():
    """Meses ('YYYY-MM') com pelo menos uma venda ou despesa registrada.

    Devolve lista de dicts `{'valor': '2026-05', 'label': 'Maio/2026'}`
    do mais recente para o mais antigo — alimenta o `<select>` do filtro.
    """
    db = get_db()
    rows = db.execute(
        "SELECT DISTINCT strftime('%Y-%m', data) AS mes FROM venda "
        "UNION "
        "SELECT DISTINCT strftime('%Y-%m', data) AS mes FROM despesa "
        "ORDER BY mes DESC"
    ).fetchall()
    return [_label_mes(r["mes"]) for r in rows if r["mes"]]


def _label_mes(valor):
    ano_str, mes_str = valor.split("-")
    return {"valor": valor, "label": f"{NOMES_MESES[int(mes_str)]}/{ano_str}"}


# ---------- Consolidado ----------

def dados_relatorio(mes=None):
    desde, ate, periodo_label = _periodo(mes)

    vendas = venda_repository.list_vendas(desde=desde, ate=ate)
    despesas = despesa_repository.list_despesas(desde=desde, ate=ate)

    faturamento = sum(v.valor_total for v in vendas)
    custo_total = sum(v.custo_total for v in vendas)
    lucro_bruto = faturamento - custo_total
    total_despesas = sum(d.valor for d in despesas)
    lucro_liquido = lucro_bruto - total_despesas

    pecas_ranking = _ranking_por_peca(vendas)
    formas_pagamento = _distribuicao_por_pagamento(vendas, faturamento)

    return {
        "mes_selecionado": mes or "",
        "periodo_label": periodo_label,
        "total_vendas": len(vendas),
        "faturamento": faturamento,
        "custo_total": custo_total,
        "lucro_bruto": lucro_bruto,
        "total_despesas": total_despesas,
        "lucro_liquido": lucro_liquido,
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


# ---------- Recortes (matéria-prima / forma de pagamento / peça) ----------

def dados_por_materia_prima(material_id, mes=None):
    desde, ate, periodo_label = _periodo(mes)
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
        "WHERE pm.material_id = ? AND v.data >= ? AND v.data <= ? "
        "GROUP BY v.peca_id, pe.nome "
        "ORDER BY total_fat DESC",
        (material_id, desde, ate),
    ).fetchall()

    # Custo gasto com este material via produções no período (preço atual × qtd consumida).
    custo_row = db.execute(
        "SELECT COALESCE(SUM(pr.quantidade * pm.quantidade * m.valor_unitario), 0) AS custo "
        "FROM producao pr "
        "JOIN peca_material pm ON pm.peca_id = pr.peca_id "
        "JOIN material m ON m.id = pm.material_id "
        "WHERE pm.material_id = ? AND pr.data >= ? AND pr.data <= ?",
        (material_id, desde, ate),
    ).fetchone()

    total_receita = sum(r["total_fat"] for r in vendas_rows)
    total_qtd_vendida = sum(r["total_qtd"] for r in vendas_rows)

    return {
        "tipo": "materia_prima",
        "periodo_label": periodo_label,
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


def dados_por_forma_pagamento_especifica(forma, mes=None):
    desde, ate, periodo_label = _periodo(mes)
    db = get_db()

    total_row = db.execute(
        "SELECT COALESCE(SUM(valor_total), 0) AS total, "
        "       COUNT(id) AS qtd_vendas, "
        "       COALESCE(SUM(quantidade), 0) AS total_itens "
        "FROM venda "
        "WHERE COALESCE(forma_pagamento, 'Não informado') = ? "
        "  AND data >= ? AND data <= ?",
        (forma, desde, ate),
    ).fetchone()

    pecas_rows = db.execute(
        "SELECT v.peca_id, pe.nome AS peca_nome, "
        "       SUM(v.quantidade) AS total_qtd, "
        "       SUM(v.valor_total) AS total_fat, "
        "       COUNT(v.id) AS total_vendas "
        "FROM venda v "
        "JOIN peca pe ON pe.id = v.peca_id "
        "WHERE COALESCE(v.forma_pagamento, 'Não informado') = ? "
        "  AND v.data >= ? AND v.data <= ? "
        "GROUP BY v.peca_id, pe.nome "
        "ORDER BY total_fat DESC",
        (forma, desde, ate),
    ).fetchall()

    qtd = total_row["qtd_vendas"]
    return {
        "tipo": "forma_pagamento",
        "periodo_label": periodo_label,
        "forma": forma,
        "total_recebido": total_row["total"],
        "qtd_vendas": qtd,
        "total_itens": total_row["total_itens"],
        "media_por_venda": (total_row["total"] / qtd) if qtd else 0.0,
        "pecas": [dict(r) for r in pecas_rows],
    }


def dados_por_peca_detalhe(peca_id, mes=None):
    desde, ate, periodo_label = _periodo(mes)
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
        "FROM producao WHERE peca_id = ? AND data >= ? AND data <= ?",
        (peca_id, desde, ate),
    ).fetchone()

    vendas_por_forma = db.execute(
        "SELECT COALESCE(forma_pagamento, 'Não informado') AS forma, "
        "       SUM(valor_total) AS total, "
        "       SUM(quantidade) AS qtd, "
        "       COUNT(id) AS vendas "
        "FROM venda "
        "WHERE peca_id = ? AND data >= ? AND data <= ? "
        "GROUP BY forma ORDER BY total DESC",
        (peca_id, desde, ate),
    ).fetchall()

    total_row = db.execute(
        "SELECT COALESCE(SUM(valor_total), 0) AS total_fat, "
        "       COALESCE(SUM(quantidade), 0) AS total_qtd, "
        "       COUNT(id) AS total_vendas "
        "FROM venda WHERE peca_id = ? AND data >= ? AND data <= ?",
        (peca_id, desde, ate),
    ).fetchone()

    return {
        "tipo": "peca",
        "periodo_label": periodo_label,
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


# ---------- Agregações em memória (consolidado) ----------

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

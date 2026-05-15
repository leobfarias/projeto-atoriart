"""Regra de negócio da página de Relatórios.

Lê as vendas dos últimos 30 dias e agrega de várias formas:

- KPIs gerais: faturamento, custo, lucro, margem%
- Ranking de peças por lucro (lista completa, ordenada)
- Distribuição por forma de pagamento (com % do faturamento)
- Detalhamento por peça (mesmo ranking, exibido como tabela)

Esta página NÃO tem repositório próprio: consome `venda_repository`.
Toda a agregação acontece em memória, em Python — o volume é pequeno
(últimos 30 dias) e fica didático ver as contas no service.
"""
from datetime import date, timedelta

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

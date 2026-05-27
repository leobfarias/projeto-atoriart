"""Regra de negócio do Catálogo (vitrine).

O catálogo é a vitrine: lista apenas as peças que JÁ FORAM PRODUZIDAS
e estão disponíveis para venda (quantidade_estoque > 0).

O cadastro/edição/remoção da peça acontece em [peca_service](peca_service.py)
e é exposto via blueprint de **Produção** — peça nasce lá quando é
produzida pela primeira vez.

`custo_investido` usa o total histórico de produções (ADR-013): soma
quantidade × custo_unitario de TODOS os registros, não do estoque atual.
Assim o valor não diminui quando peças são vendidas.
"""
from backend.repositories import peca_repository, producao_repository


def dados_catalogo():
    pecas = peca_repository.list_pecas(apenas_em_estoque=False)
    return {
        "pecas": pecas,
        "modelos_disponiveis": len(pecas),
        "pecas_em_estoque": sum(p.quantidade_estoque for p in pecas),
        "custo_investido": producao_repository.custo_total_investido(),
    }

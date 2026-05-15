"""Modelo de Venda.

Cada venda representa "no dia X foram vendidas N unidades da peça Y por
R$ Z, pagas via método W".

`peca_nome` e `peca_custo` são denormalizados aqui (vêm do JOIN com
`peca` no repositório) — evitam carregar a `Peca` completa só pra
exibir o nome e calcular o lucro bruto da venda.
"""
from dataclasses import dataclass


@dataclass
class Venda:
    id: int
    peca_id: int
    peca_nome: str
    peca_custo: float
    quantidade: int
    valor_total: float
    data: str                          # 'YYYY-MM-DD'
    forma_pagamento: str | None = None

    @property
    def custo_total(self) -> float:
        """Custo de produção das peças vendidas nesta venda."""
        return self.quantidade * self.peca_custo

    @property
    def lucro_bruto(self) -> float:
        """Valor que sobrou após cobrir o custo de produção."""
        return self.valor_total - self.custo_total

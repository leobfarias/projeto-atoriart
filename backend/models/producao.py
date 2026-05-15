"""Modelo de Produção.

Cada produção representa "no dia X foram produzidas N unidades da peça Y".

Campos `peca_nome` e `peca_custo` são denormalizados aqui (vêm do JOIN
no repositório) — evitam carregar a `Peca` inteira (com seus materiais)
só pra exibir nome e calcular subtotal de custo.
"""
from dataclasses import dataclass


@dataclass
class Producao:
    id: int
    peca_id: int
    peca_nome: str
    peca_custo: float
    quantidade: int
    data: str                     # 'YYYY-MM-DD'
    observacao: str | None = None

    @property
    def custo_subtotal(self) -> float:
        return self.quantidade * self.peca_custo

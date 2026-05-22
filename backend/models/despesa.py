"""Modelo de Despesa.

Cada despesa representa "no dia X foi gasto R$ Z com W" — um custo
operacional ou fixo do negócio: aluguel, contas de luz, marketing,
taxas, etc.

Atenção ao escopo: a matéria-prima usada na produção NÃO é despesa —
ela tem módulo próprio (/materiais/). Aqui entram só custos fora do
escopo de produto.

Diferente de `Venda` e `Producao`, a despesa NÃO tem efeito no estoque
nem referência a peça: é um registro puro. Entra apenas no cálculo da
receita líquida (faturamento − despesas) do período.
"""
from dataclasses import dataclass


@dataclass
class Despesa:
    id: int
    descricao: str
    valor: float
    data: str                      # 'YYYY-MM-DD'
    categoria: str | None = None

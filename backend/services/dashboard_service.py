"""Camada de serviço do dashboard.

Responsável por montar o ViewModel exibido no painel a partir das regras de
negócio. Por enquanto retorna dados mockados — quando os módulos de vendas,
estoque, produção e despesas existirem, esta função consultará os repositórios
e aplicará as regras de cálculo:

    faturamento_30d  = soma(valor) das vendas dos últimos 30 dias
    receita_liquida  = faturamento_30d - despesas_30d
    pecas_em_estoque = soma(quantidade) dos itens em estoque
    producao_30d     = contagem de produções nos últimos 30 dias
    estoque_baixo    = materiais com quantidade < mínimo
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LowStockItem:
    nome: str
    quantidade_atual: int
    minimo: int


@dataclass
class DashboardViewModel:
    saudacao: str
    faturamento_30d: float
    receita_liquida: float
    pecas_em_estoque: int
    producao_30d: int
    estoque_baixo: list[LowStockItem] = field(default_factory=list)


def _saudacao_por_horario(now: datetime | None = None) -> str:
    now = now or datetime.now()
    hora = now.hour
    if 5 <= hora < 12:
        return "Bom dia"
    if 12 <= hora < 18:
        return "Boa tarde"
    return "Boa noite"


def build_dashboard_view_model() -> DashboardViewModel:
    # TODO(fase futura): substituir mock por consultas reais via repositórios.
    return DashboardViewModel(
        saudacao=_saudacao_por_horario(),
        faturamento_30d=0.0,
        receita_liquida=0.0,
        pecas_em_estoque=0,
        producao_30d=0,
        estoque_baixo=[],
    )

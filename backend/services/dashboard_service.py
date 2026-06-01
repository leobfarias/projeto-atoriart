"""Camada de serviço do dashboard."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from backend.repositories import despesa_repository, material_repository
from backend.repositories import peca_repository, producao_repository
from backend.repositories import venda_repository


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
    desde = (date.today() - timedelta(days=30)).isoformat()

    vendas = venda_repository.list_vendas(desde=desde)
    faturamento_30d = sum(v.valor_total for v in vendas)

    # Receita líquida = faturamento − despesas do período − compras de materiais no período.
    despesas = despesa_repository.list_despesas(desde=desde)
    receita_liquida = (
        faturamento_30d
        - sum(d.valor for d in despesas)
        - material_repository.gasto_periodo(desde)
    )

    pecas = peca_repository.list_pecas()
    pecas_em_estoque = sum(p.quantidade_estoque for p in pecas)

    producoes = producao_repository.list_producoes(desde=desde)
    producao_30d = len(producoes)

    materiais = material_repository.list_materiais()
    estoque_baixo = [
        LowStockItem(
            nome=m.nome,
            quantidade_atual=m.quantidade_estoque,
            minimo=m.estoque_minimo,
        )
        for m in materiais
        if m.em_alerta
    ]

    return DashboardViewModel(
        saudacao=_saudacao_por_horario(),
        faturamento_30d=faturamento_30d,
        receita_liquida=receita_liquida,
        pecas_em_estoque=pecas_em_estoque,
        producao_30d=producao_30d,
        estoque_baixo=estoque_baixo,
    )

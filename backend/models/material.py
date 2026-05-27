"""Modelo de Material (matéria-prima).

Entidade própria do módulo de matéria-prima. É também usada pelo módulo
de catálogo (cada peça consome materiais via ItemMaterial).
"""
from dataclasses import dataclass


@dataclass
class Material:
    id: int
    nome: str
    unidade: str            # ex.: "m", "g", "un"
    valor_unitario: float   # custo por unidade
    quantidade_estoque: float = 0.0
    estoque_minimo: float = 0.0

    @property
    def em_alerta(self) -> bool:
        """True quando o estoque atual está abaixo do mínimo configurado."""
        return self.quantidade_estoque < self.estoque_minimo

    @property
    def valor_estoque(self) -> float:
        """Valor atual investido neste material (valor_unitario × estoque)."""
        return self.valor_unitario * self.quantidade_estoque

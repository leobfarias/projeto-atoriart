"""Modelos do catálogo.

Classes simples (dataclasses) que carregam dados de peças.
Não conhecem Flask nem SQL — quem fala com o banco é o repositório.

A classe `Material` foi movida para `backend/models/material.py` (módulo
próprio, já que matéria-prima é um domínio independente). Reimportamos
aqui pra manter compatibilidade com quem já fazia `from backend.models.peca
import Material`.
"""
from dataclasses import dataclass, field

from backend.models.material import Material  # noqa: F401 (reexport)


@dataclass
class ItemMaterial:
    """Um material consumido por uma peça, com a quantidade utilizada."""
    material: Material
    quantidade: float


@dataclass
class Peca:
    """Uma peça do catálogo.

    `preco_venda` é o preço sugerido de venda — o único valor financeiro
    que o usuário digita. `custo_producao` NÃO é digitado: é calculado a
    partir dos materiais (view `vw_peca_custo`) e chega já pronto do
    repositório. O lucro/margem saem da diferença entre os dois.
    """
    id: int
    nome: str
    preco_venda: float
    quantidade_estoque: int
    custo_producao: float = 0.0          # calculado: soma dos materiais
    materiais: list = field(default_factory=list)

    @property
    def lucro(self) -> float:
        """Lucro estimado por peça: preço de venda − custo dos materiais."""
        return self.preco_venda - self.custo_producao

    @property
    def margem(self) -> float:
        """Margem do lucro sobre o preço de venda, em %."""
        return (self.lucro / self.preco_venda * 100) if self.preco_venda else 0.0

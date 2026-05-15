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
    id: int
    nome: str
    custo_producao: float
    quantidade_estoque: int
    materiais: list = field(default_factory=list)

"""Rotas da página de Catálogo (vitrine de peças disponíveis).

O catálogo é apenas leitura: mostra as peças com `quantidade_estoque > 0`.
Cadastro/edição/remoção de peça vive em
[`producao.routes`](../producao/routes.py) (a peça nasce ao ser produzida).
"""
from flask import Blueprint, render_template

from backend.security import login_required
from backend.services import catalogo_service

catalogo_bp = Blueprint("catalogo", __name__, url_prefix="/catalogo")


@catalogo_bp.route("/")
@login_required
def index():
    dados = catalogo_service.dados_catalogo()
    return render_template("catalogo/index.html", **dados)

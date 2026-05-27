"""Rotas da página de Relatórios.

GET /relatorios/  — visão consolidada dos últimos 30 dias.
GET /relatorios/?filtro=materia_prima&material_id=X
GET /relatorios/?filtro=forma_pagamento&forma=PIX
GET /relatorios/?filtro=peca&peca_id=X

Sem ações de escrita — relatório é visão de leitura.
"""
from flask import Blueprint, render_template, request

from backend.security import login_required
from backend.repositories import material_repository, peca_repository
from backend.services.relatorios_service import (
    dados_relatorio,
    formas_pagamento_disponiveis,
    dados_por_materia_prima,
    dados_por_forma_pagamento_especifica,
    dados_por_peca_detalhe,
)

relatorios_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")


@relatorios_bp.route("/")
@login_required
def index():
    filtro = request.args.get("filtro", "")
    material_id = request.args.get("material_id", type=int)
    peca_id = request.args.get("peca_id", type=int)
    forma = request.args.get("forma", "")

    dados = dados_relatorio()
    materiais = material_repository.list_materiais()
    pecas = peca_repository.list_pecas()
    formas_disponiveis = formas_pagamento_disponiveis()

    dados_filtro = None
    if filtro == "materia_prima" and material_id:
        dados_filtro = dados_por_materia_prima(material_id)
    elif filtro == "forma_pagamento" and forma:
        dados_filtro = dados_por_forma_pagamento_especifica(forma)
    elif filtro == "peca" and peca_id:
        dados_filtro = dados_por_peca_detalhe(peca_id)

    return render_template(
        "relatorios/index.html",
        **dados,
        materiais=materiais,
        pecas=pecas,
        formas_disponiveis=formas_disponiveis,
        filtro=filtro,
        material_id=material_id,
        peca_id=peca_id,
        forma=forma,
        dados_filtro=dados_filtro,
    )

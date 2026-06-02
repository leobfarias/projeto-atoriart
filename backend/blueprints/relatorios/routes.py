"""Rotas da página de Relatórios.

GET /relatorios/  — visão consolidada (default: últimos 30 dias).
GET /relatorios/?mes=2026-05            — mês específico
GET /relatorios/?filtro=materia_prima&material_id=X[&mes=YYYY-MM]
GET /relatorios/?filtro=forma_pagamento&forma=PIX[&mes=YYYY-MM]
GET /relatorios/?filtro=peca&peca_id=X[&mes=YYYY-MM]
GET /relatorios/exportar.xlsx[?mes=YYYY-MM]
    — baixa o consolidado em Excel (Resumo + Peças + Pagamentos).

Sem ações de escrita — relatório é visão de leitura.
"""
from flask import Blueprint, render_template, request, send_file

from backend.security import login_required
from backend.repositories import material_repository, peca_repository
from backend.services.relatorios_export import gerar_xlsx
from backend.services.relatorios_service import (
    dados_relatorio,
    formas_pagamento_disponiveis,
    meses_disponiveis,
    dados_por_materia_prima,
    dados_por_forma_pagamento_especifica,
    dados_por_peca_detalhe,
)

relatorios_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")


@relatorios_bp.route("/")
@login_required
def index():
    mes = request.args.get("mes", "")
    filtro = request.args.get("filtro", "")
    material_id = request.args.get("material_id", type=int)
    peca_id = request.args.get("peca_id", type=int)
    forma = request.args.get("forma", "")

    dados = dados_relatorio(mes=mes or None)

    dados_filtro = None
    if filtro == "materia_prima" and material_id:
        dados_filtro = dados_por_materia_prima(material_id, mes=mes or None)
    elif filtro == "forma_pagamento" and forma:
        dados_filtro = dados_por_forma_pagamento_especifica(forma, mes=mes or None)
    elif filtro == "peca" and peca_id:
        dados_filtro = dados_por_peca_detalhe(peca_id, mes=mes or None)

    return render_template(
        "relatorios/index.html",
        **dados,
        materiais=material_repository.list_materiais(),
        pecas=peca_repository.list_pecas(),
        formas_disponiveis=formas_pagamento_disponiveis(),
        meses=meses_disponiveis(),
        filtro=filtro,
        material_id=material_id,
        peca_id=peca_id,
        forma=forma,
        dados_filtro=dados_filtro,
    )


@relatorios_bp.route("/exportar.xlsx")
@login_required
def exportar_excel():
    """Devolve o consolidado em .xlsx, preservando o período selecionado."""
    mes = request.args.get("mes", "")
    dados = dados_relatorio(mes=mes or None)
    arquivo = gerar_xlsx(dados)
    nome = f"relatorio-{mes or 'ultimos-30-dias'}.xlsx"
    return send_file(
        arquivo,
        as_attachment=True,
        download_name=nome,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

"""Rotas da página de Relatórios.

Só uma rota (GET): exibe o relatório consolidado dos últimos 30 dias.
Sem ações de escrita — relatório é visão de leitura.
"""
from flask import Blueprint, render_template

from backend.security import login_required
from backend.services.relatorios_service import dados_relatorio

relatorios_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")


@relatorios_bp.route("/")
@login_required
def index():
    dados = dados_relatorio()
    return render_template("relatorios/index.html", **dados)

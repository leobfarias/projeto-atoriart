"""Rotas da página de Vendas."""
from datetime import date

from flask import (Blueprint, flash, redirect, render_template,
                   request, url_for)

from backend.repositories import peca_repository
from backend.security import login_required, require_csrf
from backend.services import vendas_service

vendas_bp = Blueprint("vendas", __name__, url_prefix="/vendas")


# ---------- Listagem ----------

@vendas_bp.route("/")
@login_required
def index():
    dados = vendas_service.dados_vendas()
    return render_template("vendas/index.html", **dados)


# ---------- Criar ----------

@vendas_bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    pecas = peca_repository.list_pecas()
    formas = vendas_service.formas_pagamento_padrao()

    if request.method == "POST":
        require_csrf()
        erros, _ = vendas_service.criar(request.form)
        if erros:
            return render_template(
                "vendas/form.html",
                erros=erros, valores=request.form,
                pecas=pecas, formas=formas, hoje=date.today().isoformat(),
            )
        flash("Venda registrada (estoque atualizado).", "success")
        return redirect(url_for("vendas.index"))

    return render_template(
        "vendas/form.html",
        erros={}, valores={"data": date.today().isoformat()},
        pecas=pecas, formas=formas, hoje=date.today().isoformat(),
    )


# ---------- Apagar ----------

@vendas_bp.route("/<int:venda_id>/apagar", methods=["POST"])
@login_required
def apagar(venda_id):
    require_csrf()
    erro = vendas_service.apagar(venda_id)
    if erro:
        flash(erro, "error")
    else:
        flash("Venda apagada (estoque devolvido).", "success")
    return redirect(url_for("vendas.index"))

"""Rotas da página de Despesas.

CRUD enxuto (sem editar — assim como Vendas e Produção): a despesa é um
registro de histórico; para corrigir, apaga-se e lança-se de novo.
"""
from datetime import date

from flask import (Blueprint, flash, redirect, render_template,
                   request, url_for)

from backend.security import login_required, require_csrf
from backend.services import despesas_service

despesas_bp = Blueprint("despesas", __name__, url_prefix="/despesas")


# ---------- Listagem ----------

@despesas_bp.route("/")
@login_required
def index():
    dados = despesas_service.dados_despesas()
    return render_template("despesas/index.html", **dados)


# ---------- Criar ----------

@despesas_bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    categorias = despesas_service.categorias_padrao()

    if request.method == "POST":
        require_csrf()
        erros, _ = despesas_service.criar(request.form)
        if erros:
            return render_template(
                "despesas/form.html",
                erros=erros, valores=request.form,
                categorias=categorias, hoje=date.today().isoformat(),
            )
        flash("Despesa registrada.", "success")
        return redirect(url_for("despesas.index"))

    return render_template(
        "despesas/form.html",
        erros={}, valores={"data": date.today().isoformat()},
        categorias=categorias, hoje=date.today().isoformat(),
    )


# ---------- Apagar ----------

@despesas_bp.route("/<int:despesa_id>/apagar", methods=["POST"])
@login_required
def apagar(despesa_id):
    require_csrf()
    erro = despesas_service.apagar(despesa_id)
    if erro:
        flash(erro, "error")
    else:
        flash("Despesa apagada.", "success")
    return redirect(url_for("despesas.index"))

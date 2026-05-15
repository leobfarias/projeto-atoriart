"""Rotas da página de Matéria-prima."""
from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, url_for)

from backend.repositories import material_repository
from backend.security import login_required, require_csrf
from backend.services import materia_prima_service

materia_prima_bp = Blueprint("materia_prima", __name__, url_prefix="/materiais")


# ---------- Listagem ----------

@materia_prima_bp.route("/")
@login_required
def index():
    dados = materia_prima_service.dados_materia_prima()
    return render_template("materia_prima/index.html", **dados)


# ---------- Criar ----------

@materia_prima_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    if request.method == "POST":
        require_csrf()
        erros, novo_id = materia_prima_service.criar(request.form)
        if erros:
            return render_template(
                "materia_prima/form.html",
                modo="novo",
                erros=erros,
                valores=request.form,
            )
        flash("Material cadastrado.", "success")
        return redirect(url_for("materia_prima.index"))

    return render_template(
        "materia_prima/form.html",
        modo="novo",
        erros={},
        valores={},
    )


# ---------- Editar ----------

@materia_prima_bp.route("/<int:material_id>/editar", methods=["GET", "POST"])
@login_required
def editar(material_id):
    material = material_repository.get_material(material_id)
    if material is None:
        abort(404)

    if request.method == "POST":
        require_csrf()
        erros, _ = materia_prima_service.atualizar(material_id, request.form)
        if erros:
            return render_template(
                "materia_prima/form.html",
                modo="editar",
                material_id=material_id,
                erros=erros,
                valores=request.form,
            )
        flash("Material atualizado.", "success")
        return redirect(url_for("materia_prima.index"))

    # GET — pre-preenche com os valores atuais
    valores = {
        "nome": material.nome,
        "unidade": material.unidade,
        "valor_unitario": material.valor_unitario,
        "quantidade_estoque": material.quantidade_estoque,
        "estoque_minimo": material.estoque_minimo,
    }
    return render_template(
        "materia_prima/form.html",
        modo="editar",
        material_id=material_id,
        erros={},
        valores=valores,
    )


# ---------- Apagar ----------

@materia_prima_bp.route("/<int:material_id>/apagar", methods=["POST"])
@login_required
def apagar(material_id):
    require_csrf()
    erro = materia_prima_service.apagar(material_id)
    if erro:
        flash(erro, "error")
    else:
        flash("Material removido.", "success")
    return redirect(url_for("materia_prima.index"))

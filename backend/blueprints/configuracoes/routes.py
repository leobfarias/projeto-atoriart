"""Rotas da página de Configurações."""
from flask import (
    Blueprint, current_app, flash, redirect, render_template, request, url_for
)

from backend.security import login_required, logout_session, require_csrf
from backend.services import configuracoes_service

configuracoes_bp = Blueprint(
    "configuracoes", __name__, url_prefix="/configuracoes"
)


@configuracoes_bp.route("/")
@login_required
def index():
    dados = configuracoes_service.coletar_info_sistema()
    return render_template("configuracoes/index.html", **dados)


@configuracoes_bp.route("/trocar-senha", methods=["GET", "POST"])
@login_required
def trocar_senha():
    username = current_app.config.get("ADMIN_USERNAME", "admin")

    if request.method == "POST":
        require_csrf()
        erros, _ = configuracoes_service.trocar_senha(username, request.form)
        if erros:
            return render_template(
                "configuracoes/trocar_senha.html",
                erros=erros,
                valores={"confirma_troca": request.form.get("confirma_troca")},
            )
        # Sucesso: desloga e força login com a nova senha.
        logout_session()
        flash(
            "Senha alterada com sucesso. Entre novamente com a nova senha.",
            "success",
        )
        return redirect(url_for("auth.login"))

    return render_template(
        "configuracoes/trocar_senha.html",
        erros={},
        valores={},
    )

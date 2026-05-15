"""Rotas da página de Configurações."""
from flask import Blueprint, flash, redirect, render_template, url_for

from backend.security import login_required, require_csrf
from backend.services.configuracoes_service import coletar_info_sistema

configuracoes_bp = Blueprint(
    "configuracoes", __name__, url_prefix="/configuracoes"
)


@configuracoes_bp.route("/")
@login_required
def index():
    dados = coletar_info_sistema()
    return render_template("configuracoes/index.html", **dados)


# ---- Ações placeholder (implementação real em etapa dedicada) ----

@configuracoes_bp.route("/trocar-senha", methods=["POST"])
@login_required
def trocar_senha():
    require_csrf()
    flash(
        "Troca de senha pela interface: em desenvolvimento. "
        "Por enquanto, gere um novo ADMIN_PASSWORD_HASH no .env.",
        "info",
    )
    return redirect(url_for("configuracoes.index"))


@configuracoes_bp.route("/resetar-banco", methods=["POST"])
@login_required
def resetar_banco():
    require_csrf()
    flash(
        "Reset pela interface: em desenvolvimento. "
        "Por enquanto, rode 'python database/init_db.py' no terminal.",
        "info",
    )
    return redirect(url_for("configuracoes.index"))

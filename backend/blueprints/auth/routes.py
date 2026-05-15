"""Rotas de autenticação do administrador.

Mantém apenas controle de fluxo HTTP. Toda a regra de autenticação
(comparação de credenciais, sessão, CSRF) vive em `backend/security.py`.
"""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from backend.security import (
    authenticate,
    is_authenticated,
    login_session,
    logout_session,
    require_csrf,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if is_authenticated():
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        require_csrf()
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if authenticate(username, password):
            login_session(username)
            next_url = _safe_next(request.args.get("next"))
            return redirect(next_url or url_for("dashboard.index"))

        flash("Credenciais inválidas.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    require_csrf()
    logout_session()
    return redirect(url_for("auth.login"))


def _safe_next(target: str | None) -> str | None:
    """Aceita apenas redirects relativos (evita open redirect)."""
    if not target:
        return None
    if target.startswith("/") and not target.startswith("//"):
        return target
    return None

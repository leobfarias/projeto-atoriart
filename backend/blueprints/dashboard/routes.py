"""Rotas do Painel (Dashboard)."""
from __future__ import annotations

from flask import Blueprint, render_template

from backend.security import login_required
from backend.services.dashboard_service import build_dashboard_view_model

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/painel")


@dashboard_bp.route("/")
@login_required
def index():
    vm = build_dashboard_view_model()
    return render_template("dashboard/index.html", vm=vm)

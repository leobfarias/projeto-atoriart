"""Application factory do AtoriArt (camada backend).

Este pacote contém todo o código Python da aplicação: configuração,
segurança, blueprints, serviços, repositórios e modelos.

Templates Jinja e arquivos estáticos ficam em `frontend/`.
Banco SQLite e infra de dados ficam em `database/`.
Apontamos o Flask explicitamente para esses caminhos abaixo.
"""
from __future__ import annotations

from pathlib import Path

from flask import Flask, redirect, url_for

from backend.config import BaseConfig, get_config
from backend.security import current_user, generate_csrf_token, is_authenticated

__version__ = "1.0.0"

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def create_app(config_class: type[BaseConfig] | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(FRONTEND_DIR / "templates"),
        static_folder=str(FRONTEND_DIR / "static"),
    )

    cfg = config_class or get_config()
    app.config.from_object(cfg)

    _ensure_secret_key(app)
    _ensure_database_dir(app)
    _register_database(app)
    _register_blueprints(app)
    _register_context_processors(app)
    _register_security_headers(app)

    return app


def _ensure_secret_key(app: Flask) -> None:
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY ausente. Defina no .env. "
            'Gere com: python -c "import secrets; print(secrets.token_hex(32))"'
        )


def _ensure_database_dir(app: Flask) -> None:
    db_dir = app.config["DATABASE_DIR"]
    db_dir.mkdir(parents=True, exist_ok=True)


def _register_database(app: Flask) -> None:
    from database import db
    db.init_app(app)


def _register_blueprints(app: Flask) -> None:
    from backend.blueprints.auth.routes import auth_bp
    from backend.blueprints.catalogo.routes import catalogo_bp
    from backend.blueprints.configuracoes.routes import configuracoes_bp
    from backend.blueprints.dashboard.routes import dashboard_bp
    from backend.blueprints.despesas.routes import despesas_bp
    from backend.blueprints.materia_prima.routes import materia_prima_bp
    from backend.blueprints.producao.routes import producao_bp
    from backend.blueprints.relatorios.routes import relatorios_bp
    from backend.blueprints.vendas.routes import vendas_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(catalogo_bp)
    app.register_blueprint(materia_prima_bp)
    app.register_blueprint(producao_bp)
    app.register_blueprint(vendas_bp)
    app.register_blueprint(despesas_bp)
    app.register_blueprint(relatorios_bp)
    app.register_blueprint(configuracoes_bp)

    @app.route("/")
    def index():
        return redirect(url_for("dashboard.index"))


def _register_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_globals():
        return {
            "current_user": current_user(),
            "is_authenticated": is_authenticated(),
            "csrf_token": generate_csrf_token,
        }


def _register_security_headers(app: Flask) -> None:
    @app.after_request
    def set_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response

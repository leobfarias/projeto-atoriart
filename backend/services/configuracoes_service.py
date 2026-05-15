"""Regra de exibição da página de Configurações.

EXCEÇÃO ARQUITETURAL: este service importa `current_app` do Flask
porque a página é fundamentalmente sobre o sistema em si (config,
ambiente, banco). Não há regra de negócio aqui — só coleta e formatação
de informações do próprio runtime. Documentado para não virar moda.
"""
import os
from datetime import datetime
from pathlib import Path

from flask import current_app

from backend import __version__
from backend.security import current_user


def coletar_info_sistema():
    config = current_app.config
    db_path = Path(config["DATABASE_PATH"])

    session_minutos = int(
        config["PERMANENT_SESSION_LIFETIME"].total_seconds() // 60
    )

    info_banco = _info_banco(db_path)

    return {
        # --- Conta ---
        "usuario": current_user(),
        # --- Aplicação ---
        "versao": __version__,
        "ambiente": _ambiente_legivel(),
        "debug": bool(config.get("DEBUG")),
        "session_minutos": session_minutos,
        "cookie_secure": bool(config.get("SESSION_COOKIE_SECURE")),
        # --- Banco ---
        "db_local": str(db_path.relative_to(db_path.parent.parent)),
        "db_existe": info_banco["existe"],
        "db_tamanho_kb": info_banco["tamanho_kb"],
        "db_modificado": info_banco["modificado"],
    }


def _ambiente_legivel():
    env = (os.environ.get("FLASK_ENV") or "development").lower()
    return "Produção" if env == "production" else "Desenvolvimento"


def _info_banco(db_path: Path) -> dict:
    if not db_path.exists():
        return {"existe": False, "tamanho_kb": 0, "modificado": None}

    stat = db_path.stat()
    return {
        "existe": True,
        "tamanho_kb": round(stat.st_size / 1024, 1),
        "modificado": datetime.fromtimestamp(stat.st_mtime).strftime(
            "%d/%m/%Y %H:%M"
        ),
    }

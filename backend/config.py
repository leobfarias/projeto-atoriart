"""Configurações da aplicação.

Lê variáveis do `.env` na inicialização e expõe classes por ambiente.
Nenhum segredo fica no código — tudo vem do ambiente.
"""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


class BaseConfig:
    # --- Segurança ---
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # --- Admin ---
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")

    # --- Sessão ---
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool(os.environ.get("SESSION_COOKIE_SECURE"), False)
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=_int(os.environ.get("SESSION_LIFETIME_MINUTES"), 60)
    )

    # --- Caminhos ---
    # O banco SQLite e tudo da camada de dados vivem em database/.
    DATABASE_DIR = BASE_DIR / "database"
    DATABASE_PATH = DATABASE_DIR / "atoriart.sqlite3"

    # Pasta onde as fotos de produtos são armazenadas (servida como static).
    UPLOAD_FOLDER = BASE_DIR / "frontend" / "static" / "uploads"


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


def get_config() -> type[BaseConfig]:
    env = (os.environ.get("FLASK_ENV") or "development").lower()
    if env == "production":
        return ProductionConfig
    return DevelopmentConfig

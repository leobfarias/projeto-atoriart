"""Regra de exibição e ações da página de Configurações.

EXCEÇÃO ARQUITETURAL: este service importa `current_app` do Flask
porque a página é fundamentalmente sobre o sistema em si (config,
ambiente, banco). Documentado para não virar moda.

Funções:
    coletar_info_sistema()            -> dict (info pra render)
    validar_troca_senha(form_data,
                        senha_atual_correta_check) -> (erros, valores)
    trocar_senha(username, form_data) -> (erros, None)

Política de senha: mínimo 8 caracteres, diferente da senha atual,
confirmação digitada igual à nova e checkbox de confirmação marcado.
"""
import os
from datetime import datetime
from pathlib import Path

from flask import current_app

from backend import __version__
from backend.security import current_user, trocar_senha as _aplicar_troca_senha
from backend.repositories import credencial_repository

SENHA_MINIMA = 8


def coletar_info_sistema():
    config = current_app.config
    db_path = Path(config["DATABASE_PATH"])

    session_minutos = int(
        config["PERMANENT_SESSION_LIFETIME"].total_seconds() // 60
    )

    return {
        # --- Conta ---
        "usuario": current_user(),
        "senha_atualizada_em": _formatar_data_credencial(
            config.get("ADMIN_USERNAME", "admin")
        ),
        # --- Aplicação ---
        "versao": __version__,
        "ambiente": _ambiente_legivel(),
        "debug": bool(config.get("DEBUG")),
        "session_minutos": session_minutos,
        "cookie_secure": bool(config.get("SESSION_COOKIE_SECURE")),
        # --- Banco ---
        "db_ativo": db_path.exists(),
        "db_tamanho_kb": _tamanho_banco_kb(db_path),
        "db_modificado": _modificado_em(db_path),
    }


# ---------- Validação e troca de senha ----------

def validar_troca_senha(form_data):
    """Lê o request.form e devolve (erros, valores). Não verifica a
    senha atual contra o banco — isso é feito em `trocar_senha`."""
    erros = {}

    senha_atual = form_data.get("senha_atual") or ""
    if not senha_atual:
        erros["senha_atual"] = "Informe sua senha atual."

    senha_nova = form_data.get("senha_nova") or ""
    if len(senha_nova) < SENHA_MINIMA:
        erros["senha_nova"] = f"Nova senha precisa ter pelo menos {SENHA_MINIMA} caracteres."

    senha_nova_confirmacao = form_data.get("senha_nova_confirmacao") or ""
    if senha_nova_confirmacao != senha_nova:
        erros["senha_nova_confirmacao"] = "A confirmação não bate com a nova senha."

    if senha_nova and senha_atual and senha_nova == senha_atual:
        erros["senha_nova"] = "A nova senha precisa ser diferente da atual."

    confirmou = (form_data.get("confirma_troca") or "").strip().lower() in {"1", "on", "true"}
    if not confirmou:
        erros["confirma_troca"] = "Marque a caixa de confirmação para prosseguir."

    valores = {
        "senha_atual": senha_atual,
        "senha_nova": senha_nova,
    }
    return erros, valores


def trocar_senha(username, form_data):
    """Valida o form e, se OK, troca a senha no banco. Devolve (erros, None).

    Erros de campo (formato/preenchimento) vêm de `validar_troca_senha`.
    O erro "senha atual incorreta" volta no campo `senha_atual` porque é
    a única que esse fato afeta.
    """
    erros, valores = validar_troca_senha(form_data)
    if erros:
        return erros, None

    erro_aplicar = _aplicar_troca_senha(
        username, valores["senha_atual"], valores["senha_nova"]
    )
    if erro_aplicar:
        return {"senha_atual": erro_aplicar}, None
    return {}, None


# ---------- Helpers de exibição ----------

def _ambiente_legivel():
    env = (os.environ.get("FLASK_ENV") or "development").lower()
    return "Produção" if env == "production" else "Desenvolvimento"


def _tamanho_banco_kb(db_path: Path) -> float:
    if not db_path.exists():
        return 0.0
    return round(db_path.stat().st_size / 1024, 1)


def _modificado_em(db_path: Path) -> str | None:
    if not db_path.exists():
        return None
    return datetime.fromtimestamp(db_path.stat().st_mtime).strftime(
        "%d/%m/%Y %H:%M"
    )


def _formatar_data_credencial(username: str) -> str | None:
    """Devolve a última atualização de senha em formato amigável."""
    try:
        from database.db import get_db
        db = get_db()
        r = db.execute(
            "SELECT atualizado_em FROM admin_credencial WHERE username = ?",
            (username,),
        ).fetchone()
        iso = r["atualizado_em"] if r is not None else None
    except Exception:
        return None
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return None

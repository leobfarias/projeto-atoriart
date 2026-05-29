"""Autenticação e proteção CSRF.

Centraliza:
- decorator `login_required`
- verificação de credenciais (usuário + hash de senha do admin)
- emissão e validação de tokens CSRF por sessão
- troca de senha (verifica a atual antes de gravar a nova)

A credencial do admin vive na tabela `admin_credencial` desde o ADR-014
(antes ficava só no `.env`). O `.env` continua sendo o ponto inicial
de seed, mas a interface de troca de senha grava o novo hash no banco.
"""
from __future__ import annotations

import hmac
import secrets
from functools import wraps
from typing import Callable

from flask import abort, current_app, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from backend.repositories import credencial_repository

SESSION_USER_KEY = "auth_user"
SESSION_CSRF_KEY = "_csrf_token"


# ----------------- Autenticação -----------------

def login_required(view: Callable) -> Callable:
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def is_authenticated() -> bool:
    return bool(session.get(SESSION_USER_KEY))


def current_user() -> str | None:
    return session.get(SESSION_USER_KEY)


def authenticate(username: str, password: str) -> bool:
    """Valida credenciais do admin com comparação em tempo constante.

    Lê o hash da tabela `admin_credencial` (populada a partir do .env no
    primeiro boot). Compara o username em tempo constante e verifica o
    hash via `werkzeug.security`.
    """
    expected_user = current_app.config.get("ADMIN_USERNAME", "")
    expected_hash = credencial_repository.get_password_hash(expected_user)

    if not expected_hash:
        # Sem hash gravado: nega login para evitar bypass em deploys mal feitos.
        return False

    user_ok = hmac.compare_digest(
        (username or "").encode("utf-8"),
        expected_user.encode("utf-8"),
    )
    pass_ok = check_password_hash(expected_hash, password or "")
    return user_ok and pass_ok


def trocar_senha(username: str, senha_atual: str, senha_nova: str) -> str | None:
    """Troca a senha do admin se a senha atual conferir.

    Retorna None se OK; mensagem de erro amigável senão. Quem chama é
    responsável por já ter validado o formato da nova senha — aqui o foco
    é só a verificação de identidade + escrita.
    """
    hash_atual = credencial_repository.get_password_hash(username)
    if not hash_atual or not check_password_hash(hash_atual, senha_atual or ""):
        return "Senha atual incorreta."
    novo_hash = generate_password_hash(senha_nova)
    credencial_repository.atualizar_senha(username, novo_hash)
    return None


def login_session(username: str) -> None:
    """Inicia sessão limpando estado anterior e rotacionando CSRF."""
    session.clear()
    session[SESSION_USER_KEY] = username
    session.permanent = True
    rotate_csrf_token()


def logout_session() -> None:
    session.clear()


# ----------------- CSRF -----------------

def generate_csrf_token() -> str:
    """Retorna o token CSRF atual da sessão (cria um se não existir)."""
    token = session.get(SESSION_CSRF_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[SESSION_CSRF_KEY] = token
    return token


def rotate_csrf_token() -> str:
    session[SESSION_CSRF_KEY] = secrets.token_urlsafe(32)
    return session[SESSION_CSRF_KEY]


def validate_csrf_token(submitted: str | None) -> bool:
    expected = session.get(SESSION_CSRF_KEY, "")
    if not expected or not submitted:
        return False
    return hmac.compare_digest(expected, submitted)


def require_csrf() -> None:
    """Aborta com 400 se o token CSRF do POST for inválido."""
    token = request.form.get("csrf_token")
    if not validate_csrf_token(token):
        abort(400, description="Token CSRF inválido.")

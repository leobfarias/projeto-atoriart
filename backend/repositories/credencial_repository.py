"""Repositório da credencial do administrador (admin único).

Contrato público:
    get_password_hash(username)            -> str | None
        Retorna o hash atual armazenado pra esse username; None se não existe.
    atualizar_senha(username, novo_hash)   -> None
        Substitui o hash da credencial e marca `atualizado_em` agora.

A credencial vive na tabela `admin_credencial`. No primeiro boot, ela é
seeded a partir do `.env` (ver `database/db.py::_apply_migrations` —
ADR-014). Depois disso, a tabela é a fonte de verdade.
"""
from datetime import datetime

from database.db import get_db


def get_password_hash(username):
    db = get_db()
    r = db.execute(
        "SELECT password_hash FROM admin_credencial WHERE username = ?",
        (username,),
    ).fetchone()
    return r["password_hash"] if r is not None else None


def atualizar_senha(username, novo_hash):
    db = get_db()
    db.execute(
        "UPDATE admin_credencial "
        "SET password_hash = ?, atualizado_em = ? "
        "WHERE username = ?",
        (novo_hash, datetime.now().isoformat(timespec="seconds"), username),
    )
    db.commit()

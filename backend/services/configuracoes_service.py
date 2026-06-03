"""Regra de exibição e ações da página de Configurações.

EXCEÇÃO ARQUITETURAL: este service importa `current_app` do Flask
porque a página é fundamentalmente sobre o sistema em si (config,
ambiente, banco). Documentado para não virar moda.

Funções:
    coletar_info_sistema()            -> dict (info pra render)
    validar_troca_senha(form_data)    -> (erros, valores)
    trocar_senha(username, form_data) -> (erros, None)
    gerar_backup()                    -> (buffer_zip, nome_arquivo)
    restaurar_backup(arquivo)         -> (erro_msg | None)

Política de senha: mínimo 8 caracteres, diferente da senha atual,
confirmação digitada igual à nova e checkbox de confirmação marcado.
"""
import io
import os
import shutil
import sqlite3
import tempfile
import zipfile
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
        "session_minutos": session_minutos,
        "cookie_secure": bool(config.get("SESSION_COOKIE_SECURE")),
        "hospedagem": _hospedagem(),
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


# ---------- Backup e restauração ----------

TABELAS_OBRIGATORIAS = {
    "peca", "material", "peca_material",
    "producao", "venda", "despesa",
    "compra_material", "admin_credencial",
}
TAMANHO_MAXIMO_BYTES = 20 * 1024 * 1024  # 20 MB


def gerar_backup():
    """Compacta o banco em memória e devolve (buffer_zip, nome_arquivo).

    O chamador (blueprint) passa o buffer direto para `send_file`.
    """
    db_path = Path(current_app.config["DATABASE_PATH"])
    nome_zip = f"atoriart_backup_{datetime.today().strftime('%Y-%m-%d')}.zip"

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(db_path, "atoriart.sqlite3")
    buffer.seek(0)
    return buffer, nome_zip


def restaurar_backup(arquivo):
    """Valida e aplica o backup enviado pelo usuário.

    `arquivo` é o objeto `FileStorage` do Flask (request.files).
    Devolve uma mensagem de erro (str) ou None em caso de sucesso.

    Aceita .sqlite3 direto ou .zip contendo um .sqlite3.
    Valida as tabelas obrigatórias antes de substituir o banco atual.
    """
    if not arquivo or not arquivo.filename:
        return "Nenhum arquivo foi enviado."

    nome = arquivo.filename.lower()
    if not (nome.endswith(".sqlite3") or nome.endswith(".zip")):
        return "Formato inválido. Envie um arquivo .sqlite3 ou .zip."

    conteudo = arquivo.read()
    if len(conteudo) > TAMANHO_MAXIMO_BYTES:
        return "Arquivo muito grande (máximo 20 MB)."

    # Extrai o .sqlite3 (de dentro do zip se necessário).
    try:
        sqlite_bytes = _extrair_sqlite(conteudo, nome)
    except Exception as exc:
        return f"Não foi possível ler o arquivo: {exc}"

    if sqlite_bytes is None:
        return "Nenhum arquivo .sqlite3 encontrado dentro do ZIP."

    # Grava em arquivo temporário para validar antes de substituir.
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp:
        tmp.write(sqlite_bytes)
        tmp_path = tmp.name

    try:
        erro_validacao = _validar_sqlite(tmp_path)
        if erro_validacao:
            return erro_validacao

        db_path = Path(current_app.config["DATABASE_PATH"])
        shutil.copy2(tmp_path, db_path)
    finally:
        os.unlink(tmp_path)

    return None


def _extrair_sqlite(conteudo: bytes, nome: str) -> bytes | None:
    """Devolve os bytes do .sqlite3, extraindo do ZIP se necessário."""
    if nome.endswith(".sqlite3"):
        return conteudo

    with zipfile.ZipFile(io.BytesIO(conteudo)) as zf:
        sqlite_names = [n for n in zf.namelist() if n.lower().endswith(".sqlite3")]
        if not sqlite_names:
            return None
        return zf.read(sqlite_names[0])


def _validar_sqlite(path: str) -> str | None:
    """Abre o arquivo e verifica se é um SQLite válido com as tabelas esperadas.

    Devolve mensagem de erro ou None se OK.
    """
    try:
        conn = sqlite3.connect(path)
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        conn.close()
    except sqlite3.DatabaseError:
        return "O arquivo não é um banco de dados SQLite válido."

    tabelas_presentes = {r[0] for r in rows}
    faltando = TABELAS_OBRIGATORIAS - tabelas_presentes
    if faltando:
        return (
            f"Backup incompatível com esta versão do sistema. "
            f"Tabelas ausentes: {', '.join(sorted(faltando))}."
        )
    return None


# ---------- Helpers de exibição ----------

def _hospedagem():
    """Detecta o provedor de hospedagem por env vars que ele mesmo seta.

    Devolve uma string amigável ou None (= rodando localmente).
    """
    if os.environ.get("RENDER"):
        return "Render"
    if os.environ.get("HEROKU_APP_NAME") or os.environ.get("DYNO"):
        return "Heroku"
    if os.environ.get("FLY_APP_NAME"):
        return "Fly.io"
    return None


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

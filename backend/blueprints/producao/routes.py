"""Rotas da página de Produção.

Abriga dois conjuntos de rotas:

- **Produção (lançamentos):** `/producao/`, `/producao/nova`,
  `/producao/<id>/apagar` — mexem em `producao_service`.
- **Peças (cadastro/edição):** `/producao/pecas/nova`,
  `/producao/pecas/<id>/editar`, `/producao/pecas/<id>/apagar` —
  mexem em `peca_service`. A peça "nasce" aqui porque é
  conceitualmente a tela de produção/estoque.
"""
import os
import uuid
from datetime import date, datetime

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, url_for)

from backend.repositories import material_repository, peca_repository
from backend.security import login_required, require_csrf
from backend.services import peca_service, producao_service

_EXTENSOES_FOTO = {"jpg", "jpeg", "png", "gif", "webp"}


def _salvar_foto(arquivo):
    """Valida extensão, gera nome único e salva o arquivo. Retorna o nome ou None."""
    if not arquivo or not arquivo.filename:
        return None
    ext = arquivo.filename.rsplit(".", 1)[-1].lower() if "." in arquivo.filename else ""
    if ext not in _EXTENSOES_FOTO:
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_final = f"{timestamp}_{uuid.uuid4().hex[:8]}.{ext}"
    pasta = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(pasta, exist_ok=True)
    arquivo.save(os.path.join(pasta, nome_final))
    return nome_final


def _deletar_foto(nome_arquivo):
    """Remove o arquivo de foto do disco, ignorando se não existir."""
    if not nome_arquivo:
        return
    try:
        os.remove(os.path.join(current_app.config["UPLOAD_FOLDER"], nome_arquivo))
    except FileNotFoundError:
        pass

producao_bp = Blueprint("producao", __name__, url_prefix="/producao")


# ---------- Listagem (estoque + histórico) ----------

@producao_bp.route("/")
@login_required
def index():
    dados = producao_service.dados_producao()
    return render_template("producao/index.html", **dados)


# ---------- Produção: criar ----------

@producao_bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    pecas = peca_repository.list_pecas()

    if request.method == "POST":
        require_csrf()
        erros, _ = producao_service.criar(request.form)
        if erros:
            return render_template(
                "producao/form.html",
                erros=erros, valores=request.form,
                pecas=pecas, hoje=date.today().isoformat(),
            )
        flash("Produção registrada.", "success")
        return redirect(url_for("producao.index"))

    return render_template(
        "producao/form.html",
        erros={}, valores={"data": date.today().isoformat()},
        pecas=pecas, hoje=date.today().isoformat(),
    )


# ---------- Produção: apagar ----------

@producao_bp.route("/<int:producao_id>/apagar", methods=["POST"])
@login_required
def apagar(producao_id):
    require_csrf()
    erro = producao_service.apagar(producao_id)
    if erro:
        flash(erro, "error")
    else:
        flash("Produção apagada (estoque ajustado).", "success")
    return redirect(url_for("producao.index"))


# ---------- Peça: criar ----------

@producao_bp.route("/pecas/nova", methods=["GET", "POST"])
@login_required
def peca_nova():
    materiais_disponiveis = material_repository.list_materiais()

    if request.method == "POST":
        require_csrf()
        foto_nova = _salvar_foto(request.files.get("foto"))
        erros, _ = peca_service.criar(request.form, foto=foto_nova)
        if erros:
            _deletar_foto(foto_nova)
            return render_template(
                "producao/peca_form.html",
                modo="novo",
                erros=erros,
                valores=_valores_do_form(request.form, materiais_disponiveis),
                materiais_disponiveis=materiais_disponiveis,
                foto_atual=None,
            )
        flash("Peça cadastrada.", "success")
        return redirect(url_for("producao.index"))

    return render_template(
        "producao/peca_form.html",
        modo="novo",
        erros={},
        valores={"materiais": {}},
        materiais_disponiveis=materiais_disponiveis,
        foto_atual=None,
    )


# ---------- Peça: editar ----------

@producao_bp.route("/pecas/<int:peca_id>/editar", methods=["GET", "POST"])
@login_required
def peca_editar(peca_id):
    peca = peca_repository.get_peca(peca_id)
    if peca is None:
        abort(404)
    materiais_disponiveis = material_repository.list_materiais()

    if request.method == "POST":
        require_csrf()
        foto_nova = _salvar_foto(request.files.get("foto"))
        # Se nenhuma foto nova enviada, mantém a existente
        foto_a_salvar = foto_nova if foto_nova else peca.foto
        erros, _ = peca_service.atualizar(peca_id, request.form, foto=foto_a_salvar)
        if erros:
            _deletar_foto(foto_nova)
            return render_template(
                "producao/peca_form.html",
                modo="editar", peca_id=peca_id,
                erros=erros,
                valores=_valores_do_form(request.form, materiais_disponiveis),
                materiais_disponiveis=materiais_disponiveis,
                foto_atual=peca.foto,
            )
        # Substitui foto antiga somente após salvar com sucesso
        if foto_nova and peca.foto:
            _deletar_foto(peca.foto)
        flash("Peça atualizada.", "success")
        return redirect(url_for("producao.index"))

    valores = {
        "nome": peca.nome,
        "preco_venda": peca.preco_venda,
        "quantidade_estoque": peca.quantidade_estoque,
        "materiais": {
            im.material.id: _formatar_quantidade(im.quantidade)
            for im in peca.materiais
        },
    }
    return render_template(
        "producao/peca_form.html",
        modo="editar", peca_id=peca_id,
        erros={}, valores=valores,
        materiais_disponiveis=materiais_disponiveis,
        foto_atual=peca.foto,
    )


# ---------- Peça: apagar ----------

@producao_bp.route("/pecas/<int:peca_id>/apagar", methods=["POST"])
@login_required
def peca_apagar(peca_id):
    require_csrf()
    erro = peca_service.apagar(peca_id)
    if erro:
        flash(erro, "error")
    else:
        flash("Peça removida.", "success")
    return redirect(url_for("producao.index"))


# ---------- Helpers ----------

def _formatar_quantidade(q):
    return f"{q:g}"


def _valores_do_form(form, materiais_disponiveis):
    materiais = {}
    for m in materiais_disponiveis:
        raw = (form.get(f"material_{m.id}") or "").strip()
        if raw:
            materiais[m.id] = raw
    return {
        "nome": form.get("nome", ""),
        "preco_venda": form.get("preco_venda", ""),
        "quantidade_estoque": form.get("quantidade_estoque", ""),
        "materiais": materiais,
    }

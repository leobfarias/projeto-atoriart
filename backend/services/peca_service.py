"""Regra de negócio da entidade Peça (cadastro/edição/remoção).

A peça nasce aqui (em Produção), recebe quantidade através de lançamentos
de produção e — quando seu estoque fica > 0 — aparece automaticamente no
Catálogo (vitrine).

O custo de produção NÃO é digitado: é derivado dos materiais da peça
(view `vw_peca_custo`). O usuário informa apenas o `preco_venda` — o
preço sugerido de venda. O lucro sai da diferença (ver model `Peca`).

Funções:
    validar_form(form_data, materiais_disponiveis) -> (erros, valores)
    criar(form_data)                               -> (erros, peca_id)
    atualizar(peca_id, form_data)                  -> (erros, None)
    apagar(peca_id)                                -> (erro_msg | None)
"""
from backend.repositories import material_repository, peca_repository


# ---------- Validação ----------

def validar_form(form_data, materiais_disponiveis):
    """Valida o form de peça.

    `materiais_disponiveis` é a lista atual de materiais cadastrados,
    usada pra ler o campo `material_<id>` de cada um.
    """
    erros = {}

    nome = (form_data.get("nome") or "").strip()
    if not nome:
        erros["nome"] = "Informe o nome da peça."
    elif len(nome) > 80:
        erros["nome"] = "Nome muito longo (máx 80 caracteres)."

    preco_venda = _numero(form_data.get("preco_venda"))
    if preco_venda is None or preco_venda <= 0:
        erros["preco_venda"] = "Preço de venda deve ser maior que zero."

    estoque = _inteiro(form_data.get("quantidade_estoque"))
    if estoque is None or estoque < 0:
        erros["quantidade_estoque"] = "Estoque deve ser ≥ 0."

    materiais_selecionados = {}
    for m in materiais_disponiveis:
        raw = (form_data.get(f"material_{m.id}") or "").strip()
        if not raw:
            continue
        qtd = _numero(raw)
        if qtd is None or qtd < 0:
            erros[f"material_{m.id}"] = "Quantidade inválida."
        elif qtd > 0:
            materiais_selecionados[m.id] = qtd

    valores = {
        "nome": nome,
        "preco_venda": preco_venda or 0.0,
        "quantidade_estoque": estoque or 0,
        "materiais": materiais_selecionados,
    }
    return erros, valores


# ---------- Ações ----------

def criar(form_data, foto=None):
    materiais_disponiveis = material_repository.list_materiais()
    erros, v = validar_form(form_data, materiais_disponiveis)
    if erros:
        return erros, None
    novo_id = peca_repository.criar(**v, foto=foto)
    return {}, novo_id


def atualizar(peca_id, form_data, foto=None):
    materiais_disponiveis = material_repository.list_materiais()
    erros, v = validar_form(form_data, materiais_disponiveis)
    if erros:
        return erros, None
    peca_repository.atualizar(peca_id, **v, foto=foto)
    return {}, None


def apagar(peca_id):
    """Bloqueia se a peça já tem vendas (registro fiscal)."""
    if peca_repository.tem_vendas(peca_id):
        return (
            "Esta peça já tem vendas registradas. Não é possível apagar."
        )
    peca_repository.apagar(peca_id)
    return None


# ---------- Helpers ----------

def _numero(raw):
    if raw is None:
        return None
    raw = str(raw).strip().replace(",", ".")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _inteiro(raw):
    if raw is None:
        return None
    raw = str(raw).strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None

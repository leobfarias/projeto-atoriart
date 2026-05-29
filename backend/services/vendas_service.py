"""Regra de negócio das Vendas.

Funções:
    dados_vendas()                    -> dict (listagem + KPIs 30d)
    formas_pagamento_padrao()         -> list[str] (sugestões pro <select>)
    validar_form(form_data, pecas)    -> (erros, valores)
    criar(form_data)                  -> (erros, venda_id)
    apagar(venda_id)                  -> (erro_msg | None)

Regras de estoque:
- Criar venda SUBTRAI `quantidade` de `peca.quantidade_estoque`.
  Bloqueia se a peça não tem estoque suficiente.
- Apagar venda SOMA `quantidade` de volta em `peca.quantidade_estoque`.
"""
from datetime import date, timedelta

from backend.repositories import peca_repository, venda_repository
from backend.services.form_helpers import data_iso, inteiro, numero

JANELA_DIAS = 30

FORMAS_PAGAMENTO = ["PIX", "Dinheiro", "Cartão crédito", "Cartão débito"]


# ---------- Listagem (já existia) ----------

def dados_vendas():
    desde = (date.today() - timedelta(days=JANELA_DIAS)).isoformat()
    vendas = venda_repository.list_vendas(desde=desde)

    faturamento = sum(v.valor_total for v in vendas)
    lucro_bruto = sum(v.lucro_bruto for v in vendas)
    total = len(vendas)

    return {
        "vendas": vendas,
        "janela_dias": JANELA_DIAS,
        "total_vendas": total,
        "faturamento": faturamento,
        "lucro_bruto": lucro_bruto,
        "ticket_medio": faturamento / total if total else 0.0,
    }


def formas_pagamento_padrao():
    return list(FORMAS_PAGAMENTO)


# ---------- Validação ----------

def validar_form(form_data, pecas_disponiveis):
    erros = {}

    peca_id = inteiro(form_data.get("peca_id"))
    pecas_map = {p.id: p for p in pecas_disponiveis}
    peca = pecas_map.get(peca_id) if peca_id else None
    if peca is None:
        erros["peca_id"] = "Escolha uma peça válida."

    quantidade = inteiro(form_data.get("quantidade"))
    if quantidade is None or quantidade <= 0:
        erros["quantidade"] = "Quantidade deve ser maior que zero."
    elif peca is not None and quantidade > peca.quantidade_estoque:
        erros["quantidade"] = (
            f"Estoque insuficiente. \"{peca.nome}\" tem só "
            f"{peca.quantidade_estoque} em estoque."
        )

    valor_total = numero(form_data.get("valor_total"))
    if valor_total is None or valor_total < 0:
        erros["valor_total"] = "Valor deve ser ≥ 0."

    data_str = (form_data.get("data") or "").strip()
    data_valida = data_iso(data_str)
    if data_valida is None:
        erros["data"] = "Informe uma data válida."

    forma_pagamento = (form_data.get("forma_pagamento") or "").strip() or None
    if forma_pagamento and forma_pagamento not in FORMAS_PAGAMENTO:
        erros["forma_pagamento"] = "Forma de pagamento inválida."

    valores = {
        "peca_id": peca_id,
        "quantidade": quantidade or 0,
        "valor_total": valor_total or 0.0,
        "data": data_valida,
        "forma_pagamento": forma_pagamento,
    }
    return erros, valores


# ---------- Ações ----------

def criar(form_data):
    pecas = peca_repository.list_pecas()
    erros, v = validar_form(form_data, pecas)
    if erros:
        return erros, None
    novo_id = venda_repository.criar(**v)
    return {}, novo_id


def apagar(venda_id):
    venda = venda_repository.get_venda(venda_id)
    if venda is None:
        return "Venda não encontrada."
    venda_repository.apagar(venda_id, venda.peca_id, venda.quantidade)
    return None



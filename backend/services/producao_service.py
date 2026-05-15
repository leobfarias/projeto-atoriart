"""Regra de negócio da Produção.

Funções:
    dados_producao()                  -> dict (listagem + KPIs dos 30d)
    validar_form(form_data, pecas)    -> (erros, valores)
    criar(form_data)                  -> (erros, producao_id)
    apagar(producao_id)               -> (erro_msg | None)

Regras de estoque (centrais):
- Criar produção SOMA `quantidade` em `peca.quantidade_estoque`.
- Apagar produção SUBTRAI `quantidade` de `peca.quantidade_estoque`.
  Se isso levaria o estoque a ficar NEGATIVO (porque algumas peças
  já foram vendidas), o apagar é bloqueado com erro amigável.
"""
from collections import Counter
from datetime import date, timedelta

from backend.repositories import peca_repository, producao_repository

JANELA_DIAS = 30


# ---------- Listagem ----------

def dados_producao():
    """ViewModel da página /producao/.

    A página funciona como controle de estoque: mostra primeiro o
    estoque atual (peças com quantidade > 0 e custo investido) e
    depois o histórico recente de produções dos últimos `JANELA_DIAS`.
    """
    pecas_estoque = peca_repository.list_pecas(apenas_em_estoque=True)
    todas_pecas = peca_repository.list_pecas()
    desde = (date.today() - timedelta(days=JANELA_DIAS)).isoformat()
    producoes = producao_repository.list_producoes(desde=desde)
    return {
        # Estoque atual
        "pecas_estoque": pecas_estoque,
        "modelos_em_estoque": len(pecas_estoque),
        "pecas_em_estoque": sum(p.quantidade_estoque for p in pecas_estoque),
        "custo_investido": sum(
            p.custo_producao * p.quantidade_estoque for p in pecas_estoque
        ),
        # Para o select do form de produção
        "pecas_cadastradas": todas_pecas,
        # Histórico recente
        "producoes": producoes,
        "janela_dias": JANELA_DIAS,
        "total_producoes": len(producoes),
        "pecas_produzidas_janela": sum(p.quantidade for p in producoes),
        "peca_top": _peca_mais_produzida(producoes),
        "custo_total_janela": sum(p.custo_subtotal for p in producoes),
    }


def _peca_mais_produzida(producoes):
    if not producoes:
        return None
    c = Counter()
    for p in producoes:
        c[p.peca_nome] += p.quantidade
    return c.most_common(1)[0][0]


# ---------- Validação ----------

def validar_form(form_data, pecas_disponiveis):
    erros = {}

    peca_id = _inteiro(form_data.get("peca_id"))
    pecas_ids = {p.id for p in pecas_disponiveis}
    if peca_id is None or peca_id not in pecas_ids:
        erros["peca_id"] = "Escolha uma peça válida."

    quantidade = _inteiro(form_data.get("quantidade"))
    if quantidade is None or quantidade <= 0:
        erros["quantidade"] = "Quantidade deve ser maior que zero."

    data_str = (form_data.get("data") or "").strip()
    data_valida = _data_iso(data_str)
    if data_valida is None:
        erros["data"] = "Informe uma data válida."

    observacao = (form_data.get("observacao") or "").strip() or None

    valores = {
        "peca_id": peca_id,
        "quantidade": quantidade or 0,
        "data": data_valida,
        "observacao": observacao,
    }
    return erros, valores


# ---------- Ações ----------

def criar(form_data):
    pecas = peca_repository.list_pecas()
    erros, v = validar_form(form_data, pecas)
    if erros:
        return erros, None
    novo_id = producao_repository.criar(**v)
    return {}, novo_id


def apagar(producao_id):
    producao = producao_repository.get_producao(producao_id)
    if producao is None:
        return "Produção não encontrada."

    peca = peca_repository.get_peca(producao.peca_id)
    if peca is None:
        return "Peça associada não existe mais."

    # Se subtrair levaria o estoque a ficar negativo, bloqueia
    if peca.quantidade_estoque < producao.quantidade:
        return (
            f"Não é possível apagar: a peça \"{peca.nome}\" tem só "
            f"{peca.quantidade_estoque} em estoque, mas esta produção "
            f"adicionou {producao.quantidade}. Algumas já foram vendidas."
        )

    producao_repository.apagar(producao_id, producao.peca_id, producao.quantidade)
    return None


# ---------- Helpers ----------

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


def _data_iso(raw):
    """Aceita 'YYYY-MM-DD'. Retorna a própria string se válida, senão None."""
    if not raw:
        return None
    try:
        date.fromisoformat(raw)
        return raw
    except ValueError:
        return None

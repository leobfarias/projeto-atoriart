"""Regra de negócio da Produção.

Funções:
    dados_producao()                  -> dict (listagem + KPIs dos 30d)
    validar_form(form_data, pecas)    -> (erros, valores)
    criar(form_data)                  -> (erros, producao_id)
    apagar(producao_id)               -> (erro_msg | None)

Regras de estoque (centrais — ADR-007 estendido pelo ADR-012):
- **Criar produção** SOMA `quantidade` em `peca.quantidade_estoque` E
  SUBTRAI dos materiais da receita (qty × material_qty). Antes de
  gravar, este service confere se cada material tem estoque
  suficiente — bloqueia se não tiver.
- **Apagar produção** SUBTRAI `quantidade` de `peca.quantidade_estoque`.
  Matéria-prima **não retorna ao estoque** — já foi consumida
  fisicamente; o efeito é assimétrico em relação a criar, de propósito.
  Bloqueada se levaria o estoque da peça a ficar negativo (porque
  algumas peças já foram vendidas).
"""
from collections import Counter
from datetime import date, timedelta

from backend.repositories import peca_repository, producao_repository
from backend.services.form_helpers import data_iso, inteiro

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
        # Histórico (ADR-013): soma do snapshot custo_unitario × quantidade de
        # TODAS as produções já registradas. Não cai quando vende.
        "custo_investido": producao_repository.custo_total_investido(),
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

    peca_id = inteiro(form_data.get("peca_id"))
    pecas_ids = {p.id for p in pecas_disponiveis}
    if peca_id is None or peca_id not in pecas_ids:
        erros["peca_id"] = "Escolha uma peça válida."

    quantidade = inteiro(form_data.get("quantidade"))
    if quantidade is None or quantidade <= 0:
        erros["quantidade"] = "Quantidade deve ser maior que zero."

    data_str = (form_data.get("data") or "").strip()
    data_valida = data_iso(data_str)
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

    # Confere se a matéria-prima da peça aguenta produzir essa quantidade.
    peca = peca_repository.get_peca(v["peca_id"])
    erro_materiais = _verificar_estoque_materiais(peca, v["quantidade"])
    if erro_materiais:
        return {"quantidade": erro_materiais}, None

    novo_id = producao_repository.criar(**v)
    return {}, novo_id


def _verificar_estoque_materiais(peca, quantidade_producao):
    """Para cada material da receita da peça, vê se há estoque para produzir.

    Retorna None se OK; mensagem amigável listando os faltantes senão.
    """
    if peca is None:
        return None
    faltando = []
    for im in peca.materiais:
        necessario = im.quantidade * quantidade_producao
        if im.material.quantidade_estoque < necessario:
            faltando.append(
                f"{im.material.nome} "
                f"(precisa {necessario:g} {im.material.unidade}, "
                f"tem {im.material.quantidade_estoque:g})"
            )
    if not faltando:
        return None
    return "Matéria-prima insuficiente: " + "; ".join(faltando) + "."


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



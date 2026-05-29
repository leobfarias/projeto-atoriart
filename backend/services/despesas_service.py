"""Regra de negócio das Despesas.

Funções:
    dados_despesas()               -> dict (listagem + KPIs dos 30d)
    categorias_padrao()            -> list[str] (sugestões pro <select>)
    validar_form(form_data)        -> (erros, valores)
    criar(form_data)               -> (erros, despesa_id)
    apagar(despesa_id)             -> (erro_msg | None)

A despesa é um registro puro: criar/apagar NÃO mexem em estoque (ao
contrário de produção e venda — ver ADR-007). O total de despesas do
período é o que torna a receita líquida (faturamento − despesas) real
no dashboard.
"""
from datetime import date, timedelta

from backend.repositories import despesa_repository
from backend.services.form_helpers import data_iso, numero

JANELA_DIAS = 30

# Categorias de despesa — apenas custos operacionais / fixos do negócio,
# FORA do escopo de produto. A matéria-prima da produção NÃO entra aqui:
# ela tem módulo próprio (/materiais/). O <select> do form oferece estas
# opções e a validação rejeita qualquer valor fora da lista (mesma ideia
# das formas de pagamento em vendas_service).
CATEGORIAS = [
    "Aluguel",
    "Contas e utilidades",
    "Marketing",
    "Transporte e frete",
    "Ferramentas e equipamentos",
    "Embalagem",
    "Taxas e tarifas",
    "Outros",
]


# ---------- Listagem ----------

def dados_despesas():
    """ViewModel da página /despesas/: histórico recente + KPIs dos 30d."""
    desde = (date.today() - timedelta(days=JANELA_DIAS)).isoformat()
    despesas = despesa_repository.list_despesas(desde=desde)

    valor_total = sum(d.valor for d in despesas)
    total = len(despesas)

    return {
        "despesas": despesas,
        "janela_dias": JANELA_DIAS,
        "total_despesas": total,
        "valor_total": valor_total,
        "despesa_media": valor_total / total if total else 0.0,
        "categoria_top": _categoria_mais_gasta(despesas),
    }


def _categoria_mais_gasta(despesas):
    """Categoria com maior valor somado no período (ou None se vazio)."""
    if not despesas:
        return None
    por_categoria = {}
    for d in despesas:
        chave = d.categoria or "Outros"
        por_categoria[chave] = por_categoria.get(chave, 0.0) + d.valor
    return max(por_categoria.items(), key=lambda item: item[1])[0]


def categorias_padrao():
    return list(CATEGORIAS)


# ---------- Validação ----------

def validar_form(form_data):
    """Lê o request.form e devolve (erros, valores_normalizados).

    `erros` é um dict campo→mensagem. Vazio = válido.
    `valores` traz os campos limpos, prontos pro repositório.
    """
    erros = {}

    descricao = (form_data.get("descricao") or "").strip()
    if not descricao:
        erros["descricao"] = "Informe a descrição da despesa."
    elif len(descricao) > 120:
        erros["descricao"] = "Descrição muito longa (máx 120 caracteres)."

    valor = numero(form_data.get("valor"))
    if valor is None or valor <= 0:
        erros["valor"] = "Valor deve ser maior que zero."

    data_str = (form_data.get("data") or "").strip()
    data_valida = data_iso(data_str)
    if data_valida is None:
        erros["data"] = "Informe uma data válida."

    categoria = (form_data.get("categoria") or "").strip() or None
    if categoria and categoria not in CATEGORIAS:
        erros["categoria"] = "Categoria inválida."

    valores = {
        "descricao": descricao,
        "valor": valor or 0.0,
        "data": data_valida,
        "categoria": categoria,
    }
    return erros, valores


# ---------- Ações ----------

def criar(form_data):
    erros, v = validar_form(form_data)
    if erros:
        return erros, None
    novo_id = despesa_repository.criar(**v)
    return {}, novo_id


def apagar(despesa_id):
    """Retorna mensagem de erro se não puder apagar; None se OK."""
    despesa = despesa_repository.get_despesa(despesa_id)
    if despesa is None:
        return "Despesa não encontrada."
    despesa_repository.apagar(despesa_id)
    return None



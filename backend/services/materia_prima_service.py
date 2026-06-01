"""Regra de negócio da Matéria-prima.

Funções:
    dados_materia_prima()              -> dict (listagem + KPIs)
    validar_form(form_data)            -> (erros, valores)
    criar(form_data)                   -> (erros, material_id)
    atualizar(material_id, form_data)  -> (erros, None)
    apagar(material_id)                -> (erro_msg | None)

O usuário cadastra/edita informando o **preço total pago** pelo lote
(`preco_total`) + a quantidade comprada — o valor unitário é calculado
silenciosamente (`preco_total / quantidade_estoque`) e gravado em
`material.valor_unitario`. É esse `valor_unitario` que alimenta a view
`vw_peca_custo` e, portanto, o custo de produção das peças.
"""
from datetime import date, timedelta

from backend.repositories import material_repository
from backend.services.form_helpers import numero

JANELA_DIAS = 30


# ---------- Listagem ----------

def dados_materia_prima():
    materiais = material_repository.list_materiais()
    materiais_alerta = [m for m in materiais if m.em_alerta]
    desde = (date.today() - timedelta(days=JANELA_DIAS)).isoformat()

    return {
        "materiais": materiais,
        "materiais_alerta": materiais_alerta,
        "total_cadastrados": len(materiais),
        "total_ok": len(materiais) - len(materiais_alerta),
        "total_alerta": len(materiais_alerta),
        "valor_investido": material_repository.gasto_periodo(desde),
        "janela_dias": JANELA_DIAS,
    }


# ---------- Validação ----------

def validar_form(form_data):
    """Lê o request.form e devolve (erros, valores_normalizados).

    `erros` é um dict campo→mensagem. Vazio = válido.
    `valores` traz os campos já limpos. Note que o usuário NÃO informa
    `valor_unitario`: ele é derivado de `preco_total / quantidade_estoque`
    e entregue pronto ao repositório.
    """
    erros = {}

    nome = (form_data.get("nome") or "").strip()
    if not nome:
        erros["nome"] = "Informe o nome do material."
    elif len(nome) > 80:
        erros["nome"] = "Nome muito longo (máx 80 caracteres)."

    unidade = (form_data.get("unidade") or "").strip()
    if not unidade:
        erros["unidade"] = "Informe a unidade (m, g, un...)."
    elif len(unidade) > 10:
        erros["unidade"] = "Unidade muito longa (máx 10 caracteres)."

    preco_total = numero(form_data.get("preco_total"))
    if preco_total is None or preco_total <= 0:
        erros["preco_total"] = "Preço total pago deve ser maior que zero."

    # Quantidade > 0 é obrigatória — sem ela não dá pra calcular o
    # valor unitário (divisão por zero).
    quantidade_estoque = numero(form_data.get("quantidade_estoque"))
    if quantidade_estoque is None or quantidade_estoque <= 0:
        erros["quantidade_estoque"] = "Quantidade em estoque deve ser maior que zero."

    estoque_minimo = numero(form_data.get("estoque_minimo"))
    if estoque_minimo is None or estoque_minimo < 0:
        erros["estoque_minimo"] = "Estoque mínimo deve ser ≥ 0."

    # Cálculo silencioso do valor unitário (só faz sentido se ambos válidos).
    if preco_total and quantidade_estoque:
        valor_unitario = preco_total / quantidade_estoque
    else:
        valor_unitario = 0.0

    valores = {
        "nome": nome,
        "unidade": unidade,
        "valor_unitario": valor_unitario,
        "quantidade_estoque": quantidade_estoque or 0.0,
        "estoque_minimo": estoque_minimo or 0.0,
        "preco_total": preco_total or 0.0,
    }
    return erros, valores


# ---------- Ações ----------

def criar(form_data):
    erros, v = validar_form(form_data)
    if erros:
        return erros, None
    novo_id = material_repository.criar(**v)
    return {}, novo_id


def atualizar(material_id, form_data):
    erros, v = validar_form(form_data)
    if erros:
        return erros, None
    campos = {k: v[k] for k in ("nome", "unidade", "valor_unitario",
                                 "quantidade_estoque", "estoque_minimo")}
    material_repository.atualizar(material_id, **campos)
    return {}, None


def apagar(material_id):
    """Retorna mensagem de erro se não puder apagar; None se OK."""
    if material_repository.em_uso(material_id):
        return (
            "Este material está em uso por uma ou mais peças. "
            "Remova ele das peças antes de apagar."
        )
    material_repository.apagar(material_id)
    return None



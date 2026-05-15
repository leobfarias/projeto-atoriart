"""Regra de negócio da Matéria-prima.

Funções:
    dados_materia_prima()              -> dict (listagem + KPIs)
    validar_form(form_data)            -> (erros, valores)
    criar(form_data)                   -> (erros, material_id)
    atualizar(material_id, form_data)  -> (erros, None)
    apagar(material_id)                -> (erro_msg | None)
"""
from backend.repositories import material_repository


# ---------- Listagem (já existia) ----------

def dados_materia_prima():
    materiais = material_repository.list_materiais()
    materiais_alerta = [m for m in materiais if m.em_alerta]

    return {
        "materiais": materiais,
        "materiais_alerta": materiais_alerta,
        "total_cadastrados": len(materiais),
        "total_ok": len(materiais) - len(materiais_alerta),
        "total_alerta": len(materiais_alerta),
        "valor_investido": sum(
            m.quantidade_estoque * m.valor_unitario for m in materiais
        ),
    }


# ---------- Validação ----------

def validar_form(form_data):
    """Lê o request.form e devolve (erros, valores_normalizados).

    `erros` é um dict campo→mensagem. Vazio = válido.
    `valores` é um dict com os campos já limpos (strings .strip(),
    números convertidos), pronto pra ir pro repositório.
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

    valor_unitario = _numero(form_data.get("valor_unitario"))
    if valor_unitario is None or valor_unitario < 0:
        erros["valor_unitario"] = "Valor unitário deve ser ≥ 0."

    quantidade_estoque = _numero(form_data.get("quantidade_estoque"))
    if quantidade_estoque is None or quantidade_estoque < 0:
        erros["quantidade_estoque"] = "Quantidade em estoque deve ser ≥ 0."

    estoque_minimo = _numero(form_data.get("estoque_minimo"))
    if estoque_minimo is None or estoque_minimo < 0:
        erros["estoque_minimo"] = "Estoque mínimo deve ser ≥ 0."

    valores = {
        "nome": nome,
        "unidade": unidade,
        "valor_unitario": valor_unitario or 0.0,
        "quantidade_estoque": quantidade_estoque or 0.0,
        "estoque_minimo": estoque_minimo or 0.0,
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
    material_repository.atualizar(material_id, **v)
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


# ---------- Helpers ----------

def _numero(raw):
    """Converte string em float. Devolve None se inválido ou vazio."""
    if raw is None:
        return None
    raw = str(raw).strip().replace(",", ".")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None

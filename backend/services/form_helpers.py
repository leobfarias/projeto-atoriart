"""Conversores comuns dos formulários.

Reaproveitados por todos os `*_service.py` que implementam `validar_form`.
São puros: recebem string crua do `request.form`, devolvem o valor tipado
ou `None` quando não dá pra converter. Quem chama decide se `None` é erro
de preenchimento (vazio) ou de formato inválido — aqui não diferenciamos
porque a mensagem de erro depende do campo.

- `numero(raw)`   -> float | None   (aceita "12,50" e "12.50")
- `inteiro(raw)`  -> int | None
- `data_iso(raw)` -> str | None     (devolve a própria string se for YYYY-MM-DD)
"""
from datetime import date


def numero(raw):
    """Converte string em float. Aceita vírgula decimal brasileira."""
    if raw is None:
        return None
    raw = str(raw).strip().replace(",", ".")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def inteiro(raw):
    """Converte string em int. Devolve None se vazio ou inválido."""
    if raw is None:
        return None
    raw = str(raw).strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def data_iso(raw):
    """Valida 'YYYY-MM-DD'. Devolve a própria string se OK, senão None."""
    if not raw:
        return None
    try:
        date.fromisoformat(raw)
        return raw
    except ValueError:
        return None

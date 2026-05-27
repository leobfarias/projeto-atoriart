"""Ponto de entrada para desenvolvimento local.

Em produção, use um servidor WSGI (gunicorn, waitress) apontando para
`backend:create_app()`.
"""
from pathlib import Path

from backend.config import get_config
from database import init_db

# Garante o arquivo do banco antes de chamar create_app(). Em uma clonagem
# nova, basta `python run.py` — não precisa rodar init_db manualmente.
# Idempotente: se o arquivo já existir, não toca; se não, cria vazio
# (só a estrutura, sem dados de exemplo). Para popular com seed continue
# rodando `python database/init_db.py --com-exemplos`.
if not Path(get_config().DATABASE_PATH).exists():
    init_db.main(com_exemplos=False)

from backend import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)

"""Ponto de entrada para desenvolvimento local.

Em produção, use um servidor WSGI (gunicorn, waitress) apontando para
`backend:create_app()`.
"""
import os
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

@app.route('/ping')
def ping():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    # Em ambientes cloud (Render, Heroku, Fly...) a variável `PORT` vem
    # setada pelo provedor e o load balancer só alcança o processo se ele
    # escutar em `0.0.0.0`. Localmente, sem `PORT`, segue só no loopback
    # para evitar expor o dev server na rede da máquina.
    port = int(os.environ.get("PORT", "5000"))
    host = "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"
    print(f" * AtoriArt subindo em http://{host}:{port}")
    app.run(host=host, port=port)

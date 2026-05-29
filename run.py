"""Ponto de entrada da aplicação.

Roda local (`python run.py` → http://127.0.0.1:5000) e também é usado
pelo Render como Start Command (host vira `0.0.0.0` automaticamente
quando a variável de ambiente `PORT` está setada).
"""
import os
from pathlib import Path

from backend.config import get_config
from database import init_db

# Cria o arquivo do banco vazio na primeira execução (idempotente — se já
# existir, não toca). Roda antes do `create_app()` porque a migração
# em `database/db.py` espera a estrutura existente.
if not Path(get_config().DATABASE_PATH).exists():
    init_db.main(com_exemplos=False)

from backend import create_app

app = create_app()


# ---- TEMPORÁRIO: anti-suspend do free tier do Render ----
# Endpoint público batido por pinger externo (UptimeRobot, BetterUptime,
# cron-job.org...) a cada ~14 min, mantendo a app desperta.
# REMOVER junto com o monitor externo quando subir para plano pago.
@app.route("/ping")
def ping():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    # Em provedores cloud (Render, Heroku, Fly...) a variável `PORT` vem
    # do ambiente e precisamos escutar em `0.0.0.0` para o load balancer
    # alcançar o processo. Localmente, sem `PORT`, fica em loopback.
    port = int(os.environ.get("PORT", "5000"))
    host = "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"
    print(f" * AtoriArt subindo em http://{host}:{port}")
    app.run(host=host, port=port)

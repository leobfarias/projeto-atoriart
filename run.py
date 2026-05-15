"""Ponto de entrada para desenvolvimento local.

Em produção, use um servidor WSGI (gunicorn, waitress) apontando para
`backend:create_app()`.
"""
from backend import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)

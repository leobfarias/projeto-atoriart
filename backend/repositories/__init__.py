"""Camada de acesso a dados (SQLite).

Cada repositório encapsula consultas SQL de um domínio (vendas, estoque,
produção, etc.). Os serviços consomem repositórios — nunca o contrário.
Os módulos concretos serão adicionados nas próximas fases.
"""

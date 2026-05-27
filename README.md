# AtoriArt

Sistema web de gestão de estoque para artesanato. Aplicação administrativa
(usuário único) construída com **Python + Flask + Jinja + SQLite**.

> **Status:** Em desenvolvimento ativo. Fundação, autenticação de admin e
> todos os módulos do domínio — catálogo, matéria-prima, produção, vendas,
> despesas, relatórios e configurações — já implementados e ligados a
> dados reais do banco.

---

## Sumário
- [Stack](#stack)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Como executar localmente](#como-executar-localmente)
- [Decisões de arquitetura](#decisões-de-arquitetura)
- [Segurança](#segurança)
- [Estado atual](#estado-atual)

---

## Stack
- **Backend:** Python 3.10+ com Flask 3.x
- **Frontend:** HTML + CSS + Jinja2 (sem JavaScript, sem framework de front)
- **Banco:** SQLite (módulo `sqlite3` da stdlib — sem ORM nesta fase)
- **Config:** variáveis de ambiente via `python-dotenv`

---

## Estrutura do projeto

A árvore é dividida em **três pacotes raiz**, cada um com uma
responsabilidade clara: `backend/` (Python/Flask), `frontend/` (Jinja + CSS)
e `database/` (SQLite). Saber onde mexer fica óbvio.

```
Projeto AtoriArt/
├── backend/                         # Tudo que é Python
│   ├── __init__.py                  # create_app() — aponta Flask p/ frontend/
│   ├── config.py                    # Configs por ambiente + .env loader
│   ├── extensions.py                # Placeholder p/ futuras extensões
│   ├── security.py                  # login_required, autenticação, CSRF
│   ├── blueprints/                  # Controllers HTTP (rotas)
│   │   ├── auth/routes.py           # /auth/login, /auth/logout
│   │   ├── catalogo/routes.py       # /catalogo/
│   │   └── dashboard/routes.py      # /painel
│   ├── services/                    # Regras de negócio
│   │   ├── catalogo_service.py
│   │   └── dashboard_service.py
│   ├── repositories/                # Acesso a dados (chama database/db)
│   │   └── peca_repository.py
│   └── models/                      # Entidades de domínio (dataclasses)
│       └── peca.py
│
├── frontend/                        # Tudo que é apresentação
│   ├── templates/                   # Jinja
│   │   ├── base.html
│   │   ├── _sidebar.html
│   │   ├── auth/login.html
│   │   ├── catalogo/index.html
│   │   └── dashboard/index.html
│   └── static/
│       └── css/                     # CSS por contexto
│           ├── base.css
│           ├── login.css
│           ├── sidebar.css
│           ├── dashboard.css
│           └── catalogo.css
│
├── database/                        # Tudo que é banco
│   ├── __init__.py                  # marca como pacote Python
│   ├── db.py                        # get_db(), close_db(), init_app()
│   ├── schema.sql                   # CREATE TABLE
│   ├── init_db.py                   # cria/recria o .sqlite3 (--com-exemplos p/ seed)
│   └── atoriart.sqlite3             # gerado pelo init_db.py (gitignored)
│
├── .env / .env.example              # Variáveis de ambiente
├── .gitignore
├── requirements.txt
├── run.py                           # from backend import create_app
├── PROJECT_CONTEXT.md
└── README.md
```

---

## Como executar localmente

1. **Clonar e entrar no projeto**
   ```bash
   cd "Projeto AtoriArt"
   ```

2. **Criar e ativar virtualenv**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate     # macOS / Linux
   # .venv\Scripts\activate      # Windows PowerShell
   ```

3. **Instalar dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Criar o `.env`** (copiando o exemplo)
   ```bash
   cp .env.example .env
   ```

5. **Gerar o `SECRET_KEY`** e colar no `.env`:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

6. **Gerar o hash da senha de admin** e colar em `ADMIN_PASSWORD_HASH`:
   ```bash
   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('SuaSenhaForte'))"
   ```

7. **Criar o banco SQLite** (uma vez)
   ```bash
   python database/init_db.py                  # banco VAZIO (só a estrutura)
   python database/init_db.py --com-exemplos   # banco + dados de exemplo
   ```
   Isso cria `database/atoriart.sqlite3` com as tabelas. Sem a flag, o banco
   nasce vazio — pronto para você cadastrar seus próprios dados. Com
   `--com-exemplos`, ele é populado com materiais, peças e vendas fictícias
   úteis para ver o dashboard funcionando.

8. **Subir o servidor**
   ```bash
   python run.py
   ```
   Acesse `http://127.0.0.1:5000` — você será redirecionado para o login.

---

## Decisões de arquitetura

### Camadas (separação de responsabilidades)
| Camada           | Responsabilidade                                    | Pode importar             |
|------------------|-----------------------------------------------------|---------------------------|
| `blueprints/`    | Apenas controle HTTP (request/response, redirects)  | `services`, `security`    |
| `services/`      | Regras de negócio e construção de ViewModels        | `repositories`, `models`  |
| `repositories/`  | Acesso a dados (SQL puro no SQLite)                 | `models`                  |
| `models/`        | Entidades de domínio (dataclasses)                  | nada do backend           |
| `templates/`     | Apenas exibição — sem regra de negócio              | —                         |
| `static/css/`    | CSS separado por contexto                           | —                         |

**Regra de ouro:** Jinja **não** chama serviço nem banco. O blueprint chama o
serviço, recebe um ViewModel pronto e passa para o template. O template
apenas exibe.

### Application factory
`create_app()` em [backend/__init__.py](backend/__init__.py) permite múltiplas
instâncias (testes, scripts) e isola configuração de execução.

### Blueprints
Cada módulo do sistema (auth, dashboard, catálogo, etc.) é um blueprint
independente, com `url_prefix` próprio e templates dedicados. Isso mantém
o crescimento modular.

### Sem ORM nesta fase
Usaremos `sqlite3` da stdlib via repositórios. Motivo: o domínio é simples e
o SQL é didático para a fase inicial. Se a complexidade crescer, podemos
introduzir SQLAlchemy depois — sem mudar o resto da arquitetura, já que o
acesso a dados está isolado nos repositórios.

---

## Segurança

| Aspecto                    | O que foi feito nesta etapa                                   |
|----------------------------|----------------------------------------------------------------|
| Segredos                   | `SECRET_KEY` e credenciais no `.env` — nunca no código         |
| Senha do admin             | Armazenada como **hash** (`werkzeug.security`)                 |
| Comparação de credenciais  | Tempo constante (`hmac.compare_digest` + `check_password_hash`)|
| Sessão                     | `HttpOnly` + `SameSite=Lax` sempre; `Secure=True` em produção  |
| Tempo de sessão            | Expira após `SESSION_LIFETIME_MINUTES` (padrão: 60 min)        |
| CSRF                       | Token por sessão; validado em todo POST (login + logout)       |
| Open redirect              | `_safe_next` aceita apenas paths relativos                     |
| Headers HTTP               | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` |
| Autorização                | Decorator `@login_required` em toda rota interna               |
| Sem cadastro público       | Só existe um admin; rota de login não cria contas              |

**Em produção:**
- Servir atrás de HTTPS.
- `FLASK_ENV=production` (ativa `SESSION_COOKIE_SECURE=True`).
- Trocar `SECRET_KEY` e `ADMIN_PASSWORD_HASH` para valores reais.
- Considerar adicionar Flask-WTF para CSRF mais robusto e validação de forms.

---

## Estado atual

Todos os módulos do domínio estão implementados e ligados a dados reais
do banco:

| Módulo         | Rota             | O que faz                                                |
|----------------|------------------|----------------------------------------------------------|
| Catálogo       | `/catalogo/`     | Vitrine das peças com estoque > 0 (somente leitura).     |
| Matéria-prima  | `/materiais/`    | CRUD de insumos (cadastro pelo preço total pago) com alerta de estoque baixo. |
| Produção       | `/producao/`     | Produções e cadastro de peças; produção **debita os materiais** consumidos. |
| Vendas         | `/vendas/`       | Registro de vendas com baixa automática de estoque.      |
| Despesas       | `/despesas/`     | Registro de custos do negócio (alimenta a receita líquida).|
| Relatórios     | `/relatorios/`   | Consolidação das vendas dos últimos 30 dias.             |
| Configurações  | `/configuracoes/`| Informações do sistema, da aplicação e do banco.         |

O **custo de produção de cada peça é calculado automaticamente** a partir
dos materiais que ela consome (view `vw_peca_custo`). No cadastro da peça
o usuário informa apenas o **preço de venda sugerido** — o sistema deriva
o custo, o lucro e a margem.

### Próximas etapas (backlog)

1. Filtro de período nas listagens e no relatório (hoje fixo em 30 dias).
2. Trocar senha pela interface (migrar credencial do `.env` para tabela).
3. Resetar banco pela interface (hoje via `python database/init_db.py`).
4. Baixa automática de matéria-prima ao registrar produção.

A cada etapa, o `PROJECT_CONTEXT.md` é atualizado com as decisões tomadas.

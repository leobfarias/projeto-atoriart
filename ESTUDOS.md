# Guia de Estudos — AtoriArt

> **Para que serve este documento:** sintetiza tudo que foi construído e
> explicado durante o desenvolvimento do AtoriArt. Cada conceito tem um
> resumo + onde fica no projeto + por que foi feito daquele jeito.
> Use como material de revisão.

---

## Sumário

1. [Visão geral do projeto](#1-visão-geral-do-projeto)
2. [Stack tecnológica](#2-stack-tecnológica)
3. [Arquitetura — 3 pacotes raiz](#3-arquitetura--3-pacotes-raiz)
4. [Camadas de código (Blueprint → Service → Repository → Model)](#4-camadas-de-código)
5. [Application Factory](#5-application-factory)
6. [O arquivo `__init__.py`](#6-o-arquivo-__init__py)
7. [Configuração via `.env`](#7-configuração-via-env)
8. [Segurança](#8-segurança)
9. [Banco de dados SQLite](#9-banco-de-dados-sqlite)
10. [Modelos (dataclasses)](#10-modelos-dataclasses)
11. [Repositórios (camada de SQL)](#11-repositórios-camada-de-sql)
12. [Services (regra de negócio)](#12-services-regra-de-negócio)
13. [Blueprints e rotas](#13-blueprints-e-rotas)
14. [Templates Jinja](#14-templates-jinja)
15. [CSS — variáveis e BEM](#15-css--variáveis-e-bem)
16. [Páginas do sistema](#16-páginas-do-sistema)
17. [CRUD — padrão dos formulários](#17-crud--padrão-dos-formulários)
18. [HTML semântico sem JavaScript](#18-html-semântico-sem-javascript)
19. [Decisões registradas (ADRs)](#19-decisões-registradas-adrs)
20. [Como rodar o projeto](#20-como-rodar-o-projeto)
21. [Glossário](#21-glossário)

---

## 1. Visão geral do projeto

**AtoriArt** é um sistema web administrativo de **gestão de estoque para
artesanato**. Cliente única (artesã), sem cadastro público, apenas um
administrador autenticado. Será publicado na internet — por isso
segurança é prioridade desde o dia 1.

### Domínio do negócio

- **Catálogo de peças** produzidas (portfólio).
- **Matéria-prima** em estoque (com mínimos para alerta).
- **Produção** (lançamentos de peças produzidas).
- **Vendas** (faturamento bruto, com formas de pagamento).
- **Relatórios** (consolidam vendas + produção + catálogo).
- **Configurações** (conta admin + info de sistema).

### Como o sistema flui

1. Admin produz peças (e a produção fica registrada).
2. Peças prontas viram estoque do catálogo.
3. Quando vende, registra a venda com o valor recebido.
4. O sistema calcula: faturamento, custo de produção, lucro bruto,
   margem, e mostra rankings.

---

## 2. Stack tecnológica

| Camada     | Tecnologia                                            |
|------------|-------------------------------------------------------|
| Backend    | **Python 3.10+** com **Flask 3.x**                    |
| Frontend   | **HTML + CSS + Jinja2** (sem JavaScript principal)    |
| Banco      | **SQLite** (módulo `sqlite3` da stdlib — sem ORM)     |
| Config     | **python-dotenv** (lê variáveis do `.env`)            |
| Segurança  | `werkzeug.security`, `hmac`, `secrets`                |

### Por que essa stack?

- **Flask** é um microframework simples — não impõe estrutura,
  cabe a você organizar.
- **Jinja2** é o motor de templates do Flask, integrado por padrão.
- **SQLite** é um banco "single-file": não precisa servidor rodando,
  perfeito pra projeto solo e fácil pra estudante.
- **Sem ORM** porque o domínio é pequeno e SQL puro é didático.
  Se um dia ficar complicado, dá pra trocar pra SQLAlchemy só
  mexendo nos repositórios — o resto do código não muda.

### O que é proibido neste projeto

- JavaScript como tecnologia principal de frontend.
- Frameworks de frontend (React, Vue, etc.).
- Outros bancos (Postgres, MySQL).
- CSS inline em templates (`style="..."`).
- Regra de negócio dentro de templates Jinja.

---

## 3. Arquitetura — 3 pacotes raiz

O projeto é dividido em **três pacotes** com responsabilidades bem
distintas. Saber onde mexer fica óbvio:

```
Projeto AtoriArt/
├── backend/         # Tudo que é Python (Flask, regras, dados)
├── frontend/        # Templates Jinja + CSS
├── database/        # SQLite (db.py, schema.sql, init_db.py, .sqlite3)
└── ...
```

### Quando mexer onde

| O que você quer mudar              | Pasta            |
|------------------------------------|------------------|
| Uma rota, uma regra, uma query     | `backend/`       |
| O visual / HTML / CSS              | `frontend/`      |
| O schema, dados de exemplo, banco  | `database/`      |
| Variáveis de ambiente              | `.env`           |
| Dependências                       | `requirements.txt` |

### Por que separar assim?

Manutenção a longo prazo. Quando o sistema crescer (matéria-prima,
produção, vendas etc.), cada novo módulo replica o mesmo padrão nas
três pastas:

```
backend/blueprints/<modulo>/routes.py
backend/services/<modulo>_service.py
backend/repositories/<modulo>_repository.py
backend/models/<modulo>.py
frontend/templates/<modulo>/...
frontend/static/css/<modulo>.css
database/schema.sql        # acrescenta tabela
database/init_db.py        # acrescenta seed
```

Visualização da árvore completa:

```
Projeto AtoriArt/
├── backend/
│   ├── __init__.py                  # create_app() — application factory
│   ├── config.py                    # Configs por ambiente + .env loader
│   ├── security.py                  # login_required, autenticação, CSRF
│   ├── blueprints/                  # Controllers HTTP (rotas)
│   │   ├── auth/routes.py           # /auth/login, /auth/logout
│   │   ├── catalogo/routes.py       # /catalogo/
│   │   ├── configuracoes/routes.py  # /configuracoes/
│   │   ├── dashboard/routes.py      # /painel
│   │   ├── materia_prima/routes.py  # /materiais/
│   │   ├── producao/routes.py       # /producao/
│   │   ├── relatorios/routes.py     # /relatorios/
│   │   └── vendas/routes.py         # /vendas/
│   ├── services/                    # Regras de negócio
│   │   ├── catalogo_service.py
│   │   ├── configuracoes_service.py
│   │   ├── dashboard_service.py
│   │   ├── materia_prima_service.py
│   │   ├── producao_service.py
│   │   ├── relatorios_service.py
│   │   └── vendas_service.py
│   ├── repositories/                # Acesso a dados (SQL)
│   │   ├── material_repository.py
│   │   ├── peca_repository.py
│   │   ├── producao_repository.py
│   │   └── venda_repository.py
│   └── models/                      # Entidades de domínio
│       ├── material.py
│       ├── peca.py
│       ├── producao.py
│       └── venda.py
│
├── frontend/
│   ├── templates/
│   │   ├── base.html
│   │   ├── _sidebar.html
│   │   ├── auth/login.html
│   │   ├── catalogo/
│   │   │   ├── index.html             # listagem
│   │   │   └── form.html              # criar/editar peça
│   │   ├── configuracoes/index.html
│   │   ├── dashboard/index.html
│   │   ├── materia_prima/
│   │   │   ├── index.html             # listagem
│   │   │   └── form.html              # criar/editar material
│   │   ├── producao/
│   │   │   ├── index.html             # listagem
│   │   │   └── form.html              # registrar produção
│   │   ├── relatorios/index.html
│   │   └── vendas/
│   │       ├── index.html             # listagem
│   │       └── form.html              # registrar venda
│   └── static/css/
│       ├── base.css                   # Variáveis, reset, botões
│       ├── catalogo.css
│       ├── configuracoes.css
│       ├── dashboard.css
│       ├── forms.css                  # CSS COMPARTILHADO dos formulários
│       ├── login.css
│       ├── materia_prima.css
│       ├── producao.css
│       ├── relatorios.css
│       ├── sidebar.css
│       └── vendas.css
│
├── database/
│   ├── __init__.py                  # marca como pacote Python
│   ├── db.py                        # get_db(), close_db(), init_app()
│   ├── schema.sql                   # CREATE TABLE de todas tabelas
│   ├── init_db.py                   # cria/recria o banco + seed
│   └── atoriart.sqlite3             # arquivo do banco (gitignored)
│
├── .env / .env.example
├── .gitignore
├── requirements.txt
├── run.py
├── PROJECT_CONTEXT.md
├── README.md
└── ESTUDOS.md                       # este arquivo
```

---

## 4. Camadas de código

Cada request HTTP atravessa as mesmas camadas, na ordem:

```
HTTP request
   ↓
Blueprint (rota) ............ controla fluxo HTTP, valida CSRF, redireciona
   ↓
Service ..................... aplica regras de negócio, monta ViewModel
   ↓
Repository .................. SQL puro contra SQLite
   ↓
Model (dataclass) ........... entidade de domínio
   ↓
Template Jinja .............. SÓ EXIBE o ViewModel recebido
```

### A regra de ouro

| Camada       | Pode importar                  | NÃO pode                       |
|--------------|--------------------------------|--------------------------------|
| Blueprint    | `services`, `security`         | repositórios, SQL              |
| Service      | `repositories`, `models`       | Flask (exceção: configuracoes_service) |
| Repository   | `database.db`, `models`        | HTTP, regras                   |
| Model        | nada (dataclass pura)          | tudo                           |
| Template     | só recebe ViewModel pronto     | acessar serviço, regra de negócio |

### Por que isso importa?

- **Trocar SQL por Postgres**: você só mexe nos repositórios. Tudo
  o resto (services, blueprints, templates) continua igual.
- **Testar a regra de negócio sem Flask**: services não dependem
  de HTTP, então dá pra testar isolado.
- **Mudar o visual**: você mexe só em templates e CSS. Lógica nem
  encosta.

### Exemplo concreto — fluxo da página de Catálogo

1. **Usuário acessa** `GET /catalogo/`.
2. **Blueprint** [backend/blueprints/catalogo/routes.py](backend/blueprints/catalogo/routes.py)
   verifica `@login_required`, chama `dados_catalogo()`.
3. **Service** [backend/services/catalogo_service.py](backend/services/catalogo_service.py)
   pede `peca_repository.list_pecas()` e calcula KPIs.
4. **Repository** [backend/repositories/peca_repository.py](backend/repositories/peca_repository.py)
   roda `SELECT ... FROM peca` e hidrata objetos `Peca`.
5. **Models** [backend/models/peca.py](backend/models/peca.py) e
   [backend/models/material.py](backend/models/material.py) carregam
   os dados.
6. **Template** [frontend/templates/catalogo/index.html](frontend/templates/catalogo/index.html)
   recebe o ViewModel e renderiza HTML.

---

## 5. Application Factory

O Flask aceita ser instanciado de várias formas. A mais simples é:

```python
app = Flask(__name__)
# define rotas...
```

Mas isso tem problemas: a `app` vira global, fica difícil de testar e
fica engessado pra um único ambiente.

**Application factory** é um padrão onde a criação da app vive dentro
de uma função `create_app()`. Quem precisa da app chama a função.

### Como funciona no AtoriArt

Em [backend/__init__.py](backend/__init__.py):

```python
def create_app(config_class=None):
    app = Flask(__name__, template_folder=..., static_folder=...)
    cfg = config_class or get_config()
    app.config.from_object(cfg)

    _ensure_secret_key(app)
    _ensure_database_dir(app)
    _register_database(app)
    _register_blueprints(app)
    _register_context_processors(app)
    _register_security_headers(app)

    return app
```

E em [run.py](run.py):

```python
from backend import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
```

### Vantagens

- **Múltiplos ambientes**: pode criar `create_app(TestConfig)` pra testes.
- **Inicialização ordenada**: cada `_register_*` é um passo claro.
- **Falha rápido**: `_ensure_secret_key` aborta o boot se faltar config.
- **Flask aponta pra `frontend/`**: usamos `template_folder` e
  `static_folder` com paths absolutos pra fora do `backend/`.

---

## 6. O arquivo `__init__.py`

### O que ele faz

`__init__.py` **marca uma pasta como pacote Python**. Sem ele,
o `import` não enxerga os arquivos dentro daquela pasta.

### No projeto

Quando o código faz:

```python
from backend.security import login_required
```

O Python:
1. Procura uma pasta `backend/` com `__init__.py` → ✅ é pacote
2. Procura `security.py` dentro → ✅ achou
3. Importa `login_required` de lá

Se o `backend/__init__.py` **não existisse**, daria
`ModuleNotFoundError: No module named 'backend'`.

### Dois tipos no projeto

**1. Vazio (marcador) — a maioria**
- `backend/blueprints/__init__.py` (vazio)
- `backend/blueprints/auth/__init__.py` (vazio)
- `backend/services/__init__.py` (vazio)
- `database/__init__.py` (vazio)

Servem só para dizer "essa pasta é um pacote, pode importar coisas
daqui".

**2. Com código de inicialização**
- [backend/__init__.py](backend/__init__.py) tem a `create_app()` e a
  constante `__version__ = "1.0.0"`.

Por causa disso, `from backend import create_app` executa o arquivo e
expõe a função.

### Regra prática

Sempre que criar uma pasta com código Python que vai ser importado,
coloque um `__init__.py` dentro. Mesmo vazio.

---

## 7. Configuração via `.env`

### Por que `.env`?

Segredos (chaves, senhas, tokens) **nunca** podem ir pro repositório
git. A solução padrão é guardar num arquivo `.env` (que está no
`.gitignore`) e o código lê via `python-dotenv`.

### Variáveis usadas

```bash
# Ambiente
FLASK_ENV=development           # ou production
FLASK_DEBUG=1

# Segurança
SECRET_KEY=...                  # assina cookies de sessão do Flask
ADMIN_USERNAME=admin            # usuário do admin
ADMIN_PASSWORD_HASH=...         # hash da senha (NÃO a senha)

# Sessão
SESSION_LIFETIME_MINUTES=60     # duração em minutos
SESSION_COOKIE_SECURE=0         # 1 em produção (HTTPS)
```

### Como gerar os segredos

```bash
# SECRET_KEY (assina sessão)
python -c "import secrets; print(secrets.token_hex(32))"

# ADMIN_PASSWORD_HASH (hash de werkzeug)
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('SuaSenhaForte'))"
```

### Como é carregado no código

[backend/config.py](backend/config.py):

```python
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")    # lê .env e popula os.environ


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")
    # ...
```

### Configs por ambiente

Duas classes filhas:
- `DevelopmentConfig`: `DEBUG=True`, cookies **inseguros** OK.
- `ProductionConfig`: `DEBUG=False`, cookies **seguros** obrigatórios.

A função `get_config()` escolhe com base em `FLASK_ENV`.

---

## 8. Segurança

### Visão geral

| Aspecto                    | O que foi feito                                                  |
|----------------------------|------------------------------------------------------------------|
| Segredos                   | `.env`, nunca no código                                          |
| Senha do admin             | Armazenada como **hash** (`werkzeug.security`)                   |
| Comparação de credenciais  | Tempo constante (`hmac.compare_digest` + `check_password_hash`)  |
| Sessão                     | `HttpOnly` + `SameSite=Lax` sempre; `Secure=True` em produção    |
| Tempo de sessão            | Expira após `PERMANENT_SESSION_LIFETIME` (60 min)                |
| CSRF                       | Token por sessão; validado em todo POST                          |
| Open redirect              | `_safe_next` aceita apenas paths relativos                       |
| Headers HTTP               | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`   |
| Autorização                | Decorator `@login_required` em toda rota interna                 |

### Login (autenticação)

Arquivo: [backend/security.py](backend/security.py)

```python
def authenticate(username, password):
    expected_user = current_app.config.get("ADMIN_USERNAME", "")
    expected_hash = credencial_repository.get_password_hash(expected_user)

    if not expected_hash:
        return False  # sem hash gravado: nega o login

    user_ok = hmac.compare_digest(
        (username or "").encode("utf-8"),
        expected_user.encode("utf-8"),
    )
    pass_ok = check_password_hash(expected_hash, password or "")
    return user_ok and pass_ok
```

**Por que `hmac.compare_digest`?**
A função `==` comum compara byte a byte e **pára no primeiro diferente**.
Um atacante medindo o tempo de resposta pode deduzir letras corretas
um caractere por vez. `compare_digest` sempre compara em tempo igual.

**Por que hash da senha?**
Se o banco vazar, ainda há custo computacional pra recuperar a senha
original. `werkzeug.security.generate_password_hash` usa algoritmos
fortes (scrypt ou pbkdf2).

**Onde mora o hash?** Na tabela `admin_credencial` no banco (ADR-014).
O `.env` continua sendo o **seed inicial**: no primeiro boot,
`database/db.py._apply_migrations` cria a tabela e copia o
`ADMIN_PASSWORD_HASH` pra ela. Depois disso a tabela vira a fonte de
verdade — trocar senha pela UI grava ali, não mexe no `.env`.

### Decorator `@login_required`

```python
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped
```

Qualquer rota com `@login_required` redireciona pra `/auth/login` se
o usuário não estiver autenticado. O `next=request.path` lembra onde
ele queria ir.

### CSRF (Cross-Site Request Forgery)

CSRF é quando um site malicioso faz seu navegador enviar um POST
autenticado pra outro site (ex.: tentar deletar algo no AtoriArt
enquanto você está logado).

**Defesa:** todo formulário POST tem um token único na sessão. O
servidor valida o token no recebimento.

```python
def generate_csrf_token():
    token = session.get(SESSION_CSRF_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[SESSION_CSRF_KEY] = token
    return token


def require_csrf():
    token = request.form.get("csrf_token")
    if not validate_csrf_token(token):
        abort(400, description="Token CSRF inválido.")
```

No template:
```html
<form method="POST" action="...">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
  <!-- resto do form -->
</form>
```

### Open redirect

Se você redireciona pra uma URL vinda da query string
(`?next=...`), um atacante pode mandar `?next=https://site-malicioso.com`.

**Defesa:** só aceita caminhos relativos (começam com `/`):

```python
def _safe_next(target):
    if not target:
        return None
    if target.startswith("/") and not target.startswith("//"):
        return target
    return None
```

### Headers de segurança

[backend/__init__.py](backend/__init__.py):

```python
@app.after_request
def set_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    return response
```

- **X-Content-Type-Options: nosniff** — navegador não tenta "adivinhar"
  o tipo do arquivo (evita arquivos malformados executarem como JS).
- **X-Frame-Options: DENY** — proíbe a página de ser embarcada em
  `<iframe>` (defesa contra clickjacking).
- **Referrer-Policy: same-origin** — não revela URL completa para
  sites externos.

### Cookies de sessão

```python
SESSION_COOKIE_HTTPONLY = True      # JS não acessa o cookie (defesa XSS)
SESSION_COOKIE_SAMESITE = "Lax"     # cookie só vai no site dele mesmo
SESSION_COOKIE_SECURE = True        # só em conexão HTTPS (produção)
```

---

## 9. Banco de dados SQLite

### Por que SQLite?

- **Sem servidor**: arquivo único (`database/atoriart.sqlite3`).
- **Suficiente**: o domínio é pequeno, o admin é único.
- **Educacional**: SQL puro, sem ORM.

### Conexão por request — `database/db.py`

```python
def get_db():
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE_PATH"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(error=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_app(app):
    app.teardown_appcontext(close_db)
```

**Conceitos importantes aqui:**

- **`g`** é um objeto especial do Flask que vive **durante um único
  request**. Funciona como um cache temporário. Próximo request
  começa do zero.
- **`row_factory = sqlite3.Row`** permite acessar colunas por nome
  (`row["nome"]`) em vez de índice (`row[0]`).
- **`PRAGMA foreign_keys = ON`** liga checagem de FK no SQLite
  (vem desligada por padrão!).
- **`teardown_appcontext(close_db)`** garante que a conexão é fechada
  no fim de cada request, mesmo se der erro.

### Schema — `database/schema.sql`

Define todas as tabelas. Sempre começa com `DROP TABLE IF EXISTS`
pra ser idempotente (rodar várias vezes não quebra).

```sql
DROP VIEW  IF EXISTS vw_peca_custo;
DROP TABLE IF EXISTS despesa;
DROP TABLE IF EXISTS venda;
DROP TABLE IF EXISTS producao;
DROP TABLE IF EXISTS peca_material;
DROP TABLE IF EXISTS peca;
DROP TABLE IF EXISTS material;

CREATE TABLE material (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                TEXT    NOT NULL,
    unidade             TEXT    NOT NULL,
    valor_unitario      REAL    NOT NULL,
    quantidade_estoque  REAL    NOT NULL DEFAULT 0,
    estoque_minimo      REAL    NOT NULL DEFAULT 0
);

-- `preco_venda` é digitado; o custo NÃO é coluna (vem da view abaixo).
CREATE TABLE peca (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                TEXT    NOT NULL,
    preco_venda         REAL    NOT NULL,
    quantidade_estoque  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE peca_material (
    peca_id      INTEGER NOT NULL,
    material_id  INTEGER NOT NULL,
    quantidade   REAL    NOT NULL,
    PRIMARY KEY (peca_id, material_id),
    FOREIGN KEY (peca_id)     REFERENCES peca(id)     ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES material(id) ON DELETE RESTRICT
);

CREATE TABLE producao (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    peca_id     INTEGER NOT NULL,
    quantidade  INTEGER NOT NULL,
    data        TEXT    NOT NULL,
    observacao  TEXT,
    FOREIGN KEY (peca_id) REFERENCES peca(id) ON DELETE CASCADE
);
CREATE INDEX idx_producao_data ON producao(data);

CREATE TABLE venda (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    peca_id          INTEGER NOT NULL,
    quantidade       INTEGER NOT NULL,
    valor_total      REAL    NOT NULL,
    data             TEXT    NOT NULL,
    forma_pagamento  TEXT,
    FOREIGN KEY (peca_id) REFERENCES peca(id) ON DELETE RESTRICT
);
CREATE INDEX idx_venda_data ON venda(data);

-- Despesa: registro puro, sem FK e sem efeito no estoque.
CREATE TABLE despesa (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao   TEXT    NOT NULL,
    categoria   TEXT,
    valor       REAL    NOT NULL,
    data        TEXT    NOT NULL
);
CREATE INDEX idx_despesa_data ON despesa(data);

-- Custo de produção da peça = soma dos materiais. VIEW, não coluna.
CREATE VIEW vw_peca_custo AS
SELECT pm.peca_id                            AS peca_id,
       SUM(pm.quantidade * m.valor_unitario) AS custo_producao
FROM peca_material pm
JOIN material m ON m.id = pm.material_id
GROUP BY pm.peca_id;
```

**Conceitos a entender:**

- **PRIMARY KEY AUTOINCREMENT**: cria IDs únicos automaticamente.
- **FOREIGN KEY**: liga uma tabela a outra. Ex.: `peca_material.peca_id`
  referencia `peca.id`.
- **ON DELETE CASCADE**: se a peça for apagada, os `peca_material`
  dela somem junto (são detalhes dela).
- **ON DELETE RESTRICT**: se a peça tem vendas, **não pode apagar**.
  Vendas são histórico financeiro.
- **CREATE INDEX**: acelera consultas com `WHERE data >= ?`.
- **CREATE VIEW**: "tabela virtual" — uma consulta salva com nome.
  `vw_peca_custo` calcula o custo de cada peça (soma dos materiais);
  quem precisa do custo faz JOIN com ela em vez de repetir a conta.

### Seed — `database/init_db.py`

Script que cria (ou recria) o banco. Roda direto, não precisa do Flask.
Os dados de exemplo são **opcionais**, controlados pela flag
`--com-exemplos`:

- `python database/init_db.py` → banco **vazio** (só a estrutura).
- `python database/init_db.py --com-exemplos` → banco + dados de exemplo.

```python
def main(com_exemplos=False):
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())

    if com_exemplos:
        inserir_dados_exemplo(conn)
    conn.commit()
    conn.close()
```

A flag é lida com `argparse` no bloco `if __name__ == "__main__"`.

**Detalhe importante:** as datas das produções e vendas são geradas
**relativas a `date.today()`**:

```python
hoje = date.today()

def dia(dias_atras):
    return (hoje - timedelta(days=dias_atras)).isoformat()

producoes = [
    (1, 5, dia(1), None),     # ontem
    (3, 3, dia(2), None),     # anteontem
    # ...
]
```

Por quê? Senão, daqui a 1 ano, todas as "vendas" estariam fora dos
últimos 30 dias e o relatório ficaria vazio.

---

## 10. Modelos (dataclasses)

Modelos são **dataclasses puras**: classes que só carregam dados.
Não conhecem Flask, não conhecem SQL.

### Exemplo — `backend/models/material.py`

```python
from dataclasses import dataclass


@dataclass
class Material:
    id: int
    nome: str
    unidade: str
    valor_unitario: float
    quantidade_estoque: float = 0.0
    estoque_minimo: float = 0.0

    @property
    def em_alerta(self) -> bool:
        return self.quantidade_estoque < self.estoque_minimo
```

### O que `@dataclass` faz

O decorador `@dataclass` gera automaticamente:
- `__init__` (construtor com todos os campos)
- `__repr__` (representação em string para debug)
- `__eq__` (comparação por valor)

Sem dataclass, você teria que escrever isso na mão.

### O que `@property` faz

Transforma um método em algo que parece atributo:

```python
m = Material(id=3, nome="Pingente", unidade="un",
             valor_unitario=1.50, quantidade_estoque=6,
             estoque_minimo=10)

m.em_alerta    # True (chama o método, não precisa de parêntese)
```

### Modelos no projeto

| Arquivo | Classe(s) | Pra que serve |
|---------|-----------|---------------|
| [backend/models/material.py](backend/models/material.py) | `Material` | Insumo de matéria-prima |
| [backend/models/peca.py](backend/models/peca.py) | `ItemMaterial`, `Peca` | Peça e materiais que ela consome |
| [backend/models/producao.py](backend/models/producao.py) | `Producao` | Registro de "produzi N peças" |
| [backend/models/venda.py](backend/models/venda.py) | `Venda` | Registro de "vendi N peças" |
| [backend/models/despesa.py](backend/models/despesa.py) | `Despesa` | Registro de "gastei R$ Z com W" |

> A `Peca` traz `custo_producao` já calculado (view `vw_peca_custo`) e
> expõe as propriedades `lucro` (preço − custo) e `margem` (% sobre o
> preço) — valor derivado mora no model/banco, nunca é digitado.

### Denormalização para display

`Producao` e `Venda` têm campos `peca_nome` e `peca_custo` que vêm
do JOIN no repository. Por quê?

A alternativa seria carregar a `Peca` inteira (com todos os seus
materiais), só pra ler o nome. Caro e desnecessário.

```python
@dataclass
class Venda:
    id: int
    peca_id: int
    peca_nome: str          # vem do JOIN, denormalizado
    peca_custo: float       # vem do JOIN, denormalizado
    quantidade: int
    valor_total: float
    data: str
    forma_pagamento: str | None = None

    @property
    def custo_total(self) -> float:
        return self.quantidade * self.peca_custo

    @property
    def lucro_bruto(self) -> float:
        return self.valor_total - self.custo_total
```

---

## 11. Repositórios (camada de SQL)

Os repositórios são a **única camada que fala com o banco**. Recebem
e devolvem objetos modelo.

### Padrão geral

```python
from database.db import get_db
from backend.models.X import X


def list_x(filtros_opcionais=None):
    db = get_db()
    rows = db.execute("SELECT ... FROM x WHERE ...", params).fetchall()
    return [_row_to_x(r) for r in rows]


def get_x(x_id):
    db = get_db()
    r = db.execute("SELECT ... FROM x WHERE id = ?", (x_id,)).fetchone()
    return _row_to_x(r) if r else None


def _row_to_x(r):
    return X(id=r["id"], nome=r["nome"], ...)
```

### JOIN — exemplo de [backend/repositories/peca_repository.py](backend/repositories/peca_repository.py)

Pra trazer os materiais de uma peça, faz JOIN:

```python
def _materiais_da_peca(db, peca_id):
    rows = db.execute(
        "SELECT m.id, m.nome, m.unidade, m.valor_unitario, pm.quantidade "
        "FROM peca_material pm "
        "JOIN material m ON m.id = pm.material_id "
        "WHERE pm.peca_id = ? "
        "ORDER BY m.nome COLLATE NOCASE",
        (peca_id,),
    ).fetchall()
    return [ItemMaterial(material=Material(...), quantidade=r["quantidade"])
            for r in rows]
```

**`COLLATE NOCASE`** ordena ignorando maiúscula/minúscula
(Á = á, B = b, etc.).

### Filtro por período — exemplo de `venda_repository`

```python
def list_vendas(desde=None):
    db = get_db()
    sql = "SELECT v.*, pe.nome AS peca_nome, pe.custo_producao AS peca_custo " \
          "FROM venda v JOIN peca pe ON pe.id = v.peca_id"
    params = ()
    if desde:
        sql += " WHERE v.data >= ?"
        params = (desde,)
    sql += " ORDER BY v.data DESC, v.id DESC"
    rows = db.execute(sql, params).fetchall()
    return [_row_to_venda(r) for r in rows]
```

### SQL parametrizado (SEMPRE!)

**NUNCA** faça:

```python
# ERRADO — SQL injection!
db.execute(f"SELECT * FROM x WHERE id = {x_id}")
```

**SEMPRE**:

```python
# CERTO — placeholder ?
db.execute("SELECT * FROM x WHERE id = ?", (x_id,))
```

O `?` é placeholder. O segundo argumento é uma tupla com os valores.
O driver SQLite escapa pra você.

---

## 12. Services (regra de negócio)

Services pegam dados crus dos repositórios e devolvem o
**ViewModel** que o template vai exibir.

### Exemplo — [backend/services/catalogo_service.py](backend/services/catalogo_service.py)

```python
from backend.repositories import peca_repository


def dados_catalogo():
    pecas = peca_repository.list_pecas()
    return {
        "pecas": pecas,
        "pecas_em_estoque": sum(p.quantidade_estoque for p in pecas),
        "pecas_cadastradas": len(pecas),
        "custo_total": sum(
            p.custo_producao * p.quantidade_estoque for p in pecas
        ),
        "vendas_30d": 0,    # TODO: vendas_repository
    }
```

### Por que dicionário e não dataclass?

Pra services simples de página, dict é menos código e a chave vira
variável no template (`{{ pecas_em_estoque }}`). Pra coisas mais
estruturadas (modelos), dataclass é melhor.

### Filtro de 30 dias — exemplo de `producao_service`

```python
from datetime import date, timedelta

JANELA_DIAS = 30


def dados_producao():
    desde = (date.today() - timedelta(days=JANELA_DIAS)).isoformat()
    producoes = producao_repository.list_producoes(desde=desde)

    return {
        "producoes": producoes,
        "janela_dias": JANELA_DIAS,
        "total_producoes": len(producoes),
        "pecas_produzidas": sum(p.quantidade for p in producoes),
        "peca_top": _peca_mais_produzida(producoes),
        "custo_total": sum(p.custo_subtotal for p in producoes),
    }


def _peca_mais_produzida(producoes):
    if not producoes:
        return None
    from collections import Counter
    c = Counter()
    for p in producoes:
        c[p.peca_nome] += p.quantidade
    return c.most_common(1)[0][0]
```

### Agregações em Python — exemplo de `relatorios_service`

Pra relatórios mais complexos (top 5 peças, distribuição por
pagamento), fazemos agregação em Python em vez de SQL agregado.

```python
def _ranking_por_peca(vendas):
    por_peca = {}
    for v in vendas:
        d = por_peca.setdefault(v.peca_id, {
            "peca_nome": v.peca_nome,
            "vendas": 0,
            "quantidade": 0,
            "faturamento": 0.0,
            "custo": 0.0,
        })
        d["vendas"] += 1
        d["quantidade"] += v.quantidade
        d["faturamento"] += v.valor_total
        d["custo"] += v.custo_total

    for d in por_peca.values():
        d["lucro"] = d["faturamento"] - d["custo"]
        d["margem"] = (d["lucro"] / d["faturamento"] * 100) if d["faturamento"] else 0

    return sorted(por_peca.values(), key=lambda x: x["lucro"], reverse=True)
```

**Por que não SQL agregado?**
- Volume é pequeno (dezenas de vendas), performance é igual.
- Mais didático ver as contas em Python.
- Refazer o cálculo em SQL exige mais conhecimento (GROUP BY,
  subqueries, etc.).

### Exceção arquitetural — `configuracoes_service`

Este service é o ÚNICO que importa `current_app` do Flask. Por quê?
A página de Configurações exibe info do próprio Flask (config,
ambiente, banco) — não há "regra de negócio" tradicional.

```python
"""EXCEÇÃO ARQUITETURAL: este service importa `current_app` do Flask
porque a página é fundamentalmente sobre o sistema em si (config,
ambiente, banco). Não há regra de negócio aqui — só coleta e formatação
de informações do próprio runtime. Documentado para não virar moda.
"""
```

---

## 13. Blueprints e rotas

### O que é um Blueprint?

Um Blueprint agrupa rotas relacionadas. Cada módulo do AtoriArt
(auth, catalogo, vendas...) é um Blueprint próprio.

```python
from flask import Blueprint

catalogo_bp = Blueprint("catalogo", __name__, url_prefix="/catalogo")


@catalogo_bp.route("/")
def index():
    ...
```

- `"catalogo"` é o nome interno (usado em `url_for('catalogo.index')`).
- `url_prefix="/catalogo"` é o prefixo de URL. A rota `"/"` vira `/catalogo/`.

### Registro no `create_app()`

```python
def _register_blueprints(app):
    from backend.blueprints.catalogo.routes import catalogo_bp
    # ... outros
    app.register_blueprint(catalogo_bp)
```

> **Exceção pontual:** o `GET /ping` (health check anti-suspend do free
> tier do Render) vive direto no `run.py`, fora de qualquer blueprint.
> É **temporário** e tem um comentário em cima sinalizando isso. Toda
> rota nova permanente segue o padrão acima — ver [ADR-015](#adr-015--rota-ping-anti-suspend-em-runpy-fora-dos-blueprints).

### Padrão geral das rotas

```python
from flask import Blueprint, flash, redirect, render_template, url_for
from backend.security import login_required, require_csrf
from backend.services.X_service import dados_x

x_bp = Blueprint("x", __name__, url_prefix="/x")


@x_bp.route("/")
@login_required                       # exige usuário logado
def index():
    dados = dados_x()
    return render_template("x/index.html", **dados)


@x_bp.route("/<int:item_id>/apagar", methods=["POST"])
@login_required
def apagar(item_id):
    require_csrf()                    # valida token CSRF
    flash("Em desenvolvimento.", "info")
    return redirect(url_for("x.index"))
```

### `url_for()` em vez de URL hardcoded

Sempre use `url_for("nome.funcao")` em vez de escrever a URL na mão.

```python
return redirect(url_for("catalogo.index"))
# em vez de:
return redirect("/catalogo/")
```

Se um dia mudar o `url_prefix`, todos os links continuam funcionando
automaticamente.

### Rotas placeholder

Funcionalidades que serão implementadas depois ganham rotas
**placeholder** que respondem com flash + redirect. Por quê?

1. O template já pode apontar pra elas (`url_for(...)`).
2. A estrutura de URLs fica definida desde o dia 1.
3. Quando implementar de verdade, só troca o corpo da função.

```python
@catalogo_bp.route("/nova")
@login_required
def nova():
    flash("Cadastro de nova peça: em desenvolvimento.", "info")
    return redirect(url_for("catalogo.index"))
```

---

## 14. Templates Jinja

### Herança — `base.html`

Todo template estende uma base comum:

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <title>{% block title %}AtoriArt{% endblock %}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}" />
  {% block styles %}{% endblock %}
</head>
<body class="{% block body_class %}{% endblock %}">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      <ul class="flash-list">
        {% for category, msg in messages %}
          <li class="flash flash--{{ category }}">{{ msg }}</li>
        {% endfor %}
      </ul>
    {% endif %}
  {% endwith %}

  {% block layout %}{% endblock %}
</body>
</html>
```

Cada página define só o que muda:

```html
{% extends "base.html" %}
{% block title %}Catálogo — AtoriArt{% endblock %}
{% block body_class %}has-sidebar{% endblock %}
{% block styles %}
  <link rel="stylesheet" href="{{ url_for('static', filename='css/catalogo.css') }}" />
{% endblock %}

{% block layout %}
  {% include "_sidebar.html" %}
  <main class="content">
    <!-- conteúdo da página -->
  </main>
{% endblock %}
```

### Partials — `_sidebar.html`

Pedaços reutilizáveis começam com `_` (convenção). São incluídos
com `{% include %}`:

```html
{% include "_sidebar.html" %}
```

### Tags Jinja principais

| Tag                  | Para que serve                              |
|----------------------|---------------------------------------------|
| `{{ variavel }}`     | Imprime o valor                             |
| `{% if x %}{% endif %}` | Condicional                              |
| `{% for x in lista %}{% endfor %}` | Iteração                       |
| `{% block nome %}{% endblock %}` | Define ponto de extensão        |
| `{% extends "base.html" %}` | Herda de outro template              |
| `{% include "_x.html" %}` | Inclui outro template                  |
| `{% with x = ... %}{% endwith %}` | Variável local                  |

### Filtros — formatação

`{{ valor|filtro }}`:

| Filtro     | Exemplo                          |
|------------|----------------------------------|
| `'%.2f'\|format(x)` | `R$ {{ '%.2f'\|format(custo) }}` → `R$ 12.50` |
| `'%g'\|format(x)`   | `{{ '%g'\|format(2.0) }}` → `2` (sem zeros) |
| `\|length`          | `{{ lista\|length }}` → 4               |

### Context processors

[backend/__init__.py](backend/__init__.py) registra valores globais que
todo template vê automaticamente:

```python
@app.context_processor
def inject_globals():
    return {
        "current_user": current_user(),
        "is_authenticated": is_authenticated(),
        "csrf_token": generate_csrf_token,
    }
```

Por isso `{{ current_user }}` e `{{ csrf_token() }}` funcionam em
qualquer template.

### Sidebar com link ativo

```html
<a class="sidebar__link {% if request.endpoint and request.endpoint.startswith('catalogo.') %}is-active{% endif %}"
   href="{{ url_for('catalogo.index') }}">Catálogo</a>
```

`request.endpoint` é a função-rota atual (ex.: `"catalogo.index"`).
Se começar com `"catalogo."`, marca como ativo.

---

## 15. CSS — variáveis e BEM

### Variáveis CSS (custom properties)

Em [frontend/static/css/base.css](frontend/static/css/base.css):

```css
:root {
  --color-bg: #f6f3ef;
  --color-surface: #ffffff;
  --color-primary: #a8552b;
  --color-muted: #6b6862;
  --color-danger: #b13a3a;
  --color-success: #3e8e5e;
  --radius-md: 10px;
  --shadow-sm: 0 1px 2px rgba(20, 14, 6, 0.04);
}
```

Uso em qualquer arquivo CSS:

```css
.card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}
```

**Vantagem:** muda em 1 lugar, atualiza em todo o site.

### Convenção de nomes — BEM-ish

| Padrão         | Exemplo                  | O que significa          |
|----------------|--------------------------|--------------------------|
| `.bloco`       | `.peca`                  | Bloco autossuficiente    |
| `.bloco__elemento` | `.peca__nome`        | Parte do bloco           |
| `.bloco--modificador` | `.peca--alerta`   | Variação do bloco        |
| `.is-X`        | `.is-active`             | Estado momentâneo        |

### Um arquivo CSS por contexto

| Arquivo | Para que |
|---------|----------|
| `base.css` | Variáveis, reset, botões, flashes |
| `sidebar.css` | Painel lateral |
| `login.css` | Tela de login |
| `dashboard.css` | Painel |
| `catalogo.css` | Catálogo |
| `materia_prima.css` | Matéria-prima |
| `producao.css` | Produção |
| `vendas.css` | Vendas |
| `relatorios.css` | Relatórios |
| `configuracoes.css` | Configurações |
| `forms.css` | **Compartilhado** pelos 4 formulários de CRUD |

Cada template inclui só os CSS que precisa.

---

## 16. Páginas do sistema

### 16.1 Login — `/auth/login`

**Arquivo:** [backend/blueprints/auth/routes.py](backend/blueprints/auth/routes.py)

Form com usuário + senha. Valida via `authenticate()`. Inicia sessão
com `login_session()`. Redireciona pra `?next=` (se for path
relativo) ou pro painel.

### 16.2 Painel (Dashboard) — `/painel/`

**Arquivos:**
- [backend/blueprints/dashboard/routes.py](backend/blueprints/dashboard/routes.py)
- [backend/services/dashboard_service.py](backend/services/dashboard_service.py)
- [frontend/templates/dashboard/index.html](frontend/templates/dashboard/index.html)

Tela de entrada. 4 cards com KPIs lidos do banco (faturamento 30d,
receita líquida, peças em estoque, produção 30d) e atalhos rápidos.
A **receita líquida** = faturamento − despesas do período (ver 16.9).

### 16.3 Catálogo — `/catalogo/` (vitrine, somente leitura)

**Arquivos:**
- [backend/blueprints/catalogo/routes.py](backend/blueprints/catalogo/routes.py)
- [backend/services/catalogo_service.py](backend/services/catalogo_service.py)
- [backend/repositories/peca_repository.py](backend/repositories/peca_repository.py)
- [backend/models/peca.py](backend/models/peca.py)
- [frontend/templates/catalogo/index.html](frontend/templates/catalogo/index.html)

Vitrine: lista **só as peças com `quantidade_estoque > 0`**. 3 cards
(modelos disponíveis, peças em estoque, custo investido). Cada peça
mostra preço de venda, custo, lucro/margem e um `<details>` Materiais
que expande a tabela de materiais consumidos.

**Somente leitura** — o cadastro/edição/remoção da peça vive em
Produção (`/producao/pecas/...`, ver 16.5). A peça aparece aqui
automaticamente quando seu estoque fica > 0.

### 16.4 Matéria-prima — `/materiais/` (CRUD completo)

**Arquivos:**
- [backend/blueprints/materia_prima/routes.py](backend/blueprints/materia_prima/routes.py)
- [backend/services/materia_prima_service.py](backend/services/materia_prima_service.py)
- [backend/repositories/material_repository.py](backend/repositories/material_repository.py)
- [backend/models/material.py](backend/models/material.py)
- [frontend/templates/materia_prima/form.html](frontend/templates/materia_prima/form.html)

4 cards (cadastrados, em estoque saudável, em alerta, valor investido).
Faixa amarela no topo quando há materiais abaixo do mínimo. Lista de
materiais com badge "Estoque baixo" em vermelho e borda lateral amarela
nos que precisam de reposição.

**CRUD:** criar/editar/apagar com validação inline. Apagar material
que está em uso por uma peça é bloqueado com mensagem amigável.

**Cadastro por preço total:** o usuário **não digita** o preço por
unidade — informa o **total pago pelo lote** + a quantidade comprada.
O `valor_unitario` é calculado silenciosamente (`total / quantidade`)
e é o que alimenta `vw_peca_custo`. A listagem mostra "R$ X investidos"
(soma atual do estoque) no lugar de "R$ X / unidade". Ver
[ADR-012](#adr-012--produção-consome-matéria-prima--cadastro-por-preço-total).

### 16.5 Produção — `/producao/` (CRUD: criar / apagar)

**Arquivos:**
- [backend/blueprints/producao/routes.py](backend/blueprints/producao/routes.py)
- [backend/services/producao_service.py](backend/services/producao_service.py)
- [backend/repositories/producao_repository.py](backend/repositories/producao_repository.py)
- [backend/models/producao.py](backend/models/producao.py)
- [frontend/templates/producao/form.html](frontend/templates/producao/form.html)

4 cards (produções 30d, peças produzidas, peça mais produzida, custo total).
Lista de produções (data, peça, quantidade, custo) com observação
opcional como nota italicizada. Borda lateral laranja em cada registro.

**CRUD (sem editar — é histórico):** criar produção **soma** a quantidade
em `peca.quantidade_estoque` E **debita os materiais consumidos** da
receita (`qtd_producao × material_qty`), tudo na mesma transação. Antes
de gravar, o service checa se cada material tem estoque suficiente —
bloqueia com erro amigável se faltar. Apagar **subtrai da peça** e
**bloqueia** se o estoque ficaria negativo (peças já foram vendidas).
A matéria-prima **não retorna** ao estoque ao apagar — já foi consumida
fisicamente; o efeito é assimétrico em relação a criar, de propósito.
Ver [ADR-012](#adr-012--produção-consome-matéria-prima--cadastro-por-preço-total).

**Cadastro de peça (`/producao/pecas/nova` e `.../editar`):** a peça
nasce aqui. O formulário pede nome, **preço de venda sugerido**, estoque
inicial e a quantidade de cada material. O **custo de produção não é
digitado** — é a soma dos materiais, calculada pela view `vw_peca_custo`.
As listas de Produção e Catálogo mostram, por peça, custo, preço e
lucro/margem ([ADR-010](#adr-010--custo-da-peça-calculado-por-uma-view)).

### 16.6 Vendas — `/vendas/` (CRUD: criar / apagar)

**Arquivos:**
- [backend/blueprints/vendas/routes.py](backend/blueprints/vendas/routes.py)
- [backend/services/vendas_service.py](backend/services/vendas_service.py)
- [backend/repositories/venda_repository.py](backend/repositories/venda_repository.py)
- [backend/models/venda.py](backend/models/venda.py)
- [frontend/templates/vendas/form.html](frontend/templates/vendas/form.html)

4 cards (vendas 30d, faturamento, **lucro bruto**, ticket médio).
Lista de vendas ordenadas por data, com badge da forma de pagamento
(PIX, Dinheiro, Cartão crédito, Cartão débito) e borda lateral verde
("entrou dinheiro").

**Lucro bruto** = faturamento − soma(quantidade × `peca.custo_producao`).

**CRUD (sem editar):** criar venda **subtrai** quantidade do estoque
(bloqueada se sem estoque). Apagar **devolve** ao estoque. Forma de
pagamento validada contra lista fixa (PIX / Dinheiro / Cartão crédito /
Cartão débito).

### 16.7 Relatórios — `/relatorios/`

**Arquivos:**
- [backend/blueprints/relatorios/routes.py](backend/blueprints/relatorios/routes.py)
- [backend/services/relatorios_service.py](backend/services/relatorios_service.py)

**Sem repository próprio.** Consome `venda_repository.list_vendas()`
e agrega tudo em Python.

Conteúdo:
- 4 cards: faturamento, custo de produção, lucro bruto, margem%
- **Top 5 peças mais lucrativas** (ranking)
- **Distribuição por forma de pagamento** — usa `<meter>` HTML5 para
  barra de progresso (sem JS!)
- **Tabela detalhada por peça** com todas as colunas (vendas, qtd,
  faturamento, custo, lucro, margem)

### 16.8 Configurações — `/configuracoes/`

**Arquivos:**
- [backend/blueprints/configuracoes/routes.py](backend/blueprints/configuracoes/routes.py)
- [backend/services/configuracoes_service.py](backend/services/configuracoes_service.py)
- [backend/repositories/credencial_repository.py](backend/repositories/credencial_repository.py)
- [frontend/templates/configuracoes/index.html](frontend/templates/configuracoes/index.html)
- [frontend/templates/configuracoes/trocar_senha.html](frontend/templates/configuracoes/trocar_senha.html)

3 blocos:
1. **Sua conta** — usuário, tipo, **senha atualizada em** (vem de
   `admin_credencial.atualizado_em`) e botão "Trocar senha" que leva
   para `/configuracoes/trocar-senha`.
2. **Aplicação** — versão (`__version__`), ambiente, tempo de sessão,
   conexão segura (HTTPS) com badges visuais.
3. **Banco de dados** — badge **Ativo/Indisponível**, tamanho em KB
   e última atualização. Sem mais caminho de arquivo ou comando técnico.

**Trocar senha pela UI ([ADR-014](#adr-014--credencial-do-admin-no-banco-trocar-senha-pela-ui)):**
formulário em [trocar_senha.html](frontend/templates/configuracoes/trocar_senha.html)
pede senha atual + nova + confirmação digitada + checkbox de
confirmação explícita. Validação no `configuracoes_service.trocar_senha`:
senha atual confere, mínimo 8 caracteres, nova ≠ atual, confirmação
bate. Em caso de sucesso: grava o novo hash em `admin_credencial`,
desloga o usuário e redireciona pro `/auth/login` — relogin obrigatório
com a senha nova.

### 16.9 Despesas — `/despesas/` (CRUD: criar / apagar)

**Arquivos:**
- [backend/blueprints/despesas/routes.py](backend/blueprints/despesas/routes.py)
- [backend/services/despesas_service.py](backend/services/despesas_service.py)
- [backend/repositories/despesa_repository.py](backend/repositories/despesa_repository.py)
- [backend/models/despesa.py](backend/models/despesa.py)
- [frontend/templates/despesas/form.html](frontend/templates/despesas/form.html)

4 cards (despesas 30d, total gasto, despesa média, categoria que mais
pesa). Lista do histórico recente, com badge da categoria e borda
lateral vermelha ("saiu dinheiro").

**O que torna a despesa diferente de venda e produção:** ela é um
**registro puro**. Não tem `peca_id`, não tem chave estrangeira e não
mexe em nenhum estoque. Por isso o `despesa_repository` é o mais simples
do projeto — `criar()` é só um `INSERT` e `apagar()` é só um `DELETE`,
sem o UPDATE de estoque que produção e venda fazem ([ADR-007](#adr-007--efeitos-colaterais-no-estoque-produção-e-venda)).

**Escopo:** despesa é só **custo operacional/fixo fora do escopo de
produto** — aluguel, contas, marketing, etc. A matéria-prima da
produção NÃO entra aqui: ela tem o módulo dedicado `/materiais/`.

**CRUD (sem editar):** criar/apagar. A categoria é opcional e validada
contra a lista fixa em `despesas_service.CATEGORIAS` (Aluguel, Contas e
utilidades, Marketing, Transporte e frete, Ferramentas e equipamentos,
Embalagem, Taxas e tarifas, Outros) — mesma ideia das formas de
pagamento em Vendas.

**Ligação com o painel:** o total de despesas dos últimos 30 dias é o
que o `dashboard_service` subtrai do faturamento para chegar na
**receita líquida** real ([ADR-009](#adr-009--módulo-de-despesas-e-receita-líquida-real)).

---

## 17. CRUD — padrão dos formulários

CRUD significa as quatro operações básicas de manipulação de dados:

| Letra | Sigla     | Operação    | Verbo HTTP          |
|-------|-----------|-------------|---------------------|
| C     | Create    | Criar       | POST                |
| R     | Read      | Ler         | GET                 |
| U     | Update    | Atualizar   | POST                |
| D     | Delete    | Apagar      | POST                |

> Em apps que usam só HTML (sem JS), Update e Delete também viram POST
> porque o `<form>` HTML só suporta GET e POST. Frameworks que falam
> com APIs usariam PUT e DELETE, mas aqui não precisamos.

Os 4 módulos com CRUD seguem **exatamente o mesmo padrão**. Quem entender
um entende os outros.

### 17.1 Rotas — uma mesma função para GET e POST

Cada operação "criar" e "editar" usa **um único handler** que responde
GET (mostra o formulário) e POST (processa o envio):

```python
@bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    if request.method == "POST":
        require_csrf()
        erros, novo_id = service.criar(request.form)
        if erros:
            return render_template("modulo/form.html",
                                   modo="novo",
                                   erros=erros,
                                   valores=request.form)
        flash("Cadastrado.", "success")
        return redirect(url_for("modulo.index"))

    # GET — formulário vazio
    return render_template("modulo/form.html",
                           modo="novo", erros={}, valores={})
```

**Por que GET+POST na mesma função?**
- Menos código duplicado.
- A URL é a mesma na barra do navegador (`/materiais/novo`).
- Quando o form tem erro de validação, o template é re-renderizado
  com os mesmos campos que o usuário digitou + as mensagens de erro.

### 17.2 Validação — pattern `validar_form(form) → (erros, valores)`

Toda regra de validação vive no service, num formato único:

```python
def validar_form(form_data):
    erros = {}

    nome = (form_data.get("nome") or "").strip()
    if not nome:
        erros["nome"] = "Informe o nome."
    elif len(nome) > 80:
        erros["nome"] = "Nome muito longo (máx 80 caracteres)."

    valor = numero(form_data.get("valor_unitario"))
    if valor is None or valor < 0:
        erros["valor_unitario"] = "Valor deve ser ≥ 0."

    # ... uma validação por campo, sempre no mesmo padrão

    valores = {
        "nome": nome,
        "valor_unitario": valor or 0.0,
        # ...
    }
    return erros, valores
```

**Como ler:**
- `erros` é um dicionário `campo → mensagem`. Vazio = tudo válido.
- `valores` é um dicionário com os campos já convertidos (string em
  número, vírgula em ponto, etc.). Pronto pra ir ao banco.
- A rota decide o que fazer: se `erros` tem alguma coisa, re-renderiza
  o form com erros; se vazio, manda pro repository.

### 17.3 Conversões de tipo — helpers `numero()` / `inteiro()` / `data_iso()`

Forms HTML sempre mandam strings. Os 3 helpers compartilhados vivem em
[backend/services/form_helpers.py](backend/services/form_helpers.py) e
são importados por todos os services:

```python
# em qualquer service
from backend.services.form_helpers import numero, inteiro, data_iso

# uso
valor = numero(form_data.get("valor_unitario"))
```

A implementação de `numero`:

```python
def numero(raw):
    """String → float. Devolve None se vazio ou inválido. Aceita vírgula."""
    if raw is None:
        return None
    raw = str(raw).strip().replace(",", ".")   # 2,50 → 2.50
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None
```

**Detalhes importantes:**
- Aceita vírgula brasileira (`2,50` vira `2.50`).
- Devolve `None` em vez de explodir com erro — o chamador decide o
  que fazer (geralmente adiciona em `erros`).
- Existe `numero()`, `inteiro()` (sem vírgula), `data_iso()` (valida
  formato `YYYY-MM-DD`).
- **Por que num arquivo só?** Eram 5 cópias byte-a-byte iguais espalhadas
  pelos services. Extrair pra um módulo compartilhado é DRY clássico —
  qualquer ajuste futuro (ex.: aceitar `R$` no início) acontece em um
  lugar só.

### 17.4 Exibição dos erros no template

Cada campo tem o mesmo padrão de marcação:

```html
<div class="campo {% if erros.nome %}campo--erro{% endif %}">
  <label class="campo__label" for="nome">Nome</label>
  <input class="campo__input" type="text" name="nome" id="nome"
         value="{{ valores.nome|default('') }}" required maxlength="80" />
  {% if erros.nome %}
    <span class="campo__erro">{{ erros.nome }}</span>
  {% endif %}
</div>
```

**Repare:**
- `value="{{ valores.nome|default('') }}"` mantém o que o usuário digitou
  mesmo quando há erro (não força a redigitar tudo).
- A classe `campo--erro` ativa estilos vermelhos no CSS (borda vermelha
  no input).
- A mensagem específica aparece logo abaixo do campo, com a classe
  `campo__erro`.

Todo o estilo desses formulários vive em
[frontend/static/css/forms.css](frontend/static/css/forms.css),
**compartilhado pelos 4 módulos**.

### 17.5 Apagar — POST + CSRF (nunca GET)

Apagar é uma ação **destrutiva**. Ações destrutivas **nunca** podem ser
GET, porque qualquer link com aquela URL apagaria o registro. Sempre
POST com CSRF:

```html
<form method="POST"
      action="{{ url_for('modulo.apagar', item_id=item.id) }}">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
  <button type="submit" class="btn btn--ghost">Apagar</button>
</form>
```

E na rota:

```python
@bp.route("/<int:item_id>/apagar", methods=["POST"])
@login_required
def apagar(item_id):
    require_csrf()
    erro = service.apagar(item_id)
    if erro:
        flash(erro, "error")
    else:
        flash("Removido.", "success")
    return redirect(url_for("modulo.index"))
```

O service decide se pode apagar e devolve a mensagem de erro
(string) ou `None`. Exemplos de regras:
- Material em uso por uma peça → não apaga.
- Peça com vendas registradas → não apaga (registro fiscal).
- Apagar produção que tornaria estoque negativo → não apaga.

### 17.6 Transações atomáticas — quando criar/apagar muda mais de uma tabela

Algumas operações precisam mexer em mais de uma tabela ao mesmo tempo.
Exemplos:
- Criar produção → INSERT em `producao` + UPDATE em `peca.quantidade_estoque`.
- Criar venda → INSERT em `venda` + UPDATE em `peca.quantidade_estoque`.
- Atualizar peça → UPDATE em `peca` + DELETE/INSERT em `peca_material`.

O SQLite agrupa tudo numa **transação**: ou os dois SQLs gravam, ou
nenhum grava. Padrão no repositório:

```python
def criar(peca_id, quantidade, data, observacao):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO producao (peca_id, quantidade, data, observacao) "
        "VALUES (?, ?, ?, ?)",
        (peca_id, quantidade, data, observacao),
    )
    db.execute(
        "UPDATE peca SET quantidade_estoque = quantidade_estoque + ? "
        "WHERE id = ?",
        (quantidade, peca_id),
    )
    db.commit()       # ← só aqui os dois SQLs viram permanentes
    return cursor.lastrowid
```

Se a segunda query falhar antes do `commit()`, o INSERT da primeira
é descartado automaticamente (rollback automático do sqlite3).

### 17.7 Efeitos no estoque — resumo

| Operação           | `peca.quantidade_estoque`           | Bloqueado quando…              |
|--------------------|-------------------------------------|--------------------------------|
| Criar produção     | `+= quantidade`                     | nunca (sempre OK)              |
| Apagar produção    | `-= quantidade`                     | ficaria negativo (peças já foram vendidas) |
| Criar venda        | `-= quantidade`                     | `quantidade > estoque atual`   |
| Apagar venda       | `+= quantidade`                     | nunca (sempre OK)              |

### 17.8 Estado do form em caso de erro

Quando o form é re-renderizado com erros, ele precisa **lembrar do que
o usuário digitou** (não pode zerar). Por isso passamos `valores=request.form`:

```python
return render_template("modulo/form.html",
                       modo="novo",
                       erros=erros,
                       valores=request.form)   # ← os valores digitados
```

`request.form` é o `MultiDict` do Flask com os campos enviados.
No template, `valores.nome` retorna o que veio do form.

Caso especial: **edição** carrega valores do banco no GET. Esses valores
às vezes precisam de formatação leve antes (ex.: float `2.0` → string `"2"`
para ficar bonito no input). Isso é feito no route com `f"{x:g}"`.

### 17.9 Pra que serve cada arquivo num CRUD

Para entender qualquer CRUD, abrir esses 5 arquivos lado a lado:

| Camada     | Arquivo                                | Responsável por                         |
|------------|----------------------------------------|----------------------------------------|
| Blueprint  | `backend/blueprints/<modulo>/routes.py` | Decide qual handler chamar (GET/POST) |
| Service    | `backend/services/<modulo>_service.py`  | Valida + chama o repository           |
| Repository | `backend/repositories/<modulo>_repository.py` | Roda o SQL na transação         |
| Model      | `backend/models/<modulo>.py`            | Define a estrutura dos dados          |
| Template   | `frontend/templates/<modulo>/form.html` | Mostra o form (criar/editar)          |

---

## 18. HTML semântico sem JavaScript

O projeto não usa JS principal. Pra coisas interativas, usamos tags
nativas do HTML5.

### `<details>` / `<summary>` — toggle expandir/recolher

Usado no Catálogo pra expandir a lista de materiais de cada peça:

```html
<details class="peca__materiais">
  <summary class="peca__materiais-toggle">Materiais</summary>
  <table class="materiais-tabela">
    <!-- ... -->
  </table>
</details>
```

Comportamento: clica em "Materiais" → expande. Clica de novo → recolhe.
**Tudo nativo do navegador, zero JS.**

Customização da setinha via CSS:

```css
.peca__materiais-toggle {
  list-style: none;                  /* esconde a setinha padrão */
}
.peca__materiais-toggle::-webkit-details-marker { display: none; }
.peca__materiais-toggle::before { content: "▸"; }
.peca__materiais[open] .peca__materiais-toggle::before { content: "▾"; }
```

`[open]` é o atributo que `<details>` ganha quando expandido.

### `<meter>` — barra de progresso

Usado em Relatórios pra mostrar % de cada forma de pagamento:

```html
<meter class="pagamento__barra"
       min="0" max="100" value="63.7"
       aria-label="Porcentagem do faturamento via PIX">
  63.7%
</meter>
```

Estilização cross-browser:

```css
.pagamento__barra {
  width: 100%; height: 10px;
  appearance: none; -webkit-appearance: none;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 999px;
}
.pagamento__barra::-webkit-meter-bar { background: var(--color-bg); }
.pagamento__barra::-webkit-meter-optimum-value { background: var(--color-primary); }
.pagamento__barra::-moz-meter-bar { background: var(--color-primary); }
```

Cada navegador usa um pseudo-elemento diferente — daí os vendor prefixes.

### `<form>` + POST + CSRF — ações destrutivas

Sempre que uma ação **modifica/apaga** algo, é POST com CSRF:

```html
<form method="POST" action="{{ url_for('catalogo.apagar', peca_id=peca.id) }}">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
  <button type="submit" class="btn btn--ghost">Apagar</button>
</form>
```

GET não pode mudar estado — só leitura. Quem clica em link não
deveria deletar nada.

---

## 19. Decisões registradas (ADRs)

Documentadas em [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md).

### ADR-001 — Sem ORM na Etapa 1
Usar `sqlite3` da stdlib via repositórios.
**Motivo:** domínio simples, SQL didático, sem dependência extra,
fácil migrar pra SQLAlchemy depois sem mudar o resto.

### ADR-002 — Senha do admin como hash em `.env`
Armazenar `ADMIN_PASSWORD_HASH` (não a senha em texto puro).
**Motivo:** se o `.env` vazar, ainda há custo computacional pra
recuperar a senha.

### ADR-003 — CSRF manual antes de Flask-WTF
Token CSRF próprio em `security.py` (em vez de instalar Flask-WTF).
**Motivo:** zero dependências adicionais, padrão estabelecido pros
próximos forms. Flask-WTF entra quando precisar de validação de
campos mais complexa.

### ADR-004 — Sidebar com links desabilitados
Módulos futuros apareciam na sidebar com classe `is-disabled` e
`pointer-events: none`.
**Motivo:** usuário enxergava o mapa do sistema desde o dia 1, sem
404. *(Já não se aplica — todos os links estão funcionais agora.)*

### ADR-005 — Separação em `backend/`, `frontend/`, `database/`
Três pacotes raiz em vez de um único `app/`.
**Motivo:** torna óbvio onde mexer. Reduz fricção ao crescer.
Flask aponta `template_folder`/`static_folder` explicitamente para
`frontend/`, e `DATABASE_PATH` aponta para `database/atoriart.sqlite3`.

### ADR-006 — Padrão único de validação `validar_form()`
Todo service expõe uma função `validar_form(form_data, ...)` que
devolve `(erros, valores)`. `erros` vazio = válido.
**Motivo:** padrão único, sem dependência de Flask-WTF. O estudante lê
o código de validação de cima pra baixo sem indireções. Helpers
`numero()`, `inteiro()`, `data_iso()` (em `backend/services/form_helpers.py`) cuidam das conversões e aceitam
vírgula decimal brasileira.

### ADR-007 — Efeitos colaterais no estoque (produção e venda)
Criar/apagar produções e vendas mexe automaticamente em
`peca.quantidade_estoque` **na mesma transação SQLite** do INSERT/DELETE.
Bloqueia operações que deixariam estoque negativo.
**Motivo:** estoque sempre consistente sem precisar de rotina externa
de recálculo. SQLite garante atomicidade nativamente: ou os dois SQLs
gravam, ou nenhum grava.
**Trade-off original:** produção não consumia
`material.quantidade_estoque` na primeira versão — só mexia na peça.
**Resolvido em [ADR-012](#adr-012--produção-consome-matéria-prima--cadastro-por-preço-total):**
produção agora debita os materiais consumidos na mesma transação.

### ADR-009 — Módulo de Despesas e receita líquida real
`despesa` é uma tabela **sem chave estrangeira** e **sem efeito no
estoque** — um registro puro. Com o módulo no ar, o `dashboard_service`
passou a calcular `receita_liquida = faturamento − despesas`.
**Motivo:** despesa é um custo do negócio que não se liga a nenhuma
peça ou material, então não cabe a ela o padrão do ADR-007 — criar e
apagar são INSERT/DELETE simples. Antes deste módulo, o card "Receita
líquida" do painel mostrava na verdade o lucro bruto das vendas; o
rótulo "Faturamento menos despesas" só virou verdade agora.

### ADR-010 — Custo da peça calculado por uma view
O `custo_producao` da peça não é coluna nem é digitado: é a soma
`quantidade × valor_unitario` dos materiais, calculada pela view SQL
`vw_peca_custo`. O usuário digita só o `preco_venda` (preço sugerido).
**Motivo:** custo é dado **derivado** — guardá-lo numa coluna deixaria
ele velho quando o preço de um material mudasse. A view é fonte única
da fórmula; `peca`, `venda` e `producao` fazem `LEFT JOIN` nela. Mesmo
princípio das `@property` dos models: valor derivado se calcula.

### ADR-012 — Produção consome matéria-prima + cadastro por preço total
Estende o ADR-007: criar produção debita os materiais consumidos
(`qtd × material_qty`) no mesmo `commit()` do INSERT da produção e do
UPDATE da peça. O `producao_service` checa o estoque dos materiais
antes de gravar e bloqueia com erro amigável se faltar.
**Apagar é assimétrico:** retira as peças do estoque mas **não devolve
a matéria-prima** — material já foi fisicamente consumido, então o
registro some mas o consumo permanece.
E o **cadastro de matéria-prima** agora recebe o **preço total pago**
+ a quantidade — o `valor_unitario` é calculado silenciosamente
(`total / quantidade`) e nunca aparece na UI. A listagem mostra o
"investido" (`unit × estoque`) no lugar do preço por unidade.
**Motivo:** o usuário pensa em totais ("gastei R$ X pelo lote"), não em
preço por unidade. E debitar matéria-prima na produção é o que fecha o
ciclo material → peça → venda de verdade. A assimetria do apagar
combina com a física: insumo gasto não volta.
**Trade-off:** corrigir uma produção lançada errada requer ajustar
o estoque do material à mão antes de relançar — apagar não devolve
o insumo. Aceitável porque combina com a realidade.

### ADR-013 — Snapshot de custo na produção para custo investido histórico
O card "Custo investido" do Catálogo e da Produção usava
`Σ peca.custo_producao × peca.quantidade_estoque` — caía a cada venda
porque o estoque diminuía. **Decisão:** a tabela `producao` ganhou
`custo_unitario REAL NOT NULL DEFAULT 0`, snapshot do custo da peça
(lido de `vw_peca_custo`) no momento exato do INSERT. O card passa a
vir de `producao_repository.custo_total_investido()`:
```sql
SELECT COALESCE(SUM(quantidade * custo_unitario), 0) FROM producao
```
**Por que snapshot e não recalcular?** A `vw_peca_custo` reflete os
preços *atuais* dos materiais. Sem snapshot, mudar o preço de um material
alteraria retroativamente o custo de produções passadas — comportamento
errado. O snapshot congela o custo no momento real da fabricação.
**Efeito por operação:** criar produção sobe o total; apagar produção
desce (o registro some); vender peça não toca `producao` → total não muda
✓; mudar preço de material não toca registros passados ✓.

### ADR-014 — Credencial do admin no banco; trocar senha pela UI
A senha estava só no `.env` — impossível trocar pela interface
(reescrever `.env` é frágil, e no Render o filesystem é efêmero).
**Decisão:** mover a credencial pra tabela `admin_credencial`
(`username`, `password_hash`, `atualizado_em`). O `.env` continua sendo
o **seed inicial**: no primeiro boot, `_apply_migrations` cria a tabela
e copia o hash do `.env` quando está vazia. Depois, a tabela vira a
fonte de verdade — `authenticate()` lê dela; trocar senha pela UI grava
ali.
**Fluxo de troca:** senha atual (verificada com `check_password_hash`)
+ nova senha + confirmação digitada + checkbox de confirmação +
mínimo 8 caracteres + nova ≠ atual. Em caso de sucesso, gera novo hash
com `generate_password_hash`, atualiza o banco, faz `logout_session()`
e redireciona pro login.
**Trade-off:** se o banco for resetado, a senha volta ao hash do `.env`.
Para persistência real, configurar disco persistente no Render
(ou migrar pra Postgres).

### ADR-015 — Rota `/ping` anti-suspend (em `run.py`, fora dos blueprints)
O free tier do Render hiberna a app após ~15 min sem tráfego. Pra
contornar até subirmos pra plano pago, declaramos `GET /ping` direto no
`run.py`:
```python
@app.route("/ping")
def ping():
    return {"status": "ok"}, 200
```
Um pinger externo (UptimeRobot, BetterUptime...) bate nele a cada ~14 min
e a app não dorme.
**Motivo de quebrar o padrão:** é **temporário**, com sunset claro.
Quanto mais isolado e óbvio, mais fácil deletar depois. Em `run.py` é
um arquivo só, com um comentário em cima sinalizando "REMOVER quando
subir pra plano pago". Se virasse blueprint `health/`, espalharia
arquivos e registros pra remover.
**Exceção pontual:** **toda outra rota permanente continua indo em
`backend/blueprints/<modulo>/routes.py`**. Esta é a única.

---

## 20. Como rodar o projeto

### Primeira vez

```bash
cd "Projeto AtoriArt"

# 1. Criar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate         # macOS/Linux
# .venv\Scripts\activate          # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Criar .env a partir do exemplo
cp .env.example .env

# 4. Gerar SECRET_KEY e colar no .env
python -c "import secrets; print(secrets.token_hex(32))"

# 5. Gerar hash da senha do admin
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('SuaSenhaForte'))"

# 6. Criar o banco (use --com-exemplos p/ popular com dados de teste)
python database/init_db.py --com-exemplos

# 7. Subir o servidor
python run.py
# Acessar http://127.0.0.1:5000
```

### Resetar o banco a qualquer momento

```bash
python database/init_db.py                  # recria vazio
python database/init_db.py --com-exemplos   # recria com dados de exemplo
```

Apaga as tabelas e recria do zero. **Atenção:** perde todos os dados.

### Estrutura do `.env` (referência)

```bash
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=<32-bytes-hex>
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<werkzeug-hash>
SESSION_LIFETIME_MINUTES=60
SESSION_COOKIE_SECURE=0
```

---

## 21. Glossário

| Termo                  | Significado                                                  |
|------------------------|--------------------------------------------------------------|
| **Blueprint**          | Grupo de rotas relacionadas em Flask                         |
| **Application factory**| Função que cria a instância do Flask                         |
| **`g` (Flask)**        | Objeto-cache que vive durante 1 request                      |
| **`session` (Flask)**  | Dicionário cripto-assinado guardado em cookie                |
| **CSRF**               | Cross-Site Request Forgery — ataque que `csrf_token` previne |
| **CSP / Headers**      | Cabeçalhos HTTP que dão pistas de segurança ao navegador     |
| **ORM**                | Object-Relational Mapping (ex.: SQLAlchemy). Não usamos.     |
| **ViewModel**          | Estrutura de dados pronta pro template exibir                |
| **Dataclass**          | Classe Python que só carrega dados (decorador `@dataclass`)  |
| **JOIN**               | Comando SQL que junta linhas de duas ou mais tabelas         |
| **View (SQL)**         | "Tabela virtual": consulta salva com nome, usada como tabela |
| **PRAGMA**             | Comando SQLite pra ligar/desligar comportamentos             |
| **FK (Foreign Key)**   | Coluna que referencia o ID de outra tabela                   |
| **CASCADE**            | Apagar o pai apaga os filhos automaticamente                 |
| **RESTRICT**           | Bloqueia apagar o pai se houver filhos                       |
| **Seed**               | Dados de exemplo inseridos na primeira criação do banco      |
| **BEM**                | Block / Element / Modifier — convenção pra nomear classes CSS|
| **Vendor prefix**      | `-webkit-`, `-moz-` — prefixos que cada navegador exige      |
| **Idempotente**        | Rodar várias vezes dá o mesmo resultado (ex.: schema.sql)    |
| **Hash**               | Função que transforma senha em código irreversível           |
| **`hmac.compare_digest`** | Comparação em tempo constante (defesa contra timing attack) |
| **Open redirect**      | Redirecionar pra URL externa controlada pelo atacante        |
| **Placeholder route**  | Rota que existe mas só responde "em desenvolvimento"         |
| **CRUD**               | Create / Read / Update / Delete — as 4 operações de dado     |
| **Transação**          | Grupo de SQLs que viram permanentes juntos (ou nenhum)       |
| **Atomicidade**        | "Tudo ou nada" — a propriedade que torna transações seguras  |
| **Commit / Rollback**  | Persiste / descarta as mudanças da transação atual           |
| **Validação server-side** | Conferir os dados do form no Python, não confiar no HTML  |
| **Helper**             | Função utilitária privada do módulo (prefixo `_`)            |
| **Denormalização**     | Repetir um dado em outro lugar pra evitar JOIN na leitura    |
| **MultiDict**          | `request.form` do Flask — dicionário que aceita chaves repetidas |

---

## Notas finais

- **Quando algo der erro**, lembra do fluxo: HTTP → Blueprint → Service →
  Repository → Model. Saber em qual camada está o problema acelera o
  debug.
- **Quando for adicionar uma nova página**, replica o padrão: 1 blueprint
  + 1 service + (opcionalmente 1 repository + 1 model) + 1 template
  + 1 CSS. Registra o blueprint em `backend/__init__.py`. Ativa o link
  no sidebar.
- **Quando for criar uma nova tabela**, acrescenta no `database/schema.sql`,
  o seed em `database/init_db.py`, e cria um repository pra essa tabela.
  Roda `python database/init_db.py` pra aplicar.
- **Quando for adicionar CRUD a uma nova entidade**, copia o padrão de
  qualquer dos 4 módulos existentes (matéria-prima é o mais simples):
  - Repository: `criar()`, `atualizar()`, `apagar()` com SQL parametrizado.
  - Service: `validar_form()` retornando `(erros, valores)`, e
    `criar()`, `atualizar()`, `apagar()` orquestrando.
  - Routes: rotas com método GET+POST no mesmo handler.
  - Template `form.html` herdando `base.html` e carregando `forms.css`.
- **Quando uma operação mexer em mais de uma tabela**, faz tudo no mesmo
  repository, dentro de uma só chamada com um único `db.commit()` ao
  final. SQLite garante atomicidade. Ver
  [`producao_repository.criar()`](backend/repositories/producao_repository.py)
  e [`venda_repository.criar()`](backend/repositories/venda_repository.py).
- **Pra rever uma decisão**, abre `PROJECT_CONTEXT.md` — os ADRs estão lá.

Esse projeto foi construído incrementalmente, etapa por etapa, sempre
priorizando código limpo e arquitetura clara. A mesma disciplina vale
pras próximas etapas (filtros de período, troca de senha pela interface,
baixa automática de matéria-prima, etc.).

# PROJECT_CONTEXT.md — AtoriArt

> **Para Claude (e qualquer dev novo):** este é o documento oficial de
> contexto do projeto. **Leia este arquivo antes de qualquer alteração.**
> Ele descreve stack, arquitetura, convenções, decisões e estado atual.
> Atualize-o ao final de cada etapa.

---

## 1. O que é o AtoriArt

Sistema web administrativo de **gestão de estoque para artesanato**. Cliente
única, sem cadastro público, apenas um administrador autenticado. Será
publicado na internet, então segurança é prioridade desde a Etapa 1.

**Domínio (visão geral, será detalhado por etapa):**
- **Catálogo** — vitrine: lista apenas peças com `quantidade_estoque > 0`
  (disponíveis para venda). Somente leitura.
- **Produção** — controle de estoque + cadastro/edição de peças + log
  de produções. Peça "nasce" aqui.
- Matéria-prima em estoque (com mínimos para alerta).
- Vendas (faturamento bruto).
- Despesas (para cálculo de receita líquida).
- Relatórios.
- Configurações.

---

## 2. Stack obrigatória

| Camada        | Tecnologia                       |
|---------------|----------------------------------|
| Backend       | Python 3.10+ / Flask 3.x         |
| Frontend      | HTML + CSS + Jinja2              |
| Banco         | SQLite (módulo `sqlite3` stdlib) |
| Config        | python-dotenv                    |
| Segurança     | werkzeug.security, hmac, secrets |

**Proibido nesta arquitetura:**
- JavaScript como tecnologia principal de frontend (pequenos enhancements ok
  depois, somente se necessário).
- Frameworks de frontend (React, Vue, etc.).
- Outros bancos (Postgres, MySQL, etc.).
- ORMs além de `sqlite3` (SQLAlchemy só com aprovação explícita do dono).
- CSS inline em templates.
- Regra de negócio em template Jinja.

---

## 3. Arquitetura

### 3.1 Camadas e responsabilidades

```
HTTP request
   ↓
Blueprint (controller)   ← apenas roteamento, parsing de form, redirect
   ↓
Service                  ← regras de negócio, monta ViewModel
   ↓
Repository               ← SQL bruto contra SQLite
   ↓
Model (dataclass)        ← entidade do domínio
```

**Regra de ouro:**
- Blueprint pode importar `services`, `security`. NÃO importa repositórios
  ou SQL.
- Service pode importar `repositories`, `models`. Não conhece Flask.
- Repository conhece SQL. Não conhece HTTP nem regra.
- Model é dataclass pura. Sem dependências internas.
- Template **só exibe**. Recebe ViewModel pronto. Nada de regra ou
  formatação não-trivial — formatação pesada deve vir do service.

### 3.2 Estrutura de pastas (atual)

Separação em três pacotes raiz: **backend/** (Python/Flask), **frontend/**
(Jinja + CSS) e **database/** (SQLite e scripts de dados). O Flask em
`backend/__init__.py` aponta `template_folder`/`static_folder` para
`frontend/` e a config aponta `DATABASE_PATH` para `database/`.

```
Projeto AtoriArt/
├── backend/                         # Tudo que é Python
│   ├── __init__.py                  create_app() + paths para frontend/
│   ├── config.py                    BaseConfig / Dev / Prod (lê .env)
│   ├── security.py                  login_required, autenticação, CSRF, trocar_senha
│   ├── blueprints/                  controllers HTTP (rotas)
│   │   ├── auth/routes.py           /auth/login, /auth/logout
│   │   ├── catalogo/routes.py       /catalogo/
│   │   └── dashboard/routes.py      /painel
│   ├── services/                    regras de negócio + ViewModels
│   │   ├── form_helpers.py          numero(), inteiro(), data_iso() — partilhados
│   │   ├── catalogo_service.py
│   │   └── dashboard_service.py
│   ├── repositories/                acesso ao banco (lê via database.db)
│   │   ├── credencial_repository.py
│   │   └── peca_repository.py
│   └── models/                      entidades de domínio (dataclasses)
│       └── peca.py
│
├── frontend/                        # Tudo que é apresentação
│   ├── templates/
│   │   ├── base.html
│   │   ├── _sidebar.html
│   │   ├── auth/login.html
│   │   ├── catalogo/index.html
│   │   └── dashboard/index.html
│   └── static/
│       ├── logo.jpeg
│       ├── uploads/.gitkeep         (fotos de peças vão aqui em runtime)
│       └── css/                     CSS por contexto
│
├── database/                        # Tudo que é banco
│   ├── __init__.py                  marca como pacote Python
│   ├── db.py                        get_db() / close_db() / init_app() / migrações
│   ├── schema.sql                   CREATE TABLE / CREATE VIEW
│   ├── init_db.py                   cria o .sqlite3 (--com-exemplos p/ seed)
│   └── atoriart.sqlite3             (gerado, gitignored)
│
├── .env / .env.example / .gitignore
├── requirements.txt
├── run.py                           ponto de entrada (local e Render) + /ping temporário
├── PROJECT_CONTEXT.md
└── README.md
```

Cada novo módulo (materia_prima, producao, vendas, despesas, relatorios,
configuracoes) replica o padrão entre os três pacotes:

```
backend/blueprints/<modulo>/__init__.py
backend/blueprints/<modulo>/routes.py
backend/services/<modulo>_service.py
backend/repositories/<modulo>_repository.py
backend/models/<modulo>.py
frontend/templates/<modulo>/...
frontend/static/css/<modulo>.css
database/schema.sql                    # acrescentar tabelas
database/init_db.py                    # acrescentar seed se útil
```

### 3.3 Application factory
- `create_app(config_class=None)` em `backend/__init__.py`.
- Calcula `FRONTEND_DIR` e passa `template_folder`/`static_folder`
  absolutos ao Flask — preserva a separação backend/frontend no disco.
- Chama `database.db.init_app(app)` para registrar o fechamento da
  conexão SQLite ao fim do request.
- Carrega `.env` em `config.py` (importação topo-de-módulo).
- Falha rápido se `SECRET_KEY` ausente.
- Garante que `database/` exista.
- Registra blueprints, context processors e headers de segurança.

### 3.4 Context globals (disponíveis em todo template)
- `current_user` — username do admin logado (ou `None`).
- `is_authenticated` — bool.
- `csrf_token()` — função que retorna o token CSRF da sessão.

---

## 4. Segurança

### 4.1 Variáveis de ambiente obrigatórias (`.env`)
- `SECRET_KEY` — assina cookies de sessão. **NÃO é a senha do admin.**
- `ADMIN_USERNAME` — usuário do admin (default: `admin`).
- `ADMIN_PASSWORD_HASH` — hash da senha via `werkzeug.security`.
- `SESSION_LIFETIME_MINUTES` — duração da sessão (default 60).
- `SESSION_COOKIE_SECURE` — `1` em produção (HTTPS), `0` em dev local.
- `FLASK_ENV` — `development` | `production`.

### 4.2 Como gerar
```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# ADMIN_PASSWORD_HASH
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('SuaSenhaForte'))"
```

### 4.3 Garantias atuais
- Senha armazenada como hash, nunca texto puro.
- Comparação de usuário em tempo constante (`hmac.compare_digest`).
- Sessão: `HttpOnly` + `SameSite=Lax` sempre; `Secure=True` em produção.
- Sessão expira após `PERMANENT_SESSION_LIFETIME`.
- CSRF token por sessão, validado em todo POST.
- Open redirect prevenido em `_safe_next` (login).
- Headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `Referrer-Policy: same-origin`.
- `@login_required` em toda rota interna.
- `.env`, `instance/*.sqlite*` no `.gitignore`.

### 4.4 A endereçar em produção
- Servir atrás de HTTPS obrigatório.
- Avaliar Flask-WTF para CSRF e validação de formulários mais robusta.
- Adicionar rate limiting no `/auth/login` (ex.: Flask-Limiter).
- Logar tentativas de login falhas.

---

## 5. Convenções de código

- **Idioma:** rotas, templates e mensagens em **português**. Código (nomes de
  função/variável internos) também em português quando o termo é do domínio
  (`pecas_em_estoque`, `faturamento_30d`) — manter consistência.
- **Imports:** absolutos (`from backend.security import ...`,
  `from database.db import ...`), nunca relativos.
- **Type hints:** usar `from __future__ import annotations` no topo dos
  módulos Python.
- **Dataclasses** para ViewModels e modelos.
- **CSS:** um arquivo por contexto (`base.css` global, depois um por tela);
  classes BEM-ish (`.sidebar__link.is-active`).
- **Templates:** herança via `{% extends "base.html" %}`; partials começam
  com `_` (`_sidebar.html`).
- **Sem JS** por padrão. Se precisar, justificar e adicionar arquivo isolado.

---

## 6. Estado atual

### Etapa 1 ✅ — Fundação
- Estrutura `backend/` + `frontend/` + `database/` + application factory.
- Login admin (1 usuário, hash de senha, CSRF, sessão segura).
- Dashboard com sidebar e cards mockados.

### Etapa 2 ✅ — Infra de banco
- `database/db.py` com `get_db()`/`close_db()`/`init_app()` usando
  `sqlite3` + Flask `g`.
- `database/schema.sql` com as tabelas atuais: `material`, `peca`,
  `peca_material`, `producao`, `venda`.
- `database/init_db.py`: cria/recria o banco e popula dados de exemplo
  com datas relativas a `date.today()`.

### Etapa 3 ✅ — Catálogo (listagem)
- Página `/catalogo/` com cards, lista ordenada de peças e bloco
  `<details>` de materiais por peça.

### Etapa 4 ✅ — Matéria-prima (listagem + estoque)
- Adicionado `quantidade_estoque` e `estoque_minimo` em `material`.
- Página `/materiais/` com 4 cards (cadastrados, saudável, alerta,
  valor investido) e alerta amarelo no topo quando há estoque baixo.
- Badge "Estoque baixo" + borda lateral amarela nos materiais em alerta.

### Etapa 5 ✅ — Produção (listagem)
- Tabela `producao` (peça, quantidade, data, observação).
- Página `/producao/` com 4 cards (produções 30d, peças produzidas,
  peça mais produzida, custo total) e lista ordenada por data.

### Etapa 6 ✅ — Vendas (listagem)
- Tabela `venda` com `forma_pagamento`.
- Página `/vendas/` com 4 cards (vendas 30d, faturamento, **lucro
  bruto**, ticket médio) e lista com badge da forma de pagamento.

### Etapa 7 ✅ — Relatórios
- Página `/relatorios/` consolida dados de vendas em 4 KPIs, top 5
  peças mais lucrativas, distribuição por forma de pagamento (com
  `<meter>` HTML5) e tabela detalhada por peça.
- **Sem repositório próprio** — consome `venda_repository`.

### Etapa 8 ✅ — Configurações
- Página `/configuracoes/` com 3 blocos: conta, aplicação, banco.
- `configuracoes_service` importa `current_app` (exceção arquitetural
  documentada — única).
- Constante `__version__ = "1.0.0"` em `backend/__init__.py`.

### Etapa 10 ✅ — Reorganização do fluxo Catálogo ↔ Produção
- **Catálogo virou vitrine:** mostra apenas peças com
  `quantidade_estoque > 0`. Sem botões de cadastro/edição/apagar.
  KPIs ajustados: modelos disponíveis, peças em estoque, custo investido.
- **Produção virou estoque + log:** topo lista o estoque atual
  (peças com qtd > 0) com cards de modelos/peças/custo investido e
  ações de editar/apagar peça; embaixo, histórico de produções dos
  últimos 30 dias.
- **Cadastro de peça migrou** de `/catalogo/nova` para
  `/producao/pecas/nova` (peça nasce na produção).
- Criado `peca_service.py` com `validar_form/criar/atualizar/apagar`.
- `catalogo_service` ficou só com `dados_catalogo()`.
- `peca_repository.list_pecas(apenas_em_estoque=False)` ganhou flag.

### Etapa 9 ✅ — CRUD nos 4 módulos
- **Matéria-prima:** criar, editar, apagar (bloqueia se em uso).
- **Catálogo:** criar/editar peça com seleção de materiais via
  inputs por material (apaga + reinsere `peca_material` em
  transação); bloqueia apagar peça com vendas históricas.
- **Produção:** criar/apagar; **toda criação SOMA `quantidade` em
  `peca.quantidade_estoque` na mesma transação**; apagar SUBTRAI e
  bloqueia se ficaria negativo (peças já vendidas).
- **Vendas:** criar/apagar; **toda criação SUBTRAI `quantidade` de
  `peca.quantidade_estoque`** (bloqueada se sem estoque); apagar
  devolve. Forma de pagamento validada contra lista fixa.
- Padrão único de validação: `validar_form(form)` → `(erros, valores)`
  em todos os services.
- Forms compartilham [frontend/static/css/forms.css](frontend/static/css/forms.css).

### Etapa 11 ✅ — Despesas
- Tabela `despesa` (descrição, categoria, valor, data). Registro **puro**:
  sem FK e sem efeito no estoque — diferente de produção e venda.
- Página `/despesas/` com 4 cards (despesas 30d, total gasto, despesa
  média, categoria que mais pesa) e lista do histórico recente.
- CRUD enxuto (criar/apagar, sem editar — mesmo padrão de Vendas).
- Categoria validada contra lista fixa em `despesas_service.CATEGORIAS` —
  **apenas custos operacionais/fixos** (aluguel, contas, marketing...).
  A matéria-prima da produção NÃO é despesa: tem módulo próprio
  (`/materiais/`).
- **Receita líquida virou real:** `dashboard_service` agora calcula
  `receita_liquida = faturamento − despesas` do período (antes usava
  o lucro bruto das vendas como aproximação). Ver [ADR-009](#adr-009--módulo-de-despesas-e-receita-líquida-real).

### Etapa 11.1 ✅ — Custo automático da peça + preço de venda
- O custo de produção da peça **deixou de ser digitado**: agora é
  derivado dos materiais que ela consome, via a view SQL `vw_peca_custo`
  (`Σ quantidade × valor_unitario`).
- O formulário da peça passou a pedir o **preço de venda sugerido**
  (`peca.preco_venda`) no lugar do antigo campo de custo.
- O model `Peca` ganhou as propriedades `lucro` (preço − custo) e
  `margem` (% sobre o preço). Catálogo e Produção exibem custo, preço
  e lucro de cada peça; o `<select>` de Vendas mostra o preço sugerido.
- Ver [ADR-010](#adr-010--custo-da-peça-derivado-dos-materiais-via-view).

### Etapa 11.2 ✅ — Foto de produto
- Coluna `foto TEXT` adicionada à tabela `peca` (guarda o nome do
  arquivo, não o binário). O campo é opcional — `NULL` quando sem foto.
- **Migração automática e não destrutiva:** `database/db.py` verifica
  via `PRAGMA table_info(peca)` se a coluna existe e aplica
  `ALTER TABLE peca ADD COLUMN foto TEXT` na inicialização, sem apagar
  dados existentes. O `schema.sql` também foi atualizado para novos
  bancos.
- Formulário de cadastro e edição de peça (`/producao/pecas/nova` e
  `.../editar`) ganhou `enctype="multipart/form-data"` e um campo
  `<input type="file">` opcional, com pré-visualização da foto atual
  no modo de edição.
- **Padronização do nome:** o arquivo é salvo com o padrão
  `YYYYMMDD_HHMMSS_<8hex>.<ext>` (ex.: `20260522_143022_a3f9b12c.jpg`),
  garantindo unicidade independente do nome original.
- **Armazenamento:** os arquivos ficam em `frontend/static/uploads/`
  (servidos diretamente pelo Flask como `static`). A pasta é criada
  automaticamente na primeira subida.
- **Exibição:** Catálogo e aba Produção (estoque atual) exibem a foto
  como thumbnail ao lado do nome da peça, quando disponível.
- **Rollback:** se o upload ocorrer mas a validação do form falhar,
  o arquivo salvo é removido antes de re-renderizar o form com erros.
  Ao editar com nova foto, a foto antiga é apagada do disco só após
  o `commit()` bem-sucedido.
- Extensões aceitas: `jpg`, `jpeg`, `png`, `gif`, `webp`.
- Ver [ADR-011](#adr-011--upload-de-fotos-de-produto).

### Etapa 11.4 ✅ — Custo investido histórico (vitrine)

**Problema corrigido:** o card "Custo investido" do Catálogo calculava
`Σ custo_producao × quantidade_estoque`, então diminuía a cada venda —
o custo desaparecia junto com o estoque vendido.

**Solução (ADR-013):** a tabela `producao` ganhou a coluna
`custo_unitario REAL NOT NULL DEFAULT 0`, que grava um **snapshot** do
custo da peça (via `vw_peca_custo`) no momento exato do INSERT. O
`custo_investido` do Catálogo passa a ser calculado por
`producao_repository.custo_total_investido()` —
`SELECT SUM(quantidade * custo_unitario) FROM producao` —
valor que só cresce com novas produções e nunca diminui com vendas.

**Migration automática:** `database/db.py._apply_migrations` detecta a
ausência da coluna, aplica `ALTER TABLE producao ADD COLUMN custo_unitario`
e faz backfill dos registros já existentes com o custo atual da view
(melhor aproximação disponível para o histórico pré-migração).

**Follow-up:** o card equivalente na página de Produção
(`/producao/`) ficou inicialmente com a fórmula antiga; foi corrigido
no commit `dacfcdc` para também usar `producao_repository.custo_total_investido()`
— agora Catálogo e Produção mostram o mesmo número estável.

### Etapa 13 ✅ — Trocar senha pela interface + Configurações em produção
- **Credencial migrada do `.env` para o banco** (tabela `admin_credencial`,
  com `username`, `password_hash`, `atualizado_em`). No primeiro boot,
  `database/db.py._apply_migrations` cria a tabela e faz seed com o hash
  do `.env`. A partir daí, a tabela é a fonte de verdade. Ver [ADR-014](#adr-014--credencial-do-admin-no-banco-trocar-senha-pela-ui).
- **Novo repositório:** `backend/repositories/credencial_repository.py`
  (`get_password_hash`, `atualizar_senha`).
- **`backend/security.py` ganhou `trocar_senha(username, senha_atual, senha_nova)`**
  — verifica a senha atual com `check_password_hash` antes de gerar e
  gravar o novo hash. `authenticate()` agora lê o hash do banco.
- **Fluxo da UI** (`/configuracoes/trocar-senha`, GET+POST):
  pede senha atual + nova + confirmação digitada + checkbox de
  confirmação explícita ("Confirmo que quero trocar minha senha…").
  Validações: senha atual confere, mínimo 8 caracteres, nova ≠ atual,
  confirmação bate. Em caso de sucesso: `logout_session()` + redirect
  pro `/auth/login` com flash de sucesso — força relogin com a senha nova.
- **Removido o botão "Resetar banco"** da página e a rota
  `/configuracoes/resetar-banco`: não faz sentido com a app em produção
  na nuvem (filesystem efêmero do Render); seria perigoso e sem efeito útil.
- **Página de Configurações em modo produção:** removida a exibição do
  caminho do arquivo SQLite e a nota "rode `python database/init_db.py`",
  banco passou a mostrar badge **Ativo/Indisponível**, sessão "Cookie
  seguro" virou "Conexão segura (HTTPS) Ativa/Desligada", a seção
  "Sua conta" passou a mostrar **Senha atualizada em** (lido de
  `admin_credencial.atualizado_em`).
- **Limpeza de copy técnica:** o estado vazio de `/materiais/` deixou
  de instruir a rodar comando — agora orienta o botão "Registrar material".

### Etapa 11.3 ✅ — Consumo de matéria-prima + cadastro por preço total
- **Consumo automático:** registrar produção agora **debita** os materiais
  da receita da peça (`quantidade_producao × material_qty`) na mesma
  transação do INSERT da produção e do UPDATE do estoque da peça.
  Estende o [ADR-007](#adr-007--efeitos-colaterais-no-estoque-produção-e-venda)
  para a tabela `material` — resolve o trade-off original dele.
- **Apagar produção é assimétrico:** retira as peças do estoque mas
  **não devolve a matéria-prima** — material já foi fisicamente
  consumido, não dá pra "des-produzir".
- **Bloqueio antecipado:** `producao_service.criar` checa se cada material
  tem estoque suficiente antes de gravar; se algum falta, retorna erro
  amigável listando os faltantes (ex.: "precisa 8 un, tem 6").
- **Cadastro por preço total:** o form de matéria-prima passou a receber
  o **preço total pago pelo lote** + a quantidade comprada. O
  `valor_unitario` é calculado silenciosamente (`total / quantidade`) e
  é o que continua alimentando a view `vw_peca_custo`. O preço por
  unidade não aparece em UI nenhuma — só o "investido" (`unit × estoque`).
- Property `valor_estoque` adicionada ao model `Material`; listagem de
  matéria-prima mostra "R$ X investidos" no lugar de "R$ X / unidade".
- Ver [ADR-012](#adr-012--produção-consome-matéria-prima--cadastro-por-preço-total).

### Etapa 14 ✅ — Limpeza de código (DRY, dead files, copy)
- **Helpers `numero`, `inteiro`, `data_iso` extraídos** para
  [backend/services/form_helpers.py](backend/services/form_helpers.py)
  e importados por todos os 5 services que faziam `validar_form`. Antes
  estavam duplicados (palavra por palavra) em cada arquivo. Os nomes
  perderam o `_` privado porque agora são API pública compartilhada.
- **`backend/extensions.py` removido:** era um placeholder vazio sem
  nenhum import — espaço pra extensões Flask que nunca foram adicionadas.
  Removível sem efeito colateral.
- **Docstrings obsoletas atualizadas** em `database/db.py` e `run.py` —
  não pedem mais pra rodar `python database/init_db.py` na primeira vez,
  já que o `run.py` faz auto-create.
- **README:** seção nova "Deploy no Render" com env vars necessárias e
  o trade-off do filesystem efêmero. "Estado atual" e "Próximas etapas"
  atualizados pra refletir o que de fato sobrou no backlog.

### Etapa 15 ✅ — Filtro por mês + Lucro líquido nos Relatórios

**Filtro de período por mês:**
- Novo `<select>` no painel de filtros do `/relatorios/` lista os meses
  que têm pelo menos uma venda ou despesa registrada (ex.: "Maio/2026").
- Default mantido: "Últimos 30 dias" (janela rolante).
- Mês específico filtra todas as agregações daquele mês inteiro
  (`2026-05-01` a `2026-05-31`) — vendas, custos, despesas e os 3
  recortes (matéria-prima, forma de pagamento, peça).
- Helper centralizado `_periodo(mes)` em `relatorios_service` devolve
  `(desde, ate, label)` — uma única fonte da regra de período.
- Query `meses_disponiveis()` faz `SELECT DISTINCT strftime('%Y-%m', data)`
  unindo vendas e despesas, ordenando do mais recente.

**Lucro líquido substituindo Margem:**
- O 4º card do consolidado mudou de "Margem (%)" para
  **"Lucro líquido (R$)"** — `faturamento − custo de produção − despesas`
  do período. É o "dinheiro no bolso" depois de TUDO.
- Card mostra também as despesas subtraídas como hint:
  *"Lucro bruto − despesas (R$ X,XX)"*.
- Margem continua aparecendo no ranking por peça e na tabela de
  detalhamento, onde tem sentido contextual.

**Impacto na arquitetura:**
- `venda_repository.list_vendas(desde, ate)` e
  `despesa_repository.list_despesas(desde, ate)` ganharam o segundo
  argumento `ate` (backward-compat: ambos defaults `None`). Continua
  filtrando só por `desde` se quem chama não passar `ate`.
- Service ficou com **uma só regra de período** (`_periodo`) usada
  por consolidado e pelos 3 recortes — antes cada `dados_por_*`
  calculava o `desde` localmente.

**Não entregue (intencionalmente):**
- Filtro arbitrário (7d / 90d / range custom) — abriria muita
  combinação pra pouca demanda. Mês + últimos 30d cobre o caso real.
- Persistência confiável no Render (disco persistente ou Postgres) —
  trade-off conhecido do free tier do Render, documentado no README.

### Etapa 16 ✅ — Peça exige matéria-prima (UX guard + defesa server-side)

**Regra de negócio:** uma peça **não pode existir sem pelo menos um
material**, porque o custo de produção dela é derivado dos materiais
(view `vw_peca_custo`). Sem material, custo = 0 → lucro líquido distorce
e a peça vira um item órfão no catálogo.

**Defesa em duas camadas:**
1. **UX guard na blueprint** ([producao/routes.py](backend/blueprints/producao/routes.py)):
   o `GET /producao/pecas/nova` agora consulta `material_repository.list_materiais()`
   antes de renderizar o form. Se a lista voltar vazia:
   ```python
   flash("Cadastre pelo menos um material antes de criar uma peça...", "error")
   return redirect(url_for("materia_prima.novo"))
   ```
   O usuário é levado direto para a tela de cadastrar matéria-prima, com
   a mensagem explicando o porquê — sem ver um formulário inútil.

2. **Validação no service** ([peca_service.validar_form](backend/services/peca_service.py)):
   `if not materiais_selecionados: erros["materiais"] = "Selecione ao menos um material para a peça."`
   Vale para qualquer POST — criar ou editar, vindo da UI ou direto.
   Antes a validação só disparava quando `materiais_disponiveis` tinha
   conteúdo; agora é incondicional, o que torna o service auto-suficiente
   (não depende da blueprint pra ser correto).

**Por que as duas?** Defense in depth. A blueprint melhora a UX
(redireciona em vez de mostrar formulário furado). O service garante a
regra mesmo se alguém POSTar direto, fizer testes automatizados ou
adicionar outra rota no futuro. Cada camada faz seu trabalho sem
duplicar lógica.

| Etapa | Tema                          | Status                                              |
|-------|-------------------------------|-----------------------------------------------------|
| 1     | Fundação                      | App factory, login, dashboard mockado ✅             |
| 2     | Banco e infraestrutura        | `db.py`, `schema.sql`, `init_db.py` ✅               |
| 3     | Catálogo (listagem)           | Página `/catalogo/` ✅                               |
| 4     | Matéria-prima (listagem)      | Página `/materiais/` com alerta de estoque ✅        |
| 5     | Produção (listagem)           | Página `/producao/` ✅                               |
| 6     | Vendas (listagem)             | Página `/vendas/` com lucro bruto ✅                 |
| 7     | Relatórios                    | Página `/relatorios/` com `<meter>` ✅               |
| 8     | Configurações                 | Página `/configuracoes/` ✅                          |
| 9     | CRUD em todos os módulos      | Formulários + validação + efeitos no estoque ✅      |
| 10    | Catálogo (vitrine) + Produção (estoque) | Cat = só estoque > 0; cadastro de peça em Produção ✅ |
| 11    | Despesas                      | Tabela `despesa` + página `/despesas/` + receita líquida real ✅ |
| 11.1  | Custo automático da peça      | Custo derivado dos materiais (view) + preço de venda sugerido ✅ |
| 11.2  | Foto de produto               | Upload de foto opcional por peça; exibida no Catálogo e Produção ✅ |
| 11.3  | Consumo de matéria-prima      | Produção debita materiais + cadastro por preço total ✅ |
| 11.4  | Custo investido histórico     | Snapshot `custo_unitario` em `producao`; vitrine imune a vendas ✅ |
| 13    | Trocar senha pela interface   | Credencial em `admin_credencial`; fluxo com verificação + confirmação ✅ |
| 14    | Limpeza de código             | `form_helpers` partilhado; `extensions.py` removido; docs atualizados ✅ |
| 15    | Filtro por mês + Lucro líquido | Seletor de mês no `/relatorios/`; card Margem virou Lucro líquido ✅ |
| 16    | Peça exige matéria-prima      | Guard no `GET` redireciona pra `/materiais/novo` se vazio; validação obriga ≥1 material ✅ |

A cada etapa concluída, atualizar a seção **Estado atual** e o **Roadmap**.

---

## 8. Como rodar (resumo)

**Local:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# preencher SECRET_KEY e ADMIN_PASSWORD_HASH no .env
python run.py
# abrir http://127.0.0.1:5000
```

O banco SQLite é criado vazio automaticamente no primeiro `python run.py`.
Para popular com dados fictícios, rode `python database/init_db.py --com-exemplos`.

**Render (produção):**
- Build: `pip install -r requirements.txt`
- Start: `python run.py`
- Env vars: `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`,
  `FLASK_ENV=production`, `SESSION_COOKIE_SECURE=1`.
- `run.py` detecta `PORT` e escuta em `0.0.0.0` automaticamente.
- **Anti-suspend (free tier):** o `run.py` declara um `GET /ping` público
  fora do padrão de blueprints — único caso. Mantém a app acordada
  enquanto um pinger externo (UptimeRobot etc.) bate de 14 em 14 min.
  Remover quando subir para plano pago. Ver [ADR-015](#adr-015--rota-ping-anti-suspend-do-render-fora-do-padrão-de-blueprints).

---

## 9. Decisões registradas (ADRs leves)

### ADR-001 — Sem ORM na Etapa 1
**Decisão:** usar `sqlite3` da stdlib via repositórios.
**Motivo:** domínio simples, queries didáticas, menos dependências, e a
camada de repositório isola a possível migração futura para SQLAlchemy.

### ADR-002 — Senha do admin como hash em `.env`
**Decisão:** armazenar `ADMIN_PASSWORD_HASH` (não a senha em texto puro).
**Motivo:** se o `.env` vazar, ainda há custo computacional para
recuperar a senha. Comparação via `werkzeug.security.check_password_hash`.

### ADR-003 — CSRF manual antes de Flask-WTF
**Decisão:** implementar token CSRF próprio em `security.py` (sessão).
**Motivo:** zero dependências adicionais nesta fase e padrão fica
estabelecido para os próximos forms. Flask-WTF pode entrar depois quando
houver validação de campos mais complexa.

### ADR-005 — Separação em backend/, frontend/, database/
**Decisão:** três pacotes raiz em vez de um único `app/`.
**Motivo:** torna óbvio onde mexer. Mudou regra/SQL? `backend/`. Mudou
visual? `frontend/`. Mudou schema ou seed? `database/`. Reduz fricção
ao crescer (matéria-prima, produção, vendas, etc.) — cada módulo replica
o mesmo padrão de divisão. O Flask aponta `template_folder` e
`static_folder` explicitamente para `frontend/`, e `DATABASE_PATH`
aponta para `database/atoriart.sqlite3`.

### ADR-004 — Sidebar com links desabilitados
**Decisão:** módulos futuros apareciam na sidebar com classe `is-disabled`
e `pointer-events:none`.
**Motivo:** o usuário via o mapa do sistema desde o dia 1, sem 404s.
**Status:** *substituída* — todos os links estão funcionais agora.

### ADR-006 — Padrão único de validação de formulário
**Decisão:** todo service expõe `validar_form(form_data, ...)` que devolve
`(erros: dict, valores: dict)`. `erros` vazio = válido. Templates re-renderizam
o form passando `valores` (string ou int conforme o caso) e `erros`,
exibindo a mensagem inline ao lado do campo.
**Motivo:** padrão único, sem dependência de Flask-WTF; o estudante lê o
código de validação top-to-bottom sem indireções. Os helpers `numero()`,
`inteiro()` e `data_iso()` vivem em [backend/services/form_helpers.py](backend/services/form_helpers.py)
e são importados por todos os services — cuidam das conversões e
aceitam vírgula decimal brasileira.

### ADR-007 — Efeitos colaterais no estoque (produção e venda)
**Decisão:** criar/apagar produções e vendas mexe automaticamente em
`peca.quantidade_estoque` na **mesma transação SQLite** do INSERT/DELETE.
- Criar produção: SOMA `quantidade` ao estoque da peça.
- Criar venda: SUBTRAI `quantidade` (bloqueada se sem estoque suficiente).
- Apagar produção: SUBTRAI (bloqueada se ficaria negativo).
- Apagar venda: SOMA de volta.

**Motivo:** estoque sempre consistente sem precisar de "rotina de
recálculo". Como ambos os SQLs (INSERT/DELETE da movimentação +
UPDATE do estoque) rodam dentro do mesmo `commit()`, ou tudo grava
ou nada grava — atomicidade nativa do SQLite.

**Trade-off original:** produção não consumia `material.quantidade_estoque`
nesta primeira versão — só mexia na peça. **Resolvido em [ADR-012](#adr-012--produção-consome-matéria-prima--cadastro-por-preço-total):**
produção agora também debita os materiais consumidos na mesma transação.

### ADR-008 — Catálogo vira vitrine; peça nasce na Produção
**Decisão:** o Catálogo (`/catalogo/`) é apenas leitura e filtra por
`peca.quantidade_estoque > 0`. O cadastro/edição/remoção da peça vive em
Produção (`/producao/pecas/...`) e é orquestrado por `peca_service`.
**Motivo:** o catálogo é a vitrine que a cliente final consulta para
saber o que pode comprar — peças sem estoque não devem aparecer lá.
Produção, por sua vez, é o controle de estoque: lá a peça nasce, recebe
quantidade via lançamentos e, quando atinge estoque > 0, surge
automaticamente no catálogo. Sem flag `publicado` extra: o estoque já é
a regra implícita.
**Implicação arquitetural:** três serviços cooperam — `peca_service`
(CRUD da entidade peça), `catalogo_service` (apenas `dados_catalogo()`),
`producao_service` (estoque atual + log de produções). O blueprint
`producao` hospeda as rotas de peça (`/producao/pecas/nova` etc.).

### ADR-009 — Módulo de Despesas e receita líquida real
**Decisão:** modelar `despesa` como tabela **sem chave estrangeira** e
**sem efeito colateral em estoque** — um registro puro (descrição,
categoria, valor, data). Com o módulo no ar, `dashboard_service` passou
a calcular `receita_liquida = faturamento − despesas` do período.
**Motivo:** despesa não se conecta a peça nem a material — é um custo
operacional/fixo do negócio fora do escopo de produto (aluguel, contas,
marketing, taxas...). A matéria-prima da produção tem módulo próprio
(`/materiais/`) e não entra aqui. Por isso não cabe a ela o
padrão do [ADR-007](#adr-007--efeitos-colaterais-no-estoque-produção-e-venda):
criar/apagar despesa é um INSERT/DELETE simples. Antes deste módulo, o
card "Receita líquida" do painel exibia, na verdade, o lucro bruto das
vendas — o rótulo "Faturamento menos despesas" só passou a ser verdadeiro
agora. Segue o glossário: receita líquida = faturamento − despesas.
**Trade-off conhecido:** Relatórios continua focado em vendas e ainda
não desconta despesas do seu "Lucro bruto" — pode entrar quando o filtro
de período (Etapa 12) unificar os dois períodos.

### ADR-011 — Upload de fotos de produto
**Decisão:** fotos são armazenadas **em disco** (`frontend/static/uploads/`),
e o banco guarda apenas o nome do arquivo gerado (`foto TEXT NULL`).
O nome segue o padrão `YYYYMMDD_HHMMSS_<8hex>.<ext>` para garantir
unicidade sem depender do nome original enviado pelo usuário.
**Motivo:** guardar o binário no SQLite (coluna BLOB) é possível mas
torna o banco pesado, impede o Flask de servir os arquivos diretamente
via `url_for('static', ...)` e dificulta inspeção. A abordagem "arquivo
em disco + nome no banco" é o padrão da web: banco leve, arquivos
servidos pelo servidor estático.
**Migração:** a coluna `foto` é adicionada via `ALTER TABLE` automático
na inicialização (`database/db.py._apply_migrations`), sem recriar o
banco — dados existentes são preservados.
**Rollback no formulário:** o arquivo é salvo em disco antes da validação
do form para poder passar o nome ao repositório; se a validação falhar,
o arquivo é deletado antes de re-renderizar o form. Ao editar com nova
foto, a antiga é deletada do disco apenas após o `commit()` bem-sucedido.
**Responsabilidade de cada camada:**
- Blueprint: `_salvar_foto()` e `_deletar_foto()` — única camada que
  toca o sistema de arquivos (Flask-específico).
- Service: recebe o `foto` (nome já gerado ou `None`) como parâmetro,
  passa ao repositório.
- Repository: trata `foto` como mais uma coluna no `INSERT`/`UPDATE`.
**Trade-off conhecido:** arquivos órfãos (peça apagada sem limpar o
arquivo) não são removidos automaticamente — `peca_apagar` apaga só o
registro do banco. Se relevante no futuro, pode-se adicionar limpeza no
`peca_service.apagar()`.

### ADR-010 — Custo da peça derivado dos materiais via view
**Decisão:** o `custo_producao` da peça não é mais coluna nem valor
digitado. É calculado pela view SQL `vw_peca_custo` como a soma de
`quantidade × valor_unitario` dos materiais que a peça consome. O
usuário digita só o `preco_venda` (preço sugerido de venda).
**Motivo:** o custo é um dado **derivado** — duplicá-lo numa coluna abre
espaço para inconsistência (muda o preço de um material e o custo da
peça fica velho). A view é fonte única da fórmula: `peca`, `venda` e
`producao` fazem `LEFT JOIN vw_peca_custo` e enxergam sempre o custo
atual. Mesmo espírito das `@property` dos models (`lucro_bruto`,
`em_alerta`): valor derivado não se armazena, se calcula.
**Trade-off conhecido:** o custo de uma venda antiga reflete o preço
*atual* dos materiais, não o da época da venda. Aceitável neste estágio
— o sistema já se comportava assim quando o custo era coluna lida por
JOIN. Um snapshot histórico por venda pode entrar no futuro.

### ADR-012 — Produção consome matéria-prima + cadastro por preço total
**Decisão (parte 1):** estender o [ADR-007](#adr-007--efeitos-colaterais-no-estoque-produção-e-venda):
criar produção também debita `material.quantidade_estoque`, na mesma
transação SQLite do INSERT da produção e do UPDATE do estoque da peça.
`producao_service.criar` checa o estoque de cada material **antes** de
gravar e bloqueia com erro amigável se faltar.

**Apagar é assimétrico em relação a criar:** retira as peças do estoque
mas **não devolve a matéria-prima**. Razão: o material foi
fisicamente consumido — não dá pra "des-produzir" e recuperar insumo.
Excluir o registro de produção é só remover a linha; o consumo já
aconteceu no mundo real. (Quem está corrigindo um erro de lançamento
ajusta o estoque do material à mão.)

**Decisão (parte 2):** o usuário cadastra/edita matéria-prima informando
o **preço total pago pelo lote** + a quantidade comprada. O
`valor_unitario` (coluna que continua existindo no banco e alimenta a
view `vw_peca_custo`) é derivado silenciosamente como `total / quantidade`
e nunca aparece na UI. A listagem de materiais mostra o "investido"
atual (`valor_unitario × quantidade_estoque`), não o preço por unidade.

**Motivo:** o usuário raciocina em "gastei R$ X pelo lote" — pedir o
preço por unidade é tradução mental desnecessária. E o controle de
estoque de matéria-prima é o que torna a integração peça↔produção↔venda
fechada de verdade (resolve o trade-off do ADR-007).

**Receita de consumo:** o débito em cada material usa a receita ATUAL
da peça (`peca_material`) no momento da produção. Helper privado
`_debitar_materiais(db, peca_id, qtd_producao)` subtrai
`qtd_producao × material_qty` de cada linha.

**Trade-off conhecido:** corrigir uma produção lançada errada vira um
processo manual: apagar a produção devolve as peças mas NÃO devolve a
matéria-prima. Para "refazer" sem inflar o consumo, o usuário precisa
ajustar o estoque do material na mão (editando o material) antes de
relançar a produção. Aceitável porque combina com a realidade física —
a alternativa simétrica criava bug pior em qualquer edição da receita.

### ADR-013 — Snapshot de custo na produção para custo investido histórico

**Problema:** o card "Custo investido" do Catálogo usava
`Σ peca.custo_producao × peca.quantidade_estoque`. Como `quantidade_estoque`
diminui a cada venda, o custo investido caía junto — como se o investimento
em produção desaparecesse quando as peças eram vendidas.

**Decisão:** adicionar a coluna `producao.custo_unitario REAL NOT NULL DEFAULT 0`,
que armazena um **snapshot imutável** do custo da peça (lido de `vw_peca_custo`)
no momento exato do INSERT da produção. O `custo_investido` do Catálogo passa a
ser calculado por `producao_repository.custo_total_investido()`:

```sql
SELECT COALESCE(SUM(quantidade * custo_unitario), 0) FROM producao
```

**Por que snapshot e não recalcular da view?** A `vw_peca_custo` reflete os
preços *atuais* dos materiais. Se um material mudar de preço, o custo histórico
de produções passadas seria alterado retroativamente — comportamento incorreto.
O snapshot congela o custo no momento real da fabricação.

**Efeito em cada operação:**
- Criar produção: lê `vw_peca_custo` dentro da mesma transação e grava o snapshot.
  `custo_total_investido()` sobe.
- Apagar produção: o registro e seu snapshot são deletados. `custo_total_investido()`
  desce (correto: a produção não ocorreu de fato).
- Vender peça: não toca a tabela `producao`. `custo_total_investido()` não muda.
  ✓ Esse é o comportamento corrigido.
- Mudar preço de material: não toca produções passadas. Histórico congelado. ✓

**Migration:** `database/db.py._apply_migrations` detecta a ausência da coluna,
aplica `ALTER TABLE` e faz backfill dos registros pré-migração com o custo atual
da view (melhor aproximação histórica disponível; sem impacto em dados de produção
futuros, que sempre gravarão o valor real).

**Trade-off conhecido:** peças sem nenhum material cadastrado terão
`custo_unitario = 0` — esse caso já ocorria antes (o custo derivado era zero).

### ADR-014 — Credencial do admin no banco; trocar senha pela UI

**Problema:** com a app rodando no Render, a senha estava só no `.env`
(`ADMIN_PASSWORD_HASH`). Trocar pela UI exigiria reescrever o arquivo —
inviável porque o filesystem do Render é efêmero (some a cada deploy) e
porque mistura "configuração de boot" com "estado mutável da aplicação".

**Decisão:** mover a credencial para a tabela `admin_credencial`
(`username` PK, `password_hash`, `atualizado_em`). O `.env` continua sendo
o ponto de **seed inicial** — no primeiro boot, `_apply_migrations` cria
a tabela e insere o hash do `.env` quando a tabela está vazia. Depois
disso, a tabela é a fonte oficial, e `authenticate()` lê dela.

**Fluxo de troca pela interface (`/configuracoes/trocar-senha`):**
1. Pede a **senha atual** (verificada com `check_password_hash`).
2. Pede a nova senha + **confirmação digitada** (devem bater).
3. Mínimo de 8 caracteres; nova ≠ atual.
4. **Checkbox de confirmação explícita** marcado obrigatoriamente.
5. Em caso de sucesso: gera o novo hash com `generate_password_hash`,
   atualiza `password_hash` e `atualizado_em` no banco, faz
   `logout_session()` e redireciona pro `/auth/login` com flash de
   sucesso — força relogin com a nova senha.

**Por que forçar relogin?** Sinaliza explicitamente que a credencial
mudou e fecha qualquer sessão (em outros dispositivos, etc.) que ainda
estivesse usando o vínculo com a senha antiga. Custo baixo, ganho de
clareza alto.

**Botão "Resetar banco" removido:** com a credencial no banco e a app
em produção, dropar tabelas pela UI é destrutivo demais — qualquer
manutenção real é feita fora da aplicação.

**Trade-off conhecido:** se o banco for resetado (manualmente ou por
filesystem efêmero do provedor), a senha **volta** ao hash do `.env`,
porque o seed roda de novo. Para persistência em produção, configurar
um disco persistente no Render (ou usar Postgres).

### ADR-015 — Rota `/ping` anti-suspend do Render fora do padrão de blueprints

**Problema:** o free tier do Render hiberna a app após ~15 min sem
tráfego. O cold start seguinte demora muitos segundos. Pra contornar
até subir pra plano pago, precisamos de um endpoint público que um
pinger externo (UptimeRobot, BetterUptime, cron-job.org...) bata a
cada ~14 min.

**Decisão:** declarar a rota direto em `run.py`, **fora do padrão de
blueprints** seguido pelos outros 9 módulos. Uma exceção consciente
à regra de ouro do projeto.

```python
# em run.py
@app.route("/ping")
def ping():
    return {"status": "ok"}, 200
```

**Motivo:** a rota é **explicitamente temporária**, com sunset claro
(remover quando subir pra plano pago). Em casos assim, visibilidade e
facilidade de remoção vencem consistência arquitetural:
- Um único arquivo (`run.py`) — fácil de achar.
- Uma única linha de `@app.route` mais uma função — fácil de deletar.
- Não polui `backend/blueprints/` com um diretório `health/` órfão
  cujo propósito a UI não conhece.
- Comentário em cima do código deixa o sunset óbvio: "REMOVER quando
  subir para plano pago".

**Aceito como exceção:** o resto do projeto continua na regra (toda
rota nova permanente vai em `backend/blueprints/<modulo>/routes.py`,
registrada em `create_app()`). Esta é a **única** exceção e está
documentada justamente pra ninguém usar de precedente.

**Plano de remoção:** quando o plano do Render virar pago (ou migrar
pra outro provedor sem suspensão), apagar o bloco `@app.route("/ping")`
no `run.py` e desligar o monitor externo. ~6 linhas no total.

---

## 10. Glossário curto
- **Peça:** item produzido (ex.: brinco, colar).
- **Matéria-prima / Material:** insumo usado na produção.
- **Produção:** registro de fabricação de N peças em uma data.
- **Venda:** registro de venda com valor.
- **Despesa:** custo fixo ou variável que reduz a receita líquida.
- **Custo de produção:** soma dos materiais de uma peça — calculado
  (view `vw_peca_custo`), nunca digitado.
- **Preço de venda:** preço sugerido de venda da peça, definido pelo
  usuário. **Lucro da peça** = preço de venda − custo de produção.
- **Faturamento:** soma bruta de vendas no período.
- **Receita líquida:** faturamento − despesas no período.

-- Schema do banco AtoriArt (SQLite).
-- Rodado por init_db.py. Sempre apaga e recria as tabelas existentes.

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
    unidade             TEXT    NOT NULL,      -- "m", "g", "un", etc.
    valor_unitario      REAL    NOT NULL,      -- custo por unidade
    quantidade_estoque  REAL    NOT NULL DEFAULT 0,  -- estoque atual
    estoque_minimo      REAL    NOT NULL DEFAULT 0   -- gatilho de alerta
);

-- `preco_venda` é o preço sugerido de venda (digitado pelo usuário).
-- O custo de produção NÃO é coluna: é derivado dos materiais pela
-- view vw_peca_custo (definida no fim deste arquivo).
CREATE TABLE peca (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                TEXT    NOT NULL,
    preco_venda         REAL    NOT NULL,
    quantidade_estoque  INTEGER NOT NULL DEFAULT 0,
    foto                TEXT                          -- nome do arquivo em static/uploads/
);

-- Relação "uma peça usa N materiais, cada um em uma quantidade"
CREATE TABLE peca_material (
    peca_id      INTEGER NOT NULL,
    material_id  INTEGER NOT NULL,
    quantidade   REAL    NOT NULL,
    PRIMARY KEY (peca_id, material_id),
    FOREIGN KEY (peca_id)     REFERENCES peca(id)     ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES material(id) ON DELETE RESTRICT
);

-- Registro de produção: cada linha = "no dia X, produzi N unidades da peça Y"
CREATE TABLE producao (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    peca_id     INTEGER NOT NULL,
    quantidade  INTEGER NOT NULL,
    data        TEXT    NOT NULL,           -- 'YYYY-MM-DD'
    observacao  TEXT,                       -- opcional
    FOREIGN KEY (peca_id) REFERENCES peca(id) ON DELETE CASCADE
);
CREATE INDEX idx_producao_data ON producao(data);

-- Registro de venda: cada linha = "no dia X, vendi N unidades da peça Y por R$ Z"
-- ON DELETE RESTRICT: vendas históricas não podem sumir se a peça for apagada.
CREATE TABLE venda (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    peca_id          INTEGER NOT NULL,
    quantidade       INTEGER NOT NULL,
    valor_total      REAL    NOT NULL,        -- valor total da venda (não unitário)
    data             TEXT    NOT NULL,        -- 'YYYY-MM-DD'
    forma_pagamento  TEXT,                    -- opcional: 'PIX', 'Dinheiro', etc.
    FOREIGN KEY (peca_id) REFERENCES peca(id) ON DELETE RESTRICT
);
CREATE INDEX idx_venda_data ON venda(data);

-- Registro de despesa: cada linha = "no dia X gastei R$ Z com W".
-- Custo operacional/fixo (aluguel, contas...) — fora do escopo de
-- produto; matéria-prima da produção fica na tabela `material`.
-- Registro puro: não tem FK nem efeito no estoque.
-- Entra no cálculo da receita líquida (faturamento - despesas).
CREATE TABLE despesa (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao   TEXT    NOT NULL,
    categoria   TEXT,                         -- opcional: 'Aluguel', 'Marketing', etc.
    valor       REAL    NOT NULL,             -- valor gasto (R$)
    data        TEXT    NOT NULL              -- 'YYYY-MM-DD'
);
CREATE INDEX idx_despesa_data ON despesa(data);

-- Custo de produção de cada peça = soma (quantidade × valor_unitario) dos
-- materiais que ela consome. É uma VIEW, não uma coluna: o custo é sempre
-- derivado e reflete na hora os preços atuais dos materiais. Fonte única
-- da fórmula do custo — peca/venda/producao leem daqui.
CREATE VIEW vw_peca_custo AS
SELECT pm.peca_id                            AS peca_id,
       SUM(pm.quantidade * m.valor_unitario) AS custo_producao
FROM peca_material pm
JOIN material m ON m.id = pm.material_id
GROUP BY pm.peca_id;

-- Schema do banco AtoriArt (SQLite).
-- Rodado por init_db.py. Sempre apaga e recria as tabelas existentes.
-- Outras tabelas (despesa) serão adicionadas nas próximas etapas.

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

CREATE TABLE peca (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                TEXT    NOT NULL,
    custo_producao      REAL    NOT NULL,
    quantidade_estoque  INTEGER NOT NULL DEFAULT 0
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

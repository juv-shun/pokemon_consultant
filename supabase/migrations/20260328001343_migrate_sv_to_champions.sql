-- svスキーマからchampionsスキーマへの移行
-- ポケモン対戦が Champions に移行するため、スキーマを切り替える

-- ========================================
-- 1. スキーマ作成
-- ========================================
CREATE SCHEMA champions;

-- ========================================
-- 2. テーブル作成
-- ========================================

-- 2.1 pokemon テーブル
CREATE TABLE champions.pokemon (
    id SERIAL PRIMARY KEY,
    pokedex_no INTEGER NOT NULL,
    name_ja VARCHAR(64) UNIQUE NOT NULL,
    name_en VARCHAR(64),
    form_label VARCHAR(64),
    type_primary VARCHAR(16) NOT NULL,
    type_secondary VARCHAR(16),
    height_dm SMALLINT,
    weight_hg SMALLINT,
    low_kick_power SMALLINT,
    is_legendary BOOLEAN DEFAULT FALSE,
    is_mythical BOOLEAN DEFAULT FALSE,
    base_hp SMALLINT NOT NULL,
    base_atk SMALLINT NOT NULL,
    base_def SMALLINT NOT NULL,
    base_spa SMALLINT NOT NULL,
    base_spd SMALLINT NOT NULL,
    base_spe SMALLINT NOT NULL,
    remarks TEXT,
    CONSTRAINT chk_type_primary CHECK (type_primary IN (
        'ノーマル', 'ほのお', 'みず', 'でんき', 'くさ', 'こおり',
        'かくとう', 'どく', 'じめん', 'ひこう', 'エスパー', 'むし',
        'いわ', 'ゴースト', 'ドラゴン', 'あく', 'はがね', 'フェアリー'
    )),
    CONSTRAINT chk_type_secondary CHECK (type_secondary IS NULL OR type_secondary IN (
        'ノーマル', 'ほのお', 'みず', 'でんき', 'くさ', 'こおり',
        'かくとう', 'どく', 'じめん', 'ひこう', 'エスパー', 'むし',
        'いわ', 'ゴースト', 'ドラゴン', 'あく', 'はがね', 'フェアリー'
    ))
);

-- 2.2 abilities テーブル
CREATE TABLE champions.abilities (
    id SERIAL PRIMARY KEY,
    name_ja VARCHAR(64) UNIQUE NOT NULL,
    effect_text TEXT
);

-- 2.3 pokemon_abilities テーブル
CREATE TABLE champions.pokemon_abilities (
    pokemon_id INTEGER NOT NULL,
    ability_id INTEGER NOT NULL,
    is_hidden BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (pokemon_id, ability_id),
    FOREIGN KEY (pokemon_id) REFERENCES champions.pokemon(id) ON DELETE CASCADE,
    FOREIGN KEY (ability_id) REFERENCES champions.abilities(id) ON DELETE CASCADE
);

-- 2.4 moves テーブル
CREATE TABLE champions.moves (
    id SERIAL PRIMARY KEY,
    name_ja VARCHAR(64) UNIQUE NOT NULL,
    type_name VARCHAR(16) NOT NULL,
    damage_class VARCHAR(16),
    power SMALLINT,
    accuracy SMALLINT,
    pp SMALLINT,
    priority SMALLINT DEFAULT 0,
    effect_text TEXT,
    CONSTRAINT chk_move_type CHECK (type_name IN (
        'ノーマル', 'ほのお', 'みず', 'でんき', 'くさ', 'こおり',
        'かくとう', 'どく', 'じめん', 'ひこう', 'エスパー', 'むし',
        'いわ', 'ゴースト', 'ドラゴン', 'あく', 'はがね', 'フェアリー'
    )),
    CONSTRAINT chk_damage_class CHECK (damage_class IS NULL OR damage_class IN ('physical', 'special', 'status'))
);

-- 2.5 pokemon_moves テーブル
CREATE TABLE champions.pokemon_moves (
    pokemon_id INTEGER NOT NULL,
    move_id INTEGER NOT NULL,
    PRIMARY KEY (pokemon_id, move_id),
    FOREIGN KEY (pokemon_id) REFERENCES champions.pokemon(id) ON DELETE CASCADE,
    FOREIGN KEY (move_id) REFERENCES champions.moves(id) ON DELETE CASCADE
);

-- ========================================
-- 3. インデックス作成
-- ========================================

-- 3.1 pokemon テーブル
CREATE INDEX idx_pokemon_pokedex_no ON champions.pokemon(pokedex_no);
CREATE INDEX idx_pokemon_base_spe ON champions.pokemon(base_spe);
CREATE INDEX idx_pokemon_is_legendary ON champions.pokemon(is_legendary);
CREATE INDEX idx_pokemon_is_mythical ON champions.pokemon(is_mythical);

-- 3.2 タイプ別部分インデックス（18種類）
CREATE INDEX idx_pokemon_type_normal ON champions.pokemon(id)
    WHERE type_primary = 'ノーマル' OR type_secondary = 'ノーマル';

CREATE INDEX idx_pokemon_type_fire ON champions.pokemon(id)
    WHERE type_primary = 'ほのお' OR type_secondary = 'ほのお';

CREATE INDEX idx_pokemon_type_water ON champions.pokemon(id)
    WHERE type_primary = 'みず' OR type_secondary = 'みず';

CREATE INDEX idx_pokemon_type_electric ON champions.pokemon(id)
    WHERE type_primary = 'でんき' OR type_secondary = 'でんき';

CREATE INDEX idx_pokemon_type_grass ON champions.pokemon(id)
    WHERE type_primary = 'くさ' OR type_secondary = 'くさ';

CREATE INDEX idx_pokemon_type_ice ON champions.pokemon(id)
    WHERE type_primary = 'こおり' OR type_secondary = 'こおり';

CREATE INDEX idx_pokemon_type_fighting ON champions.pokemon(id)
    WHERE type_primary = 'かくとう' OR type_secondary = 'かくとう';

CREATE INDEX idx_pokemon_type_poison ON champions.pokemon(id)
    WHERE type_primary = 'どく' OR type_secondary = 'どく';

CREATE INDEX idx_pokemon_type_ground ON champions.pokemon(id)
    WHERE type_primary = 'じめん' OR type_secondary = 'じめん';

CREATE INDEX idx_pokemon_type_flying ON champions.pokemon(id)
    WHERE type_primary = 'ひこう' OR type_secondary = 'ひこう';

CREATE INDEX idx_pokemon_type_psychic ON champions.pokemon(id)
    WHERE type_primary = 'エスパー' OR type_secondary = 'エスパー';

CREATE INDEX idx_pokemon_type_bug ON champions.pokemon(id)
    WHERE type_primary = 'むし' OR type_secondary = 'むし';

CREATE INDEX idx_pokemon_type_rock ON champions.pokemon(id)
    WHERE type_primary = 'いわ' OR type_secondary = 'いわ';

CREATE INDEX idx_pokemon_type_ghost ON champions.pokemon(id)
    WHERE type_primary = 'ゴースト' OR type_secondary = 'ゴースト';

CREATE INDEX idx_pokemon_type_dragon ON champions.pokemon(id)
    WHERE type_primary = 'ドラゴン' OR type_secondary = 'ドラゴン';

CREATE INDEX idx_pokemon_type_dark ON champions.pokemon(id)
    WHERE type_primary = 'あく' OR type_secondary = 'あく';

CREATE INDEX idx_pokemon_type_steel ON champions.pokemon(id)
    WHERE type_primary = 'はがね' OR type_secondary = 'はがね';

CREATE INDEX idx_pokemon_type_fairy ON champions.pokemon(id)
    WHERE type_primary = 'フェアリー' OR type_secondary = 'フェアリー';

-- 3.3 pokemon_abilities テーブル
CREATE INDEX idx_pokemon_abilities_ability_id ON champions.pokemon_abilities(ability_id, pokemon_id);
CREATE INDEX idx_pokemon_abilities_is_hidden ON champions.pokemon_abilities(is_hidden);

-- 3.4 moves テーブル
CREATE INDEX idx_moves_type_name ON champions.moves(type_name);
CREATE INDEX idx_moves_damage_class ON champions.moves(damage_class);

-- 3.5 pokemon_moves テーブル
CREATE INDEX idx_pokemon_moves_move_id ON champions.pokemon_moves(move_id, pokemon_id);

-- ========================================
-- 4. コメント追加
-- ========================================

COMMENT ON SCHEMA champions IS 'ポケモン Champions データ';
COMMENT ON TABLE champions.pokemon IS 'ポケモン基本情報（フォーム違いを含む）';
COMMENT ON TABLE champions.abilities IS '特性マスタ';
COMMENT ON TABLE champions.pokemon_abilities IS 'ポケモン-特性の関連';
COMMENT ON TABLE champions.moves IS '技マスタ';
COMMENT ON TABLE champions.pokemon_moves IS 'ポケモン-技の関連';

-- ========================================
-- 5. svスキーマ削除
-- ========================================

DROP SCHEMA sv CASCADE;

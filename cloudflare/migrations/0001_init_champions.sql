-- ポケモンマスターデータベース 初期スキーマ（Cloudflare D1 / SQLite）
-- supabase/migrations/ の champions スキーマ最終形（20260510000000 時点）を D1 向けに書き換えたもの。
-- データは含まない。Supabase から書き出した INSERT 文を別途投入する。
--
-- Postgres からの主な読み替え:
--   - スキーマ champions は使わず、テーブル名のみ（D1 は単一スキーマ）
--   - SERIAL → INTEGER PRIMARY KEY（Supabase の id をそのまま投入し外部キーを維持）
--   - BOOLEAN → INTEGER + CHECK (0/1)
--   - VARCHAR(n) / SMALLINT → TEXT / INTEGER（SQLite は長さを強制しない）
--   - COMMENT ON → SQL コメント

-- ========================================
-- 1. テーブル作成
-- ========================================

-- 1.1 pokemon: ポケモン基本情報（フォーム違いを含む）
CREATE TABLE pokemon (
    id INTEGER PRIMARY KEY,
    pokedex_no INTEGER NOT NULL,
    name_ja TEXT NOT NULL UNIQUE,
    name_en TEXT,
    form_label TEXT,
    form_code TEXT, -- 詳細ページURL上のフォーム識別コード（例: m, x, y, a, h）
    type_primary TEXT NOT NULL,
    type_secondary TEXT,
    height_dm INTEGER,
    weight_hg INTEGER,
    low_kick_power INTEGER,
    is_legendary INTEGER DEFAULT 0,
    is_mythical INTEGER DEFAULT 0,
    is_mega INTEGER DEFAULT 0,
    base_hp INTEGER NOT NULL,
    base_atk INTEGER NOT NULL,
    base_def INTEGER NOT NULL,
    base_spa INTEGER NOT NULL,
    base_spd INTEGER NOT NULL,
    base_spe INTEGER NOT NULL,
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
    )),
    CONSTRAINT chk_is_legendary CHECK (is_legendary IS NULL OR is_legendary IN (0, 1)),
    CONSTRAINT chk_is_mythical CHECK (is_mythical IS NULL OR is_mythical IN (0, 1)),
    CONSTRAINT chk_is_mega CHECK (is_mega IS NULL OR is_mega IN (0, 1))
);

-- 1.2 abilities: 特性マスタ
CREATE TABLE abilities (
    id INTEGER PRIMARY KEY,
    name_ja TEXT NOT NULL UNIQUE,
    effect_text TEXT
);

-- 1.3 pokemon_abilities: ポケモン-特性の関連
CREATE TABLE pokemon_abilities (
    pokemon_id INTEGER NOT NULL,
    ability_id INTEGER NOT NULL,
    is_hidden INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (pokemon_id, ability_id),
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(id) ON DELETE CASCADE,
    FOREIGN KEY (ability_id) REFERENCES abilities(id) ON DELETE CASCADE,
    CONSTRAINT chk_is_hidden CHECK (is_hidden IN (0, 1))
) WITHOUT ROWID;

-- 1.4 moves: 技マスタ
CREATE TABLE moves (
    id INTEGER PRIMARY KEY,
    name_ja TEXT NOT NULL UNIQUE,
    type_name TEXT NOT NULL,
    damage_class TEXT,
    damage_class_ja TEXT, -- 技分類の日本語表記（物理/特殊/変化/-）
    power INTEGER,
    accuracy INTEGER,
    pp INTEGER,
    priority INTEGER DEFAULT 0,
    contact INTEGER, -- 接触技であれば 1、非接触技であれば 0
    target TEXT DEFAULT 'single',
    is_spread INTEGER DEFAULT 0,
    effect_text TEXT,
    CONSTRAINT chk_move_type CHECK (type_name IN (
        'ノーマル', 'ほのお', 'みず', 'でんき', 'くさ', 'こおり',
        'かくとう', 'どく', 'じめん', 'ひこう', 'エスパー', 'むし',
        'いわ', 'ゴースト', 'ドラゴン', 'あく', 'はがね', 'フェアリー'
    )),
    CONSTRAINT chk_damage_class CHECK (damage_class IS NULL OR damage_class IN ('physical', 'special', 'status')),
    CONSTRAINT chk_damage_class_ja CHECK (damage_class_ja IS NULL OR damage_class_ja IN ('物理', '特殊', '変化', '-')),
    CONSTRAINT chk_move_target CHECK (target IN ('single', 'all_opponents', 'all_except_self', 'self')),
    CONSTRAINT chk_contact CHECK (contact IS NULL OR contact IN (0, 1)),
    CONSTRAINT chk_is_spread CHECK (is_spread IS NULL OR is_spread IN (0, 1))
);

-- 1.5 pokemon_moves: ポケモン-技の関連
CREATE TABLE pokemon_moves (
    pokemon_id INTEGER NOT NULL,
    move_id INTEGER NOT NULL,
    PRIMARY KEY (pokemon_id, move_id),
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(id) ON DELETE CASCADE,
    FOREIGN KEY (move_id) REFERENCES moves(id) ON DELETE CASCADE
) WITHOUT ROWID;

-- ========================================
-- 2. インデックス作成
-- ========================================

-- 2.1 pokemon テーブル
CREATE INDEX idx_pokemon_pokedex_no ON pokemon(pokedex_no);
CREATE INDEX idx_pokemon_base_spe ON pokemon(base_spe);
CREATE INDEX idx_pokemon_is_legendary ON pokemon(is_legendary);
CREATE INDEX idx_pokemon_is_mythical ON pokemon(is_mythical);
CREATE INDEX idx_pokemon_is_mega ON pokemon(is_mega);

-- 2.2 タイプ別部分インデックス（18種類）
CREATE INDEX idx_pokemon_type_normal ON pokemon(id)
    WHERE type_primary = 'ノーマル' OR type_secondary = 'ノーマル';

CREATE INDEX idx_pokemon_type_fire ON pokemon(id)
    WHERE type_primary = 'ほのお' OR type_secondary = 'ほのお';

CREATE INDEX idx_pokemon_type_water ON pokemon(id)
    WHERE type_primary = 'みず' OR type_secondary = 'みず';

CREATE INDEX idx_pokemon_type_electric ON pokemon(id)
    WHERE type_primary = 'でんき' OR type_secondary = 'でんき';

CREATE INDEX idx_pokemon_type_grass ON pokemon(id)
    WHERE type_primary = 'くさ' OR type_secondary = 'くさ';

CREATE INDEX idx_pokemon_type_ice ON pokemon(id)
    WHERE type_primary = 'こおり' OR type_secondary = 'こおり';

CREATE INDEX idx_pokemon_type_fighting ON pokemon(id)
    WHERE type_primary = 'かくとう' OR type_secondary = 'かくとう';

CREATE INDEX idx_pokemon_type_poison ON pokemon(id)
    WHERE type_primary = 'どく' OR type_secondary = 'どく';

CREATE INDEX idx_pokemon_type_ground ON pokemon(id)
    WHERE type_primary = 'じめん' OR type_secondary = 'じめん';

CREATE INDEX idx_pokemon_type_flying ON pokemon(id)
    WHERE type_primary = 'ひこう' OR type_secondary = 'ひこう';

CREATE INDEX idx_pokemon_type_psychic ON pokemon(id)
    WHERE type_primary = 'エスパー' OR type_secondary = 'エスパー';

CREATE INDEX idx_pokemon_type_bug ON pokemon(id)
    WHERE type_primary = 'むし' OR type_secondary = 'むし';

CREATE INDEX idx_pokemon_type_rock ON pokemon(id)
    WHERE type_primary = 'いわ' OR type_secondary = 'いわ';

CREATE INDEX idx_pokemon_type_ghost ON pokemon(id)
    WHERE type_primary = 'ゴースト' OR type_secondary = 'ゴースト';

CREATE INDEX idx_pokemon_type_dragon ON pokemon(id)
    WHERE type_primary = 'ドラゴン' OR type_secondary = 'ドラゴン';

CREATE INDEX idx_pokemon_type_dark ON pokemon(id)
    WHERE type_primary = 'あく' OR type_secondary = 'あく';

CREATE INDEX idx_pokemon_type_steel ON pokemon(id)
    WHERE type_primary = 'はがね' OR type_secondary = 'はがね';

CREATE INDEX idx_pokemon_type_fairy ON pokemon(id)
    WHERE type_primary = 'フェアリー' OR type_secondary = 'フェアリー';

-- 2.3 pokemon_abilities テーブル
CREATE INDEX idx_pokemon_abilities_ability_id ON pokemon_abilities(ability_id, pokemon_id);
CREATE INDEX idx_pokemon_abilities_is_hidden ON pokemon_abilities(is_hidden);

-- 2.4 moves テーブル
CREATE INDEX idx_moves_type_name ON moves(type_name);
CREATE INDEX idx_moves_damage_class ON moves(damage_class);

-- 2.5 pokemon_moves テーブル
CREATE INDEX idx_pokemon_moves_move_id ON pokemon_moves(move_id, pokemon_id);

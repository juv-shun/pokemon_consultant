-- Pokemon Champions の統計情報（旧 battle-data スキルの Markdown）を保持するテーブル。
-- データは update-battle-data スキルのスクリプトがサイトから取得して直接投入する（リポジトリでは管理しない）。
-- 運用上は最新シーズン・ルールのみ保持するが、season / rule をキーに含めて複数を共存できる形にしておく。

-- 1. battle_seasons: 取り込んだ統計の対象シーズン・ルールと更新日時
CREATE TABLE battle_seasons (
    season INTEGER NOT NULL,          -- サイト上のシーズン番号（例: 6）
    rule INTEGER NOT NULL,            -- サイト上のルール番号（1 = ダブルバトル）
    season_label TEXT NOT NULL,       -- 例: 'シーズンM-6 (M-C)'
    rule_name TEXT NOT NULL,          -- 例: 'ダブルバトル'
    period_start TEXT NOT NULL,       -- 'YYYY-MM-DD'
    period_end TEXT NOT NULL,         -- 'YYYY-MM-DD'
    updated_at TEXT NOT NULL,         -- サイト表示の更新日時 'YYYY-MM-DD HH:MM'
    source_url TEXT NOT NULL,
    PRIMARY KEY (season, rule)
) WITHOUT ROWID;

-- 2. battle_rankings: 使用率ランキング（サイト上で確認できた全件）
CREATE TABLE battle_rankings (
    season INTEGER NOT NULL,
    rule INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    pokemon_name TEXT NOT NULL,       -- サイト表記の名前（例: 'イエッサン (メス)'）
    pokemon_id INTEGER,               -- pokemon.id（対応が取れない場合は NULL）
    has_detail INTEGER NOT NULL DEFAULT 0 CHECK (has_detail IN (0, 1)), -- battle_usages に詳細があれば 1
    source_url TEXT,                  -- 詳細ページの URL
    PRIMARY KEY (season, rule, rank),
    UNIQUE (season, rule, pokemon_name),
    FOREIGN KEY (season, rule) REFERENCES battle_seasons(season, rule) ON DELETE CASCADE,
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(id) ON DELETE SET NULL
) WITHOUT ROWID;

-- 3. battle_usages: 上位ポケモンの採用率（技・特性・持ち物・性格・能力ポイント）
CREATE TABLE battle_usages (
    season INTEGER NOT NULL,
    rule INTEGER NOT NULL,
    pokemon_name TEXT NOT NULL,       -- battle_rankings.pokemon_name
    category TEXT NOT NULL CHECK (category IN ('move', 'ability', 'item', 'nature', 'stat_spread')),
    rank INTEGER NOT NULL,            -- カテゴリ内の順位（1 始まり）
    name TEXT NOT NULL,               -- 技名・特性名・持ち物名・性格名・能力ポイント配分（例: 'A32, S32, +余り'）
    detail TEXT,                      -- 補足（性格の上昇下降 'C↑A↓' など）
    rate REAL NOT NULL,               -- 使用率（%、例: 44.4）
    PRIMARY KEY (season, rule, pokemon_name, category, rank),
    FOREIGN KEY (season, rule, pokemon_name) REFERENCES battle_rankings(season, rule, pokemon_name) ON DELETE CASCADE
) WITHOUT ROWID;

CREATE INDEX idx_battle_rankings_pokemon_id ON battle_rankings(pokemon_id);
CREATE INDEX idx_battle_usages_category_name ON battle_usages(category, name);

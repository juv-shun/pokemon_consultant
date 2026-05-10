-- スクレイピング結果で保持する追加情報

ALTER TABLE champions.pokemon
    ADD COLUMN form_code VARCHAR(16);

ALTER TABLE champions.moves
    ADD COLUMN damage_class_ja VARCHAR(16),
    ADD COLUMN contact BOOLEAN,
    ADD CONSTRAINT chk_damage_class_ja
        CHECK (damage_class_ja IS NULL OR damage_class_ja IN ('物理', '特殊', '変化', '-'));

COMMENT ON COLUMN champions.pokemon.form_code IS '詳細ページURL上のフォーム識別コード（例: m, x, y, a, h）';
COMMENT ON COLUMN champions.moves.damage_class_ja IS '技分類の日本語表記（物理/特殊/変化/-）';
COMMENT ON COLUMN champions.moves.contact IS '接触技であればTRUE、非接触技であればFALSE';

-- メガ進化判定カラムを追加
ALTER TABLE champions.pokemon ADD COLUMN is_mega BOOLEAN DEFAULT FALSE;

-- メガ進化フィルタ用インデックス
CREATE INDEX idx_pokemon_is_mega ON champions.pokemon(is_mega);

-- 技の対象（target）とis_spreadを effect_text から設定

-- 相手全体 → all_opponents
UPDATE champions.moves
SET target = 'all_opponents', is_spread = TRUE
WHERE effect_text LIKE '相手全体が対象%';

-- 自分以外全員 → all_except_self
UPDATE champions.moves
SET target = 'all_except_self', is_spread = TRUE
WHERE effect_text LIKE '自分以外全員が対象%';

-- 自分自身 → self（パターンベース）
UPDATE champions.moves
SET target = 'self'
WHERE damage_class = 'status'
  AND name_ja != 'のろい'
  AND (
    effect_text LIKE '自分の%'
    OR effect_text LIKE 'HPが、天気が%'
    OR effect_text LIKE 'HPと状態異常%'
    OR effect_text LIKE 'HPが最大HP%'
  );

-- 自分自身 → self（パターン外の個別指定）
UPDATE champions.moves
SET target = 'self'
WHERE name_ja IN (
  'きあいだめ',
  'バトンタッチ',
  'いやしのねがい',
  'みちづれ',
  'でんじふゆう',
  'アクアリング',
  'ねをはる'
);

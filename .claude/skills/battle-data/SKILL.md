---
name: battle-data
description: Pokemon Champions の最新流行ランキング、環境ポケモン、採用傾向、使用率、上位ポケモンの詳細データを参照する。ユーザーが流行、環境、ランキング、採用技、特性、持ち物、性格、能力ポイント、対戦環境の相談をしたときに使う。
---

# Champions Trend

Pokemon Champions の最新環境データを、ポケモンマスターデータベース（MCP サーバ `pokemon-master`）の `battle_*` テーブルから参照する。
`query` ツールで読み取り専用の SQL を実行する。カラムの詳細は `describe_schema` で確認できる。

## テーブル

| テーブル | 内容 |
| --- | --- |
| `battle_seasons` | 対象シーズン・ルール・期間・更新日時・ソースURL（1行） |
| `battle_rankings` | 使用率ランキング全件。`pokemon_name` はサイト表記、`pokemon_id` で `pokemon` に JOIN できる。`has_detail = 1` なら詳細あり |
| `battle_usages` | 上位50匹の採用率。`category` は `move` / `ability` / `item` / `nature` / `stat_spread`、`rate` は % の数値 |

## 参照手順

1. ランキングは `battle_rankings` を `rank` 順に読む。
2. 特定ポケモンの採用技、特性、持ち物、性格、能力ポイントは `battle_usages` を `pokemon_name` と `category` で絞って読む。
   - `pokemon_name` はサイト表記（例: `'イエッサン (メス)'`, `'ウインディ (ヒスイ)'`, `'フラエッテ:永遠'`）。マスターの名前から探すときは `pokemon_id` 経由で JOIN する。
3. `has_detail = 0` のポケモンは詳細な採用傾向を断定しない。ランキング順位だけを根拠に扱う。
4. 回答では必要に応じて、`battle_seasons` の対象シーズン、ルール、更新日を示す。

```sql
-- 上位10匹とタイプ
SELECT r.rank, r.pokemon_name, p.type_primary, p.type_secondary
FROM battle_rankings r LEFT JOIN pokemon p ON p.id = r.pokemon_id
ORDER BY r.rank LIMIT 10;

-- ガブリアスの持ち物・性格
SELECT category, rank, name, detail, rate
FROM battle_usages
WHERE pokemon_name = 'ガブリアス' AND category IN ('item', 'nature')
ORDER BY category, rank;

-- 特性「いかく」を採用している上位ポケモン
SELECT r.rank, u.pokemon_name, u.rate
FROM battle_usages u JOIN battle_rankings r USING (season, rule, pokemon_name)
WHERE u.category = 'ability' AND u.name = 'いかく'
ORDER BY r.rank;
```

## データの扱い

- 過去分は保持しない。常に最新シーズンのデータで入れ替わる。
- 使用率が不明な項目は推測で補完しない。数値データと解釈は分けて答える。
- 能力ポイント（`stat_spread`）は、サイトで「n件を合算」と表示される代表行のみを保持する。内訳は無い。
- このデータは会話用の環境コンテキストであり、ポケモンの種族値、技威力、タイプなどのマスタ情報は `pokemon` / `moves` などのテーブルや他スキルを参照する。
- データ更新は `update-battle-data` スキルで行う。

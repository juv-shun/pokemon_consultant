# champions スキーマのデータ書き出し

Supabase（PokemonDB プロジェクト）の `champions` スキーマ5テーブルを 2026-10-16 に書き出したもの。Cloudflare D1 への移行用。

| ファイル | 行数 |
| --- | --- |
| `pokemon.csv` | 345 |
| `abilities.csv` | 215 |
| `moves.csv` | 511 |
| `pokemon_abilities.csv` | 720 |
| `pokemon_moves.csv` | 21881 |

- CSV は1行目がヘッダー、NULL は空欄、真偽値は `true` / `false`。
- `data.sql` は全テーブルの INSERT 文。スキーマ名なし、真偽値は `1` / `0` で、D1 (SQLite) にそのまま流せる。外部キーの依存順（pokemon → abilities → moves → 中間テーブル）に並んでいる。
- 書き出し後、件数・文字数合計・`pokemon_moves` の MD5 を Supabase 側と照合済み。
- Supabase 廃止後は、これが旧 Supabase データの最終バックアップとなる。

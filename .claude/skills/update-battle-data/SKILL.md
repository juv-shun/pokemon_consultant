---
name: update-battle-data
description: Pokemon Champions のバトルデータを最新シーズンに更新し、D1 の battle_* テーブルへ投入する。champs.pokedb.tokyo のシーズン選択と日付情報から実行日に対応するシーズンを判定し、ランキング全件と上位50匹の詳細を入れ替えたいときに使う。
---

# Battle Data Updater

Pokemon Champions の統計ページから、プラグイン `pokemon-db` の MCP サーバが参照する D1 の `battle_*` テーブルを更新する。
データの中身は日々変わるため、リポジトリでは管理しない（生成 SQL は git 管理外）。

## 対象

- 投入先: D1 `pokemon-master` の `battle_seasons` / `battle_rankings` / `battle_usages`（全削除してから入れ直す）
- ランキング: サイト上のランキング全件を `battle_rankings` に入れる。
- 詳細: ランキング上位50匹の技・特性・持ち物・性格・能力ポイントを `battle_usages` に入れる。
- 過去分は保持せず、常に最新対象で上書きする。
- テーブル定義は `cloudflare/migrations/0002_battle_data.sql`。
- 生成 SQL は `data/battle/battle_data.sql` に書き出す（`.gitignore` 済み。確認用の一時ファイル）。

## 手順

1. wrangler にログイン済みの環境で、`python .claude/skills/update-battle-data/scripts/update_battle_data.py --apply remote` を実行する。
   - `--apply` を付けないと SQL を書き出すだけで投入しない。投入前に中身を確認したいときは、まず付けずに実行する。
   - ローカル D1 で試すときは `--apply local`。
2. 実行日はローカル日付で判定される。サイトのシーズン選択にある期間と比較し、実行日を含むシーズンを自動選択する。
3. 必要に応じて `--season 2` のように対象シーズンを明示する。
4. 実行後に以下を確認する。
   - 出力の season / period / updated_at
   - 標準エラーに `warning: ... has no rows for ...` が出ていないこと。一部のポケモンだけなら元データが無い可能性もあるので、詳細ページで確認する
   - あるカテゴリが上位50匹すべてで 0 件のときは、スクリプトがエラーで止まり、D1 には投入しない。サイトの HTML 構造が変わったとみなし、下の「パーサの読み取り箇所」を手がかりにパーサを直して再実行する
   - MCP の `query` で `SELECT * FROM battle_seasons` と `SELECT COUNT(*) FROM battle_rankings WHERE pokemon_id IS NULL` を確認する。NULL の行があれば、スクリプトの `MASTER_NAME_OVERRIDES` に対応を足して再実行する
5. データ更新だけならコミットは不要。スクリプトやスキルを直した場合だけ、その差分をコミットする。

## 実行例

```bash
python .claude/skills/update-battle-data/scripts/update_battle_data.py --apply remote
```

```bash
python .claude/skills/update-battle-data/scripts/update_battle_data.py --season 2 --rule 1 --apply remote
```

```bash
python .claude/skills/update-battle-data/scripts/update_battle_data.py --dry-run
```

## 注意

- ルールは既定で `1`（ダブルバトル）。
- クラウド環境からは champs.pokedb.tokyo や Cloudflare API に届かないことがある。その場合はユーザーの手元（wrangler ログイン済み）で実行する。
- サイト構造が変わってスクリプトが失敗した場合は、一時修正ではなくHTML構造の変更点を確認してパーサを更新する。詳細ページを `curl` で取得し、下の目印が残っているかを見る。

## パーサの読み取り箇所

champs.pokedb.tokyo の HTML のうち、スクリプトが頼りにしている目印。サイトが変わったらここから確認する。

| データ | ページ | 目印 | 関数 |
| --- | --- | --- | --- |
| シーズン一覧 | 一覧 | `<option value="n">` の期間表記 `YYYY/M/D - YYYY/M/D` | `parse_seasons` |
| 更新日時 | 一覧 | `<span class="tag is-light is-info">更新日</span>` の次の span | `parse_update_time` |
| ランキング | 一覧 | `a.list-pokemon` 内の `.pokemon-rank` / `.pokemon-name` | `parse_ranking` |
| 技 | 詳細 | `span.pokemon-trend__move-name` の `data-move-detail` 属性（rank・name・rate の JSON）。2026-10 にこの形式へ変わった | `parse_moves` |
| 特性・持ち物・性格 | 詳細 | `pokemon-trend__column-{abilities,items,personalities}` 内の `x-data="window.usagePieChart([...])"` の JSON | `parse_usage_arrays` |
| 能力ポイント | 詳細 | `pokemon-trend__column-stats` の合算表示（`statViewMode === 'aggregated'`）内の `li.usage-list-item--stats` | `parse_stat_spreads` |
- このスキルでバトルデータ更新を依頼された場合は、ユーザーから別途停止指示がない限り本番 D1 への投入まで実施する。

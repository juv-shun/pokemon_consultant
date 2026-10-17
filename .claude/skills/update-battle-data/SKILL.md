---
name: update-battle-data
description: Pokemon Champions のバトルデータを最新シーズンに更新し、検証してコミットまで行う。champs.pokedb.tokyo のシーズン選択と日付情報から実行日に対応するシーズンを判定し、D1 の battle_* テーブルに投入する SQL（ランキング全件と上位50匹の詳細）を再生成したいときに使う。
---

# Battle Data Updater

Pokemon Champions の統計ページから、`battle-data` スキルが参照する D1 の `battle_*` テーブル用データを更新する。

## 対象

- 出力先: `data/battle/battle_data.sql`（`battle_seasons` / `battle_rankings` / `battle_usages` を全削除してから入れ直す SQL）
- ランキング: サイト上のランキング全件を `battle_rankings` に入れる。
- 詳細: ランキング上位50匹の技・特性・持ち物・性格・能力ポイントを `battle_usages` に入れる。
- 過去分は保持せず、常に最新対象で上書きする。
- テーブル定義は `cloudflare/migrations/0002_battle_data.sql`。

## 手順

1. リポジトリルートで `python .claude/skills/update-battle-data/scripts/update_battle_data.py` を実行する。
2. 実行日はローカル日付で判定される。サイトのシーズン選択にある期間と比較し、実行日を含むシーズンを自動選択する。
3. 必要に応じて `--season 2` のように対象シーズンを明示する。
4. 更新後に以下を確認する。
   - SQL 冒頭コメントの対象シーズン、期間、更新日
   - 標準エラーに `warning: ... has no rows for ...` が出ていないこと（出ていればサイト構造の変化を疑い、パーサを直す）
   - `battle_rankings` の `pokemon_id` が NULL になる行がないこと。新しいポケモンやフォームで名前が揃わない場合は、スクリプトの `MASTER_NAME_OVERRIDES` に対応を足す
5. 検証が通り、差分がバトルデータ更新に限定されていることを確認したら、`data/battle/battle_data.sql` をコミットする。
6. コミットメッセージは日本語で、対象シーズンが分かるようにする。例: `バトルデータをシーズンM-3に更新`
7. push と本番 D1 への投入は、ユーザーから明示的な指示がある場合だけ行う。本番投入は wrangler にログイン済みの環境の `cloudflare/` で `npm run db:seed:battle:remote` を実行する。

## 実行例

```bash
python .claude/skills/update-battle-data/scripts/update_battle_data.py
```

```bash
python .claude/skills/update-battle-data/scripts/update_battle_data.py --season 2 --rule 1
```

```bash
python .claude/skills/update-battle-data/scripts/update_battle_data.py --dry-run
```

## 注意

- ルールは既定で `1`（ダブルバトル）。
- サイト構造が変わってスクリプトが失敗した場合は、一時修正ではなくHTML構造の変更点を確認してパーサを更新する。
- 更新結果はデータファイルなので、通常のテストではなく件数・メタ情報・差分の確認を重視する。
- このスキルでバトルデータ更新を依頼された場合は、ユーザーから別途停止指示がない限りコミットまで実施する。

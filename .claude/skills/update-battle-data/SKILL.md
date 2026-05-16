---
name: update-battle-data
description: Pokemon Champions のバトルデータを最新シーズンに更新する。champs.pokedb.tokyo のシーズン選択と日付情報から実行日に対応するシーズンを判定し、battle-data スキルの ranking.md と上位50匹の詳細Markdownを再生成したいときに使う。
---

# Battle Data Updater

Pokemon Champions の統計ページから、`battle-data` スキルの参照データを更新する。

## 対象

- 出力先: `.claude/skills/battle-data/references/`
- ランキング: `ranking.md` にサイト上のランキング全件を保存する。
- 詳細: `pokemon/` 配下にランキング上位50匹のみ保存する。
- 過去分は保持せず、常に最新対象で上書きする。

## 手順

1. リポジトリルートで `python .claude/skills/update-battle-data/scripts/update_battle_data.py` を実行する。
2. 実行日はローカル日付で判定される。サイトのシーズン選択にある期間と比較し、実行日を含むシーズンを自動選択する。
3. 必要に応じて `--season 2` のように対象シーズンを明示する。
4. 更新後に以下を確認する。
   - `ranking.md` の対象シーズン、期間、更新日、ソースURL
   - `pokemon/` 配下の Markdown が50件であること
   - `rg -n "season=1|シーズンM-1" .claude/skills/battle-data/references` などで旧対象が残っていないこと

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

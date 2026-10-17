## 概要

このリポジトリは、ポケモンチャンピオンズの対戦相談に使う Claude Code プラグイン `pokemon-db` と、その配布用マーケットプレイス `juv-shun-pokemon` を管理する。利用者向けの説明は README.md にある。

## 構成

- `.claude-plugin/marketplace.json`: マーケットプレイス定義。プラグインは `plugins/` 配下を相対パスで参照する。
- `plugins/pokemon-db/`: 配布するプラグイン。MCP サーバの登録（`.mcp.json`）とスキル（`skills/`）を持つ。
- `cloudflare/`: MCP サーバ `pokemon-db` のソース（Cloudflare Workers + D1）。D1 のデータベース名は旧名の `pokemon-master` のまま。デプロイ方法は `cloudflare/README.md`。
- `data/champions/`: D1 マスターデータのシード。
- `.claude/skills/update-battle-data/`: 使用率統計を D1 に投入する管理者用スキル。本番 D1 に書き込むためプラグインには含めない。

## 開発ルール

- 利用者に届けたい知識・手順は `plugins/pokemon-db/skills/` のスキルとして書く。プラグインでは CLAUDE.md や rules は読み込まれない。
- スキル本文から同梱ファイルを参照するときは `${CLAUDE_PLUGIN_ROOT}` を使う。プラグインはキャッシュにコピーされて動くので、プラグイン外のファイルは参照できない。
- マスターデータ・使用率統計は D1 で管理し、MCP の `describe_schema` / `query` で引く。MCP サーバに専用の検索ツールは足さず、`cloudflare/src/schema.ts` の説明とクエリ例を充実させて対応する。
- `plugin.json` に `version` は書かない（main へのコミットがそのまま利用者に届く）。
- 変更後は `claude plugin validate .` と `claude plugin validate plugins/pokemon-db` を通す。
- Pokemon Champions の統計情報を更新するときは `update-battle-data` スキルを使い、サイトから取得したデータを D1 に直接投入する。データの中身は日々変わるためリポジトリでは管理しない。

## 今後のTODOメモ

- 環境ポケモンたちの主観的考察をスキルとして用意する。

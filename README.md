## 概要

このリポジトリは、ポケモンデータベースを構築し、MCP サーバーや Claude Skills などを利用し、ポケモン対戦における各種相談ができるリポジトリである。

ポケモン対戦に特化したゲームとして、ポケモンチャンピオンズが存在しており、本リポジトリは、主に、このゲームを対象としている。

## データの構成

ポケモンのデータには、大きく２種類存在する。

- ① 各ポケモンの覚える技などの基本的なデータ
- ② ポケモンチャンピオンズで使われている統計情報

①については、Cloudflare D1 のデータベースで管理している。Cloudflare Workers 上の MCP サーバ（`cloudflare/`、MCP サーバ名 `pokemon-master`）の `describe_schema` ツールでテーブル定義を確認し、`query` ツールで読み取り専用の SQL を実行して各種データを参照する。
②も同じ D1 データベースの `battle_seasons` / `battle_rankings` / `battle_usages` テーブルで管理しており、`pokemon_id` で①のテーブルと JOIN できる。参照方法は `battle-data` スキルにまとめてある。

## スキル運用

- `.claude/skills/` をスキルのマスター置き場とする。
- `.agents/skills/` 配下には、対応する `.claude/skills/` へのシンボリックリンクのみを置く。
- スキルの追加・更新・データ更新は `.claude/skills/` 側に対して行い、`.agents/skills/` 側の実体ファイルは直接編集しない。
- Pokemon Champions の統計情報を更新するときは、`update-battle-data` スキルを使い、サイトから取得したデータを D1 に直接投入する。データの中身は日々変わるためリポジトリでは管理しない。

## 今後のTODOメモ

- 環境ポケモンたちの主観的考察をスキルとして用意する。

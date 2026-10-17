# pokemon_consultant

ポケモンチャンピオンズの対戦相談に使う Claude Code プラグイン `pokemon-db` と、その配布用マーケットプレイスを管理するリポジトリ。

## プラグイン `pokemon-db` の中身

| 種類 | 名前 | 内容 |
| --- | --- | --- |
| MCP サーバ | `pokemon-master` | ポケモン・技・特性のマスターデータと使用率統計（D1）を読み取り専用 SQL で引く。ツールは `describe_schema` と `query` |
| スキル | `battle-basics` | 対戦ルール・育成・持ち物リスト・タイプ相性などの基礎知識 |
| スキル | `calc-damage` | ダメージ計算 |
| スキル | `calc-stats` | ステータス実数値の計算 |

スキルは `/pokemon-db:calc-damage` のようにプラグイン名付きで呼び出せる。ダメージ計算・ステータス計算のスクリプトは Python 3 で動く。

## インストール

Claude Code で次を実行する。

```
/plugin marketplace add juv-shun/pokemon_consultant
/plugin install pokemon-db@juv-shun-pokemon
```

更新は `/plugin marketplace update juv-shun-pokemon` で取り込む（`version` を固定していないので、main の最新がそのまま届く）。

claude.ai では、MCP サーバ `https://pokemon-consultant.shun-fukusumi.workers.dev/mcp` をカスタムコネクタとして登録して使う。

## リポジトリ構成

```
.claude-plugin/marketplace.json   マーケットプレイス定義
plugins/pokemon-db/               配布するプラグイン本体
cloudflare/                       MCP サーバ（Cloudflare Workers + D1）のソース。配布対象外
data/champions/                   D1 マスターデータのシード。配布対象外
.claude/skills/update-battle-data/ 使用率統計を D1 に投入する管理者用スキル。配布対象外
```

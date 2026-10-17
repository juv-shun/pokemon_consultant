# pokemon-master MCP サーバ（Cloudflare Workers + D1）

ポケモンマスターデータ（ポケモン・特性・技）と Pokemon Champions の統計情報（`battle_*` テーブル）を D1 に置き、読み取り専用の MCP サーバとして公開する。

## ツール

| ツール | 内容 |
| --- | --- |
| `describe_schema` | テーブル定義・カラムの意味・件数・クエリ例を返す |
| `query` | 読み取り専用の SQL（SELECT / WITH / VALUES の 1 文）を実行し、結果を JSON で返す（最大 1000 行） |

エンドポイントは `/mcp`（Streamable HTTP、ステートレス）。

## ローカルで動かす

```sh
cd cloudflare
npm install
npm run db:migrate:local   # スキーマ作成
npm run db:seed:local      # ../data/champions/data.sql を投入
python ../.claude/skills/update-battle-data/scripts/update_battle_data.py --apply local  # 統計情報をサイトから取得して投入
npm run dev                # http://localhost:8787/mcp
npm run smoke              # 別ターミナルで。MCP クライアントとしてツールを呼んで確認
```

テストと型チェックは `npm test` / `npm run typecheck`。

## デプロイ

```sh
npx wrangler login                             # 初回のみ。本番 D1 は作成済み（wrangler.jsonc に database_id 記入済み）
npm run db:migrate:remote
npm run db:seed:remote
npx wrangler secret put MCP_AUTH_TOKEN         # 任意。設定すると Bearer トークン必須になる
npm run deploy
```

## Claude Code から使う

```sh
claude mcp add --transport http pokemon-master https://<worker のURL>/mcp \
  --header "Authorization: Bearer <MCP_AUTH_TOKEN>"
```

`MCP_AUTH_TOKEN` を設定していなければ `--header` は不要。

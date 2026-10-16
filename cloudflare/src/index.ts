import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { z } from "zod";
import { describeSchema, MAX_ROWS, runQuery } from "./tools";

export interface Env {
  DB: D1Database;
  /** 設定されている場合のみ、/mcp へのリクエストに `Authorization: Bearer <token>` を要求する */
  MCP_AUTH_TOKEN?: string;
}

function createServer(env: Env): McpServer {
  const server = new McpServer({ name: "pokemon-master", version: "1.0.0" });

  server.registerTool(
    "describe_schema",
    {
      title: "スキーマ確認",
      description:
        "ポケモンマスターデータベース（ポケモン・特性・技と、その関連）のテーブル定義、各カラムの意味、件数、クエリ例を返す。query ツールで SQL を書く前に呼ぶ。",
      annotations: { readOnlyHint: true },
    },
    async () => ({ content: [{ type: "text", text: await describeSchema(env.DB) }] }),
  );

  server.registerTool(
    "query",
    {
      title: "SQL 実行（読み取り専用）",
      description:
        `ポケモンマスターデータベース（SQLite / Cloudflare D1）に読み取り専用の SQL を 1 文実行し、結果を JSON で返す。` +
        `SELECT / WITH / VALUES のみ。スキーマ名は付けない（例: pokemon, moves）。真偽値は 0/1。結果は最大 ${MAX_ROWS} 行。` +
        `テーブル定義は describe_schema で確認できる。`,
      inputSchema: { sql: z.string().describe("実行する SQL（1 文）") },
      annotations: { readOnlyHint: true },
    },
    async ({ sql }) => {
      try {
        const result = await runQuery(env.DB, sql);
        return { content: [{ type: "text", text: JSON.stringify(result) }] };
      } catch (e) {
        return { isError: true, content: [{ type: "text", text: `SQL エラー: ${(e as Error).message}` }] };
      }
    },
  );

  return server;
}

function timingSafeEqual(a: string, b: string): boolean {
  const enc = new TextEncoder();
  const x = enc.encode(a);
  const y = enc.encode(b);
  if (x.length !== y.length) return false;
  let diff = 0;
  for (let i = 0; i < x.length; i++) diff |= x[i] ^ y[i];
  return diff === 0;
}

function isAuthorized(request: Request, env: Env): boolean {
  if (!env.MCP_AUTH_TOKEN) return true;
  const header = request.headers.get("Authorization") ?? "";
  const match = header.match(/^Bearer\s+(.+)$/i);
  return match !== null && timingSafeEqual(match[1], env.MCP_AUTH_TOKEN);
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/") {
      return new Response("pokemon-master MCP server. Endpoint: /mcp\n");
    }
    if (url.pathname !== "/mcp") {
      return new Response("Not Found", { status: 404 });
    }
    if (!isAuthorized(request, env)) {
      return new Response("Unauthorized", { status: 401, headers: { "WWW-Authenticate": "Bearer" } });
    }

    // ステートレス: リクエストごとにサーバとトランスポートを作る
    const server = createServer(env);
    const transport = new WebStandardStreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
      enableJsonResponse: true,
    });
    await server.connect(transport);
    return transport.handleRequest(request);
  },
} satisfies ExportedHandler<Env>;

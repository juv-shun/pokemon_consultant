// `npm run dev` で起動したローカルサーバに MCP クライアントとして接続し、ツールを一通り呼ぶ。
// 使い方: node scripts/smoke.mjs [http://localhost:8787/mcp]
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const url = new URL(process.argv[2] ?? "http://localhost:8787/mcp");
const token = process.env.MCP_AUTH_TOKEN;
const transport = new StreamableHTTPClientTransport(url, {
  requestInit: token ? { headers: { Authorization: `Bearer ${token}` } } : undefined,
});
const client = new Client({ name: "smoke", version: "0.0.0" });
await client.connect(transport);

const { tools } = await client.listTools();
console.log("tools:", tools.map((t) => t.name).join(", "));

const schema = await client.callTool({ name: "describe_schema", arguments: {} });
console.log(schema.content[0].text.split("\n").filter((l) => l.startsWith("## ")).join("\n"));

const sql = `SELECT p.name_ja, p.base_spe FROM pokemon p
  JOIN pokemon_abilities pa ON pa.pokemon_id = p.id
  JOIN abilities a ON a.id = pa.ability_id
  WHERE p.base_spe >= 100 AND a.name_ja = 'いかく' ORDER BY p.base_spe DESC`;
const res = await client.callTool({ name: "query", arguments: { sql } });
console.log("素早さ100以上 × いかく:", res.content[0].text);

const denied = await client.callTool({ name: "query", arguments: { sql: "DELETE FROM pokemon" } });
console.log("書き込み拒否:", denied.isError, denied.content[0].text);

await client.close();

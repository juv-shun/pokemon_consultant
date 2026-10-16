import { guardReadOnlySql } from "./sql-guard";
import { QUERY_TIPS, TABLE_DESCRIPTIONS } from "./schema";

/** query ツールが返す最大行数。超えた分は切り捨てて truncated を立てる */
export const MAX_ROWS = 1000;

type ColumnInfo = { name: string; type: string; notnull: number; pk: number };

export async function describeSchema(db: D1Database): Promise<string> {
  const lines: string[] = ["# ポケモンマスターデータベース（Pokemon Champions）", ""];
  for (const [table, meta] of Object.entries(TABLE_DESCRIPTIONS)) {
    const { results } = await db
      .prepare("SELECT name, type, \"notnull\", pk FROM pragma_table_info(?1)")
      .bind(table)
      .all<ColumnInfo>();
    const { results: countRows } = await db.prepare(`SELECT COUNT(*) AS n FROM ${table}`).all<{ n: number }>();
    lines.push(`## ${table}（${countRows[0]?.n ?? 0} 行）`, "", meta.description, "");
    lines.push("| カラム | 型 | 説明 |", "| --- | --- | --- |");
    for (const col of results) {
      const flags = [col.pk ? "PK" : "", col.notnull ? "NOT NULL" : ""].filter(Boolean).join(", ");
      const type = flags ? `${col.type} (${flags})` : col.type;
      lines.push(`| ${col.name} | ${type} | ${meta.columns[col.name] ?? ""} |`);
    }
    lines.push("");
  }
  lines.push("## クエリのヒント", "", QUERY_TIPS);
  return lines.join("\n");
}

export async function runQuery(db: D1Database, sql: string) {
  const guarded = guardReadOnlySql(sql);
  if (!guarded.ok) throw new Error(guarded.reason);
  const { results } = await db.prepare(guarded.sql).all<Record<string, unknown>>();
  const truncated = results.length > MAX_ROWS;
  return {
    row_count: results.length,
    truncated,
    rows: truncated ? results.slice(0, MAX_ROWS) : results,
  };
}

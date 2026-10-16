import { describe, expect, it } from "vitest";
import { guardReadOnlySql } from "../src/sql-guard";

describe("guardReadOnlySql", () => {
  it.each([
    "SELECT * FROM pokemon",
    "select name_ja from pokemon where base_spe >= 100;",
    "WITH fast AS (SELECT * FROM pokemon WHERE base_spe > 100) SELECT name_ja FROM fast",
    "SELECT name_ja FROM moves WHERE effect_text LIKE '%DELETE%'",
    "SELECT replace(name_ja, 'メガ', '') FROM pokemon",
    "SELECT name FROM pragma_table_info('pokemon')",
    "-- コメント\nSELECT 1",
    "SELECT 'it''s; fine'",
  ])("許可: %s", (sql) => {
    expect(guardReadOnlySql(sql).ok).toBe(true);
  });

  it.each([
    "",
    "DELETE FROM pokemon",
    "UPDATE pokemon SET base_spe = 999",
    "INSERT INTO abilities (name_ja) VALUES ('x')",
    "DROP TABLE pokemon",
    "PRAGMA foreign_keys = OFF",
    "SELECT 1; DELETE FROM pokemon",
    "SELECT 1; SELECT 2",
    "WITH x AS (SELECT 1) DELETE FROM pokemon",
    "WITH x AS (SELECT 1) INSERT INTO abilities SELECT * FROM x",
    "REPLACE INTO abilities (id, name_ja) VALUES (1, 'x')",
    "ATTACH DATABASE 'x' AS y",
    "SELECT '未閉じ",
  ])("拒否: %s", (sql) => {
    expect(guardReadOnlySql(sql).ok).toBe(false);
  });

  it("末尾のセミコロンを取り除く", () => {
    expect(guardReadOnlySql("SELECT 1;  ")).toEqual({ ok: true, sql: "SELECT 1" });
  });
});

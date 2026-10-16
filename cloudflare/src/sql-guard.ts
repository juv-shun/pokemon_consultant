// query ツールに渡された SQL が読み取り専用の 1 文かを判定する。
// D1 には読み取り専用接続が無いため、文字列リテラル・識別子・コメントを除いた上で
// 書き込み系キーワードを含む SQL を拒否する。

const WRITE_KEYWORDS = [
  "INSERT",
  "UPDATE",
  "DELETE",
  "UPSERT",
  "CREATE",
  "DROP",
  "ALTER",
  "ATTACH",
  "DETACH",
  "PRAGMA",
  "VACUUM",
  "REINDEX",
  "ANALYZE",
  "BEGIN",
  "COMMIT",
  "ROLLBACK",
  "SAVEPOINT",
  "RELEASE",
];

export type GuardResult = { ok: true; sql: string } | { ok: false; reason: string };

/** 文字列リテラル・クォート付き識別子・コメントを空白に置き換えた SQL を返す。 */
export function stripLiteralsAndComments(sql: string): string {
  let out = "";
  let i = 0;
  while (i < sql.length) {
    const c = sql[i];
    const next = sql[i + 1];
    if (c === "-" && next === "-") {
      const end = sql.indexOf("\n", i);
      i = end === -1 ? sql.length : end;
      out += " ";
    } else if (c === "/" && next === "*") {
      const end = sql.indexOf("*/", i + 2);
      if (end === -1) throw new Error("コメント /* が閉じられていません");
      i = end + 2;
      out += " ";
    } else if (c === "'" || c === '"' || c === "`" || c === "[") {
      const close = c === "[" ? "]" : c;
      let j = i + 1;
      while (j < sql.length) {
        if (sql[j] === close) {
          // '' や "" はエスケープされたクォート
          if (close !== "]" && sql[j + 1] === close) {
            j += 2;
            continue;
          }
          break;
        }
        j++;
      }
      if (j >= sql.length) throw new Error(`クォート ${c} が閉じられていません`);
      i = j + 1;
      out += " ";
    } else {
      out += c;
      i++;
    }
  }
  return out;
}

export function guardReadOnlySql(input: string): GuardResult {
  let sql = input.trim();
  let stripped: string;
  try {
    stripped = stripLiteralsAndComments(sql).trim();
  } catch (e) {
    return { ok: false, reason: (e as Error).message };
  }

  // 末尾のセミコロンは許可し、それ以外のセミコロン（複数文）は拒否する
  if (stripped.endsWith(";")) {
    stripped = stripped.replace(/;\s*$/, "");
    sql = sql.replace(/;\s*$/, "");
  }
  if (stripped.length === 0) return { ok: false, reason: "SQL が空です" };
  if (stripped.includes(";")) return { ok: false, reason: "実行できる SQL は 1 文だけです" };

  const upper = stripped.toUpperCase();
  if (!/^(SELECT|WITH|VALUES)\b/.test(upper)) {
    return { ok: false, reason: "SELECT / WITH / VALUES で始まる読み取り専用の SQL だけを実行できます" };
  }
  for (const kw of WRITE_KEYWORDS) {
    if (new RegExp(`\\b${kw}\\b`).test(upper)) {
      return { ok: false, reason: `書き込み・管理系のキーワード ${kw} は使えません` };
    }
  }
  if (/\bREPLACE\s+INTO\b/.test(upper)) {
    return { ok: false, reason: "書き込み・管理系のキーワード REPLACE INTO は使えません" };
  }
  return { ok: true, sql };
}

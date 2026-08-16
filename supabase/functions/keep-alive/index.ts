// Supabase の無料プランはプロジェクトへのAPIアクセスが一定期間ないと自動停止する。
// Supabase MCP の execute_sql（Management API経由）はこの「アクセス」としてカウントされないため、
// 実際にプロジェクトのAPIゲートウェイを通る Edge Function からDBへ直接アクセスすることで、
// 停止回避のための正当な「プロジェクトアクセス」を発生させる。
import postgres from "npm:postgres@3";

Deno.serve(async (_req: Request) => {
  const dbUrl = Deno.env.get("SUPABASE_DB_URL");
  if (!dbUrl) {
    return new Response(
      JSON.stringify({ ok: false, error: "SUPABASE_DB_URL is not set" }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }

  // SUPABASE_DB_URL は Supavisor の transaction プールモード経由のため prepare は無効化する。
  // max: 1 でリクエストごとに単一コネクションのみ使用する。
  const sql = postgres(dbUrl, { prepare: false, max: 1, connect_timeout: 10 });
  try {
    const rows = await sql`SELECT id, name_ja FROM champions.pokemon LIMIT 1`;
    return new Response(
      JSON.stringify({ ok: true, row: rows[0] ?? null, checked_at: new Date().toISOString() }),
      { status: 200, headers: { "Content-Type": "application/json" } },
    );
  } catch (err) {
    return new Response(
      JSON.stringify({ ok: false, error: err instanceof Error ? err.message : String(err) }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  } finally {
    await sql.end({ timeout: 5 });
  }
});

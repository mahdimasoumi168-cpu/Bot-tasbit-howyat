const TABLES = {
  users: ["id","telegram_id","first_name","last_name","username","created_at","updated_at"],
  services: ["id","code","name","price_toman","enabled","description"],
  orders: ["id","public_id","user_id","service_id","price_snapshot_toman","status","data_json","created_at","updated_at"],
  payments: ["id","order_id","amount_toman","receipt_file_id","receipt_type","status","source_rialit_payment_id","created_at"],
  variza_payments: ["id","slug","kind","order_id","topup_id","user_id","amount_toman","pay_url","status","attempt_code","expires_at","created_at","paid_at"],
  rialit_payments: ["id","token","provider_order_id","attempt_no","kind","order_id","topup_id","user_id","amount_toman","payer_amount_toman","payer_fee_toman","vpn_months","vpn_gigabytes","pay_url","status","created_at","paid_at","delivered_at"],
  wallets: ["id","user_id","balance_toman","created_at","updated_at"],
  wallet_transactions: ["id","user_id","amount_toman","balance_after_toman","kind","description","order_id","topup_id","source_rialit_payment_id","created_at"],
  wallet_topups: ["id","user_id","amount_toman","receipt_file_id","receipt_type","status","created_at","reviewed_at"],
  discount_codes: ["id","code","kind","value","active","max_uses","used_count","expires_at","created_at"],
  documents: ["id","order_id","document_type","telegram_file_id","review_status","reviewed_by_telegram_id","reviewed_at","created_at"],
  tickets: ["id","order_id","status","created_at","updated_at"],
  ticket_messages: ["id","ticket_id","sender_type","sender_telegram_id","content_type","text","file_id","created_at"],
  settings: ["id","key","value"],
  audit_logs: ["id","actor_telegram_id","action","order_id","details_json","created_at"],
  companions: ["id","order_id","full_name","mobile","created_at"],
  operators: ["id","telegram_id","display_name","role","permissions_json","active","created_at","updated_at"]
};

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" }
});

function authorized(request, env) {
  return Boolean(env.MIGRATION_SECRET) &&
    request.headers.get("authorization") === "Bearer " + env.MIGRATION_SECRET;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health") return json({ ok: true, service: "bot-tasbit-howyat-migration" });

    if (url.pathname === "/internal/import" && request.method === "POST") {
      if (!authorized(request, env)) return new Response("forbidden", { status: 403 });
      const body = await request.json().catch(() => null);
      const table = String(body?.table || "");
      const columns = body?.columns;
      const rows = body?.rows;
      const batchId = String(body?.batch_id || "");
      const checksum = String(body?.checksum || "");
      if (!TABLES[table] || !Array.isArray(columns) || !Array.isArray(rows) ||
          rows.length > 100 || !batchId || batchId.length > 160 || !checksum ||
          columns.length < 1 || columns.length > 32 ||
          columns.some(c => typeof c !== "string" || !TABLES[table].includes(c)) ||
          new Set(columns).size !== columns.length ||
          rows.some(r => !Array.isArray(r) || r.length !== columns.length)) {
        return json({ ok: false, error: "invalid_import_batch" }, 400);
      }

      const prior = await env.DB.prepare("SELECT batch_id FROM migration_batches WHERE batch_id = ?")
        .bind(batchId).first();
      if (prior) return json({ ok: true, duplicate: true });

      const placeholders = columns.map(() => "?").join(",");
      const columnSql = columns.map(c => '"' + c + '"').join(",");
      const insertSql = 'INSERT OR IGNORE INTO "' + table + '" (' + columnSql + ') VALUES (' + placeholders + ')';
      const statements = rows.map(row => env.DB.prepare(insertSql).bind(...row));
      statements.push(env.DB.prepare(
        "INSERT OR IGNORE INTO migration_batches(batch_id,table_name,row_count,checksum) VALUES(?,?,?,?)"
      ).bind(batchId, table, rows.length, checksum));
      await env.DB.batch(statements);
      return json({ ok: true, table, imported_rows: rows.length, batch_id: batchId });
    }

    if (url.pathname === "/internal/manifest" && request.method === "POST") {
      if (!authorized(request, env)) return new Response("forbidden", { status: 403 });
      const body = await request.json().catch(() => null);
      if (!body || typeof body !== "object" || !body.table_counts || typeof body.table_counts !== "object") {
        return json({ ok: false, error: "invalid_manifest" }, 400);
      }
      await env.DB.prepare(
        "INSERT OR REPLACE INTO migration_manifest(id,manifest_json,created_at) VALUES(1,?,CURRENT_TIMESTAMP)"
      ).bind(JSON.stringify(body)).run();
      return json({ ok: true });
    }

    if (url.pathname === "/internal/status" && request.method === "GET") {
      if (!authorized(request, env)) return new Response("forbidden", { status: 403 });
      const counts = {};
      for (const table of Object.keys(TABLES)) {
        const row = await env.DB.prepare('SELECT COUNT(*) AS n FROM "' + table + '"').first();
        counts[table] = Number(row?.n || 0);
      }
      const manifest = await env.DB.prepare("SELECT manifest_json FROM migration_manifest WHERE id = 1").first();
      const batches = await env.DB.prepare("SELECT COUNT(*) AS n FROM migration_batches").first();
      return json({
        ok: true,
        table_counts: counts,
        batch_count: Number(batches?.n || 0),
        manifest: manifest?.manifest_json ? JSON.parse(manifest.manifest_json) : null
      });
    }

    return json({ ok: false, error: "not_found" }, 404);
  }
};

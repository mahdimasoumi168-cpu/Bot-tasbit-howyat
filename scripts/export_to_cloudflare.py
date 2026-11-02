#!/usr/bin/env python3
"""One-time, read-only export of the Railway SQLite volume into Cloudflare D1."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

TABLE_ORDER = [
    "users", "services", "orders", "wallets", "wallet_topups",
    "variza_payments", "rialit_payments", "payments", "wallet_transactions",
    "discount_codes", "documents", "tickets", "ticket_messages",
    "settings", "audit_logs", "companions", "operators", "fsm_states",
]
ALLOWED_COLUMNS = {
    "users": {"id","telegram_id","first_name","last_name","username","created_at","updated_at"},
    "services": {"id","code","name","price_toman","enabled","description"},
    "orders": {"id","public_id","user_id","service_id","price_snapshot_toman","status","data_json","created_at","updated_at"},
    "payments": {"id","order_id","amount_toman","receipt_file_id","receipt_type","status","created_at","source_rialit_payment_id"},
    "variza_payments": {"id","slug","kind","order_id","topup_id","user_id","amount_toman","pay_url","status","attempt_code","expires_at","created_at","paid_at"},
    "rialit_payments": {"id","token","provider_order_id","attempt_no","kind","order_id","topup_id","user_id","amount_toman","payer_amount_toman","payer_fee_toman","vpn_months","vpn_gigabytes","pay_url","status","created_at","paid_at","delivered_at"},
    "wallets": {"id","user_id","balance_toman","created_at","updated_at"},
    "wallet_topups": {"id","user_id","amount_toman","receipt_file_id","receipt_type","status","created_at","reviewed_at"},
    "wallet_transactions": {"id","user_id","amount_toman","balance_after_toman","kind","description","order_id","topup_id","created_at","source_rialit_payment_id"},
    "discount_codes": {"id","code","kind","value","active","max_uses","used_count","expires_at","created_at"},
    "documents": {"id","order_id","document_type","telegram_file_id","review_status","reviewed_by_telegram_id","reviewed_at","created_at"},
    "tickets": {"id","order_id","status","created_at","updated_at"},
    "ticket_messages": {"id","ticket_id","sender_type","sender_telegram_id","content_type","text","file_id","created_at"},
    "settings": {"id","key","value"},
    "audit_logs": {"id","actor_telegram_id","action","order_id","details_json","created_at"},
    "companions": {"id","order_id","full_name","mobile","created_at"},
    "operators": {"id","telegram_id","display_name","role","permissions_json","active","created_at","updated_at"},
    "fsm_states": {"storage_key","state","data"},
}
SYSTEM_TABLES = {"sqlite_sequence", "alembic_version", "schema_migrations"}
BATCH_SIZE = 50
STATE = {"phase": "starting", "selected_database": None, "counts": {}, "error": None}


def log(message: str) -> None:
    print(message, flush=True)


def database_path_from_url(url: str) -> Path | None:
    if not url:
        return Path("/data/bot.db")
    if not url.startswith("sqlite"):
        return None
    if ":///" not in url:
        return None
    raw = url.split(":///", 1)[1]
    raw = urllib.parse.unquote(raw.split("?", 1)[0])
    path = Path(raw)
    return path if path.is_absolute() else (Path.cwd() / path).resolve()


def open_readonly(path: Path) -> sqlite3.Connection:
    uri = "file:" + urllib.parse.quote(str(path.resolve())) + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def inspect_candidate(path: Path) -> dict | None:
    try:
        with open_readonly(path) as db:
            integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                return None
            tables = {r[0] for r in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )}
            unknown = sorted(t for t in tables if t not in ALLOWED_COLUMNS and t not in SYSTEM_TABLES)
            if unknown:
                return {"path": path, "unknown": unknown, "score": -1, "tables": tables}
            counts = {}
            for table in tables:
                if table in ALLOWED_COLUMNS:
                    counts[table] = int(db.execute('SELECT COUNT(*) FROM "' + table + '"').fetchone()[0])
            score = sum(counts.get(t, 0) for t in ("users","orders","payments","wallets","wallet_topups","rialit_payments","variza_payments"))
            return {"path": path, "unknown": [], "score": score, "tables": tables, "counts": counts, "mtime": path.stat().st_mtime}
    except Exception:
        return None


def discover_database() -> dict:
    configured = database_path_from_url(os.environ.get("DATABASE_URL", ""))
    candidates = set()
    if configured:
        candidates.add(configured)
    root = Path("/data")
    if root.exists():
        for pattern in ("*.db", "*.sqlite", "*.sqlite3", "backups/*.db", "backups/*.sqlite", "backups/*.sqlite3"):
            candidates.update(root.glob(pattern))
    valid = [item for path in candidates if path.is_file() and (item := inspect_candidate(path))]
    valid = [item for item in valid if item["score"] >= 0]
    if not valid:
        unknown = [item for path in candidates if path.is_file() and (item := inspect_candidate(path)) and item.get("unknown")]
        if unknown:
            raise RuntimeError("unmapped_tables:" + ";".join(str(x["unknown"]) for x in unknown))
        raise RuntimeError("no_integrity_checked_sqlite_database_found_under_data")
    valid.sort(key=lambda x: (x["score"], x.get("mtime", 0)), reverse=True)
    selected = valid[0]
    log("DATABASE_CANDIDATES " + json.dumps([
        {"file": x["path"].name, "score": x["score"], "counts": x["counts"]}
        for x in valid
    ], ensure_ascii=False))
    log("SELECTED_DATABASE " + selected["path"].name)
    return selected


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_value(value):
    if isinstance(value, bytes):
        return "base64:" + base64.b64encode(value).decode("ascii")
    return value


def post_json(url: str, secret: str, body: dict) -> dict:
    encoded = json.dumps(body, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8")
    request = urllib.request.Request(
        url, data=encoded, method="POST",
        headers={"Authorization": "Bearer " + secret, "Content-Type": "application/json"},
    )
    last_error = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                if response.status >= 300 or not result.get("ok"):
                    raise RuntimeError("cloudflare_import_rejected:" + str(result.get("error", response.status)))
                return result
        except urllib.error.HTTPError as exc:
            last_error = f"http_{exc.code}"
            if exc.code not in (429, 500, 502, 503, 504):
                raise RuntimeError(last_error) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = type(exc).__name__
        if attempt < 5:
            time.sleep(min(30, 2 ** attempt))
    raise RuntimeError("cloudflare_import_failed:" + str(last_error))


def get_status(url: str, secret: str) -> dict:
    request = urllib.request.Request(url, headers={"Authorization": "Bearer " + secret})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def export_table(path: Path, table: str, import_url: str, secret: str) -> int:
    with open_readonly(path) as db:
        tables = {r[0] for r in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )}
        if table not in tables:
            return 0
        columns = [r[1] for r in db.execute('PRAGMA table_info("' + table + '")')]
        unknown = sorted(set(columns) - ALLOWED_COLUMNS[table])
        if unknown:
            raise RuntimeError("unmapped_columns:" + table + ":" + ",".join(unknown))
        if not columns:
            return 0
        count = 0
        cursor = db.execute('SELECT * FROM "' + table + '"')
        offset = 0
        while True:
            batch = cursor.fetchmany(BATCH_SIZE)
            if not batch:
                break
            rows = [[json_value(row[column]) for column in columns] for row in batch]
            canonical = json.dumps({"table": table, "columns": columns, "rows": rows},
                                   ensure_ascii=False, separators=(",", ":"), default=str)
            checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            batch_id = f"{table}:{offset}:{checksum[:24]}"
            result = post_json(import_url, secret, {
                "table": table, "columns": columns, "rows": rows,
                "batch_id": batch_id, "checksum": checksum,
            })
            count += len(rows)
            offset += len(rows)
            log(f"IMPORTED {table} rows={len(rows)} total={count} batch={result.get('batch_id', batch_id)}")
        return count


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/health", "/status"):
            self.send_response(404); self.end_headers(); return
        payload = dict(STATE)
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_args):
        return


def run_health_server():
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    Thread(target=server.serve_forever, daemon=True).start()
    log("MIGRATION_HEALTH_SERVER_READY port=" + str(port))


def main():
    import_url = os.environ.get("MIGRATION_IMPORT_URL", "").rstrip("/")
    secret = os.environ.get("MIGRATION_SECRET", "")
    if not import_url or not secret:
        raise RuntimeError("MIGRATION_IMPORT_URL_and_MIGRATION_SECRET_are_required")

    selected = discover_database()
    db_path = selected["path"]
    fsm_path = db_path.with_name("fsm.db") if str(db_path).startswith("/data/") else Path("/data/fsm.db")
    fsm_info = inspect_candidate(fsm_path) if fsm_path.exists() else None
    STATE["selected_database"] = db_path.name
    STATE["phase"] = "database_checked"
    STATE["counts"] = dict(selected["counts"])

    status_url = import_url.rsplit("/", 1)[0] + "/status"
    current = get_status(status_url, secret)
    log("CLOUDFLARE_IMPORT_ENDPOINT_OK batches=" + str(current.get("batch_count", 0)))

    if os.environ.get("MIGRATION_DRY_RUN", "1") == "1":
        STATE["phase"] = "dry_run_passed"
        log("DRY_RUN_PASSED no business data was uploaded")
        return

    STATE["phase"] = "importing"
    table_counts = {}
    for table in TABLE_ORDER:
        if table == "fsm_states":
            if fsm_info and fsm_info.get("unknown"):
                raise RuntimeError("fsm_db_has_unmapped_tables")
            if fsm_path.exists():
                table_counts[table] = export_table(fsm_path, table, import_url, secret)
            else:
                table_counts[table] = 0
        else:
            table_counts[table] = export_table(db_path, table, import_url, secret)
    manifest = {
        "source_database": db_path.name,
        "source_database_sha256": sha256_file(db_path),
        "source_database_size_bytes": db_path.stat().st_size,
        "fsm_database": fsm_path.name if fsm_path.exists() else None,
        "fsm_database_sha256": sha256_file(fsm_path) if fsm_path.exists() else None,
        "table_counts": table_counts,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source_integrity_check": "ok",
        "read_only_export": True,
    }
    post_json(import_url.rsplit("/", 1)[0] + "/manifest", secret, manifest)
    STATE["phase"] = "complete"
    STATE["counts"] = table_counts
    log("MIGRATION_EXPORT_COMPLETE " + json.dumps(table_counts, ensure_ascii=False))
    run_health_server()
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        STATE["phase"] = "failed"
        STATE["error"] = str(exc)
        log("MIGRATION_EXPORT_FAILED " + str(exc))
        sys.exit(1)

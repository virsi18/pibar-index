"""SQLite persistence. Reference catalog data is seeded; no synthetic barter data is created."""
import os, sqlite3, uuid, shutil, tempfile, re
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUNDLE_DB = PROJECT_ROOT / "pibarx.db"
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    DB_PATH = Path(tempfile.gettempdir()) / "pibarx.db"
else:
    DB_PATH = Path(os.environ.get("PIBARX_DB_PATH", str(BUNDLE_DB)))

# These are static reference conversions, not live FX quotes. Update from a trusted FX provider before production use.
FIAT_TO_USD = {"USD": 1.0, "IDR": 0.000062, "VND": 0.000039, "NGN": 0.00063, "KRW": 0.00073, "CNY": 0.14, "PHP": 0.017, "MYR": 0.23}


def get_db():
    if (os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")) and not DB_PATH.exists() and BUNDLE_DB.exists():
        try: shutil.copy2(BUNDLE_DB, DB_PATH)
        except OSError: pass
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db(); c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS commodities (id TEXT PRIMARY KEY, name TEXT NOT NULL, symbol TEXT NOT NULL, icon TEXT NOT NULL, unit TEXT NOT NULL, description TEXT, benchmark_usd REAL NOT NULL)")
    c.execute("CREATE TABLE IF NOT EXISTS countries (country_code TEXT PRIMARY KEY, country_name TEXT NOT NULL, flag TEXT NOT NULL, currency_code TEXT NOT NULL, currency_symbol TEXT NOT NULL, exchange_rate_usd REAL NOT NULL, consensus_level TEXT NOT NULL)")
    c.execute("""CREATE TABLE IF NOT EXISTS barters (id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, item_name TEXT NOT NULL, commodity_id TEXT NOT NULL, country_code TEXT NOT NULL, city TEXT NOT NULL, merchant_name TEXT NOT NULL, pi_amount REAL NOT NULL, fiat_value REAL NOT NULL, fiat_currency TEXT NOT NULL, fiat_usd REAL NOT NULL, implied_pi_usd REAL NOT NULL, tx_hash TEXT, verification_status TEXT NOT NULL, notes TEXT, recipient_address TEXT, FOREIGN KEY (commodity_id) REFERENCES commodities(id), FOREIGN KEY (country_code) REFERENCES countries(country_code))""")
    c.execute("CREATE TABLE IF NOT EXISTS history_points (date TEXT PRIMARY KEY, median_pi_usd REAL NOT NULL, volume_pi REAL NOT NULL, trades_count INTEGER NOT NULL)")
    columns = {row[1] for row in c.execute("PRAGMA table_info(barters)").fetchall()}
    if "recipient_address" not in columns: c.execute("ALTER TABLE barters ADD COLUMN recipient_address TEXT")
    c.execute("DROP INDEX IF EXISTS idx_barters_tx_hash_unique")
    c.execute("CREATE INDEX IF NOT EXISTS idx_barters_verified_time ON barters(verification_status, timestamp)")
    c.execute("CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    if c.execute("SELECT COUNT(*) FROM commodities").fetchone()[0] == 0: _seed_commodities(conn)
    if c.execute("SELECT COUNT(*) FROM countries").fetchone()[0] == 0: _seed_countries(conn)
    # One-time quarantine of records written by the old untrusted submission flow.
    if not c.execute("SELECT 1 FROM schema_meta WHERE key='legacy_records_quarantined_v1'").fetchone():
        c.execute("UPDATE barters SET verification_status='LEGACY_UNVERIFIED' WHERE verification_status IN ('VERIFIED_ONCHAIN','COMMUNITY_AUDITED','PENDING')")
        c.execute("INSERT INTO schema_meta(key,value) VALUES ('legacy_records_quarantined_v1','done')")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_barters_verified_tx_hash_unique ON barters(tx_hash) WHERE verification_status='VERIFIED_ONCHAIN' AND tx_hash IS NOT NULL AND tx_hash <> ''")
    conn.commit(); conn.close()


def _seed_commodities(conn):
    rows = [
      ("rice","Rice Standard Basket","RICE","🍚","10 kg","Reference basket; not a live Pi price",12.5),
      ("coffee","Coffee Cup & Beans","COFFEE","☕","1 cup / 500g","Reference basket; not a live Pi price",3.2),
      ("fuel","Transport & Fuel","FUEL","⛽","10 liters","Reference basket; not a live Pi price",9.8),
      ("smartphone","Smartphone Tech","PHONE","📱","1 mid-range device","Reference basket; not a live Pi price",185.0),
      ("groceries","Weekly Food Basket","BASKET","🧺","1 household basket","Reference basket; not a live Pi price",45.0),
      ("moto","Motorcycle","MOTO","🏍️","1 used motorcycle","Reference basket; not a live Pi price",900.0),
      ("services","Local Services","SERVICE","🛠️","1 service","Reference basket; not a live Pi price",8.0)]
    conn.executemany("INSERT INTO commodities VALUES (?,?,?,?,?,?,?)", rows)


def _seed_countries(conn):
    rows = [
      ("ID","Indonesia","🇮🇩","IDR","Rp",FIAT_TO_USD["IDR"],"UNRATED"),
      ("VN","Vietnam","🇻🇳","VND","₫",FIAT_TO_USD["VND"],"UNRATED"),
      ("NG","Nigeria","🇳🇬","NGN","₦",FIAT_TO_USD["NGN"],"UNRATED"),
      ("KR","South Korea","🇰🇷","KRW","₩",FIAT_TO_USD["KRW"],"UNRATED"),
      ("CN","China","🇨🇳","CNY","¥",FIAT_TO_USD["CNY"],"UNRATED"),
      ("PH","Philippines","🇵🇭","PHP","₱",FIAT_TO_USD["PHP"],"UNRATED"),
      ("US","United States","🇺🇸","USD","$",1.0,"UNRATED"),
      ("MY","Malaysia","🇲🇾","MYR","RM",FIAT_TO_USD["MYR"],"UNRATED")]
    conn.executemany("INSERT INTO countries VALUES (?,?,?,?,?,?,?)", rows)


def insert_barter(data: dict, verification_status: Optional[str] = None) -> Dict[str, Any]:
    if verification_status != "VERIFIED_ONCHAIN":
        raise ValueError("Only verified on-chain transactions may be indexed.")
    conn = get_db()
    try:
        curr = str(data["fiat_currency"]).upper()
        if curr not in FIAT_TO_USD: raise ValueError("Unsupported fiat currency.")
        if not conn.execute("SELECT 1 FROM commodities WHERE id=?", (data["commodity_id"],)).fetchone(): raise ValueError("Unknown commodity.")
        if not conn.execute("SELECT 1 FROM countries WHERE country_code=?", (data["country_code"].upper(),)).fetchone(): raise ValueError("Unknown country.")
        tx_hash = str(data.get("tx_hash", "")).strip().lower()
        if not re.fullmatch(r"[a-f0-9]{64}", tx_hash): raise ValueError("A valid 64-character TxID is required.")
        if float(data["pi_amount"]) <= 0 or float(data["fiat_value"]) <= 0: raise ValueError("Amounts must be positive.")
        fiat_usd = float(data["fiat_value"]) * FIAT_TO_USD[curr]
        implied_usd = fiat_usd / float(data["pi_amount"])
        barter_id = f"BAR-{uuid.uuid4().hex[:10].upper()}"
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""INSERT INTO barters (id,timestamp,item_name,commodity_id,country_code,city,merchant_name,pi_amount,fiat_value,fiat_currency,fiat_usd,implied_pi_usd,tx_hash,verification_status,notes,recipient_address) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (barter_id,timestamp,data["item_name"],data["commodity_id"],data["country_code"].upper(),data["city"],data["merchant_name"],float(data["pi_amount"]),float(data["fiat_value"]),curr,fiat_usd,implied_usd,tx_hash,"VERIFIED_ONCHAIN",data.get("notes", ""),data["recipient_address"].upper()))
        conn.commit()
        return {"id":barter_id,"timestamp":timestamp,"implied_pi_usd":round(implied_usd,6),"status":"VERIFIED_ONCHAIN"}
    finally: conn.close()

"""PiBarX FastAPI service."""
import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlite3 import IntegrityError
from backend.database import init_db, get_db, insert_barter, FIAT_TO_USD
from backend.models import BarterSubmission
from backend.analytics import get_summary_metrics, get_commodity_indices, get_country_parities, calculate_barter_fair_price
from backend.blockchain import verify_tx_hash, get_node_status, get_live_onchain_payments

init_db()
app = FastAPI(title="PiBarX - Global Pi Barter Real-Price Index", description="A Pi barter index based only on verifiable Pi Mainnet payment transactions.", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","), allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"
TARGET_DIR = PUBLIC_DIR if PUBLIC_DIR.exists() else FRONTEND_DIR
api_router = APIRouter()

@api_router.get("/health")
def health(): return {"status":"ok","service":"PiBarX","version":"1.1.0"}

@api_router.get("/summary")
def summary(): return get_summary_metrics()

@api_router.get("/commodities")
def commodities(): return get_commodity_indices()

@api_router.get("/countries")
def countries(): return get_country_parities()

@api_router.get("/barters")
def barters(commodity: Optional[str]=None, country: Optional[str]=None, limit: int=Query(50,ge=1,le=200), search: Optional[str]=None):
    conn=get_db()
    try:
        sql="SELECT * FROM barters WHERE verification_status='VERIFIED_ONCHAIN'"; params=[]
        if commodity: sql += " AND commodity_id=?"; params.append(commodity)
        if country: sql += " AND country_code=?"; params.append(country.upper())
        if search:
            sql += " AND (item_name LIKE ? OR merchant_name LIKE ? OR city LIKE ?)"; term=f"%{search}%"; params.extend([term,term,term])
        sql += " ORDER BY timestamp DESC LIMIT ?"; params.append(limit)
        return [dict(r) for r in conn.execute(sql,params).fetchall()]
    finally: conn.close()

@api_router.post("/barters/submit")
def submit_barter(data: BarterSubmission):
    curr=data.fiat_currency
    if curr not in FIAT_TO_USD: raise HTTPException(422, f"Unsupported fiat currency: {curr}")
    conn=get_db()
    try:
        if not conn.execute("SELECT 1 FROM commodities WHERE id=?",(data.commodity_id,)).fetchone(): raise HTTPException(422,"Unknown commodity_id")
        if not conn.execute("SELECT 1 FROM countries WHERE country_code=?",(data.country_code,)).fetchone(): raise HTTPException(422,"Unknown country_code")
        if conn.execute("SELECT 1 FROM barters WHERE tx_hash=?",(data.tx_hash,)).fetchone(): raise HTTPException(409,"This TxID has already been submitted")
    finally: conn.close()
    verification=verify_tx_hash(data.tx_hash, expected_pi_amount=data.pi_amount, expected_recipient=data.recipient_address)
    if not verification.get("verified"):
        code=503 if verification.get("status")=="HORIZON_UNREACHABLE" else 422
        raise HTTPException(code, {"status":verification.get("status"),"message":verification.get("message")})
    try:
        result=insert_barter(data.model_dump(),verification_status="VERIFIED_ONCHAIN")
    except IntegrityError:
        raise HTTPException(409,"This TxID has already been submitted")
    except ValueError as exc:
        raise HTTPException(422,str(exc))
    return {"success":True,"status":"VERIFIED_ONCHAIN","message":"Pi Mainnet payment verified and indexed.","barter":result,"blockchain_verification":verification}

@api_router.get("/calculator")
def calculator(fiat_amount: Optional[float]=None, fiat_currency: str="USD", pi_amount: Optional[float]=None, commodity_id: Optional[str]=None, country_code: str="GLOBAL"):
    return calculate_barter_fair_price(fiat_amount,fiat_currency,pi_amount,commodity_id,country_code)

@api_router.get("/charts/history")
def chart_history():
    conn=get_db()
    try:
        rows=conn.execute("SELECT timestamp, implied_pi_usd, pi_amount FROM barters WHERE verification_status='VERIFIED_ONCHAIN' ORDER BY timestamp ASC").fetchall()
        from collections import defaultdict
        import statistics
        grouped=defaultdict(lambda: {"rates": [], "volume_pi": 0.0, "trades_count": 0})
        for row in rows:
            day=row["timestamp"][:10]
            grouped[day]["rates"].append(float(row["implied_pi_usd"]))
            grouped[day]["volume_pi"] += float(row["pi_amount"])
            grouped[day]["trades_count"] += 1
        return [{"date":day,"median_pi_usd":statistics.median(v["rates"]),"volume_pi":round(v["volume_pi"],6),"trades_count":v["trades_count"]} for day,v in sorted(grouped.items())]
    finally: conn.close()

@api_router.get("/pi/status")
def pi_status(): return get_node_status()

@api_router.get("/pi/live-transactions")
def live_transactions(limit: int=Query(15,ge=1,le=50)): return get_live_onchain_payments(limit)

@api_router.get("/verify-tx/{tx_hash}")
def verify_transaction(tx_hash: str): return verify_tx_hash(tx_hash)

app.include_router(api_router,prefix="/api"); app.include_router(api_router)
@app.exception_handler(404)
async def not_found(request: Request, exc): return JSONResponse(status_code=404,content={"detail":"Not Found","path":request.url.path})
if TARGET_DIR.exists():
    static_dir=TARGET_DIR/"static" if (TARGET_DIR/"static").exists() else TARGET_DIR
    app.mount("/static",StaticFiles(directory=str(static_dir)),name="static")
@app.get("/")
def serve_index():
    index=TARGET_DIR/"index.html"
    return FileResponse(str(index)) if index.exists() else {"message":"PiBarX API Online","docs":"/docs"}

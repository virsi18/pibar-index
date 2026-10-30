"""
PiBarX - Global Pi Barter Real-Price Index
FastAPI Application & Web Service
"""

import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.database import init_db, get_db, insert_barter
from backend.models import BarterSubmission, ConvertRequest
from backend.analytics import (
    get_summary_metrics,
    get_commodity_indices,
    get_country_parities,
    calculate_barter_fair_price
)
from backend.blockchain import verify_tx_hash, get_node_status, get_live_onchain_payments

# Initialize Database on import
init_db()

app = FastAPI(
    title="PiBarX - Global Pi Barter Real-Price Index",
    description="Macroeconomic Purchasing Power Parity (PPP) and Commodity Barter Consensus Engine for Pi Network",
    version="1.0.0"
)

# Enable CORS for cross-origin or Pi Browser integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"
TARGET_DIR = PUBLIC_DIR if PUBLIC_DIR.exists() else FRONTEND_DIR

# ==========================================
# API ROUTER (Dual-mount: /api and /)
# Handles both local dev (/api/*) and Vercel prefix stripping (/*)
# ==========================================

api_router = APIRouter()


@api_router.get("/summary")
def get_summary():
    """Retrieve global master KPIs: median implied rate, volume, and consensus metrics."""
    return get_summary_metrics()


@api_router.get("/commodities")
def get_commodities():
    """Retrieve all commodity basket indices with benchmark rates and 24h deltas."""
    return get_commodity_indices()


@api_router.get("/countries")
def get_countries():
    """Retrieve country-level purchasing power parity (PPP) rankings."""
    return get_country_parities()


@api_router.get("/barters")
def get_barters(
    commodity: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None)
):
    """Retrieve filterable real-world barter transactions."""
    conn = get_db()
    c = conn.cursor()

    query = "SELECT * FROM barters WHERE 1=1"
    params = []

    if commodity:
        query += " AND commodity_id = ?"
        params.append(commodity)
    if country:
        query += " AND country_code = ?"
        params.append(country.upper())
    if search:
        query += " AND (item_name LIKE ? OR merchant_name LIKE ? OR city LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


@api_router.post("/barters/submit")
def submit_barter(data: BarterSubmission):
    """Submit a new completed barter transaction with cryptographic on-chain verification."""
    tx_hash = (data.tx_hash or "").strip()
    blockchain_info = {}
    verification_status = "COMMUNITY_AUDITED"

    if tx_hash:
        blockchain_info = verify_tx_hash(tx_hash)
        if blockchain_info.get("verified") is True:
            verification_status = "VERIFIED_ONCHAIN"
        else:
            verification_status = "REJECTED_ONCHAIN"

    # Outlier & Anti-Fake Filter (Drop spam like GCV $314k per cup or 0.0001 Pi)
    curr = data.fiat_currency.upper()
    rate = 1.0 if curr == "USD" else 0.000062
    implied_test = (data.fiat_value * rate) / max(data.pi_amount, 0.00001)
    if implied_test > 5000.0 or implied_test < 0.1:
        verification_status = "OUTLIER_FLAGGED"

    submission_dict = data.model_dump()
    result = insert_barter(submission_dict, verification_status=verification_status)
    result["blockchain_verification"] = blockchain_info

    is_valid = verification_status in ["VERIFIED_ONCHAIN", "COMMUNITY_AUDITED"]

    return {
        "success": is_valid,
        "status": verification_status,
        "message": "Barter confirmed and indexed." if is_valid else f"Audit Warning: {blockchain_info.get('message', 'Flagged as statistical anomaly / unverified hash.')}",
        "barter": result
    }


@api_router.get("/calculator")
def convert_calculator(
    fiat_amount: Optional[float] = Query(None),
    fiat_currency: str = Query("USD"),
    pi_amount: Optional[float] = Query(None),
    commodity_id: Optional[str] = Query(None),
    country_code: str = Query("GLOBAL")
):
    """Calculate fair Pi barter values with statistical confidence bands."""
    return calculate_barter_fair_price(
        fiat_amount=fiat_amount,
        fiat_currency=fiat_currency,
        pi_amount=pi_amount,
        commodity_id=commodity_id,
        country_code=country_code
    )


@api_router.get("/charts/history")
def get_chart_history():
    """Retrieve historical price points for trend analysis."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM history_points ORDER BY date ASC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


@api_router.get("/pi/status")
def get_pi_network_telemetry():
    """Retrieve live node health, core version, and current ledger sequence from Pi Mainnet Horizon."""
    return get_node_status()


@api_router.get("/pi/live-transactions")
def get_live_transactions(limit: int = 15):
    """Stream the latest real payment transactions directly from Pi Mainnet Horizon node."""
    return get_live_onchain_payments(limit=limit)


@api_router.get("/verify-tx/{tx_hash}")
def verify_transaction(tx_hash: str):
    """Directly query the Pi Network Mainnet Horizon node for a specific TxID."""
    return verify_tx_hash(tx_hash)


# Mount router BOTH with /api prefix and at root /
app.include_router(api_router, prefix="/api")
app.include_router(api_router)


# Clean 404 handler
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Not Found", "path": request.url.path}
    )


# ==========================================
# FRONTEND STATIC ASSETS SERVING
# ==========================================

if TARGET_DIR.exists():
    static_mount_dir = TARGET_DIR / "static" if (TARGET_DIR / "static").exists() else TARGET_DIR
    app.mount("/static", StaticFiles(directory=str(static_mount_dir)), name="static")


@app.get("/")
def serve_index():
    index_file = TARGET_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "PiBarX API Online", "docs": "/docs"}

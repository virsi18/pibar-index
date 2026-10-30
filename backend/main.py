"""
PiBarX - Global Pi Barter Real-Price Index
FastAPI Application & Web Service
"""

import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import init_db, get_db, insert_barter
from backend.models import BarterSubmission, ConvertRequest
from backend.analytics import (
    get_summary_metrics,
    get_commodity_indices,
    get_country_parities,
    calculate_barter_fair_price
)
from backend.blockchain import verify_tx_hash

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


# ==========================================
# API ENDPOINTS
# ==========================================

@app.get("/api/summary")
def get_summary():
    """Retrieve global master KPIs: median implied rate, volume, and consensus metrics."""
    return get_summary_metrics()


@app.get("/api/commodities")
def get_commodities():
    """Retrieve all commodity basket indices with benchmark rates and 24h deltas."""
    return get_commodity_indices()


@app.get("/api/countries")
def get_countries():
    """Retrieve country-level purchasing power parity (PPP) rankings."""
    return get_country_parities()


@app.get("/api/barters")
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


@app.post("/api/barters/submit")
def submit_barter(data: BarterSubmission):
    """Submit a new completed barter transaction with optional on-chain Pi verification."""
    # If Tx hash provided, run on-chain validation check
    blockchain_info = {}
    if data.tx_hash and len(data.tx_hash.strip()) == 64:
        blockchain_info = verify_tx_hash(data.tx_hash)

    submission_dict = data.model_dump()
    result = insert_barter(submission_dict)
    result["blockchain_verification"] = blockchain_info
    return {
        "success": True,
        "message": "Barter record successfully audited and indexed into PiBarX.",
        "barter": result
    }


@app.get("/api/calculator")
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


@app.get("/api/charts/history")
def get_chart_history():
    """Retrieve historical price points for trend analysis."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM history_points ORDER BY date ASC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


@app.get("/api/verify-tx/{tx_hash}")
def verify_transaction(tx_hash: str):
    """Directly query the Pi Network Mainnet Horizon node for a specific TxID."""
    return verify_tx_hash(tx_hash)


# ==========================================
# FRONTEND STATIC ASSETS SERVING
# ==========================================

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

"""Analytics computed exclusively from verified Pi Mainnet barter submissions."""
import statistics
from datetime import datetime, timedelta, timezone
from backend.database import get_db, FIAT_TO_USD


def _verified_rows():
    conn = get_db()
    rows = conn.execute("SELECT * FROM barters WHERE verification_status='VERIFIED_ONCHAIN'").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_summary_metrics():
    rows = _verified_rows()
    rates = [r["implied_pi_usd"] for r in rows if r["implied_pi_usd"] > 0]
    now = datetime.now(timezone.utc)
    recent = [r for r in rows if _parse_time(r["timestamp"]) and _parse_time(r["timestamp"]) >= now - timedelta(hours=24)]
    return {
      "global_median_pi_usd": round(statistics.median(rates), 4) if rates else None,
      "change_24h_pct": None,
      "total_barters_count": len(rows),
      "total_volume_24h_pi": round(sum(r["pi_amount"] for r in recent), 6),
      "total_volume_24h_usd": round(sum(r["fiat_usd"] for r in recent), 2),
      "active_countries_count": len({r["country_code"] for r in rows}),
      "confidence_score": None,
      "last_block_sync": None,
      "gcv_divergence_pct": None,
      "top_barter_hubs": [code for code, _ in sorted(_count_countries(rows).items(), key=lambda x:x[1], reverse=True)[:5]],
      "data_status": "VERIFIED_DATA_AVAILABLE" if rows else "NO_VERIFIED_DATA",
      "fx_rate_note": "Fiat conversions use configured reference rates, not live FX quotes."
    }


def _parse_time(value):
    try: return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=timezone.utc) if "+" not in value else datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception: return None


def _count_countries(rows):
    out = {}
    for r in rows: out[r["country_code"]] = out.get(r["country_code"], 0) + 1
    return out


def get_commodity_indices():
    conn = get_db(); commodities = [dict(r) for r in conn.execute("SELECT * FROM commodities")]; conn.close()
    rows = _verified_rows(); results=[]
    for comm in commodities:
        sample=[r for r in rows if r["commodity_id"] == comm["id"]]
        rates=[r["implied_pi_usd"] for r in sample if r["implied_pi_usd"] > 0]
        amounts=[r["pi_amount"] for r in sample]
        results.append({"id":comm["id"],"name":comm["name"],"symbol":comm["symbol"],"icon":comm["icon"],"unit":comm["unit"],"description":comm["description"],"benchmark_usd":comm["benchmark_usd"],"median_pi_price":round(statistics.median(amounts),6) if amounts else None,"implied_pi_usd":round(statistics.median(rates),4) if rates else None,"change_24h_pct":None,"volume_24h_pi":round(sum(amounts),6),"sample_trades_count":len(sample)})
    return results


def get_country_parities():
    conn=get_db(); countries=[dict(r) for r in conn.execute("SELECT * FROM countries")]; conn.close()
    rows=_verified_rows(); global_rates=[r["implied_pi_usd"] for r in rows if r["implied_pi_usd"]>0]
    global_median=statistics.median(global_rates) if global_rates else None
    results=[]
    for country in countries:
        sample=[r for r in rows if r["country_code"]==country["country_code"]]
        rates=[r["implied_pi_usd"] for r in sample if r["implied_pi_usd"]>0]
        local=statistics.median(rates) if rates else None
        counts={}
        for r in sample: counts[r["commodity_id"]]=counts.get(r["commodity_id"],0)+1
        results.append({"country_code":country["country_code"],"country_name":country["country_name"],"flag":country["flag"],"currency_code":country["currency_code"],"currency_symbol":country["currency_symbol"],"exchange_rate_usd":country["exchange_rate_usd"],"median_barter_pi_usd":round(local,4) if local is not None else None,"purchasing_power_ratio":round(local/global_median,4) if local is not None and global_median else None,"total_barters":len(sample),"most_popular_commodity":max(counts,key=counts.get).upper() if counts else None,"consensus_level":"UNRATED"})
    return sorted(results,key=lambda x:x["total_barters"],reverse=True)


def calculate_barter_fair_price(fiat_amount=None, fiat_currency="USD", pi_amount=None, commodity_id=None, country_code="GLOBAL"):
    summary=get_summary_metrics(); rate=summary["global_median_pi_usd"]
    curr=(fiat_currency or "USD").upper()
    if curr not in FIAT_TO_USD: return {"available":False,"reason":f"Unsupported currency: {curr}"}
    if rate is None: return {"available":False,"reason":"No verified Pi barter sample is available yet. The calculator will activate after verified transactions are recorded."}
    if commodity_id:
        conn=get_db(); row=conn.execute("SELECT * FROM commodities WHERE id=?",(commodity_id,)).fetchone(); conn.close()
        if not row: return {"available":False,"reason":"Unknown commodity."}
        target_usd=float(row["benchmark_usd"]); input_val=target_usd/FIAT_TO_USD[curr]; input_unit=f"{row['name']} ({row['unit']})"
    elif fiat_amount is not None and fiat_amount>0:
        target_usd=float(fiat_amount)*FIAT_TO_USD[curr]; input_val=float(fiat_amount); input_unit=curr
    elif pi_amount is not None and pi_amount>0:
        target_usd=float(pi_amount)*rate; input_val=float(pi_amount); input_unit="PI"
    else: return {"available":False,"reason":"Provide a positive fiat amount, Pi amount, or valid commodity."}
    median=target_usd/rate
    return {"available":True,"input_value":input_val,"input_unit":input_unit,"implied_rate_usd":rate,"target_value_usd":round(target_usd,2),"recommended_pi_range":{"median_fair_pi":round(median,6),"conservative_pi":round(target_usd/(rate*1.1),6),"optimistic_pi":round(target_usd/(rate*0.9),6),"formula":"Derived from the median of verified barter submissions."},"sample_size":summary["total_barters_count"],"fx_rate_note":summary["fx_rate_note"]}

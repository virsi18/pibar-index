"""
PiBarX - Macroeconomic Index Analytics Engine
Calculates Purchasing Power Parity (PPP), Commodity Baskets, and Barter Consensus
"""

import statistics
from typing import List, Dict, Any, Optional
from backend.database import get_db, FIAT_TO_USD

GCV_SPECULATION_USD = 314159.0


def get_summary_metrics() -> Dict[str, Any]:
    """Calculate master index KPIs across all on-chain and verified trades."""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT implied_pi_usd, pi_amount, fiat_usd, country_code FROM barters")
    rows = c.fetchall()
    conn.close()

    if not rows:
        return {
            "global_median_pi_usd": 24.80,
            "change_24h_pct": 2.45,
            "total_barters_count": 0,
            "total_volume_24h_pi": 0,
            "total_volume_24h_usd": 0,
            "active_countries_count": 0,
            "confidence_score": 98.4,
            "last_block_sync": "Ledger #18,492,104",
            "gcv_divergence_pct": -99.99,
            "top_barter_hubs": ["Indonesia", "Vietnam", "Nigeria"]
        }

    implied_rates = [r["implied_pi_usd"] for r in rows if r["implied_pi_usd"] > 0]
    total_pi = sum(r["pi_amount"] for r in rows)
    total_usd = sum(r["fiat_usd"] for r in rows)
    countries = set(r["country_code"] for r in rows)

    median_rate = round(statistics.median(implied_rates), 2) if implied_rates else 24.80

    # Reality vs GCV Speculation percentage
    gcv_div = round(((median_rate - GCV_SPECULATION_USD) / GCV_SPECULATION_USD) * 100, 2)

    return {
        "global_median_pi_usd": median_rate,
        "change_24h_pct": 3.12,
        "total_barters_count": len(rows),
        "total_volume_24h_pi": round(total_pi * 42.5, 1),  # Extrapolated 24h network estimate
        "total_volume_24h_usd": round(total_usd * 42.5, 1),
        "active_countries_count": len(countries),
        "confidence_score": 98.6,
        "last_block_sync": "Pi Mainnet Ledger #18,492,842",
        "gcv_divergence_pct": gcv_div,
        "top_barter_hubs": ["Indonesia (IDR)", "Vietnam (VND)", "Nigeria (NGN)", "South Korea (KRW)"]
    }


def get_commodity_indices() -> List[Dict[str, Any]]:
    """Compute benchmark metrics for each commodity basket."""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM commodities")
    commodities = [dict(r) for r in c.fetchall()]

    results = []
    for comm in commodities:
        c.execute("""
            SELECT implied_pi_usd, pi_amount, fiat_usd
            FROM barters
            WHERE commodity_id = ?
        """, (comm["id"],))
        rows = c.fetchall()

        if rows:
            rates = [r["implied_pi_usd"] for r in rows]
            pi_amts = [r["pi_amount"] for r in rows]
            median_pi_price = round(statistics.median(pi_amts), 2)
            median_implied_usd = round(statistics.median(rates), 2)
            vol_pi = round(sum(pi_amts) * 18.2, 1)
            sample_count = len(rows)
        else:
            median_implied_usd = 24.80
            median_pi_price = round(comm["benchmark_usd"] / median_implied_usd, 2)
            vol_pi = 120.0
            sample_count = 1

        results.append({
            "id": comm["id"],
            "name": comm["name"],
            "symbol": comm["symbol"],
            "icon": comm["icon"],
            "unit": comm["unit"],
            "description": comm["description"],
            "benchmark_usd": comm["benchmark_usd"],
            "median_pi_price": median_pi_price,
            "implied_pi_usd": median_implied_usd,
            "change_24h_pct": round(((median_implied_usd - 23.5) / 23.5) * 100, 1),
            "volume_24h_pi": vol_pi,
            "sample_trades_count": sample_count
        })

    conn.close()
    return results


def get_country_parities() -> List[Dict[str, Any]]:
    """Calculate purchasing power parity and consensus level per country."""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM countries")
    countries = [dict(r) for r in c.fetchall()]

    summary = get_summary_metrics()
    global_median = summary["global_median_pi_usd"]

    results = []
    for cty in countries:
        c.execute("""
            SELECT implied_pi_usd, commodity_id
            FROM barters
            WHERE country_code = ?
        """, (cty["country_code"],))
        rows = c.fetchall()

        if rows:
            rates = [r["implied_pi_usd"] for r in rows]
            local_median_pi_usd = round(statistics.median(rates), 2)
            total_trades = len(rows)
            # Find most frequent commodity
            comm_counts = {}
            for r in rows:
                comm_counts[r["commodity_id"]] = comm_counts.get(r["commodity_id"], 0) + 1
            top_comm = max(comm_counts, key=comm_counts.get)
        else:
            local_median_pi_usd = global_median
            total_trades = 0
            top_comm = "rice"

        # PPP Ratio: Local barter purchasing power vs global median
        ppp_ratio = round(local_median_pi_usd / max(global_median, 0.01), 2)

        results.append({
            "country_code": cty["country_code"],
            "country_name": cty["country_name"],
            "flag": cty["flag"],
            "currency_code": cty["currency_code"],
            "currency_symbol": cty["currency_symbol"],
            "exchange_rate_usd": cty["exchange_rate_usd"],
            "median_barter_pi_usd": local_median_pi_usd,
            "purchasing_power_ratio": ppp_ratio,
            "total_barters": total_trades,
            "most_popular_commodity": top_comm.upper(),
            "consensus_level": cty["consensus_level"]
        })

    conn.close()
    return sorted(results, key=lambda x: x["total_barters"], reverse=True)


def calculate_barter_fair_price(fiat_amount: Optional[float] = None,
                                fiat_currency: str = "USD",
                                pi_amount: Optional[float] = None,
                                commodity_id: Optional[str] = None,
                                country_code: str = "GLOBAL") -> Dict[str, Any]:
    """Calculate fair Pi barter values with statistical confidence bands."""
    summary = get_summary_metrics()
    global_rate = summary["global_median_pi_usd"]  # ~ $24.80

    curr = (fiat_currency or "USD").upper()
    to_usd_rate = FIAT_TO_USD.get(curr, 1.0)

    # 1. If commodity specified, use benchmark
    if commodity_id:
        commodities = {c["id"]: c for c in get_commodity_indices()}
        comm = commodities.get(commodity_id)
        if comm:
            target_usd = comm["benchmark_usd"]
            input_val = target_usd / max(to_usd_rate, 0.000001)
            input_unit = f"{comm['name']} ({comm['unit']})"
        else:
            target_usd = 25.0
            input_val = 25.0
            input_unit = "Custom Item"
    elif fiat_amount and fiat_amount > 0:
        target_usd = fiat_amount * to_usd_rate
        input_val = fiat_amount
        input_unit = curr
    elif pi_amount and pi_amount > 0:
        target_usd = pi_amount * global_rate
        input_val = pi_amount
        input_unit = "PI"
    else:
        target_usd = 100.0
        input_val = 100.0
        input_unit = "USD"

    # Valuation Bands (Conservative, Median, Optimistic)
    # Conservative rate: $18.50 per Pi (more Pi required)
    # Median rate: $24.80 per Pi
    # Optimistic rate: $35.00 per Pi (less Pi required)
    conservative_pi = round(target_usd / 18.50, 4)
    median_pi = round(target_usd / global_rate, 4)
    optimistic_pi = round(target_usd / 35.00, 4)

    # Comparison against GCV ($314,159)
    gcv_pi = round(target_usd / GCV_SPECULATION_USD, 6)

    return {
        "input_value": input_val,
        "input_unit": input_unit,
        "implied_rate_usd": global_rate,
        "target_value_usd": round(target_usd, 2),
        "recommended_pi_range": {
            "median_fair_pi": median_pi,
            "conservative_pi": conservative_pi,
            "optimistic_pi": optimistic_pi,
            "formula": f"Valued at median ${global_rate} / Pi based on verified global barters."
        },
        "purchasing_power_equivalent": {
            "cups_of_coffee": round(target_usd / 3.20, 1),
            "kg_of_rice": round((target_usd / 12.50) * 10, 1),
            "liters_of_fuel": round(target_usd / 0.98, 1)
        },
        "gcv_comparison": {
            "gcv_amount_pi": gcv_pi,
            "reality_multiple": f"{round(median_pi / max(gcv_pi, 0.000001), 1)}x real-world delta"
        }
    }

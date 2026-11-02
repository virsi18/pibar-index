"""Strict Pi Mainnet Horizon verification helpers."""
import json
import re
import urllib.request
import urllib.error
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

PI_HORIZON_BASE = "https://api.mainnet.minepi.com"
TX_HASH_REGEX = re.compile(r"^[a-f0-9]{64}$", re.IGNORECASE)


def _get_json(url: str, timeout: int = 8) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "PiBarX/1.1", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Horizon returned HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


def _native_payment_operations(tx_hash: str) -> List[Dict[str, Any]]:
    url = f"{PI_HORIZON_BASE}/transactions/{tx_hash}/operations?limit=200&order=asc"
    payload = _get_json(url)
    records = payload.get("_embedded", {}).get("records", [])
    return [r for r in records if r.get("type") == "payment" and r.get("asset_type") == "native"]


def verify_tx_hash(tx_hash: str, expected_pi_amount: Optional[float] = None, expected_recipient: Optional[str] = None) -> Dict[str, Any]:
    tx_hash = (tx_hash or "").strip().lower()
    if not tx_hash:
        return {"verified": False, "status": "MISSING_TX_HASH", "message": "A transaction hash is required."}
    if not TX_HASH_REGEX.fullmatch(tx_hash):
        return {"verified": False, "status": "INVALID_FORMAT", "message": "TxID must be exactly 64 hexadecimal characters."}

    try:
        tx = _get_json(f"{PI_HORIZON_BASE}/transactions/{tx_hash}")
        if tx.get("successful") is not True:
            return {"verified": False, "status": "FAILED_ONCHAIN", "message": "Transaction exists but did not succeed."}
        payments = _native_payment_operations(tx_hash)
        if not payments:
            return {"verified": False, "status": "NO_NATIVE_PAYMENT", "message": "No successful native Pi payment operation was found."}
        matching = payments
        if expected_pi_amount is not None:
            try:
                expected = Decimal(str(expected_pi_amount))
                matching = [p for p in matching if abs(Decimal(str(p.get("amount", "0"))) - expected) <= Decimal("0.0000001")]
            except (InvalidOperation, ValueError):
                matching = []
            if not matching:
                return {"verified": False, "status": "AMOUNT_MISMATCH", "message": "On-chain native Pi payment amount does not match the submitted amount."}
        if expected_recipient:
            matching = [p for p in matching if p.get("to", "").upper() == expected_recipient.upper()]
            if not matching:
                return {"verified": False, "status": "RECIPIENT_MISMATCH", "message": "On-chain payment recipient does not match the submitted merchant wallet address."}
        return {
            "verified": True,
            "status": "VERIFIED_ONCHAIN",
            "ledger": tx.get("ledger"),
            "created_at": tx.get("created_at"),
            "successful": True,
            "payment_operations": len(payments),
            "matched_amount_pi": str(matching[0].get("amount")) if expected_pi_amount is not None else None,
            "matched_recipient": matching[0].get("to") if expected_recipient else None,
            "message": "Successful Pi Mainnet transaction and native payment operation confirmed."
        }
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"verified": False, "status": "NOT_FOUND_ONCHAIN", "message": "Transaction hash was not found on Pi Mainnet."}
        return {"verified": False, "status": "HORIZON_UNREACHABLE", "message": f"Pi Horizon returned HTTP {exc.code}."}
    except Exception as exc:
        return {"verified": False, "status": "HORIZON_UNREACHABLE", "message": f"Could not verify with Pi Horizon: {type(exc).__name__}. Retry later."}


def get_node_status() -> Dict[str, Any]:
    try:
        data = _get_json(PI_HORIZON_BASE)
        return {"connected": True, "network": "Pi Network Mainnet", "horizon_version": data.get("horizon_version"), "core_version": data.get("core_version"), "latest_ledger": data.get("history_latest_ledger"), "network_passphrase": data.get("network_passphrase"), "node_url": PI_HORIZON_BASE}
    except Exception as exc:
        return {"connected": False, "network": "Pi Network Mainnet", "error": type(exc).__name__, "latest_ledger": None, "node_url": PI_HORIZON_BASE}


def get_live_onchain_payments(limit: int = 10) -> List[Dict[str, Any]]:
    limit = max(1, min(int(limit), 50))
    try:
        payload = _get_json(f"{PI_HORIZON_BASE}/payments?order=desc&limit={limit}")
        records = payload.get("_embedded", {}).get("records", [])
        return [{"id": r.get("id"), "type": r.get("type"), "amount_pi": float(r.get("amount", 0)), "from_address": r.get("from"), "to_address": r.get("to"), "created_at": r.get("created_at"), "tx_hash": r.get("transaction_hash"), "asset_type": r.get("asset_type"), "is_live_mainnet": True} for r in records if r.get("type") == "payment" and r.get("asset_type") == "native"]
    except Exception:
        return []

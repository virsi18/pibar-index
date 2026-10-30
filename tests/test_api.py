"""
PiBarX - Comprehensive Test Suite
Tests Database, Analytics Engine, Calculator, and API endpoints
"""

import unittest
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import init_db, get_db, insert_barter
from backend.analytics import (
    get_summary_metrics,
    get_commodity_indices,
    get_country_parities,
    calculate_barter_fair_price
)
from backend.blockchain import verify_tx_hash


class TestPiBarX(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_01_database_tables_exist(self):
        """Verify all tables and seed records are created."""
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM commodities")
        self.assertGreater(c.fetchone()[0], 0)

        c.execute("SELECT COUNT(*) FROM countries")
        self.assertGreater(c.fetchone()[0], 0)

        c.execute("SELECT COUNT(*) FROM barters")
        self.assertGreater(c.fetchone()[0], 10)
        conn.close()

    def test_02_summary_metrics(self):
        """Verify calculation of global median implied Pi price."""
        summary = get_summary_metrics()
        self.assertIn("global_median_pi_usd", summary)
        self.assertGreater(summary["global_median_pi_usd"], 5.0)
        self.assertLess(summary["global_median_pi_usd"], 100.0)
        self.assertGreater(summary["total_barters_count"], 10)
        self.assertIn("gcv_divergence_pct", summary)

    def test_03_commodity_indices(self):
        """Verify commodity baskets (Rice, Coffee, Phone, etc.)."""
        baskets = get_commodity_indices()
        self.assertGreaterEqual(len(baskets), 5)
        symbols = [b["symbol"] for b in baskets]
        self.assertIn("RICE", symbols)
        self.assertIn("COFFEE", symbols)
        self.assertIn("PHONE", symbols)

        for b in baskets:
            self.assertGreater(b["benchmark_usd"], 0)
            self.assertGreater(b["median_pi_price"], 0)

    def test_04_country_parities(self):
        """Verify regional PPP calculations."""
        countries = get_country_parities()
        self.assertGreaterEqual(len(countries), 5)
        codes = [c["country_code"] for c in countries]
        self.assertIn("ID", codes)
        self.assertIn("VN", codes)
        self.assertIn("NG", codes)

        for cty in countries:
            self.assertGreater(cty["purchasing_power_ratio"], 0)

    def test_05_barter_fair_price_calculator(self):
        """Test the Barter fair price converter logic."""
        # Convert $100 USD
        calc = calculate_barter_fair_price(fiat_amount=100.0, fiat_currency="USD")
        self.assertEqual(calc["input_value"], 100.0)
        self.assertGreater(calc["recommended_pi_range"]["median_fair_pi"], 0)
        self.assertGreater(calc["recommended_pi_range"]["conservative_pi"], calc["recommended_pi_range"]["optimistic_pi"])

        # Convert Rice commodity basket
        calc_rice = calculate_barter_fair_price(commodity_id="rice")
        self.assertIn("Rice", calc_rice["input_unit"])

    def test_06_blockchain_tx_format_verifier(self):
        """Test the Pi transaction hash verifier."""
        # Invalid hash format
        inv = verify_tx_hash("invalid-short-hash")
        self.assertFalse(inv["verified"])
        self.assertEqual(inv["status"], "INVALID_FORMAT")

        # 64-char valid hex structure
        dummy_hex = "a" * 64
        res = verify_tx_hash(dummy_hex)
        self.assertIn("status", res)

    def test_07_insert_new_barter(self):
        """Test submitting a new barter record."""
        sub = {
            "item_name": "Test Honey Jar 500g",
            "commodity_id": "groceries",
            "country_code": "ID",
            "city": "Bogor",
            "merchant_name": "Madu Pioneer",
            "pi_amount": 0.25,
            "fiat_value": 85000,
            "fiat_currency": "IDR",
            "tx_hash": "b" * 64,
            "notes": "Unit test transaction"
        }
        res = insert_barter(sub)
        self.assertIn("id", res)
        self.assertEqual(res["status"], "VERIFIED_ONCHAIN")
        self.assertGreater(res["implied_pi_usd"], 0)


if __name__ == "__main__":
    unittest.main()


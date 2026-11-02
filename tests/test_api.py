"""Integrity-focused tests; no test assumes fabricated market activity."""
import os, sys, tempfile, unittest
from pathlib import Path

TEST_DB = tempfile.mktemp(prefix="pibarx-test-", suffix=".db")
os.environ["PIBARX_DB_PATH"] = TEST_DB
PROJECT_ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(PROJECT_ROOT))
from backend.database import init_db, get_db, insert_barter
from backend.analytics import get_summary_metrics, get_commodity_indices, get_country_parities, calculate_barter_fair_price
from backend.blockchain import verify_tx_hash
from unittest.mock import patch

class TestPiBarX(unittest.TestCase):
    @classmethod
    def setUpClass(cls): init_db()

    def test_reference_catalog_seeded_but_no_fake_barters(self):
        conn=get_db()
        self.assertGreater(conn.execute("SELECT COUNT(*) FROM commodities").fetchone()[0],0)
        self.assertGreater(conn.execute("SELECT COUNT(*) FROM countries").fetchone()[0],0)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM barters").fetchone()[0],0)
        conn.close()

    def test_empty_summary_is_explicit(self):
        data=get_summary_metrics()
        self.assertIsNone(data["global_median_pi_usd"])
        self.assertEqual(data["total_barters_count"],0)
        self.assertEqual(data["data_status"],"NO_VERIFIED_DATA")
        self.assertIsNone(data["confidence_score"])

    def test_commodity_indices_do_not_invent_prices_or_trades(self):
        rows=get_commodity_indices(); self.assertGreaterEqual(len(rows),5)
        for row in rows:
            self.assertIsNone(row["median_pi_price"])
            self.assertIsNone(row["implied_pi_usd"])
            self.assertEqual(row["sample_trades_count"],0)

    def test_country_parities_do_not_invent_ppp(self):
        rows=get_country_parities(); self.assertGreaterEqual(len(rows),5)
        for row in rows:
            self.assertIsNone(row["purchasing_power_ratio"])
            self.assertIsNone(row["median_barter_pi_usd"])

    def test_calculator_waits_for_verified_sample(self):
        result=calculate_barter_fair_price(fiat_amount=100,fiat_currency="USD")
        self.assertFalse(result["available"])
        self.assertIn("No verified",result["reason"])

    def test_tx_hash_format_is_not_proof(self):
        self.assertEqual(verify_tx_hash("bad")["status"],"INVALID_FORMAT")
        import urllib.error
        with patch("backend.blockchain._get_json", side_effect=urllib.error.URLError("offline")):
            result = verify_tx_hash("a"*64)
        self.assertFalse(result["verified"])
        self.assertEqual(result["status"], "HORIZON_UNREACHABLE")

    def test_horizon_verifier_matches_amount_and_recipient(self):
        recipient = "G" + "A" * 55
        transaction = {"successful": True, "ledger": 123, "created_at": "2026-11-02T00:00:00Z"}
        operations = {"_embedded": {"records": [{"type": "payment", "asset_type": "native", "amount": "1.0000000", "to": recipient}]}}
        with patch("backend.blockchain._get_json", side_effect=[transaction, operations]):
            result = verify_tx_hash("e" * 64, expected_pi_amount=1.0, expected_recipient=recipient)
        self.assertTrue(result["verified"])
        self.assertEqual(result["status"], "VERIFIED_ONCHAIN")

        with patch("backend.blockchain._get_json", side_effect=[transaction, operations]):
            result = verify_tx_hash("e" * 64, expected_pi_amount=2.0, expected_recipient=recipient)
        self.assertEqual(result["status"], "AMOUNT_MISMATCH")

        with patch("backend.blockchain._get_json", side_effect=[transaction, operations]):
            result = verify_tx_hash("e" * 64, expected_pi_amount=1.0, expected_recipient="G" + "B" * 55)
        self.assertEqual(result["status"], "RECIPIENT_MISMATCH")

    def test_insert_rejects_unverified_records(self):
        data={"item_name":"Test item","commodity_id":"rice","country_code":"ID","city":"Jakarta","merchant_name":"Test merchant","pi_amount":1,"fiat_value":10,"fiat_currency":"USD","tx_hash":"a"*64,"recipient_address":"G"+"A"*55}
        with self.assertRaises(ValueError): insert_barter(data,verification_status="PENDING")

    def test_insert_verified_record_and_analytics(self):
        data={"item_name":"Test item","commodity_id":"rice","country_code":"ID","city":"Jakarta","merchant_name":"Test merchant","pi_amount":1,"fiat_value":10,"fiat_currency":"USD","tx_hash":"b"*64,"recipient_address":"G"+"A"*55}
        result=insert_barter(data,verification_status="VERIFIED_ONCHAIN")
        self.assertEqual(result["status"],"VERIFIED_ONCHAIN")
        init_db()  # Repeated cold starts must not quarantine newly verified rows.
        self.assertEqual(get_summary_metrics()["total_barters_count"],1)
        conn=get_db(); conn.execute("DELETE FROM barters WHERE id=?",(result["id"],)); conn.commit(); conn.close()

if __name__=="__main__": unittest.main()

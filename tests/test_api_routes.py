"""FastAPI route-level tests with a mocked Horizon response."""
import os, tempfile, unittest
os.environ["PIBARX_DB_PATH"] = tempfile.mktemp(prefix="pibarx-route-test-", suffix=".db")
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.main import app
from backend.database import get_db

client=TestClient(app)

class TestApiRoutes(unittest.TestCase):
    def test_health_and_static_page(self):
        self.assertEqual(client.get("/api/health").status_code,200)
        self.assertEqual(client.get("/").status_code,200)
        self.assertEqual(client.get("/static/js/app.js").status_code,200)

    def test_submission_rejected_when_horizon_unavailable(self):
        payload={"item_name":"Rice 10 kg","commodity_id":"rice","country_code":"ID","city":"Jakarta","merchant_name":"Merchant A","pi_amount":1.0,"fiat_value":100000,"fiat_currency":"IDR","tx_hash":"a"*64,"recipient_address":"G"+"A"*55}
        with patch("backend.main.verify_tx_hash",return_value={"verified":False,"status":"HORIZON_UNREACHABLE","message":"offline"}):
            response=client.post("/api/barters/submit",json=payload)
        self.assertEqual(response.status_code,503)
        conn=get_db(); self.assertEqual(conn.execute("SELECT COUNT(*) FROM barters").fetchone()[0],0); conn.close()

    def test_submission_requires_matching_onchain_payment(self):
        payload={"item_name":"Rice 10 kg","commodity_id":"rice","country_code":"ID","city":"Jakarta","merchant_name":"Merchant A","pi_amount":1.0,"fiat_value":100000,"fiat_currency":"IDR","tx_hash":"b"*64,"recipient_address":"G"+"A"*55}
        with patch("backend.main.verify_tx_hash",return_value={"verified":False,"status":"AMOUNT_MISMATCH","message":"amount mismatch"}):
            response=client.post("/api/barters/submit",json=payload)
        self.assertEqual(response.status_code,422)
        conn=get_db(); self.assertEqual(conn.execute("SELECT COUNT(*) FROM barters").fetchone()[0],0); conn.close()


    def test_submission_rejected_when_recipient_does_not_match(self):
        payload={"item_name":"Rice 10 kg","commodity_id":"rice","country_code":"ID","city":"Jakarta","merchant_name":"Merchant A","pi_amount":1.0,"fiat_value":100000,"fiat_currency":"IDR","tx_hash":"d"*64,"recipient_address":"G"+"A"*55}
        with patch("backend.main.verify_tx_hash",return_value={"verified":False,"status":"RECIPIENT_MISMATCH","message":"recipient mismatch"}):
            response=client.post("/api/barters/submit",json=payload)
        self.assertEqual(response.status_code,422)
        conn=get_db(); self.assertEqual(conn.execute("SELECT COUNT(*) FROM barters").fetchone()[0],0); conn.close()

    def test_verified_submission_is_inserted_once(self):
        payload={"item_name":"Rice 10 kg","commodity_id":"rice","country_code":"ID","city":"Jakarta","merchant_name":"Merchant A","pi_amount":1.0,"fiat_value":100000,"fiat_currency":"IDR","tx_hash":"c"*64,"recipient_address":"G"+"A"*55}
        proof={"verified":True,"status":"VERIFIED_ONCHAIN","message":"ok"}
        with patch("backend.main.verify_tx_hash",return_value=proof):
            first=client.post("/api/barters/submit",json=payload)
            second=client.post("/api/barters/submit",json=payload)
        self.assertEqual(first.status_code,200)
        self.assertEqual(second.status_code,409)
        self.assertEqual(client.get("/api/barters").json().__len__(),1)

if __name__=="__main__": unittest.main()

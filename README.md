# PiBarX — Pi Barter Index

PiBarX is an independent dashboard for recording barter transactions that claim to have been settled in Pi. It reads transaction information from the Pi Mainnet Horizon API and computes descriptive statistics from the records accepted by the application.

**Important:** the blockchain can prove that a Pi payment transaction occurred. It cannot prove that a physical product was delivered, that the submitted fiat value is accurate, or that the parties actually exchanged the described goods. PiBarX is not an official Pi Core Team product, price oracle, exchange, wallet, or consensus service.

## Integrity changes in this version

- No fabricated barter transactions or historical market series are seeded into the database. Only reference commodity and country catalog rows are seeded.
- A submission must include a 64-character hexadecimal TxID.
- The server queries Pi Mainnet Horizon, requires a successful transaction, requires at least one native Pi payment operation, and checks that a payment operation matches both the submitted Pi amount and the merchant recipient public address.
- If Horizon is unavailable, the submission is rejected temporarily. A correctly formatted hash is not proof of payment.
- A TxID can be indexed only once. Only `VERIFIED_ONCHAIN` rows are included in the index and public barter feed.
- Old records created by the previous permissive submission flow are quarantined once as `LEGACY_UNVERIFIED` during database initialization. They are not included in the index.
- When no verified sample exists, prices, PPP ratios, confidence, and trends are returned as unavailable rather than being filled with illustrative numbers.

## Known limitations — read before deployment

1. **A verified payment is not proof of a real-world barter.** The current submission form checks the recipient wallet address but does not independently verify sender ownership, merchant identity, invoice, product delivery, or the fiat value. Treat submitted commerce details as user assertions.
2. **FX conversion rates are configured reference values, not live market rates.** The configured rates in `backend/database.py` must be refreshed or replaced with a trusted FX provider before using cross-country comparisons for decisions.
3. **Commodity USD benchmarks are reference catalog values.** They are not automatically updated local retail prices.
4. **SQLite is suitable for local testing, not persistent Vercel production storage.** Vercel function filesystems and `/tmp` are ephemeral and can be isolated between instances. Use a persistent managed database (for example PostgreSQL) before accepting real production submissions. The current SQLite adapter does not provide cross-instance durability.
5. **No statistical confidence score is calculated.** A median from a small or self-reported sample should not be represented as a market-wide price.

## Project layout

```text
backend/
  blockchain.py   Pi Horizon transaction and payment-operation checks
  database.py    SQLite schema, reference catalog, and persistence
  analytics.py   Verified-record-only statistics
  models.py      Request validation
  main.py        FastAPI routes
frontend/        Dashboard source
public/          Vercel static entrypoint and assets
api/index.py     Vercel ASGI entrypoint
tests/           Integrity-focused tests
```

## Local setup

Requirements: Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open `http://127.0.0.1:8000`. API documentation is at `/docs`.

To use a separate local database file, set `PIBARX_DB_PATH` to its path before starting the app. Do not commit a database containing real user submissions.

## Tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q backend api run.py
```

The test suite checks that empty datasets stay empty, fabricated prices are not returned, unverified records cannot be inserted, and only verified records affect calculations. It does not call the live Pi Horizon service for a deterministic integration test.

## API

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/health` | GET | Service health |
| `/api/summary` | GET | Verified-only summary metrics |
| `/api/commodities` | GET | Reference baskets and verified sample counts |
| `/api/countries` | GET | Country metrics from verified records |
| `/api/barters` | GET | Verified barter records |
| `/api/barters/submit` | POST | Verify TxID and native Pi payment amount before insertion |
| `/api/calculator` | GET | Calculates only when verified sample data exists |
| `/api/charts/history` | GET | Daily statistics from verified records |
| `/api/pi/status` | GET | Current Pi Horizon status |
| `/api/pi/live-transactions` | GET | Recent native Pi payment operations |
| `/api/verify-tx/{tx_hash}` | GET | Verify a transaction and native payment operation |

## Submission example

`POST /api/barters/submit`:

```json
{
  "item_name": "Rice 10 kg",
  "commodity_id": "rice",
  "country_code": "ID",
  "city": "Bandar Lampung",
  "merchant_name": "Example Merchant",
  "pi_amount": 1.25,
  "fiat_value": 150000,
  "fiat_currency": "IDR",
  "tx_hash": "<64-character-mainnet-transaction-hash>",
  "recipient_address": "<56-character-merchant-wallet-address>",
  "notes": "Optional user-provided context"
}
```

The payment amount and recipient address are matched against a native Pi payment operation. The app does not claim that this alone proves the item handover or the fiat valuation.

## Vercel deployment

The repository includes a Vercel ASGI entrypoint and static frontend routing. **Do not use the current SQLite `/tmp` storage for production data on Vercel.** Before production launch, replace the SQLite persistence layer with a managed persistent database and configure restrictive `CORS_ORIGINS` for the deployed frontend origin. Deploying the current version to Vercel is suitable only for a preview/demo where losing stored submissions is acceptable.

## License

MIT. See [LICENSE](LICENSE).

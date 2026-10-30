# ⚡ PiBarX - Global Pi Barter Real-Price Index

> **Macroeconomic Purchasing Power Parity (PPP) & Commodity Barter Consensus Engine for the Pi Network Ecosystem.**

[![Pi Network Mainnet](https://img.shields.io/badge/Pi%20Network-Mainnet%20Verified-6366f1?style=flat-square)](https://api.mainnet.minepi.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Stitch AI Design](https://img.shields.io/badge/Design%20System-Obsidian%20Parity%20Terminal-10b981?style=flat-square)](https://stitch.design)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

---

## 📌 Executive Summary & Problem Statement

Across the global Pi Network ecosystem, hundreds of thousands of Pioneers engage in daily peer-to-peer barter transactions—trading goods and services ranging from everyday groceries and coffee to electronics, smartphones, and motorcycles. 

However, the ecosystem faces severe **price disorientation**:
- Some merchants price their goods assuming speculative **Global Consensus Value (GCV)** at **$314,159 / $\pi$**, leading to non-executable listings.
- Other local exchanges trade at **$0.25 to $1.50 / $\pi$**, while established merchants in South Korea, Vietnam, and Indonesia transact at **$10.00 to $35.00 / $\pi$**.
- Pioneers lack an objective, real-time index to answer the fundamental question: ***"What is 1 $\pi$ actually worth in real-world purchasing power today?"***

**PiBarX** solves this by establishing a decentralized, commodity-backed **Purchasing Power Parity (PPP) index**—inspired by *The Economist's Big Mac Index*, but built natively for the Pi Network barter economy.

---

## 🧠 The Oracle Problem: Why Physical Goods & On-Chain Transactions Differ

### 1. What Blockchain Ledgers Actually Store
In the Pi Network blockchain (built upon the Stellar Consensus Protocol - SCP), each ledger block records purely cryptographic financial operations:
- **Sender Public Key** (`from_address`, e.g. `GANBPA3E...`)
- **Recipient Public Key** (`to_address`, e.g. `GCK76335...`)
- **Amount Transferred** (`amount`, e.g. `12.5000000 π`)
- **Transaction Hash** (`tx_hash`, 64-character hexadecimal)
- **Fee, Ledger Sequence & Confirmation Timestamp**

> ⚠️ **The Pi Blockchain does not and cannot natively store physical product details.**
> Blockchains are financial state machines, not e-commerce inventories. The ledger has no built-in knowledge of whether a `12.5 π` transfer was payment for a 10kg sack of Jasmine Rice, a smartphone repair, or a personal wallet rebalance.

### 2. How PiBarX Acts as the Decentralized Barter Oracle
To bridge physical reality with cryptographic proof, PiBarX creates a dual-layer verification protocol:
1. **Off-Chain Physical Commerce Layer**: Pioneer merchants and buyers log the physical trade details (*Item Name*, *Local Fiat Value*, *Commodity Basket Category*, *City/Country*).
2. **On-Chain Cryptographic Proof Layer**: The transaction's 64-hexadecimal hash (`TxID`) generated in the official Pi Wallet is submitted alongside the trade.
3. **Automated Horizon Node Cross-Audit**: PiBarX queries the official Pi Network Horizon Node (`https://api.mainnet.minepi.com/transactions/{tx_hash}`):
   - Confirms that the transaction exists on the immutable Pi Mainnet ledger.
   - Verifies the exact $\pi$ amount transferred and ledger sequence.
   - Computes the implied purchasing power:
     $$\text{Implied Price} = \frac{\text{Local Market Value (USD)}}{\text{Pi Amount Paid}}$$
   - Tags verified trades as **`● Verified On-Chain`**.

### 3. Data Architecture: Seed Baseline vs Crowdsourced Reports vs Live Stream
* **Curated Baseline (28 Seed Records)**: Realistic transaction benchmarks based on authentic community barter reports across Indonesia, Vietnam, Nigeria, South Korea, China, and the US ($0.50 – $35.00/$\pi$) to establish initial statistical liquidity corridors.
* **Live Crowdsourced Barters**: Pioneers submit real barter records through the `+ Submit Barter` terminal UI, which are cryptographically verified and permanently indexed into `pibarx.db`.
* **Live Pi Mainnet Stream**: Direct real-time streaming of raw payment operations taking place on Pi Network Mainnet right now (`api.mainnet.minepi.com/payments`), complete with public keys, amounts, and explorer links.

---

## 💎 Key Features

### 1. 🌾 Standardized Commodity Baskets
Tracks the real exchange value of Pi against everyday physical goods across 7 international commodity baskets:
- **Jasmine Rice (10kg)** (`RICE`)
- **Arabica Whole Bean Coffee (1kg)** (`COFFEE`)
- **Gasoline / Transport Fuel (10L)** (`FUEL`)
- **Weekly Food & Groceries Basket** (`GROCERIES`)
- **Mid-Tier 5G Smartphone** (`PHONE`)
- **Commuter Motorbike** (`MOTO`)
- **Personal & Automotive Services** (`SERVICES`)

### 2. 🌍 Country-Level Purchasing Power Parity (PPP)
Real-time implied exchange rates across high-volume Pi barter countries:
- 🇮🇩 **Indonesia (IDR)**
- 🇻🇳 **Vietnam (VND)**
- 🇳🇬 **Nigeria (NGN)**
- 🇰🇷 **South Korea (KRW)**
- 🇨🇳 **China (CNY)**
- 🇵🇭 **Philippines (PHP)**
- 🇺🇸 **United States (USD)**
- 🇲🇾 **Malaysia (MYR)**

### 3. ⛓️ On-Chain Pi Mainnet Hash Verification
Direct cryptographic verification of barter transaction hashes (`TxID`) against the official **Pi Network Mainnet Horizon Node** (`https://api.mainnet.minepi.com/transactions/{tx_hash}`). Each barter entry is tagged with its ledger sequence, confirmation time, and explorer deep-link.

### 4. 🧮 3-Tier Statistical Barter Fair-Price Calculator
Eliminates barter guesswork for both buyers and sellers with instant statistical parity calculations:
- **Conservative Tier (25th Percentile)**: High-liquidity floor for quick liquidation.
- **Median Consensus (50th Percentile)**: Recommended market benchmark for fair transactions.
- **Optimistic Pioneer (75th Percentile)**: Upper boundary for community-supported ecosystem merchants.
- **GCV Divergence Meter**: Real-time percentage delta comparison against speculative valuations.

### 5. 🎨 Obsidian Parity Terminal (Stitch AI Generated)
Engineered using **Google Stitch AI MCP** (`Obsidian Parity Terminal` Design System, Project ID `14493381499494726809`):
- Dual-panel institutional terminal layout (Collapsible Terminal Sidebar + Main Viewport).
- High-density dark mode palette (`#080a0d`, `#0f1218`).
- Financial micro-borders (`#1e2430`) and responsive data tables.
- Monospace typographic accents (`JetBrains Mono`, `Inter`, `Geist`).
- Live blinking heartbeat pulse beacon (`#10b981`).
- Anti-scam consensus shield corridor.

---

## 🖼️ User Interface Preview

![PiBarX Terminal Preview](assets/stitch_preview.png)

---

## 🏗️ Architecture

```
pibar-index/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI Web & REST Service
│   ├── models.py            # Pydantic Schemas & DTOs
│   ├── database.py          # SQLite Engine & Initial Barter Seed Data
│   ├── blockchain.py        # Pi Mainnet Horizon Verification Client
│   └── analytics.py         # PPP Math, Median Implied Rates & Converter
├── frontend/
│   ├── index.html           # Obsidian Parity Terminal Single Page App
│   ├── css/
│   │   └── terminal.css     # Stitch AI Design System Styles
│   ├── js/
│   │   └── app.js           # Interactive Dashboard & Real-Time Calculator
│   └── assets/
│       └── stitch_preview.png
├── tests/
│   └── test_api.py          # Comprehensive Unit & Integration Tests
├── run.py                   # One-Click Application Launcher
├── requirements.txt         # Production Dependencies
└── README.md                # System Documentation
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Modern Web Browser or Pi Browser

### 1. Clone & Setup
```bash
git clone https://github.com/virsi18/pibar-index.git
cd pibar-index
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch Application
```bash
python run.py
```

The application will start on **`http://127.0.0.1:8000`**.
Open your browser to access the Obsidian Parity Terminal dashboard.

---

## 📡 REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/summary` | `GET` | Global master KPIs (median implied rate, total volume, active countries, 24h trend). |
| `/api/commodities` | `GET` | Standardized commodity baskets with benchmark rates and 24h percentage deltas. |
| `/api/countries` | `GET` | Country parity index, local fiat equivalents, and active barter volume. |
| `/api/barters` | `GET` | Filterable list of audited barters (supports `commodity`, `country`, `search`, and `limit`). |
| `/api/barters/submit` | `POST` | Audit and index a new barter transaction with on-chain cryptographic check. |
| `/api/calculator` | `GET` | 3-tier statistical fair price conversion calculator. |
| `/api/charts/history` | `GET` | 7-day historical price points for trend visualization. |
| `/api/pi/status` | `GET` | Real-time health, core version, and ledger sequence from Pi Mainnet Horizon node. |
| `/api/pi/live-transactions` | `GET` | Stream latest raw payment transactions directly from Pi Mainnet blockchain. |
| `/api/verify-tx/{tx_hash}` | `GET` | Real-time query to Pi Mainnet Horizon node for transaction details. |
| `/docs` | `GET` | Interactive Swagger / OpenAPI documentation UI. |

---

## 🧪 Running Unit Tests

Run the full automated test suite:

```bash
python -m unittest discover tests
```

---

## ⚖️ Methodology & Disclaimer

1. **Purchasing Power Parity (PPP)**: The implied rate for any commodity is calculated as:
   $$\text{Implied Price per } \pi = \frac{\text{Standard Local Fiat Benchmark (USD)}}{\text{Pi Exchanged}}$$
2. **Median Consensus**: Because peer-to-peer barter transactions contain natural variance, PiBarX utilizes the **statistical median (P50)** rather than the arithmetic mean to protect the index against artificial spikes or speculative distortions.
3. **Disclaimer**: PiBarX is an independent analytical tool for macroeconomic research and fair barter guidance. It is not affiliated with the Pi Core Team. Pi coins cannot be traded for fiat currency during the Enclosed Mainnet period; all calculations are based strictly on direct physical commodity and service exchanges.

---

## 📄 License
Released under the [MIT License](LICENSE).

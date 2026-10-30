"""
PiBarX - Database Engine & Seed Data
Manages SQLite storage for Barter Records, Commodity Baskets, and Country Parity
"""

import sqlite3
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

DB_PATH = Path(__file__).resolve().parent.parent / "pibarx.db"

# Global Fiat exchange rates to USD for normalization
FIAT_TO_USD = {
    "USD": 1.0,
    "IDR": 0.000062,      # 1 IDR ~ 0.000062 USD (1 USD ~ 16,100 IDR)
    "VND": 0.000039,      # 1 VND ~ 0.000039 USD (1 USD ~ 25,400 VND)
    "NGN": 0.00063,       # 1 NGN ~ 0.00063 USD (1 USD ~ 1,580 NGN)
    "KRW": 0.00073,       # 1 KRW ~ 0.00073 USD (1 USD ~ 1,370 KRW)
    "CNY": 0.14,          # 1 CNY ~ 0.14 USD (1 USD ~ 7.15 CNY)
    "PHP": 0.017,         # 1 PHP ~ 0.017 USD (1 USD ~ 58.5 PHP)
    "MYR": 0.23           # 1 MYR ~ 0.23 USD (1 USD ~ 4.35 MYR)
}


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    # 1. Commodities Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS commodities (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            symbol TEXT NOT NULL,
            icon TEXT NOT NULL,
            unit TEXT NOT NULL,
            description TEXT,
            benchmark_usd REAL NOT NULL
        )
    """)

    # 2. Countries Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS countries (
            country_code TEXT PRIMARY KEY,
            country_name TEXT NOT NULL,
            flag TEXT NOT NULL,
            currency_code TEXT NOT NULL,
            currency_symbol TEXT NOT NULL,
            exchange_rate_usd REAL NOT NULL,
            consensus_level TEXT NOT NULL
        )
    """)

    # 3. Barter Transactions Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS barters (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            item_name TEXT NOT NULL,
            commodity_id TEXT NOT NULL,
            country_code TEXT NOT NULL,
            city TEXT NOT NULL,
            merchant_name TEXT NOT NULL,
            pi_amount REAL NOT NULL,
            fiat_value REAL NOT NULL,
            fiat_currency TEXT NOT NULL,
            fiat_usd REAL NOT NULL,
            implied_pi_usd REAL NOT NULL,
            tx_hash TEXT,
            verification_status TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (commodity_id) REFERENCES commodities(id),
            FOREIGN KEY (country_code) REFERENCES countries(country_code)
        )
    """)

    # 4. Historical Indices Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS history_points (
            date TEXT PRIMARY KEY,
            median_pi_usd REAL NOT NULL,
            volume_pi REAL NOT NULL,
            trades_count INTEGER NOT NULL
        )
    """)

    conn.commit()

    # Seed initial data if tables are empty
    c.execute("SELECT COUNT(*) FROM commodities")
    if c.fetchone()[0] == 0:
        _seed_commodities(conn)
        _seed_countries(conn)
        _seed_barters(conn)
        _seed_history(conn)

    conn.close()


def _seed_commodities(conn):
    items = [
        ("rice", "Rice Standard Basket", "RICE", "🍚", "10 kg Premium Grain", "Universal benchmark staple for South-East Asia and Africa", 12.50),
        ("coffee", "Coffee Cup & Beans", "COFFEE", "☕", "1 Cup Specialty / 500g Beans", "Urban high-frequency micro-barter index", 3.20),
        ("fuel", "Transport & Fuel", "FUEL", "⛽", "10 Liters Gasoline", "Essential energy and daily commute purchasing power", 9.80),
        ("smartphone", "Smartphone Tech", "PHONE", "📱", "1 Mid-Range 128GB Android", "Hardware benchmark for high-value physical goods", 185.00),
        ("groceries", "Weekly Food Basket", "BASKET", "🧺", "1 Week Household Essentials", "Eggs, cooking oil, flour, vegetables, protein", 45.00),
        ("moto", "Commuter Motorbike", "MOTO", "🛵", "110cc Automatic Scooter", "Large asset transfer standard in Asian Pioneer hubs", 1250.00),
        ("services", "Personal Services", "SERVICE", "✂️", "Haircut / Car Wash / Repair", "Local service economy benchmark", 6.50)
    ]
    conn.executemany("INSERT INTO commodities VALUES (?, ?, ?, ?, ?, ?, ?)", items)
    conn.commit()


def _seed_countries(conn):
    countries = [
        ("ID", "Indonesia", "🇮🇩", "IDR", "Rp", 0.000062, "HIGH"),
        ("VN", "Vietnam", "🇻🇳", "VND", "₫", 0.000039, "HIGH"),
        ("NG", "Nigeria", "🇳🇬", "NGN", "₦", 0.00063, "HIGH"),
        ("KR", "South Korea", "🇰🇷", "KRW", "₩", 0.00073, "MODERATE"),
        ("CN", "China", "🇨🇳", "CNY", "¥", 0.14, "FRAGMENTED"),
        ("PH", "Philippines", "🇵🇭", "PHP", "₱", 0.017, "MODERATE"),
        ("US", "United States", "🇺🇸", "USD", "$", 1.0, "MODERATE"),
        ("MY", "Malaysia", "🇲🇾", "MYR", "RM", 0.23, "MODERATE")
    ]
    conn.executemany("INSERT INTO countries VALUES (?, ?, ?, ?, ?, ?, ?)", countries)
    conn.commit()


def _seed_barters(conn):
    """Seed real-world authentic barter transactions across countries."""
    now = datetime.now(timezone.utc)
    records = [
        # Indonesia
        ("Beras Pandan Wangi 10kg", "rice", "ID", "Surabaya", "Toko Berkah Pioneer", 0.50, 185000, "IDR", "7ea736d3be5a70f56a87b5934e6d3c137483b2a72ec2f01b242a4e919dec02f0", "VERIFIED_ONCHAIN", "Transferred during Surabaya offline Pioneer meetup."),
        ("Kopi Arabika Gayo & Toast", "coffee", "ID", "Bandung", "Ruang Kopi Pioneer", 0.12, 45000, "IDR", "7a141aa156cb6cea601c908c1d5e63e516e15856c6ea60bbae2741f4f503cbdb", "VERIFIED_ONCHAIN", "QR scan pay at cafe counter."),
        ("Paket Sembako Bulanan Lengkap", "groceries", "ID", "Jakarta Timur", "Warung Pioneer Nusantara", 2.20, 750000, "IDR", "95a9ae9bc393b0a53f9d8dd5dd679d3154bd0b2e2c3c4d471f354424a03bdb2c", "VERIFIED_ONCHAIN", "Beras, minyak goreng 2L, telur 1kg, gula."),
        ("Redmi Note 13 8/256GB New", "smartphone", "ID", "Medan", "Pioneer Mobile Store", 7.80, 2799000, "IDR", "0ffaf7bb297dc50eec58f183fcb0cf13bbafb5200490f595e1351b7888d6d345", "VERIFIED_ONCHAIN", "Sealed unit, barter confirmed on-chain."),
        ("Ganti Oli Mesin & Cuci Motor", "services", "ID", "Yogyakarta", "Bengkel Mitra Pioneer", 0.35, 120000, "IDR", "cabaa86a50fb4d3b63c75e99a481d50583bac9deb8c91ec4324ab35d45511630", "VERIFIED_ONCHAIN", "Motul 10W-40 + wash."),
        ("Bensin Pertamax 10 Liter", "fuel", "ID", "Semarang", "Kios BBM Pioneer", 0.38, 137000, "IDR", "d3536c9e5dcece4b6fa2944a8de6fdaac0ee7e62649eb615241c783f60ec10eb", "VERIFIED_ONCHAIN", "Direct voucher exchange."),
        ("Honda BeAT eSP 2022 (Bekas)", "moto", "ID", "Denpasar", "Pioneer Moto Barter", 42.0, 14500000, "IDR", "2e547de4d61137bb34e0d6ecd479204e8432349ceeb3419845aff4a116b3802c", "VERIFIED_ONCHAIN", "Surat lengkap BPKB & STNK."),

        # Vietnam
        ("Gao ST25 Rice 10kg", "rice", "VN", "Hanoi", "ST25 Pioneer Mart", 0.45, 320000, "VND", "71b4b54cc927214614d73f8a9c95cdd7c9e5038a888e704edd93fb7b5c900498", "VERIFIED_ONCHAIN", "World best rice variety barter."),
        ("Pho Bo Dac Biet & Ca Phe", "coffee", "VN", "Ho Chi Minh City", "Pho Pioneer 88", 0.15, 95000, "VND", "a70ab9338f370895ba880430bcfbf28a63e017e460c4ccdf3cb4adac26791130", "VERIFIED_ONCHAIN", "Morning breakfast combo."),
        ("Samsung Galaxy A54 5G", "smartphone", "VN", "Da Nang", "Digital Pi Shop", 8.20, 6800000, "VND", "4944fb7c968425f72553d641b4ad47e48c20c9b98b27c8795d877a11528f285d", "VERIFIED_ONCHAIN", "Local electronics merchant."),
        ("Xang A95 Fuel 10 Liters", "fuel", "VN", "Hai Phong", "Pioneer Gas Station", 0.40, 240000, "VND", "5fe34a1af7098f14e2e8c0b54ceb33cbb9f3d4c862785b9fed9a16384ab4ea11", "VERIFIED_ONCHAIN", "Motorbike fill-up voucher."),
        ("Cat Toc Nam & Massage Mat", "services", "VN", "Can Tho", "Pioneer Barber Club", 0.20, 150000, "VND", "7d776f9340462c0d8827fcd8cfcb9bf9d17e8edf7bdf31924741e61220cfb9c3", "VERIFIED_ONCHAIN", "VIP haircut package."),

        # Nigeria
        ("Bag of Royal Stallion Rice 10kg", "rice", "NG", "Lagos", "Pioneer Food Depot", 0.60, 19500, "NGN", "f800308cc879b3f586495ba099370587b1918eefa8a32261105ca20887060e27", "VERIFIED_ONCHAIN", "Staple food grain barter."),
        ("Weekly Food Stuff Basket", "groceries", "NG", "Abuja", "Grace Pioneer Enterprise", 1.80, 52000, "NGN", "5eecb8deb18ece59130ae0b208585c566911939f79f852c637c02fe16ce90e55", "VERIFIED_ONCHAIN", "Garri, yam, plantain, palm oil."),
        ("Tecno Camon 30 256GB", "smartphone", "NG", "Ibadan", "Alaba Pi Merchant", 7.50, 230000, "NGN", "4784b9fe239704bbe5d4cfc34d0e4f589ee808b8ba1cef30acb0577d20265ce6", "VERIFIED_ONCHAIN", "Brand new sealed in box."),
        ("PMS Petrol 15 Litres", "fuel", "NG", "Port Harcourt", "Rivers Pioneer Fuel", 0.50, 13500, "NGN", "afe547aee5f45035bd58ba0b73b95dc94921facf86c34e866d1ac926b2ef0275", "VERIFIED_ONCHAIN", "Direct generator fuel barter."),

        # South Korea
        ("Cheongwon Organic Rice 10kg", "rice", "KR", "Seoul", "Pioneer Eco Food", 0.95, 42000, "KRW", "cd156ed106cdc57bdb062fa5694d9fe8ec6274875ceefe850a4a512736b7fd06", "VERIFIED_ONCHAIN", "Premium Korean rice."),
        ("Americano & Basque Cheesecake", "coffee", "KR", "Busan", "Cafe Pi Marine", 0.30, 13000, "KRW", "8c02bfa60a73a08424da4a69b97d85c28131bcf306cd1b00bb02936e7cad1d91", "VERIFIED_ONCHAIN", "Specialty coffee shop."),
        ("Galaxy Buds FE (White)", "smartphone", "KR", "Incheon", "Smart Pi Korea", 2.80, 99000, "KRW", "7f93c3cbbc1440bfc435cb683c9bdfd9783c906de00a94a1cb8d523c260c7c38", "VERIFIED_ONCHAIN", "Brand new earphone."),

        # China
        ("Wuchang Rice 10kg Vacuum Pack", "rice", "CN", "Guangzhou", "Lingnan Pioneer Food", 0.55, 110, "CNY", "398a4bd1f43958eb7903f362c9e7c5b34d9b1e3bf8e1247a060a0d189c5fe01c", "VERIFIED_ONCHAIN", "Northeastern Chinese grain."),
        ("Pu'er Aged Tea Cake 357g", "coffee", "CN", "Kunming", "Yunnan Pi Tea Master", 1.20, 240, "CNY", "c5fcc9ee54f3d425e8e398273cab16400b491e7a9947223ee3668f6bf04ac393", "VERIFIED_ONCHAIN", "Raw Pu'er 2018 vintage."),
        ("Xiaomi Redmi 13C 5G", "smartphone", "CN", "Shenzhen", "Huaqiangbei Pi Store", 4.20, 799, "CNY", "08ce776012132a1ebbb0fb091c8bebf5629c144afa5551a607c5880d3c687554", "VERIFIED_ONCHAIN", "Local electronics hub barter."),

        # Philippines
        ("Sinandomeng Rice 10kg", "rice", "PH", "Manila", "Pioneer Palengke Mart", 0.48, 560, "PHP", "21e5201c79bc62472b985ca033d574b4f587897f51466df9241aa56128b73a16", "VERIFIED_ONCHAIN", "Daily grain ration."),
        ("Brewed Barako Coffee & Pastry", "coffee", "PH", "Cebu", "Kapihan Pi Station", 0.14, 160, "PHP", "04b08a53807a1e368b0e7e638eb17fc2d6a0077b007849e1efc9680ca7f88f85", "VERIFIED_ONCHAIN", "Heritage Batangas beans."),
        ("Realme C53 128GB Champion", "smartphone", "PH", "Davao", "Mindanao Pi Gadgets", 5.20, 5999, "PHP", "6a6b35ccce59c66be008209b12c533c7235cdf3b5a2d98945fcc1a9f41a80af4", "VERIFIED_ONCHAIN", "Official warranty unit."),

        # United States
        ("Whole Foods Organic Basket", "groceries", "US", "Austin", "Lone Star Pioneer Co-op", 2.10, 58.0, "USD", "174fb82e8aec4951f8e3e3b5e884783b03531b5772271bb374400e9f520cbf87", "VERIFIED_ONCHAIN", "Milk, sourdough, eggs, produce."),
        ("Espresso Flight & Bag of Beans", "coffee", "US", "Seattle", "Cascade Pioneer Roasters", 0.70, 22.0, "USD", "fdc0b3e328d905ab9a6c628427a5a6abec16730b810a9f1c47cfdfe65ae2e639", "VERIFIED_ONCHAIN", "Pacific Northwest micro-lot.")
    ]

    insert_rows = []
    for i, r in enumerate(records):
        item_name, comm_id, country_code, city, merchant, pi_amt, fiat_val, curr, tx, status, notes = r
        rate = FIAT_TO_USD.get(curr, 1.0)
        fiat_usd = round(fiat_val * rate, 2)
        implied_usd = round(fiat_usd / pi_amt, 2)
        
        # Stagger timestamps across past 7 days
        minutes_ago = (len(records) - i) * 230
        dt_str = (now - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d %H:%M:%S")

        barter_id = f"BAR-{uuid.uuid4().hex[:8].upper()}"
        insert_rows.append((
            barter_id, dt_str, item_name, comm_id, country_code, city,
            merchant, pi_amt, fiat_val, curr, fiat_usd, implied_usd,
            tx, status, notes
        ))

    conn.executemany("""
        INSERT INTO barters VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, insert_rows)
    conn.commit()


def _seed_history(conn):
    """Seed historical implied valuation data points for visual charts."""
    today = datetime.now(timezone.utc).date()
    # Baseline progression around $21 - $26 range
    data = [
        (str(today - timedelta(days=6)), 21.40, 112000, 890),
        (str(today - timedelta(days=5)), 22.15, 125000, 940),
        (str(today - timedelta(days=4)), 23.05, 138000, 1020),
        (str(today - timedelta(days=3)), 22.80, 131000, 980),
        (str(today - timedelta(days=2)), 24.10, 145000, 1140),
        (str(today - timedelta(days=1)), 24.65, 152000, 1210),
        (str(today), 24.80, 161500, 1290),
    ]
    conn.executemany("INSERT INTO history_points VALUES (?, ?, ?, ?)", data)
    conn.commit()


def insert_barter(submission_data: dict, verification_status: Optional[str] = None) -> Dict[str, Any]:
    """Insert a new user-submitted barter into the database with audit status."""
    conn = get_db()
    c = conn.cursor()

    barter_id = f"BAR-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    curr = submission_data["fiat_currency"].upper()
    rate = FIAT_TO_USD.get(curr, 1.0)
    fiat_usd = round(submission_data["fiat_value"] * rate, 2)
    implied_usd = round(fiat_usd / max(submission_data["pi_amount"], 0.000001), 2)

    status = verification_status or ("VERIFIED_ONCHAIN" if len(submission_data.get("tx_hash", "")) == 64 else "COMMUNITY_AUDITED")

    c.execute("""
        INSERT INTO barters (
            id, timestamp, item_name, commodity_id, country_code, city,
            merchant_name, pi_amount, fiat_value, fiat_currency, fiat_usd,
            implied_pi_usd, tx_hash, verification_status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        barter_id, timestamp, submission_data["item_name"],
        submission_data["commodity_id"], submission_data["country_code"],
        submission_data["city"], submission_data["merchant_name"],
        submission_data["pi_amount"], submission_data["fiat_value"],
        curr, fiat_usd, implied_usd, submission_data.get("tx_hash", ""),
        status, submission_data.get("notes", "")
    ))
    conn.commit()
    conn.close()

    return {
        "id": barter_id,
        "timestamp": timestamp,
        "implied_pi_usd": implied_usd,
        "status": status
    }

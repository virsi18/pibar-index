"""
PiBarX - Global Pi Barter Real-Price Index
Data Models & Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CommodityBasket(BaseModel):
    id: str
    name: str
    symbol: str
    icon: str
    unit: str
    description: str
    benchmark_usd: float
    median_pi_price: float
    implied_pi_usd: float
    change_24h_pct: float
    volume_24h_pi: float
    sample_trades_count: int


class CountryParity(BaseModel):
    country_code: str
    country_name: str
    flag: str
    currency_code: str
    currency_symbol: str
    exchange_rate_usd: float
    median_barter_pi_usd: float
    purchasing_power_ratio: float  # PPP multiplier vs global median
    total_barters: int
    most_popular_commodity: str
    consensus_level: str  # HIGH, MODERATE, FRAGMENTED


class BarterRecord(BaseModel):
    id: str
    timestamp: str
    item_name: str
    commodity_id: str
    country_code: str
    city: str
    merchant_name: str
    pi_amount: float
    fiat_value: float
    fiat_currency: str
    fiat_usd: float
    implied_pi_usd: float
    tx_hash: str
    verification_status: str  # VERIFIED_ONCHAIN, COMMUNITY_AUDITED, PENDING
    notes: Optional[str] = ""


class BarterSubmission(BaseModel):
    item_name: str = Field(..., min_length=2, max_length=120)
    commodity_id: str
    country_code: str = Field(..., min_length=2, max_length=3)
    city: str = Field(..., min_length=2, max_length=80)
    merchant_name: str = Field(..., min_length=2, max_length=80)
    pi_amount: float = Field(..., gt=0)
    fiat_value: float = Field(..., gt=0)
    fiat_currency: str = Field(..., min_length=3, max_length=4)
    tx_hash: Optional[str] = Field("", max_length=64)
    notes: Optional[str] = Field("", max_length=300)


class IndexSummary(BaseModel):
    global_median_pi_usd: float
    change_24h_pct: float
    total_barters_count: int
    total_volume_24h_pi: float
    total_volume_24h_usd: float
    active_countries_count: int
    confidence_score: float  # e.g. 98.4%
    last_block_sync: str
    gcv_divergence_pct: float  # reality vs 314,159 GCV
    top_barter_hubs: List[str]


class ConvertRequest(BaseModel):
    fiat_amount: Optional[float] = None
    fiat_currency: Optional[str] = "USD"
    pi_amount: Optional[float] = None
    commodity_id: Optional[str] = None
    target_country: Optional[str] = "GLOBAL"


class ConvertResponse(BaseModel):
    input_value: float
    input_unit: str
    implied_rate_usd: float
    recommended_pi_range: dict
    purchasing_power_equivalent: dict
    gcv_comparison: dict

"""Validated request and response models."""
import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class BarterSubmission(BaseModel):
    item_name: str = Field(..., min_length=2, max_length=120)
    commodity_id: str = Field(..., min_length=1, max_length=40)
    country_code: str = Field(..., min_length=2, max_length=3)
    city: str = Field(..., min_length=2, max_length=80)
    merchant_name: str = Field(..., min_length=2, max_length=80)
    pi_amount: float = Field(..., gt=0, le=100000000)
    fiat_value: float = Field(..., gt=0, le=1000000000000)
    fiat_currency: str = Field(..., min_length=3, max_length=4)
    tx_hash: str = Field(..., min_length=64, max_length=64)
    recipient_address: str = Field(..., min_length=56, max_length=56)
    notes: Optional[str] = Field("", max_length=300)

    @field_validator("tx_hash")
    @classmethod
    def validate_hash(cls, value):
        if not re.fullmatch(r"[a-fA-F0-9]{64}", value.strip()):
            raise ValueError("TxID must be exactly 64 hexadecimal characters")
        return value.strip().lower()

    @field_validator("recipient_address")
    @classmethod
    def validate_recipient_address(cls, value):
        value = value.strip().upper()
        if not re.fullmatch(r"G[A-Z2-7]{55}", value):
            raise ValueError("Recipient must be a 56-character Pi/Stellar public address beginning with G")
        return value

    @field_validator("fiat_currency")
    @classmethod
    def normalize_currency(cls, value): return value.strip().upper()

    @field_validator("country_code")
    @classmethod
    def normalize_country(cls, value): return value.strip().upper()

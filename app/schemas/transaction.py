from datetime import datetime
from pydantic import BaseModel, field_validator
from pydantic.types import UUID
import uuid


# Input Schema (API -> System)
class TransactionCreate(BaseModel):
    transaction_id: str
    timestamp: datetime
    amount: float
    currency: str
    customer_id: str
    product_id: str
    quantity: int

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if len(v) != 3 or not v.isalpha():
            raise ValueError("Currency must be a 3-letter code (e.g., USD).")
        return v.upper()

    @field_validator("transaction_id", "customer_id", "product_id")
    @classmethod
    def validate_uuids(cls, v: str) -> UUID:
        try:
            return uuid.UUID(v)
        except ValueError:
            raise ValueError(f"Invalid UUID format: {v}")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        return round(v, 2)


# Output Schema (System -> API)
class Transaction(BaseModel):
    transaction_id: UUID
    timestamp: datetime
    amount: float
    currency: str
    customer_id: UUID
    product_id: UUID
    quantity: int
    created_at: datetime

    class Config:
        from_attributes = True  # For ORM compatibility

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, field_validator
from pydantic.types import UUID


# Input Schema (API -> System)
class TransactionCreate(BaseModel):
    transaction_id: UUID
    timestamp: datetime
    amount: float
    currency: str
    customer_id: UUID
    product_id: UUID
    quantity: int

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

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
            if not isinstance(v, UUID):
                return uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid UUID format: {v}")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if not isinstance(v, float):
            raise ValueError("Amount must be a valid number.")
        if v <= 0:
            raise ValueError("Amount must be a positive number.")
        return round(v, 2)

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if not isinstance(v, int):
            raise ValueError("Quantity must be an integer.")
        if v <= 0:
            raise ValueError("Quantity must be a positive number.")
        return v


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

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Transaction
from app.db.session import get_db
from app.services.reports import get_customer_summary, get_product_summary

router = APIRouter()

# Exchange rates (simplified for this example)
EXCHANGE_RATES = {"PLN": 1.0, "EUR": 4.3, "USD": 4.0}


@router.get("/customer-summary/{customer_id}")
async def customer_summary(
    customer_id: UUID,
    start_date: datetime = None,
    end_date: datetime = None,
    db: Session = Depends(get_db),
):
    summary = await get_customer_summary(db, customer_id, start_date, end_date)
    if not summary:
        raise HTTPException(
            status_code=404, detail="No transactions found for this customer"
        )
    return summary


@router.get("/product-summary/{product_id}")
async def product_summary(
    product_id: UUID,
    start_date: datetime = None,
    end_date: datetime = None,
    db: Session = Depends(get_db),
):
    summary = await get_product_summary(db, product_id, start_date, end_date)
    if not summary:
        raise HTTPException(
            status_code=404, detail="No transactions found for this product"
        )
    return summary

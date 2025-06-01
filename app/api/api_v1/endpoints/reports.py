from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.exceptions import AppException
from app.logging_config import logger
from app.services.reports import (
    get_customer_summary,
    get_product_summary,
    get_relevant_transactions,
)

router = APIRouter()


@router.get("/customer-summary/{customer_id}")
async def customer_summary(
    customer_id: UUID,
    start_date: datetime = None,
    end_date: datetime = None,
    db: Session = Depends(get_db),
):
    try:
        transactions = await get_relevant_transactions(
            db=db, customer_id=customer_id, start_date=start_date, end_date=end_date
        )
        summary = get_customer_summary(customer_id, transactions)
        return summary
    except AppException:
        raise
    except Exception as e:
        logger.exception(
            f"Unexpected error generating summary for customer: {customer_id}. Error: {e}"
        )
        raise AppException(
            f"Unexpected error generating summary for customer: {customer_id}.",
            code="GET_CUSTOMER_SUMMARY_FAIL",
            status_code=500,
        )


@router.get("/product-summary/{product_id}")
async def product_summary(
    product_id: UUID,
    start_date: datetime = None,
    end_date: datetime = None,
    db: Session = Depends(get_db),
):
    try:
        transactions = await get_relevant_transactions(
            db=db, product_id=product_id, start_date=start_date, end_date=end_date
        )
        summary = get_product_summary(product_id, transactions)
        return summary
    except AppException:
        raise
    except Exception as e:
        logger.exception(
            f"Unexpected error generating summary for product: {product_id}. Error: {e}"
        )
        raise AppException(
            f"Unexpected error generating summary for product: {product_id}.",
            code="GET_PRODUCT_SUMMARY_FAIL",
            status_code=500,
        )

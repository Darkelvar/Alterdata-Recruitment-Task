from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Transaction
from app.exceptions import AppException
from app.logging_config import logger

EXCHANGE_RATES = {"PLN": 1.0, "EUR": 4.3, "USD": 4.0}


def convert_to_pln(amount: float, currency: str) -> float:
    # For any non-specified currency the exchange rate is 1 X = 4.20 PLN
    return amount * EXCHANGE_RATES.get(currency, 4.2)


async def get_relevant_transactions(
    db: AsyncSession,
    customer_id: UUID | None = None,
    product_id: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> List[Transaction]:
    try:
        context = (
            f"customer: {customer_id}" if customer_id else f"product: {product_id}"
        )
        if customer_id:
            filters = [Transaction.customer_id == customer_id]
        elif product_id:
            filters = [Transaction.product_id == product_id]
        if start_date:
            filters.append(Transaction.timestamp >= start_date)
        if end_date:
            filters.append(Transaction.timestamp <= end_date)

        result = await db.execute(select(Transaction).where(and_(*filters)))
        transactions = result.scalars().all()

        if not transactions:
            logger.exception(f"No transactions found for {context}.")
            raise AppException(
                f"No transactions found for {context}.",
                code="GET_REL_TRANSACTIONS_NOT_FOUND_FAIL",
                status_code=404,
            )
        return transactions
    except AppException:
        raise
    except SQLAlchemyError as e:
        logger.exception(f"DB error retrieving transactions for {context}. Error: {e}")
        raise AppException(
            f"DB error retrieving transactions for {context}.",
            code="GET_REL_TRANSACTIONS_DB_FAIL",
            status_code=500,
        )
    except Exception as e:
        logger.exception(
            f"Unexpected error retrieving transactions for {context}. Error: {e}"
        )
        raise AppException(
            f"Unexpected error retrieving transactions for {context}.",
            code="GET_REL_TRANSACTIONS_FAIL",
            status_code=500,
        )


def get_customer_summary(
    customer_id: UUID,
    transactions: List[Transaction],
) -> Dict[str, Any]:
    try:
        total_amount_pln = sum(
            convert_to_pln(t.amount, t.currency) for t in transactions
        )
        product_ids = {t.product_id for t in transactions}
        last_transaction = max(t.timestamp for t in transactions)

        return {
            "customer_id": customer_id,
            "total_amount_pln": round(total_amount_pln, 2),
            "unique_products_count": len(product_ids),
            "last_transaction_date": last_transaction,
            "transaction_count": len(transactions),
        }
    except Exception as e:
        logger.exception(
            f"Unexpected error generating customer summary for {customer_id}. Error: {e}"
        )
        raise AppException(
            f"Unexpected error generating customer summary for {customer_id}.",
            code="GENERATE_CUSTOMER_SUMMARY_FAIL",
            status_code=500,
        )


def get_product_summary(
    product_id: UUID,
    transactions: List[Transaction],
) -> Dict[str, Any]:
    try:
        total_amount_pln = sum(
            convert_to_pln(t.amount, t.currency) for t in transactions
        )
        total_quantity = sum(t.quantity for t in transactions)
        customer_ids = {t.customer_id for t in transactions}

        return {
            "product_id": product_id,
            "total_amount_pln": round(total_amount_pln, 2),
            "total_quantity": total_quantity,
            "unique_customers_count": len(customer_ids),
            "transaction_count": len(transactions),
        }
    except Exception as e:
        logger.exception(
            f"Unexpected error generating product summary for {product_id}. Error: {e}"
        )
        raise AppException(
            f"Unexpected error generating product summary for {product_id}.",
            code="GENERATE_PRODUCT_SUMMARY_FAIL",
            status_code=500,
        )

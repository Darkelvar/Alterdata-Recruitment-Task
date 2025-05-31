from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Transaction
from app.logging_config import logger

EXCHANGE_RATES = {"PLN": 1.0, "EUR": 4.3, "USD": 4.0}


async def get_customer_summary(
    db: AsyncSession,
    customer_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    try:
        filters = [Transaction.customer_id == customer_id]
        if start_date:
            filters.append(Transaction.timestamp >= start_date)
        if end_date:
            filters.append(Transaction.timestamp <= end_date)

        result = await db.execute(select(Transaction).where(and_(*filters)))
        transactions = result.scalars().all()

        if not transactions:
            return None

        # For any non-specified currency the exchange rate is 1 X = 4.20 PLN
        total_amount_pln = sum(
            t.amount * EXCHANGE_RATES.get(t.currency, 4.2) for t in transactions
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
        logger.error(f"Error generating customer summary: {e}")
        raise


async def get_product_summary(
    db: AsyncSession,
    product_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    try:
        filters = [Transaction.product_id == product_id]
        if start_date:
            filters.append(Transaction.timestamp >= start_date)
        if end_date:
            filters.append(Transaction.timestamp <= end_date)

        result = await db.execute(select(Transaction).where(and_(*filters)))
        transactions = result.scalars().all()

        if not transactions:
            return None

        total_amount_pln = sum(
            t.amount * EXCHANGE_RATES.get(t.currency, 4.2) for t in transactions
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
        logger.error(f"Error generating product summary: {e}")
        raise

from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.models import Transaction
from app.logging_config import logger
from app.schemas.transaction import TransactionCreate


def create_transaction(db: Session, transaction: TransactionCreate):
    try:
        db_transaction = Transaction(**transaction.model_dump())
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        return db_transaction
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB error: {str(e)}")
        raise


async def get_transaction(db: AsyncSession, transaction_id: UUID) -> Transaction | None:
    try:
        result = await db.execute(
            select(Transaction).where(Transaction.transaction_id == transaction_id)
        )
        return result.scalars().first()
    except SQLAlchemyError as e:
        logger.error(f"DB error fetching transaction {transaction_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_transactions(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    customer_id: Optional[UUID] = None,
    product_id: Optional[UUID] = None,
) -> tuple[int, List[Transaction]]:
    try:
        base_query = select(Transaction)
        count_query = select(func.count()).select_from(Transaction)

        if customer_id:
            base_query = base_query.where(Transaction.customer_id == customer_id)
            count_query = count_query.where(Transaction.customer_id == customer_id)
        if product_id:
            base_query = base_query.where(Transaction.product_id == product_id)
            count_query = count_query.where(Transaction.product_id == product_id)

        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        result = await db.execute(base_query.offset(skip).limit(limit))
        transactions = result.scalars().all()

        return total, transactions
    except SQLAlchemyError as e:
        logger.error(f"DB error fetching transactions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

from typing import List
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.models import Transaction
from app.exceptions import AppException
from app.logging_config import logger
from app.schemas.transaction import TransactionCreate


def create_transaction(db: Session, transaction: TransactionCreate):
    try:
        db_transaction = Transaction(**transaction.model_dump())
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        return db_transaction
    except IntegrityError as e:
        db.rollback()
        logger.exception(
            f"Duplicate transaction detected: {transaction.transaction_id}. Error: {e}"
        )
        raise AppException(
            f"Transaction with ID: {transaction.transaction_id} already exists.",
            code="CREATE_TRANSACTION_DUPLICATE_FAIL",
            status_code=500,
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(
            f"DB error inserting transaction {transaction.transaction_id}. Error: {e}"
        )
        raise AppException(
            f"Database error while saving transaction: {transaction.transaction_id}.",
            code="CREATE_TRANSACTION_DB_FAIL",
            status_code=500,
        )


async def get_transaction(db: AsyncSession, transaction_id: UUID) -> Transaction | None:
    try:
        result = await db.execute(
            select(Transaction).where(Transaction.transaction_id == transaction_id)
        )
        return result.scalars().first()
    except SQLAlchemyError as e:
        logger.exception(f"DB error fetching transaction {transaction_id}. Error: {e}")
        raise AppException(
            f"DB error fetching transaction {transaction_id}.",
            code="GET_TRANSACTION_DB_FAIL",
            status_code=500,
        )
    except Exception as e:
        logger.exception(
            f"Unexpected error fetching transaction {transaction_id}. Error: {e}"
        )
        raise AppException(
            f"Unexpected error fetching transaction {transaction_id}.",
            CODE="GET_TRANSACTION_SCALAR_FAIL",
            status_code=500,
        )


async def get_transactions(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    customer_id: UUID | None = None,
    product_id: UUID | None = None,
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
        logger.exception(f"DB error fetching transactions. Error: {e}")
        raise AppException(
            "Database error while fetching transactions.",
            code="GET_TRANSACTIONS_DB_FAIL",
            status_code=500,
        )
    except Exception as e:
        logger.exception(f"Unexpected error fetching transactions. Error: {e}")
        raise AppException(
            "Unexpected error while fetching transactions.",
            code="GET_TRANSACTIONS_SCALAR_FAIL",
            status_code=500,
        )

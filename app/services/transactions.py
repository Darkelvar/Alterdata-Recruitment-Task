from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.db.models import Transaction
from app.schemas.transaction import TransactionCreate
from app.logging_config import logger


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

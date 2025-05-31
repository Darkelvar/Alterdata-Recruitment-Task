from app.workers.celery_worker import celery_app
from app.services.transactions import create_transaction
from app.schemas.transaction import TransactionCreate
from app.db.session_sync import SessionLocal
import csv
import io
import logging

logger = logging.getLogger(__name__)


@celery_app.task
def process_csv_contents(contents: str):
    csv_reader = csv.DictReader(io.StringIO(contents))
    with SessionLocal() as db:
        for row_num, row in enumerate(csv_reader, 1):
            try:
                transaction_data = {
                    "transaction_id": row["transaction_id"],
                    "timestamp": row["timestamp"],
                    "amount": float(row["amount"]),
                    "currency": row["currency"],
                    "customer_id": row["customer_id"],
                    "product_id": row["product_id"],
                    "quantity": int(row["quantity"]),
                }
                validated = TransactionCreate(**transaction_data)
                create_transaction(db, validated)
            except Exception as e:
                logger.error(f"Row {row_num} failed: {e}")

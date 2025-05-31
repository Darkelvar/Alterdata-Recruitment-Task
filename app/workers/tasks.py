import csv
import io

from app.db.session_sync import SessionLocal
from app.logging_config import logger
from app.schemas.transaction import TransactionCreate
from app.services.transactions import create_transaction
from app.workers.celery_worker import celery_app


@celery_app.task
def process_csv_contents(contents: str):
    csv_reader = csv.DictReader(io.StringIO(contents))
    processed_rows = 0
    failed_rows = set()
    errors = []
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
                processed_rows += 1
            except Exception as e:
                failed_rows.add(row_num)
                error_msg = f"Row {row_num} failed: {e}"
                errors.append(error_msg)
                logger.exception(error_msg)

    summary = {
        "successfully_imported_rows": processed_rows,
        "failed_rows": list(failed_rows),
        "encountered_errors": errors,
    }
    logger.info("CSV processing complete: %s", summary)
    return summary

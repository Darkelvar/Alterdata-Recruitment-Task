import csv
import io

from pydantic import ValidationError

from app.core.exceptions import AppException
from app.core.logging_config import logger
from app.db.session_sync import SessionLocal
from app.schemas.transaction import TransactionCreate
from app.services.transactions import create_transaction
from app.workers.celery_worker import celery_app


@celery_app.task
def process_csv_contents(contents: str):
    csv_reader = csv.DictReader(io.StringIO(contents))

    required_fields = {
        "transaction_id",
        "timestamp",
        "amount",
        "currency",
        "customer_id",
        "product_id",
        "quantity",
    }
    header_fields = set(csv_reader.fieldnames or [])
    missing = required_fields - header_fields
    if missing:
        logger.exception(f"Missing required columns in CSV header: {missing}")
        raise AppException(
            f"Missing required columns in CSV header: {missing}",
            code="UPLOAD_FILE_MISSING_COLUMNS_FAIL",
            status_code=400,
        )

    errors = []
    all_rows = 0
    processed_rows = 0
    failed_rows = set()

    with SessionLocal() as db:
        for row_num, row in enumerate(csv_reader, 1):
            all_rows += 1
            try:
                transaction_data = {
                    "transaction_id": row["transaction_id"],
                    "timestamp": row["timestamp"],
                    "amount": row["amount"],
                    "currency": row["currency"],
                    "customer_id": row["customer_id"],
                    "product_id": row["product_id"],
                    "quantity": row["quantity"],
                }
                validated = TransactionCreate(**transaction_data)
                create_transaction(db, validated)
                processed_rows += 1
            except AppException as e:
                failed_rows.add(row_num)
                error_msg = f"Error with row {row_num}: {e.message}"
                logger.exception(error_msg)
                errors.append(error_msg)
            except ValidationError as e:
                failed_rows.add(row_num)
                validation_errors = ""
                for err in e.errors():
                    validation_errors += (
                        f"Error in {err.get("loc")}: {err.get("msg")}. "
                    )
                error_msg = f"Issues found in row {row_num}: " + validation_errors
                logger.exception(error_msg)
                errors.append(error_msg)
            except Exception as e:
                failed_rows.add(row_num)
                error_msg = f"Unexpected Error with row {row_num}: {e}"
                logger.exception(error_msg)
                errors.append(error_msg)

    summary = {
        "all_rows": all_rows,
        "successfully_imported_rows": processed_rows,
        "failed_rows": list(failed_rows),
        "encountered_errors": errors[:5],
    }
    logger.info("CSV processing complete: %s", summary)
    return summary

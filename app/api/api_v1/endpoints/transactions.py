from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.exceptions import AppException
from app.core.logging_config import logger
from app.db.session import get_db
from app.schemas.pagination import PaginatedResponse
from app.schemas.transaction import Transaction
from app.services.transactions import get_transaction, get_transactions
from app.workers.tasks import process_csv_contents

router = APIRouter()


@router.post("/upload", response_class=JSONResponse)
def upload_transactions(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
):
    try:
        contents = file.file.read()
        if not contents:
            logger.exception(f"Received empty file: {file.filename}.")
            raise AppException(
                "Uploaded file is empty.",
                code="UPLOAD_FILE_EMPTY_FAIL",
                status_code=400,
            )
        try:
            contents = contents.decode("utf-8")
        except UnicodeDecodeError as e:
            logger.exception(
                f"Failed to decode uploaded file: {file.filename}. Error: {e}"
            )
            raise AppException(
                "Failed to decode file. Check if it's properly encoded as UTF-8.",
                code="UPLOAD_FILE_DECODE_FAIL",
                status_code=400,
            )
        logger.info(f"Received file: {file.filename} for processing.")
        task = process_csv_contents.delay(contents)
        return {
            "message": f"{file.filename} is queued for processing.",
            "task_id": task.id,
            "status_check": f"/api/v1/tasks/{task.id}",
        }
    except AppException:
        raise
    except Exception as e:
        logger.exception(
            f"Unexpected error during file processing: {file.filename}. Error: {e}"
        )
        raise AppException(
            "Unexpected error while processing file.",
            code="UPLOAD_FILE_FAIL",
            status_code=500,
        )


@router.get("/", response_model=PaginatedResponse[Transaction])
async def read_transactions(
    skip: int = 0,
    limit: int = 100,
    customer_id: UUID = None,
    product_id: UUID = None,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    if skip < 0 or limit < 0:
        raise AppException(
            "Values for skip and limit must not be negative.",
            code="GET_TRANSACTIONS_NEGATIVE_FAIL",
            status_code=400,
        )
    try:
        total, transactions = await get_transactions(
            db, skip=skip, limit=limit, customer_id=customer_id, product_id=product_id
        )
        return PaginatedResponse(total=total, skip=skip, limit=limit, data=transactions)
    except AppException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error reading transactions. Error: {e}")
        raise AppException(
            "Unexpected error while fetching transactions.",
            code="GET_TRANSACTIONS_FAIL",
            status_code=500,
        )


@router.get("/{transaction_id}", response_model=Transaction)
async def read_transaction(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        transaction = await get_transaction(db, transaction_id=transaction_id)
        if not transaction:
            logger.exception(f"Transaction {transaction_id} not found.")
            raise AppException(
                f"Transaction {transaction_id} not found.",
                code="GET_TRANSACTION_NOT_FOUND_FAIL",
                status_code=404,
            )
        return transaction
    except AppException:
        raise
    except Exception as e:
        logger.exception(
            f"Unexpected error fetching transaction {transaction_id}. Error: {e}"
        )
        raise AppException(
            f"Unexpected error fetching transaction {transaction_id}.",
            code="GET_TRANSACTION_FAIL",
            status_code=500,
        )

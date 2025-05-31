from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.logging_config import logger
from app.schemas.pagination import PaginatedResponse
from app.schemas.transaction import Transaction
from app.services.transactions import get_transaction, get_transactions
from app.workers.tasks import process_csv_contents

router = APIRouter()


@router.post("/upload", response_class=JSONResponse)
def upload_transactions(file: UploadFile = File(...)):
    try:
        contents = file.file.read().decode("utf-8")
        task = process_csv_contents.delay(contents)
        return {
            "message": f"{file.filename} is being processed asynchronously.",
            "task_id": task.id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=PaginatedResponse[Transaction])
async def read_transactions(
    skip: int = 0,
    limit: int = 100,
    customer_id: UUID = None,
    product_id: UUID = None,
    db: AsyncSession = Depends(get_db),
):
    total, transactions = await get_transactions(
        db, skip=skip, limit=limit, customer_id=customer_id, product_id=product_id
    )
    return PaginatedResponse(total=total, skip=skip, limit=limit, data=transactions)


@router.get("/{transaction_id}", response_model=Transaction)
async def read_transaction(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    transaction = await get_transaction(db, transaction_id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

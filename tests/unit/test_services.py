from uuid import uuid4

import pytest

from app.core.exceptions import AppException
from app.db.models import Transaction
from app.schemas.transaction import TransactionCreate
from app.services.transactions import create_transaction


@pytest.mark.anyio
def test_create_transaction_success(sync_db):
    transaction = TransactionCreate(
        transaction_id=str(uuid4()),
        timestamp="2023-01-01T12:00:00",
        amount=100.0,
        currency="USD",
        customer_id=str(uuid4()),
        product_id=str(uuid4()),
        quantity=2,
    )
    result = create_transaction(sync_db, transaction)
    assert isinstance(result, Transaction)
    assert result.transaction_id == transaction.transaction_id
    count = sync_db.query(Transaction).count()
    assert count == 1


@pytest.mark.anyio
def test_duplicate_transaction_raises_app_exception(sync_db):
    transaction_id = str(uuid4())
    transaction = TransactionCreate(
        transaction_id=transaction_id,
        timestamp="2023-01-01T12:00:00",
        amount=100.0,
        currency="USD",
        customer_id=str(uuid4()),
        product_id=str(uuid4()),
        quantity=2,
    )
    create_transaction(sync_db, transaction)

    with pytest.raises(AppException) as e:
        create_transaction(sync_db, transaction)
    assert e.value.code == "CREATE_TRANSACTION_DUPLICATE_FAIL"

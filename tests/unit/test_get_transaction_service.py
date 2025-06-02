from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.db.models import Transaction
from app.services.transactions import get_transaction


@pytest.mark.anyio
async def test_get_transaction_success(async_db):
    test_tx = Transaction(
        transaction_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        amount=99.99,
        currency="USD",
        customer_id=uuid4(),
        product_id=uuid4(),
        quantity=1,
    )
    async_db.add(test_tx)
    await async_db.commit()

    result = await get_transaction(async_db, test_tx.transaction_id)
    assert result is not None
    assert result.transaction_id == test_tx.transaction_id


@pytest.mark.anyio
async def test_get_transaction_not_found(async_db):
    result = await get_transaction(async_db, uuid4())
    assert result is None

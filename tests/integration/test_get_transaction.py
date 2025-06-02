from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.db.models import Transaction


@pytest.mark.anyio
async def test_read_transaction_success(client, async_db):
    test_tx = Transaction(
        transaction_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        amount=42.0,
        currency="USD",
        customer_id=uuid4(),
        product_id=uuid4(),
        quantity=1,
    )
    async_db.add(test_tx)
    await async_db.commit()

    response = await client.get(f"/api/v1/transactions/{test_tx.transaction_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == str(test_tx.transaction_id)
    assert data["amount"] == 42.0


@pytest.mark.anyio
async def test_read_transaction_not_found(client):
    non_existent_id = uuid4()

    response = await client.get(f"/api/v1/transactions/{non_existent_id}")

    assert response.status_code == 404
    assert "not found" in response.text.lower()

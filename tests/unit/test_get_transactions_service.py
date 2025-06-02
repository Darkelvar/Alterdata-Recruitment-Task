from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.db.models import Transaction
from app.services.transactions import get_transactions


@pytest.mark.anyio
async def test_get_transactions_no_filters(async_db):
    transaction = Transaction(
        transaction_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="USD",
        customer_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        product_id=UUID("222e4567-e89b-12d3-a456-426614174002"),
        quantity=2,
    )
    transaction_2 = Transaction(
        transaction_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="USD",
        customer_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        product_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        quantity=2,
    )
    async_db.add_all([transaction, transaction_2])
    await async_db.commit()

    total, transactions = await get_transactions(async_db)
    assert total == 2
    assert len(transactions) == 2
    assert transactions[0].transaction_id == UUID(
        "123e4567-e89b-12d3-a456-426614174000"
    )


@pytest.mark.anyio
async def test_get_transactions_with_limit_and_skip(async_db):
    transaction = Transaction(
        transaction_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="USD",
        customer_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        product_id=UUID("222e4567-e89b-12d3-a456-426614174002"),
        quantity=2,
    )
    transaction_2 = Transaction(
        transaction_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="USD",
        customer_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        product_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        quantity=2,
    )
    transaction_3 = Transaction(
        transaction_id=UUID("e298d7fb-7c49-4573-bd84-1cb2be107029"),
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="USD",
        customer_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        product_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        quantity=2,
    )
    async_db.add_all([transaction, transaction_2, transaction_3])
    await async_db.commit()

    total, transactions = await get_transactions(async_db)
    assert total == 3
    assert len(transactions) == 3
    total, transactions = await get_transactions(async_db, limit=2)
    assert total == 3
    assert len(transactions) == 2
    total, transactions = await get_transactions(async_db, limit=1, skip=1)
    assert total == 3
    assert len(transactions) == 1
    assert transactions[0].transaction_id == UUID(
        "111e4567-e89b-12d3-a456-426614174001"
    )


@pytest.mark.anyio
async def test_get_transactions_by_product(async_db):
    transaction = Transaction(
        transaction_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="USD",
        customer_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        product_id=UUID("222e4567-e89b-12d3-a456-426614174002"),
        quantity=2,
    )
    transaction_2 = Transaction(
        transaction_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="USD",
        customer_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        product_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        quantity=2,
    )
    async_db.add_all([transaction, transaction_2])
    await async_db.commit()
    product_id = UUID("222e4567-e89b-12d3-a456-426614174002")
    total, transactions = await get_transactions(async_db, product_id=product_id)
    assert total == 1
    assert len(transactions) == 1
    assert all(t.product_id == product_id for t in transactions)


@pytest.mark.anyio
async def test_get_transactions_by_customer(async_db):
    transaction = Transaction(
        transaction_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="USD",
        customer_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        product_id=UUID("222e4567-e89b-12d3-a456-426614174002"),
        quantity=2,
    )
    transaction_2 = Transaction(
        transaction_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="USD",
        customer_id=UUID("222e4567-e89b-12d3-a456-426614174002"),
        product_id=UUID("222e4567-e89b-12d3-a456-426614174002"),
        quantity=2,
    )
    async_db.add_all([transaction, transaction_2])
    await async_db.commit()
    customer_id = UUID("222e4567-e89b-12d3-a456-426614174002")
    total, transactions = await get_transactions(async_db, customer_id=customer_id)
    assert total == 1
    assert len(transactions) == 1
    assert all(t.customer_id == customer_id for t in transactions)


@pytest.mark.anyio
async def test_get_transactions_no_results(async_db):
    total, transactions = await get_transactions(async_db)
    assert total == 0
    assert transactions == []

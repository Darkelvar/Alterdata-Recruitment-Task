from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.core.exceptions import AppException
from app.db.models import Transaction
from app.services.reports import (
    convert_to_pln,
    get_customer_summary,
    get_product_summary,
    get_relevant_transactions,
)


@pytest.mark.anyio
async def test_get_relevant_transactions_filters(async_db):
    customer_id = uuid4()
    product_id = uuid4()
    now = datetime.now(timezone.utc)

    transaction = Transaction(
        transaction_id=uuid4(),
        timestamp=now - timedelta(days=1),
        amount=123.45,
        currency="USD",
        customer_id=customer_id,
        product_id=product_id,
        quantity=1,
    )
    transaction_2 = Transaction(
        transaction_id=uuid4(),
        timestamp=now - timedelta(days=5),
        amount=123.45,
        currency="USD",
        customer_id=uuid4(),
        product_id=uuid4(),
        quantity=1,
    )
    async_db.add_all([transaction, transaction_2])
    await async_db.commit()

    # By customer_id
    transactions = await get_relevant_transactions(async_db, customer_id=customer_id)
    assert len(transactions) == 1
    assert all(t.customer_id == customer_id for t in transactions)

    # By product_id
    transactions = await get_relevant_transactions(async_db, product_id=product_id)
    assert len(transactions) == 1
    assert all(t.product_id == product_id for t in transactions)

    # By date range
    start_date = now - timedelta(days=2)
    end_date = now
    transactions = await get_relevant_transactions(
        async_db, customer_id=customer_id, start_date=start_date, end_date=end_date
    )
    assert len(transactions) == 1
    assert all(start_date <= t.timestamp <= end_date for t in transactions)


@pytest.mark.anyio
async def test_get_relevant_transactions_not_found(async_db):
    with pytest.raises(AppException) as excinfo:
        await get_relevant_transactions(async_db, customer_id=uuid4())
    assert excinfo.value.status_code == 404


def test_convert_to_pln():
    assert convert_to_pln(10, "EUR") == 10 * 4.3
    assert convert_to_pln(50, "USD") == 50 * 4.0
    assert convert_to_pln(19, "XYZ") == 19 * 4.2
    assert convert_to_pln(420, "PLN") == 420


def test_get_customer_summary_basic():
    customer_id = uuid4()
    from datetime import datetime

    now = datetime.now(timezone.utc)

    transactions = [
        Transaction(
            transaction_id=uuid4(),
            timestamp=now,
            amount=100,
            currency="USD",
            customer_id=customer_id,
            product_id=uuid4(),
            quantity=1,
        ),
        Transaction(
            transaction_id=uuid4(),
            timestamp=now - timedelta(days=1),
            amount=200,
            currency="EUR",
            customer_id=customer_id,
            product_id=uuid4(),
            quantity=1,
        ),
    ]

    summary = get_customer_summary(customer_id, transactions)
    assert summary["customer_id"] == customer_id
    assert summary["transaction_count"] == len(transactions)
    assert summary["unique_products_count"] == len(
        set(t.product_id for t in transactions)
    )
    assert summary["total_amount_pln"] == 1260.0
    assert summary["last_transaction_date"] == now


def test_get_product_summary_basic():
    product_id = uuid4()
    customer_id = uuid4()
    transactions = [
        Transaction(
            transaction_id=uuid4(),
            product_id=product_id,
            customer_id=customer_id,
            amount=100.0,
            currency="USD",
            quantity=2,
            timestamp=datetime.now(timezone.utc),
        ),
        Transaction(
            transaction_id=uuid4(),
            product_id=product_id,
            customer_id=customer_id,
            amount=200.0,
            currency="EUR",
            quantity=3,
            timestamp=datetime.now(timezone.utc),
        ),
        Transaction(
            transaction_id=uuid4(),
            product_id=product_id,
            customer_id=uuid4(),
            amount=50.0,
            currency="PLN",
            quantity=1,
            timestamp=datetime.now(timezone.utc),
        ),
    ]

    summary = get_product_summary(product_id, transactions)

    assert summary["product_id"] == product_id
    assert summary["transaction_count"] == 3
    assert summary["total_quantity"] == 6
    assert summary["unique_customers_count"] == 2
    assert summary["total_amount_pln"] == 1310.0

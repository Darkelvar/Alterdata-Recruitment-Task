from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.db.models import Transaction


@pytest.mark.anyio
async def test_customer_summary_success(client, async_db):
    customer_id = uuid4()
    product_id = uuid4()
    now = datetime.now(timezone.utc)
    transaction = Transaction(
        transaction_id=uuid4(),
        timestamp=now,
        amount=100,
        currency="USD",
        customer_id=customer_id,
        product_id=uuid4(),
        quantity=1,
    )
    transaction_2 = Transaction(
        transaction_id=uuid4(),
        timestamp=now - timedelta(days=5),
        amount=200,
        currency="EUR",
        customer_id=customer_id,
        product_id=product_id,
        quantity=2,
    )
    transaction_3 = Transaction(
        transaction_id=uuid4(),
        timestamp=now - timedelta(days=15),
        amount=200,
        currency="EUR",
        customer_id=customer_id,
        product_id=product_id,
        quantity=7,
    )
    async_db.add_all([transaction, transaction_2, transaction_3])
    await async_db.commit()

    response = await client.get(f"/api/v1/reports/customer-summary/{customer_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == str(customer_id)
    assert data["transaction_count"] == 3
    assert data["unique_products_count"] == 2
    assert data["total_amount_pln"] == 2120.0
    # replace = quickest fix to python ISO format vs DB format
    assert data["last_transaction_date"] == str(now).replace(" ", "T")

    start_date = now - timedelta(days=10)
    end_date = now + timedelta(days=1)
    response = await client.get(
        f"/api/v1/reports/customer-summary/{customer_id}",
        params={"start_date": start_date, "end_date": end_date},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == str(customer_id)
    assert data["transaction_count"] == 2
    assert data["unique_products_count"] == 2
    assert data["total_amount_pln"] == 1260.0
    assert data["last_transaction_date"] == str(now).replace(" ", "T")


@pytest.mark.anyio
async def test_customer_summary_no_transactions(client):
    non_existent_customer = uuid4()

    response = await client.get(
        f"/api/v1/reports/customer-summary/{non_existent_customer}"
    )
    assert response.status_code == 404
    assert "no transactions found" in response.text.lower()


@pytest.mark.anyio
async def test_product_summary_success(client, async_db):
    product_id = uuid4()
    customer_id = uuid4()
    now = datetime.now(timezone.utc)
    transaction = Transaction(
        transaction_id=uuid4(),
        timestamp=now,
        amount=100,
        currency="USD",
        customer_id=customer_id,
        product_id=product_id,
        quantity=1,
    )
    transaction_2 = Transaction(
        transaction_id=uuid4(),
        timestamp=now - timedelta(days=5),
        amount=200,
        currency="EUR",
        customer_id=customer_id,
        product_id=product_id,
        quantity=2,
    )
    transaction_3 = Transaction(
        transaction_id=uuid4(),
        timestamp=now - timedelta(days=15),
        amount=200,
        currency="EUR",
        customer_id=uuid4(),
        product_id=product_id,
        quantity=7,
    )
    async_db.add_all([transaction, transaction_2, transaction_3])
    await async_db.commit()

    response = await client.get(f"/api/v1/reports/product-summary/{product_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["product_id"] == str(product_id)
    assert data["transaction_count"] == 3
    assert data["total_quantity"] == 10
    assert data["unique_customers_count"] == 2
    assert data["total_amount_pln"] == 2120.0

    start_date = now - timedelta(days=10)
    end_date = now + timedelta(days=1)
    response = await client.get(
        f"/api/v1/reports/product-summary/{product_id}",
        params={"start_date": start_date, "end_date": end_date},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["product_id"] == str(product_id)
    assert data["transaction_count"] == 2
    assert data["total_quantity"] == 3
    assert data["unique_customers_count"] == 1
    assert data["total_amount_pln"] == 1260.0


@pytest.mark.anyio
async def test_product_summary_no_transactions(client):
    non_existent_product = uuid4()

    response = await client.get(
        f"/api/v1/reports/product-summary/{non_existent_product}"
    )
    assert response.status_code == 404
    assert "no transactions found" in response.text.lower()

from datetime import datetime, timezone
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.db.models import Transaction


@pytest.mark.anyio
async def test_get_transactions_returns_all(client, async_db):
    transaction = Transaction(
        transaction_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="USD",
        customer_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        product_id=UUID("222e4567-e89b-12d3-a456-426614174002"),
        quantity=2,
    )
    async_db.add(transaction)
    await async_db.commit()
    transaction = Transaction(
        transaction_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="USD",
        customer_id=UUID("222e4567-e89b-12d3-a456-426614174002"),
        product_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        quantity=2,
    )
    async_db.add(transaction)
    await async_db.commit()

    response = await client.get("/api/v1/transactions/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["data"]) == 2
    assert data["data"][0]["transaction_id"] == "123e4567-e89b-12d3-a456-426614174000"


@pytest.mark.anyio
async def test_get_transactions_with_filters(client, async_db):
    transaction = Transaction(
        transaction_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="USD",
        customer_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        product_id=UUID("222e4567-e89b-12d3-a456-426614174002"),
        quantity=2,
    )
    async_db.add(transaction)
    await async_db.commit()
    transaction = Transaction(
        transaction_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="USD",
        customer_id=UUID("222e4567-e89b-12d3-a456-426614174002"),
        product_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        quantity=2,
    )
    async_db.add(transaction)
    await async_db.commit()
    transaction = Transaction(
        transaction_id=UUID("9429ad84-675f-472d-b699-cf2f08ea8063"),
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="USD",
        customer_id=UUID("9429ad84-675f-472d-b699-cf2f08ea8063"),
        product_id=UUID("111e4567-e89b-12d3-a456-426614174001"),
        quantity=2,
    )
    async_db.add(transaction)
    await async_db.commit()
    response = await client.get(
        "/api/v1/transactions/",
        params={"customer_id": "111e4567-e89b-12d3-a456-426614174001"},
    )
    print(response.request.url)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert all(
        tx["customer_id"] == "111e4567-e89b-12d3-a456-426614174001"
        for tx in data["data"]
    )
    response = await client.get(
        "/api/v1/transactions/",
        params={"product_id": "111e4567-e89b-12d3-a456-426614174001"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(
        tx["product_id"] == "111e4567-e89b-12d3-a456-426614174001"
        for tx in data["data"]
    )
    response = await client.get(
        "/api/v1/transactions/",
        params={"limit": 1, "skip": 1},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["transaction_id"] == "111e4567-e89b-12d3-a456-426614174001"


@pytest.mark.anyio
async def test_get_transactions_invalid_skip_limit(client):
    response = await client.get("/api/v1/transactions/?skip=-1")
    assert response.status_code == 400
    assert "must not be negative" in response.text
    response = await client.get("/api/v1/transactions/?limit=-1")
    assert response.status_code == 400
    assert "must not be negative" in response.text


@pytest.mark.anyio
async def test_get_transactions_empty(client):
    response = await client.get("/api/v1/transactions/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 0
    assert data["total"] == 0

from uuid import uuid4

import pytest

from app.db.models import Transaction
from app.workers import tasks as task_module
from app.workers.tasks import process_csv_contents
from tests.conftest import SessionLocal

VALID_CSV = f"""transaction_id,timestamp,amount,currency,customer_id,product_id,quantity
{uuid4()},2023-01-01T12:00:00,100.0,USD,{uuid4()},{uuid4()},2
{uuid4()},2023-01-02T15:30:00,50.5,EUR,{uuid4()},{uuid4()},1
"""

INVALID_CSV_MISSING_FIELDS = """timestamp,amount,currency,customer_id,product_id,quantity
2023-01-01T12:00:00,100.0,USD,111,222,2
"""

HALF_VALID_CSV = f"""transaction_id,timestamp,amount,currency,customer_id,product_id,quantity
{uuid4()},2023-01-01T12:00:00,100.0,USD,{uuid4()},{uuid4()},2
{uuid4()},2023-01-02T15:30:00,I am an error :),EUR,{uuid4()},{uuid4()},1
"""

INVALID_CSV_BAD_DATA = f"""transaction_id,timestamp,amount,currency,customer_id,product_id,quantity
{uuid4()},INVALID_DATE,not_a_number,USD,{uuid4()},{uuid4()},x
"""


@pytest.fixture(autouse=True)
def patch_task_sessionlocal(monkeypatch):
    # Patch Celery task's SessionLocal to test DB SessionLocal
    monkeypatch.setattr(task_module, "SessionLocal", SessionLocal)


@pytest.mark.anyio
def test_process_csv_success(sync_db):
    result = process_csv_contents(VALID_CSV)

    assert result["all_rows"] == 2
    assert result["successfully_imported_rows"] == 2
    assert result["failed_rows"] == []
    assert result["encountered_errors"] == []

    count = sync_db.query(Transaction).count()
    assert count == 2


@pytest.mark.anyio
def test_process_csv_missing_columns(sync_db):
    with pytest.raises(Exception) as e:
        process_csv_contents(INVALID_CSV_MISSING_FIELDS)

    assert "Missing required columns" in str(e.value)


@pytest.mark.anyio
def test_process_csv_with_bad_rows(sync_db):
    result = process_csv_contents(INVALID_CSV_BAD_DATA)

    assert result["all_rows"] == 1
    assert result["successfully_imported_rows"] == 0
    assert 1 in result["failed_rows"]
    assert len(result["encountered_errors"]) == 1

    # Ensure DB remains unchanged
    assert sync_db.query(Transaction).count() == 0


@pytest.mark.anyio
def test_process_csv_half_success(sync_db):
    result = process_csv_contents(HALF_VALID_CSV)

    assert result["all_rows"] == 2
    assert result["successfully_imported_rows"] == 1
    assert result["failed_rows"] == [2]
    assert len(result["encountered_errors"]) == 1

    count = sync_db.query(Transaction).count()
    assert count == 1

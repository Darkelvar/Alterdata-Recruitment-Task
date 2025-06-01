import pytest

VALID_CSV = """transaction_id,timestamp,amount,currency,customer_id,product_id,quantity
123e4567-e89b-12d3-a456-426614174000,2023-01-01T12:00:00,100.0,USD,111e4567-e89b-12d3-a456-426614174001,222e4567-e89b-12d3-a456-426614174002,2
"""

EMPTY_CSV = ""


@pytest.mark.anyio
async def test_valid_csv_upload(mocker, client):
    mock_delay = mocker.patch(
        "app.api.api_v1.endpoints.transactions.process_csv_contents.delay"
    )
    mock_task = mock_delay.return_value
    mock_task.id = "fake-task-id"

    response = await client.post(
        "/api/v1/transactions/upload",
        files={"file": ("test.csv", VALID_CSV, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["task_id"] == "fake-task-id"
    mock_delay.assert_called_once()


@pytest.mark.anyio
async def test_empty_file_upload(client):
    response = await client.post(
        "/api/v1/transactions/upload",
        files={"file": ("empty.csv", EMPTY_CSV, "text/csv")},
    )
    assert response.status_code == 400
    assert "Uploaded file is empty" in response.text

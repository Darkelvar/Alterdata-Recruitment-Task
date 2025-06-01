from celery.result import AsyncResult
from fastapi import APIRouter

from app.core.exceptions import AppException
from app.core.logging_config import logger
from app.workers.celery_worker import celery_app

router = APIRouter()


@router.get("/{task_id}")
def get_task_result(task_id: str):
    try:
        result = AsyncResult(task_id, app=celery_app)

        if result.state == "PENDING":
            return {"status": "PENDING", "message": "Task is still processing"}

        return {
            "status": result.state,
            "result": result.result,
        }
    except Exception as e:
        logger.exception(
            f"Unexpected error fetching task result for {task_id}. Error: {e}"
        )
        raise AppException(
            f"Unexpected error fetching task result for {task_id}.",
            code="GET_TASK_RESULT_FAIL",
            status_code=500,
        )

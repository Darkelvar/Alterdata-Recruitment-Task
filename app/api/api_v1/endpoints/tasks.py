from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException

from app.logging_config import logger
from app.workers.celery_worker import celery_app

router = APIRouter()


@router.get("/tasks/{task_id}/result")
def get_task_result(task_id: str):
    try:
        result = AsyncResult(task_id, app=celery_app)

        if result.state == "PENDING":
            return {"status": "PENDING", "message": "Task is still processing"}

        if result.state == "FAILURE":
            return {
                "status": "FAILURE",
                "message": result.result,
            }

        if result.state == "SUCCESS":
            return {
                "status": "SUCCESS",
                "result": result.result,
            }

        logger.warning(f"Task {task_id} in unexpected state: {result.state}")
        return {"status": result.state}
    except Exception as e:
        logger.exception(f"Exception while fetching task result for {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving task result")

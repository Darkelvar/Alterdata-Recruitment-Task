from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from app.workers.tasks import process_csv_contents

router = APIRouter()


@router.post("/upload", response_class=JSONResponse)
def upload_transactions(file: UploadFile = File(...)):
    try:
        contents = file.file.read().decode("utf-8")
        task = process_csv_contents.delay(contents)
        return {
            "message": f"{file.filename} is being processed asynchronously.",
            "task_id": task.id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

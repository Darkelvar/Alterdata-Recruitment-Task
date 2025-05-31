from fastapi import APIRouter

from app.api.api_v1.endpoints import reports, transactions, tasks

api_router = APIRouter()
api_router.include_router(
    transactions.router, prefix="/transactions", tags=["transactions"]
)
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

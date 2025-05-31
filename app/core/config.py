from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Alterdata Recruitment Task"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "System for processing and aggregating transaction data"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = (
        "postgresql+asyncpg://transaction_user:transaction_pass@db:5432/transaction_db"
    )
    DATABASE_URL_SYNC: str = (
        "postgresql+psycopg2://transaction_user:transaction_pass@db:5432/transaction_db"
    )
    REDIS_HOST: str = "redis"
    REDIS_PORT: str = "6379"


settings = Settings()

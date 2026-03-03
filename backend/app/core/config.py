from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://etuser:etpass123@localhost:5432/employee_tracking"
    SECRET_KEY: str = "employee-tracking-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    INSIGHTFUL_API_BASE_URL: str = "https://app.insightful.io/api/v1"
    INSIGHTFUL_API_TOKEN: Optional[str] = None

    FULL_DAY_HOURS: float = 9.0
    THRESHOLD_HOURS_PER_DAY: float = 8.25
    PAID_HOLIDAYS_PER_MONTH: int = 2

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

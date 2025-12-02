import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "pranay2006")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkeychangeme")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

settings = Settings()

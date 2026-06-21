from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    ENV: str = "development"
    GEMINI_API_KEY: str = Field(..., alias="GEMINI_API_KEY")

    # Database
    POSTGRES_USER: str = "Dayachand"
    POSTGRES_PASSWORD: str = "Daya@mannu"
    POSTGRES_DB: str = "transaction_pipeline"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    @property
    def DATABASE_URL(self) -> str:
        # Crucial: This must evaluate to postgresql://username:password@db:5432/dbname
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # Read from a .env file if it exists locally
    model_config = SettingsConfigDict(env_file="docker/.env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
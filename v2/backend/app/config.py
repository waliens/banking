from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://banking:password@localhost:5432/banking_v2"
    jwt_secret_key: str = "change-me-in-production"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30
    model_path: str = "/data/models"
    cors_origins: list[str] = ["http://localhost:5173"]
    cookie_secure: bool = True

    model_config = {"env_prefix": "BANKING_", "env_file": ".env"}


settings = Settings()

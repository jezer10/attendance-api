from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    log_level: str = "INFO"
    base_url: str = "http://localhost:8000"
    company_id: int = 7040
    request_timeout:int = 30
    max_retries: int = 3
    latitude: float = 0.0
    longitude: float = 0.0
    host: str = "0.0.0.0"

    port: int = 8000

    supabase_url: str = "https://your-supabase-url.supabase.co"
    supabase_key: str = "your-supabase-anon-or-service-role-key"

    class Config:
        env_file = ".env"
        env_prefix = "APP_"


settings = Settings()

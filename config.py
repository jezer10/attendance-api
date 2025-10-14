from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    base_url: str = "https://movil.asisscad.cl"
    company_id: int
    request_timeout: int = 30
    max_retries: int = 3
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    log_level: str = "INFO"
    latitude: float = -6.7711
    longitude: float = -79.8431
    supported_locales: list[str] = ["en", "es", "fr"]
    default_locale: str = "es"
    port: int = 8080

    class Config:
        env_file = ".env"
        env_prefix = "APP_"  # 👈 todas las vars deben empezar así


settings = Settings()

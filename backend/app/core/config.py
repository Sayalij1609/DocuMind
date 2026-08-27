from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Nexora"
    app_version: str = "1.0.0"
    debug: bool = True
    max_file_size: int = 10 * 1024 * 1024

    upload_dir: str = "uploads"

    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
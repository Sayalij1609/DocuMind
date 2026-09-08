from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Nexora"
    app_version: str = "1.0.0"
    debug: bool = True
    max_file_size: int = 10 * 1024 * 1024

    upload_dir: str = "uploads"

    database_url: str

    tesseract_cmd: str = "tesseract"

    classification_model_dir: str = (
        "../ml/artifacts/classification"
    )

    classification_confidence_threshold: float = 0.5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
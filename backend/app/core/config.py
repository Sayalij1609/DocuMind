from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Documind"
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

    # LayoutLMv3 (Phase 6)
    layoutlm_enabled: bool = False
    layoutlm_model_dir: str = ""
    layoutlm_device: str = "auto"

    # Anomaly Detection (Phase 9)
    anomaly_model_path: str = (
        "artifacts/anomaly/isolation_forest.joblib"
    )
    anomaly_contamination: float = 0.05
    anomaly_min_training_samples: int = 10

    # Groq AI Analysis (Semantic Intelligence)
    groq_api_key: Optional[str] = None
    groq_model: str = "qwen/qwen3.8-27b"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
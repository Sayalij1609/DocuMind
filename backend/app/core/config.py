from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Nexora"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
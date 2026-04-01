"""Application configuration using pydantic-settings."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment or defaults."""

    # App
    APP_NAME: str = "AI Roster System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database — override with postgresql://... for production
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/roster.db"
    DB_ECHO: bool = False

    # Auth / JWT
    SECRET_KEY: str = "change-me-to-a-random-32-char-secret-in-prod"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # Demo account
    DEMO_EMAIL: str = "demo@roster.app"
    DEMO_PASSWORD: str = "demo1234"
    DEMO_FULL_NAME: str = "Demo User"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Scheduling defaults
    DEFAULT_REST_HOURS_MEDICAL: int = 8
    DEFAULT_REST_HOURS_IT: int = 8
    MAX_CONSECUTIVE_NIGHTS_MEDICAL: int = 3
    MAX_CONSECUTIVE_NIGHTS_IT: int = 2
    MAX_SHIFTS_PER_WEEK_MEDICAL: int = 6
    MAX_SHIFTS_PER_WEEK_IT: int = 5

    # Scoring weights - Medical
    MEDICAL_ROTATION_WEIGHT: float = 0.40
    MEDICAL_AVAILABILITY_WEIGHT: float = 0.30
    MEDICAL_REST_WEIGHT: float = 0.20
    MEDICAL_FAIRNESS_WEIGHT: float = 0.10

    # Scoring weights - IT
    IT_SKILL_WEIGHT: float = 0.40
    IT_WORKLOAD_WEIGHT: float = 0.30
    IT_AVAILABILITY_WEIGHT: float = 0.20
    IT_WEEKEND_WEIGHT: float = 0.10

    # Learning
    LEARNING_DECAY_FACTOR: float = 0.85
    LEARNING_MIN_HISTORY: int = 3

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return singleton settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

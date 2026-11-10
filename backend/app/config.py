"""Application configuration for HalluGuard."""

import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

# Load .env file if it exists
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

# Set offline defaults for model hub to prevent blocking on network calls in sandboxed environments
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


class Settings(BaseModel):
    """HalluGuard application settings."""

    # Application settings
    app_name: str = "HalluGuard Backend"
    app_version: str = "1.0.0"
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    host: str = Field(default_factory=lambda: os.getenv("APP_HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(os.getenv("APP_PORT", "8000")))
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # LettuceDetect Model settings
    model_path: str = Field(
        default_factory=lambda: os.getenv(
            "MODEL_PATH", "KRLabsOrg/lettucedect-base-modernbert-en-v1"
        )
    )
    detector_method: str = Field(
        default_factory=lambda: os.getenv("DETECTOR_METHOD", "transformer")
    )
    device: str = Field(default_factory=lambda: os.getenv("DEVICE", "cpu"))
    max_length: int = Field(
        default_factory=lambda: int(os.getenv("MAX_LENGTH", "4096"))
    )

    # DeBERTa-v3 NLI Model settings (Phase 8/9 Hybrid Verification)
    nli_model_path: str = Field(
        default_factory=lambda: os.getenv(
            "NLI_MODEL_PATH", "cross-encoder/nli-deberta-v3-small"
        )
    )
    nli_contradiction_threshold: float = Field(
        default_factory=lambda: float(os.getenv("NLI_CONTRADICTION_THRESHOLD", "0.60"))
    )
    nli_enabled: bool = Field(
        default_factory=lambda: os.getenv("NLI_ENABLED", "true").lower() in ("true", "1", "yes")
    )

    # Supabase settings
    supabase_url: str | None = Field(
        default_factory=lambda: os.getenv("SUPABASE_URL") or None
    )
    supabase_service_role_key: str | None = Field(
        default_factory=lambda: os.getenv("SUPABASE_SERVICE_ROLE_KEY") or None
    )

    @property
    def is_supabase_configured(self) -> bool:
        """Check if Supabase credentials are validly provided."""
        return bool(
            self.supabase_url
            and self.supabase_service_role_key
            and not self.supabase_url.startswith("your-")
            and not self.supabase_service_role_key.startswith("your-")
        )


settings = Settings()


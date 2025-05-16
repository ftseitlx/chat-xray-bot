import os
import logging
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Configure logger
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Telegram Bot settings
    BOT_TOKEN: str
    
    # OpenAI API settings
    OPENAI_API_KEY: str
    
    # Ollama settings
    USE_LOCAL_LLM: bool = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://llama2-ollama:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama2:7b-chat")
    
    # Default model configurations
    PRIMARY_MODEL: str = "gpt-3.5-turbo"
    META_MODEL: str = "gpt-4-turbo"  # Using GPT-4 Turbo with 128K token context window
    
    # Webhook settings (for production)
    WEBHOOK_HOST: Optional[str] = None
    WEBHOOK_PATH: str = "/webhook"
    WEBHOOK_URL: Optional[str] = None
    
    # Server settings
    PORT: int = 8080
    HOST: str = "0.0.0.0"
    
    # Sentry settings
    SENTRY_DSN: Optional[str] = None
    ENVIRONMENT: str = "development"
    
    # File paths and limits
    BASE_DIR: Path = Path(__file__).parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    REPORT_DIR: Path = BASE_DIR / "reports"
    MAX_FILE_SIZE: int = 2 * 1024 * 1024  # 2 MB
    
    # Chunking settings
    MAX_MESSAGES_PER_CHUNK: int = 500
    MAX_TOKENS_PER_CHUNK: int = 2000
    
    # Retention periods (in hours)
    UPLOAD_RETENTION_HOURS: int = 1
    REPORT_RETENTION_HOURS: int = 72
    
    # Logging and cost tracking
    ENABLE_COST_TRACKING: bool = True
    
    # Token and rate limit settings
    MAX_MESSAGES_FOR_META: int = int(os.getenv("MAX_MESSAGES_FOR_META", 100))
    
    # Rate limit handling
    ENABLE_RETRY_ON_RATE_LIMIT: bool = os.getenv("ENABLE_RETRY_ON_RATE_LIMIT", "true").lower() == "true"
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", 3))
    RETRY_DELAY_SECONDS: int = int(os.getenv("RETRY_DELAY_SECONDS", 1))
    
    # Parallelization settings
    OPENAI_CONCURRENCY_LIMIT: int = int(os.getenv("OPENAI_CONCURRENCY_LIMIT", 3))
    
    # Large file handling
    MAX_ALLOWED_MESSAGES: int = int(os.getenv("MAX_ALLOWED_MESSAGES", 5000))
    LARGE_CHAT_THRESHOLD: int = int(os.getenv("LARGE_CHAT_THRESHOLD", 1000))
    AGGRESSIVE_CHUNKING_SIZE: int = int(os.getenv("AGGRESSIVE_CHUNKING_SIZE", 15))
    
    # GPT-3.5 Turbo cost per 1K tokens (input and output combined for simplicity)
    GPT35_COST_PER_TOKEN: float = float(os.getenv("GPT35_COST_PER_TOKEN", 0.0000015))
    
    # GPT-4 cost per 1K tokens (input and output combined for simplicity)
    GPT4_COST_PER_TOKEN: float = float(os.getenv("GPT4_COST_PER_TOKEN", 0.00003))
    
    # GPT-4 Turbo cost per 1K tokens
    GPT4_TURBO_COST_PER_TOKEN: float = float(os.getenv("GPT4_TURBO_COST_PER_TOKEN", 0.00001))
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Create directories if they don't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.REPORT_DIR, exist_ok=True)

# Automatically construct webhook URL if host is provided but URL is not
if settings.WEBHOOK_HOST and not settings.WEBHOOK_URL:
    settings.WEBHOOK_URL = f"{settings.WEBHOOK_HOST}{settings.WEBHOOK_PATH}"
    logger.info(f"Constructed webhook URL: {settings.WEBHOOK_URL}") 
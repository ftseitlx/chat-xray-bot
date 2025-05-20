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
    
    # Ollama settings - disabled
    USE_LOCAL_LLM: bool = False  # Disable local LLM
    OLLAMA_URL: str = ""  # Empty to avoid connection attempts
    OLLAMA_MODEL: str = ""  # Empty to avoid usage
    
    # Default model configurations
    PRIMARY_MODEL: str = "gpt-3.5-turbo"
    META_MODEL: str = "gpt-4-turbo" # Ensure this is a current, powerful GPT-4 Turbo model
    
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
    MAX_MESSAGES_FOR_META: int = int(os.getenv("MAX_MESSAGES_FOR_META", 400)) # Kept at 400
    
    # Rate limit handling
    ENABLE_RETRY_ON_RATE_LIMIT: bool = os.getenv("ENABLE_RETRY_ON_RATE_LIMIT", "true").lower() == "true"
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", 3))
    RETRY_DELAY_SECONDS: int = int(os.getenv("RETRY_DELAY_SECONDS", 1))
    
    # Parallelization settings
    OPENAI_CONCURRENCY_LIMIT: int = int(os.getenv("OPENAI_CONCURRENCY_LIMIT", 5)) # Increased to 5
    
    # Large file handling
    MAX_ALLOWED_MESSAGES: int = int(os.getenv("MAX_ALLOWED_MESSAGES", 5000))
    LARGE_CHAT_THRESHOLD: int = int(os.getenv("LARGE_CHAT_THRESHOLD", 1000))
    AGGRESSIVE_CHUNKING_SIZE: int = int(os.getenv("AGGRESSIVE_CHUNKING_SIZE", 15))
    
    # Cost per 1K tokens (refer to OpenAI pricing for up-to-date values)
    # Assuming combined input/output for simplicity, or a primary billing metric (e.g., input tokens)
    # For gpt-3.5-turbo (e.g., gpt-3.5-turbo-0125: $0.0005/1K input, $0.0015/1K output)
    # Let's use an average or a representative value if input/output are billed separately.
    # For example, if input is dominant for primary analysis.
    COST_PER_1K_TOKENS_GPT35_TURBO: float = float(os.getenv("COST_PER_1K_TOKENS_GPT35_TURBO", 0.0010)) # Example: $1.00/1M tokens
    
    # For gpt-4-turbo (e.g., gpt-4-turbo-preview (alias gpt-4-turbo-2024-04-09): $0.01/1K input, $0.03/1K output)
    # For meta-report, output is substantial. Let's use a weighted average or separate them if cost logic allows.
    # For this config, we'll use a single value. Bot logic should handle input/output costs if possible.
    # This value will be used for meta_tokens which includes input + output from the call.
    # Weighted average (e.g. 75% input, 25% output for a meta-report call): (0.01*0.75 + 0.03*0.25) = 0.0075 + 0.0075 = $0.015 / 1K avg
    # Simpler: if input tokens dominate the count.
    COST_PER_1K_TOKENS_GPT4_TURBO_INPUT: float = float(os.getenv("COST_PER_1K_TOKENS_GPT4_TURBO_INPUT", 0.01))
    COST_PER_1K_TOKENS_GPT4_TURBO_OUTPUT: float = float(os.getenv("COST_PER_1K_TOKENS_GPT4_TURBO_OUTPUT", 0.03))

    # Old combined cost variables for reference or if simpler model needed.
    # GPT35_COST_PER_TOKEN: float = float(os.getenv("GPT35_COST_PER_TOKEN", 0.0000015))
    # GPT4_TURBO_COST_PER_TOKEN: float = float(os.getenv("GPT4_TURBO_COST_PER_TOKEN", 0.00001))


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
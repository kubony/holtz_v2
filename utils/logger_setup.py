from loguru import logger
from config.settings import settings

def setup_logging():
    logger.add("logs/app.log", rotation="500 MB", level="INFO")
    if settings.OPENAI_API_KEY:
        masked_key = f"{settings.OPENAI_API_KEY.get_secret_value()[:5]}...{settings.OPENAI_API_KEY.get_secret_value()[-5:]}"
        logger.info(f"OPENAI_API_KEY loaded: {masked_key}")
    else:
        logger.error("OPENAI_API_KEY is not set in the environment variables.")

def truncate_string(s, max_length=100):
    return s if len(s) <= max_length else s[:max_length] + '...'

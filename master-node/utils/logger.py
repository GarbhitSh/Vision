"""
Logging utilities
"""
import logging
import sys
from config.settings import settings


def setup_logger(name: str = "vision") -> logging.Logger:
    """Setup logger with configuration"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # File handler (if log file is configured)
    if settings.LOG_FILE:
        import os
        os.makedirs(os.path.dirname(settings.LOG_FILE) if os.path.dirname(settings.LOG_FILE) else ".", exist_ok=True)
        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    if settings.LOG_FILE:
        file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


# Create default logger
logger = setup_logger()


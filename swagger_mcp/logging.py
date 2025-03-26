"""
Centralized logging configuration for the swagger-mcp project.
Provides a consistent logging interface across all modules.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Constants
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_DIR = 'logs'
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

def setup_logger(name: str, log_level: int = DEFAULT_LOG_LEVEL) -> logging.Logger:
    """
    Set up and return a logger instance with both console and file handlers.
    
    Args:
        name: The name of the logger, typically __name__ from the calling module
        log_level: The logging level to use (default: INFO)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure the logger if it hasn't been configured before
    if not logger.handlers:
        logger.setLevel(log_level)
        
        # Create formatters
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        try:
            log_dir = Path(DEFAULT_LOG_DIR)
            log_dir.mkdir(exist_ok=True)
            
            log_file = log_dir / f'{name}.log'
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=MAX_LOG_SIZE,
                backupCount=BACKUP_COUNT
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Failed to set up file logging: {e}")
    
    return logger

# Create a default logger for direct imports
logger = setup_logger(__name__)

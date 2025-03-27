import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path



def setup_logger():
    """
    Configure and set up the logging system with file-based output
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logger
    logger = logging.getLogger("product_category_api")
    logger.setLevel(logging.INFO)
    
    # Create log file handler with rotation (max 5MB per file, keeping 3 backup files)
    log_file_path = log_dir / "api.log"
    file_handler = RotatingFileHandler(
        filename=log_file_path,
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=3,
        encoding="utf-8"
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    
    # Create formatter and add it to the handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class NoOpLogger(logging.Logger):
    def __init__(self, name):
        self.name = name
    
    def debug(self, msg, *args, **kwargs):
        pass
    
    def info(self, msg, *args, **kwargs):
        pass
    
    def warning(self, msg, *args, **kwargs):
        pass
    
    def error(self, msg, *args, **kwargs):
        pass
    
    def critical(self, msg, *args, **kwargs):
        pass
    
    def exception(self, msg, *args, **kwargs):
        pass

    
# Return a no-op logger unless REAL_LOGGER is set to 'true'
if os.getenv('REAL_LOGGER', '').lower() != 'true':
    logger = NoOpLogger("product_category_api")
else:
    logger = setup_logger()
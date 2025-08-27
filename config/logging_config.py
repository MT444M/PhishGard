# PhishGard-AI/config/logging_config.py

import logging
import sys

def setup_logging():
    """
    Configures the logging for the application.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Suppress verbose logging from third-party libraries
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

def get_logger(name: str):
    """
    Returns a logger instance for a given module name.
    """
    return logging.getLogger(name)

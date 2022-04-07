import logging
import os

logger = logging.getLogger(f"{os.getenv('LOGGER', 'gunicorn')}.error")

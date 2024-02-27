import logging
import sys

from app.core.config import LOG_LEVEL

logger = logging.getLogger("meta")
logger.setLevel(LOG_LEVEL)
log_to_stdout = logging.StreamHandler(sys.stdout)
log_to_stdout.setLevel(LOG_LEVEL)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log_to_stdout.setFormatter(formatter)
logger.addHandler(log_to_stdout)

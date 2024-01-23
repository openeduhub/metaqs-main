import logging
import os

from dotenv import load_dotenv
from starlette.datastructures import CommaSeparatedStrings


load_dotenv()

API_PORT = 8081

ROOT_PATH = os.getenv("ROOT_PATH", "")
API_DEBUG = os.getenv("API_DEBUG", "False").strip().lower() == "true"
ALLOWED_HOSTS = CommaSeparatedStrings(os.getenv("ALLOWED_HOSTS", "*"))
LOG_LEVEL = int(os.getenv("LOG_LEVEL", logging.INFO))

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")

MAX_CONNECTIONS_COUNT = int(os.getenv("MAX_CONNECTIONS_COUNT", 10))
MIN_CONNECTIONS_COUNT = int(os.getenv("MIN_CONNECTIONS_COUNT", 10))

ELASTIC_INDEX = "workspace"
ELASTIC_TOTAL_SIZE = 500_000  # Maximum number of entries elasticsearch queries, very large to query all entries
ELASTICSEARCH_TIMEOUT = int(os.getenv("ELASTICSEARCH_TIMEOUT", 20))


BACKGROUND_TASK_TIME_INTERVAL = int(os.getenv("BACKGROUND_TASK_TIME_INTERVAL", 10 * 60))
# Cron like schedule when quality matrix should be stored. Default to every 6 hours
# see https://crontab.guru/#0_0,6,12,18_*_*_*
QUALITY_MATRIX_BACKUP_SCHEDULE = os.getenv(
    "QUALITY_MATRIX_BACKUP_SCHEDULE", "0 0,6,12,18 * * *"
)

# The Database URL to use for storing historic quality matrix information
DATABASE_URL = os.getenv("DATABASE_URL", None)

# Used to fetch the metadataset which determines the column names of some widgets.
METADATASET_URL = os.getenv("METADATASET_URL")

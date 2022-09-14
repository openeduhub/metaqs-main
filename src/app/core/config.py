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

# Time in seconds between consecutive background calls
BACKGROUND_TASK_TIME_INTERVAL = int(os.getenv("BACKGROUND_TASK_TIME_INTERVAL", 10 * 60))

# Whether to enable the database functionality for storing and loading historic quality matrix snapshots
ENABLE_DATABASE = os.getenv("ENABLE_DATABASE", "True").lower() == "true"

# Used to fetch the metadataset which determines the column names of some widgets.
METADATASET_URL = os.getenv("METADATASET_URL")

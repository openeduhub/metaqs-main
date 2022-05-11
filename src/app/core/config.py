import os

from databases import DatabaseURL
from starlette.datastructures import CommaSeparatedStrings

API_PORT = 8081

ROOT_PATH = os.getenv("ROOT_PATH", "")
API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "X-API-KEY"
API_DEBUG = False  # os.getenv("LOG_LEVEL", "").strip().lower() == "debug"
ALLOWED_HOSTS = CommaSeparatedStrings(os.getenv("ALLOWED_HOSTS", "*"))
LOG_LEVEL = os.getenv("LOG_LEVEL")

BACKGROUND_TASK_ANALYTICS_INTERVAL = int(
    os.getenv("BACKGROUND_TASK_ANALYTICS_INTERVAL", 0)
)
BACKGROUND_TASK_SEARCH_STATS_INTERVAL = int(
    os.getenv("BACKGROUND_TASK_SEARCH_STATS_INTERVAL", 0)
)
BACKGROUND_TASK_SPELLCHECK_INTERVAL = int(
    os.getenv("BACKGROUND_TASK_SPELLCHECK_INTERVAL", 0)
)
# sleep delay between subsequent search stats requests against elastic, default 500ms
BACKGROUND_TASK_SEARCH_STATS_SLEEP_INTERVAL = int(
    os.getenv("BACKGROUND_TASK_SEARCH_STATS_SLEEP_INTERVAL", 0)
)

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB = os.getenv("POSTGRES_DB")

    DATABASE_URL = DatabaseURL(
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"
    )
else:
    DATABASE_URL = DatabaseURL(DATABASE_URL)

MAX_CONNECTIONS_COUNT = int(os.getenv("MAX_CONNECTIONS_COUNT", 10))
MIN_CONNECTIONS_COUNT = int(os.getenv("MIN_CONNECTIONS_COUNT", 10))

API_VERSION = os.getenv("API_VERSION", "v1")

ELASTIC_INDEX = "workspace"
ELASTIC_TOTAL_SIZE = 1_000_000  # Maximum number of entries elasticsearch queries, very large to query all entries
ELASTICSEARCH_TIMEOUT = int(os.getenv("ELASTICSEARCH_TIMEOUT", 20))

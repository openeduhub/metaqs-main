import os

from databases import DatabaseURL
from starlette.datastructures import CommaSeparatedStrings

ROOT_PATH = os.getenv("ROOT_PATH", "")
API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "X-API-KEY"
ALLOWED_HOSTS = CommaSeparatedStrings(os.getenv("ALLOWED_HOSTS", "*"))
LOG_LEVEL = os.getenv("LOG_LEVEL")
DEBUG = False  # os.getenv("LOG_LEVEL", "").strip().lower() == "debug"

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

DBT_URL = "http://dbt:8580/jsonrpc"
LANGUAGETOOL_URL = "http://languagetool:8010/v2"
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

PROJECT_NAME = "MetaQS"
API_VERSION = os.getenv("API_VERSION", "v1")

ELASTIC_INDEX = "workspace"
ELASTIC_MAX_SIZE = 10000
ELASTICSEARCH_TIMEOUT = int(os.getenv("ELASTICSEARCH_TIMEOUT", 20))

LANGUAGETOOL_ENABLED_CATEGORIES = [
    "TYPOGRAPHY",
    "PUNCTUATION",
    "CASING",
    "TYPOS",
    "COMPOUNDING",
]

PORTAL_ROOT_ID = "5e40e372-735c-4b17-bbf7-e827a5702b57"
PORTAL_ROOT_PATH = "/".join(
    [
        "00abdb05-6c96-4604-831c-b9846eae7d2d",
        "c73dd8be-e520-42bb-b6f1-f989714d09fc",
        "d1afbeaa-1d20-4d1d-a1aa-8d8903edff38",
        "3305f552-c931-4bcc-842b-939c99752bd5",
        "ef7e295e-d931-49eb-b1e2-76475f849e8a",
        "572c19f6-37df-4090-a116-cc93b648785d",
        "7050d184-db61-4e4b-86a0-74f35604a7da",
        "7dfccbf5-191f-4856-849a-0e6c11ff1a8d",
        "4156d4d0-79ec-4606-aab3-0133f0602561",
        "35054614-72c8-49b2-9924-7b04c7f3bf71",
        "5e40e372-735c-4b17-bbf7-e827a5702b57",
    ]
)

ENABLE_MATERIALS_API = False
ENABLE_COLLECTIONS_API = False

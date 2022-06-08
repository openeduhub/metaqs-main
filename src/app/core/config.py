import os

from starlette.datastructures import CommaSeparatedStrings

API_PORT = 8081

ROOT_PATH = os.getenv("ROOT_PATH", "")
API_DEBUG = False  # os.getenv("LOG_LEVEL", "").strip().lower() == "debug"
ALLOWED_HOSTS = CommaSeparatedStrings(os.getenv("ALLOWED_HOSTS", "*"))
LOG_LEVEL = os.getenv("LOG_LEVEL")

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")

MAX_CONNECTIONS_COUNT = int(os.getenv("MAX_CONNECTIONS_COUNT", 10))
MIN_CONNECTIONS_COUNT = int(os.getenv("MIN_CONNECTIONS_COUNT", 10))

ELASTIC_INDEX = "workspace"
ELASTIC_TOTAL_SIZE = 500_000  # Maximum number of entries elasticsearch queries, very large to query all entries
ELASTICSEARCH_TIMEOUT = int(os.getenv("ELASTICSEARCH_TIMEOUT", 20))

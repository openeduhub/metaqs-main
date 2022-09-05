import os
from urllib.parse import quote


def database_url():
    postgres_user: str = os.getenv("POSTGRES_USER")
    postgres_password = quote(os.getenv("POSTGRES_PASSWORD"))
    postgres_server: str = os.getenv("POSTGRES_SERVER", "localhost")
    postgres_port: str = os.getenv("POSTGRES_PORT", 5432)
    postgres_db: str = os.getenv("POSTGRES_DB")
    return f"postgresql://{postgres_user}:{postgres_password}@{postgres_server}:{postgres_port}/{postgres_db}"

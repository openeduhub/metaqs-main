import os


def database_url():
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv(
        "POSTGRES_PORT", 5432
    )  # default postgres port is 5432
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "tdd")
    return f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"


def timestamps():
    print(database_url())
    return [0, 1651755081, 1652359881]

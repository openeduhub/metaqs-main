import os
from typing import Any

from sqlalchemy import JSON, Column, Integer, create_engine, select
from sqlalchemy.orm import as_declarative, declared_attr, sessionmaker


def database_url():
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv(
        "POSTGRES_PORT", 5432
    )  # default postgres port is 5432
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "tdd")
    return f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"


def engine():
    return create_engine(database_url())


def session():
    _engine = engine()
    Base.metadata.create_all(bind=_engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@as_declarative()
class Base:
    id: Any
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class QualityMatrix(Base):
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(Integer, nullable=False)
    quality_matrix = Column(JSON, nullable=False)


def timestamps():
    conn = engine().connect()
    s = select()
    result = conn.execute(s)
    for row in result:
        print(row)
    return [0, 1651755081, 1652359881]

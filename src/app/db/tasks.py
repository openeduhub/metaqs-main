from functools import cache
from typing import Iterator

from fastapi_utils.session import FastAPISessionMaker
from sqlalchemy import create_engine, Column, Integer, Text, JSON
from sqlalchemy.orm import Session, declarative_base

from app.core.config import DATABASE_URL


Base = declarative_base()


class Timeline(Base):
    """Table will be automatically created at application start time if it does not exist."""

    __tablename__ = "timeline"
    timestamp = Column(Integer, nullable=False, primary_key=True)
    mode = Column(Text, nullable=False, primary_key=True)
    node_id = Column(Text, nullable=False, primary_key=True)
    quality_matrix = Column(JSON, nullable=False)


@cache
def session_maker():
    mkr = FastAPISessionMaker(DATABASE_URL)

    if DATABASE_URL.startswith("sqlite"):
        # workaround for local testing. See https://fastapi.tiangolo.com/tutorial/sql-databases/#note
        mkr._cached_engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

    Base.metadata.create_all(mkr.cached_engine, checkfirst=True)  # won't create if they already exist

    return mkr


def get_session() -> Iterator[Session]:
    yield from session_maker().get_db()

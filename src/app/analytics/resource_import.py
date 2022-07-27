from datetime import datetime

from sqlalchemy.orm import Session

from src.app.core.config import PORTAL_ROOT_ID
from src.app.crud.elastic import query_collections, query_materials
from src.app.elastic import Search
from src.app.pg.metadata import Collection, Material


def import_collections(session: Session, derived_at: datetime):
    s = (
        Search()
        .query(query_collections(ancestor_id=PORTAL_ROOT_ID))
        .source(includes=["type", "aspects", "properties.*", "nodeRef.*", "path"])
    )

    seen = set()
    for hit in s.scan():
        if hit.nodeRef["id"] in seen:
            continue

        seen.add(hit.nodeRef["id"])

        session.add(
            Collection(id=hit.nodeRef["id"], doc=hit.to_dict(), derived_at=derived_at)
        )


def import_materials(session: Session, derived_at: datetime):
    s = (
        Search()
        .query(query_materials(ancestor_id=PORTAL_ROOT_ID))
        .source(
            includes=[
                "type",
                "aspects",
                "properties.*",
                "nodeRef.*",
                "collections.nodeRef.id",
            ]
        )
    )

    seen = set()
    for hit in s.scan():
        if hit.nodeRef["id"] in seen:
            continue

        seen.add(hit.nodeRef["id"])

        session.add(
            Material(id=hit.nodeRef["id"], doc=hit.to_dict(), derived_at=derived_at)
        )

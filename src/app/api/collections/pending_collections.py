import uuid
from typing import Optional

from fastapi import HTTPException
from glom import Coalesce, Iter, glom
from pydantic import BaseModel

from app.api.api import CollectionAttribute
from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.logging import logger
from app.elastic.attributes import ElasticResourceAttribute
from app.elastic.search import CollectionSearch


class Collection(BaseModel):
    collection_id: uuid.UUID
    title: str
    keywords: list[str]
    description: Optional[str]


def get_pending_collections(collection_id: uuid.UUID, missing: CollectionAttribute) -> list[Collection]:
    """
    See API doc.
    """

    source: list = [
        ElasticResourceAttribute.NODE_ID,
        ElasticResourceAttribute.COLLECTION_TITLE,
        ElasticResourceAttribute.KEYWORDS,
        ElasticResourceAttribute.COLLECTION_DESCRIPTION,
    ]

    search = (
        CollectionSearch()
        .collection_filter(collection_id=collection_id)
        .missing_attribute_filter(missing=missing)
        .source(include=[attr.path for attr in source])
        .extra(size=ELASTIC_TOTAL_SIZE, from_=0)
    )

    response = search.execute()
    if not response.success():
        raise HTTPException(status_code=502, detail="Failed to query elastic search")

    missing_attributes_spec = {
        "title": Coalesce(ElasticResourceAttribute.COLLECTION_TITLE.path, default=None),
        "keywords": (
            Coalesce(ElasticResourceAttribute.KEYWORDS.path, default=[]),
            Iter().all(),
        ),
        "description": Coalesce(ElasticResourceAttribute.COLLECTION_DESCRIPTION.path, default=None),
    }

    def try_collection(hit) -> Optional[MissingMaterials]:
        try:
            kwargs = glom(hit.to_dict(), missing_attributes_spec)
            description = kwargs.pop("description")
            title = kwargs.pop("title")
            return MissingMaterials(
                node_id=uuid.UUID(hit["nodeRef"]["id"]),
                type="ccm:map",
                name="<irrelevant>",
                children=[],
                path=["<unused>"],
                parent_id=None,
                description=description if description is not None and description.strip() != "" else None,
                title=title or "",
                **kwargs,
            )
        except Exception as e:
            logger.warning(
                f"Failed to instantiate CollectionNode object from elastic search hit: {e}, hit:{hit.to_dict()}"
            )

    return [node for hit in response.hits if (node := try_collection(hit)) is not None]

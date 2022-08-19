import uuid
from typing import Optional

from fastapi import HTTPException
from fastapi.params import Path, Query
from glom import Coalesce, Iter, glom
from pydantic import BaseModel

from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.logging import logger
from app.core.models import ElasticResourceAttribute
from app.elastic.dsl import ElasticField
from app.elastic.search import MaterialSearch


class LearningMaterial(BaseModel):
    # fixme: remove type attribute because pointless. Will always be ccm:io.
    # fixme: remove name attribute because pointless. It is only a technical name
    #        (e.g. filename inside ES) and has no relevance for end users or metadata quality.
    # fixme: licenses should be a list[str], as it seems materials can have multiple licenses.
    node_id: uuid.UUID
    type: Optional[str]
    name: Optional[str]
    title: Optional[str]
    keywords: Optional[list[str]]
    edu_context: Optional[list[str]]
    subjects: Optional[list[str]]
    www_url: Optional[str]
    description: Optional[str]
    licenses: Optional[str]


def material_response_fields(
    *, response_fields: set[ElasticResourceAttribute] = Query(None)
) -> set[ElasticResourceAttribute]:
    return response_fields


missing_attributes_source_fields = {
    ElasticResourceAttribute.TITLE,
    ElasticResourceAttribute.LEARNINGRESOURCE_TYPE,
    ElasticResourceAttribute.SUBJECTS,
    ElasticResourceAttribute.WWW_URL,
    ElasticResourceAttribute.LICENSES,
    ElasticResourceAttribute.PUBLISHER,
    ElasticResourceAttribute.DESCRIPTION,
    ElasticResourceAttribute.EDU_ENDUSERROLE_DE,
    ElasticResourceAttribute.EDU_CONTEXT,
    ElasticResourceAttribute.COVER,
    ElasticResourceAttribute.NODE_ID,
    ElasticResourceAttribute.NAME,
    ElasticResourceAttribute.TYPE,
    ElasticResourceAttribute.KEYWORDS,
}

MissingMaterialField = ElasticField(
    "MissingMaterialField",
    [(f.name, (f.value, f.field_type)) for f in missing_attributes_source_fields],
)


class MissingAttributeFilter(BaseModel):
    attr: MissingMaterialField


def materials_filter_params(*, missing_attr: MissingMaterialField = Path(...)) -> MissingAttributeFilter:
    return MissingAttributeFilter(attr=missing_attr)


async def search_materials_with_missing_attributes(
    collection_id: uuid.UUID,
    missing: ElasticResourceAttribute,
) -> list[LearningMaterial]:

    source = [
        ElasticResourceAttribute.NODE_ID,
        ElasticResourceAttribute.TITLE,
        ElasticResourceAttribute.KEYWORDS,
        ElasticResourceAttribute.EDU_CONTEXT,
        ElasticResourceAttribute.SUBJECTS,
        ElasticResourceAttribute.WWW_URL,
        ElasticResourceAttribute.DESCRIPTION,
        ElasticResourceAttribute.LICENSES,
        # fixme: eventually we may want ot extend the LearningMaterial
        #        model to include the following three?
        # ElasticResourceAttribute.LEARNINGRESOURCE_TYPE,
        # ElasticResourceAttribute.PUBLISHER,
        # ElasticResourceAttribute.EDU_ENDUSERROLE_DE,
    ]

    search = (
        MaterialSearch()
        .collection_filter(collection_id=collection_id, transitive=True)
        .non_series_objects_filter()
        .missing_attribute_filter(missing=missing)
        .source(includes=[attr.path for attr in source])
        .extra(size=ELASTIC_TOTAL_SIZE, from_=0)
    )

    response = search.execute()
    if not response.success():
        raise HTTPException(status_code=502, detail="Failed to query elasticsearch")

    missing_materials_spec = {
        "title": Coalesce(ElasticResourceAttribute.TITLE.path, default=None),
        "keywords": (
            Coalesce(ElasticResourceAttribute.KEYWORDS.path, default=[]),
            Iter().all(),
        ),
        "edu_context": (
            Coalesce(ElasticResourceAttribute.EDU_CONTEXT.path, default=[]),
            Iter().all(),
        ),
        "subjects": (
            Coalesce(ElasticResourceAttribute.SUBJECTS.path, default=[]),
            Iter().all(),
        ),
        "www_url": Coalesce(ElasticResourceAttribute.WWW_URL.path, default=None),
        # for whatever reason some materials in elasticsearch have a list of strings as description...
        "description": (
            Coalesce(ElasticResourceAttribute.DESCRIPTION.path, default=[]),
            (Iter().all(), "\n".join),
        ),
        # it seems the data model for licenses in elasticsearch is a list of strings, however
        # our data model here expects only a single string, hence concatenate with "\n".join...
        "licenses": (
            Coalesce(ElasticResourceAttribute.LICENSES.path, default=[]),
            (Iter().all(), "\n".join),
        ),
    }

    def try_material(hit) -> Optional[LearningMaterial]:
        try:
            kwargs = glom(hit.to_dict(), missing_materials_spec)
            licenses: str = kwargs.pop("licenses")
            description: str = kwargs.pop("description")
            return LearningMaterial(
                # make sure node id is a UUID
                node_id=uuid.UUID(hit["nodeRef"]["id"]),
                type="ccm:io",
                name="<irrelevant>",
                description=description if len(description.strip()) > 0 else None,
                licenses=licenses if len(licenses.strip()) > 0 else None,
                **kwargs,
            )
        except Exception as e:
            logger.warning(f"Failed to instantiate LearningMaterial from search hit: {e}. hit: {hit.to_dict()}")
            return None

    return [material for hit in response if (material := try_material(hit)) is not None]

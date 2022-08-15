import pprint
import uuid
from typing import Optional

from elasticsearch_dsl import Q
from elasticsearch_dsl.query import Wildcard, Term
from fastapi.params import Path, Query
from glom import Coalesce, Iter
from pydantic import BaseModel, Extra
from pydantic.validators import str_validator

from app.api.collections.utils import map_elastic_response_to_model
from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.models import ElasticResourceAttribute, ResponseModel
from app.elastic.dsl import ElasticField
from app.elastic.elastic import ResourceType, query_missing_material_license
from app.elastic.search import Search


def empty_to_none(v: str) -> Optional[str]:
    if v == "":
        return None
    return v


class EmptyStrToNone(str):
    @classmethod
    def __get_validators__(cls):
        yield str_validator
        yield empty_to_none


class ElasticConfig:
    allow_population_by_field_name = True
    extra = Extra.allow


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
    "description": (
        Coalesce(ElasticResourceAttribute.DESCRIPTION.path, default=[]),
        (Iter().all(), "\n".join),
    ),
    "licenses": (
        Coalesce(ElasticResourceAttribute.LICENSES.path, default=[]),
        (Iter().all(), "\n".join),
    ),
    "node_id": ElasticResourceAttribute.NODE_ID.path,
    "type": Coalesce(ElasticResourceAttribute.TYPE.path, default=None),
    "name": Coalesce(ElasticResourceAttribute.NAME.path, default=None),
}


class LearningMaterial(ResponseModel):
    node_id: uuid.UUID
    type: Optional[EmptyStrToNone] = None
    name: Optional[EmptyStrToNone] = None
    title: Optional[EmptyStrToNone] = None
    keywords: Optional[list[str]] = None
    edu_context: Optional[list[str]] = None
    subjects: Optional[list[str]] = None
    www_url: Optional[str] = None
    description: Optional[EmptyStrToNone] = None
    licenses: Optional[EmptyStrToNone] = None

    class Config(ElasticConfig):
        pass


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


def materials_filter_params(
    *, missing_attr: MissingMaterialField = Path(...)
) -> MissingAttributeFilter:
    return MissingAttributeFilter(attr=missing_attr)


def missing_attributes_search(node_id: uuid.UUID, missing_attribute: str) -> Search:
    """
    Chemie:
     = Material X
     - Organisch
       = Material Y
     - Anorganisch

                    1.           2.
    Chemie:         3            1
     - Organisch    0            1
     - Anorganisch  0            0
    Gesamt :        3            2
                    35            24
    1. Pending-Materials
    2. Collection Details Table


    node_id = 123
    welche collection hat diese id?
    bzw. welche collection beinhaltet in ihrem Pfad diese Id, ist also eine child node


    My assumption: A material has some path attribute that is [category-root, chemie, anorganic-chemie, alkene]
            path
    Mat 1: [root, chemie]
    ...
    Mat 35: [root, chemie]

    Mat 36: [root, chemie, anorganic]
    ...
    Mat 100: [root, chemie, anorganic]

    query chemie: 35
    query anorganic-chemie: potenziell mehr als 35 -> why?
    """
    search = base_missing_material_search(node_id)
    search = search.source(includes=[source.path for source in missing_attributes_source_fields])

    if missing_attribute == ElasticResourceAttribute.LICENSES.path:
        search = search.filter(query_missing_material_license().to_dict())
        # pprint.pprint(search.to_dict(), indent=2, width=140)
        return search
    # ~ corresponds to inversion here, i.e., Wildcard must not be true
    search = search.filter(~Wildcard(**{missing_attribute: {"value": "*"}}))
    # pprint.pprint(search.to_dict(),indent=2, width=140)
    return search


def base_missing_material_search(node_id: uuid.UUID, transitive: bool = True) -> Search:
    """
    Build a search for materials that are in given collection and have missing attributes.

    :param node_id: The toplevel collection that identifies a collection subtree.
    :param transitive:
        True: The material is allowed to be in the collection or any of its children.
        False: The material must be directly in the specified collection.
    :return: A search for materials.
    """
    # make the dict returned from search.to_dict() json serializable...
    node_id = str(node_id)
    if transitive:
        query = Q(
            "bool",
            **{
                "minimum_should_match": 1,
                "should": [
                    Q(
                        "match",
                        **{
                            ElasticResourceAttribute.COLLECTION_PATH.keyword: node_id
                        }
                    ),
                    Q(
                        "match",
                        **{
                            ElasticResourceAttribute.COLLECTION_NODEREF_ID.keyword: node_id
                        }
                    ),
                ],
            }
        )
    else:
        query = Term(**{ElasticResourceAttribute.COLLECTION_NODEREF_ID.keyword: node_id})
    return (
        Search()
        .base_filters()
        .query(query)
        .type_filter(ResourceType.MATERIAL)
        .non_series_objects_filter()
        .extra(size=ELASTIC_TOTAL_SIZE, from_=0)
    )


async def search_materials_with_missing_attributes(
    node_id: Optional[uuid.UUID] = None,
    missing_attr_filter: Optional[MissingAttributeFilter] = None,
) -> list[LearningMaterial]:
    search = missing_attributes_search(node_id, missing_attr_filter.attr.value)
    # print("missing materials: ", search.to_dict())
    response = search.execute()
    if response.success():
        return map_elastic_response_to_model(
            response, missing_materials_spec, LearningMaterial
        )

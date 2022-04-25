from typing import Dict, List, Optional, Set
from uuid import UUID

from elasticsearch_dsl.response import Response
from pydantic import BaseModel

from app.core.config import ELASTIC_MAX_SIZE, PORTAL_ROOT_ID
from app.elastic import Field, Search, abucketsort, qbool, qwildcard
from app.models.collection import Collection, CollectionAttribute
from app.models.elastic import (
    DescendantCollectionsMaterialsCounts,
    ElasticResourceAttribute,
)
from app.models.learning_material import LearningMaterial, LearningMaterialAttribute

from .elastic import (
    ResourceType,
    agg_materials_by_collection,
    get_many_base_query,
    query_collections,
    query_materials,
)
from .learning_material import MissingAttributeFilter as MissingMaterialAttributeFilter
from .learning_material import get_many as get_many_materials

PORTALS = {
    # "Physik": {"value": "unknown"},
    "Mathematik": {"value": "bd8be6d5-0fbe-4534-a4b3-773154ba6abc"},
    "Biologie": {"value": "15fce411-54d9-467f-8f35-61ea374a298d"},
    "Chemie": {"value": "4940d5da-9b21-4ec0-8824-d16e0409e629"},
    "Deutsch": {"value": "69f9ff64-93da-4d68-b849-ebdf9fbdcc77"},
    "DaZ": {"value": "26a336bf-51c8-4b91-9a6c-f1cf67fd4ae4"},
    "Englisch": {"value": "15dbd166-fd31-4e01-aabd-524cfa4d2783"},
    "Informatik": {"value": "742d8c87-e5a3-4658-86f9-419c2cea6574"},
    "Kunst": {"value": "6a3f5881-cce0-4e8d-b123-26392b3f1c19"},
    "Religion": {"value": "66c667bc-8777-4c57-b476-35f54ce9ff5d"},
    "Geschichte": {"value": "324f24e3-6687-4e89-b8dd-2bd0e20ff733"},
    "Medienbildung": {"value": "eef047a3-58ba-419c-ab7d-3d0cfd04bb4e"},
    "Politische Bildung": {"value": "ffd298b5-3a04-4d13-9d26-ddd5d3b5cedc"},
    "Sport": {"value": "ea776a48-b3f4-446c-b871-19f84b31d280"},
    "Darstellendes Spiel": {"value": "7998f334-9311-491e-9a58-72baf2a7efd2"},
    "Spanisch": {"value": "11bdb8a0-a9f5-4028-becc-cbf8e328dd4b"},
    "Tuerkisch": {"value": "26105802-9039-4add-bf21-07a0f89f6e70"},
    "Nachhaltigkeit": {"value": "d0ed50e6-a49f-4566-8f3b-c545cdf75067"},
    "OER": {"value": "a87c092d-e3b5-43ef-81db-757ab1967646"},
    "Zeitgemaesse Bildung": {"value": "a3291cd2-5fe4-444e-9b7b-65807d9b0024"},
    "Wirtschaft": {"value": "f0109e16-a8fc-48b5-9461-369571fd59f2"},
    "Geografie": {"value": "f1049950-bdda-45f5-9c73-38b51ea66c74"},
    "Paedagogik": {"value": "7e2a3536-8441-4328-8ee6-ab0068bb13f8"},
    "Franzoesisch": {"value": "86b990ef-0955-45ad-bdae-ec2623cf0e1a"},
    "Musik": {"value": "2eda0065-f69b-46c8-ae09-d258c8226a5e"},
    "Philosophie": {"value": "9d364fd0-4374-40b4-a153-3c722b9cda35"},
}

MissingCollectionField = Field(
    "MissingCollectionField",
    [
        (f.name, (f.value, f.field_type))
        for f in [
            CollectionAttribute.NAME,
            CollectionAttribute.TITLE,
            CollectionAttribute.KEYWORDS,
            CollectionAttribute.DESCRIPTION,
        ]
    ],
)


class MissingAttributeFilter(BaseModel):
    attr: MissingCollectionField

    def __call__(self, query_dict: dict):
        query_dict["must_not"] = qwildcard(qfield=self.attr, value="*")
        return query_dict


def portals_query() -> Search:
    return Search().query(query_collections(ancestor_id=PORTAL_ROOT_ID))


def processed_portals_query(response: Response) -> dict:
    collections = [Collection.parse_elastic_hit(hit) for hit in response]
    return {c.noderef_id: c.title for c in collections if c.parent_id == PORTAL_ROOT_ID}


async def get_portals() -> Optional[dict]:
    s = portals_query()

    response: Response = s.source(
        [
            ElasticResourceAttribute.NODEREF_ID,
            CollectionAttribute.TITLE,
            CollectionAttribute.PATH,
            CollectionAttribute.PARENT_ID,
        ]
    )[:ELASTIC_MAX_SIZE].execute()

    if response.success():
        return processed_portals_query(response)


async def get_single(noderef_id: UUID) -> Collection:
    return Collection(noderef_id=noderef_id)


async def get_many(
    ancestor_id: Optional[UUID] = None,
    missing_attr_filter: Optional[MissingAttributeFilter] = None,
    max_hits: Optional[int] = ELASTIC_MAX_SIZE,
    source_fields: Optional[Set[CollectionAttribute]] = None,
) -> List[Collection]:
    # TOOD: Refactor duplicate code
    query_dict = get_many_base_query(
        resource_type=ResourceType.COLLECTION,
        ancestor_id=ancestor_id,
    )
    if missing_attr_filter:
        query_dict = missing_attr_filter.__call__(query_dict=query_dict)
    s = Search().query(qbool(**query_dict))

    response = s.source(source_fields if source_fields else Collection.source_fields)[
        :max_hits
    ].execute()

    if response.success():
        return [Collection.parse_elastic_hit(hit) for hit in response]


def many_sorted_query(root_noderef_id: UUID) -> Search:
    return Search().query(query_collections(root_noderef_id))


async def get_many_sorted(
    root_noderef_id: UUID = PORTAL_ROOT_ID, size: int = ELASTIC_MAX_SIZE
) -> List[Collection]:
    s = many_sorted_query(root_noderef_id)

    response: Response = (
        s.source(
            [
                ElasticResourceAttribute.NODEREF_ID,
                CollectionAttribute.TITLE,
                CollectionAttribute.PATH,
                CollectionAttribute.PARENT_ID,
            ]
        )
        .sort(CollectionAttribute.FULLPATH)[:size]
        .execute()
    )

    if response.success():
        return [Collection.parse_elastic_hit(hit) for hit in response]


# TODO: move to learning_material crud
async def get_child_materials_with_missing_attributes(
    noderef_id: UUID,
    missing_attr_filter: MissingMaterialAttributeFilter,
    source_fields: Optional[Set[LearningMaterialAttribute]],
    max_hits: Optional[int] = ELASTIC_MAX_SIZE,
) -> List[LearningMaterial]:
    return await get_many_materials(
        ancestor_id=noderef_id,
        missing_attr_filter=missing_attr_filter,
        source_fields=source_fields,
        max_hits=max_hits,
    )


# TODO: eliminate
async def get_child_collections_with_missing_attributes(
    noderef_id: UUID,
    missing_attr_filter: MissingAttributeFilter,
    source_fields: Optional[Set[CollectionAttribute]],
    max_hits: Optional[int] = ELASTIC_MAX_SIZE,
) -> List[Collection]:
    return await get_many(
        ancestor_id=noderef_id,
        missing_attr_filter=missing_attr_filter,
        source_fields=source_fields,
        max_hits=max_hits,
    )


def material_counts_search(ancestor_id) -> Search:
    search = Search().query(query_materials(ancestor_id=ancestor_id))
    search.aggs.bucket("grouped_by_collection", agg_materials_by_collection()).pipeline(
        "sorted_by_count",
        abucketsort(sort=[{"_count": {"order": "asc"}}]),
    )
    return search


async def material_counts_by_descendant(
    ancestor_id: UUID,
) -> DescendantCollectionsMaterialsCounts:
    s = material_counts_search(ancestor_id)

    response: Response = s[:0].execute()

    if response.success():
        return DescendantCollectionsMaterialsCounts.parse_elastic_response(response)

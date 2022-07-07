import datetime
import uuid
from dataclasses import dataclass
from typing import Union
from uuid import UUID

from elasticsearch_dsl.aggs import Agg
from elasticsearch_dsl.query import Q, Query
from elasticsearch_dsl.response import AggResponse, Response
from glom import merge

from app.api.analytics.analytics import (
    COUNT_STATISTICS_TYPE,
    CollectionValidationStats,
    MaterialValidationStats,
    StatsNotFoundException,
    StatsResponse,
    StatType,
    ValidationStatsResponse,
)
from app.api.analytics.models import Collection
from app.api.analytics.storage import (
    _COLLECTION_COUNT,
    _COLLECTIONS,
    _MATERIALS,
    global_storage,
)
from app.api.collections.descendants import aterms
from app.api.collections.missing_materials import base_filter
from app.api.collections.models import CollectionNode
from app.api.collections.tree import collection_tree
from app.api.score.models import (
    LearningMaterialAttribute,
    required_collection_properties,
)
from app.core.config import ELASTIC_TOTAL_SIZE
from app.elastic.dsl import qbool, qterm
from app.elastic.elastic import ResourceType, type_filter
from app.elastic.fields import ElasticField
from app.elastic.search import Search
from app.models import CollectionAttribute


def qsimplequerystring(
    query: str, qfields: list[Union[ElasticField, str]], **kwargs
) -> Query:
    kwargs["query"] = query
    kwargs["fields"] = [
        (qfield.path if isinstance(qfield, ElasticField) else qfield)
        for qfield in qfields
    ]
    return Q("simple_query_string", **kwargs)


def search_materials(query_str: str) -> Query:
    return qsimplequerystring(
        query=query_str,
        qfields=[
            LearningMaterialAttribute.TITLE,
            LearningMaterialAttribute.KEYWORDS,
            LearningMaterialAttribute.DESCRIPTION,
            LearningMaterialAttribute.CONTENT_FULLTEXT,
            LearningMaterialAttribute.SUBJECTS_DE,
            LearningMaterialAttribute.LEARNINGRESOURCE_TYPE_DE,
            LearningMaterialAttribute.EDU_CONTEXT_DE,
            LearningMaterialAttribute.EDUENDUSERROLE_DE,
        ],
        default_operator="and",
    )


def query_many(resource_type: ResourceType, ancestor_id: UUID = None) -> Query:
    qfilter = [*base_filter, *type_filter[resource_type]]
    if ancestor_id:
        if resource_type is ResourceType.COLLECTION:
            qfilter.append(qterm(qfield=CollectionAttribute.PATH, value=ancestor_id))
        elif resource_type is ResourceType.MATERIAL:
            qfilter.append(
                qterm(
                    qfield=LearningMaterialAttribute.COLLECTION_PATH, value=ancestor_id
                )
            )

    return qbool(filter=qfilter)


def query_materials(ancestor_id: UUID = None) -> Query:
    return query_many(ResourceType.MATERIAL, ancestor_id=ancestor_id)


def agg_material_types(size: int = ELASTIC_TOTAL_SIZE) -> Agg:
    # TODO: This is the key property we are aggregating for
    return aterms(
        qfield=LearningMaterialAttribute.LEARNINGRESOURCE_TYPE,
        missing="N/A",
        size=size,
    )


def merge_agg_response(
    agg: AggResponse, key: str = "key", result_field: str = "doc_count"
) -> dict:
    def op(carry: dict, bucket: dict):
        carry[bucket[key]] = bucket[result_field]

    return merge(agg.buckets, op=op)


def search_hits_by_material_type(collection_title: str) -> dict:
    """Title used here to shotgun search for any matches with the title of the material"""
    s = build_material_search(collection_title)
    response: Response = s[:0].execute()

    if response.success():
        # TODO: Clear and cleanu p: what does this do?
        stats = merge_agg_response(response.aggregations.material_types)
        stats["total"] = sum(stats.values())
        return stats


def build_material_search(query_string: str):
    s = Search().query(query_materials()).query(search_materials(query_string))
    s.aggs.bucket("material_types", agg_material_types())
    return s


@dataclass
class Row:
    id: uuid.UUID
    title: str


async def get_ids_to_iterate(node_id: UUID):
    """
    Contains the collection id's to iterate over.

    Hardcoded for now including multiple inefficient data transformations, e.g., from list to tree back to list
    :return:
    """

    def flatten_list(list_of_lists):
        flat_list = []
        for item in list_of_lists:
            if type(item) == list:
                flat_list += flatten_list(item)
            else:
                flat_list.append(item)

        return flat_list

    def nodes(data: list[CollectionNode]) -> list:
        return [
            nodes(collection.children)
            if collection.children
            else (collection.noderef_id, collection.title)
            for collection in data
        ]

    tree = await collection_tree(node_id)
    return [Row(id=row[0], title=row[1]) for row in flatten_list(nodes(tree))]


def query_material_types(node_id: UUID) -> dict[str, COUNT_STATISTICS_TYPE]:
    """
    get collections with parent id equal to node_id

    portal_id == node_id
    """
    collections = global_storage[_COLLECTIONS]
    collections = filtered_collections(collections, node_id)

    """
    collection id - learning_resource_type - counts
    Join filtered collections and filtered counts into one, now
    """
    stats = {}

    counts = global_storage[_COLLECTION_COUNT]

    # TODO: Refactor with filter and dict comprehension
    for collection in collections:
        for count in counts:
            if str(collection.id) == str(count.noderef_id):
                stats.update(
                    {str(collection.id): {"total": count.total, **count.counts}}
                )
    return stats


def filtered_collections(collections: list[Collection], node_id: uuid.UUID):
    return [
        collection
        for collection in collections
        if str(node_id) in collection.doc["path"]
    ]


async def stats_latest(
    stat_type: StatType, node_id: UUID
) -> dict[str, COUNT_STATISTICS_TYPE]:
    results = {}

    if stat_type is StatType.SEARCH:
        all_collection_nodes = await get_ids_to_iterate(node_id)
        for row in all_collection_nodes:
            stats = search_hits_by_material_type(row.title)
            results.update({str(row.id): stats})
    elif stat_type is StatType.MATERIAL_TYPES:
        results = query_material_types(node_id)
    return results


async def overall_stats(node_id) -> StatsResponse:
    search_stats = await stats_latest(stat_type=StatType.SEARCH, node_id=node_id)

    if not search_stats:
        raise StatsNotFoundException

    material_types_stats = await stats_latest(
        stat_type=StatType.MATERIAL_TYPES, node_id=node_id
    )

    if not material_types_stats:
        raise StatsNotFoundException

    stats_output = {key: {"search": value} for key, value in search_stats.items()}

    for key, value in material_types_stats.items():
        if key in stats_output.keys():
            stats_output[key].update({"material_types": value})
        else:
            stats_output.update({key: {"material_types": value}})

    output = StatsResponse(derived_at=datetime.datetime.now(), stats=stats_output)
    return output


def collections_with_missing_properties(
    node_id: uuid.UUID,
) -> list[ValidationStatsResponse[CollectionValidationStats]]:
    """
    Check whether any of the following are missing:
    title, description, keywords, license, taxon_id, edu_context, learning_resource_type, ads_qualifier, object_type

    """

    collections = global_storage[_COLLECTIONS]
    collections = filtered_collections(collections, node_id)

    missing_properties = {}
    for collection in collections:
        missing_properties.update({collection.id: {}})
        for entry in required_collection_properties.keys():
            value = {required_collection_properties[entry]: ["missing"]}
            if (
                "properties" not in collection.doc.keys()
                or entry.split(".")[-1] not in collection.doc["properties"].keys()
            ):
                missing_properties[collection.id].update(value)

    if not missing_properties:
        raise StatsNotFoundException

    return [
        ValidationStatsResponse[CollectionValidationStats](
            noderef_id=uuid.UUID(key),
            validation_stats=CollectionValidationStats(**value),
        )
        for key, value in missing_properties.items()
    ]


def materials_with_missing_properties(
    node_id,
) -> list[ValidationStatsResponse[MaterialValidationStats]]:
    """
    Returns the number of materials missing certain properties for this collection node_id and its sub collections

    Similar to collections_with_missing_properties, but counting the underlying materials missing that property

    :param node_id:
    :return:
    """

    collections: list[Collection] = global_storage[_COLLECTIONS]
    collections = filtered_collections(collections, node_id)

    materials: list[Collection] = global_storage[_MATERIALS]
    # find materials belonging to each collection
    # check whether they are missing the required properties
    # if so, add them as a list to validation stats
    # materials = filtered_collections(collections, node_id)
    missing_properties = {}
    for collection in collections:
        missing_properties.update({collection.id: {}})
        for material in materials:
            if material.doc["collections"][0]["nodeRef"]["id"] == collection.id:
                # check if property is present
                # if not, add the respective material id to the "missing" field of this property
                for entry in required_collection_properties.keys():
                    if (
                        "properties" not in material.doc.keys()
                        or entry.split(".")[-1] not in material.doc["properties"].keys()
                    ):
                        entry_key = required_collection_properties[entry]
                        if entry_key not in missing_properties[collection.id].keys():
                            missing_properties[collection.id].update(
                                {entry_key: {"missing": []}}
                            )

                        missing_properties[collection.id][entry_key]["missing"].append(
                            material.id
                        )

    if not missing_properties:
        raise StatsNotFoundException

    return [
        ValidationStatsResponse[MaterialValidationStats](
            noderef_id=uuid.UUID(key),
            validation_stats=MaterialValidationStats(**value),
        )
        for key, value in missing_properties.items()
    ]

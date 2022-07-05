import datetime
import uuid
from collections import defaultdict
from dataclasses import dataclass
from typing import Union
from uuid import UUID

from elasticsearch_dsl.aggs import Agg
from elasticsearch_dsl.query import Q, Query
from elasticsearch_dsl.response import AggResponse, Response
from glom import merge

from app.api.analytics.analytics import StatsNotFoundException, StatsResponse, StatType
from app.api.analytics.storage import _COLLECTION_COUNT, _COLLECTIONS, global_storage
from app.api.collections.descendants import aterms
from app.api.collections.missing_materials import base_filter
from app.api.collections.models import CollectionNode
from app.api.collections.tree import collection_tree
from app.api.score.models import LearningMaterialAttribute
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


def search_hits_by_material_type(query_string: str) -> dict:
    s = build_material_search(query_string)
    response: Response = s[:0].execute()

    if response.success():
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


def query_material_types(node_id: UUID) -> list[StatsResponse]:
    """
    get collections with parent id equal to node_id

    portal_id == node_id
    """
    collections = global_storage[_COLLECTIONS]
    filtered_collections = [
        collection
        for collection in collections
        if str(node_id) in collection.doc["path"]
    ]

    """
    collection id - learning_resource_type - counts
    Join filtered collections and filtered counts into one, now
    """
    stats = []

    counts = global_storage[_COLLECTION_COUNT]
    for collection in filtered_collections:
        for count in counts:
            if str(collection.id) == str(count.noderef_id):
                stats_value = {
                    str(collection.id): {
                        "material_types": {"total": count.total, **count.counts}
                    }
                }
                stats.append(
                    StatsResponse(derived_at=datetime.datetime.now(), stats=stats_value)
                )

    return stats


async def stats_latest(stat_type: StatType, node_id: UUID) -> list[StatsResponse]:
    results = []
    all_collection_nodes = await get_ids_to_iterate(node_id)

    if stat_type is StatType.SEARCH:
        for i, row in enumerate(all_collection_nodes):
            # TODO: What is the title? What is it used for?
            stats = search_hits_by_material_type(row.title)
            print("Search stats:", stats)
            stats_value = {str(row.id): {"search": stats}}
            results.append(
                StatsResponse(derived_at=datetime.datetime.now(), stats=stats_value)
            )
    elif stat_type is StatType.MATERIAL_TYPES:
        results = query_material_types(node_id)
    return results


async def overall_stats(node_id):
    search_stats = await stats_latest(stat_type=StatType.SEARCH, node_id=node_id)

    if not search_stats:
        raise StatsNotFoundException

    material_types_stats = await stats_latest(
        stat_type=StatType.MATERIAL_TYPES, node_id=node_id
    )

    if not material_types_stats:
        raise StatsNotFoundException

    stats = defaultdict(dict)
    # TODO: Howto deep merge these two dictionaries? Basically, materials overwrites search
    seen_ids = []
    for stat in search_stats + material_types_stats:
        # stats[str(stat["collection_id"])]["search"] = stat["stats"]
        print(stat.stats.keys())
        seen_ids.append(list(stat.stats.keys()))
        stats.update(**stat.stats)
    # for stat in material_types_stats:
    #     stats.update(**stat.stats)
    print(seen_ids)
    return stats

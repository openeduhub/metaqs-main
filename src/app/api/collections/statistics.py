import datetime
import uuid
from uuid import UUID

from elasticsearch_dsl.query import SimpleQueryString, Query
from elasticsearch_dsl.response import Response
from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.api.collections.tree import tree, Tree
from app.api.collections.utils import oer_ratio
from app.elastic.attributes import ElasticResourceAttribute, ElasticField
from app.elastic.search import MaterialSearch


CountStatistics = dict[str, int]


class SearchAndTotalStats(BaseModel):
    search: CountStatistics
    material_types: CountStatistics


class Statistics(BaseModel):
    """
    In principle this class is a four-dimensional array with the dimension:
     # - collection (node_id, the most outer dictionary keys)
     - "search|material_types" (mid level dictionary keys)
     - content type (Picture, Video, ..., lowest level keys, within CountStatistics)
     - total_stats vs oer_stats

     # fixme: I assume the second level should be search|collection. I.e. an indicator how many materials are in the
              collection and how many of those are available in the search?!? Then we should rename it to
              "total|searchable"?
     # fixme: having the total as part of the dictionary seems like a really bad idea :-/ We should create an extra
              field for it somehow.
     Sample:
     {
    "derived_at": "2022-08-22T14:47:21.542369",
    "total_stats": {
        "9f082eef-2f86-4007-bbf0-45690cec45a4": {
            "search": {
                "http://w3id.org/openeduhub/vocabs/new_lrt/5098cf0b-1c12-4a1b-a6d3-b3f29621e11d": 23,
                ...
                "http://w3id.org/openeduhub/vocabs/new_lrt/7a6e9608-2554-4981-95dc-47ab9ba924de": 4,
                "N/A": 2,
                "http://w3id.org/openeduhub/vocabs/new_lrt/3869b453-d3c1-4b34-8f25-9127e9d68766": 2,
                ...
                "http://w3id.org/openeduhub/vocabs/new_lrt/22823ca9-7175-4b24-892e-19ebbf5fe0e7": 1,
                "total": 110,
            },
            "material_types": {
                "total": 15,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/f1341358-3f91-449b-b6eb-f58636f756a0": 7,
                ...
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/ded96854-280a-45ac-ad3a-f5b9b8dd0a03": 1,
            },
        },
        "395864a0-732d-434e-b6d1-c6a865bfb651": {
            "search": {
                "http://w3id.org/openeduhub/vocabs/new_lrt/a0218a48-a008-4975-a62a-27b1a83d454f": 5,
                "http://w3id.org/openeduhub/vocabs/new_lrt/ef58097d-c1de-4e6a-b4da-6f10e3716d3d": 3,
                "http://w3id.org/openeduhub/vocabs/new_lrt/36e68792-6159-481d-a97b-2c00901f4f78": 1,
                "total": 9,
            },
            "material_types": {
                "total": 40,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/38774279-af36-4ec2-8e70-811d5a51a6a1": 26,
                ...
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/b8fb5fb2-d8bf-4bbe-ab68-358b65a26bed": 1,
            },
     "oer_stats": {
        "9f082eef-2f86-4007-bbf0-45690cec45a4": {
            "search": {
                "http://w3id.org/openeduhub/vocabs/new_lrt/36e68792-6159-481d-a97b-2c00901f4f78": 14,
                 ...
                "http://w3id.org/openeduhub/vocabs/new_lrt/ef58097d-c1de-4e6a-b4da-6f10e3716d3d": 5,
                "N/A": 2,
                "http://w3id.org/openeduhub/vocabs/new_lrt/9cf3c183-f37c-4b6b-8beb-65f530595dff": 2,
                "total": 53,
            },
            "material_types": {
                "total": 9,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/8526273b-2b21-46f2-ac8d-bbf362c8a690": 4,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/38774279-af36-4ec2-8e70-811d5a51a6a1": 3,
                ...
            }
        }
     }
    """

    derived_at: datetime.datetime
    total_stats: dict[uuid.UUID, SearchAndTotalStats]  # node_id: search/material_types: UUID of the material
    oer_stats: dict[uuid.UUID, SearchAndTotalStats]  # node_id: search/material_types: UUID of the material
    oer_ratio: int = Field(default=0)


def materials_by_collection_title(nodes: list[Tree], oer_only: bool) -> dict[UUID, CountStatistics]:
    """
    Fuzzy-Search for materials that have description, title, etc. similar to the titles of given collection nodes.

    This function builds and executes a composed aggregate query which for every collection node does a subaggregation,
    where the number of materials that match the collection title is counted and aggregated into buckets matching the
    material type.

    :return: A dictionary mapping from the collection IDs to counts per material type.
    """

    if oer_only:
        search = MaterialSearch().oer_filter()
    else:
        search = MaterialSearch()

    fields = [
        ElasticResourceAttribute.TITLE,
        ElasticResourceAttribute.KEYWORDS,
        ElasticResourceAttribute.DESCRIPTION,
        ElasticResourceAttribute.CONTENT_FULLTEXT,
    ]

    def filter_subquery(node: Tree) -> Query:
        return SimpleQueryString(
            query=node.title,
            fields=[(field.path if isinstance(field, ElasticField) else field) for field in fields],
            default_operator="and",
        )

    search.aggs.bucket(
        "material_types_and_collection",
        {
            "filters": {"filters": {str(node.node_id): filter_subquery(node) for node in nodes}},
            "aggs": {
                "material_type": {"terms": {"field": "properties.ccm:oeh_lrt.keyword", "missing": "N/A", "size": 50000}}
            },
        },
    )
    response: Response = search.extra(size=0, from_=0).execute()

    if not response.success():
        raise HTTPException(status_code=502, detail="Failed to query elastic search")

    def unpack(aggregation) -> CountStatistics:
        """Unpack the material count statistics for a single collection id"""
        return {bucket["key"]: bucket["doc_count"] for bucket in aggregation["material_type"]["buckets"]}

    return {
        node.node_id: unpack(response.aggregations["material_types_and_collection"]["buckets"][str(node.node_id)])
        for node in nodes
    }


def materials_by_collection_id(collection_id: UUID, oer_only: bool) -> dict[UUID, CountStatistics]:
    """
    Query the number of materials per (collection_id, material_type) combination for all collections
    of given parent collection (including the parent).
    """
    if oer_only:
        search = MaterialSearch().oer_filter()
    else:
        search = MaterialSearch()

    # fmt: off
    search = (
        search
            .collection_filter(collection_id=collection_id, transitive=True)
            .extra(size=0, from_=0)
    )
    # fmt: on

    # Make this a multi_terms bucket and aggregate over combinations of material type and collection id.
    # Elasticsearch actually does the reasonable thing and counts documents into multiple buckets, it the
    # bucket defining fields are arrays (like here). I.e. if a document has 3 different material types and is
    # in three different collections, it will be counted nine times into the 9 different combinations of
    # (material type, collection)

    # need to define a MultiTerms aggregation type, as it is otherwise not yet supported by elasticsearch-dsl :-(
    from elasticsearch_dsl.aggs import Bucket
    class MultiTerms(Bucket):  # noqa
        name = "multi_terms"

    search.aggs.bucket(
        "material_type_and_collection",
        {
            "multi_terms": {
                "size": 50000,
                "terms": [
                    {"field": "properties.ccm:oeh_lrt.keyword", "missing": "N/A"},
                    {"field": "collections.nodeRef.id.keyword"},
                ],
            }
        },
    )

    response = search.execute()
    if not response.success():
        raise HTTPException(status_code=502, detail="Failed to query elastics search")

    result = {}

    for bucket in response.aggregations["material_type_and_collection"]["buckets"]:
        # unpack composite key in same order as the fields are defined in multi terms aggregation
        material_type, collection_id = bucket["key"]
        if UUID(collection_id) not in result:
            result[UUID(collection_id)] = CountStatistics()
        result[UUID(collection_id)][material_type] = bucket["doc_count"]

    return result


async def statistics(node_id: uuid.UUID) -> Statistics:
    """
    See API /collections/{node_id}/statistics doc-string.
    """
    nodes = {node.node_id: node for node in tree(node_id=node_id).flatten(root=True)}

    total_by_title = materials_by_collection_title(nodes=list(nodes.values()), oer_only=False)
    oer_by_title = materials_by_collection_title(nodes=list(nodes.values()), oer_only=True)

    total_by_collection = materials_by_collection_id(collection_id=node_id, oer_only=False)
    oer_by_collection = materials_by_collection_id(collection_id=node_id, oer_only=True)

    def transform(by_collection, by_title) -> dict[UUID, SearchAndTotalStats]:
        collection_ids = set(by_collection.keys()) | set(by_title.keys())

        def total(counts: CountStatistics) -> CountStatistics:
            """Add the 'total' dictionary entry to the final result"""
            counts["total"] = sum(counts.values())
            return counts

        return {
            collection_id: SearchAndTotalStats(
                search=total(by_title.get(collection_id, {})),
                material_types=total(by_collection.get(collection_id, {})),
            )
            for collection_id in collection_ids
        }

    return Statistics(
        derived_at=datetime.datetime.now(),
        total_stats=transform(total_by_collection, total_by_title),
        oer_stats=transform(oer_by_collection, oer_by_title),
        oer_ratio=oer_ratio(collection_id=node_id),
    )

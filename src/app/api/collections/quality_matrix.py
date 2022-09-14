import datetime
import uuid
from typing import Iterable, Literal, Optional, Iterator
from typing import Mapping

import sqlalchemy
from databases import Database
from elasticsearch_dsl import A
from fastapi import HTTPException
from fastapi_utils.tasks import repeat_every
from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column, Integer, Text
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

from app.api.collections.tree import Tree, tree
from app.core.constants import COLLECTION_NAME_TO_ID
from app.core.logging import logger
from app.core.meta_hierarchy import METADATA_HIERARCHY, load_metadataset
from app.elastic.attributes import ElasticResourceAttribute
from app.elastic.search import MaterialSearch

QualityMatrixMode = Literal["replication-source", "collection"]


class QualityMatrixHeader(BaseModel):
    id: str
    label: str
    alt_label: Optional[str]
    level: Optional[int]


class QualityMatrixRow(BaseModel):
    meta: QualityMatrixHeader = Field(description="The ")
    counts: dict[str, int] = Field(
        description="The number of materials in the respective cell. Keys are the IDs of the columns."
    )
    # columns: dict[str, float] = Field(description="The ratio of quality per column.")
    total: int = Field(description="The number of unique materials of the row")


class QualityMatrix(BaseModel):
    columns: list[QualityMatrixHeader] = Field(description="Defines the columns of the matrix")
    rows: list[QualityMatrixRow]


def _flat_hierarchy() -> Iterator[tuple[int, str, Optional[ElasticResourceAttribute]]]:
    for key, value in METADATA_HIERARCHY.items():
        yield 0, key, None
        for attribute, name in value:
            yield 1, name, attribute


# class QualityMatrix(BaseModel):
#     rows: list[QualityMatrixRow] = Field(description="Quality data per row")
#     totals: dict[str, int] = Field(description="Column names and total materials per column")


# def collection_quality_matrix(collection: Tree) -> QualityMatrix:
#     """
#     The collection quality matrix has the collections as rows and the attribute hierarchy as columns.
#     """
#     attributes = [attribute.path for _, _, attribute in flat_hierarchy() if attribute is not None]
#     search = MaterialSearch().collection_filter(collection_id=collection.node_id, transitive=True).extra(size=0)
#
#     search.aggs.bucket(
#         "collection",
#         A(
#             "terms",
#             field="collections.nodeRef.id.keyword",
#             size=10000,
#             aggs={attribute: {"missing": {"field": f"{attribute}.keyword"}} for attribute in attributes},
#         ),
#     )
#
#     response = search.execute()
#     if not response.success():
#         raise HTTPException(status_code=502, detail="Failed to run elastic search query.")
#
#     # transform the response aggregation which looks as follows into a nested dictionary which will allow to build the
#     # desired QualityMatrix response. Sample response:
#     # ...
#     #   "aggregations" : {
#     #     "collection" : {
#     #       "doc_count_error_upper_bound" : 0,
#     #       "sum_other_doc_count" : 0,
#     #           "buckets": [
#     #               {
#     #                   "key": "458ff124-ff34-4b70-9eed-b0efe8790717",
#     #                   "doc_count": 2314,
#     #                   "properties.ccm:oeh_quality_language": {
#     #                       "doc_count": 2314
#     #                   },
#     #                   "properties.ccm:oeh_quality_correctness": {
#     #                       "doc_count": 2314
#     #                   },
#     #                   "properties.ccm:educationaltypicalagerange": {
#     #                       "doc_count": 2314
#     #                   },
#     #                   ...
#     #                },
#     #                ...
#     #              ]
#     #         ...
#
#     CollectionID = uuid.UUID  # noqa
#     Attribute = str  # noqa
#
#     # initialize empty dictionaries
#     totals: dict[CollectionID, int] = {}
#     data: dict[CollectionID, dict[Attribute, int]] = {}
#
#     # loop over result and fill dictionaries
#     for bucket in response.aggregations["collection"]["buckets"]:
#         collection_id = uuid.UUID(bucket["key"])
#         totals[collection_id] = bucket["doc_count"]
#         data[collection_id] = {attribute: bucket[attribute]["doc_count"] for attribute in attributes}
#
#     def bft_with_level(node: Tree, level=0) -> Iterable[tuple[Tree, int]]:
#         yield node, level
#         for child in node.children:
#             yield from bft_with_level(child, level=level + 1)
#
#     # if there is a collection without any materials, then it will not show up in the aggregations and hence will not be
#     # contained in the totals and data dictionaries. For those collections we return 100%.
#     def percentage(node: Tree, attribute) -> float:
#         try:
#             return int(round(100 - 100 * data[node.node_id][attribute] / totals[node.node_id]))
#         except KeyError:
#             return 100
#
#     def try_count(node: Tree, attribute) -> int:
#         try:
#             return data[node.node_id][attribute]
#         except KeyError:
#             return 0
#
#     def last(attribute):
#         # strip the properties. or other prefixes from the attributes.
#         return attribute.split(".")[-1]
#
#     return QualityMatrix(
#         rows=[
#             QualityMatrixRow(
#                 header=node.title,
#                 alternative_header=str(node.node_id),
#                 level=level,
#                 columns={last(attribute): percentage(node, attribute) for attribute in attributes},
#                 counts={last(attribute): try_count(node, attribute) for attribute in attributes}
#                 if level == 2  # for the intermediate levels like "Beschreibendes", we don't have any data
#                 else {},
#                 total=totals.get(node.node_id, 0),
#             )
#             for node, level in bft_with_level(collection)
#         ],
#         totals={node.title: totals.get(node.node_id, 0) for node in collection.bft(root=True)},
#     )


def _quality_matrix_columns() -> list[QualityMatrixHeader]:
    caption_map = load_metadataset()
    return [
        QualityMatrixHeader(
            id=name,
            label=caption_map.get(attribute.path.split(".")[-1], attribute.path.split(".")[-1]) if level > 0 else name,
            alt_label=attribute.path.split(".")[-1] if level > 0 else None,
            level=level,
        )
        for level, name, attribute in _flat_hierarchy()
    ]


def collection_quality_matrix(collection: Tree) -> QualityMatrix:
    """
    The collection quality matrix has the collections as rows and the attribute hierarchy as columns.
    """
    search = MaterialSearch().collection_filter(collection_id=collection.node_id, transitive=True).extra(size=0)

    search.aggs.bucket(
        "collection",
        A(
            "terms",
            field="collections.nodeRef.id.keyword",
            size=10000,
            aggs={
                attribute.path: {"missing": {"field": attribute.keyword}}
                for _, name, attribute in _flat_hierarchy()
                if attribute is not None
            },
        ),
    )

    response = search.execute()
    if not response.success():
        raise HTTPException(status_code=502, detail="Failed to run elastic search query.")

    # transform the response aggregation which looks as follows into a nested dictionary which will allow to build the
    # desired QualityMatrix response. Sample response:
    # ...
    #   "aggregations" : {
    #     "collection" : {
    #       "doc_count_error_upper_bound" : 0,
    #       "sum_other_doc_count" : 0,
    #           "buckets": [
    #               {
    #                   "key": "458ff124-ff34-4b70-9eed-b0efe8790717",
    #                   "doc_count": 2314,
    #                   "oeh_quality_language": {
    #                       "doc_count": 2314
    #                   },
    #                   "oeh_quality_correctness": {
    #                       "doc_count": 2314
    #                   },
    #                   "educationaltypicalagerange": {
    #                       "doc_count": 2314
    #                   },
    #                   ...
    #                },
    #                ...
    #              ]
    #         ...

    CollectionID = uuid.UUID  # noqa
    Attribute = str  # noqa

    # initialize empty dictionaries
    data: dict[(CollectionID, Attribute), int] = {}
    totals: dict[CollectionID, int] = {}

    # loop over result and fill dictionaries
    for bucket in response.aggregations["collection"]["buckets"]:
        collection_id = uuid.UUID(bucket["key"])
        totals[collection_id] = bucket["doc_count"]
        for _, name, attribute in _flat_hierarchy():
            if attribute is not None:
                data[(collection_id, name)] = bucket[attribute.path]["doc_count"]

    def bft_with_level(node: Tree, level=0) -> Iterable[tuple[Tree, int]]:
        yield node, level
        for child in node.children:
            yield from bft_with_level(child, level=level + 1)

    return QualityMatrix(
        rows=[
            QualityMatrixRow(
                meta=QualityMatrixHeader(
                    id=str(node.node_id), label=node.title, alt_label=str(node.node_id), level=level
                ),
                counts={
                    # return the number of materials where the meta data field is __NOT__ missing.
                    name: totals.get(node.node_id, 0) - data.get((node.node_id, name), 0)
                    for _, name, attribute in _flat_hierarchy()
                    if attribute is not None
                },
                total=totals.get(node.node_id, 0),
            )
            for node, level in bft_with_level(collection)
        ],
        columns=_quality_matrix_columns(),
    )


def replication_source_quality_matrix(collection: Tree) -> QualityMatrix:
    """
    The replication source quality matrix has the replication source as rows, and the attribute hierarchy as columns.
    """
    search = MaterialSearch().collection_filter(collection_id=collection.node_id, transitive=True).extra(size=0)

    search.aggs.bucket(
        "replication_source",
        A(
            "terms",
            field=ElasticResourceAttribute.REPLICATION_SOURCE.keyword,
            size=10000,
            aggs={
                attribute.path: {"missing": {"field": attribute.keyword}}
                for _, name, attribute in _flat_hierarchy()
                if attribute is not None
            },
        ),
    )

    response = search.execute()
    if not response.success():
        raise HTTPException(status_code=502, detail="Failed to run elastic search query.")

    # transform the response aggregation which looks as follows into a nested dictionary which will allow to build the
    # desired QualityMatrix response. Sample response:
    # ...
    #   "aggregations" : {
    #     "replication_source" : {
    #       "doc_count_error_upper_bound" : 0,
    #       "sum_other_doc_count" : 0,
    #       "buckets" : [
    #         {
    #           "key" : "http://w3id.org/openeduhub/vocabs/new_lrt/5098cf0b-1c12-4a1b-a6d3-b3f29621e11d",
    #           "doc_count" : 92,
    #           "metadatacontributer_validator" : { "doc_count" : 92 },
    #           ...
    #           "metadatacontributer_provider" : { "doc_count" : 92 }
    #         },
    #         {
    #           "key" : "http://w3id.org/openeduhub/vocabs/new_lrt/a0218a48-a008-4975-a62a-27b1a83d454f",
    #           "doc_count" : 76,
    #           "metadatacontributer_validator" : { "doc_count" : 76 },
    #           ...
    #           "metadatacontributer_creator" : { "doc_count" : 55 }
    #         },
    #         ...

    return QualityMatrix(
        rows=[
            QualityMatrixRow(
                meta=QualityMatrixHeader(
                    id=bucket["key"].split("/")[-1],
                    label=bucket["key"].split("/")[-1],
                    alt_label=bucket["key"],
                    level=None,
                ),
                counts={
                    # return the number of materials where the meta data field is __NOT__ missing.
                    name: bucket["doc_count"] - bucket[attribute.path]["doc_count"]
                    for _, name, attribute in _flat_hierarchy()
                    if attribute is not None
                },
                total=bucket["doc_count"],
            )
            for bucket in response.aggregations["replication_source"]["buckets"]
        ],
        columns=_quality_matrix_columns(),
    )


#
# def replication_source_quality_matrix_old(collection: Tree) -> QualityMatrix:
#     """
#     The replication source quality matrix has the attribute hierarchy as rows, and the replication source as columns.
#     """
#     attributes = [attribute.path for _, _, attribute in flat_hierarchy() if attribute is not None]
#     search = MaterialSearch().collection_filter(collection_id=collection.node_id, transitive=True).extra(size=0)
#
#     search.aggs.bucket(
#         "replication_source",
#         A(
#             "terms",
#             field=ElasticResourceAttribute.REPLICATION_SOURCE.keyword,
#             size=10000,
#             aggs={attribute: {"missing": {"field": f"{attribute}.keyword"}} for attribute in attributes},
#         ),
#     )
#
#     response = search.execute()
#     if not response.success():
#         raise HTTPException(status_code=502, detail="Failed to run elastic search query.")
#
#     # transform the response aggregation which looks as follows into a nested dictionary which will allow to build the
#     # desired QualityMatrix response. Sample response:
#     # ...
#     #   "aggregations" : {
#     #     "replication_source" : {
#     #       "doc_count_error_upper_bound" : 0,
#     #       "sum_other_doc_count" : 0,
#     #       "buckets" : [
#     #         {
#     #           "key" : "http://w3id.org/openeduhub/vocabs/new_lrt/5098cf0b-1c12-4a1b-a6d3-b3f29621e11d",
#     #           "doc_count" : 92,
#     #           "ccm:metadatacontributer_validator" : { "doc_count" : 92 },
#     #           ...
#     #           "ccm:metadatacontributer_provider" : { "doc_count" : 92 }
#     #         },
#     #         {
#     #           "key" : "http://w3id.org/openeduhub/vocabs/new_lrt/a0218a48-a008-4975-a62a-27b1a83d454f",
#     #           "doc_count" : 76,
#     #           "ccm:metadatacontributer_validator" : { "doc_count" : 76 },
#     #           ...
#     #           "ccm:metadatacontributer_creator" : { "doc_count" : 55 }
#     #         },
#     #         ...
#     Attribute = str  # noqa
#     ReplicationSource = str  # noqa
#
#     # initialize empty dictionaries
#     totals: dict[ReplicationSource, int] = {}
#     data: dict[Attribute, dict[ReplicationSource, int]] = {attribute: {} for attribute in attributes}
#
#     # loop over result and fill dictionaries
#     for bucket in response.aggregations["replication_source"]["buckets"]:
#         replication_source = bucket["key"]
#         totals[replication_source] = bucket["doc_count"]
#         for attribute in attributes:
#             data[attribute][replication_source] = bucket[attribute]["doc_count"]
#
#     def last(attribute):
#         # strip the properties. or other prefixes from the attributes.
#         return attribute.split(".")[-1]
#
#     return QualityMatrix(
#         rows=[
#             QualityMatrixRow(
#                 header=name,
#                 alternative_header=last(attribute.path) if level == 1 else None,
#                 level=level,
#                 columns={
#                     replication_source: int(
#                         round(100 - 100 * data[attribute.path][replication_source] / totals[replication_source])
#                     )
#                     for replication_source in totals.keys()
#                 }
#                 if level == 1  # for the intermediate levels like "Beschreibendes", we don't have any data
#                 else {},
#                 counts={
#                     replication_source: data[attribute.path][replication_source] for replication_source in totals.keys()
#                 }
#                 if level == 1
#                 else {},
#                 total=sum(totals.values())
#                 # Note: the total counts are really helpful for debugging
#                 # columns_missing={
#                 #     replication_source: data[attribute.path][replication_source] for replication_source in totals.keys()
#                 # }
#                 # if level == 2  # for the intermediate levels like "Beschreibendes", we don't have any data
#                 # else {},
#             )
#             for level, name, attribute in flat_hierarchy()
#         ],
#         totals=totals,
#     )


Base = declarative_base()


class Timeline(Base):
    """Table will be automatically created at application start time if it does not exist."""

    __tablename__ = "timeline"
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )
    timestamp = Column(Integer, nullable=False)
    quality = Column(JSON, nullable=False)
    mode = Column(Text, nullable=False)
    node_id = Column(UUID, nullable=False)
    total = Column(JSON, nullable=False)


@repeat_every(seconds=60 * 60, logger=logger)
async def quality_backup(database: Database):
    """Repeat every hour, but only store once per day between 00:00 and 01:00 am."""
    now = datetime.datetime.now()

    # check if this is the first execution of the day.
    if (now - datetime.timedelta(hours=1)).date() == now.date():
        return

    logger.info("Storing quality matrices in database")

    for node_id in COLLECTION_NAME_TO_ID.values():
        for mode in ["replication-source", "collection"]:
            root = tree(node_id=uuid.UUID(node_id))
            logger.info(f"Storing {mode} quality matrix for: '{root.title} ({root.node_id})'")
            if mode == "replication-source":
                quality_data, total = replication_source_quality_matrix(root)
            else:
                quality_data, total = collection_quality_matrix(root)
            await store_in_timeline(quality_data, database, mode, uuid.UUID(node_id), total)


async def timestamps(database: Database, mode: QualityMatrixMode, node_id: uuid.UUID):
    query = select([Timeline.timestamp]).where(Timeline.mode == mode).where(Timeline.node_id == node_id)
    await database.connect()
    result: list[Mapping] = await database.fetch_all(query)

    return [entry["timestamp"] for entry in result]


async def store_in_timeline(
    data: list[QualityMatrixRow],
    database: Database,
    mode: QualityMatrixMode,
    node_id: uuid.UUID,
    total: dict,
):
    await database.connect()
    await database.execute(
        sqlalchemy.insert(Timeline).values(
            {
                "timestamp": datetime.now().timestamp(),
                "quality": [
                    {
                        "row_header": entry.row_header,
                        "level": entry.level,
                        "columns": entry.columns,
                    }
                    for entry in data
                ],
                "mode": mode,
                "node_id": node_id,
                "total": total,
            }
        )
    )

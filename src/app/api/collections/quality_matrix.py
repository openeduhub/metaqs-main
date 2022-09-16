import datetime
import json
import uuid
from typing import Iterable, Literal, Optional, Iterator

from elasticsearch_dsl import A
from fastapi import HTTPException
from fastapi_utils.tasks import repeat_every
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.collections.tree import Tree, tree
from app.core.config import QUALITY_MATRIX_STORE_INTERVAL
from app.core.constants import COLLECTION_NAME_TO_ID
from app.core.logging import logger
from app.core.meta_hierarchy import METADATA_HIERARCHY, load_metadataset
from app.db.tasks import Timeline, session_maker
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


def timestamps(session: Session, mode: QualityMatrixMode, node_id: uuid.UUID) -> list[int]:
    return [
        row[0]
        for row in (
            session.query(Timeline.timestamp).where(Timeline.mode == mode).where(Timeline.node_id == str(node_id)).all()
        )
    ]


def past_quality_matrix(
    session: Session, mode: QualityMatrixMode, collection_id: uuid.UUID, timestamp: int
) -> QualityMatrix:
    result = (
        session.query(Timeline)
        .where(Timeline.timestamp == timestamp)
        .where(Timeline.mode == mode)
        .where(Timeline.node_id == str(collection_id))
        .all()
    )

    if len(result) == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    elif len(result) > 1:
        raise HTTPException(status_code=500, detail="More than one item found")

    return QualityMatrix.parse_obj(json.loads(result[0].quality_matrix))


def quality_backup(session: Session):
    logger.info("Storing quality matrices in database")

    for node_id in COLLECTION_NAME_TO_ID.values():
        root = tree(node_id=uuid.UUID(node_id))
        logger.info(f"Storing quality matrix for: '{root.title} ({root.node_id})'")
        timestamp = int(datetime.datetime.now().timestamp())
        session.add(
            Timeline(
                timestamp=timestamp,
                mode="replication-source",
                node_id=str(node_id),
                quality_matrix=replication_source_quality_matrix(root).json(),
            )
        )
        session.add(
            Timeline(
                timestamp=timestamp,
                mode="collection",
                node_id=str(node_id),
                quality_matrix=collection_quality_matrix(root).json(),
            )
        )
        session.commit()


@repeat_every(seconds=QUALITY_MATRIX_STORE_INTERVAL, logger=logger)
def quality_matrix_backup_job():
    """Periodically store the quality matrices in the database"""
    with session_maker().context_session() as session:
        quality_backup(session)

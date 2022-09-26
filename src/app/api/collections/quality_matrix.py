import datetime
import json
import uuid
from functools import cache
from typing import Iterable, Literal, Optional, Iterator, Any, Tuple

import aiocron
from elasticsearch_dsl import A
from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.collections.tree import Tree, tree
from app.core.config import QUALITY_MATRIX_BACKUP_SCHEDULE, ELASTIC_TOTAL_SIZE
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


def quality_matrix(collection: Tree, mode: QualityMatrixMode) -> QualityMatrix:
    if mode == "replication-source":
        return _replication_source_quality_matrix(collection)
    elif mode == "collection":
        return _collection_quality_matrix(collection)
    else:
        raise RuntimeError(f"Unsupported quality matrix mode: {mode}")


def _flat_hierarchy() -> Iterator[tuple[int, str, Optional[ElasticResourceAttribute]]]:
    for key, value in METADATA_HIERARCHY.items():
        yield 0, key, None
        for attribute, name in value:
            yield 1, name, attribute


@cache
def _quality_matrix_columns() -> list[QualityMatrixHeader]:
    """
    Extracts the human readable names of the metadata fields from the metadataset provided by EDU-sharing and build the
    column descriptors.
    """
    data = load_metadataset()
    caption_map = {widget["id"]: widget["caption"] for widget in data["widgets"]}
    logger.info(f"Initialized captions of MetaDataSet from EDU-Sharing service with {len(caption_map)} entries.")
    return [
        QualityMatrixHeader(
            id=name,
            label=caption_map.get(attribute.path.split(".")[-1], attribute.path.split(".")[-1]) if level > 0 else name,
            alt_label=attribute.path.split(".")[-1] if level > 0 else None,
            level=level,
        )
        for level, name, attribute in _flat_hierarchy()
    ]


@cache
def _replication_source_row_headers() -> dict[str, QualityMatrixHeader]:
    """Build the row headers for the replication-source quality matrix."""
    try:
        replication_source_widget: Optional[dict[str, Any]] = next(
            filter(lambda w: w["id"] == "ccm:replicationsource", load_metadataset()["widgets"]), None
        )

        def build(value: dict[str, Any]) -> Optional[QualityMatrixHeader]:
            """
            A value block in the MetaDataSet looks as follows:
            {
              "id": "http://w3id.org/openeduhub/vocabs/sources/003d68a3-1417-44eb-809c-dada652cbb05",
              "caption": "DLRG",
              "description": null,
              "parent": null,
              "url": "https://www.dlrg.de/",
              "alternativeIds": null # or  ["<name>_spider"]
            }
            """
            try:
                if value["alternativeIds"] is None:
                    return None

                id = value["alternativeIds"][0]
                return QualityMatrixHeader(id=id, label=value["caption"], alt_label=f'{id} ({value["id"]})', level=0)
            except (KeyError, IndexError):
                logger.warning(f"Failed to build column header for value: {value}")
                return None

        if replication_source_widget is not None:
            return {
                header.id: header for header in map(build, replication_source_widget["values"]) if header is not None
            }
        else:
            logger.warning("Failed to build replication source headers. Returning empty dictionary.")
            return {}
    except Exception as e:
        logger.exception("Failed to build replication-source headers, falling back to default headers.")
        return {}


def _collection_quality_matrix(collection: Tree) -> QualityMatrix:
    """
    The collection quality matrix has the collections as rows and the attribute hierarchy as columns.
    """
    search = MaterialSearch().collection_filter(collection_id=collection.node_id, transitive=True).extra(size=0)

    search.aggs.bucket(
        "collection",
        A(
            "terms",
            field="collections.nodeRef.id.keyword",
            size=ELASTIC_TOTAL_SIZE,
            aggs={
                attribute.path: {"missing": {"field": attribute.keyword}}
                for _, _, attribute in _flat_hierarchy()
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


def _replication_source_quality_matrix(collection: Tree) -> QualityMatrix:
    """
    The replication source quality matrix has the replication source as rows, and the attribute hierarchy as columns.
    """
    search = MaterialSearch().collection_filter(collection_id=collection.node_id, transitive=True).extra(size=0)

    search.aggs.bucket(
        "replication_source",
        A(
            "terms",
            field=ElasticResourceAttribute.REPLICATION_SOURCE.keyword,
            size=ELASTIC_TOTAL_SIZE,
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
    #           "key" : "youtube_spider",
    #           "doc_count" : 92,
    #           "metadatacontributer_validator" : { "doc_count" : 92 },
    #           ...
    #           "metadatacontributer_provider" : { "doc_count" : 92 }
    #         },
    #         {
    #           "key" : "serlo_spider",
    #           "doc_count" : 76,
    #           "metadatacontributer_validator" : { "doc_count" : 76 },
    #           ...
    #           "metadatacontributer_creator" : { "doc_count" : 55 }
    #         },
    #         ...

    row_headers = _replication_source_row_headers()

    Bucket = dict[str, Any]

    def rows() -> Iterator[tuple[QualityMatrixHeader, Optional[Bucket]]]:
        """Returns None for buckets that are not part of the elastic query result."""
        # first loop over all replication sources and insert empty rows in case we did not find anything
        # See: https://github.com/openeduhub/metaqs-main/issues/121
        buckets = {bucket["key"]: bucket for bucket in response.aggregations["replication_source"]["buckets"]}
        for key, header in row_headers.items():
            # remove bucket from dictionary to check what is left after this loop
            yield header, buckets.pop(key, None)
        # now, check if there are any buckets left (in case the set of
        # replication sources from edusharing is not complete)
        for key, bucket in buckets.items():
            # use defaults for the rows as we have no alternative...
            yield QualityMatrixHeader(id=bucket["key"], label=bucket["key"], alt_label=bucket["key"], level=0), bucket

    return QualityMatrix(
        rows=[
            QualityMatrixRow(
                meta=header,
                counts={
                    # return the number of materials where the meta data field is __NOT__ missing.
                    name: 0 if bucket is None else (bucket["doc_count"] - bucket[attribute.path]["doc_count"])
                    for _, name, attribute in _flat_hierarchy()
                    if attribute is not None
                },
                total=0 if bucket is None else bucket["doc_count"],
            )
            for header, bucket in rows()
        ],
        columns=_quality_matrix_columns(),
    )


def timestamps(session: Session, mode: QualityMatrixMode, node_id: uuid.UUID) -> list[int]:
    return [
        row.timestamp
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


def quality_backup(session: Session, timestamp: datetime.datetime):
    """
    Note: If multiple instances of the app are running (e.g. via
    multiple gunicorn workers), we should not store the quality
    matrix multiple times.

    Hence, we pass in the timestamp of the scheduled save and use
    it as part of the primary key. The database will then make sure
    we cannot write duplicate instances.
    """
    logger.info(f"Storing quality matrices in database for {timestamp}")

    modes: Tuple[QualityMatrixMode, ...] = ("replication-source", "collection")

    for node_id in COLLECTION_NAME_TO_ID.values():
        root = tree(node_id=uuid.UUID(node_id))
        for mode in modes:
            try:
                logger.debug(f"Storing '{mode}' quality matrix for: '{root.title} ({root.node_id})'")
                with session.begin():
                    session.add(
                        Timeline(
                            timestamp=timestamp.timestamp(),
                            mode=mode,
                            node_id=str(node_id),
                            quality_matrix=quality_matrix(root, mode=mode).json(),
                        )
                    )
            except IntegrityError as e:
                logger.debug(f"'{mode}' quality matrix already stored ('{root.title} / {root.node_id})': {e}")


async def quality_matrix_backup_job():
    """
    Periodically store the quality matrices in the database.

    When added as startup task, this method will run concurrently with the incoming requests in the main event loop.
    """
    cron = aiocron.crontab(QUALITY_MATRIX_BACKUP_SCHEDULE)
    logger.info(f"Starting quality matrix backup schedule with `{QUALITY_MATRIX_BACKUP_SCHEDULE}")
    while True:
        await cron.next()  # yields control and waits until the next write is scheduled
        with session_maker().context_session() as session:
            quality_backup(session, timestamp=cron.croniter.get_current(ret_type=datetime.datetime))

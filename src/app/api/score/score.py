import uuid

from elasticsearch_dsl import Q
from elasticsearch_dsl.response import Response
from fastapi import Path

import app.core.constants
from app.api.score.models import LearningMaterialAttribute
from app.elastic.dsl import afilter, amissing
from app.elastic.elastic import (
    ResourceType,
    query_collections,
    query_materials,
    query_missing_material_license,
)
from app.elastic.search import Search
from app.models import CollectionAttribute, ElasticResourceAttribute

material_terms_relevant_for_score = [
    "missing_title",
    "missing_license",
    "missing_keywords",
    "missing_taxonid",
    "missing_edu_context",
]
collections_terms_relevant_for_score = [
    "missing_title",
    "missing_keywords",
    "missing_edu_context",
]


def calc_scores(stats: dict) -> dict:
    if stats["total"] == 0:
        return {k: 0 for k in stats.keys()}

    return {k: 1 - v / stats["total"] for k, v in stats.items() if k != "total"}


def calc_weighted_score(collection_scores: dict, material_scores: dict) -> int:
    score_sum = sum(
        v
        for k, v in collection_scores.items()
        if k in collections_terms_relevant_for_score
    ) + sum(
        v for k, v in material_scores.items() if k in material_terms_relevant_for_score
    )
    number_of_relevant_terms = sum(
        1 for k in collection_scores.keys() if k in collections_terms_relevant_for_score
    ) + sum(1 for k in material_scores.keys() if k in material_terms_relevant_for_score)

    return int((100 * score_sum) / number_of_relevant_terms)


def get_score_search(node_id: uuid.UUID, resource_type: ResourceType) -> Search:
    query, aggs = None, None
    if resource_type is ResourceType.COLLECTION:
        query, aggs = query_collections, aggs_collection_validation
    elif resource_type is ResourceType.MATERIAL:
        query, aggs = query_materials, aggs_material_validation
    s = Search().base_filters().query(query(node_id=node_id))
    for name, _agg in aggs.items():
        s.aggs.bucket(name, _agg)
    return s


def score(response: Response) -> dict:
    return {
        "total": response.hits.total.value,
        **{k: v["doc_count"] for k, v in response.aggregations.to_dict().items()},
    }


async def search_score(node_id: uuid.UUID, resource_type: ResourceType) -> dict:
    s = get_score_search(node_id, resource_type)

    response: Response = s.execute()

    if response.success():
        return score(response)


def collection_id_param(
    *,
    collection_id: uuid.UUID = Path(
        ..., examples=app.core.constants.COLLECTION_NAME_TO_ID
    ),
) -> uuid.UUID:
    return collection_id


def field_names_used_for_score_calculation(properties: dict) -> list[str]:
    values = []
    for value in properties.values():
        value = list(list(value.to_dict().values())[0].values())[0]
        if isinstance(value, dict):
            value = list(value.keys())[0]

        value.replace(".keyword", "")
        if value != "should":
            values += [value]
    return values


aggs_material_validation = {
    "missing_title": amissing(qfield=LearningMaterialAttribute.TITLE),
    "missing_keywords": amissing(qfield=LearningMaterialAttribute.KEYWORDS),
    "missing_subjects": amissing(qfield=LearningMaterialAttribute.SUBJECTS),
    "missing_description": amissing(qfield=LearningMaterialAttribute.DESCRIPTION),
    "missing_license": afilter(query=query_missing_material_license()),
    "missing_edu_context": amissing(qfield=LearningMaterialAttribute.EDU_CONTEXT),
    "missing_ads_qualifier": amissing(qfield=LearningMaterialAttribute.CONTAINS_ADS),
    "missing_material_type": amissing(
        qfield=LearningMaterialAttribute.LEARNINGRESOURCE_TYPE
    ),
    "missing_object_type": amissing(qfield=LearningMaterialAttribute.OBJECT_TYPE),
}
aggs_collection_validation = {
    "missing_title": amissing(qfield=CollectionAttribute.TITLE),
    "short_title": afilter(Q("range", char_count_title={"gt": 0, "lt": 5})),
    "missing_keywords": amissing(qfield=ElasticResourceAttribute.KEYWORDS),
    "few_keywords": afilter(Q("range", token_count_keywords={"gt": 0, "lt": 3})),
    "missing_description": amissing(qfield=CollectionAttribute.DESCRIPTION),
    "short_description": afilter(
        Q("range", char_count_description={"gt": 0, "lt": 30})
    ),
    "missing_edu_context": amissing(qfield=ElasticResourceAttribute.EDU_CONTEXT),
}

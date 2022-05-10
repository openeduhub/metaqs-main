from uuid import UUID

from elasticsearch_dsl.response import Response

from app.crud.elastic import (
    ResourceType,
    aggs_collection_validation,
    aggs_material_validation,
    query_collections,
    query_materials,
)
from app.elastic.search import Search

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


def score_search(noderef_id: UUID, resource_type: ResourceType) -> Search:
    query, aggs = None, None
    if resource_type is ResourceType.COLLECTION:
        query, aggs = query_collections, aggs_collection_validation
    elif resource_type is ResourceType.MATERIAL:
        query, aggs = query_materials, aggs_material_validation
    s = Search().query(query(ancestor_id=noderef_id))
    for name, _agg in aggs.items():
        s.aggs.bucket(name, _agg)
    return s


def score(response: Response) -> dict:
    return {
        "total": response.hits.total.value,
        **{k: v["doc_count"] for k, v in response.aggregations.to_dict().items()},
    }


async def query_score(noderef_id: UUID, resource_type: ResourceType) -> dict:
    s = score_search(noderef_id, resource_type)

    response: Response = s[:0].execute()

    if response.success():
        return score(response)

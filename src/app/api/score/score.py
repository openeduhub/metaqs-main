import uuid

from elasticsearch_dsl import Q
from elasticsearch_dsl.response import Response

from app.api.collections.oer import oer_ratio
from app.api.score.models import (
    MissingCollectionProperties,
    MissingMaterialProperties,
    ScoreOutput,
)
from app.core.models import ElasticResourceAttribute
from app.elastic.dsl import afilter, amissing
from app.elastic.elastic import ResourceType, query_many, query_missing_material_license
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


def get_score_search(node_id: uuid.UUID, resource_type: ResourceType) -> Search:
    search = (
        Search()
        .base_filters()
        .query(query_many(resource_type=resource_type, node_id=node_id))
    )
    if resource_type is ResourceType.COLLECTION:
        aggs = aggs_collection_validation
    else:  # ResourceType.MATERIAL
        aggs = aggs_material_validation
    for name, _agg in aggs.items():
        search.aggs.bucket(name, _agg)
    return search


def map_response_to_output(response: Response) -> dict:
    return {
        "total": response.hits.total.value,
        **{k: v["doc_count"] for k, v in response.aggregations.to_dict().items()},
    }


def search_score(node_id: uuid.UUID, resource_type: ResourceType) -> dict:
    s = get_score_search(node_id, resource_type)

    response: Response = s.execute()

    if response.success():
        return map_response_to_output(response)


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
    "missing_title": amissing(qfield=ElasticResourceAttribute.TITLE),
    "missing_material_type": amissing(
        qfield=ElasticResourceAttribute.LEARNINGRESOURCE_TYPE
    ),
    "missing_subjects": amissing(qfield=ElasticResourceAttribute.SUBJECTS),
    "missing_url": amissing(qfield=ElasticResourceAttribute.WWW_URL),
    "missing_license": afilter(query=query_missing_material_license()),
    "missing_publisher": amissing(qfield=ElasticResourceAttribute.PUBLISHER),
    "missing_description": amissing(qfield=ElasticResourceAttribute.DESCRIPTION),
    "missing_intended_end_user_role": amissing(
        qfield=ElasticResourceAttribute.EDU_ENDUSERROLE_DE
    ),
    "missing_edu_context": amissing(qfield=ElasticResourceAttribute.EDU_CONTEXT),
}
aggs_collection_validation = {
    "missing_title": amissing(qfield=ElasticResourceAttribute.COLLECTION_TITLE),
    "short_title": afilter(Q("range", char_count_title={"gt": 0, "lt": 5})),
    "missing_keywords": amissing(qfield=ElasticResourceAttribute.KEYWORDS),
    "few_keywords": afilter(Q("range", token_count_keywords={"gt": 0, "lt": 3})),
    "missing_description": amissing(
        qfield=ElasticResourceAttribute.COLLECTION_DESCRIPTION
    ),
    "short_description": afilter(
        Q("range", char_count_description={"gt": 0, "lt": 30})
    ),
    "missing_edu_context": amissing(qfield=ElasticResourceAttribute.EDU_CONTEXT),
}


async def get_score(node_id: uuid.UUID) -> ScoreOutput:
    collection_stats = search_score(
        node_id=node_id, resource_type=ResourceType.COLLECTION
    )
    collection_scores = calc_scores(stats=collection_stats)

    material_stats = search_score(node_id=node_id, resource_type=ResourceType.MATERIAL)
    material_scores = calc_scores(stats=material_stats)

    score_ = calc_weighted_score(
        collection_scores=collection_scores, material_scores=material_scores
    )

    oer = oer_ratio(node_id)

    collections = MissingCollectionProperties(
        total=collection_stats["total"], **collection_scores
    )
    materials = MissingMaterialProperties(
        total=material_stats["total"], **material_scores
    )
    return ScoreOutput(
        score=score_, collections=collections, materials=materials, oer_ratio=oer
    )

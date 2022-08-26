import uuid

from elasticsearch_dsl import Q, A
from elasticsearch_dsl.query import Query, Bool, Terms, Exists
from elasticsearch_dsl.response import Response
from pydantic import BaseModel, Field

from app.api.collections.utils import oer_ratio
from app.core.constants import FORBIDDEN_LICENSES
from app.elastic.attributes import ElasticResourceAttribute
from app.elastic.search import CollectionSearch, MaterialSearch

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


class MissingCollectionProperties(BaseModel):
    total: int = Field(ge=0, description="Number of entries")
    short_description: float = Field(
        ge=0.0,
        le=1.0,
        description="Ratio of entries without short description",
    )
    short_title: float = Field(ge=0.0, le=1.0, description="Ratio of entries without short title")
    missing_edu_context: float = Field(ge=0.0, le=1.0, description="Ratio of entries without edu context")
    missing_description: float = Field(ge=0.0, le=1.0, description="Ratio of entries without description")
    few_keywords: float = Field(ge=0.0, le=1.0, description="Ratio of entries with few keywords")
    missing_keywords: float = Field(ge=0.0, le=1.0, description="Ratio of entries without keywords")
    missing_title: float = Field(ge=0.0, le=1.0, description="Ratio of entries without title")


class MissingMaterialProperties(BaseModel):
    total: int = Field(default=0, ge=0, description="Number of entries")
    missing_title: float = Field(ge=0.0, le=1.0, description="Ratio of entries without title")
    missing_material_type: float = Field(
        ge=0.0,
        le=1.0,
        description="Ratio of entries missing material type",
    )
    missing_subjects: float = Field(ge=0.0, le=1.0, description="Ratio of entries missing subjects")
    missing_url: float = Field(ge=0.0, le=1.0, description="Ratio of entries without url")
    missing_license: float = Field(ge=0.0, le=1.0, description="Ratio of entries with missing license")
    missing_publisher: float = Field(ge=0.0, le=1.0, description="Ratio of entries without publisher")
    missing_description: float = Field(ge=0.0, le=1.0, description="Ratio of entries without description")
    missing_intended_end_user_role: float = Field(
        ge=0.0,
        le=1.0,
        description="Ratio of entries without intended end user role",
    )
    missing_edu_context: float = Field(ge=0.0, le=1.0, description="Ratio of entries without edu context")


class Score(BaseModel):
    score: int = Field(ge=0, le=100, description="Overall score")
    oer_ratio: int = Field(ge=0, le=100, description="Overall ratio of OER content")
    collections: MissingCollectionProperties = Field(description="Score for specific collection properties")
    materials: MissingMaterialProperties = Field(description="Score for specific material properties")


def calc_scores(stats: dict) -> dict:
    if stats["total"] == 0:
        return {k: 0 for k in stats.keys()}

    return {k: 1 - v / stats["total"] for k, v in stats.items() if k != "total"}


def query_missing_material_license(name: str = "missing_license") -> Query:
    """
    :param name: An optional alias for the should query, that can be used to identify which query matched.
                 See: https://www.elastic.co/guide/en/elasticsearch/reference/7.17/query-dsl-bool-query.html#named-queries
    """
    return Bool(
        should=[
            Terms(**{ElasticResourceAttribute.LICENSES.keyword: FORBIDDEN_LICENSES}),
            Bool(must_not=Exists(field=ElasticResourceAttribute.LICENSES.path)),
        ],
        minimum_should_match=1,
        _name=name,
    )


def calc_weighted_score(collection_scores: dict, material_scores: dict) -> int:
    score_sum = sum(v for k, v in collection_scores.items() if k in collections_terms_relevant_for_score) + sum(
        v for k, v in material_scores.items() if k in material_terms_relevant_for_score
    )
    number_of_relevant_terms = sum(
        1 for k in collection_scores.keys() if k in collections_terms_relevant_for_score
    ) + sum(1 for k in material_scores.keys() if k in material_terms_relevant_for_score)

    return int((100 * score_sum) / number_of_relevant_terms)


def map_response_to_output(response: Response) -> dict:
    return {
        "total": response.hits.total.value,
        **{k: v["doc_count"] for k, v in response.aggregations.to_dict().items()},
    }


def collection_search_score(collection_id: uuid.UUID) -> dict:
    search = CollectionSearch().collection_filter(collection_id).extra(size=0, from_=0)
    aggregations = {
        "missing_title": A("missing", field=ElasticResourceAttribute.COLLECTION_TITLE.keyword),
        "short_title": A("filter", (Q("range", char_count_title={"gt": 0, "lt": 5}))),
        "missing_keywords": A("missing", field=ElasticResourceAttribute.KEYWORDS.keyword),
        "few_keywords": A("filter", (Q("range", token_count_keywords={"gt": 0, "lt": 3}))),
        "missing_description": A("missing", field=ElasticResourceAttribute.COLLECTION_DESCRIPTION.keyword),
        "short_description": A("filter", (Q("range", char_count_description={"gt": 0, "lt": 30}))),
        "missing_edu_context": A("missing", field=ElasticResourceAttribute.EDU_CONTEXT.keyword),
    }

    for name, agg in aggregations.items():
        search.aggs.bucket(name, agg)

    response: Response = search.execute()

    if response.success():
        return map_response_to_output(response)


def material_search_score(collection_id: uuid.UUID) -> dict:
    search = MaterialSearch().collection_filter(collection_id, transitive=True).extra(size=0, from_=0)

    aggregations = {
        "missing_title": A("missing", field=ElasticResourceAttribute.TITLE.keyword),
        "missing_material_type": A("missing", field=ElasticResourceAttribute.LEARNINGRESOURCE_TYPE.keyword),
        "missing_subjects": A("missing", field=ElasticResourceAttribute.SUBJECTS.keyword),
        "missing_url": A("missing", field=ElasticResourceAttribute.WWW_URL.keyword),
        "missing_license": A("filter", query_missing_material_license()),
        "missing_publisher": A("missing", field=ElasticResourceAttribute.PUBLISHER.keyword),
        "missing_description": A("missing", field=ElasticResourceAttribute.DESCRIPTION.keyword),
        "missing_intended_end_user_role": A("missing", field=ElasticResourceAttribute.EDU_ENDUSERROLE_DE.keyword),
        "missing_edu_context": A("missing", field=ElasticResourceAttribute.EDU_CONTEXT.keyword),
    }

    for name, agg in aggregations.items():
        search.aggs.bucket(name, agg)

    response: Response = search.execute()

    if response.success():
        return map_response_to_output(response)


async def score(node_id: uuid.UUID) -> Score:
    collection_stats = collection_search_score(collection_id=node_id)
    collection_scores = calc_scores(stats=collection_stats)

    material_stats = material_search_score(collection_id=node_id)
    material_scores = calc_scores(stats=material_stats)

    score_ = calc_weighted_score(collection_scores=collection_scores, material_scores=material_scores)

    oer = oer_ratio(node_id)

    collections = MissingCollectionProperties(total=collection_stats["total"], **collection_scores)
    materials = MissingMaterialProperties(total=material_stats["total"], **material_scores)
    return Score(score=score_, collections=collections, materials=materials, oer_ratio=oer)

from unittest.mock import MagicMock

import pytest
from elasticsearch_dsl.response import Response

from app.crud.elastic import ResourceType
from app.crud.stats import score, score_search
from app.score import ScoreModulator, calc_scores


def test_score_empty_hits():
    dummy_hits = {"hits": []}
    mocked_response = Response(
        search="", response={"test": "hello", "aggregations": {}, "hits": dummy_hits}
    )
    mocked_response._search = MagicMock()
    mocked_response._d_ = dummy_hits
    mocked_response._hits = MagicMock()
    mocked_response.hits = MagicMock()
    mocked_response.hits.total.value = 0
    output = score(mocked_response)

    expected_score = {"total": len(dummy_hits["hits"])}
    assert output == expected_score


@pytest.mark.skip()
def test_score_with_hits():
    mocked_response = Response(
        search="", response={"test": "hello", "aggregations": {}, "hits": {"hits": []}}
    )
    mocked_response._search = MagicMock()
    mocked_response._d_ = {"hits": []}
    mocked_response._hits = MagicMock()
    mocked_response.hits = MagicMock()
    mocked_response.hits.total.value = 0
    print(mocked_response)
    output = score(mocked_response)

    expected_score = {
        "score": 90,
        "collections": {
            "total": 122,
            "short_description": 1.0,
            "short_title": 1.0,
            "missing_edu_context": 0.319672131147541,
            "missing_description": 0.8852459016393442,
            "few_keywords": 1.0,
            "missing_keywords": 1.0,
            "missing_title": 1.0,
        },
        "materials": {
            "total": 411,
            "missing_edu_context": 1.0,
            "missing_object_type": 1.0,
            "missing_description": 0.6374695863746959,
            "missing_license": 1.0,
            "missing_ads_qualifier": 1.0,
            "missing_keywords": 1.0,
            "missing_title": 1.0,
            "missing_subjects": 1.0,
            "missing_material_type": 0.9951338199513382,
        },
    }
    expected_score = {"total": 0}
    assert output == expected_score


def test_score_search_material():
    noderef_id = "dummy_id"
    assert ResourceType.MATERIAL == "MATERIAL"
    resource_type = ResourceType.MATERIAL
    search = score_search(noderef_id, resource_type)

    expected_query = {
        "aggs": {
            "missing_ads_qualifier": {
                "missing": {"field": "properties.ccm:containsAdvertisement.keyword"}
            },
            "missing_description": {
                "missing": {"field": "properties.cclom:general_description.keyword"}
            },
            "missing_edu_context": {
                "missing": {"field": "properties.ccm:educationalcontext.keyword"}
            },
            "missing_keywords": {
                "missing": {"field": "properties.cclom:general_keyword.keyword"}
            },
            "missing_license": {
                "filter": {
                    "bool": {
                        "minimum_should_match": 1,
                        "should": [
                            {
                                "terms": {
                                    "properties.ccm:commonlicense_key.keyword": [
                                        "UNTERRICHTS_UND_LEHRMEDIEN",
                                        "NONE",
                                        "",
                                    ]
                                }
                            },
                            {
                                "bool": {
                                    "must_not": [
                                        {
                                            "exists": {
                                                "field": "properties.ccm:commonlicense_key"
                                            }
                                        }
                                    ]
                                }
                            },
                        ],
                    }
                }
            },
            "missing_material_type": {
                "missing": {"field": "properties.ccm:oeh_lrt_aggregated.keyword"}
            },
            "missing_object_type": {
                "missing": {"field": "properties.ccm:objecttype.keyword"}
            },
            "missing_subjects": {
                "missing": {"field": "properties.ccm:taxonid.keyword"}
            },
            "missing_title": {"missing": {"field": "properties.cclom:title.keyword"}},
        },
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"type": "ccm:io"}},
                    {"term": {"collections.path.keyword": noderef_id}},
                ]
            }
        },
    }
    assert search.to_dict() == expected_query


def test_score_search_collection():
    noderef_id = "dummy_id"
    assert ResourceType.COLLECTION == "COLLECTION"
    resource_type = ResourceType.COLLECTION
    search = score_search(noderef_id, resource_type)

    expected_query = {
        "aggs": {
            "few_keywords": {
                "filter": {"range": {"token_count_keywords": {"gt": 0, "lt": 3}}}
            },
            "missing_description": {
                "missing": {"field": "properties.cm:description.keyword"}
            },
            "missing_edu_context": {
                "missing": {"field": "properties.ccm:educationalcontext.keyword"}
            },
            "missing_keywords": {
                "missing": {"field": "properties.cclom:general_keyword.keyword"}
            },
            "missing_title": {"missing": {"field": "properties.cm:title.keyword"}},
            "short_description": {
                "filter": {"range": {"char_count_description": {"gt": 0, "lt": 30}}}
            },
            "short_title": {
                "filter": {"range": {"char_count_title": {"gt": 0, "lt": 5}}}
            },
        },
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"type": "ccm:map"}},
                    {"term": {"path": noderef_id}},
                ]
            }
        },
    }
    assert search.to_dict() == expected_query


@pytest.mark.skip(reason="Unhandled exception")
def test_score_search_exception():
    noderef_id = "123"
    resource_type = ""
    search = score_search(noderef_id, resource_type)
    assert search.to_dict() == {}


def test_calc_scores_zero_total():
    stats = {"total": 0, "dummy_key": "dummy_value"}
    modulator = ""
    score = calc_scores(stats, modulator)
    stats |= {"dummy_key": 0}
    assert score == stats


def test_calc_scores():
    stats = {"total": 10, "dummy_key": 1}
    modulator = ScoreModulator.LINEAR
    score = calc_scores(stats, modulator)
    stats = {"dummy_key": 0.9}
    assert score == stats

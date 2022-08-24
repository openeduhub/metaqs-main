import uuid
from unittest.mock import MagicMock

import pytest
from elasticsearch_dsl.response import Response

from app.api.collections.score import (
    calc_scores,
    calc_weighted_score,
    map_response_to_output,
    collection_search_score,
    material_search_score,
)
from app.core.constants import COLLECTION_NAME_TO_ID
from tests.conftest import elastic_search_mock


def test_score_empty_hits():
    dummy_hits = {"hits": []}
    mocked_response = Response(search="", response={"test": "hello", "aggregations": {}, "hits": dummy_hits})
    mocked_response._search = MagicMock()
    mocked_response._d_ = dummy_hits
    mocked_response._hits = MagicMock()
    mocked_response.hits = MagicMock()
    mocked_response.hits.total.value = 0
    output = map_response_to_output(mocked_response)

    expected_score = {"total": len(dummy_hits["hits"])}
    assert output == expected_score


@pytest.mark.asyncio
async def test_collection_search_score():
    chemie = uuid.UUID(COLLECTION_NAME_TO_ID["Chemie"])
    with elastic_search_mock("collection-search-score"):
        result = collection_search_score(chemie)
    assert result == {
        "total": 209,
        "short_description": 0,
        "short_title": 0,
        "missing_edu_context": 58,
        "missing_description": 156,
        "few_keywords": 0,
        "missing_keywords": 2,
        "missing_title": 0,
    }


@pytest.mark.asyncio
async def test_material_search_score():
    chemie = uuid.UUID(COLLECTION_NAME_TO_ID["Chemie"])
    with elastic_search_mock("material-search-score"):
        result = material_search_score(chemie)
    assert result == {
        "total": 2331,
        "missing_intended_end_user_role": 871,
        "missing_edu_context": 7,
        "missing_publisher": 961,
        "missing_url": 55,
        "missing_description": 819,
        "missing_license": 5,
        "missing_title": 0,
        "missing_subjects": 1,
        "missing_material_type": 15,
    }


def test_calc_scores_zero_total():
    stats = {"total": 0, "dummy_key": "dummy_value"}
    score = calc_scores(stats)
    stats |= {"dummy_key": 0}
    assert score == stats


def test_calc_scores():
    stats = {"total": 10, "dummy_key": 1}
    score = calc_scores(stats)
    stats = {"dummy_key": 0.9}
    assert score == stats


def test_calc_weighted_score_dummy_values():
    score_value = calc_weighted_score({"missing_title": 0.9}, {})
    assert score_value == 90
    score_value = calc_weighted_score({}, {"missing_title": 0.9})
    assert score_value == 90
    score_value = calc_weighted_score({"missing_title": 0.9}, {"missing_title": 0.9})
    assert score_value == 90
    score_value = calc_weighted_score({"missing_title": 0.9}, {"missing_title": 0.8})
    assert score_value == 85


def test_calc_weighted_score_empty_responses():
    with pytest.raises(ZeroDivisionError):
        calc_weighted_score({}, {})

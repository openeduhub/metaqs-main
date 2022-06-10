import uuid
from unittest import mock
from unittest.mock import MagicMock

import pytest
from elasticsearch_dsl.response import Hit, Response

from app.api.quality_matrix.quality_matrix import (
    all_sources,
    create_empty_entries_search,
    create_properties_search,
    create_sources_search,
    get_properties,
    missing_fields,
    missing_fields_ratio,
    queried_missing_properties,
    source_quality,
)
from app.api.quality_matrix.utils import transpose
from app.core.config import ELASTICSEARCH_URL
from app.elastic.elastic import add_base_match_filters
from app.elastic.search import Search
from app.elastic.utils import connect_to_elastic

DUMMY_UUID = uuid.UUID("3bbfbe37-2351-405f-b142-f62bf187b10f")


@pytest.mark.asyncio
@pytest.mark.skipif(
    condition=ELASTICSEARCH_URL is None, reason="No connection to Elasticsearch"
)
async def test_get_properties():
    await connect_to_elastic()
    data = get_properties()
    assert "ccm:author_freetext" in data


@pytest.mark.asyncio
async def test_get_quality_matrix_no_sources_no_properties():
    with mock.patch(
        "app.api.quality_matrix.quality_matrix.all_sources"
    ) as mocked_get_sourced:
        with mock.patch(
            "app.api.quality_matrix.quality_matrix.get_properties"
        ) as mocked_get_properties:
            mocked_get_properties.return_value = []
            mocked_get_sourced.return_value = {}
            assert await source_quality() == []


@pytest.mark.asyncio
async def test_get_quality_matrix_no_sources():
    with mock.patch(
        "app.api.quality_matrix.quality_matrix.all_sources"
    ) as mocked_get_sourced:
        with mock.patch(
            "app.api.quality_matrix.quality_matrix.get_properties"
        ) as mocked_get_properties:
            mocked_get_properties.return_value = ["dummy_properties"]
            mocked_get_sourced.return_value = {}
            assert await source_quality() == [
                {"metadatum": "dummy_properties", "columns": {}}
            ]


@pytest.mark.asyncio
async def test_get_quality_matrix():
    with mock.patch(
        "app.api.quality_matrix.quality_matrix.all_sources"
    ) as mocked_get_sourced:
        with mock.patch(
            "app.api.quality_matrix.quality_matrix.get_properties"
        ) as mocked_get_properties:
            with mock.patch(
                "app.api.quality_matrix.quality_matrix.queried_missing_properties"
            ) as mocked_all_missing_properties:
                mocked_get_properties.return_value = ["dummy_properties"]
                mocked_get_sourced.return_value = {"dummy_source": 10}
                mocked_response = MagicMock()
                mocked_response.aggregations.to_dict.return_value = {}
                mocked_all_missing_properties.return_value = mocked_response
                assert await source_quality() == [
                    {"metadatum": "dummy_properties", "columns": {}}
                ]

                mocked_response.aggregations.to_dict.return_value = {
                    "dummy_properties": {"doc_count": 5}
                }
                mocked_all_missing_properties.return_value = mocked_response
                assert await source_quality() == [
                    {"metadatum": "dummy_properties", "columns": {"dummy_source": 50.0}}
                ]


def test_get_empty_entries_dummy_entries():
    with mock.patch(
        "app.api.quality_matrix.quality_matrix.Search.execute"
    ) as mocked_execute:
        dummy_response = 3
        mocked_execute.return_value = dummy_response
        assert (
            queried_missing_properties(
                ["dummy_property"],
                search_keyword="dummy_source",
                node_id=DUMMY_UUID,
                match_keyword="",
            )
            == dummy_response
        )


def test_create_empty_entries_search():
    expected_query = {
        "_source": {"includes": ["aggregations"]},
        "aggs": {
            "dummy_property": {
                "missing": {"field": "properties.dummy_property.keyword"}
            }
        },
        "query": {
            "bool": {
                "must": [
                    {"match": {"properties.ccm:replicationsource": "dummy_source"}},
                    {"term": {"path": DUMMY_UUID}},
                    {"match": {"permissions.Read": "GROUP_EVERYONE"}},
                    {"match": {"properties.cm:edu_metadataset": "mds_oeh"}},
                    {"match": {"nodeRef.storeRef.protocol": "workspace"}},
                ]
            }
        },
    }
    assert (
        create_empty_entries_search(
            ["dummy_property"],
            "dummy_source",
            DUMMY_UUID,
            "properties.ccm:replicationsource",
        ).to_dict()
        == expected_query
    )


def test_create_sources_search():
    aggregation_name = "dummy_aggregation"
    expected_query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"permissions.Read": "GROUP_EVERYONE"}},
                    {"match": {"properties.cm:edu_metadataset": "mds_oeh"}},
                    {"match": {"nodeRef.storeRef.protocol": "workspace"}},
                ]
            }
        },
        "aggs": {
            aggregation_name: {
                "terms": {
                    "field": "properties.ccm:replicationsource.keyword",
                    "size": 500_000,
                }
            }
        },
    }
    assert create_sources_search(aggregation_name).to_dict() == expected_query


@pytest.mark.skip(reason="Cannot mock Hit properly,yet. TODO")
def test_sources():
    with mock.patch(
        "app.api.quality_matrix.quality_matrix.Search.execute"
    ) as mocked_execute:
        dummy_count = {"aggregations": {"unique_sources": {"buckets": []}}}
        dummy_hit = Hit({"_source": MagicMock()})
        response = Response(
            "", {"test": "hello", "aggregations": {}, "hits": {"hits": [dummy_hit]}}
        )
        mocked_execute.return_value = response
        assert all_sources() == dummy_count


def test_create_properties_search():
    expected_query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"permissions.Read": "GROUP_EVERYONE"}},
                    {"match": {"properties.cm:edu_metadataset": "mds_oeh"}},
                    {"match": {"nodeRef.storeRef.protocol": "workspace"}},
                ]
            }
        },
        "_source": ["properties"],
    }
    assert create_properties_search().to_dict() == expected_query


def test_add_base_match_filters():
    excpectation = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"permissions.Read": "GROUP_EVERYONE"}},
                    {"match": {"properties.cm:edu_metadataset": "mds_oeh"}},
                    {"match": {"nodeRef.storeRef.protocol": "workspace"}},
                ]
            }
        }
    }

    assert add_base_match_filters(Search()).to_dict() == excpectation


def test_missing_fields_zero_division_error():
    with pytest.raises(ZeroDivisionError):
        missing_fields({"doc_count": 0}, 0, "dummy_source")


def test_missing_fields():
    response = missing_fields({"doc_count": 0}, 10, "dummy_source")
    assert response == {"dummy_source": 100.0}
    response = missing_fields({"doc_count": 5}, 10, "dummy_source")
    assert response == {"dummy_source": 50.0}


def test_missing_fields_ratio():
    response = missing_fields_ratio({"doc_count": 0}, 10)
    assert response == 100
    response = missing_fields_ratio({"doc_count": 5}, 10)
    assert response == 50


def compare_lists_of_dict(expected, actually) -> bool:
    difference = [
        i for i in expected + actually if i not in expected or i not in actually
    ]
    return False if len(difference) > 0 else True


def test_transpose():
    data = [
        {
            "metadatum": "virtual",
            "columns": {
                "00abdb05-6c96-4604-831c-b9846eae7d2d": 13.0,
                "3305f552-c931-4bcc-842b-939c99752bd5": 20.0,
                "35054614-72c8-49b2-9924-7b04c7f3bf71": -10.0,
            },
        }
    ]

    assert compare_lists_of_dict(
        transpose(data),
        [
            {
                "metadatum": "00abdb05-6c96-4604-831c-b9846eae7d2d",
                "columns": {"virtual": 13.0},
            },
            {
                "metadatum": "3305f552-c931-4bcc-842b-939c99752bd5",
                "columns": {"virtual": 20.0},
            },
            {
                "metadatum": "35054614-72c8-49b2-9924-7b04c7f3bf71",
                "columns": {"virtual": -10.0},
            },
        ],
    )

    data = [
        {
            "metadatum": "virtual",
            "columns": {
                "00abdb05-6c96-4604-831c-b9846eae7d2d": 13.0,
                "3305f552-c931-4bcc-842b-939c99752bd5": 20.0,
                "35054614-72c8-49b2-9924-7b04c7f3bf71": -10.0,
            },
        },
        {
            "metadatum": "actually",
            "columns": {
                "00abdb05-6c96-4604-831c-b9846eae7d2d": 20.0,
                "3305f552-c931-4bcc-842b-939c99752bd5": 21.0,
                "35054614-72c8-49b2-9924-7b04c7f3bf71": -1.0,
            },
        },
    ]

    assert compare_lists_of_dict(
        transpose(data),
        [
            {
                "metadatum": "00abdb05-6c96-4604-831c-b9846eae7d2d",
                "columns": {"virtual": 13.0, "actually": 20},
            },
            {
                "metadatum": "3305f552-c931-4bcc-842b-939c99752bd5",
                "columns": {"virtual": 20.0, "actually": 21},
            },
            {
                "metadatum": "35054614-72c8-49b2-9924-7b04c7f3bf71",
                "columns": {"virtual": -10.0, "actually": -1},
            },
        ],
    )

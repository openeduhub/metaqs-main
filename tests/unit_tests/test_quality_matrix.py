from unittest import mock
from unittest.mock import MagicMock

import pytest
from elasticsearch_dsl.response import Hit, Response

from app.api.quality_matrix.quality_matrix import (
    add_base_match_filters,
    all_missing_properties,
    all_sources,
    create_empty_entries_search,
    create_properties_search,
    create_sources_search,
    missing_fields,
    missing_fields_ratio,
    quality_matrix,
)
from app.elastic import Search


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
            assert await quality_matrix() == []


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
            assert await quality_matrix() == [{"metadatum": "dummy_properties"}]


@pytest.mark.asyncio
async def test_get_quality_matrix():
    with mock.patch(
        "app.api.quality_matrix.quality_matrix.all_sources"
    ) as mocked_get_sourced:
        with mock.patch(
            "app.api.quality_matrix.quality_matrix.get_properties"
        ) as mocked_get_properties:
            with mock.patch(
                "app.api.quality_matrix.quality_matrix.all_missing_properties"
            ) as mocked_all_missing_properties:
                mocked_get_properties.return_value = ["dummy_properties"]
                mocked_get_sourced.return_value = {"dummy_source": 10}
                mocked_response = MagicMock()
                mocked_response.aggregations.to_dict.return_value = {}
                mocked_all_missing_properties.return_value = mocked_response
                assert await quality_matrix() == [{"metadatum": "dummy_properties"}]

                mocked_response.aggregations.to_dict.return_value = {
                    "dummy_properties": {"doc_count": 5}
                }
                mocked_all_missing_properties.return_value = mocked_response
                assert await quality_matrix() == [
                    {
                        "metadatum": "dummy_properties",
                        "dummy_source": 50.0,
                    }
                ]


def test_get_empty_entries_dummy_entries():
    with mock.patch(
        "app.api.quality_matrix.quality_matrix.Search.execute"
    ) as mocked_execute:
        dummy_response = 3
        mocked_execute.return_value = dummy_response
        assert (
            all_missing_properties(
                ["dummy_property"], replication_source="dummy_source"
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
                    {"match": {"permissions.Read": "GROUP_EVERYONE"}},
                    {"match": {"properties.cm:edu_metadataset": "mds_oeh"}},
                    {"match": {"nodeRef.storeRef.protocol": "workspace"}},
                ]
            }
        },
    }
    assert (
        create_empty_entries_search(["dummy_property"], "dummy_source").to_dict()
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
                "terms": {"field": "properties.ccm:replicationsource.keyword"}
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

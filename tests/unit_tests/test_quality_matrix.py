from unittest import mock
from unittest.mock import MagicMock

import pytest
from elasticsearch_dsl.response import Response, Hit

from app.crud.quality_matrix import get_quality_matrix, get_empty_entries, create_empty_entries_search, \
    create_non_empty_entries_search, create_sources_search, get_sources


@pytest.mark.asyncio
async def test_get_quality_matrix_no_sources():
    with mock.patch("app.crud.quality_matrix.get_sources") as mocked_get_sourced:
        mocked_get_sourced.return_value = {}
        assert await get_quality_matrix() == {}


@pytest.mark.asyncio
async def test_get_quality_matrix_no_properties():
    with mock.patch("app.crud.quality_matrix.get_sources") as mocked_get_sourced:
        with mock.patch("app.crud.quality_matrix.get_properties") as mocked_get_properties:
            mocked_get_sourced.return_value = {"dummy_source": 10}
            mocked_get_properties.return_value = []
            assert await get_quality_matrix() == {"dummy_source": {}}


@pytest.mark.asyncio
async def test_get_quality_matrix_dummy_property():
    with mock.patch("app.crud.quality_matrix.get_sources") as mocked_get_sourced:
        with mock.patch("app.crud.quality_matrix.get_properties") as mocked_get_properties:
            with mock.patch("app.crud.quality_matrix.get_non_empty_entries") as mocked_get_non_empty_entries:
                with mock.patch("app.crud.quality_matrix.get_empty_entries") as mocked_get_empty_entries:
                    mocked_get_sourced.return_value = {"dummy_source": 10}
                    mocked_get_properties.return_value = ["dummy_property"]
                    mocked_get_non_empty_entries.return_value = 0
                    mocked_get_empty_entries.return_value = 0
                    assert await get_quality_matrix() == {
                        "dummy_source": {
                            "properties.dummy_property": {'empty': 0, 'not_empty': 0, 'total_count': 10}}}


def test_get_empty_entries_dummy_entries():
    with mock.patch("app.crud.quality_matrix.Search.count") as mocked_count:
        dummy_count = 3
        mocked_count.return_value = dummy_count
        assert get_empty_entries("dummy_property", source="dummy_source") == dummy_count


def test_create_empty_entries_search():
    expected_query = {'query': {'bool': {'must': [{'match': {'properties.ccm:replicationsource': 'dummy_source'}},
                                                  {'match': {'properties.dummy_property': ''}},
                                                  {'match': {'permissions.Read': 'GROUP_EVERYONE'}},
                                                  {'match': {'properties.cm:edu_metadataset': 'mds_oeh'}},
                                                  {'match': {'nodeRef.storeRef.protocol': 'workspace'}}]}}}
    assert create_empty_entries_search("dummy_property", "dummy_source").to_dict() == expected_query


def test_create_non_empty_entries_search():
    expected_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "properties.ccm:replicationsource": "dummy_source",
                        },
                    },
                    {'match': {'permissions.Read': 'GROUP_EVERYONE'}},
                    {'match': {'properties.cm:edu_metadataset': 'mds_oeh'}},
                    {'match': {'nodeRef.storeRef.protocol': 'workspace'}}
                ],
                "must_not": [
                    {
                        "match": {
                            f"properties.dummy_property": ""
                        }
                    }
                ]
            }
        }
    }
    assert create_non_empty_entries_search("dummy_property", "dummy_source").to_dict() == expected_query


def test_create_sources_search():
    aggregation_name = "dummy_aggregation"
    expected_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "permissions.Read": "GROUP_EVERYONE"
                        }
                    },
                    {
                        "match": {
                            "properties.cm:edu_metadataset": "mds_oeh"
                        }
                    },
                    {
                        "match": {
                            "nodeRef.storeRef.protocol": "workspace"
                        }
                    }
                ]
            }
        },
        'aggs': {aggregation_name: {'terms': {'field': 'properties.ccm:replicationsource.keyword'}}},
    }
    assert create_sources_search(aggregation_name).to_dict() == expected_query


@pytest.mark.skip(reason="Cannot mock Hit properly,yet. TODO")
def test_get_sources():
    with mock.patch("app.crud.quality_matrix.Search.execute") as mocked_execute:
        dummy_count = {"aggregations": {"unique_sources": {"buckets": []}}}
        dummy_hit = Hit({"_source": MagicMock()})
        response = Response("", {"test": "hello", "aggregations": {}, "hits": {"hits": [dummy_hit]}})
        print(response._d_)
        mocked_execute.return_value = response
        assert get_sources() == dummy_count

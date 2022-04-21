from unittest import mock

import pytest

from app.crud.quality_matrix import get_quality_matrix, get_empty_entries, create_empty_entries_search


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
        assert get_empty_entries("dummy_source", "dummy_property") == dummy_count


def test_create_empty_entries_search():
    expected_query = {'query': {'bool': {'must': [{'match': {'properties.ccm:replicationsource': 'dummy_property'}},
                                                  {'match': {'properties.dummy_source': ''}},
                                                  {'match': {'permissions.Read': 'GROUP_EVERYONE'}},
                                                  {'match': {'properties.cm:edu_metadataset': 'mds_oeh'}},
                                                  {'match': {'nodeRef.storeRef.protocol': 'workspace'}}]}}}
    assert create_empty_entries_search("dummy_source", "dummy_property").to_dict() == expected_query

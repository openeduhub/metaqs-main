from unittest.mock import MagicMock

from elasticsearch_dsl.response import Response

from app.core.config import PORTAL_ROOT_ID
from app.crud.collection import portals_query, processed_portals_query


def test_portal_root():
    assert PORTAL_ROOT_ID == "5e40e372-735c-4b17-bbf7-e827a5702b57"


def test_portals_query():
    query = portals_query()
    expected_query = {'query': {'bool': {'filter': [{'term': {'permissions.Read.keyword': 'GROUP_EVERYONE'}},
                                                    {'term': {'properties.cm:edu_metadataset.keyword': 'mds_oeh'}},
                                                    {'term': {'nodeRef.storeRef.protocol': 'workspace'}},
                                                    {'term': {'type': 'ccm:map'}},
                                                    {'term': {'path': '5e40e372-735c-4b17-bbf7-e827a5702b57'}}]}}}
    assert expected_query == query.to_dict()


def test_processed_portals_query_empty_hits():
    mocked_response = Response(search="", response={})
    mocked_response._search = MagicMock()
    mocked_response._d_ = {"hits": []}
    mocked_response._hits = MagicMock()
    output = processed_portals_query(mocked_response)
    assert output == {}

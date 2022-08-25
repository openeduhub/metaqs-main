from uuid import UUID

from app.api.collections.models import PendingMaterials
from app.api.analytics.background_task import (
    build_pending_materials,
    search_query,
)
from app.core.constants import COLLECTION_NAME_TO_ID
from app.core.models import essential_frontend_properties
from app.elastic.elastic import ResourceType
from tests.conftest import elastic_search_mock


def test_build_pending_materials():
    chemie = UUID(COLLECTION_NAME_TO_ID["Chemie"])

    with elastic_search_mock(resource="build-pending-material"):
        response = build_pending_materials(collection_id=chemie, title="Chemie")

    assert response == PendingMaterials(
        collection_id=chemie,
        # 'Materialien ohne Beschreibungstext'
        description=[UUID("6cc8e664-1bd6-4b75-838c-b4091f96676e")],
        # 'Materialien ohne Bildungsstufe'
        edu_context=[UUID("4ac9e3a1-04b7-44fc-ac6f-94c116eb4b6b")],
        # 'Materialien ohne Zielgruppe'
        intended_end_user_role=[
            UUID("6cc8e664-1bd6-4b75-838c-b4091f96676e"),
            UUID("dd0b4df4-dff2-4519-a018-401c062d2192"),
        ],
        # 'Materialien ohne Kategorie',
        learning_resource_type=[UUID("dd0b4df4-dff2-4519-a018-401c062d2192")],
        # 'Materialien ohne Lizenz'
        license=[UUID("dd0b4df4-dff2-4519-a018-401c062d2192")],
        # 'Materialien ohne Herkunft'
        publisher=[UUID("4ac9e3a1-04b7-44fc-ac6f-94c116eb4b6b")],
        # 'Materialien ohne Fachgebiet'
        taxon_id=[],
        # 'Materialien ohne Titel'
        title=[],
        url=[],  # not used -> empty
    )


def test_search_query_collections():
    query = search_query(resource_type=ResourceType.COLLECTION, path="path")
    query_dict = query.to_dict()

    assert (
        len(query_dict["_source"]["includes"]) == 11
    )  # length of essential properties plus 2
    assert query_dict["_source"]["includes"] == [
        "nodeRef.*",
        "path",
        *essential_frontend_properties,
    ]
    query_dict["_source"] = {}
    assert query_dict == {
        "_source": {},
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"type": "ccm:map"}},
                    {"term": {"path": "5e40e372-735c-4b17-bbf7-e827a5702b57"}},
                ]
            }
        },
    }


def test_search_query_materials():
    query = search_query(
        resource_type=ResourceType.MATERIAL, path="collections.nodeRef.id"
    )
    query_dict = query.to_dict()

    assert (
        len(query_dict["_source"]["includes"]) == 11
    )  # length of essential properties plus 2
    assert query_dict["_source"]["includes"] == [
        "nodeRef.*",
        "collections.nodeRef.id",
        *essential_frontend_properties,
    ]
    query_dict["_source"] = {}
    assert query_dict == {
        "_source": {},
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"type": "ccm:io"}},
                    {
                        "term": {
                            "collections.path.keyword": "5e40e372-735c-4b17-bbf7-e827a5702b57"
                        }
                    },
                ]
            }
        },
    }
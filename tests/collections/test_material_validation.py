from uuid import UUID

from app.api.collections.material_validation import (
    get_material_validation,
    IncompleteMaterials,
    MaterialValidationResponse,
)
from app.core.constants import COLLECTION_NAME_TO_ID
from app.elastic.utils import connect_to_elastic
from tests.conftest import elastic_search_mock


def test_get_material_validation():
    connect_to_elastic()
    chemie = UUID(COLLECTION_NAME_TO_ID["Chemie"])

    # with elastic_search_mock(resource="material-validation"):
    response = get_material_validation(collection_id=chemie)

    assert response == MaterialValidationResponse(
        collection_id=chemie,
        missing_materials=[
            IncompleteMaterials(
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
        ],
    )

from enum import Enum

from elasticsearch_dsl.query import Query

from app.core.models import ElasticResourceAttribute, forbidden_licenses
from app.elastic.dsl import qboolor, qnotexists, qterms


class ResourceType(str, Enum):
    COLLECTION = "COLLECTION"
    MATERIAL = "MATERIAL"


def query_missing_material_license() -> Query:
    qfield = ElasticResourceAttribute.LICENSES
    return qboolor(
        [
            qterms(
                qfield=qfield,
                values=forbidden_licenses,
            ),
            qnotexists(qfield=qfield),
        ]
    )

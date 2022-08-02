import uuid
from enum import Enum

from elasticsearch_dsl.query import Query, Term

from app.core.models import ElasticResourceAttribute
from app.elastic.dsl import qbool, qboolor, qnotexists, qterm, qterms


class ResourceType(str, Enum):
    COLLECTION = "COLLECTION"
    MATERIAL = "MATERIAL"


type_filter = {
    ResourceType.COLLECTION: [
        Term(**{ElasticResourceAttribute.TYPE.path: "ccm:map"}),
    ],
    ResourceType.MATERIAL: [
        Term(**{ElasticResourceAttribute.TYPE.path: "ccm:io"}),
    ],
}


def query_many(resource_type: ResourceType, node_id: uuid.UUID = None) -> Query:
    qfilter = [*type_filter[resource_type]]
    if node_id:
        if resource_type is ResourceType.COLLECTION:
            qfilter.append(qterm(qfield=ElasticResourceAttribute.PATH, value=node_id))
        elif resource_type is ResourceType.MATERIAL:
            qfilter.append(
                qterm(qfield=ElasticResourceAttribute.COLLECTION_PATH, value=node_id)
            )

    return qbool(filter=qfilter)


def query_missing_material_license() -> Query:
    qfield = ElasticResourceAttribute.LICENSES
    return qboolor(
        [
            qterms(
                qfield=qfield,
                values=["UNTERRICHTS_UND_LEHRMEDIEN", "NONE", ""],
            ),
            qnotexists(qfield=qfield),
        ]
    )

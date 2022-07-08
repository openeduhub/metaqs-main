from enum import Enum
from uuid import UUID

from elasticsearch_dsl.query import Query

from app.api.score.models import LearningMaterialAttribute
from app.elastic.dsl import qbool, qboolor, qnotexists, qterm, qterms
from app.models import CollectionAttribute, ElasticResourceAttribute


class ResourceType(str, Enum):
    COLLECTION = "COLLECTION"
    MATERIAL = "MATERIAL"


type_filter = {
    ResourceType.COLLECTION: [
        qterm(qfield=ElasticResourceAttribute.TYPE, value="ccm:map"),
    ],
    ResourceType.MATERIAL: [
        qterm(qfield=ElasticResourceAttribute.TYPE, value="ccm:io"),
    ],
}


def query_many(resource_type: ResourceType, node_id: UUID = None) -> Query:
    qfilter = [*type_filter[resource_type]]
    if node_id:
        if resource_type is ResourceType.COLLECTION:
            qfilter.append(qterm(qfield=CollectionAttribute.PATH, value=node_id))
        elif resource_type is ResourceType.MATERIAL:
            qfilter.append(
                qterm(qfield=LearningMaterialAttribute.COLLECTION_PATH, value=node_id)
            )

    return qbool(filter=qfilter)


def query_collections(node_id: UUID = None) -> Query:
    return query_many(ResourceType.COLLECTION, node_id=node_id)


def query_materials(node_id: UUID = None) -> Query:
    return query_many(ResourceType.MATERIAL, node_id=node_id)


def query_missing_material_license() -> Query:
    qfield = LearningMaterialAttribute.LICENSES
    return qboolor(
        [
            qterms(
                qfield=qfield,
                values=["UNTERRICHTS_UND_LEHRMEDIEN", "NONE", ""],
            ),
            qnotexists(qfield=qfield),
        ]
    )

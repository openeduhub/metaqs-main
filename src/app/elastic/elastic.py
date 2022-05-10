from enum import Enum
from uuid import UUID

from elasticsearch_dsl.query import Q, Query

from app.api.score.models import CollectionAttribute, LearningMaterialAttribute
from app.elastic.dsl import afilter, amissing, qbool, qboolor, qnotexists, qterm, qterms
from app.models.elastic import ElasticResourceAttribute


class ResourceType(str, Enum):
    COLLECTION = "COLLECTION"
    MATERIAL = "MATERIAL"


base_filter = [
    qterm(qfield=ElasticResourceAttribute.PERMISSION_READ, value="GROUP_EVERYONE"),
    qterm(qfield=ElasticResourceAttribute.EDU_METADATASET, value="mds_oeh"),
    qterm(qfield=ElasticResourceAttribute.PROTOCOL, value="workspace"),
]

# TODO Combine base match and base filter
base_match_filter = [
    {"match": {"permissions.Read": "GROUP_EVERYONE"}},
    {"match": {"properties.cm:edu_metadataset": "mds_oeh"}},
    {"match": {"nodeRef.storeRef.protocol": "workspace"}},
]

type_filter = {
    ResourceType.COLLECTION: [
        qterm(qfield=ElasticResourceAttribute.TYPE, value="ccm:map"),
    ],
    ResourceType.MATERIAL: [
        qterm(qfield=ElasticResourceAttribute.TYPE, value="ccm:io"),
    ],
}


def query_many(resource_type: ResourceType, ancestor_id: UUID = None) -> Query:
    qfilter = [*base_filter, *type_filter[resource_type]]
    if ancestor_id:
        if resource_type is ResourceType.COLLECTION:
            qfilter.append(qterm(qfield=CollectionAttribute.PATH, value=ancestor_id))
        elif resource_type is ResourceType.MATERIAL:
            qfilter.append(
                qterm(
                    qfield=LearningMaterialAttribute.COLLECTION_PATH, value=ancestor_id
                )
            )

    return qbool(filter=qfilter)


def query_collections(ancestor_id: UUID = None) -> Query:
    return query_many(ResourceType.COLLECTION, ancestor_id=ancestor_id)


def query_materials(ancestor_id: UUID = None) -> Query:
    return query_many(ResourceType.MATERIAL, ancestor_id=ancestor_id)


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


def field_names_used_for_score_calculation(properties: dict) -> list[str]:
    values = []
    for value in properties.values():
        value = list(list(value.to_dict().values())[0].values())[0]
        if isinstance(value, dict):
            value = list(value.keys())[0]

        value.replace(".keyword", "")
        if value != "should":
            values += [value]
    return values


aggs_collection_validation = {
    "missing_title": amissing(qfield=CollectionAttribute.TITLE),
    "short_title": afilter(Q("range", char_count_title={"gt": 0, "lt": 5})),
    "missing_keywords": amissing(qfield=CollectionAttribute.KEYWORDS),
    "few_keywords": afilter(Q("range", token_count_keywords={"gt": 0, "lt": 3})),
    "missing_description": amissing(qfield=CollectionAttribute.DESCRIPTION),
    "short_description": afilter(
        Q("range", char_count_description={"gt": 0, "lt": 30})
    ),
    "missing_edu_context": amissing(qfield=CollectionAttribute.EDU_CONTEXT),
}

aggs_material_validation = {
    "missing_title": amissing(qfield=LearningMaterialAttribute.TITLE),
    "missing_keywords": amissing(qfield=LearningMaterialAttribute.KEYWORDS),
    "missing_subjects": amissing(qfield=LearningMaterialAttribute.SUBJECTS),
    "missing_description": amissing(qfield=LearningMaterialAttribute.DESCRIPTION),
    "missing_license": afilter(query=query_missing_material_license()),
    "missing_edu_context": amissing(qfield=LearningMaterialAttribute.EDU_CONTEXT),
    "missing_ads_qualifier": amissing(qfield=LearningMaterialAttribute.CONTAINS_ADS),
    "missing_material_type": amissing(
        qfield=LearningMaterialAttribute.LEARNINGRESOURCE_TYPE
    ),
    "missing_object_type": amissing(qfield=LearningMaterialAttribute.OBJECT_TYPE),
}

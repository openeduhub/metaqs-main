from enum import Enum
from typing import Optional
from uuid import UUID

from elasticsearch_dsl.aggs import Agg
from elasticsearch_dsl.query import Q, Query

from app.core.config import ELASTIC_MAX_SIZE
from app.elastic import (
    acomposite,
    afilter,
    amissing,
    aterms,
    qbool,
    qboolor,
    qmatch,
    qnotexists,
    qsimplequerystring,
    qterm,
    qterms,
)
from app.models.collection import CollectionAttribute
from app.models.elastic import ElasticResourceAttribute
from app.models.learning_material import LearningMaterialAttribute

MATERIAL_TYPES_MAP_EN_DE = {
    "other web resource": "Andere Web Ressource",
    "other asset type": "Anderer Ressourcentyp",
    "other": "Anderes Material",
    "application": "Anwendung/Software",
    "worksheet": "Arbeitsblatt",
    "audio": "Audio",
    "audiovisual medium": "Audiovisuelles Medium",
    "image": "Bild",
    "data": "Daten",
    "exploration": "Entdeckendes Lernen",
    "experiment": "Experiment",
    "case_study": "Fallstudie",
    "glossary": "Glossar",
    "guide": "Handbuch",
    "map": "Karte",
    "course": "Kurs",
    "assessment": "Lernkontrolle",
    "educational Game": "Lernspiel",
    "model": "Modell",
    "open activity": "Offene Aktivität",
    "presentation": "Präsentation",
    "reference": "Primärmaterial/Quelle",
    "project": "Projekt",
    "broadcast": "Radio/TV",
    "enquiry-oriented activity": "Recherche-Auftrag",
    "role play": "Rollenspiel",
    "simulation": "Simulation",
    "text": "Text",
    "drill and practice": "Übung",
    "teaching module": "Unterrichtsbaustein",
    "lesson plan": "Unterrichtsplanung",
    "demonstration": "Veranschaulichung",
    "video": "Video",
    "weblog": "Weblog",
    "web page": "Website",
    "tool": "Werkzeug",
    "wiki": "Wiki",
}


class ResourceType(str, Enum):
    COLLECTION = "COLLECTION"
    MATERIAL = "MATERIAL"


base_filter = [
    qterm(qfield=ElasticResourceAttribute.PERMISSION_READ, value="GROUP_EVERYONE"),
    qterm(qfield=ElasticResourceAttribute.EDU_METADATASET, value="mds_oeh"),
    qterm(qfield=ElasticResourceAttribute.PROTOCOL, value="workspace"),
]

base_match_filter = [
    qmatch(qfield=ElasticResourceAttribute.PERMISSION_READ, value="GROUP_EVERYONE"),
    qmatch(qfield=ElasticResourceAttribute.EDU_METADATASET, value="mds_oeh"),
    qmatch(qfield=ElasticResourceAttribute.PROTOCOL, value="workspace"),
]

type_filter = {
    ResourceType.COLLECTION: [
        qterm(qfield=ElasticResourceAttribute.TYPE, value="ccm:map"),
    ],
    ResourceType.MATERIAL: [
        qterm(qfield=ElasticResourceAttribute.TYPE, value="ccm:io"),
    ],
}

replication_source_filter = {"REPLICATION_SOURCE": [
    qterm(qfield=ElasticResourceAttribute.REPLICATION_SOURCE_DE, value="ccm:replicationsource"),
]}


# TODO: eliminate; use query_many instead
def get_many_base_query(
        resource_type: ResourceType,
        ancestor_id: Optional[UUID] = None,
) -> dict:
    query_dict = {"filter": [*base_filter, *type_filter[resource_type]]}

    if ancestor_id:
        prefix = "collections." if resource_type == ResourceType.MATERIAL else ""
        query_dict["should"] = [
            qmatch(**{f"{prefix}path": ancestor_id}),
            qmatch(**{f"{prefix}nodeRef.id": ancestor_id}),
        ]
        query_dict["minimum_should_match"] = 1

    return query_dict


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


def search_materials(query_str: str) -> Query:
    return qsimplequerystring(
        query=query_str,
        qfields=[
            LearningMaterialAttribute.TITLE,
            LearningMaterialAttribute.KEYWORDS,
            LearningMaterialAttribute.DESCRIPTION,
            LearningMaterialAttribute.CONTENT_FULLTEXT,
            LearningMaterialAttribute.SUBJECTS_DE,
            LearningMaterialAttribute.LEARNINGRESOURCE_TYPE_DE,
            LearningMaterialAttribute.EDU_CONTEXT_DE,
            LearningMaterialAttribute.EDUENDUSERROLE_DE,
        ],
        default_operator="and",
    )


def agg_materials_by_collection(size: int = ELASTIC_MAX_SIZE) -> Agg:
    return acomposite(
        sources=[
            {
                "noderef_id": aterms(
                    qfield=LearningMaterialAttribute.COLLECTION_NODEREF_ID
                )
            }
        ],
        size=size,
    )


def agg_material_types(size: int = ELASTIC_MAX_SIZE) -> Agg:
    return aterms(
        qfield=LearningMaterialAttribute.LEARNINGRESOURCE_TYPE,
        missing="N/A",
        size=size,
    )


def agg_material_types_by_collection(size: int = ELASTIC_MAX_SIZE) -> Agg:
    return acomposite(
        sources=[
            # {"material_type": aterms(qfield="material_type")},
            {
                "material_type": aterms(
                    qfield=LearningMaterialAttribute.LEARNINGRESOURCE_TYPE,
                    missing_bucket=True,
                )
            },
            {
                "noderef_id": aterms(
                    qfield=LearningMaterialAttribute.COLLECTION_NODEREF_ID
                )
            },
        ],
        size=size,
    )


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

# TODO Remove
def agg_material_score(size: int = ELASTIC_MAX_SIZE) -> Agg:
    agg = aterms(qfield=LearningMaterialAttribute.COLLECTION_NODEREF_ID, size=size)

    for name, _agg in aggs_material_validation.items():
        agg.bucket(name, _agg)

    return agg

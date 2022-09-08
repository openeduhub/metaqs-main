from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from app.elastic.attributes import ElasticResourceAttribute


@dataclass(frozen=True)
class SortNode:
    __slots__ = "title", "path", "children"
    title: str
    path: Optional[ElasticResourceAttribute]
    children: list[SortNode]


metadata_hierarchy: list[SortNode] = [
    SortNode(
        title="Beschreibendes",
        children=[
            SortNode(path=ElasticResourceAttribute.COVER, children=[], title="cover"),
            SortNode(
                path=ElasticResourceAttribute.COLLECTION_SHORT_TITLE,
                children=[],
                title="short_title",
            ),
            SortNode(path=ElasticResourceAttribute.TITLE, children=[], title="title"),
            SortNode(
                path=ElasticResourceAttribute.DESCRIPTION,
                children=[],
                title="description",
            ),
            SortNode(path=ElasticResourceAttribute.STATUS, children=[], title="status"),
            SortNode(path=ElasticResourceAttribute.WWW_URL, children=[], title="url"),
            SortNode(path=ElasticResourceAttribute.LANGUAGE, children=[], title="language"),
        ],
        path=None,
    ),
    SortNode(
        title="Typisierung",
        children=[
            SortNode(
                path=ElasticResourceAttribute.LEARNINGRESOURCE_TYPE,
                children=[],
                title="learning_resource_type",
            ),
            SortNode(path=ElasticResourceAttribute.MIMETYPE, children=[], title="mimetype"),
            SortNode(
                path=ElasticResourceAttribute.EDITORIAL_FILE_TYPE,
                children=[],
                title="file_type",
            ),
            SortNode(
                path=ElasticResourceAttribute.EDU_CONTEXT,
                children=[],
                title="edu_context",
            ),
            SortNode(path=ElasticResourceAttribute.AGE_RANGE, children=[], title="age_range"),
            SortNode(path=ElasticResourceAttribute.FSK, children=[], title="fsk"),
            SortNode(path=ElasticResourceAttribute.SUBJECTS, children=[], title="taxon_id"),
            SortNode(
                path=ElasticResourceAttribute.CLASSIFICATION_KEYWORD,
                children=[],
                title="classification",
            ),
            SortNode(
                path=ElasticResourceAttribute.KEYWORDS,
                children=[],
                title="general_keywords",
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Pädagogisch",
        children=[
            SortNode(
                path=ElasticResourceAttribute.EDU_ENDUSERROLE_DE,
                children=[],
                title="intended_end_user_role",
            ),
            SortNode(
                path=ElasticResourceAttribute.CURRICULUM,
                children=[],
                title="curriculum",
            ),
            SortNode(
                path=ElasticResourceAttribute.LEARNING_TIME,
                children=[],
                title="learning_time",
            ),
            SortNode(path=ElasticResourceAttribute.DURATION, children=[], title="duration"),
            SortNode(
                path=ElasticResourceAttribute.LANGUAGE_TARGET,
                children=[],
                title="language_target",
            ),
            SortNode(
                path=ElasticResourceAttribute.COMPETENCE,
                children=[],
                title="competence",
            ),
            SortNode(
                path=ElasticResourceAttribute.COMPETENCE_REQUIREMENTS,
                children=[],
                title="competence_requirements",
            ),
            SortNode(
                path=ElasticResourceAttribute.COMPETENCE_CHECK,
                children=[],
                title="mimetype",
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Rechtliche Unauffälligkeit",
        children=[
            SortNode(
                path=ElasticResourceAttribute.QUALITY_CRIMINAL_LAW,
                children=[],
                title="oeh_quality_criminal_law",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_COPYRIGHT_LAW,
                children=[],
                title="oeh_quality_copyright_law",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_PROTECTION_OF_MINORS,
                children=[],
                title="oeh_quality_protection_of_minors",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_PERSONAL_LAW,
                children=[],
                title="oeh_quality_personal_law",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_DATA_PRIVACY,
                children=[],
                title="oeh_quality_data_privacy",
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Qualität",
        children=[
            SortNode(
                path=ElasticResourceAttribute.QUALITY_CORRECTNESS,
                children=[],
                title="oeh_quality_correctness",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_CURRENTNESS,
                children=[],
                title="oeh_quality_currentness",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_NEUTRALNESS,
                children=[],
                title="oeh_quality_neutralness",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_LANGUAGE,
                children=[],
                title="oeh_quality_language",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_MEDIAL,
                children=[],
                title="oeh_quality_medial",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_DIAGNOSTICS,
                children=[],
                title="oeh_quality_didactics",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_TRANSPARENTNESS,
                children=[],
                title="oeh_quality_transparentness",
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Zugänglichkeit",
        children=[
            SortNode(
                path=ElasticResourceAttribute.ACCESSIBILITY_OPEN,
                children=[],
                title="oeh_accessibility_open",
            ),
            SortNode(
                path=ElasticResourceAttribute.ACCESSIBILITY_FIND,
                children=[],
                title="oeh_accessibility_find",
            ),
            SortNode(
                path=ElasticResourceAttribute.ACCESSIBILITY_SUMMARY,
                children=[],
                title="accessibilitySummary",
            ),
            SortNode(
                path=ElasticResourceAttribute.USABILITY,
                children=[],
                title="oeh_usability",
            ),
            SortNode(
                path=ElasticResourceAttribute.INTEROPERABILITY,
                children=[],
                title="oeh_interoperability",
            ),
            SortNode(path=ElasticResourceAttribute.PRICE, children=[], title="price"),
            SortNode(
                path=ElasticResourceAttribute.LOGIN,
                children=[],
                title="oeh_quality_login",
            ),
            SortNode(
                path=ElasticResourceAttribute.ACCESSIBILITY_SECURITY,
                children=[],
                title="oeh_accessibility_security",
            ),
            SortNode(
                path=ElasticResourceAttribute.LICENSED_UNTIL,
                children=[],
                title="license_to",
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Lizenz, Quelle, Mitwirkende",
        children=[
            SortNode(path=ElasticResourceAttribute.LICENSES, children=[], title="license"),
            SortNode(
                path=ElasticResourceAttribute.AUTHOR,
                children=[],
                title="author_freetext",
            ),
            SortNode(
                path=ElasticResourceAttribute.EDITORIAL_PUBLISHER,
                children=[],
                title="editorial_publisher",
            ),
            SortNode(
                path=ElasticResourceAttribute.PUBLISHED,
                children=[],
                title="published_date",
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Entstehung des Inhaltes",
        children=[
            SortNode(
                path=ElasticResourceAttribute.PUBLISHING,
                children=[],
                title="publishing",
            ),
            SortNode(path=ElasticResourceAttribute.CREATED, children=[], title="created"),
            SortNode(path=ElasticResourceAttribute.MODIFIED, children=[], title="modified"),
            SortNode(path=ElasticResourceAttribute.VERSION, children=[], title="versionLabel"),
            SortNode(path=ElasticResourceAttribute.PUBLISHER, children=[], title="publisher"),
        ],
        path=None,
    ),
    SortNode(
        title="Identifier und Signaturen",
        children=[
            SortNode(path=ElasticResourceAttribute.SYSTEM_ID, children=[], title="node_uuid"),
            SortNode(
                path=ElasticResourceAttribute.PUBLISHER_HANDLE,
                children=[],
                title="published_handle_id",
            ),
            SortNode(
                path=ElasticResourceAttribute.SIGNATURES,
                children=[],
                title="oeh_signatures",
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Nutzung und Bewertung",
        children=[
            SortNode(
                path=ElasticResourceAttribute.FEEDBACK,
                children=[],
                title="feedback_comment",
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Erschließung und Kuratierung",
        children=[
            SortNode(
                path=ElasticResourceAttribute.METADATA_CONTRIBUTER_CREATOR,
                children=[],
                title="creator",
            ),
            SortNode(
                path=ElasticResourceAttribute.METADATA_CONTRIBUTER_PROVIDER,
                children=[],
                title="provider",
            ),
            SortNode(
                path=ElasticResourceAttribute.METADATA_CONTRIBUTER_VALIDATOR,
                children=[],
                title="validator",
            ),
        ],
        path=None,
    ),
]

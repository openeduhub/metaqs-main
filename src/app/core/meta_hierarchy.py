import functools

from fastapi import HTTPException

from app.core.config import METADATASET_URL
from app.core.logging import logger
from app.elastic.attributes import ElasticResourceAttribute


METADATA_HIERARCHY: dict[str, list[tuple[ElasticResourceAttribute, str]]] = {
    "Beschreibendes": [
        (ElasticResourceAttribute.COVER, "cover"),
        (ElasticResourceAttribute.COLLECTION_SHORT_TITLE, "short_title"),
        (ElasticResourceAttribute.TITLE, "title"),
        (ElasticResourceAttribute.DESCRIPTION, "description"),
        (ElasticResourceAttribute.STATUS, "status"),
        (ElasticResourceAttribute.WWW_URL, "url"),
        (ElasticResourceAttribute.LANGUAGE, "language"),
    ],
    "Typisierung": [
        (ElasticResourceAttribute.LEARNINGRESOURCE_TYPE, "learning_resource_type"),
        (ElasticResourceAttribute.MIMETYPE, "mimetype"),
        (ElasticResourceAttribute.EDITORIAL_FILE_TYPE, "file_type"),
        (ElasticResourceAttribute.EDU_CONTEXT, "edu_context"),
        (ElasticResourceAttribute.AGE_RANGE, "age_range"),
        (ElasticResourceAttribute.FSK, "fsk"),
        (ElasticResourceAttribute.SUBJECTS, "taxon_id"),
        (ElasticResourceAttribute.CLASSIFICATION_KEYWORD, "classification"),
        (ElasticResourceAttribute.KEYWORDS, "general_keywords"),
    ],
    "Pädagogisch": [
        (ElasticResourceAttribute.EDU_ENDUSERROLE, "intended_end_user_role"),
        (ElasticResourceAttribute.CURRICULUM, "curriculum"),
        (ElasticResourceAttribute.LEARNING_TIME, "learning_time"),
        (ElasticResourceAttribute.DURATION, "duration"),
        (ElasticResourceAttribute.LANGUAGE_TARGET, "language_target"),
        (ElasticResourceAttribute.COMPETENCE, "competence"),
        (ElasticResourceAttribute.COMPETENCE_REQUIREMENTS, "competence_requirements"),
        (ElasticResourceAttribute.COMPETENCE_CHECK, "competence_check"),
    ],
    "Rechtliche Unauffälligkeit": [
        (ElasticResourceAttribute.QUALITY_CRIMINAL_LAW, "oeh_quality_criminal_law"),
        (ElasticResourceAttribute.QUALITY_COPYRIGHT_LAW, "oeh_quality_copyright_law"),
        (ElasticResourceAttribute.QUALITY_PROTECTION_OF_MINORS, "oeh_quality_protection_of_minors"),
        (ElasticResourceAttribute.QUALITY_PERSONAL_LAW, "oeh_quality_personal_law"),
        (ElasticResourceAttribute.QUALITY_DATA_PRIVACY, "oeh_quality_data_privacy"),
    ],
    "Qualität": [
        (ElasticResourceAttribute.QUALITY_CORRECTNESS, "oeh_quality_correctness"),
        (ElasticResourceAttribute.QUALITY_CURRENTNESS, "oeh_quality_currentness"),
        (ElasticResourceAttribute.QUALITY_NEUTRALNESS, "oeh_quality_neutralness"),
        (ElasticResourceAttribute.QUALITY_LANGUAGE, "oeh_quality_language"),
        (ElasticResourceAttribute.QUALITY_MEDIAL, "oeh_quality_medial"),
        (ElasticResourceAttribute.QUALITY_DIAGNOSTICS, "oeh_quality_didactics"),
        (ElasticResourceAttribute.QUALITY_TRANSPARENTNESS, "oeh_quality_transparentness"),
    ],
    "Zugänglichkeit": [
        (ElasticResourceAttribute.ACCESSIBILITY_OPEN, "oeh_accessibility_open"),
        (ElasticResourceAttribute.ACCESSIBILITY_FIND, "oeh_accessibility_find"),
        (ElasticResourceAttribute.ACCESSIBILITY_SUMMARY, "accessibilitySummary"),
        (ElasticResourceAttribute.USABILITY, "oeh_usability"),
        (ElasticResourceAttribute.INTEROPERABILITY, "oeh_interoperability"),
        (ElasticResourceAttribute.PRICE, "price"),
        (ElasticResourceAttribute.LOGIN, "oeh_quality_login"),
        (ElasticResourceAttribute.ACCESSIBILITY_SECURITY, "oeh_accessibility_security"),
        (ElasticResourceAttribute.LICENSED_UNTIL, "license_to"),
    ],
    "Lizenz, Quelle, Mitwirkende": [
        (ElasticResourceAttribute.LICENSES, "license"),
        (ElasticResourceAttribute.AUTHOR, "author_freetext"),
        (ElasticResourceAttribute.EDITORIAL_PUBLISHER, "editorial_publisher"),
        (ElasticResourceAttribute.PUBLISHED, "published_date"),
    ],
    "Entstehung des Inhaltes": [
        (ElasticResourceAttribute.PUBLISHING, "publishing"),
        (ElasticResourceAttribute.CREATED, "created"),
        (ElasticResourceAttribute.MODIFIED, "modified"),
        (ElasticResourceAttribute.VERSION, "versionLabel"),
        (ElasticResourceAttribute.PUBLISHER, "publisher"),
    ],
    "Identifier und Signaturen": [
        (ElasticResourceAttribute.SYSTEM_ID, "node_uuid"),
        (ElasticResourceAttribute.PUBLISHER_HANDLE, "published_handle_id"),
        (ElasticResourceAttribute.SIGNATURES, "oeh_signatures"),
    ],
    "Nutzung und Bewertung": [
        (ElasticResourceAttribute.FEEDBACK, "feedback_comment"),
    ],
    "Erschließung und Kuratierung": [
        (ElasticResourceAttribute.METADATA_CONTRIBUTER_CREATOR, "creator"),
        (ElasticResourceAttribute.METADATA_CONTRIBUTER_PROVIDER, "provider"),
        (ElasticResourceAttribute.METADATA_CONTRIBUTER_VALIDATOR, "validator"),
    ],
}


# Make sure the ids (second part of above tuples) are unique.
def _ids() -> list[str]:
    return [t[1] for fields in METADATA_HIERARCHY.values() for t in fields]


assert len(set(_ids())) == len(_ids()), "duplicate ids for different metadata fields"


@functools.cache
def load_metadataset() -> dict:
    """
    Load the MetaDataSet from EDU-sharing.
    See https://redaktion-staging.openeduhub.net/edu-sharing/swagger/#/MDS%20v1/getMetadataSet for more details.
    """
    import httpx

    logger.info(f"Loading MetaDataSet from {METADATASET_URL}")
    response = httpx.get(url=METADATASET_URL)
    if response.status_code != 200:
        logger.exception(f"Failed to load MetaDataSet: {response.status_code}, {response.text}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to load MetaDataSet from EDU-sharing: {METADATASET_URL}. Received: {response.status_code}.",
        )
    return response.json()

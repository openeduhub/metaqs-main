import contextlib
import json
import os
import uuid
import datetime
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

from app.api.collections.tree import Tree
from app.api.collections.quality_matrix import (
    QualityMatrix,
    QualityMatrixRow,
    QualityMatrixHeader,
    quality_backup,
    past_quality_matrix,
)
from app.api.collections.quality_matrix import _replication_source_quality_matrix
from app.api.collections.quality_matrix import _collection_quality_matrix
from app.api.collections.quality_matrix import timestamps
from app.core.constants import COLLECTION_NAME_TO_ID
from tests.conftest import elastic_search_mock


@contextlib.contextmanager
def edusharing_mock():
    """Avoid querrying the metadata set from edusharing during tests."""
    with open(Path(__file__).parent.parent / "resources" / "edu-sharing-metadataset.json", "r") as f:
        mds = json.load(f)

    def the_mock() -> dict[str, str]:
        return mds

    with mock.patch("app.api.collections.quality_matrix.load_metadataset", the_mock):
        yield


def test_quality_matrix_history(tmpdir):
    os.chdir(tmpdir)
    from app.db.tasks import (
        session_maker,
    )  # import only after changedir to create the database in the temporary directory

    matrix_mock = QualityMatrix(
        columns=[QualityMatrixHeader(id="column-id", label="column-label", alt_label="alt-column-label", level=0)],
        rows=[
            QualityMatrixRow(
                meta=QualityMatrixHeader(id="row-id", label="row-label", alt_label="alt-row-label", level=0),
                counts={"column-id": 1},
                total=1,
            )
        ],
    )

    def mock_matrix(node, mode) -> QualityMatrix:
        return matrix_mock

    node_id = uuid.UUID(COLLECTION_NAME_TO_ID["Chemie"])
    timestamp = datetime.datetime(year=2022, month=10, day=22, hour=10, minute=10, second=0)
    with (
        mock.patch("app.api.collections.quality_matrix.quality_matrix", mock_matrix),
        mock.patch("app.api.collections.quality_matrix.tree", MagicMock(title="title", id=node_id)),
        session_maker().context_session() as session,
    ):
        # save quality matrices for all collections and both modes
        quality_backup(session, timestamp=timestamp)
        # saving the same quality matrix should be a noop, as the integrity error should be ignored.
        quality_backup(session, timestamp=timestamp)

        # check that timestamps are loaded correctly
        timestamp, *other = timestamps(session, mode="replication-source", node_id=node_id)
        assert len(other) == 0, "there should be exactly one entry per mode and collection"
        (count,) = session.execute("select count(*) from timeline").first()
        assert count == len(COLLECTION_NAME_TO_ID) * 2, "there should be two entries per collection"

        # check that we can load a quality matrix by timestamp, mode and collection
        matrix = past_quality_matrix(session, timestamp=timestamp, mode="replication-source", collection_id=node_id)
        assert isinstance(matrix, QualityMatrix)

        # check that this is equal to what we mocked above
        assert matrix == matrix_mock


def test_replication_source_quality_matrix():
    collection = Tree(
        node_id=uuid.UUID("4940d5da-9b21-4ec0-8824-d16e0409e629"),
        title="root",
        level=0,
        parent_id=None,
        children=[
            Tree(
                node_id=uuid.UUID("481c9ce1-7f72-4598-a326-7dba785a065d"),
                title="child1",
                parent_id=uuid.UUID("4940d5da-9b21-4ec0-8824-d16e0409e629"),
                children=[],
                level=1,
            ),
            Tree(
                node_id=uuid.UUID("9b7299f9-31f5-477d-b10e-18a465295bdd"),
                title="child2",
                parent_id=uuid.UUID("4940d5da-9b21-4ec0-8824-d16e0409e629"),
                children=[],
                level=1,
            ),
        ],
    )
    with elastic_search_mock("quality-matrix-replication-source"), edusharing_mock():
        result = _replication_source_quality_matrix(collection=collection)
        assert result == QualityMatrix(
            columns=[
                QualityMatrixHeader(id="Beschreibendes", label="Beschreibendes", alt_label=None, level=0),
                QualityMatrixHeader(id="cover", label="preview", alt_label="preview", level=1),
                QualityMatrixHeader(
                    id="short_title", label="ccm:collectionshorttitle", alt_label="ccm:collectionshorttitle", level=1
                ),
                QualityMatrixHeader(id="title", label="cclom:title", alt_label="cclom:title", level=1),
                QualityMatrixHeader(
                    id="description", label="cclom:general_description", alt_label="cclom:general_description", level=1
                ),
                QualityMatrixHeader(id="status", label="cclom:status", alt_label="cclom:status", level=1),
                QualityMatrixHeader(id="url", label="ccm:wwwurl", alt_label="ccm:wwwurl", level=1),
                QualityMatrixHeader(
                    id="language", label="cclom:general_language", alt_label="cclom:general_language", level=1
                ),
                QualityMatrixHeader(id="Typisierung", label="Typisierung", alt_label=None, level=0),
                QualityMatrixHeader(id="learning_resource_type", label="ccm:oeh_lrt", alt_label="ccm:oeh_lrt", level=1),
                QualityMatrixHeader(id="mimetype", label="mimetype", alt_label="mimetype", level=1),
                QualityMatrixHeader(
                    id="file_type", label="Datei-/Editorformat", alt_label="virtual:editorial_file_type", level=1
                ),
                QualityMatrixHeader(
                    id="edu_context", label="ccm:educationalcontext", alt_label="ccm:educationalcontext", level=1
                ),
                QualityMatrixHeader(
                    id="age_range",
                    label="ccm:educationaltypicalagerange",
                    alt_label="ccm:educationaltypicalagerange",
                    level=1,
                ),
                QualityMatrixHeader(id="fsk", label="ccm:fskRating", alt_label="ccm:fskRating", level=1),
                QualityMatrixHeader(id="taxon_id", label="ccm:taxonid", alt_label="ccm:taxonid", level=1),
                QualityMatrixHeader(
                    id="classification",
                    label="cclom:classification_keyword",
                    alt_label="cclom:classification_keyword",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="general_keywords", label="cclom:general_keyword", alt_label="cclom:general_keyword", level=1
                ),
                QualityMatrixHeader(id="Pädagogisch", label="Pädagogisch", alt_label=None, level=0),
                QualityMatrixHeader(
                    id="intended_end_user_role",
                    label="ccm:educationalintendedenduserrole",
                    alt_label="ccm:educationalintendedenduserrole",
                    level=1,
                ),
                QualityMatrixHeader(id="curriculum", label="ccm:curriculum", alt_label="ccm:curriculum", level=1),
                QualityMatrixHeader(
                    id="learning_time",
                    label="cclom:typicallearningtime",
                    alt_label="cclom:typicallearningtime",
                    level=1,
                ),
                QualityMatrixHeader(id="duration", label="cclom:duration", alt_label="cclom:duration", level=1),
                QualityMatrixHeader(
                    id="language_target", label="ccm:oeh_languageTarget", alt_label="ccm:oeh_languageTarget", level=1
                ),
                QualityMatrixHeader(id="competence", label="ccm:competence", alt_label="ccm:competence", level=1),
                QualityMatrixHeader(
                    id="competence_requirements",
                    label="ccm:oeh_competence_requirements",
                    alt_label="ccm:oeh_competence_requirements",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="competence_check",
                    label="ccm:oeh_competence_check",
                    alt_label="ccm:oeh_competence_check",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="Rechtliche Unauffälligkeit", label="Rechtliche Unauffälligkeit", alt_label=None, level=0
                ),
                QualityMatrixHeader(
                    id="oeh_quality_criminal_law",
                    label="ccm:oeh_quality_criminal_law",
                    alt_label="ccm:oeh_quality_criminal_law",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_copyright_law",
                    label="ccm:oeh_quality_copyright_law",
                    alt_label="ccm:oeh_quality_copyright_law",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_protection_of_minors",
                    label="ccm:oeh_quality_protection_of_minors",
                    alt_label="ccm:oeh_quality_protection_of_minors",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_personal_law",
                    label="ccm:oeh_quality_personal_law",
                    alt_label="ccm:oeh_quality_personal_law",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_data_privacy",
                    label="ccm:oeh_quality_data_privacy",
                    alt_label="ccm:oeh_quality_data_privacy",
                    level=1,
                ),
                QualityMatrixHeader(id="Qualität", label="Qualität", alt_label=None, level=0),
                QualityMatrixHeader(
                    id="oeh_quality_correctness",
                    label="Sachrichtigkeit",
                    alt_label="ccm:oeh_quality_correctness",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_currentness",
                    label="ccm:oeh_quality_currentness",
                    alt_label="ccm:oeh_quality_currentness",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_neutralness",
                    label="ccm:oeh_quality_neutralness",
                    alt_label="ccm:oeh_quality_neutralness",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_language",
                    label="ccm:oeh_quality_language",
                    alt_label="ccm:oeh_quality_language",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_medial", label="ccm:oeh_quality_medial", alt_label="ccm:oeh_quality_medial", level=1
                ),
                QualityMatrixHeader(
                    id="oeh_quality_didactics",
                    label="ccm:oeh_quality_didactics",
                    alt_label="ccm:oeh_quality_didactics",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_transparentness",
                    label="ccm:oeh_quality_transparentness",
                    alt_label="ccm:oeh_quality_transparentness",
                    level=1,
                ),
                QualityMatrixHeader(id="Zugänglichkeit", label="Zugänglichkeit", alt_label=None, level=0),
                QualityMatrixHeader(
                    id="oeh_accessibility_open",
                    label="ccm:oeh_accessibility_open",
                    alt_label="ccm:oeh_accessibility_open",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_accessibility_find",
                    label="ccm:oeh_accessibility_find",
                    alt_label="ccm:oeh_accessibility_find",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="accessibilitySummary",
                    label="ccm:accessibilitySummary",
                    alt_label="ccm:accessibilitySummary",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_usability", label="ccm:oeh_usability", alt_label="ccm:oeh_usability", level=1
                ),
                QualityMatrixHeader(
                    id="oeh_interoperability",
                    label="ccm:oeh_interoperability",
                    alt_label="ccm:oeh_interoperability",
                    level=1,
                ),
                QualityMatrixHeader(id="price", label="ccm:price", alt_label="ccm:price", level=1),
                QualityMatrixHeader(
                    id="oeh_quality_login", label="ccm:oeh_quality_login", alt_label="ccm:oeh_quality_login", level=1
                ),
                QualityMatrixHeader(
                    id="oeh_accessibility_security",
                    label="ccm:oeh_accessibility_security",
                    alt_label="ccm:oeh_accessibility_security",
                    level=1,
                ),
                QualityMatrixHeader(id="license_to", label="ccm:license_to", alt_label="ccm:license_to", level=1),
                QualityMatrixHeader(
                    id="Lizenz, Quelle, Mitwirkende", label="Lizenz, Quelle, Mitwirkende", alt_label=None, level=0
                ),
                QualityMatrixHeader(
                    id="license", label="ccm:commonlicense_key", alt_label="ccm:commonlicense_key", level=1
                ),
                QualityMatrixHeader(
                    id="author_freetext", label="ccm:author_freetext", alt_label="ccm:author_freetext", level=1
                ),
                QualityMatrixHeader(
                    id="editorial_publisher",
                    label="virtual:editorial_publisher",
                    alt_label="virtual:editorial_publisher",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="published_date", label="ccm:published_date", alt_label="ccm:published_date", level=1
                ),
                QualityMatrixHeader(
                    id="Entstehung des Inhaltes", label="Entstehung des Inhaltes", alt_label=None, level=0
                ),
                QualityMatrixHeader(
                    id="publishing",
                    label="ccm:lifecyclecontributer_publisher",
                    alt_label="ccm:lifecyclecontributer_publisher",
                    level=1,
                ),
                QualityMatrixHeader(id="created", label="cm:created", alt_label="cm:created", level=1),
                QualityMatrixHeader(id="modified", label="cm:modified", alt_label="cm:modified", level=1),
                QualityMatrixHeader(id="versionLabel", label="Versionsnummer", alt_label="cm:versionLabel", level=1),
                QualityMatrixHeader(
                    id="publisher", label="ccm:oeh_publisher_combined", alt_label="ccm:oeh_publisher_combined", level=1
                ),
                QualityMatrixHeader(
                    id="Identifier und Signaturen", label="Identifier und Signaturen", alt_label=None, level=0
                ),
                QualityMatrixHeader(id="node_uuid", label="WLO-Identifier", alt_label="sys:node-uuid", level=1),
                QualityMatrixHeader(
                    id="published_handle_id",
                    label="UID - im Internet eindeutige Adresse",
                    alt_label="ccm:published_handle_id",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_signatures", label="ccm:oeh_signatures", alt_label="ccm:oeh_signatures", level=1
                ),
                QualityMatrixHeader(id="Nutzung und Bewertung", label="Nutzung und Bewertung", alt_label=None, level=0),
                QualityMatrixHeader(
                    id="feedback_comment", label="feedback_comment", alt_label="feedback_comment", level=1
                ),
                QualityMatrixHeader(
                    id="Erschließung und Kuratierung", label="Erschließung und Kuratierung", alt_label=None, level=0
                ),
                QualityMatrixHeader(
                    id="creator",
                    label="ccm:metadatacontributer_creator",
                    alt_label="ccm:metadatacontributer_creator",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="provider",
                    label="ccm:metadatacontributer_provider",
                    alt_label="ccm:metadatacontributer_provider",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="validator",
                    label="ccm:metadatacontributer_validator",
                    alt_label="ccm:metadatacontributer_validator",
                    level=1,
                ),
            ],
            rows=[
                QualityMatrixRow(
                    meta=QualityMatrixHeader(
                        id="youtube_spider",
                        label="Youtube",
                        alt_label="youtube_spider (http://w3id.org/openeduhub/vocabs/sources/f5da1c8f-094a-4914-a9a6-4fb123d598c5)",
                        level=0,
                    ),
                    counts={
                        "cover": 0,
                        "short_title": 0,
                        "title": 382,
                        "description": 86,
                        "status": 0,
                        "url": 382,
                        "language": 382,
                        "learning_resource_type": 382,
                        "mimetype": 382,
                        "file_type": 0,
                        "edu_context": 382,
                        "age_range": 0,
                        "fsk": 0,
                        "taxon_id": 382,
                        "classification": 0,
                        "general_keywords": 382,
                        "intended_end_user_role": 367,
                        "curriculum": 382,
                        "learning_time": 0,
                        "duration": 354,
                        "language_target": 0,
                        "competence": 0,
                        "competence_requirements": 0,
                        "competence_check": 0,
                        "oeh_quality_criminal_law": 0,
                        "oeh_quality_copyright_law": 0,
                        "oeh_quality_protection_of_minors": 0,
                        "oeh_quality_personal_law": 0,
                        "oeh_quality_data_privacy": 0,
                        "oeh_quality_correctness": 0,
                        "oeh_quality_currentness": 0,
                        "oeh_quality_neutralness": 0,
                        "oeh_quality_language": 0,
                        "oeh_quality_medial": 0,
                        "oeh_quality_didactics": 0,
                        "oeh_quality_transparentness": 0,
                        "oeh_accessibility_open": 0,
                        "oeh_accessibility_find": 0,
                        "accessibilitySummary": 0,
                        "oeh_usability": 0,
                        "oeh_interoperability": 0,
                        "price": 4,
                        "oeh_quality_login": 0,
                        "oeh_accessibility_security": 0,
                        "license_to": 0,
                        "license": 382,
                        "author_freetext": 198,
                        "editorial_publisher": 0,
                        "published_date": 354,
                        "publishing": 354,
                        "created": 382,
                        "modified": 382,
                        "versionLabel": 0,
                        "publisher": 382,
                        "node_uuid": 0,
                        "published_handle_id": 0,
                        "oeh_signatures": 0,
                        "feedback_comment": 0,
                        "creator": 0,
                        "provider": 0,
                        "validator": 0,
                    },
                    total=382,
                ),
                QualityMatrixRow(
                    meta=QualityMatrixHeader(
                        id="biologie_lernprogramme_spider",
                        label="Biologie Lernprogramme",
                        alt_label="biologie_lernprogramme_spider (http://w3id.org/openeduhub/vocabs/sources/432c9be5-eabd-4f50-9359-0a6afbc2e0d8)",
                        level=0,
                    ),
                    counts={
                        "cover": 0,
                        "short_title": 0,
                        "title": 0,
                        "description": 0,
                        "status": 0,
                        "url": 0,
                        "language": 0,
                        "learning_resource_type": 0,
                        "mimetype": 0,
                        "file_type": 0,
                        "edu_context": 0,
                        "age_range": 0,
                        "fsk": 0,
                        "taxon_id": 0,
                        "classification": 0,
                        "general_keywords": 0,
                        "intended_end_user_role": 0,
                        "curriculum": 0,
                        "learning_time": 0,
                        "duration": 0,
                        "language_target": 0,
                        "competence": 0,
                        "competence_requirements": 0,
                        "competence_check": 0,
                        "oeh_quality_criminal_law": 0,
                        "oeh_quality_copyright_law": 0,
                        "oeh_quality_protection_of_minors": 0,
                        "oeh_quality_personal_law": 0,
                        "oeh_quality_data_privacy": 0,
                        "oeh_quality_correctness": 0,
                        "oeh_quality_currentness": 0,
                        "oeh_quality_neutralness": 0,
                        "oeh_quality_language": 0,
                        "oeh_quality_medial": 0,
                        "oeh_quality_didactics": 0,
                        "oeh_quality_transparentness": 0,
                        "oeh_accessibility_open": 0,
                        "oeh_accessibility_find": 0,
                        "accessibilitySummary": 0,
                        "oeh_usability": 0,
                        "oeh_interoperability": 0,
                        "price": 0,
                        "oeh_quality_login": 0,
                        "oeh_accessibility_security": 0,
                        "license_to": 0,
                        "license": 0,
                        "author_freetext": 0,
                        "editorial_publisher": 0,
                        "published_date": 0,
                        "publishing": 0,
                        "created": 0,
                        "modified": 0,
                        "versionLabel": 0,
                        "publisher": 0,
                        "node_uuid": 0,
                        "published_handle_id": 0,
                        "oeh_signatures": 0,
                        "feedback_comment": 0,
                        "creator": 0,
                        "provider": 0,
                        "validator": 0,
                    },
                    total=0,
                ),
                QualityMatrixRow(
                    meta=QualityMatrixHeader(
                        id="digitallearninglab_spider",
                        label="Digital Learning Lab",
                        alt_label="digitallearninglab_spider (http://w3id.org/openeduhub/vocabs/sources/7d22f062-1718-4f8d-b2c0-32751bc6f24c)",
                        level=0,
                    ),
                    counts={
                        "cover": 0,
                        "short_title": 0,
                        "title": 0,
                        "description": 0,
                        "status": 0,
                        "url": 0,
                        "language": 0,
                        "learning_resource_type": 0,
                        "mimetype": 0,
                        "file_type": 0,
                        "edu_context": 0,
                        "age_range": 0,
                        "fsk": 0,
                        "taxon_id": 0,
                        "classification": 0,
                        "general_keywords": 0,
                        "intended_end_user_role": 0,
                        "curriculum": 0,
                        "learning_time": 0,
                        "duration": 0,
                        "language_target": 0,
                        "competence": 0,
                        "competence_requirements": 0,
                        "competence_check": 0,
                        "oeh_quality_criminal_law": 0,
                        "oeh_quality_copyright_law": 0,
                        "oeh_quality_protection_of_minors": 0,
                        "oeh_quality_personal_law": 0,
                        "oeh_quality_data_privacy": 0,
                        "oeh_quality_correctness": 0,
                        "oeh_quality_currentness": 0,
                        "oeh_quality_neutralness": 0,
                        "oeh_quality_language": 0,
                        "oeh_quality_medial": 0,
                        "oeh_quality_didactics": 0,
                        "oeh_quality_transparentness": 0,
                        "oeh_accessibility_open": 0,
                        "oeh_accessibility_find": 0,
                        "accessibilitySummary": 0,
                        "oeh_usability": 0,
                        "oeh_interoperability": 0,
                        "price": 0,
                        "oeh_quality_login": 0,
                        "oeh_accessibility_security": 0,
                        "license_to": 0,
                        "license": 0,
                        "author_freetext": 0,
                        "editorial_publisher": 0,
                        "published_date": 0,
                        "publishing": 0,
                        "created": 0,
                        "modified": 0,
                        "versionLabel": 0,
                        "publisher": 0,
                        "node_uuid": 0,
                        "published_handle_id": 0,
                        "oeh_signatures": 0,
                        "feedback_comment": 0,
                        "creator": 0,
                        "provider": 0,
                        "validator": 0,
                    },
                    total=0,
                ),
                QualityMatrixRow(
                    meta=QualityMatrixHeader(
                        id="dilertube_spider",
                        label="DiLerTube",
                        alt_label="dilertube_spider (http://w3id.org/openeduhub/vocabs/sources/011766b1-07f8-4cbe-bef1-3316458ed7cb)",
                        level=0,
                    ),
                    counts={
                        "cover": 0,
                        "short_title": 0,
                        "title": 0,
                        "description": 0,
                        "status": 0,
                        "url": 0,
                        "language": 0,
                        "learning_resource_type": 0,
                        "mimetype": 0,
                        "file_type": 0,
                        "edu_context": 0,
                        "age_range": 0,
                        "fsk": 0,
                        "taxon_id": 0,
                        "classification": 0,
                        "general_keywords": 0,
                        "intended_end_user_role": 0,
                        "curriculum": 0,
                        "learning_time": 0,
                        "duration": 0,
                        "language_target": 0,
                        "competence": 0,
                        "competence_requirements": 0,
                        "competence_check": 0,
                        "oeh_quality_criminal_law": 0,
                        "oeh_quality_copyright_law": 0,
                        "oeh_quality_protection_of_minors": 0,
                        "oeh_quality_personal_law": 0,
                        "oeh_quality_data_privacy": 0,
                        "oeh_quality_correctness": 0,
                        "oeh_quality_currentness": 0,
                        "oeh_quality_neutralness": 0,
                        "oeh_quality_language": 0,
                        "oeh_quality_medial": 0,
                        "oeh_quality_didactics": 0,
                        "oeh_quality_transparentness": 0,
                        "oeh_accessibility_open": 0,
                        "oeh_accessibility_find": 0,
                        "accessibilitySummary": 0,
                        "oeh_usability": 0,
                        "oeh_interoperability": 0,
                        "price": 0,
                        "oeh_quality_login": 0,
                        "oeh_accessibility_security": 0,
                        "license_to": 0,
                        "license": 0,
                        "author_freetext": 0,
                        "editorial_publisher": 0,
                        "published_date": 0,
                        "publishing": 0,
                        "created": 0,
                        "modified": 0,
                        "versionLabel": 0,
                        "publisher": 0,
                        "node_uuid": 0,
                        "published_handle_id": 0,
                        "oeh_signatures": 0,
                        "feedback_comment": 0,
                        "creator": 0,
                        "provider": 0,
                        "validator": 0,
                    },
                    total=0,
                ),
                QualityMatrixRow(
                    meta=QualityMatrixHeader(
                        id="oai_sodis_spider", label="oai_sodis_spider", alt_label="oai_sodis_spider", level=0
                    ),
                    counts={
                        "cover": 0,
                        "short_title": 0,
                        "title": 227,
                        "description": 193,
                        "status": 0,
                        "url": 227,
                        "language": 0,
                        "learning_resource_type": 227,
                        "mimetype": 226,
                        "file_type": 0,
                        "edu_context": 227,
                        "age_range": 0,
                        "fsk": 0,
                        "taxon_id": 227,
                        "classification": 0,
                        "general_keywords": 227,
                        "intended_end_user_role": 161,
                        "curriculum": 227,
                        "learning_time": 0,
                        "duration": 0,
                        "language_target": 0,
                        "competence": 0,
                        "competence_requirements": 0,
                        "competence_check": 0,
                        "oeh_quality_criminal_law": 0,
                        "oeh_quality_copyright_law": 0,
                        "oeh_quality_protection_of_minors": 0,
                        "oeh_quality_personal_law": 0,
                        "oeh_quality_data_privacy": 0,
                        "oeh_quality_correctness": 0,
                        "oeh_quality_currentness": 0,
                        "oeh_quality_neutralness": 0,
                        "oeh_quality_language": 0,
                        "oeh_quality_medial": 0,
                        "oeh_quality_didactics": 0,
                        "oeh_quality_transparentness": 0,
                        "oeh_accessibility_open": 0,
                        "oeh_accessibility_find": 0,
                        "accessibilitySummary": 0,
                        "oeh_usability": 0,
                        "oeh_interoperability": 0,
                        "price": 2,
                        "oeh_quality_login": 0,
                        "oeh_accessibility_security": 0,
                        "license_to": 0,
                        "license": 227,
                        "author_freetext": 137,
                        "editorial_publisher": 0,
                        "published_date": 0,
                        "publishing": 184,
                        "created": 227,
                        "modified": 227,
                        "versionLabel": 0,
                        "publisher": 227,
                        "node_uuid": 0,
                        "published_handle_id": 0,
                        "oeh_signatures": 0,
                        "feedback_comment": 0,
                        "creator": 0,
                        "provider": 0,
                        "validator": 0,
                    },
                    total=227,
                ),
                QualityMatrixRow(
                    meta=QualityMatrixHeader(id="rlp_spider", label="rlp_spider", alt_label="rlp_spider", level=0),
                    counts={
                        "cover": 0,
                        "short_title": 0,
                        "title": 189,
                        "description": 173,
                        "status": 0,
                        "url": 189,
                        "language": 0,
                        "learning_resource_type": 189,
                        "mimetype": 189,
                        "file_type": 0,
                        "edu_context": 189,
                        "age_range": 0,
                        "fsk": 0,
                        "taxon_id": 189,
                        "classification": 0,
                        "general_keywords": 189,
                        "intended_end_user_role": 3,
                        "curriculum": 188,
                        "learning_time": 0,
                        "duration": 0,
                        "language_target": 0,
                        "competence": 0,
                        "competence_requirements": 0,
                        "competence_check": 0,
                        "oeh_quality_criminal_law": 0,
                        "oeh_quality_copyright_law": 0,
                        "oeh_quality_protection_of_minors": 0,
                        "oeh_quality_personal_law": 0,
                        "oeh_quality_data_privacy": 0,
                        "oeh_quality_correctness": 0,
                        "oeh_quality_currentness": 0,
                        "oeh_quality_neutralness": 0,
                        "oeh_quality_language": 0,
                        "oeh_quality_medial": 0,
                        "oeh_quality_didactics": 0,
                        "oeh_quality_transparentness": 0,
                        "oeh_accessibility_open": 0,
                        "oeh_accessibility_find": 0,
                        "accessibilitySummary": 0,
                        "oeh_usability": 0,
                        "oeh_interoperability": 0,
                        "price": 0,
                        "oeh_quality_login": 0,
                        "oeh_accessibility_security": 0,
                        "license_to": 0,
                        "license": 189,
                        "author_freetext": 1,
                        "editorial_publisher": 0,
                        "published_date": 0,
                        "publishing": 0,
                        "created": 189,
                        "modified": 189,
                        "versionLabel": 0,
                        "publisher": 189,
                        "node_uuid": 0,
                        "published_handle_id": 0,
                        "oeh_signatures": 0,
                        "feedback_comment": 0,
                        "creator": 0,
                        "provider": 0,
                        "validator": 0,
                    },
                    total=189,
                ),
            ],
        )


def test_collection_quality_matrix():
    collection = Tree(
        node_id=uuid.UUID("4940d5da-9b21-4ec0-8824-d16e0409e629"),
        title="root",
        parent_id=None,
        level=0,
        children=[
            Tree(
                node_id=uuid.UUID("481c9ce1-7f72-4598-a326-7dba785a065d"),
                title="child1",
                parent_id=uuid.UUID("4940d5da-9b21-4ec0-8824-d16e0409e629"),
                children=[],
                level=1,
            ),
            Tree(
                node_id=uuid.UUID("9b7299f9-31f5-477d-b10e-18a465295bdd"),
                title="child2",
                parent_id=uuid.UUID("4940d5da-9b21-4ec0-8824-d16e0409e629"),
                children=[],
                level=1,
            ),
        ],
    )
    with elastic_search_mock("quality-matrix-collection"), edusharing_mock():
        result = _collection_quality_matrix(collection=collection)
        assert result == QualityMatrix(
            columns=[
                QualityMatrixHeader(id="Beschreibendes", label="Beschreibendes", alt_label=None, level=0),
                QualityMatrixHeader(id="cover", label="preview", alt_label="preview", level=1),
                QualityMatrixHeader(
                    id="short_title", label="ccm:collectionshorttitle", alt_label="ccm:collectionshorttitle", level=1
                ),
                QualityMatrixHeader(id="title", label="cclom:title", alt_label="cclom:title", level=1),
                QualityMatrixHeader(
                    id="description", label="cclom:general_description", alt_label="cclom:general_description", level=1
                ),
                QualityMatrixHeader(id="status", label="cclom:status", alt_label="cclom:status", level=1),
                QualityMatrixHeader(id="url", label="ccm:wwwurl", alt_label="ccm:wwwurl", level=1),
                QualityMatrixHeader(
                    id="language", label="cclom:general_language", alt_label="cclom:general_language", level=1
                ),
                QualityMatrixHeader(id="Typisierung", label="Typisierung", alt_label=None, level=0),
                QualityMatrixHeader(id="learning_resource_type", label="ccm:oeh_lrt", alt_label="ccm:oeh_lrt", level=1),
                QualityMatrixHeader(id="mimetype", label="mimetype", alt_label="mimetype", level=1),
                QualityMatrixHeader(
                    id="file_type", label="Datei-/Editorformat", alt_label="virtual:editorial_file_type", level=1
                ),
                QualityMatrixHeader(
                    id="edu_context", label="ccm:educationalcontext", alt_label="ccm:educationalcontext", level=1
                ),
                QualityMatrixHeader(
                    id="age_range",
                    label="ccm:educationaltypicalagerange",
                    alt_label="ccm:educationaltypicalagerange",
                    level=1,
                ),
                QualityMatrixHeader(id="fsk", label="ccm:fskRating", alt_label="ccm:fskRating", level=1),
                QualityMatrixHeader(id="taxon_id", label="ccm:taxonid", alt_label="ccm:taxonid", level=1),
                QualityMatrixHeader(
                    id="classification",
                    label="cclom:classification_keyword",
                    alt_label="cclom:classification_keyword",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="general_keywords", label="cclom:general_keyword", alt_label="cclom:general_keyword", level=1
                ),
                QualityMatrixHeader(id="Pädagogisch", label="Pädagogisch", alt_label=None, level=0),
                QualityMatrixHeader(
                    id="intended_end_user_role",
                    label="ccm:educationalintendedenduserrole",
                    alt_label="ccm:educationalintendedenduserrole",
                    level=1,
                ),
                QualityMatrixHeader(id="curriculum", label="ccm:curriculum", alt_label="ccm:curriculum", level=1),
                QualityMatrixHeader(
                    id="learning_time",
                    label="cclom:typicallearningtime",
                    alt_label="cclom:typicallearningtime",
                    level=1,
                ),
                QualityMatrixHeader(id="duration", label="cclom:duration", alt_label="cclom:duration", level=1),
                QualityMatrixHeader(
                    id="language_target", label="ccm:oeh_languageTarget", alt_label="ccm:oeh_languageTarget", level=1
                ),
                QualityMatrixHeader(id="competence", label="ccm:competence", alt_label="ccm:competence", level=1),
                QualityMatrixHeader(
                    id="competence_requirements",
                    label="ccm:oeh_competence_requirements",
                    alt_label="ccm:oeh_competence_requirements",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="competence_check",
                    label="ccm:oeh_competence_check",
                    alt_label="ccm:oeh_competence_check",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="Rechtliche Unauffälligkeit", label="Rechtliche Unauffälligkeit", alt_label=None, level=0
                ),
                QualityMatrixHeader(
                    id="oeh_quality_criminal_law",
                    label="ccm:oeh_quality_criminal_law",
                    alt_label="ccm:oeh_quality_criminal_law",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_copyright_law",
                    label="ccm:oeh_quality_copyright_law",
                    alt_label="ccm:oeh_quality_copyright_law",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_protection_of_minors",
                    label="ccm:oeh_quality_protection_of_minors",
                    alt_label="ccm:oeh_quality_protection_of_minors",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_personal_law",
                    label="ccm:oeh_quality_personal_law",
                    alt_label="ccm:oeh_quality_personal_law",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_data_privacy",
                    label="ccm:oeh_quality_data_privacy",
                    alt_label="ccm:oeh_quality_data_privacy",
                    level=1,
                ),
                QualityMatrixHeader(id="Qualität", label="Qualität", alt_label=None, level=0),
                QualityMatrixHeader(
                    id="oeh_quality_correctness",
                    label="Sachrichtigkeit",
                    alt_label="ccm:oeh_quality_correctness",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_currentness",
                    label="ccm:oeh_quality_currentness",
                    alt_label="ccm:oeh_quality_currentness",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_neutralness",
                    label="ccm:oeh_quality_neutralness",
                    alt_label="ccm:oeh_quality_neutralness",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_language",
                    label="ccm:oeh_quality_language",
                    alt_label="ccm:oeh_quality_language",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_medial", label="ccm:oeh_quality_medial", alt_label="ccm:oeh_quality_medial", level=1
                ),
                QualityMatrixHeader(
                    id="oeh_quality_didactics",
                    label="ccm:oeh_quality_didactics",
                    alt_label="ccm:oeh_quality_didactics",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_quality_transparentness",
                    label="ccm:oeh_quality_transparentness",
                    alt_label="ccm:oeh_quality_transparentness",
                    level=1,
                ),
                QualityMatrixHeader(id="Zugänglichkeit", label="Zugänglichkeit", alt_label=None, level=0),
                QualityMatrixHeader(
                    id="oeh_accessibility_open",
                    label="ccm:oeh_accessibility_open",
                    alt_label="ccm:oeh_accessibility_open",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_accessibility_find",
                    label="ccm:oeh_accessibility_find",
                    alt_label="ccm:oeh_accessibility_find",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="accessibilitySummary",
                    label="ccm:accessibilitySummary",
                    alt_label="ccm:accessibilitySummary",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_usability", label="ccm:oeh_usability", alt_label="ccm:oeh_usability", level=1
                ),
                QualityMatrixHeader(
                    id="oeh_interoperability",
                    label="ccm:oeh_interoperability",
                    alt_label="ccm:oeh_interoperability",
                    level=1,
                ),
                QualityMatrixHeader(id="price", label="ccm:price", alt_label="ccm:price", level=1),
                QualityMatrixHeader(
                    id="oeh_quality_login", label="ccm:oeh_quality_login", alt_label="ccm:oeh_quality_login", level=1
                ),
                QualityMatrixHeader(
                    id="oeh_accessibility_security",
                    label="ccm:oeh_accessibility_security",
                    alt_label="ccm:oeh_accessibility_security",
                    level=1,
                ),
                QualityMatrixHeader(id="license_to", label="ccm:license_to", alt_label="ccm:license_to", level=1),
                QualityMatrixHeader(
                    id="Lizenz, Quelle, Mitwirkende", label="Lizenz, Quelle, Mitwirkende", alt_label=None, level=0
                ),
                QualityMatrixHeader(
                    id="license", label="ccm:commonlicense_key", alt_label="ccm:commonlicense_key", level=1
                ),
                QualityMatrixHeader(
                    id="author_freetext", label="ccm:author_freetext", alt_label="ccm:author_freetext", level=1
                ),
                QualityMatrixHeader(
                    id="editorial_publisher",
                    label="virtual:editorial_publisher",
                    alt_label="virtual:editorial_publisher",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="published_date", label="ccm:published_date", alt_label="ccm:published_date", level=1
                ),
                QualityMatrixHeader(
                    id="Entstehung des Inhaltes", label="Entstehung des Inhaltes", alt_label=None, level=0
                ),
                QualityMatrixHeader(
                    id="publishing",
                    label="ccm:lifecyclecontributer_publisher",
                    alt_label="ccm:lifecyclecontributer_publisher",
                    level=1,
                ),
                QualityMatrixHeader(id="created", label="cm:created", alt_label="cm:created", level=1),
                QualityMatrixHeader(id="modified", label="cm:modified", alt_label="cm:modified", level=1),
                QualityMatrixHeader(id="versionLabel", label="Versionsnummer", alt_label="cm:versionLabel", level=1),
                QualityMatrixHeader(
                    id="publisher", label="ccm:oeh_publisher_combined", alt_label="ccm:oeh_publisher_combined", level=1
                ),
                QualityMatrixHeader(
                    id="Identifier und Signaturen", label="Identifier und Signaturen", alt_label=None, level=0
                ),
                QualityMatrixHeader(id="node_uuid", label="WLO-Identifier", alt_label="sys:node-uuid", level=1),
                QualityMatrixHeader(
                    id="published_handle_id",
                    label="UID - im Internet eindeutige Adresse",
                    alt_label="ccm:published_handle_id",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="oeh_signatures", label="ccm:oeh_signatures", alt_label="ccm:oeh_signatures", level=1
                ),
                QualityMatrixHeader(id="Nutzung und Bewertung", label="Nutzung und Bewertung", alt_label=None, level=0),
                QualityMatrixHeader(
                    id="feedback_comment", label="feedback_comment", alt_label="feedback_comment", level=1
                ),
                QualityMatrixHeader(
                    id="Erschließung und Kuratierung", label="Erschließung und Kuratierung", alt_label=None, level=0
                ),
                QualityMatrixHeader(
                    id="creator",
                    label="ccm:metadatacontributer_creator",
                    alt_label="ccm:metadatacontributer_creator",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="provider",
                    label="ccm:metadatacontributer_provider",
                    alt_label="ccm:metadatacontributer_provider",
                    level=1,
                ),
                QualityMatrixHeader(
                    id="validator",
                    label="ccm:metadatacontributer_validator",
                    alt_label="ccm:metadatacontributer_validator",
                    level=1,
                ),
            ],
            rows=[
                QualityMatrixRow(
                    meta=QualityMatrixHeader(
                        id="4940d5da-9b21-4ec0-8824-d16e0409e629",
                        label="root",
                        alt_label="4940d5da-9b21-4ec0-8824-d16e0409e629",
                        level=0,
                    ),
                    counts={
                        "cover": 0,
                        "short_title": 0,
                        "title": 2314,
                        "description": 1498,
                        "status": 0,
                        "url": 2260,
                        "language": 693,
                        "learning_resource_type": 2300,
                        "mimetype": 1305,
                        "file_type": 0,
                        "edu_context": 2309,
                        "age_range": 0,
                        "fsk": 0,
                        "taxon_id": 2313,
                        "classification": 0,
                        "general_keywords": 2240,
                        "intended_end_user_role": 1452,
                        "curriculum": 2160,
                        "learning_time": 0,
                        "duration": 354,
                        "language_target": 0,
                        "competence": 0,
                        "competence_requirements": 0,
                        "competence_check": 0,
                        "oeh_quality_criminal_law": 0,
                        "oeh_quality_copyright_law": 0,
                        "oeh_quality_protection_of_minors": 0,
                        "oeh_quality_personal_law": 0,
                        "oeh_quality_data_privacy": 0,
                        "oeh_quality_correctness": 0,
                        "oeh_quality_currentness": 0,
                        "oeh_quality_neutralness": 0,
                        "oeh_quality_language": 0,
                        "oeh_quality_medial": 0,
                        "oeh_quality_didactics": 0,
                        "oeh_quality_transparentness": 0,
                        "oeh_accessibility_open": 0,
                        "oeh_accessibility_find": 0,
                        "accessibilitySummary": 22,
                        "oeh_usability": 0,
                        "oeh_interoperability": 0,
                        "price": 772,
                        "oeh_quality_login": 0,
                        "oeh_accessibility_security": 0,
                        "license_to": 0,
                        "license": 2312,
                        "author_freetext": 1491,
                        "editorial_publisher": 0,
                        "published_date": 374,
                        "publishing": 643,
                        "created": 2314,
                        "modified": 2314,
                        "versionLabel": 0,
                        "publisher": 1358,
                        "node_uuid": 0,
                        "published_handle_id": 0,
                        "oeh_signatures": 0,
                        "feedback_comment": 0,
                        "creator": 748,
                        "provider": 0,
                        "validator": 0,
                    },
                    total=2314,
                ),
                QualityMatrixRow(
                    meta=QualityMatrixHeader(
                        id="481c9ce1-7f72-4598-a326-7dba785a065d",
                        label="child1",
                        alt_label="481c9ce1-7f72-4598-a326-7dba785a065d",
                        level=1,
                    ),
                    counts={
                        "cover": 0,
                        "short_title": 0,
                        "title": 87,
                        "description": 4,
                        "status": 0,
                        "url": 87,
                        "language": 87,
                        "learning_resource_type": 87,
                        "mimetype": 87,
                        "file_type": 0,
                        "edu_context": 87,
                        "age_range": 0,
                        "fsk": 0,
                        "taxon_id": 87,
                        "classification": 0,
                        "general_keywords": 87,
                        "intended_end_user_role": 87,
                        "curriculum": 87,
                        "learning_time": 0,
                        "duration": 87,
                        "language_target": 0,
                        "competence": 0,
                        "competence_requirements": 0,
                        "competence_check": 0,
                        "oeh_quality_criminal_law": 0,
                        "oeh_quality_copyright_law": 0,
                        "oeh_quality_protection_of_minors": 0,
                        "oeh_quality_personal_law": 0,
                        "oeh_quality_data_privacy": 0,
                        "oeh_quality_correctness": 0,
                        "oeh_quality_currentness": 0,
                        "oeh_quality_neutralness": 0,
                        "oeh_quality_language": 0,
                        "oeh_quality_medial": 0,
                        "oeh_quality_didactics": 0,
                        "oeh_quality_transparentness": 0,
                        "oeh_accessibility_open": 0,
                        "oeh_accessibility_find": 0,
                        "accessibilitySummary": 0,
                        "oeh_usability": 0,
                        "oeh_interoperability": 0,
                        "price": 0,
                        "oeh_quality_login": 0,
                        "oeh_accessibility_security": 0,
                        "license_to": 0,
                        "license": 87,
                        "author_freetext": 87,
                        "editorial_publisher": 0,
                        "published_date": 87,
                        "publishing": 87,
                        "created": 87,
                        "modified": 87,
                        "versionLabel": 0,
                        "publisher": 87,
                        "node_uuid": 0,
                        "published_handle_id": 0,
                        "oeh_signatures": 0,
                        "feedback_comment": 0,
                        "creator": 0,
                        "provider": 0,
                        "validator": 0,
                    },
                    total=87,
                ),
                QualityMatrixRow(
                    meta=QualityMatrixHeader(
                        id="9b7299f9-31f5-477d-b10e-18a465295bdd",
                        label="child2",
                        alt_label="9b7299f9-31f5-477d-b10e-18a465295bdd",
                        level=1,
                    ),
                    counts={
                        "cover": 0,
                        "short_title": 0,
                        "title": 72,
                        "description": 31,
                        "status": 0,
                        "url": 72,
                        "language": 29,
                        "learning_resource_type": 72,
                        "mimetype": 37,
                        "file_type": 0,
                        "edu_context": 72,
                        "age_range": 0,
                        "fsk": 0,
                        "taxon_id": 72,
                        "classification": 0,
                        "general_keywords": 72,
                        "intended_end_user_role": 62,
                        "curriculum": 72,
                        "learning_time": 0,
                        "duration": 28,
                        "language_target": 0,
                        "competence": 0,
                        "competence_requirements": 0,
                        "competence_check": 0,
                        "oeh_quality_criminal_law": 0,
                        "oeh_quality_copyright_law": 0,
                        "oeh_quality_protection_of_minors": 0,
                        "oeh_quality_personal_law": 0,
                        "oeh_quality_data_privacy": 0,
                        "oeh_quality_correctness": 0,
                        "oeh_quality_currentness": 0,
                        "oeh_quality_neutralness": 0,
                        "oeh_quality_language": 0,
                        "oeh_quality_medial": 0,
                        "oeh_quality_didactics": 0,
                        "oeh_quality_transparentness": 0,
                        "oeh_accessibility_open": 0,
                        "oeh_accessibility_find": 0,
                        "accessibilitySummary": 0,
                        "oeh_usability": 0,
                        "oeh_interoperability": 0,
                        "price": 34,
                        "oeh_quality_login": 0,
                        "oeh_accessibility_security": 0,
                        "license_to": 0,
                        "license": 72,
                        "author_freetext": 62,
                        "editorial_publisher": 0,
                        "published_date": 28,
                        "publishing": 28,
                        "created": 72,
                        "modified": 72,
                        "versionLabel": 0,
                        "publisher": 38,
                        "node_uuid": 0,
                        "published_handle_id": 0,
                        "oeh_signatures": 0,
                        "feedback_comment": 0,
                        "creator": 33,
                        "provider": 0,
                        "validator": 0,
                    },
                    total=72,
                ),
            ],
        )

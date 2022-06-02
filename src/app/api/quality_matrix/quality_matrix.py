from datetime import datetime
from typing import Union
from uuid import UUID

import sqlalchemy
from databases import Database
from elasticsearch_dsl import AttrDict
from elasticsearch_dsl.response import Response

from app.api.collections.tree import collection_tree
from app.api.quality_matrix.models import Timeline
from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.constants import PROPERTIES, REPLICATION_SOURCE_ID
from app.core.logging import logger
from app.elastic.dsl import qbool, qmatch
from app.elastic.elastic import base_match_filter
from app.elastic.search import Search

PROPERTY_TYPE = list[str]
QUALITY_MATRIX_RETURN_TYPE = list[dict[str, Union[str, float]]]


def add_base_match_filters(search: Search) -> Search:
    for entry in base_match_filter:
        search = search.query(entry)
    return search


def create_sources_search(aggregation_name: str):
    s = add_base_match_filters(Search())
    s.aggs.bucket(
        aggregation_name,
        "terms",
        field=f"{PROPERTIES}.{REPLICATION_SOURCE_ID}.keyword",
        size=ELASTIC_TOTAL_SIZE,
    )
    return s


def extract_sources_from_response(
    response: Response, aggregation_name: str
) -> dict[str, int]:
    return {
        entry["key"]: entry["doc_count"]
        for entry in response.aggregations.to_dict()[aggregation_name]["buckets"]
    }


def all_sources() -> dict[str, int]:
    aggregation_name = "unique_sources"
    s = create_sources_search(aggregation_name)
    response: Response = s.execute()
    return extract_sources_from_response(
        response=response, aggregation_name=aggregation_name
    )


def default_properties() -> list[str]:
    return [
        "add_to_stream_description",
        "add_to_stream_priority",
        "add_to_stream_title",
        "cclom:aggregationlevel",
        "cclom:classification_keyword",
        "cclom:duration",
        "cclom:format",
        "cclom:general_description",
        "cclom:general_keyword",
        "cclom:general_language",
        "cclom:location",
        "cclom:size",
        "cclom:status",
        "cclom:title",
        "cclom:typicallearningtime",
        "ccm:accessibilitySummary",
        "ccm:author_freetext",
        "ccm:classification_purpose",
        "ccm:collection_ordered_position",
        "ccm:collection_proposal_status",
        "ccm:collectionshorttitle",
        "ccm:commonlicense_key",
        "ccm:competence",
        "ccm:conditionsOfAccess",
        "ccm:containsAdvertisement",
        "ccm:curriculum",
        "ccm:custom_license",
        "ccm:dataProtectionConformity",
        "ccm:editorial_checklist",
        "ccm:editorial_state",
        "ccm:educationalcontext",
        "ccm:educationaldifficulty",
        "ccm:educationalintendedenduserrole",
        "ccm:educationalinteractivitytype",
        "ccm:educationallearningresourcetype",
        "ccm:educationaltypicalagerange",
        "ccm:fskRating",
        "ccm:general_identifier",
        "ccm:imported_object_appname",
        "ccm:license_oer",
        "ccm:license_to",
        "ccm:lifecyclecontributer_author",
        "ccm:lifecyclecontributer_content_provider",
        "ccm:lifecyclecontributer_editor",
        "ccm:lifecyclecontributer_educational_validator",
        "ccm:lifecyclecontributer_graphical_designer",
        "ccm:lifecyclecontributer_initiator",
        "ccm:lifecyclecontributer_instructional_designer",
        "ccm:lifecyclecontributer_publisher",
        "ccm:lifecyclecontributer_script_writer",
        "ccm:lifecyclecontributer_subject_matter_expert",
        "ccm:lifecyclecontributer_technical_implementer",
        "ccm:lifecyclecontributer_terminator",
        "ccm:lifecyclecontributer_unknown",
        "ccm:lifecyclecontributer_validator",
        "ccm:metadatacontributer_creator",
        "ccm:metadatacontributer_provider",
        "ccm:metadatacontributer_validator",
        "ccm:notes",
        "ccm:objecttype",
        "ccm:oeh_accessibility_find",
        "ccm:oeh_accessibility_open",
        "ccm:oeh_accessibility_security",
        "ccm:oeh_buffet_criteria",
        "ccm:oeh_competence_check",
        "ccm:oeh_competence_requirements",
        "ccm:oeh_digitalCompetencies",
        "ccm:oeh_internalDocument",
        "ccm:oeh_interoperability",
        "ccm:oeh_languageLevel",
        "ccm:oeh_languageTarget",
        "ccm:oeh_lrt",
        "ccm:oeh_lrt_aggregated",
        "ccm:oeh_quality_copyright_law",
        "ccm:oeh_quality_correctness",
        "ccm:oeh_quality_criminal_law",
        "ccm:oeh_quality_currentness",
        "ccm:oeh_quality_data_privacy",
        "ccm:oeh_quality_didactics",
        "ccm:oeh_quality_language",
        "ccm:oeh_quality_login",
        "ccm:oeh_quality_medial",
        "ccm:oeh_quality_neutralness",
        "ccm:oeh_quality_personal_law",
        "ccm:oeh_quality_protection_of_minors",
        "ccm:oeh_quality_relevancy_for_education",
        "ccm:oeh_quality_transparentness",
        "ccm:oeh_signatures",
        "ccm:oeh_usability",
        "ccm:oeh_widgets",
        "ccm:pointsdefault",
        "ccm:price",
        "ccm:published_date",
        "ccm:published_handle_id",
        "ccm:replicationsource",
        "ccm:restricted_access",
        "ccm:sourceContentType",
        "ccm:taxonid",
        "ccm:toolCategory",
        "ccm:tool_category",
        "ccm:tool_instance_access",
        "ccm:tool_instance_key",
        "ccm:tool_instance_license",
        "ccm:tool_instance_params",
        "ccm:tool_instance_provider",
        "ccm:tool_instance_provider_url",
        "ccm:tool_instance_secret",
        "ccm:tool_instance_support_contact",
        "ccm:tool_instance_support_mail",
        "ccm:tool_producer",
        "ccm:unmetLegalCriteria",
        "ccm:wwwurl",
        "cm:created",
        "cm:description",
        "cm:modified",
        "cm:name",
        "cm:title",
        "cm:versionLabel",
        "collection_feedback",
        "feedback_comment",
        "feedback_rating",
        "license",
        "sys:node-uuid",
        "virtual:author",
        "virtual:collection_id",
        "virtual:collection_id_primary",
        "virtual:data_privacy",
        "virtual:editorial_edit_type",
        "virtual:editorial_exclusion",
        "virtual:editorial_file_type",
        "virtual:editorial_filter",
        "virtual:editorial_publisher",
        "virtual:editorial_replicationsource",
        "virtual:editorial_status",
        "virtual:editorial_taxonid",
        "virtual:editorial_title",
        "virtual:email",
        "virtual:mediatype",
        "virtual:newsletter",
        "virtual:portal_type",
        "virtual:publish_location",
        "virtual:search_tasks",
        "virtual:time_after_created",
        "virtual:time_after_modified",
        "virtual:type",
    ]


def extract_properties(hits: list[AttrDict]) -> PROPERTY_TYPE:
    return list(set(list(hits[0].to_dict()[PROPERTIES].keys()) + default_properties()))


def create_properties_search() -> Search:
    return add_base_match_filters(Search().source([PROPERTIES]))


def get_properties() -> PROPERTY_TYPE:
    s = create_properties_search()
    response = s.execute()
    return extract_properties(response.hits)


def create_empty_entries_search(
    properties: PROPERTY_TYPE, replication_source: str
) -> Search:
    s = add_base_match_filters(
        Search()
        .query(
            qbool(
                must=[
                    qmatch(
                        **{f"{PROPERTIES}.{REPLICATION_SOURCE_ID}": replication_source}
                    ),
                ]
            )
        )
        .source(includes=["aggregations"])
    )
    for keyword in properties:
        s.aggs.bucket(keyword, "missing", field=f"{PROPERTIES}.{keyword}.keyword")
    return s


def all_missing_properties(
    properties: PROPERTY_TYPE, replication_source: str
) -> Response:
    return create_empty_entries_search(properties, replication_source).execute()


def join_data(data, key):
    return {"metadatum": key, "columns": data}


def api_ready_output(raw_input: dict) -> QUALITY_MATRIX_RETURN_TYPE:
    return [join_data(data, key) for key, data in raw_input.items()]


def missing_fields_ratio(value: dict, total_count: int) -> float:
    return round((1 - value["doc_count"] / total_count) * 100, 2)


def missing_fields(
    value: dict, total_count: int, replication_source: str
) -> dict[str, float]:
    return {replication_source: missing_fields_ratio(value, total_count)}


async def stored_in_timeline(data: QUALITY_MATRIX_RETURN_TYPE, database: Database):
    await database.connect()
    await database.execute(
        sqlalchemy.insert(Timeline).values(
            {"timestamp": datetime.now().timestamp(), "quality_matrix": data}
        )
    )
    await database.disconnect()


async def quality_matrix() -> QUALITY_MATRIX_RETURN_TYPE:
    properties = get_properties()
    output = {k: {} for k in properties}
    for replication_source, total_count in all_sources().items():
        response = all_missing_properties(properties, replication_source)
        for key, value in response.aggregations.to_dict().items():
            output[key] |= missing_fields(value, total_count, replication_source)

    logger.debug(f"Quality matrix output:\n{output}")
    return api_ready_output(output)


# TODO fuse with create_empty_entries_search
def create_empty_entries_collection_search(
    properties: PROPERTY_TYPE, node_id: str
) -> Search:
    s = add_base_match_filters(
        Search()
        .query(
            qbool(
                must=[
                    qmatch(**{"path": node_id}),
                ]
            )
        )
        .source(includes=["aggregations"])
    )
    for keyword in properties:
        s.aggs.bucket(keyword, "missing", field=f"{PROPERTIES}.{keyword}.keyword")
    return s


def node_count(data: list) -> list[UUID]:
    output = []
    for collection in data:
        if collection.children:
            output += node_count(collection.children)
        else:
            output = [collection.noderef_id]
    return output


async def collection_quality_matrix(node_id: UUID) -> QUALITY_MATRIX_RETURN_TYPE:
    properties = get_properties()
    output = {k: {} for k in properties}
    print(node_id)
    collections = await collection_tree(node_id)
    nodes = node_count(collections)
    print(collections)
    print(nodes)
    for collection in nodes:
        total_count = 1000
        response = create_empty_entries_collection_search(
            properties, str(collection)
        ).execute()
        print(response)
        for key, value in response.aggregations.to_dict().items():
            output[key] |= missing_fields(value, total_count, str(collection))

    logger.debug(f"Quality matrix output:\n{output}")
    return api_ready_output(output)

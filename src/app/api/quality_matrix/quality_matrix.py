from typing import Union

from elasticsearch_dsl import AttrDict
from elasticsearch_dsl.response import Response

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
        "ccm:educationalintendedenduserrole",
        "cclom:location",
        "ccm:educationalcontext",
        "ccm:oeh_quality_relevancy_for_education",
        "ccm:oeh_buffet_criteria",
        "ccm:tool_instance_license",
        "virtual:publish_location",
        "ccm:metadatacontributer_provider",
        "ccm:dataProtectionConformity",
        "ccm:classification_purpose",
        "ccm:tool_instance_provider",
        "ccm:oeh_usability",
        "cm:versionLabel",
        "virtual:data_privacy",
        "ccm:curriculum",
        "ccm:tool_instance_key",
        "cm:title",
        "ccm:published_handle_id",
        "ccm:lifecyclecontributer_terminator",
        "ccm:imported_object_appname",
        "ccm:oeh_quality_personal_law",
        "virtual:search_tasks",
        "ccm:metadatacontributer_validator",
        "ccm:published_date",
        "cm:created",
        "ccm:oeh_quality_copyright_law",
        "ccm:oeh_accessibility_open",
        "ccm:tool_producer",
        "ccm:oeh_internalDocument",
        "virtual:type",
        "ccm:lifecyclecontributer_technical_implementer",
        "ccm:oeh_competence_requirements",
        "virtual:newsletter",
        "ccm:restricted_access",
        "ccm:lifecyclecontributer_content_provider",
        "ccm:oeh_widgets",
        "ccm:accessibilitySummary",
        "ccm:oeh_quality_neutralness",
        "ccm:oeh_quality_protection_of_minors",
        "ccm:price",
        "ccm:oeh_lrt_aggregated",
        "ccm:oeh_competence_check",
        "virtual:collection_id_primary",
        "ccm:educationaltypicalagerange",
        "ccm:pointsdefault",
        "cm:name",
        "ccm:lifecyclecontributer_instructional_designer",
        "ccm:lifecyclecontributer_graphical_designer",
        "ccm:collectionshorttitle",
        "cclom:general_description",
        "cclom:typicallearningtime",
        "add_to_stream_title",
        "virtual:collection_id",
        "ccm:lifecyclecontributer_initiator",
        "ccm:conditionsOfAccess",
        "ccm:oeh_lrt",
        "virtual:mediatype",
        "cclom:duration",
        "ccm:lifecyclecontributer_editor",
        "cm:modified",
        "virtual:editorial_status",
        "virtual:editorial_taxonid",
        "ccm:oeh_accessibility_find",
        "add_to_stream_priority",
        "cclom:title",
        "ccm:toolCategory",
        "feedback_comment",
        "ccm:oeh_languageTarget",
        "ccm:lifecyclecontributer_publisher",
        "ccm:tool_instance_support_contact",
        "virtual:portal_type",
        "ccm:oeh_languageLevel",
        "virtual:editorial_exclusion",
        "ccm:lifecyclecontributer_validator",
        "ccm:lifecyclecontributer_unknown",
        "ccm:wwwurl",
        "ccm:oeh_quality_login",
        "ccm:oeh_quality_currentness",
        "ccm:oeh_quality_correctness",
        "ccm:general_identifier",
        "ccm:editorial_state",
        "ccm:notes",
        "sys:node-uuid",
        "ccm:tool_instance_support_mail",
        "ccm:objecttype",
        "ccm:oeh_digitalCompetencies",
        "ccm:oeh_interoperability",
        "ccm:educationallearningresourcetype",
        "license",
        "ccm:fskRating",
        "ccm:unmetLegalCriteria",
        "ccm:oeh_quality_didactics",
        "ccm:oeh_quality_medial",
        "ccm:oeh_quality_language",
        "ccm:containsAdvertisement",
        "virtual:editorial_replicationsource",
        "cclom:aggregationlevel",
        "ccm:taxonid",
        "cclom:size",
        "ccm:author_freetext",
        "ccm:metadatacontributer_creator",
        "ccm:tool_instance_provider_url",
        "virtual:editorial_edit_type",
        "ccm:collection_proposal_status",
        "ccm:license_oer",
        "ccm:tool_instance_access",
        "ccm:competence",
        "collection_feedback",
        "ccm:sourceContentType",
        "cclom:format",
        "cm:description",
        "cclom:status",
        "virtual:author",
        "virtual:editorial_filter",
        "ccm:tool_instance_params",
        "virtual:editorial_publisher",
        "add_to_stream_description",
        "ccm:oeh_quality_criminal_law",
        "virtual:editorial_file_type",
        "ccm:license_to",
        "virtual:time_after_created",
        "ccm:editorial_checklist",
        "ccm:oeh_signatures",
        "ccm:oeh_quality_transparentness",
        "cclom:general_language",
        "ccm:oeh_accessibility_security",
        "virtual:editorial_title",
        "virtual:email",
        "feedback_rating",
        "ccm:oeh_quality_data_privacy",
        "ccm:collection_ordered_position",
        "cclom:general_keyword",
        "ccm:educationalinteractivitytype",
        "virtual:time_after_modified",
        "ccm:tool_instance_secret",
        "ccm:replicationsource",
        "ccm:lifecyclecontributer_author",
        "ccm:lifecyclecontributer_script_writer",
        "ccm:educationaldifficulty",
        "ccm:commonlicense_key",
        "ccm:custom_license",
        "ccm:lifecyclecontributer_educational_validator",
        "cclom:classification_keyword",
        "ccm:lifecyclecontributer_subject_matter_expert",
        "ccm:tool_category",
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


async def quality_matrix() -> QUALITY_MATRIX_RETURN_TYPE:
    properties = get_properties()
    output = {k: {} for k in properties}
    for replication_source, total_count in all_sources().items():
        response = all_missing_properties(properties, replication_source)
        for key, value in response.aggregations.to_dict().items():
            output[key] |= missing_fields(value, total_count, replication_source)

    logger.debug(f"Quality matrix output:\n{output}")
    return api_ready_output(output)

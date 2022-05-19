import json
from datetime import datetime
from typing import Union

from databases import Database
from elasticsearch_dsl import AttrDict
from elasticsearch_dsl.response import Response

from app.api.quality_matrix.timeline import create_timeline_table, get_table, has_table
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
        "virtual:collection_id_primary",
        "virtual:collection_id",
        "ccm:collection_proposal_status",
        "virtual:portal_type",
        "ccm:oeh_quality_correctness",
        "ccm:published_handle_id",
        "sys:node-uuid",
        "sys:node-uuid",
        "cm:versionLabel",
        "virtual:search_tasks",
        "virtual:author",
        "virtual:time_after_modified",
        "virtual:time_after_created",
        "virtual:editorial_exclusion",
        "virtual:editorial_taxonid",
        "virtual:editorial_file_type",
        "virtual:editorial_edit_type",
        "virtual:editorial_filter",
        "virtual:editorial_status",
        "virtual:publish_location",
        "virtual:data_privacy",
        "virtual:newsletter",
        "virtual:email",
        "ccm:lifecyclecontributer_publisher",
        "ccm:replicationsource",
        "ccm:replicationsource",
        "ccm:replicationsource",
        "ccm:general_identifier",
        "ccm:wwwurl",
        "ccm:wwwurl",
        "ccm:wwwurl",
        "ccm:wwwurl",
        "ccm:oeh_digitalCompetencies",
        "ccm:oeh_languageLevel",
        "cclom:aggregationlevel",
        "ccm:curriculum",
        "ccm:lifecyclecontributer_author",
        "ccm:author_freetext",
        "ccm:custom_license",
        "ccm:custom_license",
        "cclom:title",
        "cclom:title",
        "cclom:title",
        "cclom:title",
        "ccm:editorial_state",
        "ccm:editorial_checklist",
        "ccm:editorial_checklist",
        "ccm:editorial_checklist",
        "ccm:editorial_checklist",
        "ccm:pointsdefault",
        "ccm:collectionshorttitle",
        "ccm:sourceContentType",
        "ccm:toolCategory",
        "ccm:objecttype",
        "ccm:educationalintendedenduserrole",
        "ccm:oeh_widgets",
        "ccm:oeh_lrt_aggregated",
        "ccm:oeh_lrt",
        "ccm:educationalcontext",
        "cm:description",
        "cm:title",
        "virtual:type",
        "cclom:general_description",
        "ccm:objecttype",
        "ccm:commonlicense_key",
        "ccm:taxonid",
        "cclom:typicallearningtime",
        "cclom:duration",
        "ccm:unmetLegalCriteria",
        "ccm:oeh_buffet_criteria",
        "cclom:format",
        "virtual:mediatype",
        "ccm:oeh_languageTarget",
        "cclom:general_language",
        "cclom:classification_keyword",
        "ccm:oeh_competence_check",
        "ccm:oeh_competence_requirements",
        "ccm:competence",
        "ccm:oeh_internalDocument",
        "cclom:size",
        "cclom:status",
        "virtual:editorial_title",
        "virtual:editorial_replicationsource",
        "virtual:editorial_publisher",
        "ccm:oeh_signatures",
        "ccm:license_to",
        "ccm:published_date",
        "ccm:oeh_interoperability",
        "ccm:oeh_usability",
        "ccm:oeh_accessibility_security",
        "ccm:oeh_quality_personal_law",
        "ccm:oeh_quality_protection_of_minors",
        "ccm:oeh_quality_copyright_law",
        "ccm:oeh_quality_criminal_law",
        "ccm:oeh_quality_login",
        "ccm:oeh_quality_relevancy_for_education",
        "ccm:containsAdvertisement",
        "ccm:oeh_accessibility_open",
        "ccm:oeh_accessibility_find",
        "ccm:oeh_quality_transparentness",
        "ccm:oeh_quality_didactics",
        "ccm:oeh_quality_medial",
        "ccm:oeh_quality_language",
        "ccm:oeh_quality_neutralness",
        "ccm:oeh_quality_currentness",
        "ccm:oeh_quality_data_privacy",
        "cclom:general_keyword",
        "ccm:educationallearningresourcetype",
        "ccm:collection_ordered_position",
        "cclom:location",
        "ccm:notes",
        "ccm:license_oer",
        "ccm:fskRating",
        "ccm:dataProtectionConformity",
        "ccm:accessibilitySummary",
        "ccm:price",
        "ccm:conditionsOfAccess",
        "cclom:general_keyword",
        "ccm:classification_purpose",
        "ccm:educationaldifficulty",
        "ccm:educationalinteractivitytype",
        "cm:name",
        "cclom:general_keyword",
        "ccm:restricted_access",
        "ccm:tool_category",
        "ccm:tool_producer",
        "ccm:tool_instance_key",
        "ccm:tool_instance_secret",
        "ccm:tool_instance_params",
        "ccm:tool_instance_license",
        "ccm:tool_instance_support_contact",
        "ccm:tool_instance_support_mail",
        "ccm:tool_instance_provider",
        "ccm:tool_instance_provider_url",
        "ccm:tool_instance_access",
        "ccm:lifecyclecontributer_unknown",
        "ccm:lifecyclecontributer_initiator",
        "ccm:lifecyclecontributer_terminator",
        "ccm:lifecyclecontributer_validator",
        "ccm:lifecyclecontributer_editor",
        "ccm:lifecyclecontributer_graphical_designer",
        "ccm:lifecyclecontributer_technical_implementer",
        "ccm:lifecyclecontributer_content_provider",
        "ccm:lifecyclecontributer_educational_validator",
        "ccm:lifecyclecontributer_script_writer",
        "ccm:lifecyclecontributer_instructional_designer",
        "ccm:lifecyclecontributer_subject_matter_expert",
        "ccm:metadatacontributer_creator",
        "ccm:metadatacontributer_validator",
        "ccm:metadatacontributer_provider",
        "cm:created",
        "cm:modified",
        "license",
        "sys:node-uuid",
        "ccm:educationaltypicalagerange",
        "ccm:imported_object_appname",
        "add_to_stream_title",
        "add_to_stream_description",
        "add_to_stream_priority",
        "feedback_rating",
        "feedback_comment",
        "collection_feedback",
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
    # TODO: use database for connection

    if not await has_table("timeline"):
        await create_timeline_table()

    engine, timeline_table = await get_table()
    insert_statement = timeline_table.insert().values(
        timestamp=datetime.now().timestamp(), quality_matrix=data
    )
    engine.connect().execute(insert_statement)


async def quality_matrix() -> QUALITY_MATRIX_RETURN_TYPE:
    with open("test_response.json") as test_file:
        output = json.loads(test_file.readlines()[0])

    if False:
        properties = get_properties()
        output = {k: {} for k in properties}
        for replication_source, total_count in all_sources().items():
            response = all_missing_properties(properties, replication_source)
            for key, value in response.aggregations.to_dict().items():
                output[key] |= missing_fields(value, total_count, replication_source)

        logger.debug(f"Quality matrix output:\n{output}")
        output = api_ready_output(output)
    return output

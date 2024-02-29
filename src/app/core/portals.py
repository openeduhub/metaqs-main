from datetime import datetime
from pprint import pformat
from typing import Optional

import httpx
from fastapi import HTTPException
from fastapi_utils.tasks import repeat_every

from app.core.constants import (
    COLLECTION_COMMUNITIES_ROOT_NODE_ID,
    COLLECTION_TOPIC_PORTALS_ROOT_NODE_ID,
)
from app.core.custom_logging import logger

# ToDo: implement tests for this module (mock requests / responses)

portal_data_cache: dict = {}


def fetch_and_merge_portal_collections(mode: str = "flat") -> Optional[dict]:
    """
    Fetches "Fachportal"- and "Community"-collections and returns a merged dictionary.

    This function supports two modes:
    * "flat" (default): returns a flat dictionary (key: the title of the collection; value: the node-ID)
    * "nested": returns a dictionary with nested properties

    :return: If both API requests were successful, returns the (merged) dictionary containing
    "portal"-collection-names (key) and their collection node-ID (value).
    """

    if mode == "flat" or mode == "nested":
        pass
    else:
        logger.exception(
            f"This function does not support the provided argument {mode}. "
            f"Please use either 'flat' or 'nested' as a function argument!"
        )

    root_node_id_topic_portals: str = COLLECTION_TOPIC_PORTALS_ROOT_NODE_ID
    root_node_id_communities: str = COLLECTION_COMMUNITIES_ROOT_NODE_ID

    topic_portals: dict = _fetch_portal_collection_children_from_edu_sharing(root_node_id_topic_portals)
    topic_portals_timestamp: datetime = datetime.now()
    logger.debug(f"Retrieved topic portals at {topic_portals_timestamp}:\n" f"{pformat(topic_portals)}")

    community_portals: dict = _fetch_portal_collection_children_from_edu_sharing(root_node_id_communities)
    community_timestamp: datetime = datetime.now()
    logger.debug(f"Retrieved community portals at {community_timestamp}:\n" f"{pformat(community_portals)}")
    portals_aggregated = dict()
    if topic_portals and community_portals:
        if mode == "flat":
            portals_aggregated.update(topic_portals)
            portals_aggregated.update(community_portals)
        elif mode == "nested":
            # the nested mode might be necessary due to the api.py implementation of "valid_node_ids",
            # which is used as example data for the OpenAPI docs
            portals_aggregated = {"Alle Fachportale": {}}
            portals_aggregated["Alle Fachportale"][root_node_id_topic_portals] = topic_portals
            portals_aggregated["Alle Fachportale"][root_node_id_communities] = community_portals
    if portals_aggregated:
        # only return the dict if API query was successful
        return portals_aggregated
    else:
        return None


def _fetch_portal_collection_children_from_edu_sharing(node_id_of_collection_root: str) -> dict[str, str]:
    """
    Load "Community-" or "Fach-Portal" collection names and their node-IDs from the edu-sharing REST API.

    :return: If the API request was successful,
    returns a dictionary containing "portal"-collection-names (key) and collection node-IDs (value).
    """
    # ToDo: control to-be-queried edu-sharing repo via .env setting
    _collection_root_node_id: str = node_id_of_collection_root
    # all children of the provided root nodeId are:
    # - either topic portals ("Fachportale" -> "Deutsch", "Spanisch", "Nachhaltigkeit")
    # - or community portals (e.g. "Projektmanagement -GPM", "RPI-virtuell" etc.)
    _edu_sharing_repository_base_url: str = "https://redaktion.openeduhub.net/edu-sharing/"
    _edu_sharing_api_path: str = (
        f"rest/collection/v1/collections/local/" f"{_collection_root_node_id}/children/collections"
    )
    _edu_sharing_url: str = f"{_edu_sharing_repository_base_url}{_edu_sharing_api_path}"
    _param_skip_count: str = str(0)
    _param_max_items: str = str(10000)  # the max amount of 'portal'-collections expected:
    # as of 2024-02-27 we count 31 'Fachportale' and 7 "Community-Portale"
    _param_sort_properties: str = "ccm:collection_ordered_position"
    _param_sort_ascending: str = "true"
    _param_scope: str = "MY"
    _query_parameters: dict[str, str] = {
        "skipCount": _param_skip_count,
        "maxItems": _param_max_items,
        "sortProperties": _param_sort_properties,
        "sortAscending": _param_sort_ascending,
        "scope": _param_scope,
    }

    logger.info(
        f"Loading 'portal'-collections ('Fachportal' or 'Community-Portal') from edu-sharing " f"{_edu_sharing_url} ..."
    )

    response = httpx.get(url=_edu_sharing_url, params=_query_parameters)
    if response.status_code != 200:
        logger.exception(
            f"Failed to load portal ('Fachportal-' or 'Community-Portal') data: "
            f"{response.status_code}, {response.text}"
        )
        raise HTTPException(
            status_code=502,
            detail=f"Failed to load portal data from edu-sharing: "
            f"{_edu_sharing_url} . Received HTTP Status: {response.status_code} Message: {response.text}",
        )
    if response.is_success:
        r_json = response.json()
        try:
            portal_names_to_node_ids: dict[str, str] = {}
            pagination_count: int = r_json["pagination"]["total"]
            pagination_total: int = r_json["pagination"]["count"]
            if "collections" in r_json:
                collections: list[dict] = r_json["collections"]
                if collections and isinstance(collections, list):
                    for collection in collections:
                        # we need to use "collection.title" because some collections have "Umlaute" in their name,
                        # ('collection.name' strings do not have Umlaute, which would cause problems)
                        collection_title: str = collection["title"]
                        if _collection_root_node_id == COLLECTION_COMMUNITIES_ROOT_NODE_ID:
                            # Prefixing community names, so they're more easily distinguishable
                            collection_title = f"Community - {collection_title}"
                        collection_node_id: str = collection["ref"]["id"]  # nodeId of "Fach-" or "Community-Portal"
                        if (
                            collection_title
                            and isinstance(collection_title, str)
                            and collection_node_id
                            and isinstance(collection_node_id, str)
                        ):
                            portal_names_to_node_ids.update({collection_title: collection_node_id})
            logger.info(
                f"Received {len(portal_names_to_node_ids)} 'portal'-collections. "
                f"(Expected 'pagination.count' / 'pagination.total': "
                f"{pagination_count} / {pagination_total})"
            )
            if len(portal_names_to_node_ids) == pagination_count and pagination_count == pagination_total:
                # only return the dictionary if the amount of items received is equal to the result counter
                return portal_names_to_node_ids
            # ToDo: if pagination.count < pagination.total, we need to iterate over API result pages
            #   but this event should not happen anytime soon
        except KeyError as ke:
            logger.exception(
                "Failed to retrieve names and nodeIds of topic portals from edu-sharing. "
                "The JSON response did not provide the expected key-value pairs!"
            )
            raise ke


def get_portal_cache() -> dict:
    """
    Get the currently cached values for "Community-" and "Fachportal"-collections as a dict.
    """
    return portal_data_cache


def reset_portal_cache():
    """
    Resets the previously cached "portal"-values by clearing the dictionary first,
    then overwriting it with fresh data from the edu-sharing API.

    (This function is mainly intended to hard-reset the cached dictionary from an API route
    without restarting the whole metaQS service.)
    """
    global portal_data_cache
    portal_data_cache = {}
    new_cache = fetch_and_merge_portal_collections()
    if new_cache:
        portal_data_cache = new_cache
        return portal_data_cache
    else:
        logger.warning("Reset the 'portal'-cache, but failed to retrieve fresh values from edu-sharing.")


@repeat_every(seconds=900, logger=logger)
def update_portal_data_cache():
    """
    Periodically updates the cached "portal"-data (names and node-IDs) and stores it within the global variable
    'portal_data_cache' if the necessary API requests were successful.
    If failing to retrieve valid data from the edu-sharing API, the (previously) cached data is not touched until
    the next try.
    """
    # ToDo: set to repeat every 15/30 minutes after confirming intended behaviour
    merged_portal_data = fetch_and_merge_portal_collections()
    if merged_portal_data:
        global portal_data_cache
        portal_data_cache.update(merged_portal_data)
    else:
        logger.warning(
            "Periodic update of the portal cache failed! "
            "The previously cached data will be be kept until the next update attempt. "
            "(Retrying in a few minutes...)"
        )


if __name__ == "__main__":
    all_collections_and_node_ids = fetch_and_merge_portal_collections()
    logger.info(f"Portals aggregated:\n" f"{pformat(all_collections_and_node_ids)}")
    print(portal_data_cache)
    nested_cache: dict = fetch_and_merge_portal_collections("nested")
    logger.info(f"Nested portal cache:\n{nested_cache}")
    pass

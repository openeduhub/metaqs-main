import uuid

from elasticsearch_dsl import Q
from elasticsearch_dsl.aggs import A
from elasticsearch_dsl.response import Response
from fastapi import HTTPException
from pydantic import BaseModel

from app.api.collections.models import CollectionNode
from app.core.models import ElasticResourceAttribute
from app.elastic.elastic import ResourceType
from app.elastic.search import Search


class CollectionMaterialCount(BaseModel):
    node_id: uuid.UUID
    title: str
    materials_count: int


async def get_collection_material_counts(collection: CollectionNode) -> list[CollectionMaterialCount]:
    """
    Compute the number of materials for every node of the collection subtree (including the root) defined
    by given collection_id.

    :param collection: The collection tree for which material counts should be computed.
    """
    # The approach here is:
    # - Step #1: run the equivalent of a
    #           select
    #               collection_leaf, count(*)
    #           from materials
    #           where 'material somewhere in collection subtree'
    #           group by collection_leaf
    #   query on elastic. This will return the number of materials that are directly within each collection id. However,
    #   it will only return collection_ids for which the count is larger than 0.
    # - Hence Step #2: Loop through the tree for which we want the counts, and just fill in the zeros where appropriate
    #   to get a result for all nodes of the collection tree.
    #
    # While doing this, we also have to combine the search result with the predefined collection tree to fill in the
    # titles of the collections, as they won't be returned by the elasticsearch. Note that the set of nodes of the
    # passed in collection tree is a superset of the results we get back from the issued elastic query, as the query
    # specifies to count only materials within the given collection tree root (via the collection path). I.e. there will
    # not be counts for collections returned from elasticsearch that are not in the respective collection tree.

    search = (
        Search()
        .base_filters()
        .type_filter(ResourceType.MATERIAL)
        # fixme: below is copy pasted from missing_materials.py and should be consolidated
        #        into a MaterialSearch builder pattern
        .query(
            Q(
                "bool",
                **{
                    "minimum_should_match": 1,
                    "should": [
                        Q("match", **{ElasticResourceAttribute.COLLECTION_PATH.keyword: str(collection.node_id)}),
                        Q("match", **{ElasticResourceAttribute.COLLECTION_NODEREF_ID.keyword: str(collection.node_id)}),
                    ],
                },
            )
        )
        .extra(size=0)
    )

    search.aggs.bucket(
        "collections",  # the name used for the aggregation, referenced when iterating over the result
        A("terms", field=ElasticResourceAttribute.COLLECTION_NODEREF_ID.keyword, size=65536),
    )

    response: Response = search.execute()

    if not response.success():
        raise HTTPException(status_code=502, detail="Failed to fetch data from elasticsearch")

    # the collections where the count is larger than zero
    counts: dict[uuid.UUID, int] = {
        uuid.UUID(bucket["key"]): bucket["doc_count"] for bucket in response.aggregations["collections"]["buckets"]
    }

    # fixme: eventually sort in the frontend and document in the API that the order of elements is unspecified?
    return sorted(
        [
            CollectionMaterialCount(node_id=node.node_id, title=node.title, materials_count=counts.get(node.node_id, 0))
            for node in collection.flatten(root=True)
        ],
        key=lambda c: c.materials_count,
    )

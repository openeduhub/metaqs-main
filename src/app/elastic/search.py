from __future__ import annotations

import uuid
from enum import Enum
from pprint import pformat
from uuid import UUID

import elasticsearch_dsl
from elasticsearch_dsl.query import Q, Term, Bool, Terms, Match, Query, Wildcard
from elasticsearch_dsl.response import Response

from app.core.config import ELASTIC_INDEX
from app.core.logging import logger
from app.elastic.attributes import ElasticResourceAttribute
from app.elastic.dsl import qterm


class ResourceType(str, Enum):
    COLLECTION = "COLLECTION"
    MATERIAL = "MATERIAL"


class Search(elasticsearch_dsl.Search):  # todo remove entirely in favour of below Material and CollectionSearch
    __base_filter = [
        qterm(qfield=ElasticResourceAttribute.PERMISSION_READ, value="GROUP_EVERYONE"),
        qterm(qfield=ElasticResourceAttribute.EDU_METADATASET, value="mds_oeh"),
        qterm(qfield=ElasticResourceAttribute.PROTOCOL, value="workspace"),
    ]

    def __init__(self, index=ELASTIC_INDEX, **kwargs):
        super(Search, self).__init__(index=index, **kwargs)

    # TODO: These are always applied - make them part of the init itself
    def base_filters(self) -> Search:
        search = self
        for entry in self.__base_filter:
            search = search.filter(entry)
        return search

    def type_filter(self, resource_type: ResourceType) -> Search:
        if resource_type == ResourceType.COLLECTION:
            return self.filter(Term(**{ElasticResourceAttribute.TYPE.path: "ccm:map"}))
        return self.filter(Term(**{ElasticResourceAttribute.TYPE.path: "ccm:io"}))

    def node_filter(self, resource_type: ResourceType, node_id: uuid.UUID) -> Search:
        # make self.to_dict() json serializable
        node_id = str(node_id)
        search = self.type_filter(resource_type=resource_type)

        if resource_type is ResourceType.COLLECTION:
            return search.filter(qterm(qfield=ElasticResourceAttribute.PATH, value=node_id))
        return search.filter(qterm(qfield=ElasticResourceAttribute.COLLECTION_PATH, value=node_id))

    def non_series_objects_filter(self):
        return self.filter(Q("bool", **{"must_not": [{"term": {"aspects": "ccm:io_childobject"}}]}))

    def text_only_filter(self):
        return self.filter(
            Q(
                {
                    "terms": {
                        f"{ElasticResourceAttribute.MIMETYPE.path}.keyword": [
                            "application/pdf",
                            "application/msword",
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            "application/vnd.oasis.opendocument.text",
                            "text/html",
                            "application/vnd.ms-powerpoint",
                        ]
                    }
                }
            ),
        )

    def execute(self, ignore_cache=False) -> Response:
        logger.debug(f"Sending query to elastic:\n{pformat(self.to_dict())}")
        response = super(Search, self).execute(ignore_cache=ignore_cache)
        logger.debug(f"Response received from elastic:\n{pformat(response.to_dict())}")
        return response


_base_filters = [
    Term(**{ElasticResourceAttribute.PERMISSION_READ.keyword: "GROUP_EVERYONE"}),
    Term(**{ElasticResourceAttribute.EDU_METADATASET.keyword: "mds_oeh"}),
    Term(**{ElasticResourceAttribute.PROTOCOL.path: "workspace"}),  # fixme: why not keyword?
]


class _Search(elasticsearch_dsl.Search):
    def missing_attribute_filter(self, **attributes: ElasticResourceAttribute) -> MaterialSearch:
        """
        Only return documents where at least one of the provided attributes is missing, empty or "invalid".

        The definition of valid depends on the respective attributes and usually is
        - "not empty string"
        - "not null"
        - "not empty list"

        fixme: We use this for both, Material- and CollectionSearch for now. However, the set of allowed attributes
               obviously depends on the type of document that is searched. E.g. the following statement makes no sence:
                    CollectionSearch().missing_attribute_filter(license=ElasticResourceAttribute.LICENSE)
               because collections do not have a License attribute.

        This method will make used of [named queries](1) for every provided attribute. This allows to check for each
        hit which of the documents' attributes are considered missing.
        By doing so, we avoid mixing elastic search validation of attributes with python code validation. I.e.
        whether an attribute is missing is fully defined via the elastic search query - Hence we avoid reimplementing
        the elastic search validation on the returned materials.

        Example for checking the names queries:

        ```python
        hits = search.missing_attribute_filter(licence=ElasticResourceAttribute.LICENSE).execute().hits
        for hit in hits:
            for matched_query in hit.meta.matched_queries:
                print(matched_query) # a string with the name of the matched query ("licence" in this case)
        ```

        The name of the attribute subquery is defined by the keyword used to pass in the ElasticResourceAttribute.

        [1]: https://www.elastic.co/guide/en/elasticsearch/reference/7.17/query-dsl-bool-query.html#named-queries)
        :param attributes: The keys will define the query names, the values define the attributes to check.
        """

        # fixme: technically we could pass in attributes of collections here, which does not make any sense.
        #        Solution: separate the ElasticResourceAttributes into Collection and Material attributes!

        def attribute_specific_query(name: str, attribute: ElasticResourceAttribute) -> Query:
            if attribute == ElasticResourceAttribute.LICENSES:
                # fixme: eventually change this to a whitelist?
                return Bool(
                    should=[
                        Terms(
                            **{ElasticResourceAttribute.LICENSES.keyword: ["UNTERRICHTS_UND_LEHRMEDIEN", "NONE", ""]}
                        ),
                        Bool(must_not=Q("exists", field=ElasticResourceAttribute.LICENSES.path)),
                    ],
                    minimum_should_match=1,
                    _name=name,
                )

            return Bool(must_not=Wildcard(**{attribute.path: {"value": "*"}}), _name=name)

        return self.filter(
            Bool(
                minimum_should_match=1,
                should=[attribute_specific_query(name, attribute) for name, attribute in attributes.items()],
            )
        )

    def execute(self, ignore_cache=False) -> Response:
        logger.debug(f"Sending query to elastic:\n{pformat(self.to_dict())}")
        response = super(_Search, self).execute(ignore_cache=ignore_cache)
        logger.debug(f"Response received from elastic:\n{pformat(response.to_dict())}")
        return response


class CollectionSearch(_Search):
    def __init__(self, index=ELASTIC_INDEX, **kwargs):
        super().__init__(index=index, **kwargs)
        self.query = Bool(
            filter=[
                *_base_filters,
                Term(**{ElasticResourceAttribute.TYPE.path: "ccm:map"}),  # fixme: why not keyword?
            ]
        )

    def collection_filter(self, collection_id: UUID) -> CollectionSearch:
        """
        Filter for collections that are nodes of the subtree defined by given collection id.
        :param collection_id: The ID of the collection that defines the subtree within which to search.
        """
        # make the search.to_dict json serializable
        collection_id = str(collection_id)
        exact_collection = Term(**{ElasticResourceAttribute.NODE_ID.keyword: collection_id})
        collection_subtree = Term(**{ElasticResourceAttribute.PATH.path: collection_id})
        return self.filter(exact_collection | collection_subtree)


class MaterialSearch(_Search):
    def __init__(self, index=ELASTIC_INDEX, **kwargs):
        super().__init__(index=index, **kwargs)
        self.query = Bool(
            filter=[
                *_base_filters,
                Term(**{ElasticResourceAttribute.TYPE.path: "ccm:io"}),  # fixme: why not keyword?
            ]
        )

    def oer_filter(self) -> MaterialSearch:
        """Return a new search with an added filter to only return OER materials."""
        return self.filter(Terms(**{ElasticResourceAttribute.LICENSES.keyword: ["CC_0", "PDM", "CC_BY", "CC_BY_SA"]}))

    def collection_filter(self, collection_id: UUID, transitive: bool) -> MaterialSearch:
        """
        Return a new search with an added filter to only return materials from given collection.
        :param collection_id: The collection the materials have to be in.
        :param transitive: Whether to include materials that are not directly in given collection, but in any of the
                           collection-nodes of the subtree defined by the collection.
        """
        collection_id = str(collection_id)
        exact_collection = Term(**{ElasticResourceAttribute.COLLECTION_NODEREF_ID.keyword: collection_id})
        if transitive:
            collection_subtree = Match(**{ElasticResourceAttribute.COLLECTION_PATH.keyword: collection_id})
            return self.filter(exact_collection | collection_subtree)
        else:
            return self.filter(exact_collection)

    # def source(self, *attributes: ElasticResourceAttribute) -> MaterialSearch:
    #     """Only return the specified attributes for the matched search results."""
    #     # fixme: eventually implement validation as drafted below.
    #     # material_attributes = {
    #     #     ElasticResourceAttribute.TITLE,
    #     #     ElasticResourceAttribute.DESCRIPTION,
    #     #     ElasticResourceAttribute.EDU_CONTEXT,
    #     #     ...
    #     # }
    #     # for attr in attributes:
    #     #     assert attr in material_attributes, f"{attr} is non a valid material attribute"
    #     return super().source(fields=[attr.path for attr in attributes])

    def non_series_objects_filter(self) -> MaterialSearch:
        """Only return materials that are not series objects."""
        return self.filter(Bool(**{"must_not": [{"term": {"aspects": "ccm:io_childobject"}}]}))

from __future__ import annotations
from pprint import pformat
from uuid import UUID

import elasticsearch_dsl
from elasticsearch_dsl.query import Term, Bool
from elasticsearch_dsl.response import Response
from starlette_context import context
from starlette_context.errors import ContextDoesNotExistError

from app.core.config import ELASTIC_INDEX
from app.core.logging import logger


class Search(elasticsearch_dsl.Search):
    def __init__(self, index=ELASTIC_INDEX, **kwargs):
        super(Search, self).__init__(index=index, **kwargs)

    def base_filters(self) -> Search:
        return (
            self.filter(Term(**{"permissions.Read.keyword": "GROUP_EVERYONE"}))
            .filter(Term(**{"properties.cm:edu_metadataset.keyword": "mds_oeh"}))
            .filter(Term(**{"nodeRef.storeRef.protocol": "workspace"}))
        )

    # fixme: Is ccm:map really a collection? or is this accidentally swapped here?
    def collection(self, id: UUID) -> Search:
        """Query collections."""
        # fixme: Define collection!
        return self.query(Bool(filter=[Term(type="ccm:map"), Term(path=id)]))

    def material(self, id: UUID) -> Search:
        """Query materials."""
        # fixme: Define material!
        return self.query(
            Bool(filter=[Term(type="ccm:io"), Term(**{"collections.path.keyword": id})])
        )

    def execute(self, ignore_cache=False) -> Response:
        logger.debug(f"Sending query to elastic:\n{pformat(self.to_dict())}")

        response = super(Search, self).execute(ignore_cache=ignore_cache)

        logger.debug(f"Response received from elastic:\n{pformat(response.to_dict())}")

        # TODO: Refactor into speaking function,e.g. see RawcontextMiddleware
        #  https://starlette-context.readthedocs.io/en/latest/middleware.html
        try:
            context["elastic_queries"] = context.get("elastic_queries", []) + [
                {"query": self.to_dict(), "response": response.to_dict()}
            ]
        except ContextDoesNotExistError:
            pass

        return response

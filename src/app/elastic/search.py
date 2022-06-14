from pprint import pformat

import elasticsearch_dsl
from elasticsearch_dsl.response import Response
from starlette_context import context
from starlette_context.errors import ContextDoesNotExistError

from app.core.config import ELASTIC_INDEX
from app.core.logging import logger
from app.elastic.filters import base_filter


class Search(elasticsearch_dsl.Search):
    def __init__(self, index=ELASTIC_INDEX, **kwargs):
        super(Search, self).__init__(index=index, **kwargs)

    def base_filters(self):
        return add_base_match_filters(self)

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


def add_base_match_filters(search: Search) -> Search:
    for entry in base_filter:
        search = search.filter(entry)
    return search

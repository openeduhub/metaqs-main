from pprint import pformat

import elasticsearch_dsl
from starlette_context import context
from starlette_context.errors import ContextDoesNotExistError

from app.core.config import ELASTIC_INDEX
from app.core.logging import logger


class Search(elasticsearch_dsl.Search):
    def __init__(self, index=ELASTIC_INDEX, **kwargs):
        super(Search, self).__init__(index=index, **kwargs)

    def execute(self, ignore_cache=False):
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

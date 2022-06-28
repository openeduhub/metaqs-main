from pprint import pformat

from elasticsearch_dsl import Search as ElasticSearch
from starlette_context import context
from starlette_context.errors import ContextDoesNotExistError

from src.app.core.config import DEBUG, ELASTIC_INDEX
from src.app.core.logging import logger

from .fields import Field
from .utils import handle_text_field


class Search(ElasticSearch):
    def __init__(self, index=ELASTIC_INDEX, **kwargs):
        super(Search, self).__init__(index=index, **kwargs)

    def source(self, source_fields=None, **kwargs):
        if source_fields:
            source_fields = [
                (field.path if isinstance(field, Field) else field)
                for field in source_fields
            ]
        return super(Search, self).source(source_fields, **kwargs)

    def sort(self, *keys):
        return super(Search, self).sort(*[handle_text_field(key) for key in keys])

    def execute(self, ignore_cache=False):
        if DEBUG:
            logger.debug(f"Sending query to elastic:\n{pformat(self.to_dict())}")

        response = super(Search, self).execute(ignore_cache=ignore_cache)

        # TODO: Refactor
        if DEBUG:
            logger.debug(
                f"Response received from elastic:\n{pformat(response.to_dict())}"
            )

        # TODO: Refactor into speaking function,e.g. see RawcontextMiddleware https://starlette-context.readthedocs.io/en/latest/middleware.html
        try:
            context["elastic_queries"] = context.get("elastic_queries", []) + [
                {"query": self.to_dict(), "response": response.to_dict()}
            ]
        except ContextDoesNotExistError:
            pass

        return response

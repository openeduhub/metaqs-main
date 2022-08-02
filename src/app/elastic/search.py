from pprint import pformat

import elasticsearch_dsl
from elasticsearch_dsl.response import Response

from app.core.config import ELASTIC_INDEX
from app.core.logging import logger
from app.core.models import ElasticResourceAttribute
from app.elastic.dsl import qterm


class Search(elasticsearch_dsl.Search):
    __base_filter = [
        qterm(qfield=ElasticResourceAttribute.PERMISSION_READ, value="GROUP_EVERYONE"),
        qterm(qfield=ElasticResourceAttribute.EDU_METADATASET, value="mds_oeh"),
        qterm(qfield=ElasticResourceAttribute.PROTOCOL, value="workspace"),
    ]

    def __init__(self, index=ELASTIC_INDEX, **kwargs):
        super(Search, self).__init__(index=index, **kwargs)

    def base_filters(self):
        def add_base_filters(search: Search) -> Search:
            for entry in self.__base_filter:
                search = search.filter(entry)
            return search

        return add_base_filters(self)

    def execute(self, ignore_cache=False) -> Response:
        logger.debug(f"Sending query to elastic:\n{pformat(self.to_dict())}")
        response = super(Search, self).execute(ignore_cache=ignore_cache)
        logger.debug(f"Response received from elastic:\n{pformat(response.to_dict())}")
        return response

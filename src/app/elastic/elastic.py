from enum import Enum

from elasticsearch_dsl.query import Query, Bool

from app.core.models import ElasticResourceAttribute, forbidden_licenses
from app.elastic.dsl import qnotexists, qterms


class ResourceType(str, Enum):
    COLLECTION = "COLLECTION"
    MATERIAL = "MATERIAL"


def query_missing_material_license(name: str = "missing_license") -> Query:
    """
    :param name: An optional alias for the should query, that can be used to identify which query matched.
                 See: https://www.elastic.co/guide/en/elasticsearch/reference/7.17/query-dsl-bool-query.html#named-queries
    """
    qfield = ElasticResourceAttribute.LICENSES
    return Bool(
        should=[
            qterms(
                qfield=qfield,
                values=forbidden_licenses,
            ),
            qnotexists(qfield=qfield),
        ],
        minimum_should_match=1,
        _name=name,
    )

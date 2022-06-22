from typing import List, Union

from elasticsearch_dsl import A, Q
from elasticsearch_dsl.aggs import Agg
from elasticsearch_dsl.query import Query

from .fields import ElasticField
from .utils import handle_text_field


def qterm(qfield: Union[ElasticField, str], value, **kwargs) -> Query:
    kwargs[handle_text_field(qfield)] = value
    return Q("term", **kwargs)


def qterms(qfield: Union[ElasticField, str], values: list, **kwargs) -> Query:
    kwargs[handle_text_field(qfield)] = values
    return Q("terms", **kwargs)


def qmatch(**kwargs) -> Query:
    return Q("match", **kwargs)


def qbool(**kwargs) -> Query:
    return Q("bool", **kwargs)


def qexists(qfield: Union[ElasticField, str], **kwargs) -> Query:
    if isinstance(qfield, ElasticField):
        qfield = qfield.path
    return Q("exists", field=qfield, **kwargs)


def qnotexists(qfield: str) -> Query:
    return qbool(must_not=qexists(qfield))


def qboolor(conditions: List[Query]) -> Query:
    return qbool(
        should=conditions,
        minimum_should_match=1,
    )


def afilter(query: Query) -> Agg:
    return A("filter", query)


def amissing(qfield: Union[ElasticField, str]) -> Agg:
    return A("missing", field=handle_text_field(qfield))

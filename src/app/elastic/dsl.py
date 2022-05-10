from typing import List, Union

from elasticsearch_dsl import A, Q
from elasticsearch_dsl.aggs import Agg
from elasticsearch_dsl.query import Query

from .fields import Field
from .utils import handle_text_field


def qterm(qfield: Union[Field, str], value, **kwargs) -> Query:
    kwargs[handle_text_field(qfield)] = value
    return Q("term", **kwargs)


def qterms(qfield: Union[Field, str], values: list, **kwargs) -> Query:
    kwargs[handle_text_field(qfield)] = values
    return Q("terms", **kwargs)


def qmatch(**kwargs) -> Query:
    return Q("match", **kwargs)


def qbool(**kwargs) -> Query:
    return Q("bool", **kwargs)


def qexists(qfield: Union[Field, str], **kwargs) -> Query:
    if isinstance(qfield, Field):
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


def amissing(qfield: Union[Field, str]) -> Agg:
    return A("missing", field=handle_text_field(qfield))

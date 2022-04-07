from typing import List, Union

from elasticsearch_dsl import A, Q
from elasticsearch_dsl.aggs import Agg
from elasticsearch_dsl.query import Query

from .fields import Field
from .utils import handle_text_field


def qsimplequerystring(query: str, qfields: List[Union[Field, str]], **kwargs) -> Query:
    kwargs["query"] = query
    kwargs["fields"] = [
        (qfield.path if isinstance(qfield, Field) else qfield) for qfield in qfields
    ]
    return Q("simple_query_string", **kwargs)


def qterm(qfield: Union[Field, str], value, **kwargs) -> Query:
    kwargs[handle_text_field(qfield)] = value
    return Q("term", **kwargs)


def qterms(qfield: Union[Field, str], values: list, **kwargs) -> Query:
    kwargs[handle_text_field(qfield)] = values
    return Q("terms", **kwargs)


def qmatch(**kwargs) -> Query:
    return Q("match", **kwargs)


def qwildcard(qfield: Union[Field, str], value: str) -> Query:
    if isinstance(qfield, Field):
        qfield = qfield.path
    return Q("wildcard", **{qfield: {"value": value}})


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


def aterms(qfield: Union[Field, str], **kwargs) -> Agg:
    kwargs["field"] = handle_text_field(qfield)
    return A("terms", **kwargs)


def afilter(query: Query) -> Agg:
    return A("filter", query)


def amissing(qfield: Union[Field, str]) -> Agg:
    return A("missing", field=handle_text_field(qfield))


def acomposite(sources: List[Union[Query, dict]], **kwargs) -> Agg:
    return A("composite", sources=sources, **kwargs)


def abucketsort(sort: List[Union[Query, dict]], **kwargs) -> Agg:
    return A("bucket_sort", sort=sort, **kwargs)


def script(source: str, params: dict = None) -> dict:
    snippet = {
        "source": source,
    }
    if params:
        snippet["params"] = params
    return snippet

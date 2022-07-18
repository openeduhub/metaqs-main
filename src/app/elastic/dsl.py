from enum import Enum, auto
from typing import List, Union

from elasticsearch_dsl import A, Q
from elasticsearch_dsl.aggs import Agg
from elasticsearch_dsl.query import Query


class ElasticFieldType(str, Enum):
    KEYWORD = auto()
    TEXT = auto()


class ElasticField(str, Enum):
    def __new__(cls, path: str, field_type: ElasticFieldType):
        obj = str.__new__(cls, [path])
        obj._value_ = path
        obj.path = path
        obj.field_type = field_type
        return obj


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


def aterms(qfield: Union[ElasticField, str], **kwargs) -> Agg:
    kwargs["field"] = handle_text_field(qfield)
    return A("terms", **kwargs)


def handle_text_field(qfield: Union[ElasticField, str]) -> str:
    if isinstance(qfield, ElasticField):
        qfield_key = qfield.path
        if qfield.field_type is ElasticFieldType.TEXT:
            qfield_key = f"{qfield_key}.keyword"
        return qfield_key
    else:
        return qfield

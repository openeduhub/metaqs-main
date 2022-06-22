from enum import Enum, auto


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

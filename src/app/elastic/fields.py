from enum import Enum, auto


class FieldType(str, Enum):
    KEYWORD = auto()
    TEXT = auto()


class Field(str, Enum):
    def __new__(cls, path: str, field_type: FieldType):
        obj = str.__new__(cls, [path])
        obj._value_ = path
        obj.path = path
        obj.field_type = field_type
        return obj

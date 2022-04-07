from typing import Optional

from pydantic.validators import str_validator


def none_to_zero(v: int) -> Optional[int]:
    if v is None:
        return 0
    return v


def none_to_empty_list(v: list) -> Optional[list]:
    if v is None:
        return []
    return v


def empty_to_none(v: str) -> Optional[str]:
    if v == "":
        return None
    return v


class EmptyStrToNone(str):
    @classmethod
    def __get_validators__(cls):
        yield str_validator
        yield empty_to_none

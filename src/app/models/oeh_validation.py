from enum import Enum
from typing import ClassVar, List, Optional
from uuid import UUID

from pydantic import BaseModel, validator

from .util import none_to_empty_list


class OehValidationError(str, Enum):
    MISSING = "missing"
    TOO_SHORT = "too_short"
    TOO_FEW = "too_few"
    LACKS_CLARITY = "lacks_clarity"
    INVALID_SPELLING = "invalid_spelling"

    _lut: ClassVar[dict]


OehValidationError._lut = {
    e.value: e for _, e in OehValidationError.__members__.items()
}


class MaterialFieldValidation(BaseModel):
    missing: Optional[List[UUID]]
    too_short: Optional[List[UUID]]
    too_few: Optional[List[UUID]]
    lacks_clarity: Optional[List[UUID]]
    invalid_spelling: Optional[List[UUID]]

    # validators
    _none_to_empty_list = validator("*", pre=True, allow_reuse=True)(none_to_empty_list)

from enum import Enum

from ._types import NonEmptyString
from ._validators import EitherFieldMixin, OpenCostModel


class InstitutionIdType(Enum):
    ror = "ror"
    isni = "isni"
    ringold = "ringold"


class InstitutionId(OpenCostModel):
    value: NonEmptyString
    type: InstitutionIdType


class InstitutionNameType(Enum):
    full = "full"
    short = "short"


class InstitutionName(OpenCostModel):
    value: NonEmptyString
    type: InstitutionNameType


class InstitutionType(EitherFieldMixin):
    either_fields = ("name", "id")
    name: list[InstitutionName] | None = None
    id: list[InstitutionId] | None = None

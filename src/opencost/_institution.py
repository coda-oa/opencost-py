# Field descriptions and notes are taken from the openCost documentation
# (doc/README.md of https://github.com/opencost-de/opencost), GPL-3.0-or-later,
# vendored as submodule vendor/opencost
from enum import Enum

from pydantic import Field

from ._types import NonEmptyString
from ._validators import EitherFieldMixin, OpenCostModel


class InstitutionIdType(Enum):
    """Identifier scheme an institution can be referenced by."""

    ror = "ror"
    isni = "isni"
    ringold = "ringold"


class InstitutionId(OpenCostModel):
    """Contains persistent identifiers for an institution (§4.1, §3.1)."""

    value: NonEmptyString = Field(description="Institution identifier value, e.g. a ROR id.")
    type: InstitutionIdType = Field(description="Identifier scheme of `value`.")


class InstitutionNameType(Enum):
    """Whether the name is given in full or abbreviated."""

    full = "full"
    short = "short"


class InstitutionName(OpenCostModel):
    """Human-readable institution name (§4.2, §3.2)."""

    value: NonEmptyString = Field(description="Name of the institution.")
    type: InstitutionNameType = Field(description="`full` or `short` name form.")


class InstitutionType(EitherFieldMixin):
    """Contains information to identify the institution.

    Either `id` (persistent identifiers) or `name` (human-readable) must be
    given.
    """

    either_fields = ("name", "id")
    name: list[InstitutionName] | None = Field(
        default=None,
        description=(
            "The names are meant to be human-readable. Either this element or "
            "the institution's `id` is required."
        ),
    )
    id: list[InstitutionId] | None = Field(
        default=None,
        description="Either this element or the institution's `name` is required.",
    )

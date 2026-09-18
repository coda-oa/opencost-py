from typing import Any, ClassVar, Self

from pydantic import BaseModel, ConfigDict, model_validator

from ._types import PartialDate


class OpenCostModel(BaseModel):
    """Base for every openCost domain model.

    ``extra="forbid"``: unknown/misspelled fields fail at construction
    instead of being silently dropped (default ``ignore``).
    ``populate_by_name=True``: aliased fields (``from_`` <-> ``"from"``)
    can be constructed with either spelling; the XML serializer keeps
    using the alias as the wire name.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class EitherFieldMixin(OpenCostModel):
    """Mixin for models that require at least one of the named fields to be set.

    Inherits :class:`OpenCostModel` validation behavior. Do not instantiate directly.
    """

    either_fields: ClassVar[tuple[str, ...]] = ()

    def model_post_init(self, __context: Any) -> None:
        if type(self) is EitherFieldMixin:
            raise TypeError("EitherFieldMixin must not be instantiated directly")

    @model_validator(mode="after")
    def _at_least_one_either_field(self) -> Self:
        names = type(self).either_fields
        if names and not any(getattr(self, name) for name in names):
            choices = " or ".join(f"'{name}'" for name in names)
            raise ValueError(f"at least one of {choices} must be set")
        return self


def _interval_start(value: PartialDate) -> tuple[int, int, int]:
    """Earliest date a validated ``DateFormat`` value can denote.

    A canonical ``PartialDate`` anchors partial values at the start of their
    span (January 1 / the first of the month), so the anchor is the start.
    """
    return value.anchor.year, value.anchor.month, value.anchor.day


def _interval_end(value: PartialDate) -> tuple[int, int, int]:
    """Latest date a validated ``DateFormat`` value can denote.

    Days are not clamped to the length of the month: an upper bound up to
    three days too wide can only make the comparison more permissive, never
    wrongly reject.
    """
    match value.precision:
        case "year":
            return value.anchor.year, 12, 31
        case "month":
            return value.anchor.year, value.anchor.month, 31
        case "day":
            return value.anchor.year, value.anchor.month, value.anchor.day


def _check_date_range(from_: PartialDate, to: PartialDate) -> None:
    """Reject a clearly inverted ``from``/``to`` pair, tolerating mixed precision.

    Precision is flexible by design (§4.1, §7.1.2: ``YYYY``, ``YYYY-MM`` or
    ``YYYY-MM-DD``), so each value is compared as the interval it covers rather
    than as a single day: ``2026`` spans the year, ``2026-02`` the month. Only a
    pair that cannot overlap at all fails -- ``from="2026" to="2026-01-01"`` is
    accepted, ``from="2027-01" to="2026-12"`` is not.

    Precondition: both values already passed ``DateFormat`` validation, which is
    the case for ``mode="after"`` model validators.
    """
    if _interval_start(from_) > _interval_end(to):
        raise ValueError(f"'from' ({from_}) must not be after 'to' ({to})")

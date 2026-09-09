from typing import Any, ClassVar, Self

from pydantic import BaseModel, ConfigDict, model_validator


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

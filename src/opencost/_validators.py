from typing import Annotated, Any, ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

# pydantic's declarative "non-empty list". conlist() would do the same at
# runtime but is a function call in annotation position, which static
# checkers reject; Annotated + Field is the documented type-checker-safe
# spelling of the same Len constraint.
type RequiredList[T] = Annotated[list[T], Field(min_length=1)]


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

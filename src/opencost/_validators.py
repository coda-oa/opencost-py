from typing import Annotated, Any, ClassVar, Self

from pydantic import BaseModel, Field, model_validator

# pydantic's declarative "non-empty list". conlist() would do the same at
# runtime but is a function call in annotation position, which static
# checkers reject; Annotated + Field is the documented type-checker-safe
# spelling of the same Len constraint.
type RequiredList[T] = Annotated[list[T], Field(min_length=1)]


class EitherFieldMixin(BaseModel):
    """Mixin for models that require at least one of the named fields to be set.

    Must be mixed into a ``BaseModel`` subclass. Do not instantiate directly.
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

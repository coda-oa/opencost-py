"""Basic type definitions for OpenCost domain models.

The cost-type definitions are taken from the openCost cost-types glossary
(`Cost_types_glossary.md` of https://github.com/opencost-de/opencost),
GPL-3.0-or-later, vendored as submodule vendor/opencost
"""

import re
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Annotated, Literal, Self

from pydantic import PlainSerializer, PlainValidator, StringConstraints, WithJsonSchema

# pydantic matches `pattern` as an unanchored regex search; the XSD patterns are
# implicitly anchored, so they must be spelled out here.
NonEmptyString = Annotated[str, StringConstraints(min_length=1)]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


_DATE_PATTERN = r"^[0-9]{4}(-[0-9]{2}){0,2}$"

type Precision = Literal["year", "month", "day"]


@dataclass(frozen=True, slots=True)
class PartialDate:
    """A Gregorian calendar date with explicit precision (§4.1, §7.1.2).

    Examples:
        PartialDate.year(2024)
        PartialDate.month(2024, 1)
        PartialDate.day(2024, 1, 31)

    Internally, `anchor` is always a real Python `date`, but `precision`
    preserves whether the original value was YYYY, YYYY-MM, or YYYY-MM-DD.
    """

    anchor: date
    precision: Precision

    def __post_init__(self) -> None:
        """Ensure anchor and precision cannot represent an ambiguous value."""
        if self.precision == "year" and (self.anchor.month != 1 or self.anchor.day != 1):
            raise ValueError("Year-precision PartialDate must use January 1 as its anchor")
        if self.precision == "month" and self.anchor.day != 1:
            raise ValueError("Month-precision PartialDate must use the first day as its anchor")

    @classmethod
    def year(cls, year: int) -> Self:
        return cls(anchor=date(year, 1, 1), precision="year")

    @classmethod
    def month(cls, year: int, month: int) -> Self:
        return cls(anchor=date(year, month, 1), precision="month")

    @classmethod
    def day(cls, year: int, month: int, day: int) -> Self:
        return cls(anchor=date(year, month, day), precision="day")

    @classmethod
    def parse(cls, value: str) -> Self:
        """Parse exactly one of: YYYY, YYYY-MM, YYYY-MM-DD.

        The shape check runs with `fullmatch`: the `pattern` is anchored for
        the exported JSON schema (pydantic matches it unanchored), and
        `fullmatch` additionally rules out the trailing-newline allowance
        that a bare `$` match would give. The int() slices below rely on
        this shape; change the two together.
        """
        if re.fullmatch(_DATE_PATTERN, value) is None:
            raise ValueError("Expected a date in YYYY, YYYY-MM, or YYYY-MM-DD format")
        parts = value.split("-")
        year = int(parts[0])
        month = int(parts[1]) if len(parts) >= 2 else 1
        day = int(parts[2]) if len(parts) == 3 else 1
        try:
            anchor = date(year, month, day)
        except ValueError as exc:  # calendar check the pattern cannot express
            raise ValueError(f"Expected a valid Gregorian date, got {value!r}") from exc
        precision: Precision = ("year", "month", "day")[len(parts) - 1]
        return cls(anchor=anchor, precision=precision)

    @property
    def is_complete(self) -> bool:
        """Whether this represents an actual specified day."""
        return self.precision == "day"

    @property
    def full_date(self) -> date | None:
        """Return a native `date` only when day precision was supplied.

        This avoids accidentally interpreting '2024-01' as 2024-01-01.
        """
        return self.anchor if self.precision == "day" else None

    def __str__(self) -> str:
        """Canonical, lossless wire representation at the stored precision."""
        match self.precision:
            case "year":
                return f"{self.anchor.year:04d}"
            case "month":
                return f"{self.anchor.year:04d}-{self.anchor.month:02d}"
            case "day":
                return self.anchor.isoformat()


type PartialDateInput = str | date | PartialDate | None


def _parse_partial_date(value: object) -> PartialDate:
    """Pydantic input adapter.

    Accepted:
      - PartialDate: retained unchanged
      - date: interpreted as day precision
      - str: parsed as YYYY, YYYY-MM, or YYYY-MM-DD

    Deliberately rejected:
      - datetime: it carries information this type cannot represent, so it
        must not be silently truncated; pass ``value.date()`` explicitly

    Raises ValueError (never TypeError): pydantic-core converts ValueError
    into a ``ValidationError``, which is the package's bad-input contract.
    """
    if isinstance(value, PartialDate):
        return value
    if isinstance(value, datetime):
        raise ValueError(
            "datetime is not accepted for PartialDate; "
            "pass value.date() explicitly if day precision is intended"
        )
    if isinstance(value, date):
        return PartialDate.day(value.year, value.month, value.day)
    if isinstance(value, str):
        return PartialDate.parse(value)
    raise ValueError(
        "Expected PartialDate, datetime.date, or a string in YYYY, YYYY-MM, or YYYY-MM-DD format"
    )


# Precision-preserving canonical form: every input path (Python objects as
# well as parsed XML/JSON text) normalizes through the one validator, so a
# model built from dates or strings compares equal to one parsed back by
# ``from_xml``, and ``to_xml`` re-emits each value at its own precision via
# ``PartialDate.__str__``. WithJsonSchema pins the exported JSON schema to
# the wire spelling: a JSON document carries strings only.
DateFormat = Annotated[
    PartialDate,
    PlainValidator(_parse_partial_date),
    PlainSerializer(str, return_type=str, when_used="always"),
    WithJsonSchema({"type": "string", "pattern": _DATE_PATTERN}),
]


class ContractCostType(Enum):
    """Contract cost type (§7.1.3.5.1.3): the object/purpose of the payment.

    Definitions from the openCost cost-types glossary:

    - `publish`: charges for Open Access publishing within the framework of
      (e.g. Publish & Read) contracts; flat rate to cover all publication
      services for publishing in publication organs covered by the contract.
    - `read`: charges for the read access of a Closed Access portfolio within
      the framework of (e.g. Publish & Read or subscription) contracts.
    - `publish and read`: charges for publishing under 'Publish & Read' or
      'Read & Publish' contracts where the publish and read portions are not
      itemized separately on an invoice.
    - `service fee`: additional charges to cover service and operating costs.
    - `vat`: value added tax.
    """

    publish = "publish"
    read = "read"
    publish_and_read = "publish and read"
    service_fee = "service fee"
    vat = "vat"


class PublicationCostType(Enum):
    """Publication cost type (§7.2.5.1.3): the object/purpose of the payment.

    Definitions from the openCost cost-types glossary:

    - `gold-oa`: charges for the Open Access status in a pure Open Access
      publication organ; usually named APC, BPC etc. on the invoice.
    - `hybrid-oa`: charges for the Open Access status in a Closed Access
      publication organ.
    - `vat`: value added tax.
    - `colour charge`: charges for colour printing (colour images, pages,
      illustrations, etc.); relevance for print versions.
    - `cover charge`: charges for the illustration of a cover (publication of
      content for cover/cover design).
    - `page charge`: charges for excess length or page-based billing (the
      latter may then not appear as an additional charge, but functionally
      replaces a Processing Charge, to be assigned to the gold- or hybrid-oa
      categories).
    - `permission`: charges for the acquisition of a license (right of use,
      e.g. for an image in order to be able to use it within a publication).
    - `publication charge`: publication charges to be paid in the context of
      Closed Access.
    - `reprint`: reproduction charges for copies of publications.
    - `submission fee`: charges for submitting a publication.
    - `payment fee`: charges for the financial transaction of the payment
      (e.g. bank transfer or credit card charges).
    - `other`: all other charges that are not already defined elsewhere in
      the glossary and cannot be assigned to any of the named categories.
    """

    gold_oa = "gold-oa"
    vat = "vat"
    colour_charge = "colour charge"
    cover_charge = "cover charge"
    hybrid_oa = "hybrid-oa"
    other = "other"
    page_charge = "page charge"
    permission = "permission"
    publication_charge = "publication charge"
    reprint = "reprint"
    submission_fee = "submission fee"
    payment_fee = "payment fee"

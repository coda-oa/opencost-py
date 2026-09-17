"""Basic type definitions for OpenCost domain models.

The cost-type definitions are taken from the openCost cost-types glossary
(`Cost_types_glossary.md` of https://github.com/opencost-de/opencost),
GPL-3.0-or-later, vendored as submodule vendor/opencost
"""

from datetime import date
from enum import Enum
from typing import Annotated

from pydantic import AfterValidator, StringConstraints

# pydantic matches `pattern` as an unanchored regex search; the XSD patterns are
# implicitly anchored, so they must be spelled out here.
NonEmptyString = Annotated[str, StringConstraints(min_length=1)]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


def _calendar_date(value: str) -> str:
    """Reject shape-valid but calendar-impossible dates such as `2020-06-31`.

    openCost constrains `date_format` by pattern only, so June the 31st is
    schema-valid upstream -- it shipped in the upstream examples themselves
    (opencost-de/opencost#109). `datetime.date` supplies the calendar check a
    pattern cannot express: month/day ranges and leap years.

    `pattern` owns the shape and runs first, so each component is already ASCII
    digits of width 4 / 2 / 2 -- padded cases included, because pydantic-core
    matches `pattern` with a Rust regex whose `$` does not match before a
    trailing newline. The shape is deliberately not re-checked here; loosening
    `pattern` would silently widen what `int()` accepts (unicode digits, padded
    components, ignored trailing components), so change the two together.
    """
    parts = value.split("-")
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else 1
    day = int(parts[2]) if len(parts) > 2 else 1
    date(year, month, day)
    return value


# The pattern reports shape errors; `_calendar_date` reports calendar errors.
DateFormat = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9]{4}(-[0-9]{2}){0,2}$"),
    AfterValidator(_calendar_date),
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

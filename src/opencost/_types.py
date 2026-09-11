"""Basic type definitions for OpenCost domain models.

The cost-type definitions are taken from the openCost cost-types glossary
(`Cost_types_glossary.md` of https://github.com/opencost-de/opencost),
GPL-3.0-or-later, vendored as submodule vendor/opencost
"""

from enum import Enum
from typing import Annotated

from pydantic import StringConstraints

# pydantic matches `pattern` unanchored (re.search); the XSD patterns are
# implicitly anchored, so they must be spelled out here.
NonEmptyString = Annotated[str, StringConstraints(min_length=1)]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
DateFormat = Annotated[str, StringConstraints(pattern=r"^[0-9]{4}(-[0-9]{2}){0,2}$")]


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

# Field descriptions and notes are taken from the openCost documentation
# (doc/README.md of https://github.com/opencost-de/opencost), GPL-3.0-or-later,
# vendored as submodule vendor/opencost
from __future__ import annotations

from enum import Enum
from typing import Annotated, Self

from pydantic import Field, model_validator

from ._coar import CoarPublicationType
from ._contract import ContractPrimaryIdentifier
from ._institution import InstitutionType
from ._invoice import PublicationInvoiceType
from ._types import NonEmptyString
from ._validators import EitherFieldMixin, OpenCostModel


class PublicationSecondaryIdTypeEnum(Enum):
    """Secondary identifier scheme (§3.1.1)."""

    doi = "doi"
    handle = "handle"
    urn = "urn"
    isbn = "isbn"
    pmid = "pmid"
    pmc = "pmc"
    arxiv = "arxiv"
    oai = "oai"
    local = "local"


class PublicationSecondaryIdType(OpenCostModel):
    """Secondary identifier for the publication (§3.1)."""

    value: NonEmptyString = Field(description="Identifier value.")
    type: PublicationSecondaryIdTypeEnum = Field(description="Identifier scheme of `value`.")


class PublicationSecondaryIdentifiers(OpenCostModel):
    """Contains additional, optional identifiers (§3)."""

    id: Annotated[
        list[PublicationSecondaryIdType],
        Field(
            min_length=1,
            description="Additional (persistent) identifiers for the publication.",
        ),
    ]


class BibliographicInformation(OpenCostModel):
    """Block of bibliographic metadata describing the publication (§2.2).

    This serves as a backup and only has to be given if no `doi` can be
    provided. Contains a subset of Dublin Core elements.
    """

    Title: NonEmptyString = Field(
        description="Title of the publication. Dublin Core term (http://purl.org/dc/terms/title)."
    )
    Publisher: NonEmptyString = Field(
        description="Publisher of the journal. Dublin Core term "
        "(http://purl.org/dc/terms/publisher)."
    )
    isPartOf: NonEmptyString = Field(
        description="Name of the journal. Dublin Core term (http://purl.org/dc/terms/isPartOf)."
    )


class PublicationPrimaryIdentifier(OpenCostModel):
    """Contains the primary identifier for the publication (§2).

    A `doi` is strongly preferred, otherwise a `bibliographic_information`
    block has to be provided instead.
    """

    doi: NonEmptyString | None = Field(
        default=None,
        description="Digital Object Identifier (doi) to identify the "
        "publication. Serves as primary identifier.",
    )
    bibliographic_information: BibliographicInformation | None = Field(
        default=None,
        description="Backup description; only has to be given if no `doi` can be provided.",
    )

    @model_validator(mode="after")
    def _exactly_one_of_doi_or_bibliographic_information(self) -> Self:
        if (self.doi is not None) == (self.bibliographic_information is not None):
            raise ValueError("exactly one of 'doi' or 'bibliographic_information' must be set")
        return self


class PartOfContractType(OpenCostModel):
    """Contains identifiers to link this publication to a contract (§7.1).

    Providing just a `primary_identifier` is possible to denote that a
    publication belongs to a contract but was still paid for individually.
    """

    group_id: NonEmptyString | None = Field(
        default=None,
        description="Identical to the `group_id` of an "
        "`opencost:contract//opencost:cost_data//opencost:invoice_group` "
        "element. Indicates that publication costs relate to that particular "
        "`invoice_group` within a defined accounting period of a contract. "
        "Can be omitted to just link a publication to a certain contract. "
        "Generating a `uuid` or using another type of unique identifier is "
        "recommended.",
    )
    primary_identifier: ContractPrimaryIdentifier = Field(
        description="Identical to the `primary_identifier` of an "
        "`opencost:contract` and indicates that the article was published "
        "under that contract."
    )


class PublicationCostDataType(EitherFieldMixin):
    """Aggregates all publication-related payments (§7).

    Payments are recorded as `invoice` elements; a transformative agreement
    can be referenced via a `part_of_contract` element. At least one of the
    two must be provided.
    """

    either_fields = ("invoice", "part_of_contract")
    invoice: list[PublicationInvoiceType] | None = Field(
        default=None,
        description="An `invoice` block encapsulates payment information and "
        "is meant to correspond to a real-world invoice.",
    )
    part_of_contract: PartOfContractType | None = Field(
        default=None,
        description="Links this publication to a contract.",
    )


class PublicationType(OpenCostModel):
    """Top-level element, corresponds to a single publication for which costs
    are to be recorded (§1)."""

    primary_identifier: PublicationPrimaryIdentifier
    secondary_identifiers: PublicationSecondaryIdentifiers | None = None
    institution: InstitutionType = Field(
        description="Contains information to identify the paying institution."
    )
    publication_type: CoarPublicationType = Field(
        description="Type of the publication as the reporting institution "
        "categorizes it. COAR controlled vocabulary (v3.2) English label or "
        "the corresponding COAR PURL; PURLs are recommended as "
        "language-independent persistent identifiers."
    )
    external_costsplitting: bool | None = Field(
        default=None,
        description="Indicates if costs for this publication have been split "
        "with another institution. This element should only be added if "
        "there is distinct information (either positive or negative) on "
        "external cost splitting.",
    )
    cost_data: PublicationCostDataType = Field(
        description="Aggregates all publication-related payments."
    )

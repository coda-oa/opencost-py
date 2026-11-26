# Field descriptions and notes are taken from the openCost documentation
# (doc/README.md of https://github.com/opencost-de/opencost), GPL-3.0-or-later,
# vendored as submodule vendor/opencost
from __future__ import annotations

from enum import Enum
from typing import Annotated, Self

from pydantic import Field, GetJsonSchemaHandler, model_validator
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema

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
    ark = "ark"
    purl = "purl"


class PublicationPrimaryIdTypeEnum(Enum):
    """Primary identifier scheme (§2.2.1).

    A DOI should be the preferred option; other persistent identifier types
    exist mainly as backup.
    """

    doi = "doi"
    handle = "handle"
    urn = "urn"
    isbn = "isbn"
    arxiv = "arxiv"
    ark = "ark"


class PublicationPrimaryIdType(OpenCostModel):
    """Primary identifier for the publication (§2.2)."""

    value: NonEmptyString = Field(description="Identifier value.")
    type: PublicationPrimaryIdTypeEnum = Field(description="Identifier scheme of `value`.")


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
    """Block of bibliographic metadata describing the publication (§2.3).

    This serves as a backup and should only be used if no other persistent
    identifier is available. Contains a subset of Dublin Core elements.
    """

    Title: NonEmptyString = Field(
        description="Title of the publication. Dublin Core term (http://purl.org/dc/terms/title)."
    )
    Publisher: NonEmptyString = Field(
        description="Publisher of the publication. Dublin Core term "
        "(http://purl.org/dc/terms/publisher)."
    )
    isPartOf: NonEmptyString | None = Field(
        default=None,
        description="Bibliographic host item relation, like a journal (for "
        "articles) or a book (for book chapters). Dublin Core term "
        "(http://purl.org/dc/terms/isPartOf).",
    )


class PublicationHostItemType(OpenCostModel):
    """Bibliographic host item the publication belongs to (§8).

    May be used to store information on a bibliographic host item, like the
    ISBN for a book if the publication describes a book chapter.
    """

    id: Annotated[
        list[PublicationPrimaryIdType],
        Field(
            min_length=1,
            description="Persistent identifiers of the host item.",
        ),
    ]


class PublicationPrimaryIdentifier(OpenCostModel):
    """Contains the primary identifier for the publication (§2).

    Exactly one of `doi`, `id` or `bibliographic_information` has to be
    provided. A persistent identifier is preferred: `id` (or its deprecated
    predecessor `doi`), with `bibliographic_information` as the backup.
    """

    doi: NonEmptyString | None = Field(
        default=None,
        description="Digital Object Identifier (doi) to identify the "
        "publication. Deprecated; kept for backwards compatibility, use `id` "
        "instead.",
    )
    id: PublicationPrimaryIdType | None = Field(
        default=None,
        description="Primary identifier for the publication.",
    )
    bibliographic_information: BibliographicInformation | None = Field(
        default=None,
        description="Backup description; only has to be given if no "
        "persistent identifier can be provided.",
    )

    @model_validator(mode="after")
    def _exactly_one_identifier(self) -> Self:
        present = sum(
            value is not None for value in (self.doi, self.id, self.bibliographic_information)
        )
        if present != 1:
            raise ValueError(
                "exactly one of 'doi', 'id' or 'bibliographic_information' must be set"
            )
        return self

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """Mirror the exactly-one-of model validator as JSON Schema ``oneOf``.
        Pydantic cannot derive ``oneOf`` from ``mode="after"`` validators, so
        the flat all-optional-fields shape is rewritten: each branch requires
        exactly one of the fields, with the generated property schema
        (minus the ``null`` alternative) as the branch's only property.
        """
        schema = handler(core_schema)
        schema["oneOf"] = [
            {
                "type": "object",
                "additionalProperties": False,
                "required": [name],
                "properties": {
                    name: {
                        **schema["properties"][name]["anyOf"][0],
                        "description": schema["properties"][name].get("description"),
                    }
                },
            }
            for name in ("doi", "id", "bibliographic_information")
        ]
        # Branches carry their own ``additionalProperties``; the parent's
        # would reject every key now that ``properties`` is gone.
        schema.pop("properties")
        schema.pop("additionalProperties", None)
        return schema


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
    host_item: PublicationHostItemType | None = Field(
        default=None,
        description="Bibliographic host item this publication belongs to, "
        "like the ISBN for a book if the publication describes a book chapter.",
    )
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

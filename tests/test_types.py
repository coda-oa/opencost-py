"""Static type assertions on the public API surface.

`assert_type` is verified by every compliant type checker; these tests run
under mypy, pyright and pyrefly (see noxfile.py) so the read-side types that
users see are pinned across all of them.
"""

from decimal import Decimal
from typing import assert_type

import opencost
from opencost import (
    CoarPublicationType,
    ContractPrimaryIdentifier,
    ContractPrimaryIdentifierType,
    ContractType,
    Data,
    Dates,
    InstitutionId,
    InstitutionIdType,
    InstitutionType,
    PartOfContractType,
    PublicationAmountPaidType,
    PublicationAmountsPaid,
    PublicationCostDataType,
    PublicationCostType,
    PublicationInvoiceType,
    PublicationPrimaryIdentifier,
    PublicationType,
)


def test_read_side_types_are_canonical() -> None:
    invoice = PublicationInvoiceType(
        dates=Dates(paid="2026"),
        amounts_paid=PublicationAmountsPaid(
            amount_paid=[
                PublicationAmountPaidType(
                    amount=Decimal("1.00"),
                    currency="EUR",
                    cost_type=PublicationCostType.gold_oa,
                )
            ]
        ),
    )

    assert_type(invoice.dates.paid, str | None)
    assert_type(invoice.invoice_number, str | None)
    assert_type(invoice.creditor, str | None)

    amount = invoice.amounts_paid.amount_paid[0]
    assert_type(amount.amount, Decimal)
    assert_type(amount.currency, str)
    assert_type(amount.cost_type, PublicationCostType)
    assert_type(amount.vat, Decimal | None)


def test_public_api_round_trip_types() -> None:
    publication = PublicationType(
        primary_identifier=PublicationPrimaryIdentifier(doi="10.1234/abcd"),
        institution=InstitutionType(
            id=[InstitutionId(type=InstitutionIdType.ror, value="010zzcb52")]
        ),
        publication_type=CoarPublicationType.journal_article,
        cost_data=PublicationCostDataType(
            part_of_contract=PartOfContractType(
                primary_identifier=ContractPrimaryIdentifier(
                    type=ContractPrimaryIdentifierType.ESAC, value="deal_de_1"
                )
            )
        ),
    )
    assert_type(publication.primary_identifier.doi, str | None)
    assert_type(publication.external_costsplitting, bool | None)
    assert_type(publication.cost_data.invoice, list[PublicationInvoiceType] | None)

    data = Data(publication=[publication])
    assert_type(opencost.to_xml(data), str)
    parsed = opencost.from_xml(opencost.to_xml(data))
    assert_type(parsed, Data)
    assert_type(parsed.publication, list[PublicationType] | None)
    assert_type(parsed.contract, list[ContractType] | None)

"""Validate serialized XML against the shipped openCost XSD with lxml."""

from decimal import Decimal
from pathlib import Path

import pytest
from lxml import etree

import opencost
from opencost import Data, to_xml
from test_xml_generation import make_contract, make_publication

XSD_PATH = Path(opencost.__file__).parent / "opencost.xsd"


@pytest.fixture(scope="module")
def schema() -> etree.XMLSchema:
    assert XSD_PATH.is_file(), "opencost.xsd must ship inside the package"
    return etree.XMLSchema(etree.parse(str(XSD_PATH)))


def assert_valid(schema: etree.XMLSchema, data: Data) -> None:
    document = etree.fromstring(to_xml(data).encode())
    schema.assertValid(document)


def test__publication_document__validates_against_xsd(schema: etree.XMLSchema) -> None:
    assert_valid(schema, Data(publication=[make_publication()]))


def test__contract_document__validates_against_xsd(schema: etree.XMLSchema) -> None:
    assert_valid(schema, Data(contract=[make_contract()]))


def test__mixed_document__validates_against_xsd(schema: etree.XMLSchema) -> None:
    assert_valid(
        schema,
        Data(publication=[make_publication()], contract=[make_contract()]),
    )


def test__publication_without_doi__validates_against_xsd(
    schema: etree.XMLSchema,
) -> None:
    from opencost import BibliographicInformation, PublicationPrimaryIdentifier

    pub = make_publication(
        primary_identifier=PublicationPrimaryIdentifier(
            bibliographic_information=BibliographicInformation(
                Title="A Paper",
                Publisher="Some Publisher",
                isPartOf="Journal of Costs",
            )
        )
    )
    assert_valid(schema, Data(publication=[pub]))


def test__publication_part_of_contract__validates_against_xsd(
    schema: etree.XMLSchema,
) -> None:
    from opencost import (
        ContractPrimaryIdentifier,
        PartOfContractType,
        PublicationCostDataType,
    )

    pub = make_publication(
        cost_data=PublicationCostDataType(
            part_of_contract=PartOfContractType(
                primary_identifier=ContractPrimaryIdentifier(type="ESAC", value="deal_de_1234")
            )
        )
    )
    assert_valid(schema, Data(publication=[pub]))


def test__contract_without_invoices_in_group__validates_against_xsd(
    schema: etree.XMLSchema,
) -> None:
    from opencost import (
        ContractCostDataType,
        ContractInvoiceGroupType,
        ContractInvoicePeriodType,
    )

    contract = make_contract()
    contract.cost_data = ContractCostDataType(
        invoice_group=[
            ContractInvoiceGroupType(
                group_id="g-1",
                invoices_period=ContractInvoicePeriodType(**{"from": "2024", "to": "2024-12"}),
            )
        ]
    )
    assert_valid(schema, Data(contract=[contract]))


def test__negative_amount_denotes_reimbursement__validates_against_xsd(
    schema: etree.XMLSchema,
) -> None:
    from opencost import (
        Dates,
        PublicationAmountPaidType,
        PublicationAmountsPaid,
        PublicationCostDataType,
        PublicationInvoiceType,
    )

    pub = make_publication(
        cost_data=PublicationCostDataType(
            invoice=[
                PublicationInvoiceType(
                    dates=Dates(paid="2026-01-01"),
                    amounts_paid=PublicationAmountsPaid(
                        amount_paid=[
                            PublicationAmountPaidType(
                                amount=Decimal("-100.00"),
                                currency="EUR",
                                cost_type="other",
                            )
                        ]
                    ),
                )
            ]
        )
    )
    assert_valid(schema, Data(publication=[pub]))

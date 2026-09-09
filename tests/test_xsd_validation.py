"""Validate serialized XML against the authoritative openCost XSD (vendor/opencost submodule)."""

from decimal import Decimal

import pytest
from lxml import etree

from opencost import (
    BibliographicInformation,
    ContractCostDataType,
    ContractInvoiceGroupType,
    ContractInvoicePeriodType,
    ContractPrimaryIdentifier,
    Data,
    Dates,
    PartOfContractType,
    PublicationAmountPaidType,
    PublicationAmountsPaid,
    PublicationCostDataType,
    PublicationInvoiceType,
    PublicationPrimaryIdentifier,
    to_xml,
)
from test_xml_generation import make_contract, make_publication


@pytest.fixture(scope="module")
def schema(schema_path) -> etree.XMLSchema:
    return etree.XMLSchema(etree.parse(str(schema_path)))


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
    contract = make_contract()
    contract.cost_data = ContractCostDataType(
        invoice_group=[
            ContractInvoiceGroupType(
                group_id="g-1",
                invoices_period=ContractInvoicePeriodType(from_="2024", to="2024-12"),
            )
        ]
    )
    assert_valid(schema, Data(contract=[contract]))


def test__negative_amount_denotes_reimbursement__validates_against_xsd(
    schema: etree.XMLSchema,
) -> None:
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


def test__official_example_documents__validate_against_pinned_schema(
    schema: etree.XMLSchema, example_docs: list
) -> None:
    """The upstream examples must validate against the pinned schema commit.

    Guards that the submodule pin still matches the documents our models
    are designed to serialize.
    """
    assert example_docs, "no example documents found in submodule"
    invalid = []
    for path in example_docs:
        try:
            schema.assertValid(etree.parse(str(path)))
        except etree.XMLSyntaxError:
            invalid.append(path.name)
    assert not invalid, f"examples invalid against pinned schema: {invalid}"

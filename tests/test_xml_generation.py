"""XML serialization tests for the openCost domain models (no framework deps)."""

from decimal import Decimal
from xml.etree import ElementTree as ET

import pytest

from opencost import (
    NAMESPACE,
    AmountInvoice,
    BibliographicInformation,
    CoarPublicationType,
    ContractAmountPaidType,
    ContractAmountsPaid,
    ContractCostDataType,
    ContractInvoiceGroupType,
    ContractInvoicePeriodType,
    ContractInvoiceType,
    ContractPrimaryIdentifier,
    ContractSecondaryIdentifiersType,
    ContractSecondaryIdType,
    ContractType,
    Data,
    Dates,
    InstitutionId,
    InstitutionName,
    InstitutionType,
    ParticipationType,
    PartOfContractType,
    PublicationAmountPaidType,
    PublicationAmountsPaid,
    PublicationCostDataType,
    PublicationInvoiceType,
    PublicationPrimaryIdentifier,
    PublicationSecondaryIdentifiers,
    PublicationSecondaryIdType,
    PublicationType,
    to_xml,
)

NS = {"oc": NAMESPACE}


def find(root: ET.Element, path: str) -> ET.Element:
    elem = root.find(path, NS)
    assert elem is not None, f"missing element: {path}"
    return elem


def make_institution() -> InstitutionType:
    return InstitutionType(
        id=[InstitutionId(type="ror", value="010zzcb52")],
        name=[InstitutionName(type="full", value="TU Braunschweig")],
    )


def make_amounts_paid() -> PublicationAmountsPaid:
    return PublicationAmountsPaid(
        amount_paid=[
            PublicationAmountPaidType(
                amount=Decimal("1650.00"),
                currency="EUR",
                cost_type="gold-oa",
                vat=Decimal("342.00"),
            )
        ]
    )


def make_invoice(number: str = "INV-4711") -> PublicationInvoiceType:
    return PublicationInvoiceType(
        invoice_number=number,
        creditor="Publisher GmbH",
        dates=Dates(invoice="2026-05-01", paid="2026-05-20"),
        amount_invoice=AmountInvoice(amount=Decimal("1980.00"), currency="EUR"),
        amounts_paid=make_amounts_paid(),
    )


def make_publication(**overrides: object) -> PublicationType:
    kwargs: dict = {
        "primary_identifier": PublicationPrimaryIdentifier(doi="10.1234/abcd"),
        "institution": make_institution(),
        "publication_type": CoarPublicationType.journal_article,
        "cost_data": PublicationCostDataType(invoice=[make_invoice()]),
    }
    kwargs.update(overrides)
    return PublicationType(**kwargs)


def parse(data: Data) -> ET.Element:
    return ET.fromstring(to_xml(data))


def test__root_is_namespaced_data_element() -> None:
    xml = to_xml(Data(publication=[make_publication()]))
    assert xml.startswith('<data xmlns="https://opencost.de">')
    root = ET.fromstring(xml)
    assert root.tag == f"{{{NAMESPACE}}}data"


def test__publication__emits_all_elements() -> None:
    root = parse(Data(publication=[make_publication()]))

    pub = find(root, "oc:publication")
    assert find(pub, "oc:primary_identifier/oc:doi").text == "10.1234/abcd"
    assert find(pub, "oc:institution/oc:id/oc:value").text == "010zzcb52"
    assert find(pub, "oc:institution/oc:id/oc:type").text == "ror"
    assert find(pub, "oc:institution/oc:name/oc:type").text == "full"
    assert find(pub, "oc:publication_type").text == "journal article"

    invoice = find(pub, "oc:cost_data/oc:invoice")
    assert find(invoice, "oc:invoice_number").text == "INV-4711"
    assert find(invoice, "oc:creditor").text == "Publisher GmbH"
    assert find(invoice, "oc:dates/oc:invoice").text == "2026-05-01"
    assert find(invoice, "oc:dates/oc:paid").text == "2026-05-20"
    assert find(invoice, "oc:amount_invoice/oc:amount").text == "1980.00"
    assert find(invoice, "oc:amount_invoice/oc:currency").text == "EUR"

    amount_paid = find(invoice, "oc:amounts_paid/oc:amount_paid")
    assert find(amount_paid, "oc:amount").text == "1650.00"
    assert find(amount_paid, "oc:cost_type").text == "gold-oa"
    assert find(amount_paid, "oc:vat").text == "342.00"


def test__publication_without_doi__emits_bibliographic_information() -> None:
    pub = make_publication(
        primary_identifier=PublicationPrimaryIdentifier(
            bibliographic_information=BibliographicInformation(
                Title="A Paper",
                Publisher="Some Publisher",
                isPartOf="Journal of Costs",
            )
        )
    )
    root = parse(Data(publication=[pub]))

    primary = find(root, "oc:publication/oc:primary_identifier")
    assert primary.find("oc:doi", NS) is None
    bio = find(primary, "oc:bibliographic_information")
    assert find(bio, "oc:Title").text == "A Paper"
    assert find(bio, "oc:Publisher").text == "Some Publisher"
    assert find(bio, "oc:isPartOf").text == "Journal of Costs"


def test__external_costsplitting__formats_as_xsd_boolean() -> None:
    root = parse(Data(publication=[make_publication(external_costsplitting=True)]))
    assert find(root, "oc:publication/oc:external_costsplitting").text == "true"

    root = parse(Data(publication=[make_publication(external_costsplitting=False)]))
    assert find(root, "oc:publication/oc:external_costsplitting").text == "false"


def test__external_costsplitting_none__element_omitted() -> None:
    root = parse(Data(publication=[make_publication(external_costsplitting=None)]))
    assert root.find("oc:publication/oc:external_costsplitting", NS) is None


def test__optional_elements__omitted_when_none() -> None:
    pub = make_publication(
        cost_data=PublicationCostDataType(
            invoice=[
                PublicationInvoiceType(
                    dates=Dates(paid="2026"),
                    amounts_paid=make_amounts_paid(),
                )
            ]
        )
    )
    root = parse(Data(publication=[pub]))

    invoice = find(root, "oc:publication/oc:cost_data/oc:invoice")
    assert invoice.find("oc:invoice_number", NS) is None
    assert invoice.find("oc:creditor", NS) is None
    assert invoice.find("oc:amount_invoice", NS) is None
    assert invoice.find("oc:dates/oc:invoice", NS) is None
    assert find(invoice, "oc:dates/oc:paid").text == "2026"


def test__repeated_fields__become_sibling_elements() -> None:
    pub = make_publication(
        secondary_identifiers=PublicationSecondaryIdentifiers(
            id=[
                PublicationSecondaryIdType(type="pmid", value="12345"),
                PublicationSecondaryIdType(type="handle", value="abc/1"),
            ]
        ),
        cost_data=PublicationCostDataType(invoice=[make_invoice("INV-1"), make_invoice("INV-2")]),
    )
    root = parse(Data(publication=[pub]))

    ids = root.findall("oc:publication/oc:secondary_identifiers/oc:id", NS)
    assert len(ids) == 2
    assert find(ids[0], "oc:type").text == "pmid"
    assert find(ids[1], "oc:value").text == "abc/1"

    invoices = root.findall("oc:publication/oc:cost_data/oc:invoice", NS)
    assert len(invoices) == 2
    assert find(invoices[0], "oc:invoice_number").text == "INV-1"
    assert find(invoices[1], "oc:invoice_number").text == "INV-2"


def test__publication_part_of_contract__links_group_id() -> None:
    pub = make_publication(
        cost_data=PublicationCostDataType(
            part_of_contract=PartOfContractType(
                primary_identifier=ContractPrimaryIdentifier(type="ESAC", value="deal_de_1234"),
                group_id="010zzcb52-deal_de_1234-2026",
            )
        )
    )
    root = parse(Data(publication=[pub]))

    part = find(root, "oc:publication/oc:cost_data/oc:part_of_contract")
    assert find(part, "oc:primary_identifier/oc:type").text == "ESAC"
    assert find(part, "oc:primary_identifier/oc:value").text == "deal_de_1234"
    assert find(part, "oc:group_id").text == "010zzcb52-deal_de_1234-2026"


def make_contract(group_id: str = "010zzcb52-deal_de_1234-2026") -> ContractType:
    return ContractType(
        contract_name="DEAL",
        institution=make_institution(),
        # "from" is an alias; pydantic v2 validates by alias only.
        participation=ParticipationType(**{"from": "2024-01-01", "to": "2024-12-31"}),
        primary_identifier=ContractPrimaryIdentifier(type="ESAC", value="deal_de_1234"),
        secondary_identifiers=ContractSecondaryIdentifiersType(
            id=[ContractSecondaryIdType(type="local", value="L-1")]
        ),
        cost_data=ContractCostDataType(
            invoice_group=[
                ContractInvoiceGroupType(
                    group_id=group_id,
                    invoices_period=ContractInvoicePeriodType(
                        **{"from": "2024-01-01", "to": "2024-12-31"}
                    ),
                    invoice=[
                        ContractInvoiceType(
                            invoice_number="INV-C-1",
                            creditor="Wiley",
                            dates=Dates(invoice="2024-06-01"),
                            amounts_paid=ContractAmountsPaid(
                                amount_paid=[
                                    ContractAmountPaidType(
                                        amount=Decimal("100000.00"),
                                        currency="EUR",
                                        cost_type="publish and read",
                                    )
                                ]
                            ),
                        )
                    ],
                )
            ]
        ),
    )


def test__contract__emits_all_elements_with_from_alias() -> None:
    root = parse(Data(contract=[make_contract()]))

    contract = find(root, "oc:contract")
    assert find(contract, "oc:contract_name").text == "DEAL"
    assert find(contract, "oc:primary_identifier/oc:type").text == "ESAC"
    assert find(contract, "oc:secondary_identifiers/oc:id/oc:type").text == "local"

    # from_ field must serialize under its "from" alias.
    assert find(contract, "oc:participation/oc:from").text == "2024-01-01"
    assert find(contract, "oc:participation/oc:to").text == "2024-12-31"

    group = find(contract, "oc:cost_data/oc:invoice_group")
    assert find(group, "oc:group_id").text == "010zzcb52-deal_de_1234-2026"
    assert find(group, "oc:invoices_period/oc:from").text == "2024-01-01"

    invoice = find(group, "oc:invoice")
    assert find(invoice, "oc:creditor").text == "Wiley"
    amount_paid = find(invoice, "oc:amounts_paid/oc:amount_paid")
    assert find(amount_paid, "oc:amount").text == "100000.00"
    assert find(amount_paid, "oc:cost_type").text == "publish and read"
    # vat is optional and None -> absent
    assert amount_paid.find("oc:vat", NS) is None


def test__data__mixes_publications_and_contracts() -> None:
    contract = make_contract()
    group_id_elem = parse(Data(contract=[contract])).find(
        "oc:contract/oc:cost_data/oc:invoice_group/oc:group_id", NS
    )
    assert group_id_elem is not None
    group_id = group_id_elem.text

    linked_publication = make_publication(
        cost_data=PublicationCostDataType(
            part_of_contract=PartOfContractType(
                primary_identifier=ContractPrimaryIdentifier(type="ESAC", value="deal_de_1234"),
                group_id=group_id,
            )
        )
    )
    root = parse(Data(publication=[linked_publication], contract=[contract]))

    assert len(root.findall("oc:publication", NS)) == 1
    assert len(root.findall("oc:contract", NS)) == 1
    pub_group = find(root, "oc:publication/oc:cost_data/oc:part_of_contract/oc:group_id").text
    contract_group = find(root, "oc:contract/oc:cost_data/oc:invoice_group/oc:group_id").text
    assert pub_group == contract_group


def test__decimal_amounts__formatted_with_two_places() -> None:
    invoice = make_invoice()
    assert invoice.amount_invoice is not None
    invoice.amount_invoice.amount = Decimal("1500")
    pub = make_publication(cost_data=PublicationCostDataType(invoice=[invoice]))
    root = parse(Data(publication=[pub]))
    assert (
        find(root, "oc:publication/oc:cost_data/oc:invoice/oc:amount_invoice/oc:amount").text
        == "1500.00"
    )


@pytest.mark.parametrize(
    ("data", "expected_child"),
    [
        (Data(publication=[make_publication()]), "publication"),
        (Data(contract=[make_contract()]), "contract"),
    ],
)
def test__to_xml__output_is_indented(data: Data, expected_child: str) -> None:
    xml = to_xml(data)
    assert "\n  <" in xml
    assert f"<{expected_child}>" in xml

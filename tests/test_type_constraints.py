from decimal import Decimal

import pytest

from opencost import (
    AmountInvoice,
    ContractAmountsPaid,
    ContractCostDataType,
    ContractSecondaryIdentifiersType,
    Data,
    Dates,
    EitherFieldMixin,
    InstitutionType,
    PublicationCostDataType,
    PublicationPrimaryIdentifier,
    PublicationSecondaryIdentifiers,
)


def test__publication_secondary_identifier__needs_at_least_one_id() -> None:
    with pytest.raises(ValueError):
        _ = PublicationSecondaryIdentifiers(id=[])


def test__publication_primary_identifier__needs_doi_or_bibliographic_information() -> None:
    with pytest.raises(ValueError):
        _ = PublicationPrimaryIdentifier(doi=None, bibliographic_information=None)


def test__publication_cost_data_type__needs_either_invoice_or_contract() -> None:
    with pytest.raises(ValueError):
        _ = PublicationCostDataType(invoice=None, part_of_contract=None)

    with pytest.raises(ValueError):
        _ = PublicationCostDataType(invoice=[], part_of_contract=None)


def test__contract_secondary_identifier__needs_at_least_one_id() -> None:
    with pytest.raises(ValueError):
        _ = ContractSecondaryIdentifiersType(id=[])


def test__dates_requires_invoice_or_paid() -> None:
    with pytest.raises(ValueError):
        _ = Dates(invoice=None, paid=None)


def test__contract_amount_paid__requires_at_least_one_item() -> None:
    with pytest.raises(ValueError):
        _ = ContractAmountsPaid(amount_paid=[])


def test__contract_cost_data__requires_at_least_one_invoice_group() -> None:
    with pytest.raises(ValueError):
        _ = ContractCostDataType(invoice_group=[])


def test__publication_primary_identifier__rejects_doi_and_bibliographic_information() -> None:
    from opencost import BibliographicInformation

    with pytest.raises(ValueError):
        _ = PublicationPrimaryIdentifier(
            doi="10.1234/abcd",
            bibliographic_information=BibliographicInformation(
                Title="T", Publisher="P", isPartOf="J"
            ),
        )


def test__institution_requires_name_or_id() -> None:
    with pytest.raises(ValueError):
        _ = InstitutionType(name=None, id=None)

    with pytest.raises(ValueError):
        _ = InstitutionType(name=[], id=[])


def test__data_requires_publication_or_contract() -> None:
    with pytest.raises(ValueError):
        _ = Data(publication=None, contract=None)

    with pytest.raises(ValueError):
        _ = Data(publication=[], contract=None)


def test__either_field_mixin__must_not_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        _ = EitherFieldMixin()


def test__currency__must_be_three_uppercase_letters() -> None:
    with pytest.raises(ValueError):
        _ = AmountInvoice(amount=Decimal("1.00"), currency="eur")

    with pytest.raises(ValueError):
        _ = AmountInvoice(amount=Decimal("1.00"), currency="EURO")


def test__dates__accept_only_xs_date_formats() -> None:
    # The XSD constrains the *shape* (YYYY, YYYY-MM, YYYY-MM-DD), not calendar
    # correctness — "2026-13-99" is shape-valid and stays accepted.
    for bad in ("2026/05/01", "20261", "26-05"):
        with pytest.raises(ValueError):
            _ = Dates(invoice=bad)

    _ = Dates(invoice="2026-13-99")


def test__unknown_fields__are_rejected() -> None:
    # extra="forbid": misspelled/unknown kwargs fail loudly, never silently dropped.
    with pytest.raises(ValueError):
        _ = AmountInvoice(amount=Decimal("1.00"), currency="EUR", amout=Decimal("999"))  # type: ignore[call-arg]


def test__aliased_fields__construct_by_python_name_or_alias() -> None:
    from opencost import ParticipationType

    by_name = ParticipationType(from_="2024-01-01", to="2024-12-31")  # type: ignore[call-arg]
    by_alias = ParticipationType(**{"from": "2024-01-01", "to": "2024-12-31"})
    assert by_name == by_alias


def test__enum_fields__accept_wire_values() -> None:
    # CoarPublicationType / cost types accept their XSD strings directly.
    identifier = PublicationSecondaryIdentifiers(id=[{"type": "pmid", "value": "123"}])  # type: ignore[list-item]
    assert identifier.id[0].type.value == "pmid"


def test__contract_secondary_id__accepts_new_wire_values() -> None:
    from opencost import ContractSecondaryIdType

    for wire in ("ESAC", "opencostid"):
        assert ContractSecondaryIdType(type=wire, value="x").type.value == wire  # type: ignore[arg-type]

from decimal import Decimal

import pytest

from opencost import (
    AmountInvoice,
    ContractAmountsPaid,
    ContractCostDataType,
    ContractInvoicePeriodType,
    ContractSecondaryIdentifiersType,
    Data,
    Dates,
    EitherFieldMixin,
    InstitutionType,
    ParticipationType,
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


def test__dates__reject_impossible_calendar_dates() -> None:
    # Shape is the pattern's job; DateFormat additionally demands a real day.
    # The XSD cannot express that: 2020-06-31 is schema-valid upstream and
    # shipped in the upstream examples (opencost-de/opencost#109).
    for bad_shape in ("2026/05/01", "20261", "26-05"):
        with pytest.raises(ValueError):
            _ = Dates(invoice=bad_shape)

    for impossible in (
        "2026-13-99",
        "2020-06-31",
        "2026-02-29",  # 2026 is not a leap year
        "2026-13",
        "2026-00",
        "0000-01-01",
    ):
        with pytest.raises(ValueError):
            _ = Dates(invoice=impossible)

    # Every documented precision stays usable, leap day included.
    _ = Dates(invoice="2026", paid="2024-02-29")


def test__participation__rejects_impossible_and_inverted_dates() -> None:
    with pytest.raises(ValueError):
        _ = ParticipationType(from_="2020-01-01", to="2020-06-31")  # type: ignore[call-arg]

    with pytest.raises(ValueError):
        _ = ParticipationType(from_="2026-12-31", to="2026-01-01")  # type: ignore[call-arg]

    joined = ParticipationType(from_="2019-07-01", to="2021-12-31")  # type: ignore[call-arg]
    assert (joined.from_, joined.to) == ("2019-07-01", "2021-12-31")


def test__invoice_period__compares_partial_dates_as_intervals() -> None:
    # YYYY, YYYY-MM and YYYY-MM-DD may be mixed: a value covers its whole year
    # or month, so only a pair that cannot overlap at all counts as inverted.
    for pair in (("2024", "2024-12"), ("2026-02", "2026"), ("2026", "2026-01-01")):
        period = ContractInvoicePeriodType(from_=pair[0], to=pair[1])  # type: ignore[call-arg]
        assert (period.from_, period.to) == pair

    with pytest.raises(ValueError):
        _ = ContractInvoicePeriodType(from_="2027-01", to="2026-12")  # type: ignore[call-arg]


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


def test__coar_publication_type__accepts_purls_both_schemes() -> None:
    from opencost import CoarPublicationType

    assert CoarPublicationType("journal article") is CoarPublicationType.journal_article
    assert CoarPublicationType("https://purl.org/coar/resource_type/c_6501") is (
        CoarPublicationType.journal_article_purl
    )
    assert CoarPublicationType("http://purl.org/coar/resource_type/c_6501") is (
        CoarPublicationType.journal_article_purl_http
    )

    with pytest.raises(ValueError):
        CoarPublicationType("https://purl.org/coar/resource_type/c_deprecated")


def test__publication_purl__round_trips_scheme_verbatim() -> None:
    # XSD fidelity: http PURLs are a distinct member and must never be
    # normalized to https on the way out.
    from opencost import (
        CoarPublicationType,
        ContractPrimaryIdentifier,
        ContractPrimaryIdentifierType,
        InstitutionId,
        InstitutionIdType,
        PartOfContractType,
        PublicationType,
        from_xml,
        to_xml,
    )

    publication = PublicationType(
        primary_identifier=PublicationPrimaryIdentifier(doi="10.1234/abcd"),
        institution=InstitutionType(
            id=[InstitutionId(type=InstitutionIdType.ror, value="010zzcb52")]
        ),
        publication_type=CoarPublicationType.journal_article_purl_http,
        cost_data=PublicationCostDataType(
            part_of_contract=PartOfContractType(
                primary_identifier=ContractPrimaryIdentifier(
                    type=ContractPrimaryIdentifierType.opencostid, value="oc-x-1"
                )
            )
        ),
    )
    data = Data(publication=[publication])
    xml = to_xml(data)
    purl = "http://purl.org/coar/resource_type/c_6501"
    assert f"<publication_type>{purl}</publication_type>" in xml
    assert from_xml(xml) == data


def test__contract_secondary_id__accepts_new_wire_values() -> None:
    from opencost import ContractSecondaryIdType

    for wire in ("ESAC", "opencostid"):
        assert ContractSecondaryIdType(type=wire, value="x").type.value == wire  # type: ignore[arg-type]

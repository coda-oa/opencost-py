"""Deserialization (XML -> models) tests, incl. round-trips over upstream examples."""

import re
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from conftest import EXAMPLES_DIR
from opencost import (
    CoarPublicationType,
    Data,
    InstitutionIdType,
    InstitutionNameType,
    ParticipationType,
    PublicationCostType,
    from_xml,
    to_xml,
)
from test_xml_generation import make_contract, make_publication

MINIMAL = """<?xml version="1.0"?>
<data xmlns="https://opencost.de">
  <publication>
    <primary_identifier><doi>10.1234/abcd</doi></primary_identifier>
    <institution>
      <id><type>ror</type><value>010zzcb52</value></id>
      <name><type>full</type><value>TU Braunschweig</value></name>
    </institution>
    <publication_type>journal article</publication_type>
    <external_costsplitting>true</external_costsplitting>
    <cost_data>
      <invoice>
        <invoice_number>INV-1</invoice_number>
        <dates><paid>2026</paid></dates>
        <amounts_paid>
          <amount_paid>
            <amount>1980.00</amount>
            <currency>EUR</currency>
            <cost_type>gold-oa</cost_type>
            <vat>342.00</vat>
          </amount_paid>
        </amounts_paid>
      </invoice>
    </cost_data>
  </publication>
</data>
"""


def test__minimal_document__parses_to_typed_models() -> None:
    data = from_xml(MINIMAL)

    assert isinstance(data, Data)
    (pub,) = data.publication
    assert pub is not None
    assert pub.primary_identifier.doi == "10.1234/abcd"
    assert pub.publication_type is CoarPublicationType.journal_article
    assert pub.external_costsplitting is True

    institution = pub.institution
    assert institution.id is not None and institution.name is not None
    assert institution.id[0].type is InstitutionIdType.ror
    assert institution.name[0].type is InstitutionNameType.full

    (invoice,) = pub.cost_data.invoice or ()
    assert invoice.invoice_number == "INV-1"
    assert invoice.creditor is None  # optional element absent
    assert invoice.dates.paid == "2026"
    (amount_paid,) = invoice.amounts_paid.amount_paid
    assert amount_paid.amount == Decimal("1980.00")
    assert isinstance(amount_paid.amount, Decimal)
    assert amount_paid.cost_type is PublicationCostType.gold_oa
    assert amount_paid.vat == Decimal("342.00")


def test__namespaced_prefix_tags__parse_like_default_namespace() -> None:
    # <opencost:foo> prefixes must parse identically to the default-
    # namespace form; prefix every tag mechanically.
    inner = (
        MINIMAL.replace('<?xml version="1.0"?>\n', "")
        .replace('<data xmlns="https://opencost.de">', "")
        .replace("</data>", "")
        .strip()
    )
    inner = re.sub(r"<(/?)([a-z_]+)", r"<\1opencost:\2", inner)
    prefixed = '<opencost:data xmlns:opencost="https://opencost.de">' + inner + "</opencost:data>"
    assert from_xml(prefixed) == from_xml(MINIMAL)


def test__round_trip__models_survive_serialize_parse() -> None:
    original = Data(publication=[make_publication()], contract=[make_contract()])
    assert from_xml(to_xml(original)) == original


def test__alias_from__parses_back_to_python_name() -> None:
    contract = make_contract()
    parsed = from_xml(to_xml(Data(contract=[contract])))
    assert parsed.contract is not None
    assert parsed.contract[0].participation == ParticipationType(
        from_="2024-01-01", to="2024-12-31"
    )


def test__unknown_element__is_rejected() -> None:
    broken = MINIMAL.replace(
        "<doi>10.1234/abcd</doi>",
        "<doi>10.1234/abcd</doi><unknown>stuff</unknown>",
    )
    with pytest.raises(ValidationError, match="extra_forbidden"):
        from_xml(broken)


def test__missing_required_element__is_rejected() -> None:
    broken = MINIMAL.replace(
        "<primary_identifier><doi>10.1234/abcd</doi></primary_identifier>",
        "<primary_identifier/>",
    )
    with pytest.raises(ValidationError):
        from_xml(broken)


def test__wrong_root_element__is_rejected() -> None:
    with pytest.raises(ValueError, match="expected root element 'data'"):
        from_xml("<contracts/>")


CONTRACT_DOC = to_xml(Data(contract=[make_contract()]))


def test__python_field_name_as_element__is_rejected_not_merged() -> None:
    # <from_> is not a wire element; it must not overwrite <from> nor
    # parse alone (populate_by_name must not leak into the XML surface).
    both = CONTRACT_DOC.replace(
        "<from>2024-01-01</from>",
        "<from>2024-01-01</from><from_>2099-09-09</from_>",
    )
    with pytest.raises(ValidationError, match="extra_forbidden"):
        from_xml(both)

    alone = CONTRACT_DOC.replace("<from>2024-01-01</from>", "<from_>2099-09-09</from_>")
    with pytest.raises(ValidationError, match="extra_forbidden"):
        from_xml(alone)


def test__markup_inside_scalar_element__is_rejected() -> None:
    # Nested children inside a leaf must raise, not degrade to whitespace.
    nested = MINIMAL.replace(
        "<doi>10.1234/abcd</doi>",
        "<doi>\n  <value>10.1234/abcd</value>\n</doi>",
    )
    with pytest.raises(ValueError, match="must contain text"):
        from_xml(nested)

    tail = MINIMAL.replace(
        "<invoice_number>INV-1</invoice_number>",
        "<invoice_number>INV-1<b>x</b>2</invoice_number>",
    )
    with pytest.raises(ValueError, match="must contain text"):
        from_xml(tail)


def test__foreign_namespace__is_rejected() -> None:
    foreign_elem = MINIMAL.replace(
        '<data xmlns="https://opencost.de">',
        '<data xmlns="https://opencost.de" xmlns:datacite="http://datacite.org/schema/kernel-4">',
    ).replace("<doi>10.1234/abcd</doi>", "<datacite:doi>10.1/x</datacite:doi>")
    with pytest.raises(ValidationError, match="extra_forbidden"):
        from_xml(foreign_elem)

    foreign_root = MINIMAL.replace("https://opencost.de", "https://evil.example.org/other")
    with pytest.raises(ValueError, match="expected root element 'data'"):
        from_xml(foreign_root)


@pytest.mark.parametrize("path", sorted(EXAMPLES_DIR.glob("*.xml")), ids=lambda p: p.name)
def test__upstream_examples__parse_and_round_trip(path: Path) -> None:
    data = from_xml(path.read_text())
    canonical = to_xml(data)
    assert from_xml(canonical) == data

"""Smoke test for the built artifact, run in an isolated environment.

Deliberately NOT a pytest module: it runs against a freshly installed
wheel (or sdist) with nothing but the package and the stdlib available,
proving the published artifact is importable and its core contract
holds. Executed by the release workflow:

    uv run --isolated --no-project --with dist/*.whl tests/smoke_test.py
    uv run --isolated --no-project --with dist/*.tar.gz tests/smoke_test.py
"""

import importlib.metadata
import sys
from decimal import Decimal

import opencost
from opencost import (
    AmountInvoice,
    CoarPublicationType,
    Data,
    Dates,
    InstitutionId,
    InstitutionIdType,
    InstitutionType,
    PublicationAmountPaidType,
    PublicationAmountsPaid,
    PublicationCostDataType,
    PublicationCostType,
    PublicationInvoiceType,
    PublicationPrimaryIdentifier,
    PublicationType,
)


def build_data() -> Data:
    return Data(
        publication=[
            PublicationType(
                primary_identifier=PublicationPrimaryIdentifier(doi="10.1234/abcd"),
                institution=InstitutionType(
                    id=[InstitutionId(type=InstitutionIdType.ror, value="010zzcb52")]
                ),
                publication_type=CoarPublicationType.journal_article,
                external_costsplitting=True,
                cost_data=PublicationCostDataType(
                    invoice=[
                        PublicationInvoiceType(
                            invoice_number="INV-1",
                            dates=Dates(invoice="2026-05-01", paid="2026-05-20"),
                            amount_invoice=AmountInvoice(amount=Decimal("1980.00"), currency="EUR"),
                            amounts_paid=PublicationAmountsPaid(
                                amount_paid=[
                                    PublicationAmountPaidType(
                                        amount=Decimal("1650.00"),
                                        currency="EUR",
                                        cost_type=PublicationCostType.gold_oa,
                                        vat=Decimal("342.00"),
                                    )
                                ]
                            ),
                        )
                    ]
                ),
            )
        ]
    )


def main() -> None:
    version = importlib.metadata.version("opencost")
    assert version, "missing distribution metadata"

    # public surface resolves
    for name in opencost.__all__:
        assert getattr(opencost, name) is not None, name

    # core contract: serialize -> parse is lossless
    data = build_data()
    xml = opencost.to_xml(data)
    assert xml.startswith(f'<data xmlns="{opencost.NAMESPACE}">'), xml[:80]
    assert "<external_costsplitting>true</external_costsplitting>" in xml
    assert opencost.from_xml(xml) == data

    # shipped strictness: unknown fields and unknown elements are rejected
    try:
        AmountInvoice(amount=Decimal("1"), currency="EUR", amout=Decimal("9"))
    except ValueError:
        pass
    else:
        raise AssertionError("extra field was not rejected")

    try:
        opencost.from_xml(xml.replace("<doi>10.1234/abcd</doi>", "<doi>x</doi><oops>y</oops>"))
    except ValueError:
        pass
    else:
        raise AssertionError("unknown element was not rejected")

    print(f"smoke ok: opencost {version} on python {sys.version.split()[0]}")


if __name__ == "__main__":
    main()

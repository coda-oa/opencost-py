# Field descriptions and notes are taken from the openCost documentation
# (doc/README.md of https://github.com/opencost-de/opencost), GPL-3.0-or-later,
# vendored as submodule vendor/opencost
from decimal import Decimal
from typing import Annotated

from pydantic import Field

from ._types import ContractCostType, Currency, DateFormat, NonEmptyString, PublicationCostType
from ._validators import EitherFieldMixin, OpenCostModel


class PublicationAmountPaidType(OpenCostModel):
    """A single amount paid by the institution (§7.2.5.1).

    Usually corresponding to an item on the invoice.
    """

    currency: Currency = Field(description="ISO 4217 currency code of the `amount_paid`.")
    amount: Decimal = Field(
        description="Amount of the `amount_paid`. Net monetary value. "
        "Negative or zero values are valid to denote reimbursements or "
        "Diamond OA models."
    )
    cost_type: PublicationCostType = Field(
        description="Describes the object/purpose of the payment. If the VAT "
        "cannot be subdivided specifically for the individual cost types, but "
        "only for the total amount of the invoice, a separate entry with the "
        "`cost_type` `vat` is possible here instead of the `vat` field "
        "(7.2.5.1.4)."
    )
    vat: Decimal | None = Field(
        default=None,
        description="Vat of the `amount_paid`. State in the same currency as "
        "`amount`. Must be specified and assigned according to the individual "
        "cost type; if a differentiated specification is not possible, use a "
        "separate entry with `cost_type` `vat` (7.2.5.1.3).",
    )


class PublicationAmountsPaid(OpenCostModel):
    """Contains all itemized amounts paid corresponding to one invoice (§7.2.5)."""

    amount_paid: Annotated[
        list[PublicationAmountPaidType],
        Field(min_length=1, description="The itemized amounts paid."),
    ]


class AmountInvoice(OpenCostModel):
    """Contains the total price as stated on the invoice (§7.2.4, §7.1.3.4)."""

    currency: Currency = Field(
        description="ISO 4217 currency code of the total amount as stated on the invoice."
    )
    amount: Decimal = Field(
        description="Total amount as stated on the invoice. Net monetary value."
    )


class Dates(EitherFieldMixin):
    """Contains different payment-related dates (§7.2.3).

    At least one of `invoice` or `paid` must be given.
    """

    either_fields = ("invoice", "paid")

    invoice: DateFormat | None = Field(
        default=None,
        description="Invoice date. Either this element or the date `paid` is required.",
    )
    paid: DateFormat | None = Field(
        default=None,
        description="Date of payment. Either this element or the invoice date is required.",
    )


class PublicationInvoiceType(OpenCostModel):
    """Encapsulates payment information, meant to correspond to a real-world
    invoice (§7.2)."""

    amount_invoice: AmountInvoice | None = Field(
        default=None,
        description="The total price as stated on the invoice.",
    )
    invoice_number: NonEmptyString | None = Field(
        default=None,
        description="Optional invoice number. As mentioned on the invoice.",
    )
    amounts_paid: PublicationAmountsPaid = Field(
        description="All itemized amounts paid corresponding to this invoice."
    )
    dates: Dates = Field(description="Payment-related dates of this invoice.")
    creditor: NonEmptyString | None = Field(
        default=None,
        description="Payment receiver as mentioned on the invoice. Might not "
        "be the actual publisher, but also e.g. a service provider from "
        "another publisher.",
    )


class ContractAmountPaidType(OpenCostModel):
    """An amount paid by the institution (§7.1.3.5.1).

    Usually corresponding to an item on the invoice.
    """

    currency: Currency = Field(description="ISO 4217 currency code of the `amount_paid`.")
    amount: Decimal = Field(
        description="Amount of the `amount_paid`. Net monetary value. "
        "Negative or zero values are valid to denote reimbursements."
    )
    cost_type: ContractCostType = Field(
        description="Describes the object/purpose of the payment. If the VAT "
        "cannot be subdivided specifically for the individual cost types, but "
        "only for the total amount of the invoice, a separate entry with the "
        "`cost_type` `vat` is possible here instead of the `vat` field "
        "(7.1.3.5.1.4)."
    )
    vat: Decimal | None = Field(
        default=None,
        description="Vat of the `amount_paid`. State in the same currency as "
        "`amount`. Must be specified and assigned according to the individual "
        "cost type; if a differentiated specification is not possible, use a "
        "separate entry with `cost_type` `vat` (7.1.3.5.1.3).",
    )


class ContractAmountsPaid(OpenCostModel):
    """Contains all itemized amounts paid corresponding to one invoice of a
    contract (§7.1.3.5)."""

    amount_paid: Annotated[
        list[ContractAmountPaidType],
        Field(min_length=1, description="The itemized amounts paid."),
    ]


class ContractInvoiceType(OpenCostModel):
    """Encapsulates payment information for a contract, meant to correspond to
    a real-world invoice (§7.1.3)."""

    amount_invoice: AmountInvoice | None = Field(
        default=None,
        description="The total price as stated on the invoice for the contract.",
    )
    invoice_number: NonEmptyString | None = Field(
        default=None,
        description="Optional invoice number. As mentioned on the invoice.",
    )
    creditor: NonEmptyString | None = Field(
        default=None,
        description="Payment receiver as mentioned on the invoice. Might not "
        "be the actual publisher, but also e.g. a service provider.",
    )
    dates: Dates = Field(description="Payment-related dates of this invoice.")
    amounts_paid: ContractAmountsPaid = Field(
        description="All itemized amounts paid corresponding to this invoice."
    )


class ContractInvoicePeriodType(OpenCostModel):
    """Identifies the time frame an invoice refers to (§7.1.2)."""

    from_: DateFormat = Field(
        ...,
        alias="from",
        description="Start date of the time frame the invoice refers to. Can "
        "be different to an institution's contract accession "
        "(`participation // from`) if multiple invoices have been issued over "
        "the total contract duration.",
    )
    to: DateFormat = Field(
        description="End date of the time frame the invoice refers to. Can be "
        "different to an institution's contract termination "
        "(`participation // to`) if multiple invoices have been issued over "
        "the total contract duration."
    )


class ContractInvoiceGroupType(OpenCostModel):
    """Contains all invoices that belong to a billing period within a contract
    (§7.1).

    Such a contract phase is limited by a time period (`invoices_period`) to
    which a respective invoice can be assigned.
    """

    group_id: NonEmptyString = Field(
        description="An id to uniquely name and identify the `invoice_group`. "
        "Necessary to link not only from an individual publication to the "
        "global contract but also to a specific invoice and contract period: "
        "relates cost data for an `opencost:publication` to this contract via "
        "the `opencost:part_of_contract` element. Generating a `uuid` or "
        "using another type of unique identifier is recommended."
    )
    invoices_period: ContractInvoicePeriodType = Field(
        description="Identifies the time frame the invoices in this group refer to."
    )
    invoice: list[ContractInvoiceType] | None = Field(
        default=None,
        description="The invoices belonging to this billing period.",
    )


class ContractCostDataType(OpenCostModel):
    """Aggregates payments related to a contract (§7, contract).

    The `invoice` elements can be combined into one or more common
    `invoice_group` elements referring to a shared `invoices_period` of the
    contract concerned.
    """

    invoice_group: Annotated[
        list[ContractInvoiceGroupType],
        Field(min_length=1, description="The billing periods of the contract."),
    ]

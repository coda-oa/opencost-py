from decimal import Decimal
from typing import Annotated

from pydantic import Field

from ._types import ContractCostType, Currency, DateFormat, NonEmptyString, PublicationCostType
from ._validators import EitherFieldMixin, OpenCostModel


class PublicationAmountPaidType(OpenCostModel):
    currency: Currency
    amount: Decimal
    cost_type: PublicationCostType
    vat: Decimal | None = None


class PublicationAmountsPaid(OpenCostModel):
    amount_paid: Annotated[list[PublicationAmountPaidType], Field(min_length=1)]


class AmountInvoice(OpenCostModel):
    currency: Currency
    amount: Decimal


class Dates(EitherFieldMixin):
    either_fields = ("invoice", "paid")

    invoice: DateFormat | None = None
    paid: DateFormat | None = None


class PublicationInvoiceType(OpenCostModel):
    amount_invoice: AmountInvoice | None = None
    invoice_number: NonEmptyString | None = None
    amounts_paid: PublicationAmountsPaid
    dates: Dates
    creditor: NonEmptyString | None = None


class ContractAmountPaidType(OpenCostModel):
    currency: Currency
    amount: Decimal
    cost_type: ContractCostType
    vat: Decimal | None = None


class ContractAmountsPaid(OpenCostModel):
    amount_paid: Annotated[list[ContractAmountPaidType], Field(min_length=1)]


class ContractInvoiceType(OpenCostModel):
    amount_invoice: AmountInvoice | None = None
    invoice_number: NonEmptyString | None = None
    creditor: NonEmptyString | None = None
    dates: Dates
    amounts_paid: ContractAmountsPaid


class ContractInvoicePeriodType(OpenCostModel):
    from_: DateFormat = Field(..., alias="from")
    to: DateFormat


class ContractInvoiceGroupType(OpenCostModel):
    group_id: NonEmptyString
    invoices_period: ContractInvoicePeriodType
    invoice: list[ContractInvoiceType] | None = None


class ContractCostDataType(OpenCostModel):
    invoice_group: Annotated[list[ContractInvoiceGroupType], Field(min_length=1)]

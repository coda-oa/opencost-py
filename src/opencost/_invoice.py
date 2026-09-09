from decimal import Decimal

from pydantic import BaseModel, Field, conlist

from ._types import ContractCostType, Currency, DateFormat, NonEmptyString, PublicationCostType
from ._validators import EitherFieldMixin


class PublicationAmountPaidType(BaseModel):
    currency: Currency
    amount: Decimal
    cost_type: PublicationCostType
    vat: Decimal | None = None


class PublicationAmountsPaid(BaseModel):
    amount_paid: conlist(PublicationAmountPaidType, min_length=1)


class AmountInvoice(BaseModel):
    currency: Currency
    amount: Decimal


class Dates(EitherFieldMixin):
    either_fields = ("invoice", "paid")

    invoice: DateFormat | None = None
    paid: DateFormat | None = None


class PublicationInvoiceType(BaseModel):
    amount_invoice: AmountInvoice | None = None
    invoice_number: NonEmptyString | None = None
    amounts_paid: PublicationAmountsPaid
    dates: Dates
    creditor: NonEmptyString | None = None


class ContractAmountPaidType(BaseModel):
    currency: Currency
    amount: Decimal
    cost_type: ContractCostType
    vat: Decimal | None = None


class ContractAmountsPaid(BaseModel):
    amount_paid: conlist(ContractAmountPaidType, min_length=1)


class ContractInvoiceType(BaseModel):
    amount_invoice: AmountInvoice | None = None
    invoice_number: NonEmptyString | None = None
    creditor: NonEmptyString | None = None
    dates: Dates
    amounts_paid: ContractAmountsPaid


class ContractInvoicePeriodType(BaseModel):
    from_: DateFormat = Field(..., alias="from")
    to: DateFormat


class ContractInvoiceGroupType(BaseModel):
    group_id: NonEmptyString
    invoices_period: ContractInvoicePeriodType
    invoice: list[ContractInvoiceType] | None = None


class ContractCostDataType(BaseModel):
    invoice_group: conlist(ContractInvoiceGroupType, min_length=1)

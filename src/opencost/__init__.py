"""Pydantic models for the openCost metadata schema, with XML (de)serialization.

openCost (https://github.com/opencost-de/opencost) is a metadata schema for
the financial side of scholarly publishing: article-level cost data
(``publication``) and contracts / transformative agreements (``contract``).

>>> from opencost import Data, PublicationType, from_xml, to_xml
>>> xml = to_xml(Data(publication=[...]))          # models -> openCost XML
>>> data = from_xml('<data xmlns="https://opencost.de">…</data>')  # XML -> models
"""

from ._types import NonEmptyString as NonEmptyString
from ._types import Currency as Currency
from ._types import DateFormat as DateFormat
from ._types import ContractCostType as ContractCostType
from ._types import PublicationCostType as PublicationCostType
from ._common import Data as Data
from ._contract import ContractType as ContractType
from ._contract import ContractPrimaryIdentifier as ContractPrimaryIdentifier
from ._contract import ContractPrimaryIdentifierType as ContractPrimaryIdentifierType
from ._contract import ContractSecondaryIdType as ContractSecondaryIdType
from ._contract import ContractSecondaryIdTypeEnum as ContractSecondaryIdTypeEnum
from ._contract import ContractSecondaryIdentifiersType as ContractSecondaryIdentifiersType
from ._contract import ParticipationType as ParticipationType
from ._invoice import PublicationInvoiceType as PublicationInvoiceType
from ._invoice import PublicationAmountPaidType as PublicationAmountPaidType
from ._invoice import PublicationAmountsPaid as PublicationAmountsPaid
from ._invoice import AmountInvoice as AmountInvoice
from ._invoice import Dates as Dates
from ._invoice import ContractCostDataType as ContractCostDataType
from ._invoice import ContractAmountPaidType as ContractAmountPaidType
from ._invoice import ContractAmountsPaid as ContractAmountsPaid
from ._invoice import ContractInvoiceType as ContractInvoiceType
from ._invoice import ContractInvoicePeriodType as ContractInvoicePeriodType
from ._invoice import ContractInvoiceGroupType as ContractInvoiceGroupType
from ._institution import InstitutionType as InstitutionType
from ._institution import InstitutionId as InstitutionId
from ._institution import InstitutionIdType as InstitutionIdType
from ._institution import InstitutionName as InstitutionName
from ._institution import InstitutionNameType as InstitutionNameType
from ._publication import PublicationType as PublicationType
from ._publication import PublicationPrimaryIdentifier as PublicationPrimaryIdentifier
from ._publication import PublicationSecondaryIdType as PublicationSecondaryIdType
from ._publication import PublicationSecondaryIdTypeEnum as PublicationSecondaryIdTypeEnum
from ._publication import PublicationSecondaryIdentifiers as PublicationSecondaryIdentifiers
from ._publication import BibliographicInformation as BibliographicInformation
from ._coar import CoarPublicationType as CoarPublicationType
from ._publication import PublicationCostDataType as PublicationCostDataType
from ._publication import PartOfContractType as PartOfContractType
from ._validators import EitherFieldMixin as EitherFieldMixin
from ._validators import OpenCostModel as OpenCostModel
from .xml import NAMESPACE as NAMESPACE
from .xml import from_xml as from_xml
from .xml import to_xml as to_xml

__all__ = [
    "NonEmptyString",
    "Currency",
    "DateFormat",
    "ContractCostType",
    "PublicationCostType",
    "Data",
    "ContractType",
    "ContractPrimaryIdentifier",
    "ContractPrimaryIdentifierType",
    "ContractSecondaryIdType",
    "ContractSecondaryIdTypeEnum",
    "ContractSecondaryIdentifiersType",
    "ParticipationType",
    "PublicationInvoiceType",
    "PublicationAmountPaidType",
    "PublicationAmountsPaid",
    "AmountInvoice",
    "Dates",
    "ContractCostDataType",
    "ContractAmountPaidType",
    "ContractAmountsPaid",
    "ContractInvoiceType",
    "ContractInvoicePeriodType",
    "ContractInvoiceGroupType",
    "InstitutionType",
    "InstitutionId",
    "InstitutionIdType",
    "InstitutionName",
    "InstitutionNameType",
    "PublicationType",
    "PublicationPrimaryIdentifier",
    "PublicationSecondaryIdType",
    "PublicationSecondaryIdTypeEnum",
    "PublicationSecondaryIdentifiers",
    "BibliographicInformation",
    "CoarPublicationType",
    "PartOfContractType",
    "PublicationCostDataType",
    "EitherFieldMixin",
    "OpenCostModel",
    "NAMESPACE",
    "from_xml",
    "to_xml",
]

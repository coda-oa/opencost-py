from enum import Enum

from pydantic import Field

from ._institution import InstitutionType
from ._invoice import ContractCostDataType
from ._types import DateFormat, NonEmptyString
from ._validators import OpenCostModel, RequiredList


class ContractPrimaryIdentifierType(Enum):
    ESAC = "ESAC"


class ContractPrimaryIdentifier(OpenCostModel):
    value: NonEmptyString
    type: ContractPrimaryIdentifierType


class ContractSecondaryIdTypeEnum(Enum):
    oai = "oai"
    ezb = "ezb"
    local = "local"


class ContractSecondaryIdType(OpenCostModel):
    value: NonEmptyString
    type: ContractSecondaryIdTypeEnum


class ContractSecondaryIdentifiersType(OpenCostModel):
    id: RequiredList[ContractSecondaryIdType]


class ParticipationType(OpenCostModel):
    to: DateFormat
    from_: DateFormat = Field(..., alias="from")


class ContractType(OpenCostModel):
    contract_name: NonEmptyString
    institution: InstitutionType
    participation: ParticipationType
    primary_identifier: ContractPrimaryIdentifier
    secondary_identifiers: ContractSecondaryIdentifiersType | None = None
    cost_data: ContractCostDataType

# Field descriptions and notes are taken from the openCost documentation
# (doc/README.md of https://github.com/opencost-de/opencost), GPL-3.0-or-later,
# vendored as submodule vendor/opencost
from enum import Enum
from typing import Annotated

from pydantic import Field

from ._institution import InstitutionType
from ._invoice import ContractCostDataType
from ._types import DateFormat, NonEmptyString
from ._validators import OpenCostModel


class ContractPrimaryIdentifierType(Enum):
    """Contract primary identifier scheme (§5.1).

    `ESAC` or `opencostid` is accepted.
    """

    ESAC = "ESAC"
    opencostid = "opencostid"


class ContractPrimaryIdentifier(OpenCostModel):
    """Persistent, global identifier for the contract (§5).

    Currently an `ESAC` ID
    (https://esac-initiative.org/about/transformative-agreements/agreement-registry/)
    or an `opencostid` (a self-issued id for the contract).
    """

    value: NonEmptyString = Field(description="Identifier value of the contract.")
    type: ContractPrimaryIdentifierType = Field(
        description="Identifier scheme; `ESAC` or `opencostid`."
    )


class ContractSecondaryIdTypeEnum(Enum):
    """Contract secondary identifier scheme (§6.1.1)."""

    oai = "oai"
    ezb = "ezb"
    local = "local"
    ESAC = "ESAC"
    opencostid = "opencostid"


class ContractSecondaryIdType(OpenCostModel):
    """Secondary identifier for the contract (§6.1)."""

    value: NonEmptyString = Field(description="Identifier value.")
    type: ContractSecondaryIdTypeEnum = Field(description="Identifier scheme of `value`.")


class ContractSecondaryIdentifiersType(OpenCostModel):
    """Contains additional, optional identifiers for the contract (§6)."""

    id: Annotated[
        list[ContractSecondaryIdType],
        Field(min_length=1, description="Additional (persistent) identifiers."),
    ]


class ParticipationType(OpenCostModel):
    """Contains information on the dates an institution joined and left a
    contract (§4)."""

    to: DateFormat = Field(
        description="The date when the institution left the contract. Not to "
        "be confused with the end date of the agreement itself, which may be "
        "later."
    )
    from_: DateFormat = Field(
        ...,
        alias="from",
        description="The date when the institution joined the contract. Not "
        "to be confused with the start date of the agreement itself, which "
        "may be earlier.",
    )


class ContractType(OpenCostModel):
    """Top-level element, corresponds to a contract for which costs are to be
    recorded (§1).

    Examples of such contracts are transformative agreements and memberships.
    """

    contract_name: NonEmptyString = Field(description="A human-readable label for the contract.")
    institution: InstitutionType = Field(
        description="Contains information to identify the institution taking part in the contract."
    )
    participation: ParticipationType = Field(
        description="The dates the institution joined and left the contract."
    )
    primary_identifier: ContractPrimaryIdentifier = Field(
        description="Persistent, global identifier for the contract; "
        "currently `ESAC` or `opencostid` is accepted."
    )
    secondary_identifiers: ContractSecondaryIdentifiersType | None = Field(
        default=None,
        description="Additional, optional identifiers for the contract.",
    )
    cost_data: ContractCostDataType = Field(
        description="Aggregates payments related to this contract."
    )

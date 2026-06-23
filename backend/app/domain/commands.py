from decimal import Decimal
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator


class OpenAccountCommand(BaseModel):
    owner_name:      str     = Field(..., min_length=1, max_length=120)
    initial_balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency:        str     = Field(default="USD", pattern=r"^[A-Z]{3}$")
    correlation_id:  UUID    = Field(default_factory=uuid4)


class DepositMoneyCommand(BaseModel):
    account_id:     UUID
    amount:         Decimal = Field(..., gt=0)
    description:    str     = Field(default="", max_length=255)
    correlation_id: UUID    = Field(default_factory=uuid4)

    @field_validator("amount")
    @classmethod
    def round_to_cents(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))


class WithdrawMoneyCommand(BaseModel):
    account_id:     UUID
    amount:         Decimal = Field(..., gt=0)
    description:    str     = Field(default="", max_length=255)
    correlation_id: UUID    = Field(default_factory=uuid4)

    @field_validator("amount")
    @classmethod
    def round_to_cents(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))


class CloseAccountCommand(BaseModel):
    account_id:     UUID
    reason:         str  = Field(default="", max_length=255)
    correlation_id: UUID = Field(default_factory=uuid4)
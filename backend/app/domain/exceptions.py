class LedgerError(Exception):
    """Base for all domain errors."""


class AccountNotFoundError(LedgerError):
    def __init__(self, account_id: str):
        super().__init__(f"Account not found: {account_id}")


class InsufficientFundsError(LedgerError):
    pass


class InvalidAmountError(LedgerError):
    pass


class AccountAlreadyClosedError(LedgerError):
    def __init__(self, account_id: str):
        super().__init__(f"Account is closed: {account_id}")


class ConcurrencyConflictError(LedgerError):
    """Raised when optimistic concurrency check fails (version mismatch)."""
    def __init__(self, stream_id: str, expected: int):
        super().__init__(
            f"Concurrency conflict on stream {stream_id}: "
            f"expected version {expected} already taken."
        )
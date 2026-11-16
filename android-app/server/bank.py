"""The bank provider boundary. SandboxBank is the only implementation in this repository; a licensed
payment provider (SEPA Direct Debit under PSD2, or open-banking payment initiation) implements the
same three calls. The server never keeps the IBAN: it passes it to the provider once and stores the
token that comes back."""
from __future__ import annotations

import secrets
from typing import Protocol

from atlas_go import payments as pay


class BankProvider(Protocol):
    def tokenise(self, iban: str, holder: str, purpose: str) -> dict:
        """Register an account with the provider -> dict(token, mandate_id or None)."""

    def debit(self, token: str, last4: str, amount: int, reference: str) -> str:
        """Collect amount (cents) under the mandate -> 'approved' or a decline code."""

    def credit(self, token: str, last4: str, amount: int, reference: str) -> str:
        """Pay amount (cents) out to the account -> 'approved' or a decline code."""


class SandboxBank:
    """Deterministic test bank: decides by the last four characters, exactly as the phone does
    (payments.sandbox_outcome). It keeps no state and moves no money."""

    def tokenise(self, iban: str, holder: str, purpose: str) -> dict:
        return dict(token='sbx_' + secrets.token_urlsafe(18),
                    mandate_id='M-' + secrets.token_hex(6).upper() if purpose == 'debit' else None)

    def debit(self, token: str, last4: str, amount: int, reference: str) -> str:
        return pay.sandbox_outcome(last4, amount)

    def credit(self, token: str, last4: str, amount: int, reference: str) -> str:
        return 'account_closed' if pay.sandbox_outcome(last4, 0) == 'account_closed' else 'approved'

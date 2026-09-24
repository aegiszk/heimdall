"""Immutable domain models for already-observed EVM wallet swaps."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Literal, Mapping


SCHEMA_VERSION = 1
Side = Literal["buy", "sell"]


def _require_hex(value: str, *, field: str, bytes_length: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    normalized = value.lower()
    expected_length = 2 + (bytes_length * 2)
    if not normalized.startswith("0x") or len(normalized) != expected_length:
        raise ValueError(f"{field} must be a 0x-prefixed {bytes_length}-byte hex value")
    try:
        int(normalized[2:], 16)
    except ValueError as exc:
        raise ValueError(f"{field} contains non-hex characters") from exc
    return normalized


def _positive_decimal(value: Decimal | str | int, *, field: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a decimal number") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise ValueError(f"{field} must be finite and greater than zero")
    return parsed


def _decimal_text(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


@dataclass(frozen=True, slots=True)
class EvmLogIdentity:
    chain_id: int
    transaction_hash: str
    log_index: int

    def __post_init__(self) -> None:
        if isinstance(self.chain_id, bool) or not isinstance(self.chain_id, int) or self.chain_id <= 0:
            raise ValueError("chain_id must be a positive integer")
        if isinstance(self.log_index, bool) or not isinstance(self.log_index, int) or self.log_index < 0:
            raise ValueError("log_index must be a non-negative integer")
        object.__setattr__(
            self,
            "transaction_hash",
            _require_hex(self.transaction_hash, field="transaction_hash", bytes_length=32),
        )

    def as_key(self) -> tuple[int, str, int]:
        return self.chain_id, self.transaction_hash, self.log_index

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "log_index": self.log_index,
            "transaction_hash": self.transaction_hash,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EvmLogIdentity":
        if set(data) != {"chain_id", "log_index", "transaction_hash"}:
            raise ValueError("identity has missing or unknown fields")
        return cls(
            chain_id=data["chain_id"],
            transaction_hash=data["transaction_hash"],
            log_index=data["log_index"],
        )


@dataclass(frozen=True, slots=True)
class WalletTradeObservation:
    """One decoded swap observed from public chain data.

    Times use Unix nanoseconds. ``observed_at_ns`` is local receipt time, while
    ``block_timestamp_ns`` is chain time. Both are facts supplied by the observer.
    """

    identity: EvmLogIdentity
    block_number: int
    block_timestamp_ns: int
    observed_at_ns: int
    wallet_address: str
    token_in: str
    token_out: str
    amount_in: Decimal
    amount_out: Decimal
    source: str = "evm_public_log"

    def __post_init__(self) -> None:
        for field, value in (
            ("block_number", self.block_number),
            ("block_timestamp_ns", self.block_timestamp_ns),
            ("observed_at_ns", self.observed_at_ns),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{field} must be a non-negative integer")
        if self.observed_at_ns < self.block_timestamp_ns:
            raise ValueError("observed_at_ns cannot precede block_timestamp_ns")
        for field in ("wallet_address", "token_in", "token_out"):
            object.__setattr__(self, field, _require_hex(getattr(self, field), field=field, bytes_length=20))
        if self.token_in == self.token_out:
            raise ValueError("token_in and token_out must differ")
        object.__setattr__(self, "amount_in", _positive_decimal(self.amount_in, field="amount_in"))
        object.__setattr__(self, "amount_out", _positive_decimal(self.amount_out, field="amount_out"))
        if self.source != "evm_public_log":
            raise ValueError("source must be 'evm_public_log'")

    def to_dict(self) -> dict[str, Any]:
        return {
            "amount_in": _decimal_text(self.amount_in),
            "amount_out": _decimal_text(self.amount_out),
            "block_number": self.block_number,
            "block_timestamp_ns": self.block_timestamp_ns,
            "identity": self.identity.to_dict(),
            "observed_at_ns": self.observed_at_ns,
            "schema_version": SCHEMA_VERSION,
            "source": self.source,
            "token_in": self.token_in,
            "token_out": self.token_out,
            "wallet_address": self.wallet_address,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "WalletTradeObservation":
        expected = {
            "amount_in",
            "amount_out",
            "block_number",
            "block_timestamp_ns",
            "identity",
            "observed_at_ns",
            "schema_version",
            "source",
            "token_in",
            "token_out",
            "wallet_address",
        }
        if set(data) != expected:
            raise ValueError("observation has missing or unknown fields")
        if data["schema_version"] != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version {data['schema_version']!r}")
        identity = data["identity"]
        if not isinstance(identity, Mapping):
            raise ValueError("identity must be an object")
        return cls(
            identity=EvmLogIdentity.from_dict(identity),
            block_number=data["block_number"],
            block_timestamp_ns=data["block_timestamp_ns"],
            observed_at_ns=data["observed_at_ns"],
            wallet_address=data["wallet_address"],
            token_in=data["token_in"],
            token_out=data["token_out"],
            amount_in=data["amount_in"],
            amount_out=data["amount_out"],
            source=data["source"],
        )

    def copy_signal(self, *, quote_token: str) -> "CopySignal":
        quote = _require_hex(quote_token, field="quote_token", bytes_length=20)
        quote_is_in = self.token_in == quote
        quote_is_out = self.token_out == quote
        if quote_is_in == quote_is_out:
            raise ValueError("ambiguous swap: quote_token must match exactly one swap token")
        if quote_is_in:
            side: Side = "buy"
            target_token = self.token_out
            target_amount = self.amount_out
            quote_amount = self.amount_in
        else:
            side = "sell"
            target_token = self.token_in
            target_amount = self.amount_in
            quote_amount = self.amount_out
        return CopySignal(
            identity=self.identity,
            observed_at_ns=self.observed_at_ns,
            side=side,
            target_token=target_token,
            quote_token=quote,
            target_amount=target_amount,
            reference_price=quote_amount / target_amount,
        )


@dataclass(frozen=True, slots=True)
class CopySignal:
    identity: EvmLogIdentity
    observed_at_ns: int
    side: Side
    target_token: str
    quote_token: str
    target_amount: Decimal
    reference_price: Decimal

    def __post_init__(self) -> None:
        if self.side not in ("buy", "sell"):
            raise ValueError("side must be 'buy' or 'sell'")
        if isinstance(self.observed_at_ns, bool) or not isinstance(self.observed_at_ns, int) or self.observed_at_ns < 0:
            raise ValueError("observed_at_ns must be a non-negative integer")
        for field in ("target_token", "quote_token"):
            object.__setattr__(self, field, _require_hex(getattr(self, field), field=field, bytes_length=20))
        if self.target_token == self.quote_token:
            raise ValueError("target_token and quote_token must differ")
        object.__setattr__(self, "target_amount", _positive_decimal(self.target_amount, field="target_amount"))
        object.__setattr__(self, "reference_price", _positive_decimal(self.reference_price, field="reference_price"))


@dataclass(frozen=True, slots=True)
class HypotheticalCopy:
    identity: EvmLogIdentity
    copied_at_ns: int
    copy_price: Decimal

    def __post_init__(self) -> None:
        if isinstance(self.copied_at_ns, bool) or not isinstance(self.copied_at_ns, int) or self.copied_at_ns < 0:
            raise ValueError("copied_at_ns must be a non-negative integer")
        object.__setattr__(self, "copy_price", _positive_decimal(self.copy_price, field="copy_price"))

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from meta.wallet_copy import (
    EvmLogIdentity,
    HypotheticalCopy,
    ObservationRecorder,
    WalletTradeObservation,
    evaluate_copy,
    load_observations,
)
from meta.wallet_copy.recorder import canonical_json


WALLET = "0x" + "11" * 20
QUOTE = "0x" + "22" * 20
TARGET = "0x" + "33" * 20
OTHER = "0x" + "44" * 20


def _observation(*, suffix=1, observed_at_ns=2_000_000_000, token_in=QUOTE, token_out=TARGET):
    return WalletTradeObservation(
        identity=EvmLogIdentity(2020, "0x" + f"{suffix:064x}", 7),
        block_number=100,
        block_timestamp_ns=1_000_000_000,
        observed_at_ns=observed_at_ns,
        wallet_address=WALLET,
        token_in=token_in,
        token_out=token_out,
        amount_in=Decimal("100"),
        amount_out=Decimal("20"),
    )


def test_canonical_jsonl_round_trip_and_immutable_models(tmp_path):
    path = tmp_path / "observations.jsonl"
    observation = _observation()
    recorder = ObservationRecorder(path)
    recorder.append(observation)

    assert load_observations(path) == (observation,)
    assert path.read_text(encoding="ascii") == canonical_json(observation) + "\n"
    assert path.read_text(encoding="ascii").startswith('{"amount_in":"100"')
    with pytest.raises(FrozenInstanceError):
        observation.block_number = 101


def test_recorder_requires_monotonic_timestamps_and_unique_log_identity(tmp_path):
    path = tmp_path / "observations.jsonl"
    recorder = ObservationRecorder(path)
    recorder.append(_observation())

    with pytest.raises(ValueError, match="duplicate transaction/log identity"):
        recorder.append(_observation(observed_at_ns=3_000_000_000))
    with pytest.raises(ValueError, match="monotonic"):
        recorder.append(_observation(suffix=2, observed_at_ns=1_999_999_999))

    assert load_observations(path) == (_observation(),)


def test_loader_rejects_duplicate_identity_in_existing_file(tmp_path):
    path = tmp_path / "observations.jsonl"
    line = canonical_json(_observation()) + "\n"
    path.write_text(line + line, encoding="ascii")

    with pytest.raises(ValueError, match="duplicates transaction/log identity"):
        load_observations(path)


def test_signal_rejects_ambiguous_quote_token():
    observation = _observation(token_in=TARGET, token_out=OTHER)

    with pytest.raises(ValueError, match="ambiguous swap"):
        observation.copy_signal(quote_token=QUOTE)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"transaction_hash": "0x1"}, "transaction_hash"),
        ({"amount_in": Decimal("NaN")}, "amount_in"),
        ({"token_out": QUOTE}, "must differ"),
        ({"observed_at_ns": 999_999_999}, "cannot precede"),
    ],
)
def test_malformed_observations_are_rejected(change, message):
    with pytest.raises(ValueError, match=message):
        values = {
            "identity": EvmLogIdentity(2020, "0x" + "01" * 32, 7),
            "block_number": 100,
            "block_timestamp_ns": 1_000_000_000,
            "observed_at_ns": 2_000_000_000,
            "wallet_address": WALLET,
            "token_in": QUOTE,
            "token_out": TARGET,
            "amount_in": Decimal("100"),
            "amount_out": Decimal("20"),
        }
        if "transaction_hash" in change:
            values["identity"] = EvmLogIdentity(2020, change["transaction_hash"], 7)
        else:
            values.update(change)
        WalletTradeObservation(**values)


def test_replay_measures_latency_and_buy_price_drift():
    signal = _observation().copy_signal(quote_token=QUOTE)
    copy = HypotheticalCopy(signal.identity, 2_125_000_000, Decimal("5.05"))

    metric = evaluate_copy(signal, copy)

    assert signal.side == "buy"
    assert signal.reference_price == Decimal("5")
    assert metric.latency_ms == Decimal("125")
    assert metric.price_drift_bps == Decimal("100")
    assert metric.adverse_drift_bps == Decimal("100")


def test_replay_sell_drift_and_pre_observation_copy_rejection():
    signal = _observation(token_in=TARGET, token_out=QUOTE).copy_signal(quote_token=QUOTE)
    favorable_copy = HypotheticalCopy(signal.identity, 2_001_000_000, Decimal("0.19"))

    metric = evaluate_copy(signal, favorable_copy)

    assert signal.side == "sell"
    assert signal.reference_price == Decimal("0.2")
    assert metric.price_drift_bps == Decimal("-500.00")
    assert metric.adverse_drift_bps == Decimal("500.00")
    with pytest.raises(ValueError, match="cannot precede observation"):
        evaluate_copy(signal, HypotheticalCopy(signal.identity, 1_999_999_999, Decimal("0.2")))

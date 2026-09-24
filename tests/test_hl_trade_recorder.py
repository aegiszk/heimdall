"""Offline tests for the read-only HL trade recorder and the latency probe clock math."""

import datetime as dt
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rec = _load("hl_trade_recorder")
probe = _load("feed_latency_probe")

GOOD = {
    "coin": "xyz:SP500", "side": "A", "px": "7761.2", "sz": "1.191", "time": 1790108614226,
    "hash": "0x4aae", "tid": 397308368082810,
    "users": ["0xE8FD6379F60487A463A38395F598B3008AD8489C", "0x6064f2eb787873a532da5b2b3f7a13429f99ba68"],
}


def test_parse_keeps_exact_strings_and_lowercases_wallets():
    r = rec.parse_trade(GOOD, recv_ns=1790108614500000000, snapshot=False)
    assert r["px"] == "7761.2" and r["sz"] == "1.191"
    assert r["buyer"] == "0xe8fd6379f60487a463a38395f598b3008ad8489c"
    assert r["seller"] == "0x6064f2eb787873a532da5b2b3f7a13429f99ba68"
    assert r["ex_ms"] == 1790108614226 and r["snap"] is False


@pytest.mark.parametrize("patch", [
    {"users": ["0xabc"]},
    {"users": ["0x" + "1" * 40, "not-an-address"]},
    {"px": "-1"}, {"sz": "0"}, {"px": "1e5"},
    {"side": "X"}, {"time": "1790108614226"}, {"tid": None},
])
def test_parse_rejects_malformed(patch):
    with pytest.raises(ValueError):
        rec.parse_trade({**GOOD, **patch}, recv_ns=1, snapshot=False)


def test_writer_is_append_only_hourly_and_drops_duplicates(tmp_path):
    ns = int(dt.datetime(2026, 9, 23, 14, 59, 59, tzinfo=dt.timezone.utc).timestamp() * 1e9)
    w = rec.AppendOnlyHourlyWriter(tmp_path)
    a = rec.parse_trade(GOOD, ns, False)
    assert w.write(a) is True
    assert w.write(a) is False  # same (coin, tid) from a reconnect snapshot
    b = rec.parse_trade({**GOOD, "tid": 1}, ns + 2 * 10**9, False)  # next UTC hour
    assert w.write(b) is True
    w.close()
    f14 = tmp_path / "trades" / "2026-09-23" / "14.jsonl"
    f15 = tmp_path / "trades" / "2026-09-23" / "15.jsonl"
    assert [json.loads(x)["tid"] for x in f14.read_text().splitlines()] == [GOOD["tid"]]
    assert [json.loads(x)["tid"] for x in f15.read_text().splitlines()] == [1]
    assert w.written == 2 and w.dropped_duplicates == 1
    # a second writer appends; prior bytes are untouched
    before = f15.read_bytes()
    w2 = rec.AppendOnlyHourlyWriter(tmp_path)
    w2.write(rec.parse_trade({**GOOD, "tid": 2}, ns + 3 * 10**9, False))
    w2.close()
    assert f15.read_bytes().startswith(before)


def test_recorder_has_no_order_path():
    src = (ROOT / "tools" / "hl_trade_recorder.py").read_text()
    for forbidden in ("/exchange", "eth_account", "sign_", "private_key", "secret", '"action"', "place_order"):
        assert forbidden not in src


def test_sntp_offset_math():
    # server clock 15 s behind local; symmetric 40 ms path, 0 server processing
    t0 = 1_000_000_000_000
    t1 = t0 + 20_000_000 - 15_000_000_000
    t2 = t1
    t3 = t0 + 40_000_000
    off, rtt = probe.sntp_offset(t0, t1, t2, t3)
    assert off == pytest.approx(-15000.0)
    assert rtt == pytest.approx(40.0)

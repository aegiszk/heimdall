import os, sys, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.alpha.base import Signal, QuantModel
from core.alpha.carry import FundingCarryModel
from core.execution.paper_broker import PaperBroker
from tools.check_core_purity import violations

class FakeData:
    def __init__(self, f): self._f = f
    def funding_bps(self, a, ts): return self._f

def test_signal_range():
    Signal("m","BTC","t",0.5)
    with pytest.raises(ValueError): Signal("m","BTC","t",1.5)

def test_carry_enters_short_on_high_funding():
    m = FundingCarryModel(enter_bps=3.0, exit_bps=-1.0)
    s = m.predict("BTC","t", FakeData(5.0))
    assert s.conviction == -1.0 and s.metadata["leg"] == "short_perp_long_spot"

def test_carry_abstains_midband():
    m = FundingCarryModel(3.0, -1.0)
    assert m.predict("BTC","t", FakeData(0.5)).conviction == 0.0

def test_i7_blocks_real_order_when_flag_off():
    b = PaperBroker()
    b.send("okx","spot","buy",1,100, is_paper=True)          # ok
    with pytest.raises(PermissionError):
        b.send("okx","spot","buy",1,100, is_paper=False)     # blocked (I7)

def test_core_purity_clean():
    assert violations() == []

def test_core_purity_detects_violation(tmp_path):
    # synthetic: prove the firewall actually catches a /meta import
    import pathlib
    d = tmp_path/"core"; d.mkdir()
    (d/"bad.py").write_text("from meta.regime import detect_regime\n")
    cwd = os.getcwd(); os.chdir(tmp_path)
    try:
        assert len(violations("core")) == 1
    finally:
        os.chdir(cwd)

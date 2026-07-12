"""Bars-contract tests, ported with gambit_data from homily validate [21]-[23].

The contract these pin (G-S1 gate): raw 6-tuple bars + aligned adj closes,
host rotation with backoff retry, epoch params for rng=max, REFUSAL of any
non-daily response (the validate-[22] Yahoo monthly-bars bug class), and the
R7 session-date discipline (bar dates from timestamps in America/New_York,
never local time).
"""
import datetime
import json
import urllib.error

import pytest

import gambit_data

# 2023-11-14 14:30 UTC / 09:30 America/New_York — a real session-open stamp
TS0 = 1699972200
TS1 = TS0 + 86400


def _payload(**over):
    d = {"chart": {"result": [{
        "timestamp": [TS0, TS1],
        "indicators": {"quote": [{"open": [10, 11], "high": [10.5, 11.5],
                                  "low": [9.5, 10.5], "close": [10, 11],
                                  "volume": [100, 110]}]}}]}}
    res = d["chart"]["result"][0]
    res.update(over)
    return json.dumps(d).encode()


class _Resp:
    def __init__(self, data): self._d = data
    def read(self): return self._d
    def __enter__(self): return self
    def __exit__(self, *a): return False


class Opener:
    """Injectable opener: fails `fail` times, then serves `payload`."""

    def __init__(self, fail=0, payload=None):
        self.fail, self.calls, self.urls = fail, 0, []
        self.payload = _payload() if payload is None else payload

    def __call__(self, req, timeout=None, context=None):
        self.urls.append(req.full_url)
        self.calls += 1
        if self.calls <= self.fail:
            raise urllib.error.URLError("flaky")
        return _Resp(self.payload)


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(gambit_data, "BACKOFF", 0.0)
    monkeypatch.setattr(gambit_data, "JITTER", 0.0)


def test_bars_contract_and_retry_rotation():
    op = Opener(fail=2)
    bars = gambit_data.fetch_daily("TEST", rng="1mo", opener=op)
    assert len(bars) == 2 and len(bars[0]) == 6, "bars must be 6-tuples"
    assert bars[0][4] == 10 and bars[1][4] == 11, "raw closes untouched"
    assert op.calls == 3, "must retry through two failures"
    assert "query1" in op.urls[0] and "query2" in op.urls[1], "no host rotation"


def test_exhausted_retries_raise():
    with pytest.raises(urllib.error.URLError):
        gambit_data.fetch_daily("TEST", opener=Opener(fail=99))


def test_max_range_uses_epoch_params():
    # range=max silently degrades to 1mo bars; epoch params keep true dailies
    op = Opener()
    gambit_data.fetch_daily("TEST", rng="max", opener=op)
    assert "period1=0" in op.urls[0] and "range=max" not in op.urls[0]


def test_non_daily_bars_refused():
    # THE G-S1 GATE FIXTURE: a deliberately-broken (monthly) response must
    # fail the contract, loudly. Coarse bars never feed a signal.
    coarse = _payload(meta={"dataGranularity": "1mo"})
    with pytest.raises(ValueError, match="not 1d"):
        gambit_data.fetch_daily("TEST", rng="max", opener=Opener(payload=coarse))


def test_daily_granularity_accepted():
    bars = gambit_data.fetch_daily(
        "TEST", opener=Opener(payload=_payload(meta={"dataGranularity": "1d"})))
    assert len(bars) == 2


def test_adjclose_parallel_series_and_fallback():
    adj_payload = _payload(indicators={
        "quote": [{"open": [10, 11], "high": [10.5, 11.5],
                   "low": [9.5, 10.5], "close": [10, 11],
                   "volume": [100, 110]}],
        "adjclose": [{"adjclose": [9.8, 11]}]})
    bars, adj = gambit_data.fetch_series("TEST", opener=Opener(payload=adj_payload))
    assert [b[4] for b in bars] == [10, 11], "raw closes must survive untouched"
    assert adj == [9.8, 11] and len(adj) == len(bars)
    # no adjclose block -> fall back to raw closes
    bars2, adj2 = gambit_data.fetch_series("TEST", opener=Opener())
    assert adj2 == [b[4] for b in bars2]


def test_half_formed_rows_skipped():
    broken = _payload(indicators={"quote": [{
        "open": [10, None, 12], "high": [10.5, 11.5, 12.5],
        "low": [9.5, 10.5, 11.5], "close": [10, 11, 12],
        "volume": [100, 110, 0]}]},
        timestamp=[TS0, TS1, TS1 + 86400])
    bars = gambit_data.fetch_daily("TEST", opener=Opener(payload=broken))
    assert len(bars) == 1 and bars[0][4] == 10, \
        "None fields and zero-volume rows must be dropped"


def test_session_date_pinned_to_us_market_tz():
    # R7 pin: the same timestamps must yield the same session date on any
    # machine. TS0 is 22:30 SGT / 09:30 ET on 2023-11-14 — a naive local
    # fromtimestamp() east of UTC gives the right answer by luck here, so
    # also pin a 19:00 ET stamp (next day in SGT) where naive-local breaks.
    assert gambit_data.session_date(TS0) == datetime.date(2023, 11, 14)
    evening_et = TS0 + 9 * 3600 + 30 * 60          # 2023-11-14 19:00 ET
    assert gambit_data.session_date(evening_et) == datetime.date(2023, 11, 14)


def test_resample_weekly_monthly():
    # Mon 2023-11-13 .. Fri 2023-12-01: 3 ISO weeks, 2 months
    start = datetime.date(2023, 11, 13)
    bars, px = [], 100.0
    d = start
    while d <= datetime.date(2023, 12, 1):
        if d.weekday() < 5:
            px += 1
            bars.append((d, px, px, px, px, 1000))
        d += datetime.timedelta(days=1)
    wk = gambit_data.weekly_closes(bars)
    mo = gambit_data.monthly_closes(bars)
    assert len(wk) == 3 and wk[-1] == bars[-1][4]
    assert len(mo) == 2 and mo[-1] == bars[-1][4]

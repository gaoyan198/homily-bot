"""G-S2 gate tests: universe.json builds deterministically from a fixture
snapshot of the NASDAQ Trader directory; the `constructed:` stamp is present;
every directory row lands in the filter trace with its fate."""
import datetime
import json

import gambit_universe as gu

NASDAQ_TXT = """Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares
GOODA|Alpha Corp. Common Stock|Q|N|N|100|N|N
GOODB|Beta Inc. Common Stock|Q|N|N|100|N|N
SPACX|Blank Check Acquisition Corp. Class A Ordinary Shares|G|N|N|100|N|N
ETFY|Some Index ETF|G|N|N|100|Y|N
TESTZ|NASDAQ TEST STOCK|G|Y|N|100|N|N
CHEAP|Cheapo Industries Common Stock|Q|N|N|100|N|N
THINQ|Thin Trading Co. Common Stock|Q|N|N|100|N|N
BADFT|Fetchfail Corp. Common Stock|Q|N|N|100|N|N
File Creation Time: 0101202599:99|||||||
"""

OTHER_TXT = """ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol
GOODC|Gamma plc Ordinary Shares|N|GOODC|N|100|N|GOODC
GOODD|Delta Ltd. American Depositary Shares|N|GOODD|N|100|N|GOODD
WARR|Omega Corp. Warrants|N|WARR|N|100|N|WARR
PREF.A|Omega Corp. 5.25% Preferred Stock|N|PREF$A|N|100|N|PREF-A
IEXCO|Iex Listed Co. Common Stock|V|IEXCO|N|100|N|IEXCO
File Creation Time: 0101202599:99|||||||
"""

# close, volume -> flat 130-bar tapes; mdv = close*volume
TAPES = {
    "GOODA": (100.0, 2_000_000),   # $200M/day — rank 1
    "GOODB": (50.0, 2_000_000),    # $100M/day — rank 2
    "GOODC": (40.0, 1_500_000),    # $60M/day — rank 3
    "GOODD": (30.0, 1_000_000),    # $30M/day — rank 4 (capacity-cut at top_n=3)
    "CHEAP": (9.99, 90_000_000),   # fails price gate despite huge $vol
    "THINQ": (100.0, 100_000),     # $10M/day — fails mdv20 gate
}


def fake_fetch(sym):
    if sym == "BADFT":
        raise ValueError("BADFT: Yahoo returned 1mo bars, not 1d")
    close, vol = TAPES[sym]
    d0 = datetime.date(2026, 1, 5)
    return [(d0 + datetime.timedelta(days=i), close, close, close, close, vol)
            for i in range(130)]


def build(top_n=3):
    rows = gu.parse_directory(NASDAQ_TXT, OTHER_TXT)
    return gu.build_universe(rows, constructed=datetime.date(2026, 7, 10),
                             fetch=fake_fetch, top_n=top_n, workers=3)


def test_deterministic_from_fixture_snapshot():
    a, b = build(), build()
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True), \
        "same snapshot + same fetch must build byte-identical universes"


def test_constructed_stamp_present():
    u = build()
    assert u["constructed"] == "2026-07-10"


def test_ranking_and_capacity_cut():
    u = build(top_n=3)
    assert [m["symbol"] for m in u["symbols"]] == ["GOODA", "GOODB", "GOODC"]
    assert [m["rank"] for m in u["symbols"]] == [1, 2, 3]
    assert u["trace"]["GOODD"]["drop"] == "capacity-cut"
    assert u["trace"]["GOODD"]["mdv126"] == 30_000_000


def test_filter_trace_covers_every_row():
    u = build()
    expect = {
        "SPACX": "name:acquisition corp",
        "ETFY": "etf",
        "TESTZ": "test-issue",
        "WARR": "name:warrants",
        "PREF.A": "symbol-suffix",
        "IEXCO": "exchange:V",
        "CHEAP": "price",
        "THINQ": "mdv20",
        "BADFT": "fetch-error:ValueError",
    }
    for sym, reason in expect.items():
        assert u["trace"][sym]["drop"] == reason, (sym, u["trace"][sym])
    for m in u["symbols"]:
        assert u["trace"][m["symbol"]] == {
            "kept": True, "last_close": m["last_close"],
            "mdv20": m["mdv20"], "mdv126": m["mdv126"]}
    # nothing silently vanishes: every parsed row is traced
    rows = gu.parse_directory(NASDAQ_TXT, OTHER_TXT)
    assert set(u["trace"]) == {r["symbol"] for r in rows}


def test_price_and_liquidity_gates_use_registered_constants():
    u = build()
    assert u["spec"]["min_price"] == 10.0
    assert u["spec"]["min_mdv20"] == 25e6
    assert u["trace"]["CHEAP"]["last_close"] == 9.99  # gate values traced


def test_refresh_due_quarter_cycle():
    c = datetime.date(2026, 7, 10)                     # Q3 build
    assert not gu.refresh_due(c, datetime.date(2026, 8, 30))   # same quarter
    assert not gu.refresh_due(c, datetime.date(2026, 9, 30))
    assert gu.refresh_due(c, datetime.date(2026, 10, 3))       # Q4 → rebuild
    assert gu.refresh_due(c, datetime.date(2027, 1, 2))        # year rollover

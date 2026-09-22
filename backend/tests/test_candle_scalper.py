import sys
import types

import pytest


if "MetaTrader5" not in sys.modules:
    fake_mt5 = types.SimpleNamespace(
        TIMEFRAME_M1=1,
        copy_rates_from_pos=lambda *args, **kwargs: None,
    )
    sys.modules["MetaTrader5"] = fake_mt5

from backend.trading_engine.candle_scalper import candle_scalper as cs


def _bars():
    return [
        {"open": 100.0, "high": 101.0, "low": 99.5, "close": 100.2},
        {"open": 100.2, "high": 101.0, "low": 100.0, "close": 100.3},
        {"open": 100.3, "high": 101.2, "low": 100.1, "close": 100.4},
        {"open": 100.4, "high": 101.0, "low": 100.2, "close": 100.5},
        # Last closed candle: strong bullish body.
        {"open": 100.5, "high": 102.0, "low": 100.45, "close": 101.8},
        # Current/forming candle. It is intentionally ignored for entry.
        {"open": 101.8, "high": 101.9, "low": 101.7, "close": 101.81},
    ]


def test_strong_closed_candle_creates_independent_buy_burst():
    result = cs.analyze_candle_momentum("TEST", rates=_bars())

    assert result["signal"] == "BUY"
    assert result["confidence"] == 80.0
    assert result["burst_count"] == 3
    assert result["profit_target_usd"] == pytest.approx(2.50)
    assert result["timeframe"] == "M1"
    assert result["candle_move_target"] == pytest.approx(1.3)


def test_weak_closed_candle_holds_even_if_forming_candle_is_strong():
    bars = _bars()
    bars[-2] = {
        "open": 100.5,
        "high": 101.0,
        "low": 100.0,
        "close": 100.6,
    }
    bars[-1] = {
        "open": 100.6,
        "high": 103.0,
        "low": 100.55,
        "close": 102.9,
    }

    result = cs.analyze_candle_momentum("TEST", rates=bars)

    assert result["signal"] == "HOLD"


def test_position_comment_round_trips():
    comment = cs.candle_position_comment("SELL", 1.23456789)

    parsed = cs.parse_candle_position_comment(comment)

    assert parsed["strategy"] == "CANDLE_SCALPER"
    assert parsed["direction"] == "SELL"
    assert parsed["candle_move_target"] == pytest.approx(1.23456789)


def test_current_candle_movement_is_directional(monkeypatch):
    monkeypatch.setattr(
        cs.mt5,
        "copy_rates_from_pos",
        lambda *args, **kwargs: [
            {"open": 100.0, "high": 101.0, "low": 99.9, "close": 100.8}
        ],
    )

    result = cs.current_candle_movement("TEST", "BUY")

    assert result["ready"] is True
    assert result["movement"] == pytest.approx(0.8)

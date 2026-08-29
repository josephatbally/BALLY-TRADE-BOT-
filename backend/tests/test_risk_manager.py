import pytest
from backend.trading_engine.risk import risk_manager as rm


def test_risk_manager_info():
    info = rm.risk_manager_info()
    assert info['status'] == 'READY'
    assert info['decision_generation'] is False
    assert info['decision_override'] is False
    assert info['mt5_order_send'] is False
    assert info['hard_max_risk_percent'] == 2.0
    assert info['minimum_rr'] == 1.0
    assert info['maximum_rr'] == 3.0


@pytest.mark.parametrize(('signal','entry','sl','tp'), [
    ('BUY', 4700.0, 4680.0, 4760.0),
    ('SELL', 4700.0, 4720.0, 4640.0),
])
def test_rr_exact_maximum(signal, entry, sl, tp):
    r = rm.validate_risk_reward(signal, entry, sl, tp)
    assert r['valid'] is True
    assert r['risk_authorized'] is True
    assert r['rr'] == pytest.approx(3.0)


def test_rr_above_maximum_blocks():
    r = rm.validate_risk_reward('BUY', 4700, 4680, 4770)
    assert r['valid'] is False
    assert r['risk_authorized'] is False
    assert r['rr'] == pytest.approx(3.5)
    assert 'exceeds maximum' in r['reason']


def test_rr_below_minimum_blocks():
    r = rm.validate_risk_reward('BUY', 4700, 4680, 4710)
    assert r['valid'] is False
    assert r['risk_authorized'] is False
    assert r['rr'] == pytest.approx(0.5)


@pytest.mark.parametrize(('signal','entry','sl','tp'), [
    ('BUY', 4700, 4700, 4760),
    ('BUY', 4700, 4710, 4760),
    ('SELL', 4700, 4700, 4640),
    ('SELL', 4700, 4690, 4640),
])
def test_invalid_trade_geometry_blocks(signal, entry, sl, tp):
    r = rm.validate_risk_reward(signal, entry, sl, tp)
    assert r['valid'] is False
    assert r['risk_authorized'] is False


@pytest.mark.parametrize('signal', ['NO_TRADE', 'HOLD', '', None])
def test_invalid_signal_blocks_rr(signal):
    r = rm.validate_risk_reward(signal, 4700, 4680, 4760)
    assert r['valid'] is False
    assert r['risk_authorized'] is False


def test_adjusted_risk_default():
    r = rm.calculate_adjusted_risk_percent()
    assert r['valid'] is True
    assert r['adjusted_risk_percent'] == pytest.approx(1.0)


def test_adjusted_risk_hard_cap():
    r = rm.calculate_adjusted_risk_percent(base_risk_percent=10.0)
    assert r['adjusted_risk_percent'] <= 2.0
    assert r['hard_max_risk_percent'] == 2.0


def test_adjusted_risk_floor():
    r = rm.calculate_adjusted_risk_percent(base_risk_percent=0.001)
    assert r['adjusted_risk_percent'] == pytest.approx(0.1)


def test_adjusted_risk_drawdown_multiplier():
    r = rm.calculate_adjusted_risk_percent(
        base_risk_percent=1.0,
        drawdown_result={'risk_multiplier': 0.75},
    )
    assert r['adjusted_risk_percent'] == pytest.approx(0.75)


def test_adjusted_risk_zero_multiplier():
    r = rm.calculate_adjusted_risk_percent(
        base_risk_percent=1.0,
        drawdown_result={'risk_multiplier': 0.0},
    )
    assert r['adjusted_risk_percent'] == pytest.approx(0.0)


def test_low_opportunity_reduces_risk():
    r = rm.calculate_adjusted_risk_percent(
        base_risk_percent=1.0,
        opportunity_score=40.0,
    )
    assert r['opportunity_multiplier'] == pytest.approx(0.50)
    assert r['adjusted_risk_percent'] == pytest.approx(0.5)


def test_preferred_lot_is_soft_preference():
    r = rm.apply_preferred_lot_policy(0.01, 0.05)
    assert r['valid'] is True
    assert r['volume'] == pytest.approx(0.01)
    assert r['calculated_volume'] == pytest.approx(0.01)
    assert r['preferred_lot'] == pytest.approx(0.05)
    assert r['preferred_lot_applied'] is False
    assert r['preferred_lot_is_hard'] is False


def test_no_preferred_lot():
    r = rm.apply_preferred_lot_policy(0.03, None)
    assert r['valid'] is True
    assert r['volume'] == pytest.approx(0.03)


def test_zero_calculated_volume_blocks():
    r = rm.apply_preferred_lot_policy(0, 0.05)
    assert r['valid'] is False


def test_no_trade_never_enters_risk():
    r = rm.evaluate_risk('NO_TRADE', 'XAUUSD', 4700.0)
    assert r['status'] == 'BLOCKED'
    assert r['risk_authorized'] is False
    assert r['execution_allowed'] is False
    assert r['order_builder_allowed'] is False
    assert r['real_trade'] is False


@pytest.mark.parametrize('signal', ['HOLD', 'BUY_LIMIT', '', None])
def test_invalid_decision_blocks(signal):
    r = rm.evaluate_risk(signal, 'XAUUSD', 4700.0)
    assert r['status'] == 'BLOCKED'
    assert r['risk_authorized'] is False


def test_missing_symbol_blocks():
    r = rm.evaluate_risk('BUY', '', 4700.0)
    assert r['status'] == 'BLOCKED'
    assert r['risk_authorized'] is False


@pytest.mark.parametrize('entry', [None, 0, -1, 'invalid'])
def test_invalid_entry_blocks(entry):
    r = rm.evaluate_risk('BUY', 'XAUUSD', entry)
    assert r['status'] == 'BLOCKED'
    assert r['risk_authorized'] is False


def install_success_children(monkeypatch):
    monkeypatch.setattr(rm, 'evaluate_account_drawdown', lambda **kw: {
        'status': 'READY', 'valid': True, 'risk_authorized': True,
        'risk_multiplier': 1.0,
    })
    monkeypatch.setattr(rm, 'calculate_stop_loss', lambda *a, **kw: {
        'status': 'READY', 'valid': True, 'risk_authorized': True,
        'stop_loss': 4680.0,
    })
    monkeypatch.setattr(rm, 'calculate_take_profit', lambda *a, **kw: {
        'status': 'READY', 'valid': True, 'risk_authorized': True,
        'take_profit': 4760.0,
    })
    monkeypatch.setattr(rm, 'calculate_position_size', lambda *a, **kw: {
        'status': 'READY', 'valid': True, 'risk_authorized': True,
        'volume': 0.01,
    })
    monkeypatch.setattr(rm, 'check_margin', lambda *a, **kw: {
        'status': 'READY', 'valid': True, 'risk_authorized': True,
        'margin_authorized': True,
    })


def test_complete_buy_authorization(monkeypatch):
    install_success_children(monkeypatch)
    r = rm.evaluate_risk(
        'BUY', 'XAUUSD', 4700.0,
        account_balance=10000.0,
        account_equity=10000.0,
        base_risk_percent=1.0,
    )
    assert r['status'] == 'READY'
    assert r['risk_authorized'] is True
    assert r['decision'] == 'BUY'
    assert r['symbol'] == 'XAUUSD'
    plan = r['trade_plan']
    assert plan['entry'] == pytest.approx(4700.0)
    assert plan['stop_loss'] == pytest.approx(4680.0)
    assert plan['take_profit'] == pytest.approx(4760.0)
    assert plan['volume'] == pytest.approx(0.01)
    assert plan['rr'] == pytest.approx(3.0)
    assert plan['risk_percent'] <= 2.0
    assert r['execution_allowed'] is False
    assert r['order_builder_allowed'] is False
    assert r['final_gate_required'] is True
    assert r['final_gate_passed'] is False
    assert r['mt5_order_check'] is False
    assert r['mt5_order_send'] is False
    assert r['real_trade'] is False
    assert r['failed_checks'] == []


def test_complete_sell_authorization(monkeypatch):
    install_success_children(monkeypatch)
    monkeypatch.setattr(rm, 'calculate_stop_loss', lambda *a, **kw: {
        'status': 'READY', 'valid': True, 'risk_authorized': True,
        'stop_loss': 4720.0,
    })
    monkeypatch.setattr(rm, 'calculate_take_profit', lambda *a, **kw: {
        'status': 'READY', 'valid': True, 'risk_authorized': True,
        'take_profit': 4640.0,
    })
    r = rm.evaluate_risk('SELL', 'XAUUSD', 4700.0,
                         account_balance=10000.0, account_equity=10000.0)
    assert r['status'] == 'READY'
    assert r['risk_authorized'] is True
    assert r['trade_plan']['decision'] == 'SELL'
    assert r['trade_plan']['rr'] == pytest.approx(3.0)


def test_margin_failure_blocks(monkeypatch):
    install_success_children(monkeypatch)
    monkeypatch.setattr(rm, 'check_margin', lambda *a, **kw: {
        'status': 'BLOCKED', 'valid': False, 'risk_authorized': False,
        'margin_authorized': False, 'reason': 'insufficient free margin',
    })
    r = rm.evaluate_risk('BUY', 'XAUUSD', 4700.0)
    assert r['status'] == 'BLOCKED'
    assert r['risk_authorized'] is False

    assert r.get('margin_authorized') is False or r.get('risk_authorized') is False
    assert 'insufficient free margin' in r.get('reason', '')


def test_rr_above_maximum_blocks_complete_pipeline(monkeypatch):
    install_success_children(monkeypatch)
    monkeypatch.setattr(rm, 'calculate_take_profit', lambda *a, **kw: {
        'status': 'READY', 'valid': True, 'risk_authorized': True,
        'take_profit': 4770.0,
    })
    r = rm.evaluate_risk('BUY', 'XAUUSD', 4700.0)
    assert r['status'] == 'BLOCKED'
    assert r['risk_authorized'] is False
    assert r['risk_reward']['valid'] is False
    assert r['risk_reward']['rr'] == pytest.approx(3.5)


def test_manage_risk_alias(monkeypatch):
    install_success_children(monkeypatch)
    r = rm.manage_risk('BUY', 'XAUUSD', 4700.0)
    assert r['status'] == 'READY'
    assert r['risk_authorized'] is True


def test_calculate_risk_alias(monkeypatch):
    install_success_children(monkeypatch)
    r = rm.calculate_risk('BUY', 'XAUUSD', 4700.0)
    assert r['status'] == 'READY'
    assert r['risk_authorized'] is True


def test_authorize_risk_alias(monkeypatch):
    install_success_children(monkeypatch)
    r = rm.authorize_risk('BUY', 'XAUUSD', 4700.0)
    assert r['status'] == 'READY'
    assert r['risk_authorized'] is True

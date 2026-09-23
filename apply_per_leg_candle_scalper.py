#!/usr/bin/env python3
"""
Update BALLY FLOW to support per-leg profit exits ($2.50) and active replenishment:
1. Always maintain up to 3 positions per symbol for Candle Scalper.
2. Evaluate each leg individually: when any leg hits >= $2.50 profit, close only that ticket.
3. If 1 or 2 legs close, replenish the open slots based on current M1 candle momentum.
4. Active forming candle momentum (USE_CLOSED_CANDLE = False).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CANDLE_SCALPER_PATH = ROOT / "backend" / "trading_engine" / "candle_scalper" / "candle_scalper.py"
AUTO_TRADER_PATH = ROOT / "backend" / "trading_engine" / "auto_trader.py"

def update_candle_scalper():
    content = CANDLE_SCALPER_PATH.read_text(encoding="utf-8")
    
    # Update USE_CLOSED_CANDLE to False
    content = re.sub(
        r"USE_CLOSED_CANDLE\s*=\s*True",
        "USE_CLOSED_CANDLE = False",
        content
    )
    # Ensure DEFAULT_BURST_COUNT = 3
    content = re.sub(
        r"DEFAULT_BURST_COUNT\s*=\s*\d+",
        "DEFAULT_BURST_COUNT = 3",
        content
    )
    # Ensure DEFAULT_PROFIT_TARGET_USD = 2.50
    content = re.sub(
        r"DEFAULT_PROFIT_TARGET_USD\s*=\s*[\d\.]+",
        "DEFAULT_PROFIT_TARGET_USD = 2.50",
        content
    )

    CANDLE_SCALPER_PATH.write_text(content, encoding="utf-8")
    print("✓ Updated candle_scalper.py: USE_CLOSED_CANDLE=False, BURST_COUNT=3, PROFIT_TARGET=2.50")

def update_auto_trader():
    content = AUTO_TRADER_PATH.read_text(encoding="utf-8")

    # Replace _manage_candle_scalper_bursts with per-leg individual exit logic
    new_manage_logic = '''    async def _manage_candle_scalper_bursts(self, positions):
        """Manage Candle Momentum positions independently per leg.
        
        Closes individual legs when their floating profit reaches >= $2.50.
        Does not close unaffected legs in the group.
        """
        for pos in positions:
            comment = (
                pos.get("comment", "")
                if isinstance(pos, dict)
                else getattr(pos, "comment", "")
            )
            parsed = parse_candle_position_comment(comment)
            if not parsed:
                continue

            profit = float(
                pos.get("profit", 0.0)
                if isinstance(pos, dict)
                else getattr(pos, "profit", 0.0)
            )
            ticket = (
                pos.get("ticket")
                if isinstance(pos, dict)
                else getattr(pos, "ticket", None)
            )
            symbol = (
                pos.get("symbol", "")
                if isinstance(pos, dict)
                else getattr(pos, "symbol", "")
            )
            direction = parsed.get("direction", "")

            # Strict individual leg exit: each leg must hit >= $2.50
            if profit >= DEFAULT_PROFIT_TARGET_USD and ticket is not None:
                self._add_log(
                    "SUCCESS",
                    f"[CANDLE SCALPER] Leg profit hit: {symbol} (#{ticket}) {direction} "
                    f"+${profit:.2f} >= ${DEFAULT_PROFIT_TARGET_USD:.2f} -> Closing leg",
                )
                close_position(ticket)'''

    content = re.sub(
        r'    async def _manage_candle_scalper_bursts\(self, positions\):.*?(?=\n    async def _manage_positions|\n    def |\Z)',
        new_manage_logic + '\n',
        content,
        flags=re.DOTALL
    )

    # In _evaluate_and_execute_symbol, handle replenishment for Candle Scalper without open_symbols block
    old_guard = '        if symbol in open_symbols:\n            return False'
    new_guard = '''        active_strategy = getattr(self, "active_strategy", "SMC").upper()
        if active_strategy != "CANDLE_SCALPER" and symbol in open_symbols:
            return False'''

    if old_guard in content:
        content = content.replace(old_guard, new_guard, 1)

    # Ensure Candle Scalper calculates available slots up to DEFAULT_BURST_COUNT (3)
    old_eval_head = '''        # --- 1. CANDLE MOMENTUM SCALPER BRANCH ---
        # Independent from SMC, Hybrid and AI.
        active_strategy = getattr(self, "active_strategy", "SMC").upper()
        if active_strategy == "CANDLE_SCALPER":'''

    new_eval_head = '''        # --- 1. CANDLE MOMENTUM SCALPER BRANCH ---
        # Independent from SMC, Hybrid and AI.
        if active_strategy == "CANDLE_SCALPER":
            all_positions = get_positions() or []
            active_cs_legs = [
                p for p in all_positions
                if (p.get("symbol") if isinstance(p, dict) else getattr(p, "symbol", "")) == symbol
                and parse_candle_position_comment(
                    p.get("comment", "") if isinstance(p, dict) else getattr(p, "comment", "")
                )
            ]
            current_cs_count = len(active_cs_legs)
            slots_needed = max(0, DEFAULT_BURST_COUNT - current_cs_count)

            if slots_needed <= 0:
                return False'''

    if old_eval_head in content:
        content = content.replace(old_eval_head, new_eval_head, 1)

    # Adjust burst_count used for order loop to slots_needed
    old_burst_count = '''                burst_count = max(1, int(scalp_res.get("burst_count", 3)))'''
    new_burst_count = '''                burst_count = slots_needed'''

    if old_burst_count in content:
        content = content.replace(old_burst_count, new_burst_count, 1)

    AUTO_TRADER_PATH.write_text(content, encoding="utf-8")
    print("✓ Updated auto_trader.py: Per-leg exit evaluation + dynamic 3-leg replenishment")

if __name__ == "__main__":
    update_candle_scalper()
    update_auto_trader()
    print("✓ Done applying updates.")

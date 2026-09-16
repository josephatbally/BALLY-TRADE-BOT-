"""
Makes AutoTrader.start()/stop() awaitable for the FastAPI lifespan,
while toggle/set_enabled keep returning plain booleans for JSON.
"""

path = "backend/trading_engine/auto_trader.py"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Insert the _AwaitableResult helper if missing
if "_AwaitableResult" not in code:
    helper = '''class _AwaitableResult:
    """Supports both sync usage and 'await' syntax seamlessly."""
    def __init__(self, value=True):
        self.value = value
    def __bool__(self):
        return bool(self.value)
    def __await__(self):
        async def _coro():
            return self.value
        return _coro().__await__()


'''
    code = code.replace("class AutoTrader:", helper + "class AutoTrader:")

# 2. start() returns an awaitable result
start_old = '''                self._add_log("SUCCESS", "Auto-trading daemon background worker started")
            except RuntimeError:
                pass
        return True'''
start_new = '''                self._add_log("SUCCESS", "Auto-trading daemon background worker started")
            except RuntimeError:
                pass
        return _AwaitableResult(True)'''
if start_old in code:
    code = code.replace(start_old, start_new)
    print("[OK] start() now returns an awaitable result")

# 3. stop() returns an awaitable result
stop_old = '''        self._add_log("WARNING", "Auto-trading daemon stopped")
        return False'''
stop_new = '''        self._add_log("WARNING", "Auto-trading daemon stopped")
        return _AwaitableResult(False)'''
if stop_old in code:
    code = code.replace(stop_old, stop_new)
    print("[OK] stop() now returns an awaitable result")

# 4. Keep toggle/set_enabled returning plain booleans for JSON serialization
old_toggle = "            return self.start()\n        else:\n            return self.stop()"
new_toggle = "            return bool(self.start())\n        else:\n            return bool(self.stop())"
if old_toggle in code:
    code = code.replace(old_toggle, new_toggle)
    print("[OK] toggle/set_enabled return plain booleans")

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print("[DONE] AutoTrader is lifespan-safe.")

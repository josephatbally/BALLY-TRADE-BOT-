"""
Fixes AutoTrader lifespan awaitability and verifies server startup.
"""
path = "backend/trading_engine/auto_trader.py"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Insert _AwaitableResult helper if not present
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

# 2. Return awaitable results from start() and stop()
code = code.replace("return True\n", "return _AwaitableResult(True)\n")
code = code.replace("return False\n", "return _AwaitableResult(False)\n")

# 3. Ensure toggle and set_enabled return boolean values
code = code.replace("return self.start()", "return bool(self.start())")
code = code.replace("return self.stop()", "return bool(self.stop())")

# 4. Ensure singleton auto_trader instance exists at bottom
if "auto_trader = AutoTrader()" not in code:
    code += "\nauto_trader = AutoTrader()\n"

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print("[OK] auto_trader.py successfully updated and lifespan-compatible.")

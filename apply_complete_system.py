import os

# 1. Notifications directory and telegram_alerts.py
os.makedirs("backend/notifications", exist_ok=True)
with open("backend/notifications/telegram_alerts.py", "w", encoding="utf-8") as f:
    f.write('''"""
BALLY FLOW - Telegram Bot Alert Integration
"""
import json, logging, os, urllib.request
logger = logging.getLogger("TelegramAlerts")

def send_telegram_message(text: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    enabled = os.getenv("TELEGRAM_NOTIFICATIONS_ENABLED", "true").strip().lower() in ("true", "1", "yes")
    if not enabled or not token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status == 200
    except Exception as e:
        logger.warning(f"Telegram alert error: {e}")
        return False

def notify_order_executed(symbol, action, lot_size, price, strategy="SMC", ticket=None, tp=None, sl=None):
    emoji = "🟢 <b>BUY ORDER EXECUTED</b>" if action.upper() == "BUY" else "🔴 <b>SELL ORDER EXECUTED</b>"
    ticket_str = f"\\n🎫 <b>Ticket:</b> <code>#{ticket}</code>" if ticket else ""
    msg = (f"{emoji}\\n━━━━━━━━━━━━━━━━━━━━\\n📈 <b>Symbol:</b> <code>{symbol}</code>\\n"
           f"⚡ <b>Action:</b> <b>{action.upper()}</b>\\n📦 <b>Lot Size:</b> <code>{lot_size:.2f}</code>\\n"
           f"💵 <b>Price:</b> <code>{price:.5f}</code>\\n🧠 <b>Strategy:</b> <code>{strategy}</code>{ticket_str}\\n"
           f"━━━━━━━━━━━━━━━━━━━━\\n⚡ <i>BALLY FLOW Trading Engine</i>")
    return send_telegram_message(msg)

def notify_position_closed(ticket, symbol, action, profit, close_price, reason="Profit Target"):
    emoji = "💰 <b>TRADE CLOSED (PROFIT)</b>" if profit >= 0 else "⚠️ <b>TRADE CLOSED (LOSS)</b>"
    pnl = f"+${profit:.2f}" if profit >= 0 else f"-${abs(profit):.2f}"
    msg = (f"{emoji}\\n━━━━━━━━━━━━━━━━━━━━\\n🎫 <b>Ticket:</b> <code>#{ticket}</code>\\n"
           f"💵 <b>Close Price:</b> <code>{close_price:.5f}</code>\\n📊 <b>Net P&L:</b> <b>{pnl}</b>\\n"
           f"📝 <b>Reason:</b> <i>{reason}</i>\\n━━━━━━━━━━━━━━━━━━━━")
    return send_telegram_message(msg)
''')

with open("backend/notifications/__init__.py", "w", encoding="utf-8") as f:
    f.write("from backend.notifications.telegram_alerts import *\n")

# 2. Candle Scalper module
os.makedirs("backend/trading_engine/candle_scalper", exist_ok=True)
with open("backend/trading_engine/candle_scalper/candle_scalper.py", "w", encoding="utf-8") as f:
    f.write('''"""
BALLY FLOW - Candle Momentum Scalper Engine
"""
import logging, MetaTrader5 as mt5
logger = logging.getLogger("CandleScalper")

def get_tiered_lot_size(balance: float) -> float:
    b = max(0.0, float(balance))
    if b < 500: return 0.01
    elif b < 1000: return 0.05
    elif b < 2000: return 0.10
    elif b < 5000: return 0.50
    elif b < 10000: return 1.00
    elif b < 20000: return 2.00
    elif b < 50000: return 5.00
    else: return 10.00

def analyze_candle_momentum(symbol: str):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 5)
    if rates is None or len(rates) < 2:
        return {"signal": "HOLD", "confidence": 0}
    current = rates[-1]
    delta = float(current["close"]) - float(current["open"])
    body = abs(delta)
    total_range = max(float(current["high"]) - float(current["low"]), 1e-6)
    if delta > 0 and (body / total_range) > 0.55:
        return {"signal": "BUY", "confidence": 80, "burst_count": 3, "profit_target_usd": 2.50}
    elif delta < 0 and (body / total_range) > 0.55:
        return {"signal": "SELL", "confidence": 80, "burst_count": 3, "profit_target_usd": 2.50}
    return {"signal": "HOLD", "confidence": 40}
''')

with open("backend/trading_engine/candle_scalper/__init__.py", "w", encoding="utf-8") as f:
    f.write("from backend.trading_engine.candle_scalper.candle_scalper import *\n")

# 3. Add strategy endpoint to backend/api/routes/application.py
app_py = "backend/api/routes/application.py"
if os.path.exists(app_py):
    with open(app_py, "r", encoding="utf-8") as f:
        app_code = f.read()
    if "/strategy" not in app_code:
        app_code += """

from pydantic import BaseModel
class StrategyUpdateRequest(BaseModel):
    strategy: str

@router.get("/strategy")
def get_bot_strategy():
    from backend.trading_engine.auto_trader import auto_trader
    current = getattr(auto_trader, "active_strategy", "SMC")
    return {"status": "ok", "strategy": current}

@router.put("/strategy")
def update_bot_strategy(req: StrategyUpdateRequest):
    from backend.trading_engine.auto_trader import auto_trader
    strat = req.strategy.upper()
    if strat not in ("SMC", "CANDLE_SCALPER"):
        strat = "SMC"
    auto_trader.active_strategy = strat
    return {"status": "ok", "strategy": strat, "message": f"Strategy updated to {strat}"}
"""
        with open(app_py, "w", encoding="utf-8") as f:
            f.write(app_code)

# 4. Wire Telegram alerts to manual orders in backend/api/routes/orders.py
orders_py = "backend/api/routes/orders.py"
if os.path.exists(orders_py):
    with open(orders_py, "r", encoding="utf-8") as f:
        oc = f.read()
    if "notify_order_executed" not in oc:
        oc = "from backend.notifications.telegram_alerts import notify_order_executed, notify_position_closed\n" + oc
        oc = oc.replace(
            'return {"status": "EXECUTED", "order_sent": True,',
            'try:\n            notify_order_executed(symbol=req.symbol, action=req.action, lot_size=lot, price=float(res.get("price", 0.0) or 0.0), strategy="MANUAL", ticket=res.get("ticket"))\n        except Exception:\n            pass\n        return {"status": "EXECUTED", "order_sent": True,'
        )
        oc = oc.replace(
            'return res\n\n\n@router.post("/close-all")',
            'try:\n        notify_position_closed(ticket=ticket, symbol="", action="", profit=float(res.get("profit", 0.0) or 0.0), close_price=float(res.get("price", 0.0) or 0.0))\n    except Exception:\n        pass\n    return res\n\n\n@router.post("/close-all")'
        )
        with open(orders_py, "w", encoding="utf-8") as f:
            f.write(oc)

# 5. Gmail SMTP OTP in backend/api/routes/auth.py
auth_py = "backend/api/routes/auth.py"
if os.path.exists(auth_py):
    with open(auth_py, "r", encoding="utf-8") as f:
        ac = f.read()
    if "def _send_gmail_otp" not in ac:
        smtp_func = """
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def _send_gmail_otp(to_email: str, code: str) -> bool:
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASS", "").strip()
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587").strip() or 587)
    smtp_from = os.getenv("SMTP_FROM", smtp_user).strip()

    if not smtp_user or not smtp_pass:
        print(f"[BALLY FLOW OTP] Dev OTP for {to_email} is: {code}")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your BALLY FLOW Verification Code: {code}"
        msg["From"] = f"BALLY FLOW <{smtp_from}>"
        msg["To"] = to_email
        msg.attach(MIMEText(f"Your BALLY FLOW verification code is: {code}", "plain"))
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_from, [to_email], msg.as_string())
        server.quit()
        return True
    except Exception as err:
        print(f"[BALLY FLOW OTP] SMTP error: {err}")
        return False
"""
        ac = ac.replace("router = APIRouter()", smtp_func + "\nrouter = APIRouter()")
        with open(auth_py, "w", encoding="utf-8") as f:
            f.write(ac)

# 6. Dashboard MT5-speed refresh (2.5s)
dash_file = "mobile/src/screens/DashboardScreen.tsx"
if os.path.exists(dash_file):
    with open(dash_file, "r", encoding="utf-8") as f:
        c = f.read()
    c = c.replace("}, 15000);", "}, 2500);")
    with open(dash_file, "w", encoding="utf-8") as f:
        f.write(c)

print("Applied all trading engine, Telegram, and mobile speed updates!")

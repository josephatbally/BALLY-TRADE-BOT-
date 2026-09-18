"""
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
    ticket_str = f"\n🎫 <b>Ticket:</b> <code>#{ticket}</code>" if ticket else ""
    msg = (f"{emoji}\n━━━━━━━━━━━━━━━━━━━━\n📈 <b>Symbol:</b> <code>{symbol}</code>\n"
           f"⚡ <b>Action:</b> <b>{action.upper()}</b>\n📦 <b>Lot Size:</b> <code>{lot_size:.2f}</code>\n"
           f"💵 <b>Price:</b> <code>{price:.5f}</code>\n🧠 <b>Strategy:</b> <code>{strategy}</code>{ticket_str}\n"
           f"━━━━━━━━━━━━━━━━━━━━\n⚡ <i>BALLY FLOW Trading Engine</i>")
    return send_telegram_message(msg)

def notify_position_closed(ticket, symbol, action, profit, close_price, reason="Profit Target"):
    emoji = "💰 <b>TRADE CLOSED (PROFIT)</b>" if profit >= 0 else "⚠️ <b>TRADE CLOSED (LOSS)</b>"
    pnl = f"+${profit:.2f}" if profit >= 0 else f"-${abs(profit):.2f}"
    msg = (f"{emoji}\n━━━━━━━━━━━━━━━━━━━━\n🎫 <b>Ticket:</b> <code>#{ticket}</code>\n"
           f"💵 <b>Close Price:</b> <code>{close_price:.5f}</code>\n📊 <b>Net P&L:</b> <b>{pnl}</b>\n"
           f"📝 <b>Reason:</b> <i>{reason}</i>\n━━━━━━━━━━━━━━━━━━━━")
    return send_telegram_message(msg)

import websocket, json, requests, time

BOT_TOKEN = "8860942386:AAH-TEui7ZLCRX_Yk-_5u4HRz_xkJdkJG-Q"
CHAT_ID = "8607132973"

def send(msg):
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", params={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except: pass

def on_message(ws, message):
    data = json.loads(message)
    o = data.get('o')
    if not o: return
    value = float(o['q']) * float(o['p'])
    if value >= 3000:
        side = "LONG LIQ 🔴" if o['S'] == 'SELL' else "SHORT LIQ 🟢"
        send(f"🚨 {o['s']} {side}\n💰 ${value:,.0f} @ ${o['p']}")

def on_open(ws):
    send("✅ Wow Bot 24/7 LIVE")

while True:
    try:
        ws = websocket.WebSocketApp("wss://fstream.binance.com/ws/!forceOrder@arr", on_message=on_message, on_open=on_open)
        ws.run_forever(ping_interval=20)
    except:
        time.sleep(5)

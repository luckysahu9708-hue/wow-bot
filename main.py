import os, time, threading, requests, io, base64
from flask import Flask, jsonify
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

app = Flask(__name__)
latest_data = []

def get_binance_data():
    try:
        url = "https://fapi.binance.com/fapi/v1/depth?symbol=BTCUSDT&limit=100"
        r = requests.get(url, timeout=10).json()
        bids = [[float(p[0]), float(p[1])] for p in r['bids']]
        asks = [[float(p[0]), float(p[1])] for p in r['asks']]
        price_url = "https://fapi.binance.com/fapi/v1/ticker/price?symbol=BTCUSDT"
        price = float(requests.get(price_url, timeout=10).json()['price'])
        return bids, asks, price
    except:
        return [], [], 0

def make_chart_image(bids, asks, price):
    plt.figure(figsize=(10,5))
    if bids: plt.scatter([b[0] for b in bids], [b[1] for b in bids], c='green', label='Long Liquidity', alpha=0.6)
    if asks: plt.scatter([a[0] for a in asks], [a[1] for a in asks], c='red', label='Short Liquidity', alpha=0.6)
    plt.axvline(price, color='yellow', linestyle='--', label=f'BTC: ${price}')
    plt.title(f'Lucky Heatmap - BTC ${price}')
    plt.xlabel('Price'); plt.ylabel('Size'); plt.legend(); plt.grid(True, alpha=0.3)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor='black', edgecolor='none')
    plt.close()
    buf.seek(0)
    return buf

def bot_loop():
    global latest_data
    while True:
        try:
            bids, asks, price = get_binance_data()
            if price:
                latest_data = {"bids": bids[:20], "asks": asks[:20], "price": price}
                img = make_chart_image(bids, asks, price)
                if BOT_TOKEN and CHAT_ID:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                    requests.post(url, data={"chat_id": CHAT_ID, "caption": f"🔥 Lucky Heatmap - BTC ${price}\nLive: https://lucky-heatmap.onrender.com"}, files={"photo": img}, timeout=20)
            time.sleep(300) # 5 min pe Telegram pe
        except Exception as e:
            print(e); time.sleep(10)

@app.route('/')
def home():
    return """
    <html><head><title>Lucky Heatmap</title>
    <meta http-equiv="refresh" content="10">
    <style>body{background:#000;color:#fff;text-align:center;font-family:Arial} img{width:95%;max-width:1000px;}</style>
    </head><body>
    <h1>🔥 Lucky Heatmap - LIVE</h1>
    <h3 id="price">Loading...</h3>
    <img id="chart" src="/chart">
    <p>Auto refreshes every 10 sec | Telegram bot also active</p>
    <script>
    async function load(){
        let d=await fetch('/api').then(r=>r.json());
        document.getElementById('price').innerText='BTC: $'+d.price;
        document.getElementById('chart').src='/chart?'+Date.now();
    }
    setInterval(load, 10000); load();
    </script></body></html>
    """

@app.route('/api')
def api():
    return jsonify(latest_data)

@app.route('/chart')
def chart():
    bids, asks, price = get_binance_data()
    buf = make_chart_image(bids, asks, price)
    return buf.getvalue(), 200, {'Content-Type': 'image/png'}

if __name__ == '__main__':
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

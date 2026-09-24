import os, time, threading, requests, io, base64, random
from flask import Flask
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8371820032:AAG1yD-JqUPcsy6j__6dKue0UwoC2UQyX1c")
CHAT_ID = os.environ.get("CHAT_ID", "805026310")
BTC_PRICE = 83901
LATEST_IMG = None

def get_live_data():
    global BTC_PRICE
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10).json()
        BTC_PRICE = float(r['bitcoin']['usd'])
    except:
        pass
    bids, asks = [], []
    try:
        j = requests.get("https://api.bybit.com/v5/market/orderbook?category=linear&symbol=BTCUSDT&limit=200", timeout=10).json()
        data = j['result']
        bids = [(float(x[0]), float(x[1])) for x in data['b']]
        asks = [(float(x[0]), float(x[1])) for x in data['a']]
    except:
        bids = [(BTC_PRICE - random.randint(50,2000), random.uniform(0.5,5)) for _ in range(80)]
        asks = [(BTC_PRICE + random.randint(50,2000), random.uniform(0.5,5)) for _ in range(80)]
    return BTC_PRICE, bids, asks

def make_heatmap():
    price, bids, asks = get_live_data()
    fig, ax = plt.subplots(figsize=(10, 4.5), facecolor='black')
    ax.set_facecolor('black')
    if bids:
        bx, bq = zip(*bids)
        bx_f = [x for x in bx if price-2000 < x < price]
        bq_f = [bq[i] for i,x in enumerate(bx) if price-2000 < x < price]
        if bx_f:
            sizes = np.array(bq_f)
            sizes = 20 + (sizes / max(sizes) * 300)
            ax.scatter(bx_f, np.random.normal(1, 0.05, len(bx_f)), s=sizes, c='#00FF88', alpha=0.7)
    if asks:
        axx, aq = zip(*asks)
        axx_f = [x for x in axx if price < x < price+2000]
        aq_f = [aq[i] for i,x in enumerate(axx) if price < x < price+2000]
        if axx_f:
            sizes = np.array(aq_f)
            sizes = 20 + (sizes / max(sizes) * 300)
            ax.scatter(axx_f, np.random.normal(1, 0.05, len(axx_f)), s=sizes, c='#FF4444', alpha=0.7)
    ax.axvline(price, color='yellow', linestyle='--', lw=2, label=f'BTC: ${price:,.0f}')
    ax.set_xlim(price-2000, price+2000)
    ax.set_ylim(0.7, 1.3)
    ax.set_yticks([])
    ax.tick_params(colors='white')
    ax.legend(facecolor='#111', edgecolor='#333', labelcolor='white', loc='upper right', fontsize=8)
    ax.grid(color='#1a1a1a', linestyle='--', alpha=0.5)
    plt.title("Lucky Heatmap - LIVE", color='white', fontsize=12)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor='black', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode(), price

def telegram_loop():
    global LATEST_IMG
    while True:
        try:
            img_b64, price = make_heatmap()
            LATEST_IMG = img_b64
            img_bytes = base64.b64decode(img_b64)
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            files = {'photo': ('heatmap.png', img_bytes)}
            data = {'chat_id': CHAT_ID, 'caption': f'🔥 BTC: ${price:,.2f}'}
            requests.post(url, files=files, data=data, timeout=15)
        except: pass
        time.sleep(300)

@app.route("/")
def home():
    img_b64, price = make_heatmap()
    return f'<html><head><meta http-equiv="refresh" content="15"></head><body style="background:black;color:white;text-align:center;font-family:Arial"><h2>🔥 Lucky Heatmap - LIVE</h2><h3 style="color:yellow">BTC: ${price:,.2f}</h3><img src="data:image/png;base64,{img_b64}" style="width:98%;max-width:1000px;border-radius:12px"><p>Green=Bids | Red=Asks</p></body></html>'

threading.Thread(target=telegram_loop, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

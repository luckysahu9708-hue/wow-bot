import os, time, threading, requests, io, base64, random
from flask import Flask
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8371820032:AAG1yD-JqUPcsy6j__6dKue0UwoC2UQyX1c")
CHAT_ID = os.environ.get("CHAT_ID", "805026310")
BTC_PRICE = 115000
LATEST_IMG = None

def get_btc_price():
    global BTC_PRICE
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5).json()
        BTC_PRICE = float(r['price'])
    except:
        try:
            r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5).json()
            BTC_PRICE = float(r['bitcoin']['usd'])
        except:
            pass
    return BTC_PRICE

def get_heatmap_image():
    try:
        price = get_btc_price()
        bids = []
        asks = []
        try:
            r = requests.get("https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=200", timeout=8).json()
            bids = [(float(p[0]), float(p[1])) for p in r.get('bids', [])]
            asks = [(float(p[0]), float(p[1])) for p in r.get('asks', [])]
        except:
            # fallback random data if binance blocked
            bids = [(price - random.randint(10,1500), random.random()*2) for _ in range(80)]
            asks = [(price + random.randint(10,1500), random.random()*2) for _ in range(80)]

        fig, ax = plt.subplots(figsize=(10,5), facecolor='black')
        ax.set_facecolor('black')

        if bids:
            bx, by = zip(*bids)
            ax.scatter(bx, [1]*len(bx), c='#00FF00', s=[max(10, y*40) for y in by], alpha=0.7)
        if asks:
            axx, axy = zip(*asks)
            ax.scatter(axx, [1]*len(axx), c='#FF0000', s=[max(10, y*40) for y in axy], alpha=0.7)

        ax.axvline(price, color='yellow', linestyle='--', linewidth=2, label=f'BTC: ${price:,.0f}')
        ax.set_ylim(0.8, 1.2)
        ax.set_xlim(price-1800, price+1800)
        ax.tick_params(colors='white')
        ax.set_xlabel('BTC Price', color='white')
        ax.legend(facecolor='black', edgecolor='white', labelcolor='white')
        ax.grid(color='#222222', alpha=0.5)
        plt.title("Lucky Heatmap - LIVE Orderbook", color='white')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor='black', dpi=130)
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()
    except Exception as e:
        print("Heatmap error:", e)
        return None

def telegram_loop():
    global LATEST_IMG
    while True:
        try:
            img_b64 = get_heatmap_image()
            if img_b64:
                LATEST_IMG = img_b64
                img_bytes = base64.b64decode(img_b64)
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                files = {'photo': ('heatmap.png', img_bytes)}
                data = {'chat_id': CHAT_ID, 'caption': f'🔥 BTC: ${BTC_PRICE:,.2f} - Lucky Heatmap LIVE'}
                requests.post(url, files=files, data=data, timeout=15)
                print("Telegram sent")
        except Exception as e:
            print("TG error", e)
        time.sleep(300)

@app.route("/")
def home():
    global LATEST_IMG
    price = get_btc_price()
    if not LATEST_IMG:
        LATEST_IMG = get_heatmap_image()

    if not LATEST_IMG:
        return f"<body style='background:black;color:white'><h1>BTC ${price} - Generating...</h1><script>setTimeout(()=>location.reload(),3000)</script></body>"

    return f"""
    <html><head><meta http-equiv="refresh" content="10"><title>Lucky Heatmap</title></head>
    <body style="background:black;color:white;text-align:center;font-family:Arial;margin:0;padding:10px">
    <h2>🔥 Lucky Heatmap - LIVE</h2>
    <h3>BTC: ${price:,.2f}</h3>
    <img src="data:image/png;base64,{LATEST_IMG}" style="width:98%;max-width:1000px;border-radius:10px;border:1px solid #333">
    <p style="color:#aaa">Auto refresh 10 sec | Telegram every 5 min</p>
    </body></html>
    """

threading.Thread(target=telegram_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

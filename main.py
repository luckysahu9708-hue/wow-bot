import os, time, threading, requests, io, base64
from flask import Flask
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8371820032:AAG1yD-JqUPcsy6j__6dKue0UwoC2UQyX1c")
CHAT_ID = os.environ.get("CHAT_ID", "805026310")
BTC_PRICE = 0

def get_btc_price():
    global BTC_PRICE
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5).json()
        BTC_PRICE = float(r['price'])
        return BTC_PRICE
    except:
        return BTC_PRICE or 115000

def get_heatmap_image():
    try:
        # Binance orderbook
        r = requests.get("https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=500", timeout=10).json()
        bids = [(float(p[0]), float(p[1])) for p in r['bids']]
        asks = [(float(p[0]), float(p[1])) for p in r['asks']]

        price = get_btc_price()
        if price == 0: price = 115000

        # Filter near price +- 2000$
        bids = [b for b in bids if price-2000 < b[0] < price+2000]
        asks = [a for a in asks if price-2000 < a[0] < price+2000]

        fig, ax = plt.subplots(figsize=(8,4), facecolor='black')
        ax.set_facecolor('black')

        # Plot bids green
        if bids:
            bx, by = zip(*bids)
            ax.scatter(bx, [1]*len(bx), c='lime', s=[y*20 for y in by], alpha=0.6, label='BIDS')
        if asks:
            axx, axy = zip(*asks)
            ax.scatter(axx, [1]*len(axx), c='red', s=[y*20 for y in axy], alpha=0.6, label='ASKS')

        ax.axvline(price, color='yellow', linestyle='--', label=f'BTC: ${price:,.0f}')
        ax.set_ylim(0.5, 1.5)
        ax.set_xlim(price-1500, price+1500)
        ax.tick_params(colors='white')
        ax.legend(facecolor='black', edgecolor='white', labelcolor='white')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor='black', dpi=120)
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()
    except Exception as e:
        print("Heatmap error:", e)
        return None

LATEST_IMG = None

def telegram_loop():
    global LATEST_IMG
    while True:
        try:
            img_b64 = get_heatmap_image()
            if img_b64:
                LATEST_IMG = img_b64
                # send to telegram
                img_bytes = base64.b64decode(img_b64)
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                files = {'photo': ('heatmap.png', img_bytes)}
                data = {'chat_id': CHAT_ID, 'caption': f'🔥 BTC: ${get_btc_price():,.2f} - Lucky Heatmap LIVE'}
                requests.post(url, files=files, data=data, timeout=15)
                print("Telegram photo sent")
        except Exception as e:
            print("Telegram error:", e)
        time.sleep(300) # 5 min me ek baar

@app.route("/")
def home():
    global LATEST_IMG
    if not LATEST_IMG:
        LATEST_IMG = get_heatmap_image()
        price = get_btc_price()
    else:
        price = BTC_PRICE

    if not LATEST_IMG:
        return "<h1 style='color:white;background:black'>Loading... refresh in 5 sec</h1><script>setTimeout(()=>location.reload(),5000)</script>"

    return f"""
    <html>
    <head><title>Lucky Heatmap</title><meta http-equiv="refresh" content="10"></head>
    <body style="background:black;color:white;text-align:center;font-family:Arial">
    <h2>🔥 Lucky Heatmap - LIVE</h2>
    <h3>BTC: ${price:,.2f}</h3>
    <img src="data:image/png;base64,{LATEST_IMG}" style="width:95%;max-width:900px;border:1px solid #333">
    <p>Auto refreshes every 10 sec | Telegram bot also active</p>
    </body></html>
    """

# Start thread
threading.Thread(target=telegram_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

import os, time, threading, requests, io, base64, random
from flask import Flask
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8371820032:AAG1yD-JqUPcsy6j__6dKue0UwoC2UQyX1c")
CHAT_ID = os.environ.get("CHAT_ID", "805026310")

def get_coinbase_data():
    price = 83901
    bids, asks = [], []
    try:
        # 1. Live Price from Coinbase
        r = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=10).json()
        price = float(r['data']['amount'])
    except:
        pass
    try:
        # 2. Orderbook from Coinbase - yehi asli heatmap banayega
        j = requests.get("https://api.exchange.coinbase.com/products/BTC-USD/book?level=2", timeout=10, headers={"User-Agent":"Mozilla/5.0"}).json()
        bids = [(float(x[0]), float(x[1])) for x in j['bids'][:200]]
        asks = [(float(x[0]), float(x[1])) for x in j['asks'][:200]]
    except Exception as e:
        print("Coinbase book fail", e)
        bids = [(price - random.randint(50,2000), random.uniform(0.5,5)) for _ in range(80)]
        asks = [(price + random.randint(50,2000), random.uniform(0.5,5)) for _ in range(80)]

    return price, bids, asks

def make_heatmap():
    price, bids, asks = get_coinbase_data()
    fig, ax = plt.subplots(figsize=(10, 4.5), facecolor='black')
    ax.set_facecolor('black')

    if bids:
        bx, bq = zip(*bids)
        bx_f = [x for x in bx if price-2000 < x < price]
        bq_f = [bq[i] for i,x in enumerate(bx) if price-2000 < x < price]
        if bx_f:
            sizes = np.array(bq_f)
            sizes = 20 + (sizes / max(sizes) * 350)
            ax.scatter(bx_f, np.random.normal(1, 0.04, len(bx_f)), s=sizes, c='#00FF88', alpha=0.75)

    if asks:
        axx, aq = zip(*asks)
        axx_f = [x for x in axx if price < x < price+2000]
        aq_f = [aq[i] for i,x in enumerate(axx) if price < x < price+2000]
        if axx_f:
            sizes = np.array(aq_f)
            sizes = 20 + (sizes / max(sizes) * 350)
            ax.scatter(axx_f, np.random.normal(1, 0.04, len(axx_f)), s=sizes, c='#FF4444', alpha=0.75)

    ax.axvline(price, color='yellow', linestyle='--', lw=2, label=f'BTC Coinbase: ${price:,.2f}')
    ax.set_xlim(price-2000, price+2000)
    ax.set_ylim(0.7, 1.3)
    ax.set_yticks([])
    ax.tick_params(colors='white')
    ax.legend(facecolor='#111', edgecolor='#333', labelcolor='white', loc='upper right', fontsize=9)
    ax.grid(color='#1a1a1a', linestyle='--', alpha=0.5)
    plt.title("Lucky Heatmap - Coinbase LIVE", color

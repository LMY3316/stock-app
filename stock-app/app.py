import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
from fredapi import Fred
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)

# FRED API 金鑰
FRED_API_KEY = "f8c628f6ead461499c67471a516d1e8c"
fred = Fred(api_key=FRED_API_KEY)

# 1. 取得美股個股 5 分鐘線圖與最新價格
@app.route('/api/stock/<ticker>')
def get_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1d", interval="5m")
        chart_data = [{"time": idx.strftime('%H:%M'), "price": round(row['Close'], 2)} for idx, row in df.iterrows()]
        current_price = stock.info.get('regularMarketPrice') or (round(df['Close'].iloc[-1], 2) if not df.empty else 0)
        return jsonify({"status": "success", "symbol": ticker.upper(), "price": current_price, "chart": chart_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# 2. 抓取美國總經數據 (CPI, PCE, GDP, NFP)
@app.route('/api/macro/<series_id>')
def get_macro(series_id):
    try:
        data = fred.get_series(series_id).tail(12)
        result = [{"date": idx.strftime('%Y-%m'), "value": float(val)} for idx, val in data.items()]
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# 3. 抓取國外重大新聞 RSS
@app.route('/api/news')
def get_news():
    url = "https://news.google.com/rss/search?q=Federal+Reserve+OR+CPI+OR+PCE+OR+GDP&hl=en-US&gl=US&ceid=US:en"
    try:
        res = requests.get(url, timeout=5)
        root = ET.fromstring(res.content)
        news = [{"title": item.find('title').text, "link": item.find('link').text} for item in root.findall('.//item')[:5]]
        return jsonify({"status": "success", "news": news})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
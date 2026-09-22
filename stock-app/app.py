from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
from fredapi import Fred
import os
import requests
from xml.etree import ElementTree as ET

app = Flask(__name__)
CORS(app)

FRED_API_KEY = os.environ.get('FRED_API_KEY', '')

@app.route('/')
def home():
    return jsonify({"status": "API is running!"})

@app.route('/api/stock')
def get_stock():
    symbol = request.args.get('symbol', 'NVDA').upper()
    try:
        df = yf.download(tickers=symbol, period='1mo', interval='1d', progress=False)
        
        if df.empty:
            return jsonify({"error": f"No data found for symbol {symbol}"}), 404

        if hasattr(df.columns, 'levels'):
            close_data = df['Close'][symbol] if symbol in df['Close'] else df['Close'].iloc[:, 0]
        else:
            close_data = df['Close']

        close_data = close_data.tail(30)

        timestamps = [d.strftime('%Y-%m-%d') for d in close_data.index]
        prices = [round(float(p), 2) for p in close_data.values]

        return jsonify({
            "symbol": symbol,
            "timestamps": timestamps,
            "prices": prices
        })
    except Exception as e:
        print("Stock Error:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/macro')
def get_macro():
    indicator = request.args.get('indicator', 'CPI').upper()
    
    series_map = {
        'CPI': 'CPIAUCSL',
        'PCE': 'PCEPI',
        'GDP': 'GDP',
        'NFP': 'PAYEMS'
    }
    
    series_id = series_map.get(indicator, 'CPIAUCSL')

    if not FRED_API_KEY:
        return jsonify({"error": "FRED_API_KEY is missing"}), 500

    try:
        fred = Fred(api_key=FRED_API_KEY)
        data = fred.get_series(series_id)
        
        recent_data = data.tail(12)
        
        result = []
        for date, val in recent_data.items():
            result.append({
                "date": date.strftime('%Y-%m'),
                "value": round(float(val), 2)
            })
        
        result.reverse()
        return jsonify(result)
    except Exception as e:
        print("Macro Error:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/news')
def get_news():
    try:
        url = "https://news.google.com/rss/search?q=Federal+Reserve+economy+when:7d&hl=en-US&gl=US&ceid=US:en"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(resp.content)

        news_items = []
        for item in root.findall('.//item')[:5]:
            title = item.find('title').text if item.find('title') is not None else 'No Title'
            link = item.find('link').text if item.find('link') is not None else '#'
            news_items.append({
                "title": title,
                "link": link
            })
        return jsonify(news_items)
    except Exception as e:
        print("News Error:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

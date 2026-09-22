from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
from fredapi import Fred
import os
import requests
from xml.etree import ElementTree as ET

app = Flask(__name__)
CORS(app)  # 允許跨域請求

# 取得 FRED API Key
FRED_API_KEY = os.environ.get('FRED_API_KEY', '')

@app.route('/')
def home():
    return jsonify({"status": "API is running!"})

# 1. 股票數據 API (含休市自動備援)
@app.route('/api/stock')
def get_stock():
    symbol = request.args.get('symbol', 'NVDA').upper()
    try:
        ticker = yf.Ticker(symbol)
        
        # 先嘗試抓取 5 天內的 5 分鐘 K 線
        df = ticker.history(period='5d', interval='5m')
        
        # 如果休市或無分線資料，自動降級抓取近期日線
        if df.empty:
            df = ticker.history(period='1mo', interval='1d')
            
        if df.empty:
            return jsonify({"error": "No data found for symbol"}), 404

        # 取最近 50 筆資料避免圖表過於擁擠
        df = df.tail(50)

        # 格式化時間與價格
        timestamps = [d.strftime('%m-%d %H:%M') if '5m' in str(df.index.inferred_type) else d.strftime('%Y-%m-%d') for d declared_in_index for d in df.index]
        
        # 修正時間格式化
        timestamps = []
        for idx in df.index:
            try:
                timestamps.append(idx.strftime('%m/%d %H:%M'))
            except:
                timestamps.append(str(idx)[:10])

        prices = [round(p, 2) for p in df['Close'].tolist()]

        return jsonify({
            "symbol": symbol,
            "timestamps": timestamps,
            "prices": prices
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. 總經數據 API
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
        
        # 取最新的 12 筆歷史資料
        recent_data = data.tail(12)
        
        result = []
        for date, val in recent_data.items():
            result.append({
                "date": date.strftime('%Y-%m'),
                "value": round(val, 2)
            })
        
        # 最新日期排在最前
        result.reverse()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. 新聞 API
@app.route('/api/news')
def get_news():
    try:
        url = "https://news.google.com/rss/search?q=Federal+Reserve+economy+when:7d&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(url, timeout=10)
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
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

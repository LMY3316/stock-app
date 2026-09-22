from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"status": "Stock API is running!"})

@app.route('/api/stock')
def get_stock():
    symbol = request.args.get('symbol', 'NVDA').upper()
    try:
        df = yf.download(tickers=symbol, period='1mo', interval='1d', progress=False)
        
        if df.empty:
            return jsonify({"error": f"找不到股票代號 {symbol} 的數據"}), 404

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
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

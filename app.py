from flask import Flask, request, jsonify
import pandas as pd
import pandas_ta as ta

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "ARION Technical Analysis Service is Running!"

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        # Menerima data dari Make.com
        # Kita harapkan format: { "ohlcv_data": [[time, o, h, l, c, v], ...] }
        content = request.json
        raw_data = content.get('ohlcv_data', [])

        if not raw_data:
            return jsonify({"error": "No data provided"}), 400

        # GeckoTerminal memberikan format: [Timestamp, Open, High, Low, Close, Volume]
        # Kita ubah menjadi DataFrame (Tabel)
        df = pd.DataFrame(raw_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Pastikan data diurutkan dari terlama ke terbaru
        df = df.sort_values('timestamp', ascending=True)
        
        # Konversi ke angka float (untuk keamanan)
        df['close'] = df['close'].astype(float)

        # --- PERHITUNGAN INDIKATOR ---
        # 1. RSI (14)
        df['RSI'] = df.ta.rsi(close='close', length=14)
        
        # 2. EMA (20 & 200)
        df['EMA_20'] = df.ta.ema(close='close', length=20)
        df['EMA_200'] = df.ta.ema(close='close', length=200)

        # Ambil baris data terakhir (Candle terbaru/closed)
        last_row = df.iloc[-1]

        # Tentukan Sinyal Sederhana untuk membantu Gemini
        trend = "UPTREND" if last_row['close'] > last_row['EMA_200'] else "DOWNTREND"
        momentum = "OVERSOLD" if last_row['RSI'] < 30 else ("OVERBOUGHT" if last_row['RSI'] > 70 else "NEUTRAL")

        result = {
            "price": last_row['close'],
            "rsi": round(last_row['RSI'], 2),
            "ema_20": last_row['EMA_20'],
            "ema_200": last_row['EMA_200'],
            "signal_hint": {
                "trend_status": trend,
                "momentum_status": momentum
            }
        }

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
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
        content = request.json
        
        # --- LOGIKA BARU: DETEKSI FORMAT OTOMATIS ---
        raw_data = []
        
        # Kasus A: Jika data dikirim rapi dengan kunci 'ohlcv_data'
        if 'ohlcv_data' in content:
            raw_data = content['ohlcv_data']
            
        # Kasus B: Jika data dikirim MENTAH (Raw) langsung dari GeckoTerminal
        # Struktur: { "data": { "attributes": { "ohlcv_list": [...] } } }
        elif 'data' in content and 'attributes' in content['data']:
            raw_data = content['data']['attributes']['ohlcv_list']
            
        else:
            return jsonify({"error": "Format JSON tidak dikenali. Pastikan data GeckoTerminal masuk."}), 400

        # --- LANJUT KE PERHITUNGAN BIASA ---
        if not raw_data:
             return jsonify({"error": "Data kosong"}), 400

        df = pd.DataFrame(raw_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = df.sort_values('timestamp', ascending=True)
        df['close'] = df['close'].astype(float)

        # Hitung Indikator
        df['RSI'] = df.ta.rsi(close='close', length=14)
        df['EMA_20'] = df.ta.ema(close='close', length=20)
        df['EMA_200'] = df.ta.ema(close='close', length=200)

        last_row = df.iloc[-1]
        
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
from flask import Flask, request, jsonify
import pandas as pd
import pandas_ta as ta
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "ARION Technical Analysis Service is Running!", 200

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        content = request.json
        
        # --- 1. LOGIKA DETEKSI FORMAT DATA (Tetap Pertahankan ini) ---
        raw_data = []
        
        # Kasus A: Format Make.com standar
        if 'ohlcv_data' in content:
            raw_data = content['ohlcv_data']
            
        # Kasus B: Format Mentah GeckoTerminal/Birdeye
        elif 'data' in content and 'attributes' in content['data']:
            raw_data = content['data']['attributes']['ohlcv_list']
            
        else:
            return jsonify({"error": "Format JSON tidak dikenali."}), 400

        if not raw_data:
             return jsonify({"error": "Data kosong"}), 400

        # --- 2. PERSIAPAN DATAFRAME ---
        # Kolom standar: Timestamp, Open, High, Low, Close, Volume
        df = pd.DataFrame(raw_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Pastikan data urut dari lama ke baru
        df = df.sort_values('timestamp', ascending=True)
        
        # Konversi ke angka desimal (float) agar bisa dihitung
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)

        # --- 3. PERHITUNGAN INDIKATOR (UPDATE DI SINI) ---
        
        # A. RSI (Momentum)
        df['RSI'] = df.ta.rsi(close='close', length=14)
        
        # B. EMA (Moving Averages)
        df['EMA_20'] = df.ta.ema(close='close', length=20)   # Tren Jangka Pendek
        df['EMA_50'] = df.ta.ema(close='close', length=50)   # Tren Jangka Menengah (BARU)
        df['EMA_200'] = df.ta.ema(close='close', length=200) # Tren Jangka Panjang

        # C. Volume Analysis (BARU)
        # Menghitung rata-rata volume 20 candle terakhir
        df['VOL_SMA_20'] = df.ta.sma(close='volume', length=20)

        # Ambil baris data terakhir (Candle terbaru yang sudah close)
        last_row = df.iloc[-1]
        
        # --- 4. LOGIKA SINYAL & STATUS ---
        
        # Tentukan Tren Harga
        trend = "UPTREND" if last_row['close'] > last_row['EMA_200'] else "DOWNTREND"
        
        # Tentukan Momentum RSI
        momentum = "OVERSOLD" if last_row['RSI'] < 30 else ("OVERBOUGHT" if last_row['RSI'] > 70 else "NEUTRAL")

        # Tentukan Status Volume (BARU)
        # Jika volume > 1.5x rata-rata, kita sebut "SPIKE" (Lonjakan)
        # Jika volume > rata-rata, kita sebut "HIGH"
        if last_row['volume'] > (last_row['VOL_SMA_20'] * 1.5):
            vol_status = "SPIKE (Huge Interest)"
        elif last_row['volume'] > last_row['VOL_SMA_20']:
            vol_status = "HIGH (Active)"
        else:
            vol_status = "NORMAL/LOW"

        # --- 5. MENYUSUN HASIL AKHIR (JSON RESPONSE) ---
        result = {
            "price": last_row['close'],
            "rsi": round(last_row['RSI'], 2),
            "ema_20": last_row['EMA_20'],
            "ema_50": last_row['EMA_50'],     # Data Baru
            "ema_200": last_row['EMA_200'],
            "volume_data": {                  # Data Baru
                "current": last_row['volume'],
                "average_20": last_row['VOL_SMA_20'],
                "status": vol_status
            },
            "signal_hint": {
                "trend_status": trend,
                "momentum_status": momentum
            }
        }

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
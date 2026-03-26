from flask import Flask, jsonify, request
from flask_cors import CORS
import MetaTrader5 as mt5
from datetime import datetime, timezone

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

INSTRUMENTS = {
    "GOLD": {"symbol": "XAUUSD", "name": "Gold (XAU/USD)"},
    "OIL": {"symbol": "WTI", "name": "Crude Oil (WTI)"},
    "EURUSD": {"symbol": "EURUSD", "name": "EUR/USD"},
    "NATGAS": {"symbol": "NATGAS", "name": "Natural Gas"},
    "NASDAQ100": {"symbol": "NAS100", "name": "Nasdaq 100"},
}

TIMEFRAMES = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "H1": mt5.TIMEFRAME_H1,
    "D1": mt5.TIMEFRAME_D1,
}

# Number of bars to fetch per timeframe
BAR_COUNTS = {
    "M1": 500,
    "M5": 500,
    "M15": 500,
    "H1": 500,
    "D1": 365,
}


def init_mt5():
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/instruments")
def get_instruments():
    return jsonify(INSTRUMENTS)


@app.route("/api/history/<instrument_key>")
def get_history(instrument_key):
    instrument_key = instrument_key.upper()
    if instrument_key not in INSTRUMENTS:
        return jsonify({"error": "Unknown instrument"}), 404

    symbol = INSTRUMENTS[instrument_key]["symbol"]
    timeframe_key = request.args.get("timeframe", "D1").upper()

    if timeframe_key not in TIMEFRAMES:
        return jsonify({"error": f"Invalid timeframe: {timeframe_key}"}), 400

    mt5_tf = TIMEFRAMES[timeframe_key]
    count = BAR_COUNTS.get(timeframe_key, 500)

    try:
        init_mt5()
        rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, count)

        if rates is None or len(rates) == 0:
            return jsonify({"error": f"No data for {symbol}"}), 404

        data = []
        for r in rates:
            data.append({
                "time": int(r["time"]),
                "open": round(float(r["open"]), 5),
                "high": round(float(r["high"]), 5),
                "low": round(float(r["low"]), 5),
                "close": round(float(r["close"]), 5),
                "volume": int(r["tick_volume"]),
            })

        return jsonify({
            "name": INSTRUMENTS[instrument_key]["name"],
            "symbol": symbol,
            "timeframe": timeframe_key,
            "data": data,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/quote/<instrument_key>")
def get_quote(instrument_key):
    instrument_key = instrument_key.upper()
    if instrument_key not in INSTRUMENTS:
        return jsonify({"error": "Unknown instrument"}), 404

    symbol = INSTRUMENTS[instrument_key]["symbol"]

    try:
        init_mt5()
        tick = mt5.symbol_info_tick(symbol)
        info = mt5.symbol_info(symbol)

        if tick is None or info is None:
            return jsonify({"error": f"No tick data for {symbol}"}), 404

        # Get previous day's close for change calculation
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 2)
        print(rates)
        if rates is not None and len(rates) >= 2:
            prev_close = float(rates[-2]["close"])
            current_close = float(rates[-1]["close"])
            change = current_close - prev_close
            change_pct = (change / prev_close) * 100
        else:
            change = 0
            change_pct = 0

        price = (tick.bid + tick.ask) / 2

        return jsonify({
            "name": INSTRUMENTS[instrument_key]["name"],
            "price": round(price, 5),
            "bid": round(tick.bid, 5),
            "ask": round(tick.ask, 5),
            "change": round(change, 5),
            "changePct": round(change_pct, 2),
            "high": round(float(rates[-1]["high"]), 5) if rates is not None and len(rates) > 0 else 0,
            "low": round(float(rates[-1]["low"]), 5) if rates is not None and len(rates) > 0 else 0,
            "open": round(float(rates[-1]["open"]), 5) if rates is not None and len(rates) > 0 else 0,
            "volume": int(rates[-1]["tick_volume"]) if rates is not None and len(rates) > 0 else 0,
            "spread": round(tick.ask - tick.bid, 5),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("Trading Dashboard (MT5) running at http://localhost:5000")
    app.run(debug=True, port=5000)

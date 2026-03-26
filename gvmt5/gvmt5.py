"""gvmt5 - Fetch candles from MetaTrader 5, calculate SMA & RSI for multiple symbols."""

import sys

import MetaTrader5 as mt5
import pandas as pd

SYMBOLS = ["XAUUSD", "XAGUSD", "WTI", "NATGAS", "NAS100", "JPN225", "BTCUSD"]
CANDLE_COUNT = 200
SMA_PERIOD = 150
RSI_PERIOD = 14

TIMEFRAMES = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
}


def initialize_mt5():
    if not mt5.initialize():
        print(f"MT5 initialization failed: {mt5.last_error()}")
        sys.exit(1)
    print(f"Connected to MetaTrader 5 build {mt5.version()}")


def fetch_candles(symbol, timeframe_mt5, count):
    rates = mt5.copy_rates_from_pos(symbol, timeframe_mt5, 0, count)
    if rates is None or len(rates) == 0:
        print(f"Failed to fetch {symbol} candles: {mt5.last_error()}")
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df


def calc_sma(series, period):
    return series.rolling(window=period).mean()


def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def print_results(symbol, label, df):
    df = df.copy()
    df["SMA_150"] = calc_sma(df["close"], SMA_PERIOD)
    df["RSI_14"] = calc_rsi(df["close"], RSI_PERIOD)

    latest = df.iloc[-1]
    sma_str = f"{latest['SMA_150']:.2f}" if pd.notna(latest["SMA_150"]) else "N/A"
    rsi_str = f"{latest['RSI_14']:.2f}" if pd.notna(latest["RSI_14"]) else "N/A"
    print(f"  {symbol:<10} {label:<4}  |  Close: {latest['close']:.2f}  |  SMA(150): {sma_str}  |  RSI(14): {rsi_str}")


def main():
    initialize_mt5()

    print(f"\n{'=' * 80}")
    print(f"  {'Symbol':<10} {'TF':<4}  |  {'Close':>10}  |  {'SMA(150)':>10}  |  {'RSI(14)':>8}")
    print(f"{'=' * 80}")

    for symbol in SYMBOLS:
        if not mt5.symbol_select(symbol, True):
            print(f"Failed to select {symbol}: {mt5.last_error()} — skipping")
            continue

        for label, tf in TIMEFRAMES.items():
            df = fetch_candles(symbol, tf, CANDLE_COUNT)
            if df is not None:
                print_results(symbol, label, df)

    mt5.shutdown()
    print(f"\n{'=' * 90}")
    print("MT5 connection closed.")


if __name__ == "__main__":
    main()

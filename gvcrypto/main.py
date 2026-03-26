#!/usr/bin/env python3
"""
gvcrypto — ETH Price + Technical Analysis Alerter
Fetches ETH_USDT price, 150-candle SMA, and RSI from MEXC Futures
for 1-minute and 5-minute timeframes, then sends to Telegram every 5 minutes.
"""

import json
import logging
import os
import sys
import time as time_module
from datetime import datetime, timezone

import requests
import schedule

# ─── Configuration ────────────────────────────────────────────────────────────

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config() -> dict:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ─── Logging (Windows-safe UTF-8) ─────────────────────────────────────────────

log = logging.getLogger("gvcrypto")
log.setLevel(logging.INFO)
_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

_stream = logging.StreamHandler(
    stream=open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1, closefd=False)
)
_stream.setFormatter(_fmt)
log.addHandler(_stream)

_file_handler = logging.FileHandler(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "gvcrypto.log"),
    encoding="utf-8",
)
_file_handler.setFormatter(_fmt)
log.addHandler(_file_handler)

# ─── MEXC Futures API ─────────────────────────────────────────────────────────

MEXC_BASE_URL = "https://contract.mexc.com"

# Seconds per interval — used to calculate start timestamps
INTERVAL_SECONDS = {
    "Min1":  60,
    "Min3":  180,
    "Min5":  300,
    "Min15": 900,
    "Min30": 1800,
    "Min60": 3600,
}


def get_eth_ticker() -> dict | None:
    """Fetch the latest ETH_USDT spot ticker from MEXC Futures."""
    url = f"{MEXC_BASE_URL}/api/v1/contract/ticker"
    params = {"symbol": "ETH_USDT"}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        if not payload.get("success"):
            log.error("MEXC ticker API error: %s", payload)
            return None
        data = payload.get("data", {})
        if isinstance(data, list):
            data = next((d for d in data if d.get("symbol") == "ETH_USDT"), None)
        return data
    except requests.exceptions.RequestException as e:
        log.error("MEXC ticker request failed: %s", e)
        return None


def get_candles(symbol: str, interval: str, limit: int = 200) -> list | None:
    """
    Fetch OHLCV candles from MEXC Futures kline API.
    Returns a list of closing prices (floats), newest last.
    Endpoint: GET /api/v1/contract/kline/{symbol}
    """
    url = f"{MEXC_BASE_URL}/api/v1/contract/kline/{symbol}"
    secs = INTERVAL_SECONDS.get(interval, 60)

    # Request a window with buffer so we always get >= limit candles
    end_ts   = int(time_module.time())
    start_ts = end_ts - (limit + 10) * secs

    params = {
        "interval": interval,
        "start":    start_ts,
        "end":      end_ts,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        payload = resp.json()

        if not payload.get("success"):
            log.error("MEXC kline API error (%s %s): %s", symbol, interval, payload)
            return None

        data = payload.get("data", {})
        raw_closes = data.get("close", [])

        if not raw_closes:
            log.warning("No candle data returned for %s %s", symbol, interval)
            return None

        closes = [float(c) for c in raw_closes]
        # Return the most recent `limit` candles
        return closes[-limit:]

    except requests.exceptions.RequestException as e:
        log.error("MEXC kline request failed (%s %s): %s", symbol, interval, e)
        return None
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        log.error("Failed to parse MEXC kline response (%s %s): %s", symbol, interval, e)
        return None


def get_1h_high_low(symbol: str) -> tuple[float, float] | None:
    """
    Fetch the latest 1-hour candle for `symbol` and return (high, low).
    Used to calculate 1-hour volatility.
    """
    url = f"{MEXC_BASE_URL}/api/v1/contract/kline/{symbol}"
    end_ts   = int(time_module.time())
    start_ts = end_ts - 2 * 3600  # fetch last 2 hours to ensure we catch the current candle

    params = {
        "interval": "Min60",
        "start":    start_ts,
        "end":      end_ts,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        payload = resp.json()

        if not payload.get("success"):
            log.error("MEXC 1h kline API error: %s", payload)
            return None

        data = payload.get("data", {})
        highs  = data.get("high", [])
        lows   = data.get("low", [])

        if not highs or not lows:
            log.warning("No 1h candle data returned for %s", symbol)
            return None

        # Use the most recent completed candle
        high_1h = float(highs[-1])
        low_1h  = float(lows[-1])
        return high_1h, low_1h

    except requests.exceptions.RequestException as e:
        log.error("MEXC 1h kline request failed: %s", e)
        return None
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        log.error("Failed to parse MEXC 1h kline response: %s", e)
        return None


# ─── Technical Indicators ─────────────────────────────────────────────────────

def calculate_sma(prices: list, period: int = 150) -> float | None:
    """Simple Moving Average over the last `period` prices."""
    if len(prices) < period:
        log.warning("Not enough data for SMA-%d (got %d candles)", period, len(prices))
        return None
    return round(sum(prices[-period:]) / period, 4)


def calculate_rsi(prices: list, period: int = 14) -> float | None:
    """
    Relative Strength Index using Wilder's smoothing method.
    Requires at least period+1 data points.
    """
    if len(prices) < period + 1:
        log.warning("Not enough data for RSI-%d (got %d candles)", period, len(prices))
        return None

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

    gains  = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]

    # Seed: simple average of first `period` values
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Wilder's smoothed rolling average
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    rs  = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return round(rsi, 2)


def calculate_volatility(high: float, low: float, last_price: float) -> float | None:
    """
    1-Hour Volatility = (1h High - 1h Low) / Last Price * 100
    Returns a percentage rounded to 4 decimal places.
    """
    if last_price == 0:
        return None
    return round(((high - low) / last_price) * 100, 4)


def rsi_label(rsi: float | None) -> str:
    """Return a human-readable RSI zone label."""
    if rsi is None:
        return "N/A"
    if rsi >= 80:
        return "Extremely Overbought"
    if rsi >= 70:
        return "Overbought"
    if rsi <= 20:
        return "Extremely Oversold"
    if rsi <= 30:
        return "Oversold"
    if rsi >= 55:
        return "Bullish"
    if rsi <= 45:
        return "Bearish"
    return "Neutral"


def price_vs_ma_label(price: float, ma: float | None) -> str:
    """Return bullish/bearish label relative to the MA."""
    if ma is None:
        return "N/A"
    diff_pct = ((price - ma) / ma) * 100
    if diff_pct > 0:
        return f"Above MA (+{diff_pct:.2f}%)"
    return f"Below MA ({diff_pct:.2f}%)"


# ─── ntfy.sh Push Notifications (used for HIGH ALERTS only) ──────────────────

NTFY_URL = "https://ntfy.sh/gv_ethusdt_bot_55555"


def send_ntfy_alert(title: str, message: str, priority: str = "urgent") -> bool:
    """
    Send a push notification via ntfy.sh.
    Used exclusively for HIGH ALERT (price breaking 1h high/low).
    NOT used for regular 5-minute updates.
    """
    try:
        resp = requests.post(
            NTFY_URL,
            data=message.encode("utf-8"),
            headers={
                "Title":    title,
                "Priority": priority,
                "Tags":     "rotating_light",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        log.error("ntfy.sh alert failed: %s", e)
        return False


# ─── Telegram ─────────────────────────────────────────────────────────────────

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram_message(token: str, chat_id, text: str) -> bool:
    """Send a message via Telegram Bot API."""
    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        if not result.get("ok"):
            log.error("Telegram API error: %s", result)
            return False
        return True
    except requests.exceptions.RequestException as e:
        log.error("Failed to send Telegram message: %s", e)
        return False


# ─── Message Formatting ───────────────────────────────────────────────────────

def _divider() -> str:
    return "\u2500" * 30


def format_full_message(
    ticker: dict,
    closes_1m: list | None,
    closes_5m: list | None,
    high_1h: float | None = None,
    low_1h: float | None = None,
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # ── Ticker fields ──
    last_price = float(ticker.get("lastPrice", 0))
    fair_price = float(ticker.get("fairPrice", 0))

    # ── Indicators ──
    sma_1m = calculate_sma(closes_1m, 150) if closes_1m else None
    rsi_1m = calculate_rsi(closes_1m, 14)  if closes_1m else None
    sma_5m = calculate_sma(closes_5m, 150) if closes_5m else None
    rsi_5m = calculate_rsi(closes_5m, 14)  if closes_5m else None

    candles_1m = len(closes_1m) if closes_1m else 0
    candles_5m = len(closes_5m) if closes_5m else 0

    # ── Volatility ──
    volatility = None
    if high_1h is not None and low_1h is not None and last_price > 0:
        volatility = calculate_volatility(high_1h, low_1h, last_price)

    def fmt_sma(sma):
        return f"${sma:,.4f}" if sma is not None else "Insufficient data"

    def fmt_rsi(rsi):
        return f"{rsi:.2f}  [{rsi_label(rsi)}]" if rsi is not None else "Insufficient data"

    def fmt_vol(vol):
        if vol is None:
            return "Insufficient data"
        level = "Low" if vol < 0.5 else "Moderate" if vol < 1.5 else "High"
        return f"{vol:.4f}%  [{level}]"

    msg = (
        "<b>\u26a1 GVCrypto \u2014 ETH/USDT Analysis</b>\n"
        + _divider() + "\n"

        # Price
        + "\U0001f4b0 <b>Last Price:</b> <code>${:,.2f}</code>\n".format(last_price)
        + "\u2696\ufe0f <b>Fair Price:</b> <code>${:,.2f}</code>\n".format(fair_price)
        + _divider() + "\n"

        # 1-hour volatility
        + "\U0001f525 <b>1-Hr Volatility</b>\n"
        + "   \U0001f4ca <b>1h High:</b> <code>${:,.2f}</code>\n".format(high_1h if high_1h else 0)
        + "   \U0001f4ca <b>1h Low:</b>  <code>${:,.2f}</code>\n".format(low_1h if low_1h else 0)
        + "   \U0001f300 <b>Volatility:</b> <code>{}</code>\n".format(fmt_vol(volatility))
        + _divider() + "\n"

        # 1-minute timeframe
        + "\U0001f558 <b>1-Min Timeframe</b>  <i>({} candles)</i>\n".format(candles_1m)
        + "   \U0001f4cf <b>SMA-150:</b> <code>{}</code>\n".format(fmt_sma(sma_1m))
        + "   \U0001f4c9 <b>Trend:</b>   <code>{}</code>\n".format(price_vs_ma_label(last_price, sma_1m))
        + "   \U0001f4a1 <b>RSI-14:</b>  <code>{}</code>\n".format(fmt_rsi(rsi_1m))
        + _divider() + "\n"

        # 5-minute timeframe
        + "\U0001f559 <b>5-Min Timeframe</b>  <i>({} candles)</i>\n".format(candles_5m)
        + "   \U0001f4cf <b>SMA-150:</b> <code>{}</code>\n".format(fmt_sma(sma_5m))
        + "   \U0001f4c9 <b>Trend:</b>   <code>{}</code>\n".format(price_vs_ma_label(last_price, sma_5m))
        + "   \U0001f4a1 <b>RSI-14:</b>  <code>{}</code>\n".format(fmt_rsi(rsi_5m))
        + _divider() + "\n"

        + "\U0001f550 <b>Time:</b> <code>{}</code>\n".format(now)
        + "<i>Source: MEXC Futures (ETH_USDT Perpetual)</i>"
    )
    return msg


# ─── Alert Formatting ─────────────────────────────────────────────────────────

def format_alert_message(
    alert_type: str,
    last_price: float,
    rsi_1m: float,
    high_1h: float,
    low_1h: float,
) -> str:
    """
    Format a HIGH ALERT message for Telegram.
    alert_type: 'HIGH' (price broke above 1h high) or 'LOW' (price broke below 1h low)
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if alert_type == "HIGH":
        header  = "\U0001f6a8\U0001f6a8\U0001f6a8 HIGH ALERT \U0001f6a8\U0001f6a8\U0001f6a8"
        title   = "PRICE BREAKING HIGH"
        detail  = (
            "\U0001f4c8 Price has crossed <b>above</b> the 1-Hour High!\n"
            + "   \U0001f539 1h High:    <code>${:,.2f}</code>\n".format(high_1h)
            + "   \U0001f539 Last Price: <code>${:,.2f}</code>  (+${:,.2f})\n".format(
                last_price, last_price - high_1h
            )
        )
    else:
        header  = "\U0001f198\U0001f198\U0001f198 HIGH ALERT \U0001f198\U0001f198\U0001f198"
        title   = "PRICE BREAKING LOW"
        detail  = (
            "\U0001f4c9 Price has crashed <b>below</b> the 1-Hour Low!\n"
            + "   \U0001f538 1h Low:     <code>${:,.2f}</code>\n".format(low_1h)
            + "   \U0001f538 Last Price: <code>${:,.2f}</code>  (-${:,.2f})\n".format(
                last_price, low_1h - last_price
            )
        )

    msg = (
        "<b>{}</b>\n".format(header)
        + "<b>\u26a0\ufe0f  ETH/USDT \u2014 {}</b>\n".format(title)
        + _divider() + "\n"
        + detail
        + _divider() + "\n"
        + "\U0001f4a1 <b>1-Min RSI-14:</b> <code>{:.2f}  [{}]</code>\n".format(rsi_1m, rsi_label(rsi_1m))
        + "\U0001f4b0 <b>Last Price:</b>   <code>${:,.2f}</code>\n".format(last_price)
        + "\U0001f4ca <b>1h High:</b>      <code>${:,.2f}</code>\n".format(high_1h)
        + "\U0001f4ca <b>1h Low:</b>       <code>${:,.2f}</code>\n".format(low_1h)
        + _divider() + "\n"
        + "\U0001f550 <code>{}</code>\n".format(now)
        + "<i>GVCrypto \u2014 MEXC Futures (ETH_USDT Perpetual)</i>"
    )
    return msg


def check_and_send_alerts(
    last_price: float,
    rsi_1m: float | None,
    high_1h: float | None,
    low_1h: float | None,
) -> None:
    """
    Check alert conditions and fire a push notification via ntfy.sh if triggered.
    This is SEPARATE from the regular 5-minute Telegram updates.

    BREAKING HIGH: last_price > high_1h  AND  rsi_1m > 70
    BREAKING LOW:  last_price < low_1h   AND  rsi_1m < 30
    """
    if rsi_1m is None or high_1h is None or low_1h is None:
        log.info("Skipping alert check -- missing RSI or 1h high/low data.")
        return

    if last_price > high_1h and rsi_1m > 70:
        log.warning(
            "ALERT: Price $%.2f broke above 1h High $%.2f  |  RSI-1m: %.2f",
            last_price, high_1h, rsi_1m,
        )
        title = "HIGH ALERT - PRICE BREAKING HIGH"
        body  = (
            "ETH/USDT has crossed ABOVE the 1-Hour High!\n"
            "Last Price : ${:,.2f}\n"
            "1h High    : ${:,.2f}  (+${:,.2f})\n"
            "1m RSI-14  : {:.2f}  [{}]"
        ).format(last_price, high_1h, last_price - high_1h, rsi_1m, rsi_label(rsi_1m))
        sent = send_ntfy_alert(title, body, priority="urgent")
        if sent:
            log.info("HIGH ALERT sent via ntfy.sh.")
        else:
            log.error("Failed to send HIGH ALERT via ntfy.sh.")

    elif last_price < low_1h and rsi_1m < 30:
        log.warning(
            "ALERT: Price $%.2f broke below 1h Low $%.2f  |  RSI-1m: %.2f",
            last_price, low_1h, rsi_1m,
        )
        title = "HIGH ALERT - PRICE BREAKING LOW"
        body  = (
            "ETH/USDT has crashed BELOW the 1-Hour Low!\n"
            "Last Price : ${:,.2f}\n"
            "1h Low     : ${:,.2f}  (-${:,.2f})\n"
            "1m RSI-14  : {:.2f}  [{}]"
        ).format(last_price, low_1h, low_1h - last_price, rsi_1m, rsi_label(rsi_1m))
        sent = send_ntfy_alert(title, body, priority="urgent")
        if sent:
            log.info("LOW ALERT sent via ntfy.sh.")
        else:
            log.error("Failed to send LOW ALERT via ntfy.sh.")

    else:
        log.info(
            "No alert triggered. Price: $%.2f | 1h High: $%.2f | 1h Low: $%.2f | RSI-1m: %.2f",
            last_price, high_1h, low_1h, rsi_1m,
        )


# ─── Main Job ─────────────────────────────────────────────────────────────────

def price_update_job(config: dict) -> None:
    """Fetch ETH price + indicators and dispatch to Telegram."""
    log.info("--- Starting price update job ---")

    # 1. Ticker
    log.info("Fetching ETH ticker...")
    ticker = get_eth_ticker()
    if ticker is None:
        log.warning("Skipping update -- could not retrieve ETH ticker.")
        return
    log.info("ETH last price: $%s", ticker.get("lastPrice"))

    # 2. Candles
    log.info("Fetching 1-min candles (150)...")
    closes_1m = get_candles("ETH_USDT", "Min1", 150)
    log.info("1-min candles received: %d", len(closes_1m) if closes_1m else 0)

    log.info("Fetching 5-min candles (150)...")
    closes_5m = get_candles("ETH_USDT", "Min5", 150)
    log.info("5-min candles received: %d", len(closes_5m) if closes_5m else 0)

    log.info("Fetching 1-hour high/low for volatility...")
    hl_1h = get_1h_high_low("ETH_USDT")
    high_1h, low_1h = hl_1h if hl_1h else (None, None)
    if hl_1h:
        log.info("1h High: $%s  |  1h Low: $%s", high_1h, low_1h)

    # 3. Calculate indicators needed for alert check
    last_price = float(ticker.get("lastPrice", 0))
    rsi_1m     = calculate_rsi(closes_1m, 14) if closes_1m else None

    # 4. Format and send regular update
    message = format_full_message(ticker, closes_1m, closes_5m, high_1h, low_1h)

    token   = config["telegram"]["bot_token"]
    chat_id = config["telegram"]["chat_id"]

    success = send_telegram_message(token, chat_id, message)
    if success:
        log.info("Price + indicator update sent to Telegram (chat_id=%s)", chat_id)
    else:
        log.error("FAILED to send update to Telegram.")

    # 5. Check and fire high/low alerts via ntfy.sh (independent of Telegram)
    log.info("Checking alert conditions...")
    check_and_send_alerts(last_price, rsi_1m, high_1h, low_1h)


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    log.info("=" * 52)
    log.info("  gvcrypto -- ETH Price + TA Alerter starting...")
    log.info("=" * 52)

    try:
        config = load_config()
    except FileNotFoundError:
        log.critical("config.json not found.")
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        log.critical("config.json is malformed: %s", e)
        raise SystemExit(1)

    chat_id = config.get("telegram", {}).get("chat_id", "")
    if not chat_id or chat_id == "YOUR_CHAT_ID_HERE":
        log.critical(
            "chat_id is not set in config.json!\n"
            "  Run: python setup_chat_id.py\n"
            "  Then update config.json with your chat_id."
        )
        raise SystemExit(1)

    interval_minutes = config.get("interval_minutes", 5)
    log.info("Sending ETH updates every %d minute(s).", interval_minutes)
    log.info("Telegram chat_id: %s", chat_id)
    log.info("Indicators: SMA-150 + RSI-14 on 1m and 5m timeframes")

    # Run immediately on startup, then on schedule
    price_update_job(config)

    schedule.every(interval_minutes).minutes.do(price_update_job, config=config)

    log.info("Scheduler running. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time_module.sleep(10)
    except KeyboardInterrupt:
        log.info("gvcrypto stopped by user.")


if __name__ == "__main__":
    main()

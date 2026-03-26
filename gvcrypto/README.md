# gvcrypto 🚀

ETH price alerter — fetches Ethereum futures price from **MEXC** and sends updates to your **Telegram** channel every 5 minutes via **GV_ALGO_BOT**.

---

## Quick Start

### 1. Install dependencies

```bash
cd gvcrypto
pip install -r requirements.txt
```

### 2. Get your Telegram chat_id

First, open Telegram and **send any message to @gvalgo1979bot**.

Then run the setup helper:

```bash
python3 setup_chat_id.py
```

It will print your `chat_id` and offer to auto-update `config.json`.

### 3. Verify config.json

Open `config.json` and confirm it looks like this:

```json
{
  "telegram": {
    "bot_token": "8317896999:AAH-...",
    "chat_id": "123456789"
  },
  "interval_minutes": 5
}
```

> For a **Telegram channel**, add the bot as an admin and use the channel's numeric ID (e.g. `-1001234567890`) or `@channelname`.

### 4. Run the app

```bash
python3 main.py
```

The app will:
- Send one ETH price update immediately on startup
- Continue sending updates every 5 minutes
- Log all activity to `gvcrypto.log`

---

## Configuration

| Key | Description | Default |
|-----|-------------|---------|
| `telegram.bot_token` | Your Telegram bot token | pre-filled |
| `telegram.chat_id` | Target chat or channel ID | **must set** |
| `interval_minutes` | Update frequency in minutes | `5` |

---

## Sample Message

```
⚡ GVCrypto — ETH Price Update
────────────────────────────
💰 Last Price:  $3,241.50
📊 Index Price: $3,240.88
⚖️ Fair Price:  $3,241.12
────────────────────────────
🟢 24h Change: +2.35%
📈 24h High:   $3,310.00
📉 24h Low:    $3,180.00
📦 24h Volume: 152,430 ETH
────────────────────────────
💸 Funding Rate: 0.0100%
🕐 Time: 2026-03-23 10:30:00 UTC
────────────────────────────
Source: MEXC Futures (ETH_USDT Perpetual)
```

---

## Run as a background service (optional)

**Linux/macOS:**
```bash
nohup python3 main.py &> gvcrypto.log &
```

**Windows (PowerShell):**
```powershell
Start-Process python -ArgumentList "main.py" -WindowStyle Hidden
```

---

## Data Source

Prices are fetched from the **MEXC Futures API**:
- Endpoint: `GET https://contract.mexc.com/api/v1/contract/ticker?symbol=ETH_USDT`
- Docs: https://www.mexc.com/api-docs/futures/market-endpoints

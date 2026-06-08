# Binance Futures Testnet Trading Bot

A clean, production-structured Python CLI for placing orders on the **Binance USDT-M Futures Testnet**.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package marker
│   ├── client.py            # Binance REST client (signing, HTTP, error handling)
│   ├── orders.py            # Order orchestration & response formatting
│   ├── validators.py        # Input validation (symbol, side, type, qty, price)
│   └── logging_config.py    # Structured logging setup (file + console)
├── cli.py                   # CLI entry point (argparse)
├── logs/                    # Auto-created; stores daily rotating log files
│   ├── market_order_sample.log
│   └── limit_order_sample.log
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Prerequisites

- Python 3.9+
- A [Binance Futures Testnet](https://testnet.binancefuture.com) account with API credentials

### 2. Clone / unzip the project

```bash
cd trading_bot
```

### 3. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Set your API credentials

**Option A — environment variables (recommended):**

```bash
# Linux / macOS
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"

# Windows (PowerShell)
$env:BINANCE_API_KEY = "your_testnet_api_key"
$env:BINANCE_API_SECRET = "your_testnet_api_secret"
```

**Option B — pass inline (not recommended for shared terminals):**

```bash
python cli.py --api-key YOUR_KEY --api-secret YOUR_SECRET ...
```

---

## How to Run

### Market BUY order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Market SELL order

```bash
python cli.py --symbol ETHUSDT --side SELL --type MARKET --quantity 0.01
```

### Limit SELL order

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 70000
```

### Limit BUY order

```bash
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 60000
```

### Stop-Market BUY (bonus order type)

```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --stop-price 65000
```

### Enable verbose/debug console output

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --verbose
```

---

## Sample Output

```
────────────────────────────────────────────────────
  ORDER REQUEST SUMMARY
────────────────────────────────────────────────────
  Symbol         : BTCUSDT
  Side           : BUY
  Type           : MARKET
  Quantity       : 0.001
────────────────────────────────────────────────────

────────────────────────────────────────────────────
  ORDER RESPONSE
────────────────────────────────────────────────────
  Order ID       : 4085973
  Symbol         : BTCUSDT
  Side           : BUY
  Type           : MARKET
  Status         : FILLED
  Orig Quantity  : 0.001
  Executed Qty   : 0.001
  Avg Fill Price : 67423.10
  Limit Price    : N/A
  Time-in-Force  : GTC
────────────────────────────────────────────────────

✅  Order FILLED successfully!
```

---

## Logging

Log files are written to `./logs/trading_bot_YYYYMMDD.log` automatically.

- **File handler**: captures DEBUG and above (full request/response details, signatures excluded)
- **Console handler**: WARNING and above by default; use `--verbose` for DEBUG on console

Sample log files for a MARKET and LIMIT order are included in `logs/`.

---

## Error Handling

| Scenario | Exit Code | Message prefix |
|---|---|---|
| Invalid input (symbol, qty, price, etc.) | 2 | `[VALIDATION ERROR]` |
| Binance API error (wrong key, bad params) | 3 | `[API ERROR]` |
| Network / timeout | 4 | `[NETWORK ERROR]` |
| Unexpected exception | 99 | `[UNEXPECTED ERROR]` |

---

## Assumptions

1. All orders are placed against the **USDT-M Futures Testnet** (`https://testnet.binancefuture.com`).
2. LIMIT orders default to `timeInForce=GTC`. This is the standard and sufficient for testnet evaluation.
3. Quantity precision is passed as-is; if Binance rejects it due to step-size rules you will see an `[API ERROR]` with code `-1111` — adjust your quantity accordingly (e.g. use `0.001` not `0.0015` for BTC).
4. No position-side (`BOTH` is implicit) — the testnet defaults to one-way mode.
5. Dependencies are intentionally minimal: only `requests` is required (stdlib only otherwise).

---

## Requirements

```
requests>=2.31.0
```

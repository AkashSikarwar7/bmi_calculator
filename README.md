## Python Trading Bot (SMA Crossover)

A minimal-yet-complete trading bot scaffold featuring:

- Backtesting on CSV OHLCV data
- SMA crossover strategy
- Paper trading broker
- Optional CCXT-powered live broker
- YAML configuration and .env secrets
- Clean CLI with `backtest` and `live` commands

### Quickstart

1) Create and activate a virtual environment, then install requirements:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2) Copy samples and adjust:

```bash
cp config.yaml.sample config.yaml
cp .env.example .env
```

3) Backtest using a CSV file with at least: timestamp,open,high,low,close,volume

```bash
python -m trading_bot.cli backtest --csv path/to/data.csv --fast 20 --slow 50 --cash 10000 --fee 0.0005
```

4) Paper trade live (dry-run by default). Example for Binance spot BTC/USDT on 1m timeframe:

```bash
python -m trading_bot.cli live --exchange binance --symbol BTC/USDT --timeframe 1m --fast 20 --slow 50 --paper
```

5) For real trading, set your API keys in `.env` and config, then pass `--live` explicitly.

### CSV Format

The backtester expects a CSV with columns:

```csv
timestamp,open,high,low,close,volume
2024-01-01T00:00:00Z,42500,42600,42450,42550,10.5
```

`timestamp` must be ISO8601 or epoch milliseconds.

### Disclaimer

This repository is for educational purposes only. Trading involves significant risk. Use at your own risk.


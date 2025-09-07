from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Optional

import click
import pandas as pd

from .config import load_config
from .data import read_csv_ohlcv
from .logger import setup_rich_logger
from .strategy import SmaCrossoverParams, SmaCrossoverStrategy
from .backtester import SmaCrossBacktester
from .broker import PaperBroker, CcxtBroker


@click.group()
@click.option("--config", "config_path", type=click.Path(exists=False), default="config.yaml")
@click.pass_context
def cli(ctx: click.Context, config_path: str):
    cfg = load_config(config_path)
    logger = setup_rich_logger(level=cfg.log_level)
    ctx.obj = {
        "cfg": cfg,
        "logger": logger,
    }


@cli.command()
@click.option("--csv", "csv_path", type=click.Path(exists=True), required=True)
@click.option("--fast", type=int, default=20)
@click.option("--slow", type=int, default=50)
@click.option("--cash", type=float, default=10_000)
@click.option("--fee", type=float, default=0.0005)
@click.pass_context
def backtest(ctx: click.Context, csv_path: str, fast: int, slow: int, cash: float, fee: float):
    logger = ctx.obj["logger"]
    logger.info("Loading CSV data...")
    df = read_csv_ohlcv(csv_path)

    logger.info("Running SMA crossover backtest...")
    strategy = SmaCrossoverStrategy(SmaCrossoverParams(fast_window=fast, slow_window=slow))
    df_signals = strategy.generate_signals(df)
    engine = SmaCrossBacktester(fee=fee, initial_cash=cash)
    result = engine.run(df_signals)

    logger.info(f"Stats: {result.stats}")
    if not result.trades.empty:
        logger.info(f"Trades head:\n{result.trades.head(10)}")


@cli.command()
@click.option("--exchange", "exchange_id", type=str, default=None)
@click.option("--symbol", type=str, required=True)
@click.option("--timeframe", type=str, default="1m")
@click.option("--fast", type=int, default=20)
@click.option("--slow", type=int, default=50)
@click.option("--paper/--live", default=True)
@click.option("--cash", type=float, default=10_000)
@click.option("--fee", type=float, default=0.0005)
@click.option("--limit", type=int, default=200)
@click.pass_context
def live(
    ctx: click.Context,
    exchange_id: Optional[str],
    symbol: str,
    timeframe: str,
    fast: int,
    slow: int,
    paper: bool,
    cash: float,
    fee: float,
    limit: int,
):
    cfg = ctx.obj["cfg"]
    logger = ctx.obj["logger"]

    exchange_id = exchange_id or cfg.broker.get("exchange_id")

    strategy = SmaCrossoverStrategy(SmaCrossoverParams(fast_window=fast, slow_window=slow))

    if paper:
        broker = PaperBroker(fee=fee, initial_cash=cash)
        logger.info("Paper trading mode.")
    else:
        broker = CcxtBroker(
            exchange_id=exchange_id,
            api_key=cfg.broker.get("api_key"),
            api_secret=cfg.broker.get("api_secret"),
            api_password=cfg.broker.get("api_password"),
        )
        logger.info(f"Live broker initialized: {exchange_id}")

    if paper:
        logger.info("Fetching historical candles with CCXT for signal generation...")
        ccxt_broker = CcxtBroker(exchange_id=exchange_id)
        ohlcv = ccxt_broker.fetch_ohlcv(symbol, timeframe, limit=limit)
    else:
        ohlcv = broker.fetch_ohlcv(symbol, timeframe, limit=limit)  # type: ignore[attr-defined]

    import pandas as pd

    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]).astype(
        {"timestamp": "int64", "open": "float64", "high": "float64", "low": "float64", "close": "float64", "volume": "float64"}
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.set_index("timestamp").sort_index()

    df_signals = strategy.generate_signals(df)
    last = df_signals.iloc[-1]
    price = float(last["close"])
    signal = str(last["signal"]).lower()

    if paper:
        if signal == "buy" and broker.cash > 0:  # type: ignore[attr-defined]
            order = broker.buy(price=price, amount_cash=broker.cash)  # type: ignore[attr-defined]
            logger.info(f"Paper BUY: {order}")
        elif signal == "sell" and broker.position_units > 0:  # type: ignore[attr-defined]
            order = broker.sell_all(price=price)  # type: ignore[attr-defined]
            logger.info(f"Paper SELL: {order}")
        logger.info(f"Equity: {broker.equity(price):.2f}")  # type: ignore[attr-defined]
    else:
        # Live mode places market orders with naive sizing (risk: high!).
        # Users should extend this for robust risk management.
        market = symbol.split("/")
        quote_allocation = cfg.broker.get("base_order_size", 0.001)
        if signal == "buy":
            # amount is in base currency units; here we do minimalistic sizing
            broker.create_market_order(symbol, "buy", amount=quote_allocation)  # type: ignore[arg-type]
            logger.info("Submitted live BUY market order")
        elif signal == "sell":
            broker.create_market_order(symbol, "sell", amount=quote_allocation)
            logger.info("Submitted live SELL market order")

    logger.info(f"Latest signal: {signal} at price {price}")


if __name__ == "__main__":
    cli()


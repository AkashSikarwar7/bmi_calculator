from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: pd.DataFrame
    stats: dict


class SmaCrossBacktester:
    def __init__(self, fee: float = 0.0, initial_cash: float = 10_000.0):
        self.fee = float(fee)
        self.initial_cash = float(initial_cash)

    def run(self, df: pd.DataFrame) -> BacktestResult:
        prices = df["close"].copy()
        signals = df["signal"].copy()

        position = 0  # 0 = flat, 1 = long
        cash = self.initial_cash
        units = 0.0
        equity = []
        trade_records = []

        previous_price = None
        for timestamp, price in prices.items():
            signal = signals.loc[timestamp]

            # Close position on sell
            if signal == "sell" and position == 1:
                proceeds = units * price
                fee_cost = proceeds * self.fee
                cash += proceeds - fee_cost
                trade_records.append({
                    "timestamp": timestamp,
                    "side": "sell",
                    "price": price,
                    "units": units,
                    "fee": fee_cost,
                })
                position = 0
                units = 0.0

            # Open long on buy
            if signal == "buy" and position == 0 and cash > 0:
                alloc = cash
                fee_cost = alloc * self.fee
                alloc_after_fee = alloc - fee_cost
                units = alloc_after_fee / price
                cash = 0.0
                trade_records.append({
                    "timestamp": timestamp,
                    "side": "buy",
                    "price": price,
                    "units": units,
                    "fee": fee_cost,
                })
                position = 1

            equity_value = cash + units * price
            equity.append((timestamp, equity_value))
            previous_price = price

        # Close any open position at the end
        if position == 1 and previous_price is not None:
            price = previous_price
            proceeds = units * price
            fee_cost = proceeds * self.fee
            cash += proceeds - fee_cost
            trade_records.append({
                "timestamp": prices.index[-1],
                "side": "sell",
                "price": price,
                "units": units,
                "fee": fee_cost,
            })
            position = 0
            units = 0.0
            equity_value = cash
            equity[-1] = (prices.index[-1], equity_value)

        equity_series = pd.Series(
            data=[v for _, v in equity], index=[t for t, _ in equity], name="equity"
        )
        trades_df = pd.DataFrame(trade_records)

        returns = equity_series.pct_change().fillna(0.0)
        total_return = equity_series.iloc[-1] / equity_series.iloc[0] - 1.0
        sharpe = self._sharpe(returns)

        stats = {
            "initial_cash": self.initial_cash,
            "ending_equity": float(equity_series.iloc[-1]),
            "total_return": float(total_return),
            "num_trades": int(len(trades_df)),
            "sharpe": float(sharpe),
            "fee": self.fee,
        }

        return BacktestResult(equity_curve=equity_series, trades=trades_df, stats=stats)

    @staticmethod
    def _sharpe(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        if returns.std() == 0 or len(returns) < 2:
            return 0.0
        # Daily-ish Sharpe assuming input frequency is uniform; user can rescale
        excess = returns - risk_free_rate
        sharpe = excess.mean() / excess.std()
        return float(sharpe * np.sqrt(252))


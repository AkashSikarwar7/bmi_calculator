from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import ccxt


@dataclass
class Order:
    side: str
    price: float
    amount: float
    fee: float


class PaperBroker:
    def __init__(self, fee: float = 0.0, initial_cash: float = 10_000.0):
        self.fee = float(fee)
        self.cash = float(initial_cash)
        self.position_units = 0.0

    def buy(self, price: float, amount_cash: float) -> Order:
        alloc = min(amount_cash, self.cash)
        fee_cost = alloc * self.fee
        units = (alloc - fee_cost) / price if price > 0 else 0.0
        self.cash -= alloc
        self.position_units += units
        return Order(side="buy", price=float(price), amount=float(units), fee=float(fee_cost))

    def sell_all(self, price: float) -> Order:
        units = self.position_units
        proceeds = units * price
        fee_cost = proceeds * self.fee
        self.cash += proceeds - fee_cost
        self.position_units = 0.0
        return Order(side="sell", price=float(price), amount=float(units), fee=float(fee_cost))

    def equity(self, price: float) -> float:
        return float(self.cash + self.position_units * price)


class CcxtBroker:
    def __init__(
        self,
        exchange_id: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_password: Optional[str] = None,
        enable_rate_limit: bool = True,
        testnet: bool = False,
    ) -> None:
        if not hasattr(ccxt, exchange_id):
            raise ValueError(f"Unknown exchange id: {exchange_id}")
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            "apiKey": api_key or "",
            "secret": api_secret or "",
            "password": api_password or None,
            "enableRateLimit": enable_rate_limit,
            "options": {
                "defaultType": "spot",
            },
        })
        if testnet and hasattr(self.exchange, "set_sandbox_mode"):
            self.exchange.set_sandbox_mode(True)

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 200):
        return self.exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)

    def create_market_order(self, symbol: str, side: str, amount: float):
        return self.exchange.create_order(symbol=symbol, type="market", side=side, amount=amount)


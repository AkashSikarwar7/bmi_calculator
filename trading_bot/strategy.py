from dataclasses import dataclass
from typing import Literal, Optional

import pandas as pd


Signal = Literal["buy", "sell", "hold"]


@dataclass
class SmaCrossoverParams:
    fast_window: int = 20
    slow_window: int = 50


class SmaCrossoverStrategy:
    def __init__(self, params: SmaCrossoverParams):
        if params.fast_window >= params.slow_window:
            raise ValueError("fast_window must be < slow_window")
        self.params = params

    def generate_signals(self, ohlcv: pd.DataFrame) -> pd.DataFrame:
        df = ohlcv.copy()
        if "close" not in df.columns:
            raise ValueError("OHLCV DataFrame must contain 'close' column")
        df["sma_fast"] = df["close"].rolling(self.params.fast_window).mean()
        df["sma_slow"] = df["close"].rolling(self.params.slow_window).mean()
        df["signal"] = "hold"
        df.loc[df["sma_fast"] > df["sma_slow"], "signal"] = "buy"
        df.loc[df["sma_fast"] < df["sma_slow"], "signal"] = "sell"
        return df

    def latest_signal(self, ohlcv: pd.DataFrame) -> Signal:
        df = self.generate_signals(ohlcv)
        last_row = df.iloc[-1]
        return last_row["signal"]  # type: ignore[return-value]


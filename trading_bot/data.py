from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import pandas as pd


def read_csv_ohlcv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normalize timestamp to pandas datetime
    if "timestamp" in df.columns:
        try:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        except Exception:
            # Might be epoch ms
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df = df.set_index("timestamp").sort_index()
    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing columns: {sorted(missing)}")
    return df


def compute_position_pnl(entries: pd.Series, exits: pd.Series, fee: float = 0.0) -> float:
    if entries.empty or exits.empty:
        return 0.0
    gross = (exits - entries).sum()
    cost = fee * (entries.abs().sum() + exits.abs().sum())
    return float(gross - cost)


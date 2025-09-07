import os
from dataclasses import dataclass
from typing import Any, Dict

import yaml
from dotenv import load_dotenv


@dataclass
class AppConfig:
    raw: Dict[str, Any]

    @property
    def log_level(self) -> str:
        return str(self.raw.get("general", {}).get("log_level", "INFO")).upper()

    @property
    def broker(self) -> Dict[str, Any]:
        return dict(self.raw.get("broker", {}))

    @property
    def strategy(self) -> Dict[str, Any]:
        return dict(self.raw.get("strategy", {}))

    @property
    def live(self) -> Dict[str, Any]:
        return dict(self.raw.get("live", {}))


def load_config(config_path: str | None = None) -> AppConfig:
    load_dotenv(override=False)

    path = config_path or os.environ.get("TRADING_BOT_CONFIG", "config.yaml")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Merge env secrets into broker section if available
    broker_section = data.setdefault("broker", {})
    broker_section.setdefault("exchange_id", os.environ.get("EXCHANGE_ID"))
    broker_section.setdefault("api_key", os.environ.get("API_KEY"))
    broker_section.setdefault("api_secret", os.environ.get("API_SECRET"))
    broker_section.setdefault("api_password", os.environ.get("API_PASSWORD"))

    return AppConfig(raw=data)


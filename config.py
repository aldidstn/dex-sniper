import os
from dotenv import load_dotenv

load_dotenv()

# General Bot Settings
FETCH_INTERVAL_SECONDS = int(os.getenv("FETCH_INTERVAL_SECONDS", 30))
PAPER_TRADING_MODE = os.getenv("PAPER_TRADING_MODE", "True").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///memecoins.db")

# Dexscreener API
DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex"
DEX_FILTER_MAX_VOLUME_24H_USD = float(os.getenv("DEX_FILTER_MAX_VOLUME_24H_USD", 1_500_000))
DEX_FILTER_MAX_AGE_DAYS = int(os.getenv("DEX_FILTER_MAX_AGE_DAYS", 2))
DEX_FILTER_MIN_HOLDER_COUNT = int(os.getenv("DEX_FILTER_MIN_HOLDER_COUNT", 10000))

# PumpFun API
PUMPFUN_API_URL = os.getenv("PUMPFUN_API_URL", "https://api.pump.fun/coins")
PUMPFUN_WEBSOCKET_URL = os.getenv("PUMPFUN_WEBSOCKET_URL", "wss://api.pump.fun/socket/websocket")
PUMPFUN_RECONNECT_DELAY = int(os.getenv("PUMPFUN_RECONNECT_DELAY", 5))
PUMPFUN_MAX_RECONNECT_ATTEMPTS = int(os.getenv("PUMPFUN_MAX_RECONNECT_ATTEMPTS", 10))


# Trading Parameters
DEFAULT_SLIPPAGE_BPS = int(os.getenv("DEFAULT_SLIPPAGE_BPS", 100))
MAX_TRADE_SIZE_USD = float(os.getenv("MAX_TRADE_SIZE_USD", 50.0))

# Trend Analyzer Parameters
TREND_EMA_SHORT_PERIOD = int(os.getenv("TREND_EMA_SHORT_PERIOD", 9))
TREND_EMA_LONG_PERIOD = int(os.getenv("TREND_EMA_LONG_PERIOD", 21))
TREND_RSI_PERIOD = int(os.getenv("TREND_RSI_PERIOD", 14))
TREND_BB_PERIOD = int(os.getenv("TREND_BB_PERIOD", 20))
TREND_CANDLE_RESOLUTION_MINUTES = int(os.getenv("TREND_CANDLE_RESOLUTION_MINUTES", 15))
TREND_CANDLE_COUNT = int(os.getenv("TREND_CANDLE_COUNT", 100))

# import os
# from dotenv import load_dotenv

# load_dotenv()

# # General Bot Settings
# FETCH_INTERVAL_SECONDS = int(os.getenv("FETCH_INTERVAL_SECONDS", 30))
# PAPER_TRADING_MODE = os.getenv("PAPER_TRADING_MODE", "True").lower() == "true"
# LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# # Database Configuration
# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///memecoins.db")

# # Dexscreener API
# DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex"
# DEX_FILTER_MAX_VOLUME_24H_USD = float(os.getenv("DEX_FILTER_MAX_VOLUME_24H_USD", 1_500_000))
# DEX_FILTER_MAX_AGE_DAYS = int(os.getenv("DEX_FILTER_MAX_AGE_DAYS", 2))
# DEX_FILTER_MIN_HOLDER_COUNT = int(os.getenv("DEX_FILTER_MIN_HOLDER_COUNT", 10000))

# # PumpFun API
# PUMPFUN_API_URL = os.getenv("PUMPFUN_API_URL", "https://api.pump.fun/coins")
# PUMPFUN_WEBSOCKET_URL = os.getenv("PUMPFUN_WEBSOCKET_URL", "wss://api.pump.fun/socket/websocket")
# PUMPFUN_RECONNECT_DELAY = int(os.getenv("PUMPFUN_RECONNECT_DELAY", 5))
# PUMPFUN_MAX_RECONNECT_ATTEMPTS = int(os.getenv("PUMPFUN_MAX_RECONNECT_ATTEMPTS", 10))


# # Trading Parameters
# DEFAULT_SLIPPAGE_BPS = int(os.getenv("DEFAULT_SLIPPAGE_BPS", 100))
# MAX_TRADE_SIZE_USD = float(os.getenv("MAX_TRADE_SIZE_USD", 50.0))

# # Trend Analyzer Parameters
# TREND_EMA_SHORT_PERIOD = int(os.getenv("TREND_EMA_SHORT_PERIOD", 9))
# TREND_EMA_LONG_PERIOD = int(os.getenv("TREND_EMA_LONG_PERIOD", 21))
# TREND_RSI_PERIOD = int(os.getenv("TREND_RSI_PERIOD", 14))
# TREND_BB_PERIOD = int(os.getenv("TREND_BB_PERIOD", 20))
# TREND_CANDLE_RESOLUTION_MINUTES = int(os.getenv("TREND_CANDLE_RESOLUTION_MINUTES", 15))
# TREND_CANDLE_COUNT = int(os.getenv("TREND_CANDLE_COUNT", 100))

import os
from dotenv import load_dotenv

load_dotenv()

# General Bot Settings
FETCH_INTERVAL_SECONDS = int(os.getenv("FETCH_INTERVAL_SECONDS", 30))
PAPER_TRADING_MODE = os.getenv("PAPER_TRADING_MODE", "True").lower() == "true"

# Moralis API Configuration
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjNmOTFkN2Y3LTljMzUtNDhhZS1hZjc2LWJmODk1ZGQ2YWU2ZiIsIm9yZ0lkIjoiNDUwMTk5IiwidXNlcklkIjoiNDYzMjE1IiwidHlwZUlkIjoiNGQyMjRlNzctMDdhNy00MGMzLTljYWQtNDE4NzZjZjkwY2E4IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NDg2ODY5MzYsImV4cCI6NDkwNDQ0NjkzNn0.JIqzBKmEzu2WN07EUF9KSLuHd_H4ZEo80uVsXjyHg28")
MORALIS_BASE_URL = "https://solana-gateway.moralis.io"
PUMPFUN_NEW_TOKENS_ENDPOINT = f"{MORALIS_BASE_URL}/token/mainnet/exchange/pumpfun/new"

# Request Configuration
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 15))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 2))

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///memecoins.db")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


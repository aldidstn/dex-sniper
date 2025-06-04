# import os
# from dataclasses import dataclass
# from typing import Optional

# # Database Configuration
# DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///memecoins.db')

# @dataclass
# class Config:
#     # API Configuration
#     moralis_api_key: Optional[str] = None
#     api_timeout: int = 30
#     max_retries: int = 3
    
#     db_path: str = "memecoins.db"

#     # Logging Configuration
#     log_level: str = "INFO"
#     log_file: str = "dex_sniper.log"
    
#     # Sniper Configuration
#     min_market_cap: float = 1000.0
#     max_market_cap: float = 100000.0
#     check_interval: int = 10  # seconds
    
#     # Trading Configuration
#     max_concurrent_tokens: int = 5
#     default_buy_amount: float = 0.1  # SOL
    
#     def __post_init__(self):
#         # Try to load API key from environment if not provided
#         if not self.moralis_api_key:
#             self.moralis_api_key = os.getenv('MORALIS_API_KEY')
    
#     @classmethod
#     def from_env(cls):
#         """Create config from environment variables"""
#         return cls(
#             moralis_api_key=os.getenv('MORALIS_API_KEY'),
#             api_timeout=int(os.getenv('API_TIMEOUT', '30')),
#             max_retries=int(os.getenv('MAX_RETRIES', '3')),
#             db_path=os.getenv('DB_PATH', 'memecoins.db'),
#             log_level=os.getenv('LOG_LEVEL', 'INFO'),
#             log_file=os.getenv('LOG_FILE', 'dex_sniper.log'),
#             min_market_cap=float(os.getenv('MIN_MARKET_CAP', '1000.0')),
#             max_market_cap=float(os.getenv('MAX_MARKET_CAP', '100000.0')),
#             check_interval=int(os.getenv('CHECK_INTERVAL', '10')),
#             max_concurrent_tokens=int(os.getenv('MAX_CONCURRENT_TOKENS', '5')),
#             default_buy_amount=float(os.getenv('DEFAULT_BUY_AMOUNT', '0.1'))
#         )

import os
from dataclasses import dataclass
from typing import Optional

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///memecoins.db')

@dataclass
class Config:
    # Updated API Configuration for RapidAPI
    rapidapi_key: Optional[str] = "47f8a0ad6cmsh0931d63e060bd42p167f5djsn78b3278e46b0"
    api_timeout: int = 30
    max_retries: int = 3
    
    # Keep legacy support
    moralis_api_key: Optional[str] = None  # Deprecated
    
    db_path: str = "memecoins.db"

    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "dex_sniper.log"
    
    # Sniper Configuration
    min_liquidity: float = 1000.0
    max_market_cap: float = 100000.0
    
    # API endpoint configuration
    pumpfun_api_url: str = "https://pumpfun-scraper-api.p.rapidapi.com/get_latest_token"
    
    def __post_init__(self):
        # Ensure backward compatibility
        if self.moralis_api_key and not self.rapidapi_key:
            self.rapidapi_key = self.moralis_api_key

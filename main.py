import logging
import time
import sys
import signal
from typing import Optional
from config import Config
from database import Database
from pumpfun_fetcher import PumpFunFetcher

# Configure logging
def setup_logging(config: Config):
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

class DexSniper:
    def __init__(self, config: Config):
        self.config = config
        self.db = Database(config.db_path)
        self.fetcher = PumpFunFetcher(
            api_key=config.moralis_api_key,
            timeout=config.api_timeout,
            max_retries=config.max_retries
        )
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logging.info(f"Received signal {signum}. Shutting down gracefully...")
        self.running = False
    
    def setup_api_key(self, api_key: str) -> bool:
        """
        Setup or update the API key
        
        Args:
            api_key: The Moralis API key
            
        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            self.fetcher.update_api_key(api_key)
            return self.fetcher.health_check()
        except Exception as e:
            logging.error(f"Failed to setup API key: {str(e)}")
            return False
    
    def initialize(self) -> bool:
        """Initialize the sniper system"""
        try:
            logging.info("Initializing database...")
            self.db.initialize()
            
            logging.info("Performing API health check...")
            if not self.fetcher.health_check():
                if not self.config.moralis_api_key:
                    logging.error("No API key configured. Please set MORALIS_API_KEY environment variable or provide it via setup_api_key() method.")
                else:
                    logging.error("API health check failed. Please verify your API key is valid.")
                return False
            
            logging.info("Initialization complete")
            return True
            
        except Exception as e:
            logging.error(f"Initialization failed: {str(e)}")
            return False
    
    def process_new_tokens(self):
        """Process newly discovered tokens"""
        try:
            tokens = self.fetcher.get_new_tokens()
            if not tokens:
                logging.warning("No tokens retrieved from API")
                return
            
            for token in tokens:
                try:
                    # Extract token information
                    token_address = token.get('address', '')
                    name = token.get('name', 'Unknown')
                    symbol = token.get('symbol', 'UNK')
                    market_cap = token.get('market_cap', 0)
                    
                    if not token_address:
                        logging.warning("Token missing address, skipping")
                        continue
                    
                    # Apply filters
                    if market_cap < self.config.min_market_cap or market_cap > self.config.max_market_cap:
                        logging.debug(f"Token {symbol} filtered out by market cap: {market_cap}")
                        continue
                    
                    # Check if we already processed this token
                    if self.db.token_exists(token_address):
                        logging.debug(f"Token {symbol} already processed")
                        continue
                    
                    # Store token in database
                    self.db.add_token(token)
                    logging.info(f"New token discovered: {name} ({symbol}) - Market Cap: {market_cap}")
                    
                    # Here you would add your sniping logic
                    # self.execute_snipe(token)
                    
                except Exception as e:
                    logging.error(f"Error processing token: {str(e)}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error in process_new_tokens: {str(e)}")
    
    def run(self):
        """Main execution loop"""
        if not self.initialize():
            logging.error("Failed to initialize. Exiting.")
            return
        
        self.running = True
        logging.info("Starting dex sniper main loop...")
        
        try:
            while self.running:
                try:
                    self.process_new_tokens()
                    time.sleep(self.config.check_interval)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logging.error(f"Error in main loop: {str(e)}")
                    time.sleep(5)  # Brief pause before retrying
                    
        except Exception as e:
            logging.error(f"Fatal error in main loop: {str(e)}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        logging.info("Cleaning up resources...")
        try:
            self.fetcher.close()
            self.db.close()
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")

def main():
    # Load configuration
    config = Config.from_env()
    
    # Setup logging
    setup_logging(config)
    
    # Create and run sniper
    sniper = DexSniper(config)
    
    # If no API key is configured, prompt user or exit
    if not config.moralis_api_key:
        print("No Moralis API key found.")
        print("Please set the MORALIS_API_KEY environment variable or")
        print("call sniper.setup_api_key('your_api_key_here') before running.")
        return
    
    sniper.run()

if __name__ == "__main__":
    main()

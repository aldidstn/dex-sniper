import logging
import time
import signal
import sys
from database import init_db, SessionLocal
from pumpfun_fetcher import PumpFunFetcher, MoralisAPIError
from config import FETCH_INTERVAL_SECONDS, LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dex_sniper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class DexSniper:
    """Main application class for DEX sniping operations"""
    
    def __init__(self):
        self.running = False
        self.pumpfun_fetcher = PumpFunFetcher()
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        
    def start(self):
        """Start the main sniping loop"""
        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        
        # Perform health check
        logger.info("Performing API health check...")
        if not self.pumpfun_fetcher.health_check():
            logger.error("API health check failed. Exiting.")
            return
        
        self.running = True
        logger.info(f"Starting DEX sniper with {FETCH_INTERVAL_SECONDS}s intervals")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Fetch and process new tokens
                processed_count = self.pumpfun_fetcher.fetch_and_process_new_tokens(limit=50)
                
                execution_time = time.time() - start_time
                logger.info(f"Cycle completed: {processed_count} tokens processed in {execution_time:.2f}s")
                
                # Sleep for remaining interval time
                remaining_time = max(0, FETCH_INTERVAL_SECONDS - execution_time)
                if remaining_time > 0:
                    time.sleep(remaining_time)
                    
            except MoralisAPIError as e:
                logger.error(f"Moralis API error: {e}")
                time.sleep(60)  # Wait longer on API errors
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
                time.sleep(30)
        
        logger.info("DEX sniper stopped")

def main():
    """Main entry point"""
    snieper = DexSniper()
    snieper.start()

if __name__ == "__main__":
    main()

# import logging
# import time
# from database import init_db, SessionLocal
# from dexscreener_fetcher import fetch_dexscreener_pairs, store_tokens_from_dexscreener
# from pumpfun_fetcher import _process_pumpfun_coin_data
# from config import FETCH_INTERVAL_SECONDS, LOG_LEVEL

# # Configure logging
# logging.basicConfig(
#     level=getattr(logging, LOG_LEVEL),
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# def main():
#     """Main bot execution function"""
#     logger.info("Starting Memecoin Trading Bot...")
    
#     # Initialize database
#     init_db()
    
#     # Main loop
#     while True:
#         try:
#             with SessionLocal() as db:
#                 # Fetch DexScreener data
#                 logger.info("Fetching DexScreener pairs...")
#                 pairs = fetch_dexscreener_pairs(chain_id="solana")
                
#                 if pairs:
#                     new_count, updated_count = store_tokens_from_dexscreener(db, pairs)
#                     logger.info(f"DexScreener sync complete: {new_count} new, {updated_count} updated")
                
#                 # Add PumpFun fetching logic here when needed
                
#         except Exception as e:
#             logger.error(f"Error in main loop: {e}", exc_info=True)
        
#         logger.info(f"Sleeping for {FETCH_INTERVAL_SECONDS} seconds...")
#         time.sleep(FETCH_INTERVAL_SECONDS)

# if __name__ == "__main__":
#     main()
import logging
import time
from database import init_db, SessionLocal
from dexscreener_fetcher import fetch_trending_pairs, fetch_token_pairs, store_tokens_from_dexscreener
from pumpfun_fetcher import PumpFunFetcher
from config import FETCH_INTERVAL_SECONDS, LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main bot execution function"""
    logger.info("Starting Memecoin Trading Bot...")
    
    # Initialize database
    init_db()
    
    # Initialize PumpFun fetcher
    pumpfun_fetcher = PumpFunFetcher()
    
    # Start PumpFun WebSocket in background (optional - for real-time updates)
    try:
        pumpfun_fetcher.start_websocket_thread()
        logger.info("PumpFun WebSocket started for real-time updates")
    except Exception as e:
        logger.warning(f"Could not start PumpFun WebSocket: {e}")
    
    # Main loop
    while True:
        try:
            with SessionLocal() as db:
                # === DEXSCREENER FETCHING ===
                logger.info("Fetching trending pairs from DexScreener...")
                pairs = fetch_trending_pairs(chain_id="solana", limit=20)
                
                # Fallback to popular tokens if trending doesn't work
                if not pairs:
                    logger.info("No trending pairs found, trying popular Solana tokens...")
                    popular_tokens = [
                        "So11111111111111111111111111111111111111112",  # SOL
                        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                        "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",  # Bonk
                    ]
                    
                    for token_address in popular_tokens:
                        token_pairs = fetch_token_pairs(token_address, "solana")
                        pairs.extend(token_pairs)
                        if len(pairs) >= 10:  # Limit to avoid too much data
                            break
                
                if pairs:
                    new_count, updated_count = store_tokens_from_dexscreener(db, pairs)
                    logger.info(f"DexScreener sync complete: {new_count} new, {updated_count} updated")
                else:
                    logger.warning("No pairs data retrieved from DexScreener")
                
                # === PUMPFUN FETCHING ===
                logger.info("Fetching latest coins from PumpFun...")
                
                # Try trending first, then fallback to latest
                pumpfun_coins = pumpfun_fetcher.fetch_trending_coins(limit=30)
                if not pumpfun_coins:
                    logger.info("No trending PumpFun coins, fetching latest...")
                    pumpfun_coins = pumpfun_fetcher.fetch_latest_coins(limit=50)
                
                if pumpfun_coins:
                    new_pf_count, updated_pf_count = store_pumpfun_coins(db, pumpfun_coins)
                    logger.info(f"PumpFun sync complete: {new_pf_count} new, {updated_pf_count} updated")
                else:
                    logger.warning("No coins data retrieved from PumpFun")
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal...")
            pumpfun_fetcher.stop_websocket()
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        
        logger.info(f"Sleeping for {FETCH_INTERVAL_SECONDS} seconds...")
        time.sleep(FETCH_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
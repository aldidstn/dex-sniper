# import requests
# import websocket
# import json
# import logging
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import IntegrityError
# from database import Token
# from datetime import datetime, timezone

# logger_pumpfun = logging.getLogger(__name__ + ".pumpfun_fetcher")

# def _process_pumpfun_coin_data(db: Session, coin_data: dict):
#     """Processes and stores a new coin from Pump.fun data."""
#     try:
#         mint_address = coin_data.get('mint')
#         if not mint_address:
#             logger_pumpfun.warning(f"Pump.fun coin data missing mint address: {coin_data.get('name')}")
#             return
#         existing_token = db.query(Token).filter(Token.pumpfun_mint_address == mint_address).first()
#         if existing_token:
#             existing_token.pumpfun_metadata = coin_data
#         else:
#             new_token = Token(
#                 pumpfun_mint_address=mint_address,
#                 is_pumpfun_launch=True,
#                 pumpfun_metadata=coin_data,
#                 chain_id="solana"
#             )
#             db.add(new_token)
#         db.commit()
#     except IntegrityError as e:
#         db.rollback()
#         logger_pumpfun.error(f"Integrity error processing PumpFun coin {mint_address}: {e}")
#     except Exception as e:
#         db.rollback()
#         logger_pumpfun.error(f"Error processing PumpFun coin {mint_address}: {e}", exc_info=True)

import requests
import websocket
import json
import logging
import threading
import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import Token, SessionLocal
from datetime import datetime, timezone
from config import PUMPFUN_API_URL, PUMPFUN_WEBSOCKET_URL

logger_pumpfun = logging.getLogger(__name__ + ".pumpfun_fetcher")

class PumpFunFetcher:
    def __init__(self):
        self.ws = None
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
    def fetch_latest_coins(self, limit: int = 50, offset: int = 0):
        """Fetch latest coins from PumpFun REST API"""
        try:
            params = {
                'offset': offset,
                'limit': limit,
                'sort': 'created_timestamp',
                'order': 'DESC',
                'includeNsfw': 'false'
            }
            
            logger_pumpfun.info(f"Fetching latest PumpFun coins: limit={limit}, offset={offset}")
            response = requests.get(
                PUMPFUN_API_URL,
                params=params,
                timeout=15,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json'
                }
            )
            response.raise_for_status()
            
            data = response.json()
            coins = []
            
            if isinstance(data, list):
                coins = data
            elif isinstance(data, dict) and 'coins' in data:
                coins = data['coins']
            elif isinstance(data, dict) and 'data' in data:
                coins = data['data']
            
            logger_pumpfun.info(f"Fetched {len(coins)} coins from PumpFun API")
            return coins
            
        except requests.RequestException as e:
            logger_pumpfun.error(f"Error fetching from PumpFun API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger_pumpfun.error(f"PumpFun API Response: Status {e.response.status_code}, Body: {e.response.text}")
            return []
        except Exception as e:
            logger_pumpfun.error(f"Unexpected error in PumpFun fetcher: {e}", exc_info=True)
            return []
    
    def fetch_trending_coins(self, limit: int = 20):
        """Fetch trending coins from PumpFun"""
        try:
            # Try the trending endpoint
            trending_url = f"{PUMPFUN_API_URL}/trending"
            params = {'limit': limit}
            
            logger_pumpfun.info(f"Fetching trending PumpFun coins from: {trending_url}")
            response = requests.get(
                trending_url,
                params=params,
                timeout=15,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json'
                }
            )
            
            if response.status_code == 404:
                # Fallback to latest coins if trending endpoint doesn't exist
                logger_pumpfun.info("Trending endpoint not found, falling back to latest coins")
                return self.fetch_latest_coins(limit=limit)
            
            response.raise_for_status()
            data = response.json()
            
            coins = []
            if isinstance(data, list):
                coins = data
            elif isinstance(data, dict) and 'coins' in data:
                coins = data['coins']
            elif isinstance(data, dict) and 'data' in data:
                coins = data['data']
            
            logger_pumpfun.info(f"Fetched {len(coins)} trending coins from PumpFun")
            return coins
            
        except Exception as e:
            logger_pumpfun.error(f"Error fetching trending coins, trying latest: {e}")
            # Fallback to latest coins
            return self.fetch_latest_coins(limit=limit)
    
    def fetch_coin_by_address(self, mint_address: str):
        """Fetch specific coin data by mint address"""
        try:
            url = f"{PUMPFUN_API_URL}/{mint_address}"
            logger_pumpfun.info(f"Fetching PumpFun coin: {mint_address}")
            
            response = requests.get(
                url,
                timeout=15,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json'
                }
            )
            response.raise_for_status()
            
            coin_data = response.json()
            logger_pumpfun.info(f"Successfully fetched coin data for {mint_address}")
            return coin_data
            
        except Exception as e:
            logger_pumpfun.error(f"Error fetching coin {mint_address}: {e}")
            return None
    
    def on_websocket_message(self, ws, message):
        """Handle WebSocket messages"""
        try:
            data = json.loads(message)
            logger_pumpfun.debug(f"WebSocket message received: {data}")
            
            # Handle different message types
            if isinstance(data, list) and len(data) >= 2:
                # Phoenix WebSocket format: [null, null, "topic", "event", payload]
                if len(data) >= 5:
                    topic = data[2]
                    event = data[3]
                    payload = data[4]
                    
                    if event == "new_coin" and isinstance(payload, dict):
                        logger_pumpfun.info(f"New coin detected: {payload.get('name', 'Unknown')}")
                        with SessionLocal() as db:
                            self._process_pumpfun_coin_data(db, payload)
            
            elif isinstance(data, dict):
                # Direct coin data
                if data.get('mint') or data.get('address'):
                    logger_pumpfun.info(f"Coin update: {data.get('name', 'Unknown')}")
                    with SessionLocal() as db:
                        self._process_pumpfun_coin_data(db, data)
                        
        except json.JSONDecodeError:
            logger_pumpfun.warning(f"Invalid JSON message: {message}")
        except Exception as e:
            logger_pumpfun.error(f"Error processing WebSocket message: {e}", exc_info=True)
    
    def on_websocket_error(self, ws, error):
        """Handle WebSocket errors"""
        logger_pumpfun.error(f"WebSocket error: {error}")
        
    def on_websocket_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger_pumpfun.info(f"WebSocket closed: {close_status_code} - {close_msg}")
        if self.running and self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logger_pumpfun.info(f"Attempting to reconnect... (attempt {self.reconnect_attempts})")
            time.sleep(5)
            self.start_websocket()
    
    def on_websocket_open(self, ws):
        """Handle WebSocket open"""
        logger_pumpfun.info("PumpFun WebSocket connected")
        self.reconnect_attempts = 0
        
        # Subscribe to new coins channel
        try:
            # Phoenix WebSocket join message format
            join_message = [
                None,  # join_ref
                None,  # message_ref  
                "coins:new",  # topic
                "phx_join",  # event
                {}  # payload
            ]
            ws.send(json.dumps(join_message))
            logger_pumpfun.info("Subscribed to new coins channel")
        except Exception as e:
            logger_pumpfun.error(f"Error subscribing to channel: {e}")
    
    def start_websocket(self):
        """Start WebSocket connection"""
        try:
            logger_pumpfun.info("Starting PumpFun WebSocket connection...")
            self.ws = websocket.WebSocketApp(
                PUMPFUN_WEBSOCKET_URL,
                on_open=self.on_websocket_open,
                on_message=self.on_websocket_message,
                on_error=self.on_websocket_error,
                on_close=self.on_websocket_close
            )
            self.running = True
            self.ws.run_forever()
        except Exception as e:
            logger_pumpfun.error(f"Error starting WebSocket: {e}")
    
    def start_websocket_thread(self):
        """Start WebSocket in a separate thread"""
        ws_thread = threading.Thread(target=self.start_websocket, daemon=True)
        ws_thread.start()
        logger_pumpfun.info("PumpFun WebSocket thread started")
        return ws_thread
    
    def stop_websocket(self):
        """Stop WebSocket connection"""
        self.running = False
        if self.ws:
            self.ws.close()
            logger_pumpfun.info("PumpFun WebSocket stopped")
    
    def _process_pumpfun_coin_data(self, db: Session, coin_data: dict):
        """Process and store PumpFun coin data"""
        try:
            mint_address = coin_data.get('mint') or coin_data.get('address')
            if not mint_address:
                logger_pumpfun.warning(f"PumpFun coin data missing mint address: {coin_data.get('name', 'Unknown')}")
                return False
            
            existing_token = db.query(Token).filter(Token.pumpfun_mint_address == mint_address).first()
            
            # Extract common fields
            common_data = {
                'pumpfun_mint_address': mint_address,
                'is_pumpfun_launch': True,
                'pumpfun_metadata': coin_data,
                'chain_id': 'solana',
                'base_token_address': mint_address,
                'base_token_name': coin_data.get('name'),
                'base_token_symbol': coin_data.get('symbol'),
                'price_usd': float(coin_data.get('usd_market_cap', 0)) / float(coin_data.get('total_supply', 1)) if coin_data.get('usd_market_cap') and coin_data.get('total_supply') else None,
                'market_cap_usd': float(coin_data.get('usd_market_cap')) if coin_data.get('usd_market_cap') else None,
                'volume_h24': float(coin_data.get('volume_24h')) if coin_data.get('volume_24h') else None,
                'liquidity_usd': float(coin_data.get('liquidity')) if coin_data.get('liquidity') else None,
                'market_state': coin_data.get('complete', False) and 'GRADUATED' or 'ACTIVE',
                'last_updated_at': datetime.now(timezone.utc)
            }
            
            # Handle creation timestamp
            if coin_data.get('created_timestamp'):
                try:
                    created_ts = int(coin_data['created_timestamp'])
                    if created_ts > 1000000000000:  # milliseconds
                        created_ts = created_ts / 1000
                    common_data['pair_created_at'] = datetime.fromtimestamp(created_ts, tz=timezone.utc)
                except Exception as ts_e:
                    logger_pumpfun.warning(f"Could not parse created_timestamp {coin_data.get('created_timestamp')}: {ts_e}")
            
            if existing_token:
                # Update existing token
                for key, value in common_data.items():
                    if value is not None:  # Only update non-None values
                        setattr(existing_token, key, value)
                logger_pumpfun.debug(f"Updated existing PumpFun token: {mint_address}")
            else:
                # Create new token
                new_token = Token(
                    **common_data,
                    first_seen_at=datetime.now(timezone.utc)
                )
                db.add(new_token)
                logger_pumpfun.info(f"Added new PumpFun token: {coin_data.get('name', 'Unknown')} ({mint_address})")
            
            db.commit()
            return True
            
        except IntegrityError as e:
            db.rollback()
            logger_pumpfun.error(f"Integrity error processing PumpFun coin {mint_address}: {e}")
            return False
        except Exception as e:
            db.rollback()
            logger_pumpfun.error(f"Error processing PumpFun coin {mint_address}: {e}", exc_info=True)
            return False

def store_pumpfun_coins(db: Session, coins_data: list):
    """Store multiple PumpFun coins in database"""
    if not coins_data:
        logger_pumpfun.info("No PumpFun coins data to store.")
        return 0, 0
    
    fetcher = PumpFunFetcher()
    new_count = 0
    updated_count = 0
    
    for coin_data in coins_data:
        if not coin_data or not isinstance(coin_data, dict):
            continue
            
        # Check if token already exists
        mint_address = coin_data.get('mint') or coin_data.get('address')
        if not mint_address:
            continue
            
        existing_token = db.query(Token).filter(Token.pumpfun_mint_address == mint_address).first()
        
        if fetcher._process_pumpfun_coin_data(db, coin_data):
            if existing_token:
                updated_count += 1
            else:
                new_count += 1
    
    logger_pumpfun.info(f"PumpFun sync: Stored {new_count} new tokens, updated {updated_count} tokens.")
    return new_count, updated_count

# Legacy function for backward compatibility
def _process_pumpfun_coin_data(db: Session, coin_data: dict):
    """Legacy function - use PumpFunFetcher class instead"""
    fetcher = PumpFunFetcher()
    return fetcher._process_pumpfun_coin_data(db, coin_data)
import requests
import json
import logging
import time
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import Token, SessionLocal
from datetime import datetime, timezone
from config import (
    MORALIS_API_KEY, 
    PUMPFUN_NEW_TOKENS_ENDPOINT,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY
)

logger = logging.getLogger(__name__)

class MoralisAPIError(Exception):
    """Custom exception for Moralis API errors"""
    pass

class PumpFunFetcher:
    """
    Enhanced PumpFun token fetcher using Moralis API
    Provides robust error handling, retry logic, and rate limiting
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'X-API-Key': MORALIS_API_KEY,
            'User-Agent': 'DEX-Sniper/1.0'
        })
        self.last_request_time = 0
        self.rate_limit_delay = 1  # Minimum delay between requests
        
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a rate-limited request to the Moralis API with retry logic
        """
        # Implement rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        for attempt in range(MAX_RETRIES):
            try:
                self.last_request_time = time.time()
                
                logger.info(f"Making request to {url} (attempt {attempt + 1}/{MAX_RETRIES})")
                response = self.session.get(
                    url, 
                    params=params or {}, 
                    timeout=REQUEST_TIMEOUT
                )
                
                # Handle different HTTP status codes
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise MoralisAPIError("Invalid API key or authentication failed")
                elif response.status_code == 429:
                    # Rate limited - exponential backoff
                    wait_time = (2 ** attempt) * RETRY_DELAY
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 404:
                    logger.warning(f"Endpoint not found: {url}")
                    return {}
                else:
                    response.raise_for_status()
                    
            except requests.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == MAX_RETRIES - 1:
                    raise MoralisAPIError(f"Failed to fetch data after {MAX_RETRIES} attempts: {e}")
                time.sleep(RETRY_DELAY * (attempt + 1))
                
        return {}
    
    def fetch_new_pumpfun_tokens(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch new PumpFun tokens from Moralis API
        """
        try:
            params = {
                'limit': min(limit, 100),  # Respect API limits
            }
            
            logger.info(f"Fetching new PumpFun tokens with limit: {limit}")
            data = self._make_request(PUMPFUN_NEW_TOKENS_ENDPOINT, params)
            
            # Handle different response formats
            if isinstance(data, list):
                tokens = data
            elif isinstance(data, dict):
                # Try common response format keys
                tokens = data.get('data', data.get('tokens', data.get('result', [])))
            else:
                tokens = []
            
            logger.info(f"Successfully fetched {len(tokens)} new tokens")
            return tokens
            
        except MoralisAPIError as e:
            logger.error(f"Moralis API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching new tokens: {e}", exc_info=True)
            return []
    
    def process_and_store_tokens(self, tokens: List[Dict[str, Any]]) -> int:
        """
        Process and store tokens in database
        Returns number of successfully processed tokens
        """
        processed_count = 0
        
        with SessionLocal() as db:
            for token_data in tokens:
                try:
                    if self._process_single_token(db, token_data):
                        processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing token: {e}", exc_info=True)
                    continue
        
        logger.info(f"Successfully processed {processed_count}/{len(tokens)} tokens")
        return processed_count
    
    def _process_single_token(self, db: Session, token_data: Dict[str, Any]) -> bool:
        """
        Process and store a single token
        """
        try:
            # Extract token identifier (adapt based on actual API response format)
            mint_address = token_data.get('mint_address') or token_data.get('address') or token_data.get('mint')
            
            if not mint_address:
                logger.warning(f"Token data missing mint address: {token_data}")
                return False
            
            # Check if token already exists
            existing_token = db.query(Token).filter(
                Token.pumpfun_mint_address == mint_address
            ).first()
            
            if existing_token:
                # Update existing token
                existing_token.pumpfun_metadata = token_data
                existing_token.last_updated = datetime.now(timezone.utc)
                logger.debug(f"Updated existing token: {mint_address}")
            else:
                # Create new token
                new_token = Token(
                    pumpfun_mint_address=mint_address,
                    is_pumpfun_launch=True,
                    pumpfun_metadata=token_data,
                    chain_id="solana",
                    created_at=datetime.now(timezone.utc),
                    last_updated=datetime.now(timezone.utc)
                )
                db.add(new_token)
                logger.info(f"Added new token: {mint_address} - {token_data.get('name', 'Unknown')}")
            
            db.commit()
            return True
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error for token {mint_address}: {e}")
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error processing token {mint_address}: {e}")
            return False
    
    def fetch_and_process_new_tokens(self, limit: int = 50) -> int:
        """
        Convenience method to fetch and process new tokens in one call
        """
        tokens = self.fetch_new_pumpfun_tokens(limit)
        if tokens:
            return self.process_and_store_tokens(tokens)
        return 0
    
    def health_check(self) -> bool:
        """
        Perform a health check of the Moralis API connection
        """
        try:
            # Make a minimal request to test connectivity
            data = self._make_request(PUMPFUN_NEW_TOKENS_ENDPOINT, {'limit': 1})
            logger.info("Moralis API health check passed")
            return True
        except Exception as e:
            logger.error(f"Moralis API health check failed: {e}")
            return False

# Convenience functions for backward compatibility
def fetch_new_pumpfun_tokens(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch new PumpFun tokens"""
    fetcher = PumpFunFetcher()
    return fetcher.fetch_new_pumpfun_tokens(limit)

def process_pumpfun_tokens(tokens: List[Dict[str, Any]]) -> int:
    """Process and store PumpFun tokens"""
    fetcher = PumpFunFetcher()
    return fetcher.process_and_store_tokens(tokens)

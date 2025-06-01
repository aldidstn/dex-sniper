import requests
import logging
import time
import os
from typing import Dict, List, Optional, Any
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class PumpFunFetcher:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
        """
        Initialize PumpFun fetcher with Moralis API integration
        
        Args:
            api_key: Moralis API key (if None, will try to get from environment)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key or os.getenv('MORALIS_API_KEY')
        if not self.api_key:
            logger.warning("No API key provided. Set MORALIS_API_KEY environment variable or provide api_key parameter")
        
        self.base_url = "https://solana-gateway.moralis.io"
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "DexSniper/1.0"
        })
        
        if self.api_key:
            self.session.headers.update({"X-API-Key": self.api_key})
    
    def update_api_key(self, api_key: str) -> None:
        """Update the API key for authentication"""
        self.api_key = api_key
        self.session.headers.update({"X-API-Key": self.api_key})
        logger.info("API key updated successfully")
    
    def health_check(self) -> bool:
        """
        Perform API health check to verify authentication and connectivity
        
        Returns:
            bool: True if API is accessible, False otherwise
        """
        if not self.api_key:
            logger.error("No API key configured. Cannot perform health check.")
            return False
        
        endpoint = f"{self.base_url}/token/mainnet/exchange/pumpfun/new"
        
        try:
            logger.info(f"Making health check request to {endpoint}")
            response = self.session.get(endpoint, timeout=self.timeout)
            
            if response.status_code == 200:
                logger.info("API health check successful")
                return True
            elif response.status_code == 401:
                logger.error("API health check failed: Invalid API key or authentication failed")
                return False
            elif response.status_code == 429:
                logger.error("API health check failed: Rate limit exceeded")
                return False
            else:
                logger.error(f"API health check failed: HTTP {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("API health check failed: Request timeout")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("API health check failed: Connection error")
            return False
        except Exception as e:
            logger.error(f"API health check failed: Unexpected error - {str(e)}")
            return False
    
    def get_new_tokens(self, limit: int = 50) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch new tokens from Pump.Fun platform
        
        Args:
            limit: Maximum number of tokens to retrieve
            
        Returns:
            List of token data or None if request fails
        """
        if not self.api_key:
            logger.error("No API key configured. Cannot fetch tokens.")
            return None
        
        endpoint = f"{self.base_url}/token/mainnet/exchange/pumpfun/new"
        params = {"limit": limit} if limit != 50 else {}
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Making request to {endpoint} (attempt {attempt}/{self.max_retries})")
                response = self.session.get(endpoint, params=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully retrieved {len(data)} tokens")
                    return data
                elif response.status_code == 401:
                    logger.error("Authentication failed: Invalid API key")
                    return None
                elif response.status_code == 429:
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Request failed: HTTP {response.status_code} - {response.text}")
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt)
                        continue
                    return None
                    
            except requests.exceptions.Timeout:
                logger.error(f"Request timeout (attempt {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
                return None
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error (attempt {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
                return None
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON response")
                return None
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                return None
        
        return None
    
    def get_token_details(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific token
        
        Args:
            token_address: The token contract address
            
        Returns:
            Token details or None if request fails
        """
        if not self.api_key:
            logger.error("No API key configured. Cannot fetch token details.")
            return None
        
        endpoint = f"{self.base_url}/token/mainnet/{token_address}"
        
        try:
            logger.info(f"Fetching details for token {token_address}")
            response = self.session.get(endpoint, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Token {token_address} not found")
                return None
            else:
                logger.error(f"Failed to fetch token details: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching token details: {str(e)}")
            return None
    
    def close(self):
        """Close the session"""
        self.session.close()

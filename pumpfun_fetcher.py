# import requests
# import logging
# import time
# import os
# from typing import Dict, List, Optional, Any
# import json
# from requests.adapters import HTTPAdapter
# from urllib3.util.retry import Retry

# logger = logging.getLogger(__name__)

# class PumpFunFetcher:
#     def __init__(self, api_key: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
#         """
#         Initialize PumpFun fetcher with Moralis API integration
        
#         Args:
#             api_key: Moralis API key (if None, will try to get from environment)
#             timeout: Request timeout in seconds
#             max_retries: Maximum number of retry attempts
#         """
#         self.api_key = api_key or os.getenv('MORALIS_API_KEY')
#         if not self.api_key:
#             logger.warning("No API key provided. Set MORALIS_API_KEY environment variable or provide api_key parameter")
        
#         self.base_url = "https://solana-gateway.moralis.io"
#         self.timeout = timeout
#         self.max_retries = max_retries
        
#         # Setup session with retry strategy
#         self.session = requests.Session()
#         retry_strategy = Retry(
#             total=max_retries,
#             backoff_factor=1,
#             status_forcelist=[429, 500, 502, 503, 504],
#             allowed_methods=["HEAD", "GET", "OPTIONS"]
#         )
#         adapter = HTTPAdapter(max_retries=retry_strategy)
#         self.session.mount("http://", adapter)
#         self.session.mount("https://", adapter)
        
#         # Set default headers
#         self.session.headers.update({
#             "Accept": "application/json",
#             "Content-Type": "application/json",
#             "User-Agent": "DexSniper/1.0"
#         })
        
#         if self.api_key:
#             self.session.headers.update({"X-API-Key": self.api_key})
    
#     def update_api_key(self, api_key: str) -> None:
#         """Update the API key for authentication"""
#         self.api_key = api_key
#         self.session.headers.update({"X-API-Key": self.api_key})
#         logger.info("API key updated successfully")
    
#     # def health_check(self) -> bool:
#     #     """
#     #     Perform API health check to verify authentication and connectivity
        
#     #     Returns:
#     #         bool: True if API is accessible, False otherwise
#     #     """
#     #     if not self.api_key:
#     #         logger.error("No API key configured. Cannot perform health check.")
#     #         return False
        
#     #     endpoint = f"{self.base_url}/token/mainnet/exchange/pumpfun/new"
        
#     #     try:
#     #         logger.info(f"Making health check request to {endpoint}")
#     #         response = self.session.get(endpoint, timeout=self.timeout)
            
#     #         if response.status_code == 200:
#     #             logger.info("API health check successful")
#     #             return True
#     #         elif response.status_code == 401:
#     #             logger.error("API health check failed: Invalid API key or authentication failed")
#     #             return False
#     #         elif response.status_code == 429:
#     #             logger.error("API health check failed: Rate limit exceeded")
#     #             return False
#     #         else:
#     #             logger.error(f"API health check failed: HTTP {response.status_code} - {response.text}")
#     #             return False
                
#     #     except requests.exceptions.Timeout:
#     #         logger.error("API health check failed: Request timeout")
#     #         return False
#     #     except requests.exceptions.ConnectionError:
#     #         logger.error("API health check failed: Connection error")
#     #         return False
#     #     except Exception as e:
#     #         logger.error(f"API health check failed: Unexpected error - {str(e)}")
#     #         return False
    
#     def get_new_tokens(self, limit: int = 50) -> Optional[List[Dict[str, Any]]]:
#         """
#         Fetch new tokens from Pump.Fun platform
        
#         Args:
#             limit: Maximum number of tokens to retrieve
            
#         Returns:
#             List of token data or None if request fails
#         """
#         if not self.api_key:
#             logger.error("No API key configured. Cannot fetch tokens.")
#             return None
        
#         endpoint = f"{self.base_url}/token/mainnet/exchange/pumpfun/new"
#         params = {"limit": limit} if limit != 50 else {}
        
#         for attempt in range(1, self.max_retries + 1):
#             try:
#                 logger.info(f"Making request to {endpoint} (attempt {attempt}/{self.max_retries})")
#                 response = self.session.get(endpoint, params=params, timeout=self.timeout)
                
#                 if response.status_code == 200:
#                     data = response.json()
#                     logger.info(f"Successfully retrieved {len(data)} tokens")
#                     return data
#                 elif response.status_code == 401:
#                     logger.error("Authentication failed: Invalid API key")
#                     return None
#                 elif response.status_code == 429:
#                     wait_time = 2 ** attempt
#                     logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds before retry...")
#                     time.sleep(wait_time)
#                     continue
#                 else:
#                     logger.error(f"Request failed: HTTP {response.status_code} - {response.text}")
#                     if attempt < self.max_retries:
#                         time.sleep(2 ** attempt)
#                         continue
#                     return None
                    
#             except requests.exceptions.Timeout:
#                 logger.error(f"Request timeout (attempt {attempt}/{self.max_retries})")
#                 if attempt < self.max_retries:
#                     time.sleep(2 ** attempt)
#                     continue
#                 return None
#             except requests.exceptions.ConnectionError:
#                 logger.error(f"Connection error (attempt {attempt}/{self.max_retries})")
#                 if attempt < self.max_retries:
#                     time.sleep(2 ** attempt)
#                     continue
#                 return None
#             except json.JSONDecodeError:
#                 logger.error("Failed to parse JSON response")
#                 return None
#             except Exception as e:
#                 logger.error(f"Unexpected error: {str(e)}")
#                 return None
        
#         return None
    
#     def get_token_details(self, token_address: str) -> Optional[Dict[str, Any]]:
#         """
#         Get detailed information about a specific token
        
#         Args:
#             token_address: The token contract address
            
#         Returns:
#             Token details or None if request fails
#         """
#         if not self.api_key:
#             logger.error("No API key configured. Cannot fetch token details.")
#             return None
        
#         endpoint = f"{self.base_url}/token/mainnet/{token_address}"
        
#         try:
#             logger.info(f"Fetching details for token {token_address}")
#             response = self.session.get(endpoint, timeout=self.timeout)
            
#             if response.status_code == 200:
#                 return response.json()
#             elif response.status_code == 404:
#                 logger.warning(f"Token {token_address} not found")
#                 return None
#             else:
#                 logger.error(f"Failed to fetch token details: HTTP {response.status_code}")
#                 return None
                
#         except Exception as e:
#             logger.error(f"Error fetching token details: {str(e)}")
#             return None
    
#     def close(self):
#         """Close the session"""
#         self.session.close()

import requests
import logging
import time
import os
from typing import Dict, List, Optional, Any
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class MoralisAPIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code

class PumpFunFetcher:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
        """
        Initialize PumpFun fetcher with RapidAPI integration
        
        Args:
            api_key: RapidAPI key (if None, will try to get from environment)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        # Use provided API key or the one specified by user
        self.api_key = api_key or "47f8a0ad6cmsh0931d63e060bd42p167f5djsn78b3278e46b0"
        
        # Update base URL and endpoint for new API
        self.base_url = "https://pumpfun-scraper-api.p.rapidapi.com"
        self.endpoint = "/get_latest_token"
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
        
        # Set RapidAPI headers
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "DexSniper/1.0",
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "pumpfun-scraper-api.p.rapidapi.com"
        })
    
    def update_api_key(self, api_key: str) -> None:
        """Update the API key for authentication"""
        self.api_key = api_key
        self.session.headers.update({"x-rapidapi-key": self.api_key})
        logger.info("RapidAPI key updated successfully")
    
    def health_check(self) -> bool:
        """
        Perform API health check to verify authentication and connectivity
        
        Returns:
            bool: True if API is accessible, False otherwise
        """
        if not self.api_key:
            logger.error("No API key configured. Cannot perform health check.")
            return False
        
        full_url = f"{self.base_url}{self.endpoint}"
        
        try:
            logger.info(f"Making health check request to {full_url}")
            response = self.session.get(full_url, timeout=self.timeout)
            
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
        Fetch new tokens from Pump.Fun platform via RapidAPI
        
        Args:
            limit: Maximum number of tokens to retrieve (may not be supported by new API)
            
        Returns:
            List of token data or None if request fails
        """
        full_url = f"{self.base_url}{self.endpoint}"
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Making request to {full_url} (attempt {attempt}/{self.max_retries})")
                response = self.session.get(full_url, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    # Handle different response formats - new API might return different structure
                    if isinstance(data, list):
                        logger.info(f"Successfully retrieved {len(data)} tokens")
                        return data[:limit] if limit and len(data) > limit else data
                    elif isinstance(data, dict) and 'tokens' in data:
                        tokens = data['tokens']
                        logger.info(f"Successfully retrieved {len(tokens)} tokens")
                        return tokens[:limit] if limit and len(tokens) > limit else tokens
                    else:
                        logger.info("Successfully retrieved token data")
                        return [data] if isinstance(data, dict) else []
                        
                elif response.status_code == 401:
                    logger.error("Authentication failed: Invalid RapidAPI key")
                    raise MoralisAPIError("Invalid RapidAPI key", response.status_code)
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
                    raise MoralisAPIError(f"API request failed with status {response.status_code}", response.status_code)
                    
            except requests.exceptions.Timeout:
                logger.error(f"Request timeout (attempt {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
                raise MoralisAPIError("Request timeout")
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error (attempt {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
                raise MoralisAPIError("Connection error")
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON response")
                raise MoralisAPIError("Invalid JSON response")
            except MoralisAPIError:
                raise
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise MoralisAPIError(f"Unexpected error: {str(e)}")
        
        raise MoralisAPIError("Max retries exceeded")
    
    def get_token_details(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific token
        Note: This functionality may not be available in the new API
        
        Args:
            token_address: The token contract address
            
        Returns:
            Token details or None if not supported
        """
        logger.warning("get_token_details may not be supported by the new PumpFun API")
        logger.info(f"Token details requested for {token_address} - functionality may be limited")
        
        # If the new API doesn't support individual token lookup,
        # we could fetch all tokens and filter by address
        try:
            all_tokens = self.get_new_tokens()
            if all_tokens:
                for token in all_tokens:
                    if isinstance(token, dict):
                        # Check various possible address fields
                        if (token.get('address') == token_address or 
                            token.get('token_address') == token_address or
                            token.get('contract_address') == token_address):
                            return token
            return None
        except Exception as e:
            logger.error(f"Error fetching token details: {str(e)}")
            return None
    
    def close(self):
        """Close the session"""
        self.session.close()

# Maintain backward compatibility
def moralis_api_error(message, status_code=None):
    """Factory function for creating API errors"""
    return MoralisAPIError(message, status_code)


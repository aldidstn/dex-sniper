# test_pumpfun_fetcher.py
import unittest
import json
from unittest.mock import patch, Mock
from pumpfun_fetcher import PumpFunFetcher, moralis_api_error, MoralisAPIError
import requests
class MoralisAPIError(Exception):
    """Custom exception for Moralis API errors"""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code
class PumpFunFetcher:
    """Class to fetch new tokens from the PumpFun API"""
    
    def __init__(self, api_key=None, timeout=30, max_retries=3):
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = "https://api.pumpfun.com/v1"
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'X-API-Key': api_key})
    
    def update_api_key(self, api_key):
        """Update the API key for the session"""
        self.api_key = api_key
        self.session.headers.update({'X-API-Key': api_key})
    
    def _make_request(self, endpoint, params=None):
        """Make a GET request to the PumpFun API"""
        url = f"{self.base_url}/{endpoint}"
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise MoralisAPIError("Invalid API key", status_code=response.status_code)
                else:
                    raise MoralisAPIError(f"Request failed with status {response.status_code}", status_code=response.status_code)
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    continue
                raise MoralisAPIError("Request timed out")
            except requests.exceptions.RequestException as e:
                raise MoralisAPIError(f"Request error: {str(e)}")
    
    def fetch_new_pumpfun_tokens(self, limit=100):
        """Fetch new tokens from the PumpFun API"""
        return self._make_request('tokens/new', params={'limit': limit})
    
    def health_check(self):
        """Check if the API is reachable"""
        try:
            response = self._make_request('health')
            return response.get('status') == 'ok'
        except MoralisAPIError as e:
            print(f"Health check failed: {e}")
            return False
import unittest
from unittest.mock import patch, Mock
from pumpfun_fetcher import PumpFunFetcher, MoralisAPIError
import requests
import logging
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class TestPumpFunFetcher(unittest.TestCase):
    
    def setUp(self):
        self.fetcher = PumpFunFetcher()
        
    @patch('pumpfun_fetcher.requests.Session.get')
    def test_successful_token_fetch(self, mock_get):
        """Test successful token fetching"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'mint_address': 'test123',
                'name': 'Test Token',
                'symbol': 'TEST'
            }
        ]
        mock_get.return_value = mock_response
        
        tokens = self.fetcher.fetch_new_pumpfun_tokens(limit=1)
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0]['name'], 'Test Token')
        
    @patch('pumpfun_fetcher.requests.Session.get')
    def test_api_key_error(self, mock_get):
        """Test handling of invalid API key"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        with self.assertRaises(MoralisAPIError):
            self.fetcher._make_request('http://test.com')
            
    def test_health_check(self):
        """Test API health check functionality"""
        with patch.object(self.fetcher, '_make_request', return_value={}):
            self.assertTrue(self.fetcher.health_check())

if __name__ == '__main__':
    unittest.main()

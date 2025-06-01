# test_pumpfun_fetcher.py
import unittest
import json
from unittest.mock import patch, Mock
from pumpfun_fetcher import PumpFunFetcher, MoralisAPIError

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

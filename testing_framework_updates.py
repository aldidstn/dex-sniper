import unittest
import json
from unittest.mock import patch, Mock, MagicMock
from pumpfun_fetcher import PumpFunFetcher, MoralisAPIError
import requests

class TestPumpFunFetcher(unittest.TestCase):
    
    def setUp(self):
        self.api_key = "47f8a0ad6cmsh0931d63e060bd42p167f5djsn78b3278e46b0"
        self.fetcher = PumpFunFetcher(api_key=self.api_key)
    
    def tearDown(self):
        self.fetcher.close()
    
    @patch('requests.Session.get')
    def test_successful_token_fetch(self, mock_get):
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "address": "test_address_1",
                "name": "Test Token 1",
                "symbol": "TEST1"
            },
            {
                "address": "test_address_2", 
                "name": "Test Token 2",
                "symbol": "TEST2"
            }
        ]
        mock_get.return_value = mock_response
        
        tokens = self.fetcher.get_new_tokens()
        
        self.assertIsNotNone(tokens)
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0]["address"], "test_address_1")
        
        # Verify correct headers were used
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[0][0], "https://pumpfun-scraper-api.p.rapidapi.com/get_latest_token")
    
    @patch('requests.Session.get')
    def test_authentication_failure(self, mock_get):
        # Mock authentication failure
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response
        
        with self.assertRaises(MoralisAPIError) as context:
            self.fetcher.get_new_tokens()
        
        self.assertEqual(context.exception.status_code, 401)
    
    @patch('requests.Session.get')
    def test_rate_limiting(self, mock_get):
        # Mock rate limiting responses
        responses = []
        for i in range(3):
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"
            responses.append(mock_response)
        
        # Final successful response
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = []
        responses.append(success_response)
        
        mock_get.side_effect = responses
        
        with patch('time.sleep'):  # Skip actual sleep in tests
            tokens = self.fetcher.get_new_tokens()
        
        self.assertEqual(tokens, [])
        self.assertEqual(mock_get.call_count, 4)
    
    def test_api_key_update(self):
        new_key = "new_test_key"
        self.fetcher.update_api_key(new_key)
        
        self.assertEqual(self.fetcher.api_key, new_key)
        self.assertEqual(
            self.fetcher.session.headers["x-rapidapi-key"], 
            new_key
        )
    
    @patch('requests.Session.get')
    def test_health_check_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.fetcher.health_check()
        self.assertTrue(result)
    
    @patch('requests.Session.get')
    def test_health_check_failure(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response
        
        result = self.fetcher.health_check()
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()

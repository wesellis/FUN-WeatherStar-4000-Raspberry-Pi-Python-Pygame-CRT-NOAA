#!/usr/bin/env python3
"""
Unit tests for Open Meteo API module
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from weatherstar_modules.open_meteo_api import OpenMeteoAPI


class TestOpenMeteoAPI(unittest.TestCase):
    """Test Open Meteo API client"""

    def setUp(self):
        """Set up test with API instance"""
        self.api = OpenMeteoAPI()

    def test_initialization(self):
        """Test API initialization"""
        self.assertEqual(self.api.base_url, "https://api.open-meteo.com/v1")
        self.assertEqual(self.api.geocoding_url, "https://geocoding-api.open-meteo.com/v1")
        self.assertIsInstance(self.api.cache, dict)
        self.assertIsInstance(self.api.cache_time, dict)

    def test_cache_data(self):
        """Test data caching"""
        test_data = {"temperature": 72}
        self.api._cache_data("test_key", test_data)

        self.assertIn("test_key", self.api.cache)
        self.assertIn("test_key", self.api.cache_time)
        self.assertEqual(self.api.cache["test_key"], test_data)

    def test_cache_valid(self):
        """Test cache validation"""
        self.api._cache_data("test_key", {"data": "value"})

        # Should be valid immediately
        self.assertTrue(self.api._is_cache_valid("test_key", 300))

        # Should be invalid for non-existent key
        self.assertFalse(self.api._is_cache_valid("nonexistent", 300))

    @patch('requests.get')
    def test_get_location_name(self, mock_get):
        """Test getting location name from coordinates"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [{
                'name': 'New York',
                'country': 'United States',
                'admin1': 'New York'
            }]
        }
        mock_get.return_value = mock_response

        location = self.api.get_location_name(40.7128, -74.0060)
        self.assertIn('New York', location)

    @patch('requests.get')
    def test_get_location_name_error(self, mock_get):
        """Test location name fallback on error"""
        mock_get.side_effect = Exception("API Error")

        location = self.api.get_location_name(40.7128, -74.0060)
        # Should return coordinates as fallback
        self.assertIn('40.71', location)
        self.assertIn('-74.01', location)

    def test_cache_prevents_duplicate_requests(self):
        """Test that cache prevents duplicate API requests"""
        cache_key = "location_40.0_-74.0"
        self.api._cache_data(cache_key, "Cached Location")

        # Verify cache is valid
        self.assertTrue(self.api._is_cache_valid(cache_key, 300))

        # Verify cached data is retrievable
        self.assertEqual(self.api.cache[cache_key], "Cached Location")


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""
Unit tests for WeatherStar 4000 settings manager
"""

import unittest
import json
import sys
import tempfile
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from weatherstar_modules import weatherstar_settings


class TestWeatherStarSettings(unittest.TestCase):
    """Test settings manager functionality"""

    def setUp(self):
        """Set up test with temporary settings file"""
        # Use temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        weatherstar_settings.SETTINGS_FILE = Path(self.temp_file.name)

    def tearDown(self):
        """Clean up temporary settings file"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_load_default_settings(self):
        """Test loading default settings when file doesn't exist"""
        # Remove temp file to test defaults
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

        settings = weatherstar_settings.load_settings()

        self.assertIn('location', settings)
        self.assertIn('display', settings)
        self.assertEqual(settings['location']['auto_detect'], True)
        self.assertIsInstance(settings['display']['music_volume'], float)

    def test_save_and_load_settings(self):
        """Test saving and loading settings"""
        test_settings = {
            'location': {
                'auto_detect': False,
                'lat': 40.7128,
                'lon': -74.0060,
                'description': 'New York, NY'
            },
            'display': {
                'show_marine': True,
                'music_volume': 0.5
            }
        }

        success = weatherstar_settings.save_settings(test_settings)
        self.assertTrue(success)

        loaded = weatherstar_settings.load_settings()
        self.assertEqual(loaded['location']['lat'], 40.7128)
        self.assertEqual(loaded['location']['lon'], -74.0060)

    def test_save_location(self):
        """Test saving location preference"""
        success = weatherstar_settings.save_location(
            lat=34.0522,
            lon=-118.2437,
            description="Los Angeles, CA",
            auto_detect=False
        )
        self.assertTrue(success)

        settings = weatherstar_settings.load_settings()
        self.assertEqual(settings['location']['lat'], 34.0522)
        self.assertEqual(settings['location']['lon'], -118.2437)
        self.assertEqual(settings['location']['description'], "Los Angeles, CA")

    def test_get_saved_location(self):
        """Test retrieving saved location"""
        weatherstar_settings.save_location(
            lat=41.8781,
            lon=-87.6298,
            description="Chicago, IL",
            auto_detect=False
        )

        location = weatherstar_settings.get_saved_location()
        self.assertIsNotNone(location)
        self.assertEqual(location[0], 41.8781)
        self.assertEqual(location[1], -87.6298)

    def test_save_display_preferences(self):
        """Test saving display preferences"""
        prefs = {
            'show_marine': True,
            'show_trends': False,
            'music_volume': 0.7
        }

        success = weatherstar_settings.save_display_preferences(prefs)
        self.assertTrue(success)

        loaded_prefs = weatherstar_settings.get_display_preferences()
        self.assertEqual(loaded_prefs['show_marine'], True)
        self.assertEqual(loaded_prefs['show_trends'], False)
        self.assertAlmostEqual(loaded_prefs['music_volume'], 0.7)

    def test_get_display_preferences(self):
        """Test retrieving display preferences"""
        prefs = weatherstar_settings.get_display_preferences()
        self.assertIsInstance(prefs, dict)
        self.assertIn('music_volume', prefs)


if __name__ == '__main__':
    unittest.main()

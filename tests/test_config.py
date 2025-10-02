#!/usr/bin/env python3
"""
Unit tests for WeatherStar 4000 configuration module
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from weatherstar_modules.config import *


class TestConfig(unittest.TestCase):
    """Test configuration constants and enums"""

    def test_screen_dimensions(self):
        """Test that screen dimensions are set correctly"""
        self.assertEqual(SCREEN_WIDTH, 640)
        self.assertEqual(SCREEN_HEIGHT, 480)

    def test_display_timing(self):
        """Test display timing constants"""
        self.assertEqual(DISPLAY_DURATION_MS, 15000)
        self.assertEqual(SCROLL_SPEED, 100)

    def test_font_sizes(self):
        """Test font size constants"""
        self.assertEqual(FONT_SIZE_SMALL, 16)
        self.assertEqual(FONT_SIZE_NORMAL, 20)
        self.assertEqual(FONT_SIZE_LARGE, 24)
        self.assertEqual(FONT_SIZE_HEADER, 36)

    def test_colors_palette(self):
        """Test that color palette is defined"""
        self.assertIn('blue', COLORS)
        self.assertIn('white', COLORS)
        self.assertIn('yellow', COLORS)
        self.assertIsInstance(COLORS['blue'], tuple)
        self.assertEqual(len(COLORS['blue']), 3)

    def test_display_modes_enum(self):
        """Test DisplayMode enum"""
        self.assertTrue(hasattr(DisplayMode, 'CURRENT_CONDITIONS'))
        self.assertTrue(hasattr(DisplayMode, 'LOCAL_FORECAST'))
        self.assertTrue(hasattr(DisplayMode, 'RADAR'))
        self.assertTrue(hasattr(DisplayMode, 'HAZARDS'))

    def test_display_mode_values(self):
        """Test DisplayMode enum values are strings"""
        for mode in DisplayMode:
            self.assertIsInstance(mode.value, str)


if __name__ == '__main__':
    unittest.main()

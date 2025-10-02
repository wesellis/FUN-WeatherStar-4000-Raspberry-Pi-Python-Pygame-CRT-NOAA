#!/usr/bin/env python3
"""
Weather History Module - 90s WeatherStar Aesthetic
Displays 30-day temperature and precipitation history in scrolling text format
"""

import time
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional


class WeatherHistory:
    """Manages 30-day weather history data for text-based displays"""

    def __init__(self):
        self.history_data = {
            'temperature': [],  # List of (date, high, low) tuples
            'precipitation': [],  # List of (date, precip) tuples
        }
        self.cache_time = 0
        self.cache_duration = 3600  # Cache for 1 hour
        self.scroll_offset_temp = 0
        self.scroll_offset_precip = 0
        self.last_scroll_time = time.time()
        self.scroll_delay = 3.0  # Seconds before scrolling starts

    def fetch_history_data(self, lat: float, lon: float) -> bool:
        """Fetch 30-day weather history from Open Meteo API"""
        # Check cache
        if time.time() - self.cache_time < self.cache_duration:
            return len(self.history_data['temperature']) > 0

        try:
            import requests

            # Get 30 days of historical data from Open Meteo
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
                'temperature_unit': 'fahrenheit',
                'precipitation_unit': 'inch',
                'past_days': 30,
                'timezone': 'auto'
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                daily = data.get('daily', {})

                dates = daily.get('time', [])
                temp_max = daily.get('temperature_2m_max', [])
                temp_min = daily.get('temperature_2m_min', [])
                precip = daily.get('precipitation_sum', [])

                # Store temperature data (most recent first for scrolling)
                self.history_data['temperature'] = []
                for i in range(len(dates) - 1, -1, -1):  # Reverse order
                    if i < len(temp_max) and i < len(temp_min):
                        self.history_data['temperature'].append(
                            (dates[i], temp_max[i], temp_min[i])
                        )

                # Store precipitation data (most recent first)
                self.history_data['precipitation'] = []
                for i in range(len(dates) - 1, -1, -1):  # Reverse order
                    if i < len(precip):
                        self.history_data['precipitation'].append(
                            (dates[i], precip[i] if precip[i] else 0)
                        )

                self.cache_time = time.time()
                return True

        except Exception as e:
            print(f"Error fetching history data: {e}")
            return False

        return False

    def update_scroll(self, current_time: float, scroll_speed: float = 20):
        """Update scroll position for smooth scrolling"""
        # Wait before starting scroll
        if current_time - self.last_scroll_time < self.scroll_delay:
            return

        # Scroll speed in pixels per second
        self.scroll_offset_temp += scroll_speed * (1/60)  # Assuming 60 FPS
        self.scroll_offset_precip += scroll_speed * (1/60)


# Singleton instance
_history_instance = None

def get_weather_history():
    """Get singleton instance of weather history"""
    global _history_instance
    if _history_instance is None:
        _history_instance = WeatherHistory()
    return _history_instance

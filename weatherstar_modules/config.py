"""
WeatherStar 4000 Configuration and Constants
"""

from enum import Enum

# Screen dimensions (authentic WeatherStar 4000)
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

# Display timing
DISPLAY_DURATION_MS = 15000  # 15 seconds per screen
SCROLL_SPEED = 100  # pixels/second for bottom scroll

# Font sizes
FONT_SIZE_SMALL = 16
FONT_SIZE_NORMAL = 20
FONT_SIZE_LARGE = 24
FONT_SIZE_HEADER = 36

# Colors - WeatherStar 4000 palette
COLORS = {
    'blue': (0, 71, 171),      # WeatherStar primary blue
    'orange': (255, 140, 0),   # WeatherStar accent orange
    'yellow': (255, 255, 0),   # Text highlights
    'white': (255, 255, 255),  # Primary text
    'black': (0, 0, 0),        # Background
    'gray': (128, 128, 128),   # Secondary info
    'green': (0, 255, 0),      # Good conditions
    'red': (255, 0, 0),        # Warnings/alerts
    'cyan': (0, 255, 255),     # Categories
    'dark_blue': (0, 50, 100), # Night sky
}

# Display Modes
class DisplayMode(Enum):
    """All available display screens"""
    CURRENT_CONDITIONS = "current-conditions"
    LOCAL_FORECAST = "local-forecast"
    EXTENDED_FORECAST = "extended-forecast"
    HOURLY_FORECAST = "hourly-forecast"
    REGIONAL_OBSERVATIONS = "regional-observations"
    TRAVEL_CITIES = "travel-cities"
    MARINE_FORECAST = "marine-forecast"
    AIR_QUALITY = "air-quality"
    TEMPERATURE_GRAPH = "temperature-graph"
    WEATHER_RECORDS = "weather-records"
    SUN_MOON = "sun-moon"
    WIND_PRESSURE = "wind-pressure"
    WEEKEND_FORECAST = "weekend-forecast"
    MONTHLY_OUTLOOK = "monthly-outlook"
    ALMANAC = "almanac"
    HAZARDS = "hazards"
    RADAR = "radar"
    PROGRESS = "progress"
    MSN_NEWS = "msn-news"
    REDDIT_NEWS = "reddit-news"
    LOCAL_NEWS = "local-news"
    TEMPERATURE_HISTORY = "temperature-history"  # 30-day temperature history
    PRECIPITATION_HISTORY = "precipitation-history"  # 30-day precipitation history
    UV_INDEX = "uv-index"  # UV Index forecast
    EARTHQUAKES = "earthquakes"  # Recent earthquakes (USGS)
    STOCK_MARKET = "stock-market"  # Stock market indices
    SEVERE_WEATHER_ALERT = "severe-weather-alert"  # Animated weather alerts
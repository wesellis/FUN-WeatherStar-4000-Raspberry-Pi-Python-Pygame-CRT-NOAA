#!/usr/bin/env python3
"""
WeatherStar 4000+ Python Implementation with Comprehensive Logging
"""

import pygame
import requests
import json
import time
import os
import sys
import io
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from typing import Dict, List, Optional, Tuple
import math
import random
import logging
import webbrowser
import threading

# Import our custom modules
from weatherstar_modules.weatherstar_logger import init_logger, get_logger
from weatherstar_modules import weatherstar_settings
from weatherstar_modules import get_local_news
from weatherstar_modules.animated_icons import AnimatedIconManager
from weatherstar_modules.displays import WeatherStarDisplays
from weatherstar_modules.news_displays import WeatherStarNewsDisplays
from weatherstar_modules.data_fetchers import WeatherStarDataFetchers
from weatherstar_modules.themes import get_theme, list_themes, CLASSIC_THEME
from weatherstar_modules.history_graphs import get_weather_history
from weatherstar_modules.emergency_animations import SevereWeatherDisplay
from weatherstar_modules.performance import get_performance_optimizer
from weatherstar_modules.voice_narration import get_narrator
from weatherstar_modules import display_history

# Initialize logging
logger = init_logger()

# Log imports
logger.main_logger.info("Importing modules...")

try:
    import pygame
    logger.main_logger.debug("pygame imported successfully")
except ImportError as e:
    logger.log_error("Failed to import pygame", e)
    sys.exit(1)

try:
    import requests
    logger.main_logger.debug("requests imported successfully")
except ImportError as e:
    logger.log_error("Failed to import requests", e)
    sys.exit(1)

# Screen dimensions (authentic WeatherStar 4000)
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

# Display timing (from ws4kp navigation.mjs)
DISPLAY_DURATION_MS = 15000  # 15 seconds per screen (slowed down for better viewing)
SCROLL_SPEED = 100  # pixels/second for bottom scroll

# Authentic ws4kp display modes
class DisplayMode(Enum):
    PROGRESS = "progress"
    CURRENT_CONDITIONS = "current-weather"
    LOCAL_FORECAST = "local-forecast"
    EXTENDED_FORECAST = "extended-forecast"
    HOURLY_FORECAST = "hourly"
    REGIONAL_OBSERVATIONS = "latest-observations"
    TRAVEL_CITIES = "travel-cities"
    ALMANAC = "almanac"
    RADAR = "radar"
    HAZARDS = "hazards"
    MARINE_FORECAST = "marine-forecast"
    AIR_QUALITY = "air-quality"
    TEMPERATURE_GRAPH = "temperature-graph"
    WEATHER_RECORDS = "weather-records"
    SUN_MOON = "sun-moon"
    WIND_PRESSURE = "wind-pressure"
    WEEKEND_FORECAST = "weekend-forecast"
    MONTHLY_OUTLOOK = "monthly-outlook"
    MSN_NEWS = "msn-news"
    REDDIT_NEWS = "reddit-news"
    LOCAL_NEWS = "local-news"
    TEMPERATURE_HISTORY = "temperature-history"
    PRECIPITATION_HISTORY = "precipitation-history"
    UV_INDEX = "uv-index"
    EARTHQUAKES = "earthquakes"
    STOCK_MARKET = "stock-market"
    SEVERE_WEATHER_ALERT = "severe-weather-alert"

# Colors from ws4kp SCSS
COLORS = {
    'yellow': (255, 255, 0),           # Title color
    'white': (255, 255, 255),          # Main text
    'black': (0, 0, 0),                # Text shadows
    'purple_header': (32, 0, 87),      # Column headers
    'blue_gradient_1': (16, 32, 128),  # Gradient start
    'blue_gradient_2': (0, 16, 64),    # Gradient end
    'light_blue': (128, 128, 255),     # Low temperatures
    'blue': (128, 128, 255),           # Alias for light_blue
    'cyan': (0, 255, 255),             # Reddit subreddits
    'red': (255, 0, 0),                # Breaking news
}

class WeatherIcon:
    """Maps weather conditions to icon files"""

    @staticmethod
    def get_icon(condition_code, is_night=False):
        """Get icon filename for weather condition"""
        icon_map = {
            'skc': 'Clear.gif' if is_night else 'Sunny.gif',
            'few': 'Mostly-Clear.gif' if is_night else 'Partly-Cloudy.gif',
            'sct': 'Partly-Cloudy.gif',
            'bkn': 'Cloudy.gif',
            'ovc': 'Cloudy.gif',
            'fog': 'Fog.gif',
            'smoke': 'Smoke.gif',
            'rain': 'Rain.gif',
            'rain_showers': 'Shower.gif',
            'tsra': 'Scattered-Thunderstorms-Day.gif' if not is_night else 'Scattered-Thunderstorms-Night.gif',
            'snow': 'Snow.gif',
            'sleet': 'Sleet.gif',
            'frzra': 'Freezing-Rain.gif',
            'wind': 'Windy.gif',
        }

        result = icon_map.get(condition_code, 'No-Data.gif')
        logger.main_logger.debug(f"Icon mapping: {condition_code} -> {result}")
        return result

class ScrollingText:
    """Bottom scrolling text"""

    def __init__(self, font):
        self.font = font
        self.text_items = []
        self.current_text = ""
        self.scroll_x = SCREEN_WIDTH
        self.last_update = time.time()
        logger.main_logger.debug("ScrollingText initialized")

    def add_item(self, text):
        """Add item to scroll"""
        self.text_items.append(text)
        logger.main_logger.debug(f"Added scroll item: {text[:50]}...")

    def update(self):
        """Update scroll position"""
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time

        # Move text left
        self.scroll_x -= SCROLL_SPEED * dt

        # Reset when text goes off screen
        text_width = self.font.size(self.current_text)[0]
        if self.scroll_x < -text_width:
            self.scroll_x = SCREEN_WIDTH
            # Cycle to next text item
            if self.text_items:
                self.current_text = self.text_items[0]
                self.text_items = self.text_items[1:] + [self.text_items[0]]
                logger.main_logger.debug(f"Cycled to next scroll text: {self.current_text[:30]}...")

    def draw(self, screen, y_pos):
        """Draw scrolling text"""
        if self.current_text:
            text_surface = self.font.render(self.current_text, True, COLORS['white'])
            screen.blit(text_surface, (self.scroll_x, y_pos))


def get_automatic_location():
    """Try to automatically detect location using various methods"""
    logger.main_logger.info("Attempting automatic location detection...")

    # Method 1: Try IP geolocation using ipapi.co (free, no key required)
    try:
        import requests
        response = requests.get('https://ipapi.co/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            lat = data.get('latitude')
            lon = data.get('longitude')
            city = data.get('city', 'Unknown')
            region = data.get('region', '')
            country = data.get('country_code', '')

            # Only use if it's in the US (NOAA only covers US)
            if country == 'US' and lat and lon:
                logger.main_logger.info(f"Location detected: {city}, {region} ({lat}, {lon})")
                return lat, lon, f"{city}, {region}"
    except Exception as e:
        logger.main_logger.debug(f"IP geolocation failed: {e}")

    # Method 2: Try alternative IP geolocation service
    try:
        response = requests.get('http://ip-api.com/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                lat = data.get('lat')
                lon = data.get('lon')
                city = data.get('city', 'Unknown')
                region = data.get('regionName', '')
                country = data.get('countryCode', '')

                if country == 'US' and lat and lon:
                    logger.main_logger.info(f"Location detected: {city}, {region} ({lat}, {lon})")
                    return lat, lon, f"{city}, {region}"
    except Exception as e:
        logger.main_logger.debug(f"Alternative IP geolocation failed: {e}")

    # If all methods fail, return None
    logger.main_logger.info("Automatic location detection failed, using default")
    return None


class NOAAWeatherAPI:
    """Weather data fetcher matching ws4kp's approach"""

    def __init__(self):
        self.base_url = "https://api.weather.gov"
        self.headers = {'User-Agent': 'WeatherStar4000Python/1.0'}
        self.cache = {}
        self.cache_time = {}
        logger.api_logger.info("NOAA Weather API initialized")

    def _is_cache_valid(self, key, max_age=300):
        """Check if cached data is still valid"""
        if key not in self.cache_time:
            return False
        age = time.time() - self.cache_time[key]
        valid = age < max_age
        if valid:
            logger.api_logger.debug(f"Cache hit for {key} (age: {age:.1f}s)")
        return valid

    def _cache_data(self, key, data):
        """Cache data with timestamp"""
        self.cache[key] = data
        self.cache_time[key] = time.time()
        logger.api_logger.debug(f"Cached data for {key}")

    def get_point_data(self, lat, lon):
        """Get weather grid point data"""
        cache_key = f"point_{lat}_{lon}"

        if self._is_cache_valid(cache_key, 3600):
            return self.cache[cache_key]

        try:
            url = f"{self.base_url}/points/{lat},{lon}"
            logger.log_api_call(url)
            resp = requests.get(url, headers=self.headers, timeout=10)
            logger.log_api_call(url, resp.status_code)

            if resp.status_code == 200:
                data = resp.json()
                self._cache_data(cache_key, data)
                logger.api_logger.info(f"Got point data for {lat},{lon}")
                return data
            else:
                logger.api_logger.warning(f"Point data request failed: {resp.status_code}")
        except Exception as e:
            logger.log_api_call(url, error=str(e))
            logger.log_error(f"Error getting point data for {lat},{lon}", e)
        return None

    def get_stations(self, stations_url):
        """Get observation stations"""
        cache_key = f"stations_{stations_url}"

        if self._is_cache_valid(cache_key, 3600):
            return self.cache[cache_key]

        try:
            logger.log_api_call(stations_url)
            resp = requests.get(stations_url, headers=self.headers, timeout=10)
            logger.log_api_call(stations_url, resp.status_code)

            if resp.status_code == 200:
                data = resp.json()
                self._cache_data(cache_key, data)
                station_count = len(data.get('features', []))
                logger.api_logger.info(f"Got {station_count} stations")
                return data
        except Exception as e:
            logger.log_api_call(stations_url, error=str(e))
            logger.log_error(f"Error getting stations", e)
        return None

    def get_current_observations(self, station_id):
        """Get current weather observations"""
        cache_key = f"obs_{station_id}"

        if self._is_cache_valid(cache_key, 300):
            return self.cache[cache_key]

        try:
            url = f"{self.base_url}/stations/{station_id}/observations/latest"
            logger.log_api_call(url)
            resp = requests.get(url, headers=self.headers, timeout=10)
            logger.log_api_call(url, resp.status_code)

            if resp.status_code == 200:
                data = resp.json()
                self._cache_data(cache_key, data)
                logger.log_weather_data("current", data.get('properties'))
                return data
        except Exception as e:
            logger.log_api_call(url, error=str(e))
            logger.log_error(f"Error getting observations for {station_id}", e)
        return None

    def get_forecast(self, office, gridX, gridY, units='us'):
        """Get weather forecast"""
        cache_key = f"forecast_{office}_{gridX}_{gridY}"

        if self._is_cache_valid(cache_key, 1800):
            return self.cache[cache_key]

        try:
            url = f"{self.base_url}/gridpoints/{office}/{gridX},{gridY}/forecast"
            logger.log_api_call(url)
            params = {'units': units}
            resp = requests.get(url, headers=self.headers, params=params, timeout=10)
            logger.log_api_call(url, resp.status_code)

            if resp.status_code == 200:
                data = resp.json()
                self._cache_data(cache_key, data)
                periods = len(data.get('properties', {}).get('periods', []))
                logger.api_logger.info(f"Got forecast with {periods} periods")
                return data
        except Exception as e:
            logger.log_api_call(url, error=str(e))
            logger.log_error(f"Error getting forecast", e)
        return None

    def get_hourly_forecast(self, office, gridX, gridY, units='us'):
        """Get hourly weather forecast"""
        cache_key = f"hourly_{office}_{gridX}_{gridY}"
        if self._is_cache_valid(cache_key, 1800):
            return self.cache[cache_key]

        try:
            url = f"{self.base_url}/gridpoints/{office}/{gridX},{gridY}/forecast/hourly"
            logger.log_api_call(url)
            params = {'units': units}
            resp = requests.get(url, headers=self.headers, params=params, timeout=10)
            logger.log_api_call(url, resp.status_code)

            if resp.status_code == 200:
                data = resp.json()
                self._cache_data(cache_key, data)
                periods = len(data.get('properties', {}).get('periods', []))
                logger.api_logger.info(f"Got hourly forecast with {periods} periods")
                return data
        except Exception as e:
            logger.log_api_call(url, error=str(e))
            logger.log_error(f"Error getting hourly forecast", e)
        return None

class WeatherStar4000Complete:
    """Complete WeatherStar 4000 implementation with logging"""

    def __init__(self, lat=None, lon=None):
        # Try automatic location detection if no coordinates provided
        if lat is None or lon is None:
            auto_result = get_automatic_location()
            if auto_result:
                lat, lon, location_desc = auto_result
                logger.main_logger.info(f"Using auto-detected location: {location_desc}")
            else:
                # Fall back to Orlando, FL
                lat, lon = 28.5383, -81.3792
                logger.main_logger.info("Using default location: Orlando, FL")

        logger.log_startup(lat, lon)
        logger.main_logger.info("Initializing WeatherStar 4000...")

        # Initialize settings
        self.settings = {
            'show_marine': False,  # Only show marine forecast if enabled
            'units': 'F',  # F or C
            'music_volume': 0.3,
            'show_trends': True,
            'show_historical': True,
            'show_msn': True,  # Auto-enabled by default
            'show_reddit': True,  # Auto-enabled by default
            'use_international': False,  # Use Open Meteo API for international weather
            'theme': 'classic',  # Color theme
            'voice_narration': False  # Voice announcements (OFF by default for authenticity)
        }

        # Load current theme
        self.current_theme = get_theme(self.settings['theme'])

        # Initialize performance optimizer
        self.perf_optimizer = get_performance_optimizer()

        # Initialize history graphs
        self.weather_history = get_weather_history()

        # Initialize severe weather display
        self.severe_weather_display = SevereWeatherDisplay(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Initialize voice narrator
        self.narrator = get_narrator()
        self.original_music_volume = 0.3  # Store original volume for ducking
        self.narrator.set_audio_callbacks(
            duck_callback=self._duck_music_volume,
            restore_callback=self._restore_music_volume
        )

        # Weather trends storage for arrow indicators
        self.weather_trends = {
            'temp': [],  # Store last 5 temperature readings
            'pressure': []  # Store last 5 pressure readings
        }

        try:
            pygame.init()
            logger.main_logger.debug("pygame initialized")
        except Exception as e:
            logger.log_error("Failed to initialize pygame", e)
            sys.exit(1)

        # Create display
        try:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("WeatherStar 4000+")
            logger.main_logger.info(f"Display created: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        except Exception as e:
            logger.log_error("Failed to create display", e)
            sys.exit(1)

        # Clock for timing
        self.clock = pygame.time.Clock()

        # Load assets
        self.assets_path = Path("weatherstar_assets")
        logger.main_logger.info(f"Loading assets from {self.assets_path}")

        self.backgrounds = self._load_backgrounds()
        self.icons = {}
        self.icon_manager = None  # Will be initialized in _load_icons
        self._load_icons()
        self.logos = self._load_logos()

        # Initialize fonts
        self._init_fonts()

        # Initialize music
        self._init_music()

        # Transition effects
        # Simple 90s style - no complex transitions

        # API client
        self.api = NOAAWeatherAPI()

        # Weather data
        self.weather_data = {}
        self.location = {}
        self.lat = lat
        self.lon = lon

        # Cache city name for local news (avoid repeated API calls)
        self.cached_city_name = None
        self.city_name_cached_at = 0

        # Display management
        self.displays = self._init_displays()
        self.current_display_index = 0
        self.display_timer = 0
        self.is_playing = True

        # Update display list after settings are initialized
        # This will be called again after settings are fully set up

        # Scrolling text
        self.scroller = ScrollingText(self.font_scroller if hasattr(self, 'font_scroller') else self.font_small)

        # Initialize weather data
        self.point_data = None
        self.station = None
        self.office = None
        self.gridX = None
        self.gridY = None

        # Now that settings are initialized, update display list to include MSN/Reddit if enabled
        self.update_display_list()

        logger.main_logger.info("WeatherStar 4000 initialization complete")

    def _load_backgrounds(self):
        """Load background images"""
        backgrounds = {}
        bg_path = self.assets_path / "backgrounds"

        logger.main_logger.info(f"Loading backgrounds from {bg_path}")

        if bg_path.exists():
            for bg_file in bg_path.glob("*.png"):
                try:
                    name = bg_file.stem
                    backgrounds[name] = pygame.image.load(str(bg_file))
                    logger.log_asset_load("background", name, True)
                except Exception as e:
                    logger.log_asset_load("background", str(bg_file), False)
                    logger.log_error(f"Error loading background {bg_file}", e)

        # Create default if none loaded
        if not backgrounds:
            logger.main_logger.warning("No backgrounds loaded, creating default")
            backgrounds['default'] = self._create_default_background()

        logger.main_logger.info(f"Loaded {len(backgrounds)} backgrounds")
        return backgrounds

    def _create_default_background(self):
        """Create default background if assets not found"""
        logger.main_logger.debug("Creating default background")
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            b = int(128 + 127 * ratio)
            color = (0, 0, b)
            pygame.draw.line(surf, color, (0, y), (SCREEN_WIDTH, y))
        return surf

    def _load_icons(self):
        """Load weather icons with animation support"""
        icons_path = self.assets_path / "icons"
        logger.main_logger.info(f"Loading icons from {icons_path}")

        # Initialize animated icon manager
        try:
            self.icon_manager = AnimatedIconManager(str(icons_path))
            logger.main_logger.info("Animated icon manager initialized")
        except Exception as e:
            logger.log_error("Failed to initialize animated icon manager", e)
            self.icon_manager = None

        # Initialize display modules
        try:
            self.displays_module = WeatherStarDisplays(self)
            self.news_module = WeatherStarNewsDisplays(self)
            self.data_module = WeatherStarDataFetchers(self)
            logger.main_logger.info("Display modules initialized successfully")
        except Exception as e:
            logger.log_error("Failed to initialize display modules", e)
            self.displays_module = None
            self.news_module = None
            self.data_module = None

        # Fallback: Load static versions for compatibility
        if icons_path.exists():
            icon_count = 0
            for icon_file in icons_path.glob("*.gif"):
                try:
                    name = icon_file.stem
                    # Load as static image for backwards compatibility
                    self.icons[name] = pygame.image.load(str(icon_file))
                    logger.log_asset_load("icon", name, True)
                    icon_count += 1
                except Exception as e:
                    logger.log_asset_load("icon", str(icon_file), False)
                    logger.log_error(f"Error loading icon {icon_file}", e)

            logger.main_logger.info(f"Loaded {icon_count} static icons as fallback")
        else:
            logger.main_logger.warning(f"Icons path not found: {icons_path}")

    def _load_logos(self):
        """Load TWC logos"""
        logos = {}
        logos_path = self.assets_path / "logos"
        logger.main_logger.info(f"Loading logos from {logos_path}")

        if logos_path.exists():
            # Load PNG logos
            for logo_file in logos_path.glob("*.png"):
                try:
                    name = logo_file.stem
                    logos[name] = pygame.image.load(str(logo_file))
                    logger.log_asset_load("logo", name, True)
                except Exception as e:
                    logger.log_asset_load("logo", str(logo_file), False)
                    logger.log_error(f"Error loading logo {logo_file}", e)
            # Load GIF logos (NOAA)
            for logo_file in logos_path.glob("*.gif"):
                try:
                    name = logo_file.stem
                    logos[name] = pygame.image.load(str(logo_file))
                    logger.log_asset_load("logo", name, True)
                except Exception as e:
                    logger.log_asset_load("logo", str(logo_file), False)
                    logger.log_error(f"Error loading logo {logo_file}", e)

        logger.main_logger.info(f"Loaded {len(logos)} logos")
        return logos

    def _init_fonts(self):
        """Initialize fonts matching ws4kp sizes"""
        logger.main_logger.info("Initializing fonts")

        # Check for converted Star4000 TTF fonts first
        font_dir = Path("weatherstar_assets/fonts_ttf")
        star4000_path = font_dir / "star4000.ttf"
        star4000_large_path = font_dir / "star4000_large.ttf"
        star4000_extended_path = font_dir / "star4000_extended.ttf"
        star4000_small_path = font_dir / "star4000_small.ttf"

        # Try to use actual Star4000 fonts
        if all(f.exists() for f in [star4000_path, star4000_large_path, star4000_extended_path, star4000_small_path]):
            logger.main_logger.info("Using authentic Star4000 fonts!")
            try:
                # Use actual Star4000 fonts with proper sizes (24pt ≈ 32px)
                self.font_title = pygame.font.Font(str(star4000_path), 32)
                self.font_large = pygame.font.Font(str(star4000_large_path), 32)
                self.font_extended = pygame.font.Font(str(star4000_extended_path), 32)
                self.font_small = pygame.font.Font(str(star4000_small_path), 28)  # Reduced from 32 for Local Forecast
                self.font_normal = pygame.font.Font(str(star4000_path), 20)
                self.font_scroller = pygame.font.Font(str(star4000_extended_path), 24)  # Sized to fit in banner
                self.font_forecast = pygame.font.Font(str(star4000_small_path), 24)  # Smaller for Local Forecast text
                self.font_tiny = pygame.font.Font(str(star4000_path), 16)  # Tiny font for compact displays
                logger.main_logger.info("Star4000 fonts loaded successfully")
                return
            except Exception as e:
                logger.log_error("Failed to load Star4000 fonts", e)

        # Fallback to system fonts
        logger.main_logger.info("Star4000 fonts not found, using fallback fonts")
        font_candidates = ['consolas', 'courier new', 'courier', 'monospace', 'dejavu sans mono']
        selected_font = None
        for font_name in font_candidates:
            font_path = pygame.font.match_font(font_name, bold=True)
            if font_path:
                selected_font = font_name
                logger.main_logger.info(f"Using font: {font_name}")
                break

        if selected_font:
            # Match ws4kp font sizes (24pt = 32px)
            self.font_title = pygame.font.Font(pygame.font.match_font(selected_font, bold=True), 32)  # Star4000
            self.font_large = pygame.font.Font(pygame.font.match_font(selected_font, bold=True), 32)  # Star4000 Large
            self.font_extended = pygame.font.Font(pygame.font.match_font(selected_font, bold=True), 32)  # Star4000 Extended
            self.font_normal = pygame.font.Font(pygame.font.match_font(selected_font, bold=False), 20)  # For data
            self.font_small = pygame.font.Font(pygame.font.match_font(selected_font, bold=False), 28)  # Star4000 Small - reduced
            self.font_forecast = pygame.font.Font(pygame.font.match_font(selected_font, bold=False), 24)  # For Local Forecast
            self.font_tiny = pygame.font.Font(pygame.font.match_font(selected_font, bold=False), 16)  # Tiny font
            self.font_scroller = pygame.font.Font(pygame.font.match_font(selected_font, bold=True), 24)  # Sized to fit in banner
            logger.main_logger.debug(f"Fonts initialized with {selected_font}")
        else:
            logger.main_logger.warning("No suitable font found, using defaults")
            self.font_title = pygame.font.Font(None, 32)
            self.font_large = pygame.font.Font(None, 32)
            self.font_extended = pygame.font.Font(None, 32)
            self.font_normal = pygame.font.Font(None, 20)
            self.font_small = pygame.font.Font(None, 28)
            self.font_forecast = pygame.font.Font(None, 24)  # For Local Forecast
            self.font_tiny = pygame.font.Font(None, 16)  # Tiny font
            self.font_scroller = pygame.font.Font(None, 24)  # Sized to fit in banner

    def _init_music(self):
        """Initialize background music player"""
        try:
            # Check if mixer is already initialized
            if not pygame.mixer.get_init():
                # Initialize mixer with specific parameters for better compatibility
                pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
                logger.main_logger.info("Music mixer initialized")
            else:
                logger.main_logger.info("Music mixer already initialized")

            # Try multiple paths for music files
            music_dirs = [
                Path("weatherstar_assets/music"),
                Path("ws4kp/server/music/default")  # Fallback to ws4kp music if needed
            ]

            music_files = []
            music_dir = None
            for dir_path in music_dirs:
                if dir_path.exists():
                    music_files = list(dir_path.glob("*.mp3"))
                    if music_files:
                        music_dir = dir_path
                        logger.main_logger.info(f"Found {len(music_files)} music files in {dir_path}")
                        break

            if music_files:
                # Pick a random song to start
                import random
                self.music_playlist = music_files
                random.shuffle(self.music_playlist)
                self.current_song_index = 0

                # Load and play first song
                first_song = self.music_playlist[0]
                try:
                    pygame.mixer.music.load(str(first_song.absolute()))
                    pygame.mixer.music.set_volume(0.6)  # 60% volume
                    pygame.mixer.music.play(-1)  # Loop indefinitely
                    logger.main_logger.info(f"Playing music: {first_song.name}")
                    logger.main_logger.info(f"Music volume: {pygame.mixer.music.get_volume()}")
                    # Check if music is actually playing
                    if pygame.mixer.music.get_busy():
                        logger.main_logger.info("Music playback confirmed active")
                    else:
                        logger.main_logger.warning("Music loaded but not playing")
                except pygame.error as e:
                    logger.log_error(f"Failed to play music file {first_song.name}", e)
            else:
                logger.main_logger.warning("No music files found in any location")
                for dir_path in music_dirs:
                    logger.main_logger.debug(f"Checked: {dir_path} - exists: {dir_path.exists()}")
        except Exception as e:
            logger.log_error("Failed to initialize music", e)

    def _init_displays(self):
        """Initialize display screens"""
        displays = [
            DisplayMode.CURRENT_CONDITIONS,
            DisplayMode.LOCAL_FORECAST,
            DisplayMode.EXTENDED_FORECAST,
            DisplayMode.HOURLY_FORECAST,
            DisplayMode.REGIONAL_OBSERVATIONS,
            DisplayMode.TRAVEL_CITIES,
            DisplayMode.MARINE_FORECAST,
            DisplayMode.AIR_QUALITY,
            DisplayMode.TEMPERATURE_GRAPH,
            DisplayMode.WEATHER_RECORDS,
            DisplayMode.SUN_MOON,
            DisplayMode.WIND_PRESSURE,
            DisplayMode.WEEKEND_FORECAST,
            DisplayMode.MONTHLY_OUTLOOK,
            DisplayMode.MSN_NEWS,  # Auto-enabled by default
            DisplayMode.REDDIT_NEWS,  # Auto-enabled by default
            DisplayMode.ALMANAC,
            DisplayMode.HAZARDS,
            DisplayMode.RADAR,
        ]
        logger.main_logger.info(f"Initialized {len(displays)} display modes")
        return displays

    def initialize_location(self):
        """Initialize weather location"""
        logger.main_logger.info(f"Initializing location: {self.lat}, {self.lon}")

        # Get point data
        self.point_data = self.api.get_point_data(self.lat, self.lon)
        if not self.point_data:
            logger.main_logger.error("Failed to get point data")
            return False

        props = self.point_data['properties']

        # Extract grid info
        self.office = props.get('gridId')
        self.gridX = props.get('gridX')
        self.gridY = props.get('gridY')
        self.radarStation = props.get('radarStation')  # Get radar station from point data

        logger.main_logger.info(f"Grid info: Office={self.office}, X={self.gridX}, Y={self.gridY}")
        if self.radarStation:
            logger.main_logger.info(f"Radar station: {self.radarStation}")
        else:
            logger.main_logger.warning("No radar station found in point data")

        # Get location info
        rel_location = props.get('relativeLocation', {}).get('properties', {})
        self.location = {
            'city': rel_location.get('city', ''),
            'state': rel_location.get('state', ''),
        }

        logger.main_logger.info(f"Location: {self.location['city']}, {self.location['state']}")

        # Get observation stations
        stations_url = props.get('observationStations')
        if stations_url:
            stations = self.api.get_stations(stations_url)
            if stations and stations.get('features'):
                # Filter for 4-letter stations
                for feature in stations['features']:
                    station_id = feature['properties']['stationIdentifier']
                    if len(station_id) == 4 and not station_id[0] in 'UC':
                        self.station = station_id
                        logger.main_logger.info(f"Selected 4-letter station: {station_id}")
                        break

                if not self.station and stations['features']:
                    self.station = stations['features'][0]['properties']['stationIdentifier']
                    logger.main_logger.info(f"Using first available station: {self.station}")
        else:
            logger.main_logger.warning("No observation stations URL")

        logger.main_logger.info(f"Initialization complete - Station: {self.station}")
        return True

    def update_weather_data(self):
        """Update all weather data"""
        logger.main_logger.info("Updating weather data...")

        if not self.station or not self.office:
            logger.main_logger.warning("Missing station or office data")
            return

        # Get current observations
        obs = self.api.get_current_observations(self.station)
        if obs:
            self.weather_data['current'] = obs.get('properties', {})
            logger.main_logger.info("Current observations updated")

        # Get forecast
        forecast = self.api.get_forecast(self.office, self.gridX, self.gridY)
        if forecast:
            self.weather_data['forecast'] = forecast.get('properties', {})
            logger.main_logger.info("Forecast updated")

            # Update scrolling text with new weather data
            if hasattr(self, 'scroller'):
                self._update_scroll_text()

        # Get hourly forecast
        hourly_forecast = self.api.get_hourly_forecast(self.office, self.gridX, self.gridY)
        if hourly_forecast:
            self.weather_data['hourly'] = hourly_forecast.get('properties', {})
            logger.main_logger.info("Hourly forecast updated")

        # Preload radar image to prevent stuttering
        logger.main_logger.info("Preloading radar image...")
        if self.data_module:
            self.data_module.fetch_radar_image()
        else:
            logger.main_logger.warning("Data module not available for radar image fetching")

    def _update_scroll_text(self):
        """Update scrolling text with current weather information"""
        try:
            if not hasattr(self, 'scroller') or not self.scroller:
                logger.main_logger.warning("No scroller available")
                return

            # Clear existing text items
            self.scroller.text_items = []

            # Add location information
            if hasattr(self, 'location') and self.location:
                city = self.location.get('city', '')
                state = self.location.get('state', '')
                if city and state:
                    self.scroller.add_item(f" +++ {city.upper()}, {state} +++ ")

            # Add current conditions if available
            current = self.weather_data.get('current', {})
            if current:
                temp = current.get('temperature', {}).get('value')
                conditions = current.get('textDescription', 'Unknown')
                humidity = current.get('relativeHumidity', {}).get('value')
                wind_speed = current.get('windSpeed', {}).get('value')
                wind_dir = current.get('windDirection', {}).get('value')

                # Build current conditions text
                current_text = ""
                if temp is not None:
                    temp_f = round(temp * 9/5 + 32)
                    current_text = f"CURRENTLY: {temp_f}°F, {conditions}"

                    # Add humidity if available
                    if humidity is not None:
                        current_text += f" ... HUMIDITY: {round(humidity)}%"

                    # Add wind information if available
                    if wind_speed is not None:
                        wind_mph = round(wind_speed * 2.237)  # Convert m/s to mph
                        wind_text = f" ... WIND: "
                        if wind_dir is not None:
                            direction = self._get_wind_direction(wind_dir)
                            wind_text += f"{direction} "
                        wind_text += f"{wind_mph} MPH"
                        current_text += wind_text

                    self.scroller.add_item(current_text)

            # Add today's high/low and forecast
            forecast = self.weather_data.get('forecast', {})
            periods = forecast.get('periods', [])
            if periods:
                today = periods[0]
                today_name = today.get('name', 'Today')
                today_forecast = today.get('shortForecast', '')
                today_temp = today.get('temperature', '')

                if today_temp and today_forecast:
                    # Try to get both high and low for today
                    high_temp = None
                    low_temp = None

                    # Check if this is a daytime or nighttime period
                    if today.get('isDaytime', True):
                        high_temp = today_temp
                        # Look for tonight's low
                        if len(periods) > 1:
                            tonight = periods[1]
                            if not tonight.get('isDaytime', True):
                                low_temp = tonight.get('temperature', '')
                    else:
                        low_temp = today_temp
                        # This shouldn't happen often, but handle it
                        high_temp = today_temp

                    forecast_text = f" +++ {today_name.upper()}: {today_forecast.upper()}"
                    if high_temp and low_temp:
                        forecast_text += f", HIGH {high_temp}°F LOW {low_temp}°F"
                    elif high_temp:
                        forecast_text += f", HIGH {high_temp}°F"
                    elif low_temp:
                        forecast_text += f", LOW {low_temp}°F"

                    self.scroller.add_item(forecast_text + " +++ ")

                # Add tonight's forecast if available
                if len(periods) > 1:
                    tonight = periods[1]
                    tonight_name = tonight.get('name', 'Tonight')
                    if 'tonight' in tonight_name.lower() or not tonight.get('isDaytime', True):
                        tonight_forecast = tonight.get('shortForecast', '')
                        tonight_temp = tonight.get('temperature', '')
                        if tonight_forecast:
                            tonight_text = f" +++ {tonight_name.upper()}: {tonight_forecast.upper()}"
                            if tonight_temp:
                                tonight_text += f", LOW {tonight_temp}°F"
                            self.scroller.add_item(tonight_text + " +++ ")

                # Add tomorrow's forecast if available
                if len(periods) > 2:
                    tomorrow = periods[2]
                    tomorrow_name = tomorrow.get('name', 'Tomorrow')
                    if 'tomorrow' in tomorrow_name.lower() or tomorrow.get('isDaytime', True):
                        tomorrow_forecast = tomorrow.get('shortForecast', '')
                        tomorrow_temp = tomorrow.get('temperature', '')
                        if tomorrow_forecast:
                            tomorrow_text = f" +++ {tomorrow_name.upper()}: {tomorrow_forecast.upper()}"
                            if tomorrow_temp:
                                tomorrow_text += f", HIGH {tomorrow_temp}°F"
                            self.scroller.add_item(tomorrow_text + " +++ ")

            # Add weather alerts placeholder (could be enhanced with actual alerts)
            self.scroller.add_item(" +++ NO WEATHER WARNINGS OR ADVISORIES IN EFFECT +++ ")

            # Add informational message
            self.scroller.add_item(" +++ VISIT WEATHER.GOV FOR THE LATEST WEATHER INFORMATION +++ ")

            # Initialize current text if empty
            if not self.scroller.current_text and self.scroller.text_items:
                self.scroller.current_text = self.scroller.text_items[0]

            logger.main_logger.info(f"Updated scroll text with {len(self.scroller.text_items)} items")

        except Exception as e:
            logger.main_logger.error(f"Error updating scroll text: {e}")

    def _get_wind_direction(self, degrees):
        """Convert wind degrees to compass direction"""
        if degrees is None:
            return ''
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                     'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        idx = int((degrees + 11.25) / 22.5) % 16
        return directions[idx]

    def draw_background(self, bg_name='1'):
        """Draw background image"""
        if bg_name in self.backgrounds:
            self.screen.blit(self.backgrounds[bg_name], (0, 0))
        else:
            bg = list(self.backgrounds.values())[0] if self.backgrounds else None
            if bg:
                self.screen.blit(bg, (0, 0))

    def draw_header(self, title_top, title_bottom=None, has_noaa=False):
        """Draw standard header matching ws4kp exact layout"""
        # Logo at exact position: top: 25px (moved up 5 pixels), left: 50px
        if 'logo-corner' in self.logos:
            self.screen.blit(self.logos['logo-corner'], (50, 25))

        # Title at exact position: left: 170px
        if title_bottom:
            # Dual line title - top: -3px (relative), bottom: 26px (relative)
            text1 = self.font_title.render(title_top.upper(), True, COLORS['yellow'])
            text2 = self.font_title.render(title_bottom.upper(), True, COLORS['yellow'])
            self.screen.blit(text1, (170, 27))  # Adjusted for absolute positioning
            self.screen.blit(text2, (170, 53))  # 26px below the first line
        else:
            # Single line title - top: 40px
            text = self.font_title.render(title_top.upper(), True, COLORS['yellow'])
            self.screen.blit(text, (170, 40))

        # NOAA logo at exact position: top: 39px, left: 356px
        if has_noaa and 'noaa' in self.logos:
            self.screen.blit(self.logos['noaa'], (356, 39))

        # Time at exact position: right-aligned, moved up 10px and right 5px
        time_str = datetime.now().strftime("%I:%M %p").lstrip('0')
        time_text = self.font_small.render(time_str, True, COLORS['white'])
        # Right-align at 590 (was 585+5), y=34 (was 44-10)
        time_rect = time_text.get_rect(right=590, y=34)
        self.screen.blit(time_text, time_rect)

        # Date below the time (authentic WeatherStar 4000 style)
        date_str = datetime.now().strftime("%a %b %d").upper()  # "WED OCT 02"
        date_text = self.font_small.render(date_str, True, COLORS['white'])
        # Right-align below the time at 590, y=54 (was 64-10)
        date_rect = date_text.get_rect(right=590, y=54)
        self.screen.blit(date_text, date_rect)

    def show_context_menu(self):
        """Show Windows 95-style menu on right-click"""
        # Classic Windows 95 colors
        WIN95_GREY = (192, 192, 192)  # Classic Windows grey
        WIN95_DARK = (128, 128, 128)  # Dark grey for shadows
        WIN95_LIGHT = (255, 255, 255)  # White for highlights
        WIN95_BLACK = (0, 0, 0)  # Black text
        WIN95_BLUE = (0, 0, 128)  # Selection blue
        WIN95_SELECTED = (10, 36, 106)  # Navy blue for selected items

        # Check for settings attribute
        if not hasattr(self, 'settings'):
            self.settings = {
                'show_marine': False,
                'units': 'F',
                'music_volume': 0.3,
                'show_trends': True,
                'show_historical': True,
                'show_msn': False,
                'show_reddit': False,
                'show_local_news': True,
                'use_international': False
            }

        # Create smaller, compact menu
        menu_width = 280
        menu_height = 320
        menu_surface = pygame.Surface((menu_width, menu_height))
        menu_surface.fill(WIN95_GREY)

        # Draw 3D raised border (Windows 95 style)
        # Top and left edges (light)
        pygame.draw.line(menu_surface, WIN95_LIGHT, (0, 0), (menu_width-1, 0), 2)
        pygame.draw.line(menu_surface, WIN95_LIGHT, (0, 0), (0, menu_height-1), 2)
        # Bottom and right edges (dark)
        pygame.draw.line(menu_surface, WIN95_DARK, (0, menu_height-1), (menu_width-1, menu_height-1), 2)
        pygame.draw.line(menu_surface, WIN95_DARK, (menu_width-1, 0), (menu_width-1, menu_height-1), 2)

        # Title bar with gradient effect
        title_height = 18
        title_rect = pygame.Rect(2, 2, menu_width-4, title_height)
        pygame.draw.rect(menu_surface, WIN95_SELECTED, title_rect)
        title_font = pygame.font.Font(None, 14)  # Smaller font
        title = title_font.render("WeatherStar Settings", True, WIN95_LIGHT)
        menu_surface.blit(title, (6, 5))

        # Menu categories with separators
        y_pos = 25
        item_font = pygame.font.Font(None, 13)  # Small Windows font

        # Category: Display Options
        category = item_font.render("Display Options", True, WIN95_BLACK)
        menu_surface.blit(category, (8, y_pos))
        y_pos += 16
        pygame.draw.line(menu_surface, WIN95_DARK, (8, y_pos), (menu_width-8, y_pos), 1)
        y_pos += 4

        menu_items = [
            ("[1] Marine Forecast", "show_marine", self.settings.get('show_marine', False)),
            ("[2] Weather Trends", "show_trends", self.settings.get('show_trends', True)),
            ("[3] Historical Data", "show_historical", self.settings.get('show_historical', True)),
            ("---", None, None),  # Separator
            ("Audio Settings", "category", None),
            ("[4] Music Volume", "volume", self.settings.get('music_volume', 0.3)),
            ("[0] Voice Narration", "voice_narration", self.settings.get('voice_narration', False)),
            ("---", None, None),  # Separator
            ("Weather Source", "category", None),
            ("[8] International Weather", "use_international", self.settings.get('use_international', False)),
            ("---", None, None),  # Separator
            ("Appearance", "category", None),
            ("[9] Color Theme", "theme", self.settings.get('theme', 'classic')),
            ("---", None, None),  # Separator
            ("News & Information", "category", None),
            ("[5] MSN Top Stories", "show_msn", self.settings.get('show_msn', False)),
            ("[6] Reddit Headlines", "show_reddit", self.settings.get('show_reddit', False)),
            ("[7] Local News", "show_local_news", self.settings.get('show_local_news', True)),
            ("---", None, None),  # Separator
            ("System", "category", None),
            ("[R] Refresh Weather", "refresh", None),
            ("[ESC] Close Menu", None, None)
        ]

        for text, setting, value in menu_items:
            if text == "---":
                # Draw separator line
                pygame.draw.line(menu_surface, WIN95_DARK, (8, y_pos+2), (menu_width-8, y_pos+2), 1)
                pygame.draw.line(menu_surface, WIN95_LIGHT, (8, y_pos+3), (menu_width-8, y_pos+3), 1)
                y_pos += 8
            elif setting == "category":
                # Category header
                cat_text = item_font.render(text, True, WIN95_BLACK)
                menu_surface.blit(cat_text, (8, y_pos))
                y_pos += 16
                pygame.draw.line(menu_surface, WIN95_DARK, (8, y_pos), (menu_width-8, y_pos), 1)
                y_pos += 4
            else:
                # Regular menu item with checkbox style
                item_x = 20
                # Draw checkbox for toggleable items
                if setting in ["show_marine", "show_trends", "show_historical", "show_msn", "show_reddit", "show_local_news", "use_international", "voice_narration"]:
                    # Draw checkbox
                    checkbox = pygame.Rect(item_x, y_pos, 11, 11)
                    pygame.draw.rect(menu_surface, WIN95_LIGHT, checkbox)
                    pygame.draw.rect(menu_surface, WIN95_BLACK, checkbox, 1)
                    # Draw inner shadow
                    pygame.draw.line(menu_surface, WIN95_DARK, (item_x+1, y_pos+1), (item_x+9, y_pos+1), 1)
                    pygame.draw.line(menu_surface, WIN95_DARK, (item_x+1, y_pos+1), (item_x+1, y_pos+9), 1)
                    # Draw checkmark if enabled
                    if value:
                        # Draw a checkmark
                        pygame.draw.lines(menu_surface, WIN95_BLACK, False,
                                        [(item_x+2, y_pos+5), (item_x+4, y_pos+7), (item_x+8, y_pos+3)], 2)
                    item_x += 15

                # Draw text
                if setting == "volume":
                    vol_pct = int(value * 100)
                    text = f"{text}: {vol_pct}%"
                elif setting == "theme":
                    theme_name = get_theme(value).name
                    text = f"{text}: {theme_name}"

                item_text = item_font.render(text, True, WIN95_BLACK)
                menu_surface.blit(item_text, (item_x, y_pos))
                y_pos += 18

        # Display menu centered on screen
        menu_x = (self.screen.get_width() - menu_width) // 2
        menu_y = (self.screen.get_height() - menu_height) // 2
        self.screen.blit(menu_surface, (menu_x, menu_y))
        pygame.display.flip()

        # Wait for input
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        waiting = False
                    elif event.key == pygame.K_1:
                        self.settings['show_marine'] = not self.settings.get('show_marine', False)
                        self.update_display_list()
                        logger.main_logger.info(f"Marine forecast: {self.settings['show_marine']}")
                        self.show_context_menu()  # Redraw menu
                        return
                    elif event.key == pygame.K_2:
                        self.settings['show_trends'] = not self.settings.get('show_trends', True)
                        logger.main_logger.info(f"Weather trends: {self.settings['show_trends']}")
                        self.show_context_menu()  # Redraw menu
                        return
                    elif event.key == pygame.K_3:
                        self.settings['show_historical'] = not self.settings.get('show_historical', True)
                        logger.main_logger.info(f"Historical data: {self.settings['show_historical']}")
                        self.show_context_menu()  # Redraw menu
                        return
                    elif event.key == pygame.K_4:
                        current_vol = self.settings.get('music_volume', 0.3)
                        new_vol = (current_vol + 0.1) % 1.1
                        if new_vol > 1.0:
                            new_vol = 0.0
                        self.settings['music_volume'] = new_vol
                        if self.music:
                            self.music.set_volume(new_vol)
                        logger.main_logger.info(f"Music volume: {int(new_vol * 100)}%")
                        self.show_context_menu()  # Redraw menu
                        return
                    elif event.key == pygame.K_5:
                        # Toggle MSN news
                        self.settings['show_msn'] = not self.settings.get('show_msn', False)
                        self.update_display_list()
                        logger.main_logger.info(f"MSN news: {self.settings['show_msn']}")
                        self.show_context_menu()  # Redraw menu
                        return
                    elif event.key == pygame.K_6:
                        # Toggle Reddit news
                        self.settings['show_reddit'] = not self.settings.get('show_reddit', False)
                        self.update_display_list()
                        logger.main_logger.info(f"Reddit news: {self.settings['show_reddit']}")
                        self.show_context_menu()  # Redraw menu
                        return
                    elif event.key == pygame.K_7:
                        # Toggle Local news
                        self.settings['show_local_news'] = not self.settings.get('show_local_news', True)
                        self.update_display_list()
                        logger.main_logger.info(f"Local news: {self.settings['show_local_news']}")
                        self.show_context_menu()  # Redraw menu
                        return
                    elif event.key == pygame.K_8:
                        # Toggle International Weather (Open Meteo API)
                        self.settings['use_international'] = not self.settings.get('use_international', False)
                        self.get_weather_data()  # Refresh with new API
                        api_name = "Open Meteo (International)" if self.settings['use_international'] else "NOAA (US Only)"
                        logger.main_logger.info(f"Weather API: {api_name}")
                        self.show_context_menu()  # Redraw menu
                        return
                    elif event.key == pygame.K_9:
                        # Cycle through color themes
                        themes = list_themes()
                        current_theme = self.settings.get('theme', 'classic')
                        current_index = themes.index(current_theme) if current_theme in themes else 0
                        next_index = (current_index + 1) % len(themes)
                        self.settings['theme'] = themes[next_index]
                        self.current_theme = get_theme(themes[next_index])
                        logger.main_logger.info(f"Color theme: {self.current_theme.name}")
                        self.show_context_menu()  # Redraw menu
                        return
                    elif event.key == pygame.K_0:
                        # Toggle voice narration
                        self.settings['voice_narration'] = not self.settings.get('voice_narration', False)
                        self.narrator.set_enabled(self.settings['voice_narration'])
                        status = "enabled" if self.settings['voice_narration'] else "disabled"
                        logger.main_logger.info(f"Voice narration: {status}")
                        if self.settings['voice_narration'] and self.narrator.is_available():
                            # Test announcement
                            self.narrator._speak_async("Voice narration enabled.")
                        self.show_context_menu()  # Redraw menu
                        return
                    elif event.key == pygame.K_r:
                        self.get_weather_data()
                        logger.main_logger.info("Weather data refreshed")
                        waiting = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Click to close menu
                    mouse_x, mouse_y = event.pos
                    if not (menu_x <= mouse_x <= menu_x + menu_width and menu_y <= mouse_y <= menu_y + menu_height):
                        waiting = False

    def draw_severe_weather_alert(self, dt):
        """Draw animated severe weather alert"""
        display_history.draw_severe_weather_alert(self, dt)

    def _duck_music_volume(self):
        """Lower background music volume for voice narration (90s style)"""
        try:
            # Store current volume
            self.original_music_volume = pygame.mixer.music.get_volume()
            # Duck to 20% (low but still present - authentic to 90s weather broadcasts)
            pygame.mixer.music.set_volume(0.20)
            logger.main_logger.debug("Music ducked for voice narration")
        except Exception as e:
            logger.log_error("Error ducking music volume", e)

    def _restore_music_volume(self):
        """Restore background music volume after voice narration"""
        try:
            # Restore to original volume
            pygame.mixer.music.set_volume(self.original_music_volume)
            logger.main_logger.debug("Music volume restored")
        except Exception as e:
            logger.log_error("Error restoring music volume", e)

    def update_display_list(self):
        """Update display list based on settings"""
        # Authentic WeatherStar 4000 display sequence (90s style)
        base_displays = [
            DisplayMode.CURRENT_CONDITIONS,     # 1. Current Conditions
            DisplayMode.REGIONAL_OBSERVATIONS,  # 2. Latest Observations
            DisplayMode.HOURLY_FORECAST,       # 3. 12/24 Hour Forecast
            DisplayMode.EXTENDED_FORECAST,     # 4. Extended Forecast
            DisplayMode.RADAR,                 # 5. Local Radar
            DisplayMode.TRAVEL_CITIES,         # 6. Travel Cities Weather
            DisplayMode.ALMANAC,               # 7. Almanac
            DisplayMode.TEMPERATURE_HISTORY,   # 8. 30-Day Temperature History
            DisplayMode.PRECIPITATION_HISTORY, # 9. 30-Day Precipitation History
            DisplayMode.UV_INDEX,              # 10. UV Index Forecast
            DisplayMode.EARTHQUAKES,           # 11. Recent Earthquakes
            DisplayMode.STOCK_MARKET,          # 12. Stock Market Indices
        ]

        # Add optional displays only if enabled (keep it simple by default)
        if self.settings.get('show_marine', False):
            base_displays.append(DisplayMode.MARINE_FORECAST)

        # News displays (optional for authenticity)
        if self.settings.get('show_msn', False):
            base_displays.append(DisplayMode.MSN_NEWS)
        if self.settings.get('show_reddit', False):
            base_displays.append(DisplayMode.REDDIT_NEWS)
        if self.settings.get('show_local_news', False):
            base_displays.append(DisplayMode.LOCAL_NEWS)

        self.display_list = base_displays
        self.displays = [mode for mode in self.display_list if mode != DisplayMode.PROGRESS]








    def cycle_display(self):
        """Cycle to next display - simple 90s style"""
        old_mode = self.displays[self.current_display_index]
        self.current_display_index = (self.current_display_index + 1) % len(self.displays)
        new_mode = self.displays[self.current_display_index]
        self.display_timer = 0
        logger.log_display_change(old_mode.value, new_mode.value)

        # Voice narration for new display (if enabled)
        if self.settings.get('voice_narration', False):
            self.narrator.set_enabled(True)
            self.narrator.announce_display(new_mode.value, self.weather_data)

    def run(self):
        """Main application loop"""
        logger.main_logger.info("Starting main loop")

        # Initialize location quickly
        if not self.initialize_location():
            logger.main_logger.error("Failed to initialize location, exiting")
            return

        # Start with minimal data - just get current conditions quickly
        self.weather_data = {'properties': {}}  # Initialize empty

        # Start background thread to load weather data
        def load_data_background():
            logger.main_logger.info("Loading weather data in background thread...")
            self.update_weather_data()
            self._update_scroll_text()
            logger.main_logger.info("Background data loading complete")

        data_thread = threading.Thread(target=load_data_background, daemon=True)
        data_thread.start()

        # Show first page immediately while loading
        running = True
        last_update = time.time()  # Set to current time so we don't immediately update again
        frame_count = 0

        try:
            while running:
                frame_count += 1
                dt = self.clock.tick(30)  # 30 FPS

                # Update performance optimizer
                self.perf_optimizer.update(target_fps=30)

                # Skip frame if performance is poor (Pi optimization)
                if self.perf_optimizer.should_skip_frame():
                    continue

                self.display_timer += dt

                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        logger.main_logger.info("Quit event received")
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 3:  # Right click
                            logger.main_logger.info("Right-click menu opened")
                            self.show_context_menu()
                        elif event.button == 1:  # Left click
                            # Check if clicking on a news headline
                            if hasattr(self, 'clickable_headlines'):
                                mouse_pos = event.pos
                                for headline_info in self.clickable_headlines:
                                    # Handle dict format from news_displays.py
                                    if isinstance(headline_info, dict):
                                        rect = headline_info.get('rect')
                                        url = headline_info.get('url')
                                        if rect and rect.collidepoint(mouse_pos):
                                            logger.main_logger.info(f"Opening URL: {url}")
                                            try:
                                                webbrowser.open(url)
                                            except Exception as e:
                                                logger.main_logger.error(f"Failed to open URL: {e}")
                                            break
                                    else:
                                        # Handle tuple format (legacy)
                                        try:
                                            rect, url = headline_info
                                            if rect.collidepoint(mouse_pos):
                                                logger.main_logger.info(f"Opening URL: {url}")
                                                webbrowser.open(url)
                                                break
                                        except:
                                            pass
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            logger.main_logger.info("Escape key pressed")
                            running = False
                        elif event.key == pygame.K_SPACE:
                            self.is_playing = not self.is_playing
                            logger.main_logger.info(f"Play/pause toggled: playing={self.is_playing}")
                        elif event.key == pygame.K_RIGHT:
                            self.cycle_display()
                        elif event.key == pygame.K_LEFT:
                            old_mode = self.displays[self.current_display_index]
                            self.current_display_index = (self.current_display_index - 1) % len(self.displays)
                            new_mode = self.displays[self.current_display_index]
                            logger.log_display_change(old_mode.value, new_mode.value)
                            self.display_timer = 0
                        elif event.key == pygame.K_m:  # M key for menu
                            logger.main_logger.info("M key pressed - opening menu")
                            self.show_context_menu()

                # Auto-cycle displays
                if self.is_playing and self.display_timer >= DISPLAY_DURATION_MS:
                    self.cycle_display()

                # Update weather data every 5 minutes
                if time.time() - last_update > 300:
                    logger.main_logger.info("5-minute weather update")
                    self.update_weather_data()
                    last_update = time.time()

                # Draw current display
                current_mode = self.displays[self.current_display_index]

                try:
                    # Use modular display methods
                    if current_mode == DisplayMode.CURRENT_CONDITIONS:
                        if self.displays_module:
                            self.displays_module.draw_current_conditions()
                    elif current_mode == DisplayMode.LOCAL_FORECAST:
                        if self.displays_module:
                            self.displays_module.draw_local_forecast()
                    elif current_mode == DisplayMode.EXTENDED_FORECAST:
                        if self.displays_module:
                            self.displays_module.draw_extended_forecast()
                    elif current_mode == DisplayMode.HOURLY_FORECAST:
                        if self.displays_module:
                            self.displays_module.draw_hourly_forecast()
                    elif current_mode == DisplayMode.REGIONAL_OBSERVATIONS:
                        if self.displays_module:
                            self.displays_module.draw_latest_observations()
                    elif current_mode == DisplayMode.TRAVEL_CITIES:
                        if self.displays_module:
                            self.displays_module.draw_travel_cities()
                    elif current_mode == DisplayMode.MARINE_FORECAST:
                        if self.displays_module:
                            self.displays_module.draw_marine_forecast()
                    elif current_mode == DisplayMode.AIR_QUALITY:
                        if self.displays_module:
                            self.displays_module.draw_air_quality()
                    elif current_mode == DisplayMode.TEMPERATURE_GRAPH:
                        if self.displays_module:
                            self.displays_module.draw_temperature_graph()
                    elif current_mode == DisplayMode.WEATHER_RECORDS:
                        if self.displays_module:
                            self.displays_module.draw_weather_records()
                    elif current_mode == DisplayMode.SUN_MOON:
                        if self.displays_module:
                            self.displays_module.draw_sun_moon()
                    elif current_mode == DisplayMode.WIND_PRESSURE:
                        if self.displays_module:
                            self.displays_module.draw_wind_pressure()
                    elif current_mode == DisplayMode.WEEKEND_FORECAST:
                        if self.displays_module:
                            self.displays_module.draw_weekend_forecast()
                    elif current_mode == DisplayMode.MONTHLY_OUTLOOK:
                        if self.displays_module:
                            self.displays_module.draw_monthly_outlook()
                    elif current_mode == DisplayMode.MSN_NEWS:
                        if self.news_module:
                            self.news_module.draw_msn_news()
                    elif current_mode == DisplayMode.REDDIT_NEWS:
                        if self.news_module:
                            self.news_module.draw_reddit_news()
                    elif current_mode == DisplayMode.LOCAL_NEWS:
                        if self.news_module:
                            self.news_module.draw_local_news()
                    elif current_mode == DisplayMode.ALMANAC:
                        if self.displays_module:
                            self.displays_module.draw_almanac()
                    elif current_mode == DisplayMode.HAZARDS:
                        if self.displays_module:
                            self.displays_module.draw_hazards()
                    elif current_mode == DisplayMode.RADAR:
                        if self.displays_module:
                            self.displays_module.draw_radar()
                    elif current_mode == DisplayMode.TEMPERATURE_HISTORY:
                        # Draw 30-Day Temperature History
                        if self.displays_module:
                            self.displays_module.draw_temperature_history()
                    elif current_mode == DisplayMode.PRECIPITATION_HISTORY:
                        # Draw 30-Day Precipitation History
                        if self.displays_module:
                            self.displays_module.draw_precipitation_history()
                    elif current_mode == DisplayMode.UV_INDEX:
                        # Draw UV Index Forecast
                        if self.displays_module:
                            self.displays_module.draw_uv_index()
                    elif current_mode == DisplayMode.EARTHQUAKES:
                        # Draw Recent Earthquakes
                        if self.displays_module:
                            self.displays_module.draw_recent_earthquakes()
                    elif current_mode == DisplayMode.STOCK_MARKET:
                        # Draw Stock Market Indices
                        if self.displays_module:
                            self.displays_module.draw_stock_market()
                    elif current_mode == DisplayMode.SEVERE_WEATHER_ALERT:
                        # NEW: Animated severe weather alert
                        self.draw_severe_weather_alert(dt / 1000.0)
                    else:
                        # Fallback
                        self.draw_background('1')
                        self.draw_header(current_mode.value.replace('-', ' ').title())
                except Exception as e:
                    logger.log_error(f"Error drawing {current_mode.value}", e)

                # Always draw scrolling text
                if self.displays_module:
                    self.displays_module.draw_scrolling_text()

                # Simple display updates - no complex transitions

                # Update display
                pygame.display.flip()

                # Log performance every 1000 frames
                if frame_count % 1000 == 0:
                    logger.main_logger.debug(f"Frame {frame_count}, FPS: {self.clock.get_fps():.1f}")

        except Exception as e:
            logger.log_error("Fatal error in main loop", e)
        finally:
            logger.log_shutdown()
            pygame.quit()

            # Print log summary
            print("\n" + "=" * 60)
            print("Session Logs:")
            for key, value in logger.get_log_summary().items():
                print(f"  {key}: {value}")
            print("=" * 60)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='WeatherStar 4000+ with Logging')
    parser.add_argument('--lat', type=float, default=None, help='Latitude (auto-detect if not specified)')
    parser.add_argument('--lon', type=float, default=None, help='Longitude (auto-detect if not specified)')
    parser.add_argument('--log-level', default='DEBUG',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')

    args = parser.parse_args()

    # Set logging level
    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }

    # Re-initialize logger with specified level
    global logger
    logger = init_logger(log_level=log_levels[args.log_level])

    try:
        ws = WeatherStar4000Complete(args.lat, args.lon)
        ws.run()
    except Exception as e:
        logger.log_error("Failed to start WeatherStar", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
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

# Import our custom logger
from weatherstar_logger import init_logger, get_logger

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
            'show_historical': True
        }

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
        self._load_icons()
        self.logos = self._load_logos()

        # Initialize fonts
        self._init_fonts()

        # Initialize music
        self._init_music()

        # Transition effects
        self.transition_alpha = 255  # For fade transitions
        self.transition_active = False
        self.transition_surface = None

        # API client
        self.api = NOAAWeatherAPI()

        # Weather data
        self.weather_data = {}
        self.location = {}
        self.lat = lat
        self.lon = lon

        # Display management
        self.displays = self._init_displays()
        self.current_display_index = 0
        self.display_timer = 0
        self.is_playing = True

        # Scrolling text
        self.scroller = ScrollingText(self.font_scroller if hasattr(self, 'font_scroller') else self.font_small)

        # Initialize weather data
        self.point_data = None
        self.station = None
        self.office = None
        self.gridX = None
        self.gridY = None

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
        """Load weather icons"""
        icons_path = self.assets_path / "icons"
        logger.main_logger.info(f"Loading icons from {icons_path}")

        if icons_path.exists():
            icon_count = 0
            for icon_file in icons_path.glob("*.gif"):
                try:
                    name = icon_file.stem
                    self.icons[name] = pygame.image.load(str(icon_file))
                    logger.log_asset_load("icon", name, True)
                    icon_count += 1
                except Exception as e:
                    logger.log_asset_load("icon", str(icon_file), False)
                    logger.log_error(f"Error loading icon {icon_file}", e)

            logger.main_logger.info(f"Loaded {icon_count} icons")
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
                self.font_small = pygame.font.Font(str(star4000_small_path), 32)
                self.font_normal = pygame.font.Font(str(star4000_path), 20)
                self.font_scroller = pygame.font.Font(str(star4000_extended_path), 24)  # Sized to fit in banner
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
            self.font_small = pygame.font.Font(pygame.font.match_font(selected_font, bold=False), 32)  # Star4000 Small
            self.font_scroller = pygame.font.Font(pygame.font.match_font(selected_font, bold=True), 24)  # Sized to fit in banner
            logger.main_logger.debug(f"Fonts initialized with {selected_font}")
        else:
            logger.main_logger.warning("No suitable font found, using defaults")
            self.font_title = pygame.font.Font(None, 32)
            self.font_large = pygame.font.Font(None, 32)
            self.font_extended = pygame.font.Font(None, 32)
            self.font_normal = pygame.font.Font(None, 20)
            self.font_small = pygame.font.Font(None, 32)
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

        # Time at exact position: left: 415px, right-aligned within 170px width
        time_str = datetime.now().strftime("%I:%M %p").lstrip('0')
        time_text = self.font_small.render(time_str, True, COLORS['white'])
        # Right-align within the box from 415 to 585 (415 + 170)
        time_rect = time_text.get_rect(right=585, y=44)
        self.screen.blit(time_text, time_rect)

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
                'show_reddit': False
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
            ("---", None, None),  # Separator
            ("News & Information", "category", None),
            ("[5] MSN Top Stories", "show_msn", self.settings.get('show_msn', False)),
            ("[6] Reddit Headlines", "show_reddit", self.settings.get('show_reddit', False)),
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
                if setting in ["show_marine", "show_trends", "show_historical", "show_msn", "show_reddit"]:
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
                    elif event.key == pygame.K_r:
                        self.get_weather_data()
                        logger.main_logger.info("Weather data refreshed")
                        waiting = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Click to close menu
                    mouse_x, mouse_y = event.pos
                    if not (menu_x <= mouse_x <= menu_x + menu_width and menu_y <= mouse_y <= menu_y + menu_height):
                        waiting = False

    def update_display_list(self):
        """Update display list based on settings"""
        # Rebuild display list
        base_displays = [
            DisplayMode.CURRENT_CONDITIONS,
            DisplayMode.EXTENDED_FORECAST,
            DisplayMode.HOURLY_FORECAST,
            DisplayMode.REGIONAL_OBSERVATIONS,
            DisplayMode.TRAVEL_CITIES,
            DisplayMode.LOCAL_FORECAST,
            DisplayMode.ALMANAC,
            DisplayMode.RADAR,
            DisplayMode.HAZARDS,
            DisplayMode.AIR_QUALITY,
            DisplayMode.TEMPERATURE_GRAPH,
            DisplayMode.WEATHER_RECORDS,
            DisplayMode.SUN_MOON,
            DisplayMode.WIND_PRESSURE,
            DisplayMode.WEEKEND_FORECAST,
            DisplayMode.MONTHLY_OUTLOOK,
        ]

        # Add optional displays based on settings
        if self.settings.get('show_marine', False):
            base_displays.insert(9, DisplayMode.MARINE_FORECAST)

        # Add news displays if enabled
        if self.settings.get('show_msn', False):
            base_displays.append(DisplayMode.MSN_NEWS)
        if self.settings.get('show_reddit', False):
            base_displays.append(DisplayMode.REDDIT_NEWS)

        self.display_list = base_displays
        self.displays = [mode for mode in self.display_list if mode != DisplayMode.PROGRESS]

    def draw_msn_news(self):
        """Display MSN news headlines with scrolling"""
        self.draw_background('1')
        self.draw_header("MSN", "Top Stories")

        # Fetch MSN headlines (simulated for now - in production would fetch real news)
        headlines = [
            "Breaking: Major Winter Storm System Moving Across United States Bringing Heavy Snow and Ice",
            "Technology: Apple Announces Revolutionary New Product Line at Annual Developer Conference",
            "Sports: Underdog Team Wins Championship in Dramatic Overtime Victory Against All Odds",
            "World News: Global Climate Summit Concludes with Historic Agreement Among Nations",
            "Business: Stock Market Reaches All-Time High as Economic Recovery Continues to Accelerate",
            "Entertainment: Surprise Winners at Annual Award Show Leave Audiences Stunned",
            "Health: Scientists Announce Major Medical Breakthrough in Cancer Research Treatment",
            "Science: Space Mission Successfully Launches New Era of Deep Space Exploration",
            "Politics: Congress Passes Landmark Legislation with Bipartisan Support",
            "Local: Community Rallies Together to Support Families Affected by Recent Events",
            "Weather: Hurricane Season Expected to Be More Active Than Normal This Year",
            "Technology: Artificial Intelligence Breakthrough Could Transform Daily Life"
        ]

        self._display_scrolling_headlines(headlines, "msn")
        logger.main_logger.debug("Drew MSN news display")

    def draw_reddit_news(self):
        """Display Reddit news headlines with scrolling"""
        self.draw_background('1')
        self.draw_header("Reddit", "Headlines")

        # Fetch Reddit headlines (simulated for now - in production would use Reddit API)
        headlines = [
            "r/news: Major Storm System Approaching East Coast with Potential for Historic Snowfall Amounts",
            "r/worldnews: International Summit Concludes with Unexpected Alliance Between Former Rivals",
            "r/technology: New AI Breakthrough Could Revolutionize How We Interact with Computers",
            "r/science: Scientists Discover New Species in Previously Unexplored Deep Ocean Trench",
            "r/gaming: Popular Game Franchise Gets Surprise Major Update After Years of Silence",
            "r/movies: Independent Film Breaks Box Office Records in Limited Release",
            "r/sports: Underdog Team's Cinderella Story Continues with Another Upset Victory",
            "r/space: New Images from James Webb Space Telescope Reveal Stunning Cosmic Phenomena",
            "r/AskReddit: What's the most interesting historical fact you know that sounds fake?",
            "r/todayilearned: TIL that honey never spoils and archaeologists have found 3000 year old honey",
            "r/EarthPorn: Sunrise over the Grand Canyon after fresh snowfall [OC] [4032x3024]",
            "r/dataisbeautiful: [OC] Visualization of global temperature changes over the last century"
        ]

        self._display_scrolling_headlines(headlines, "reddit")
        logger.main_logger.debug("Drew Reddit news display")

    def _display_scrolling_headlines(self, headlines, source):
        """Display news with vertical scrolling from bottom"""
        # Initialize vertical scroll position if not exists
        if not hasattr(self, 'news_vertical_scroll'):
            self.news_vertical_scroll = {}

        if source not in self.news_vertical_scroll:
            self.news_vertical_scroll[source] = 480  # Start from bottom of screen

        # Use readable font
        try:
            news_font = pygame.font.Font(self.font_paths.get('small'), 20)
            title_font = pygame.font.Font(self.font_paths.get('normal'), 22)
        except:
            news_font = pygame.font.Font(None, 20)
            title_font = pygame.font.Font(None, 22)

        # Create clipping region for scrolling area
        clip_rect = pygame.Rect(40, 100, 560, 320)
        self.screen.set_clip(clip_rect)

        # Calculate total height needed for all headlines
        line_height = 28
        headline_spacing = 15  # Extra space between headlines

        # Draw headlines scrolling up
        y_pos = self.news_vertical_scroll[source]

        for i, headline in enumerate(headlines[:20], 1):  # Show up to 20 headlines
            # Only draw if potentially visible
            if y_pos > -100 and y_pos < 500:
                # Number in yellow
                num_text = title_font.render(f"{i}.", True, COLORS['yellow'])
                self.screen.blit(num_text, (50, y_pos))

                # Word-wrap the headline for better readability
                words = headline.split()
                lines = []
                current_line = ""

                for word in words:
                    test_line = current_line + " " + word if current_line else word
                    test_surface = news_font.render(test_line, True, COLORS['white'])

                    if test_surface.get_width() > 500:  # Max width for text
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                    else:
                        current_line = test_line

                if current_line:
                    lines.append(current_line)

                # Draw wrapped lines
                line_y = y_pos
                for line in lines:
                    if line_y > 80 and line_y < 420:  # Only draw visible lines
                        text_surface = news_font.render(line, True, COLORS['white'])
                        self.screen.blit(text_surface, (80, line_y))
                    line_y += line_height

                # Move to next headline position
                y_pos = line_y + headline_spacing
            else:
                # Still calculate position even if not drawing
                y_pos += line_height * 2 + headline_spacing

        # Remove clipping
        self.screen.set_clip(None)

        # Update scroll position (slow upward scroll)
        self.news_vertical_scroll[source] -= 0.5  # Slow scroll speed

        # Reset when all headlines have scrolled past
        if y_pos < 80:
            self.news_vertical_scroll[source] = 480

        # Footer with update time (outside clipping area)
        update_time = datetime.now().strftime("%I:%M %p")
        footer = news_font.render(f"Updated: {update_time}", True, COLORS['yellow'])
        footer_rect = footer.get_rect(center=(320, 440))
        self.screen.blit(footer, footer_rect)

    def _display_news_headlines(self, headlines):
        """Legacy helper to display news headlines (deprecated)"""
        y_pos = 120
        for i, headline in enumerate(headlines[:10], 1):
            # Number
            num_text = self.font_small.render(f"{i}.", True, COLORS['yellow'])
            self.screen.blit(num_text, (60, y_pos))

            # Headline (truncate if too long)
            if len(headline) > 60:
                headline = headline[:57] + "..."
            headline_text = self.font_small.render(headline, True, COLORS['white'])
            self.screen.blit(headline_text, (85, y_pos))

            y_pos += 28

    def show_news_display(self, source):
        """Display news headlines from MSN or Reddit (deprecated - use draw_msn_news or draw_reddit_news)"""
        self.draw_background('1')

        if source == 'msn':
            self.draw_header("MSN", "Top Stories")
            # Fetch MSN headlines (simulated for now)
            headlines = [
                "Breaking: Major Weather System Moving Across US",
                "Tech: Apple Announces New Product Line",
                "Sports: Championship Game Results",
                "World: Global Climate Summit Begins",
                "Business: Stock Market Reaches New High",
                "Entertainment: Award Show Winners Announced",
                "Health: New Medical Breakthrough Reported",
                "Science: Space Mission Successfully Launches"
            ]
        else:  # reddit
            self.draw_header("Reddit", "Headlines")
            # Fetch Reddit headlines (simulated for now)
            headlines = [
                "r/news: Major Storm System Approaching East Coast",
                "r/worldnews: International Summit Concludes",
                "r/technology: New AI Breakthrough Announced",
                "r/science: Scientists Discover New Species",
                "r/gaming: Popular Game Gets Major Update",
                "r/movies: Box Office Records Broken",
                "r/sports: Underdog Team Wins Championship",
                "r/space: New Images from Space Telescope"
            ]

        # Display headlines
        y_pos = 120
        for i, headline in enumerate(headlines[:10], 1):
            # Number
            num_text = self.font_small.render(f"{i}.", True, COLORS['yellow'])
            self.screen.blit(num_text, (60, y_pos))

            # Headline (truncate if too long)
            if len(headline) > 60:
                headline = headline[:57] + "..."
            headline_text = self.font_small.render(headline, True, COLORS['white'])
            self.screen.blit(headline_text, (85, y_pos))

            y_pos += 28

        # Footer with update time
        footer_text = self.font_small.render("Press any key to return", True, COLORS['yellow'])
        footer_rect = footer_text.get_rect(center=(320, 420))
        self.screen.blit(footer_text, footer_rect)

        pygame.display.flip()

        # Wait for key press to return
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False

        logger.main_logger.info(f"Displayed {source} news")

    def fetch_real_news(self, source):
        """Fetch real news headlines from APIs (future enhancement)"""
        # This would use requests to fetch real headlines
        # For MSN: Could scrape or use news API
        # For Reddit: Use Reddit API or PRAW library
        pass

    def draw_current_conditions(self):
        """Draw Current Conditions screen matching ws4kp exact layout"""
        self.draw_background('1')
        self.draw_header("Current", "Conditions", has_noaa=True)

        current = self.weather_data.get('current', {})
        if not current:
            logger.main_logger.debug("No current data to display")
            return

        # Main content area has 64px margins on each side (has-box class)
        # So actual content width is 640 - 128 = 512px
        # Left column is 255px, right column is 255px (with 2px gap)
        content_left = 64  # Start of content area

        # LEFT COLUMN: starts at x=64, width=255px
        left_col_center = content_left + 127  # Center of left column

        # Temperature (large, top of column)
        temp_c = current.get('temperature', {}).get('value')
        if temp_c is not None:
            temp_f = int(temp_c * 9/5 + 32)
            temp_text = self.font_large.render(f"{temp_f}°", True, COLORS['white'])
            temp_rect = temp_text.get_rect(center=(left_col_center, 140))
            self.screen.blit(temp_text, temp_rect)

        # Weather condition (below temp)
        description = current.get('textDescription', '')
        if description:
            # Shorten if too long
            if len(description) > 15:
                description = description[:15]
            desc_text = self.font_extended.render(description, True, COLORS['white'])
            desc_rect = desc_text.get_rect(center=(left_col_center, 190))
            self.screen.blit(desc_text, desc_rect)

        # Weather icon (centered below condition)
        icon_name = self._get_icon_name(current.get('icon', ''))
        if icon_name and icon_name in self.icons:
            icon = self.icons[icon_name]
            icon_rect = icon.get_rect(center=(left_col_center, 260))
            self.screen.blit(icon, icon_rect)

        # Wind information with flex layout
        wind_y = 320
        wind_speed = current.get('windSpeed', {}).get('value')
        wind_dir = current.get('windDirection', {}).get('value')

        # Wind container - flex with 50% each side
        wind_label = self.font_extended.render("Wind:", True, COLORS['white'])
        self.screen.blit(wind_label, (content_left + 10, wind_y))  # margin-left: 10px

        if wind_speed is not None:
            if wind_speed == 0:
                wind_str = "Calm"
            else:
                wind_mph = int(wind_speed * 0.621371)
                direction = self._get_wind_direction(wind_dir) if wind_dir else ''
                # Format like ws4kp: direction padded to 3, speed right-aligned to 3
                wind_str = f"{direction.ljust(3)}{str(wind_mph).rjust(3)}"

            wind_text = self.font_extended.render(wind_str, True, COLORS['white'])
            # Right side of flex container
            wind_rect = wind_text.get_rect(right=content_left + 245, y=wind_y)
            self.screen.blit(wind_text, wind_rect)

        # Wind gusts (right-aligned below wind)
        wind_gust = current.get('windGust', {}).get('value')
        if wind_gust is not None:
            gust_mph = int(wind_gust * 0.621371)
            gust_text = self.font_normal.render(f"Gusts to {gust_mph}", True, COLORS['white'])
            gust_rect = gust_text.get_rect(right=content_left + 245, y=wind_y + 35)
            self.screen.blit(gust_text, gust_rect)

        # RIGHT COLUMN: starts at 64 + 257 = 321px from left edge
        right_col_x = content_left + 257  # Small gap between columns
        label_x = right_col_x + 20  # Labels have margin-left: 20px
        value_x = 640 - 64 - 10  # Right edge minus margin minus 10px

        # Location in yellow at top
        y_pos = 100
        location_str = f"{self.location.get('city', '')}".strip()[:20]  # Max 20 chars
        if location_str:
            location_text = self.font_normal.render(location_str, True, COLORS['yellow'])
            self.screen.blit(location_text, (right_col_x, y_pos))
            y_pos += 34  # margin-bottom: 10px + line-height: 24px

        # Data rows with labels and values
        row_data = []

        # Humidity
        humidity = current.get('relativeHumidity', {}).get('value')
        if humidity is not None:
            row_data.append(("Humidity:", f"{int(humidity)}%"))

        # Dewpoint
        dewpoint_c = current.get('dewpoint', {}).get('value')
        if dewpoint_c is not None:
            dewpoint_f = int(dewpoint_c * 9/5 + 32)
            row_data.append(("Dewpoint:", f"{dewpoint_f}°"))

        # Ceiling (cloud base height)
        cloud_layers = current.get('cloudLayers', [])
        ceiling = None
        if cloud_layers:
            # Find the lowest broken or overcast layer
            for layer in cloud_layers:
                if layer.get('amount') in ['BKN', 'OVC']:
                    height = layer.get('base', {}).get('value')
                    if height is not None:
                        ceiling = int(height * 3.28084)  # Convert meters to feet
                        break

        if ceiling is None or ceiling == 0:
            ceiling_str = "Unlimited"
        else:
            ceiling_str = f"{ceiling} ft"
        row_data.append(("Ceiling:", ceiling_str))

        # Visibility
        visibility = current.get('visibility', {}).get('value')
        if visibility is not None:
            vis_miles = visibility * 0.000621371
            if vis_miles >= 10:
                vis_str = "10 mi"
            else:
                vis_str = f"{vis_miles:.1f} mi"
            row_data.append(("Visibility:", vis_str))

        # Pressure with trend
        pressure = current.get('barometricPressure', {}).get('value')
        if pressure is not None:
            pressure_inhg = pressure * 0.0002953

            # Calculate pressure trend if enabled
            pressure_trend = ""
            if hasattr(self, 'settings') and self.settings.get('show_trends', True):
                if not hasattr(self, 'weather_trends'):
                    self.weather_trends = {'temp': [], 'pressure': []}

                self.weather_trends['pressure'].append(pressure_inhg)
                if len(self.weather_trends['pressure']) > 5:
                    self.weather_trends['pressure'].pop(0)

                if len(self.weather_trends['pressure']) >= 2:
                    pressure_change = self.weather_trends['pressure'][-1] - self.weather_trends['pressure'][0]
                    if pressure_change > 0.02:
                        pressure_trend = "↑"  # Rising
                    elif pressure_change < -0.02:
                        pressure_trend = "↓"  # Falling
                    else:
                        pressure_trend = "→"  # Steady

            row_data.append(("Pressure:", f"{pressure_inhg:.2f}\" {pressure_trend}".strip()))

        # Heat Index or Wind Chill
        heat_index = current.get('heatIndex', {}).get('value')
        wind_chill = current.get('windChill', {}).get('value')

        if heat_index is not None and temp_c is not None and temp_c > 26:  # Only show if > 80°F
            heat_f = int(heat_index * 9/5 + 32)
            row_data.append(("Heat Index:", f"{heat_f}°"))
        elif wind_chill is not None and temp_c is not None and temp_c < 10:  # Only show if < 50°F
            chill_f = int(wind_chill * 9/5 + 32)
            row_data.append(("Wind Chill:", f"{chill_f}°"))

        # Draw all the data rows with ws4kp spacing
        # margin-bottom: 12px between rows, line-height: 24px
        for label, value in row_data:
            # Label with margin-left: 20px
            label_text = self.font_normal.render(label, True, COLORS['white'])
            self.screen.blit(label_text, (label_x, y_pos))

            # Value right-aligned with margin-right: 10px
            value_text = self.font_normal.render(value, True, COLORS['white'])
            value_rect = value_text.get_rect(right=value_x, y=y_pos)
            self.screen.blit(value_text, value_rect)

            y_pos += 36  # line-height: 24px + margin-bottom: 12px

    def draw_local_forecast(self):
        """Draw Local Forecast screen with 3-day forecast layout"""
        self.draw_background('2')
        self.draw_header("Local", "Forecast", has_noaa=True)

        forecast = self.weather_data.get('forecast', {})
        periods = forecast.get('periods', [])

        if len(periods) < 3:
            return

        # Three column layout for 3 different days
        total_width = 640
        col_width = 180  # Width of each column
        col_spacing = 30  # Space between columns
        total_cols_width = (col_width * 3) + (col_spacing * 2)

        # Center the 3-column block
        start_x = (total_width - total_cols_width) // 2

        # Column positions
        columns = [
            start_x,
            start_x + col_width + col_spacing,
            start_x + (col_width + col_spacing) * 2
        ]

        # Process first 3 periods (Today, Tomorrow, Day after)
        for col_idx, period in enumerate(periods[:3]):
            col_x = columns[col_idx]

            # Day name header in yellow
            name = period.get('name', '')
            # Format day names based on position and content
            if col_idx == 0:
                # First column is always today/tonight
                if 'Tonight' in name or 'Overnight' in name or 'Night' in name.split()[-1]:
                    display_name = 'TONIGHT'
                else:
                    display_name = 'TODAY'
            elif col_idx == 1:
                # Second column is tomorrow
                display_name = 'TOMORROW'
            else:
                # Third column - get the actual day name from period name
                # Period names are like "Tuesday", "Tuesday Night", "Wednesday", etc.
                day_name = name.replace(' Night', '').replace(' Afternoon', '').replace(' Morning', '')
                display_name = day_name.upper()[:9]  # Limit to 9 chars

            # Draw day name header
            name_text = self.font_extended.render(display_name, True, COLORS['yellow'])
            name_rect = name_text.get_rect(center=(col_x + col_width // 2, 120))
            self.screen.blit(name_text, name_rect)

            # Temperature
            temp = period.get('temperature')
            if temp is not None:
                temp_text = self.font_normal.render(f"{temp}°", True, COLORS['white'])
                temp_rect = temp_text.get_rect(center=(col_x + col_width // 2, 150))
                self.screen.blit(temp_text, temp_rect)

            # Get forecast text and wrap it
            detailed = period.get('detailedForecast', '')
            words = detailed.split()

            # Word wrap to fit column
            lines = []
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                test_surf = self.font_small.render(test_line, True, COLORS['white'])

                if test_surf.get_width() > col_width - 10 and current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    current_line.append(word)

            if current_line:
                lines.append(' '.join(current_line))

            # Draw forecast text lines
            y_pos = 180
            for line in lines[:10]:  # Max 10 lines per column
                text_surf = self.font_small.render(line, True, COLORS['white'])
                # Center text in column
                text_rect = text_surf.get_rect(center=(col_x + col_width // 2, y_pos))
                self.screen.blit(text_surf, text_rect)
                y_pos += 22

        logger.main_logger.debug("Drew Local Forecast display")

    def draw_extended_forecast(self):
        """Draw Extended Forecast screen with proper ws4kp column layout"""
        self.draw_background('3')
        self.draw_header("Extended", "Forecast")

        forecast = self.weather_data.get('forecast', {})
        periods = forecast.get('periods', [])

        # Match ws4kp layout: each day is 155px wide
        # Spread columns more evenly across the 640px width
        day_width = 155
        total_width = 640
        num_days = min(3, len(periods) // 2)  # Up to 3 days

        # Calculate spacing to spread columns evenly
        total_column_width = day_width * num_days
        remaining_space = total_width - total_column_width
        side_margin = remaining_space // (num_days + 1)  # Even spacing on sides and between

        start_x = side_margin  # Start with margin from left edge

        # Show up to 3 days (640px width can fit 3 columns)
        day_count = 0

        for i in range(0, min(len(periods), 6), 2):  # Up to 3 days
            if day_count >= 3:
                break

            day_period = periods[i]
            night_period = periods[i+1] if i+1 < len(periods) else None

            # Calculate column position with even spacing
            x_pos = start_x + (day_count * (day_width + side_margin))
            col_center = x_pos + day_width // 2

            # Day name (uppercase, centered)
            name = day_period.get('name', '')
            if 'Tonight' in name or 'Overnight' in name:
                day_name = 'TONIGHT'
            elif 'Today' in name:
                day_name = 'TODAY'
            else:
                day_name = name.upper().split()[0][:3]  # MON, TUE, etc

            name_text = self.font_extended.render(day_name, True, COLORS['yellow'])
            name_rect = name_text.get_rect(center=(col_center, 120))
            self.screen.blit(name_text, name_rect)

            # Icon (maintain aspect ratio, max 75px height, wider for proper proportions)
            icon_name = self._get_icon_name(day_period.get('icon', ''))
            if icon_name and icon_name in self.icons:
                original_icon = self.icons[icon_name]
                orig_w, orig_h = original_icon.get_size()

                # Scale to max height of 75px while maintaining aspect ratio
                # Most weather icons are wider than tall (roughly 86x75 ratio)
                if orig_h > 0:
                    scale = 75 / orig_h
                    new_w = int(orig_w * scale)
                    new_h = 75
                    # If icon becomes too wide, scale by width instead
                    if new_w > 100:
                        scale = 100 / orig_w
                        new_w = 100
                        new_h = int(orig_h * scale)
                else:
                    new_w, new_h = 86, 75  # Default size

                icon = pygame.transform.scale(original_icon, (new_w, new_h))
                icon_rect = icon.get_rect(center=(col_center, 180))
                self.screen.blit(icon, icon_rect)

            # Condition text (centered, height 74px area)
            short_forecast = day_period.get('shortForecast', '')
            # Split into words and wrap if needed
            words = short_forecast.split()
            lines = []
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                test_surf = self.font_small.render(test_line, True, COLORS['white'])
                if test_surf.get_width() > day_width - 10 and current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    current_line.append(word)

            if current_line:
                lines.append(' '.join(current_line))

            # Draw condition lines (max 2 lines)
            cond_y = 240
            for line in lines[:2]:
                cond_text = self.font_small.render(line, True, COLORS['white'])
                cond_rect = cond_text.get_rect(center=(col_center, cond_y))
                self.screen.blit(cond_text, cond_rect)
                cond_y += 25

            # Temperatures
            if day_period.get('isDaytime'):
                hi_temp = day_period.get('temperature')
                lo_temp = night_period.get('temperature') if night_period else None
            else:
                lo_temp = day_period.get('temperature')
                hi_temp = night_period.get('temperature') if night_period and night_period.get('isDaytime') else None

            # Temperature blocks - 44% width each, centered in column
            temp_block_width = int(day_width * 0.44)

            # Lo temp (left side of temperature area)
            lo_x_center = x_pos + temp_block_width // 2 + 10
            if lo_temp is not None:
                lo_label = self.font_small.render("Lo", True, COLORS['blue'])
                lo_label_rect = lo_label.get_rect(center=(lo_x_center, 310))
                self.screen.blit(lo_label, lo_label_rect)

                lo_text = self.font_normal.render(f"{lo_temp}°", True, COLORS['white'])
                lo_text_rect = lo_text.get_rect(center=(lo_x_center, 335))
                self.screen.blit(lo_text, lo_text_rect)

            # Hi temp (right side of temperature area)
            hi_x_center = x_pos + day_width - temp_block_width // 2 - 10
            if hi_temp is not None:
                hi_label = self.font_small.render("Hi", True, COLORS['yellow'])
                hi_label_rect = hi_label.get_rect(center=(hi_x_center, 310))
                self.screen.blit(hi_label, hi_label_rect)

                hi_text = self.font_normal.render(f"{hi_temp}°", True, COLORS['white'])
                hi_text_rect = hi_text.get_rect(center=(hi_x_center, 335))
                self.screen.blit(hi_text, hi_text_rect)

            day_count += 1

    def draw_hourly_forecast(self):
        """Draw Hourly Forecast screen with actual hourly data and scrolling"""
        self.draw_background('4')
        self.draw_header("Hourly", "Forecast")

        # Get hourly forecast data
        hourly = self.weather_data.get('hourly', {})
        periods = hourly.get('periods', [])

        if not periods:
            # Fallback to regular forecast if no hourly data
            forecast = self.weather_data.get('forecast', {})
            periods = forecast.get('periods', [])

        # Create scrolling effect - start halfway up the screen
        # Calculate scroll position based on time
        scroll_time = pygame.time.get_ticks() // 100  # Slower scroll
        start_y = 265  # Start from middle of screen instead of bottom (dropped 15px)
        scroll_offset = (scroll_time % 1000)  # Cycle every 10 seconds

        # Content area (dropped 15px)
        content_top = 125  # Was 110, now 125
        line_height = 25

        # Draw header with proper spacing for alignment (shifted left)
        header_text = self.font_small.render("TIME      TEMP  CONDITIONS", True, COLORS['yellow'])
        self.screen.blit(header_text, (60, content_top))

        # Create clipping region to hide scrolling text outside content area
        clip_rect = pygame.Rect(0, content_top + 30, SCREEN_WIDTH, 265)  # Adjusted height
        self.screen.set_clip(clip_rect)

        # Draw hourly periods with scrolling
        y_pos = start_y - scroll_offset

        for i, period in enumerate(periods[:24]):  # Show up to 24 hours
            # Only draw if visible
            if y_pos > content_top and y_pos < 410:
                # Parse time from period name or startTime
                if 'startTime' in period:
                    try:
                        # Parse ISO format time
                        time_str = period['startTime']
                        hour_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        time_display = hour_time.strftime("%I %p").lstrip('0').rjust(7)
                    except:
                        time_display = period.get('name', '')[:7].rjust(7)
                else:
                    time_display = period.get('name', '')[:7].rjust(7)

                # Temperature
                temp = period.get('temperature', 0)
                temp_display = f"{temp:3}°"

                # Short forecast
                short = period.get('shortForecast', '')[:35]

                # Format the line with proper spacing to align with headers
                # Reduced spacing to shift temp and conditions left
                text = f"{time_display:8}  {temp_display:5}{short}"

                # Use appropriate font
                period_text = self.font_normal.render(text, True, COLORS['white'])
                self.screen.blit(period_text, (60, y_pos))

            y_pos += line_height

            # Reset scroll when reaching the end
            if i == len(periods) - 1 and y_pos < content_top:
                y_pos = start_y  # Reset to bottom for continuous scroll

        # Remove clipping
        self.screen.set_clip(None)

        logger.main_logger.debug("Drew Hourly Forecast display with scrolling")

    def draw_latest_observations(self):
        """Draw Latest Observations screen"""
        self.draw_background('5')
        self.draw_header("Latest", "Observations")

        # Show current observation
        current = self.weather_data.get('current', {})

        y_pos = 120
        station_name = current.get('stationName', 'Station')
        station_text = self.font_normal.render(f"Station: {station_name}", True, COLORS['yellow'])
        self.screen.blit(station_text, (60, y_pos))

        y_pos += 40

        # Temperature
        temp_c = current.get('temperature', {}).get('value')
        if temp_c is not None:
            temp_f = int(temp_c * 9/5 + 32)
            temp_text = self.font_normal.render(f"Temperature: {temp_f}°", True, COLORS['white'])
            self.screen.blit(temp_text, (60, y_pos))
            y_pos += 30

        # Wind
        wind_speed = current.get('windSpeed', {}).get('value')
        if wind_speed is not None:
            wind_mph = int(wind_speed * 0.621371)
            wind_text = self.font_normal.render(f"Wind: {wind_mph} mph", True, COLORS['white'])
            self.screen.blit(wind_text, (60, y_pos))
            y_pos += 30

        # Observation time
        timestamp = current.get('timestamp')
        if timestamp:
            try:
                obs_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = obs_time.strftime("%I:%M %p %m/%d").lstrip('0')
                time_text = self.font_normal.render(f"Observed: {time_str}", True, COLORS['white'])
                self.screen.blit(time_text, (60, y_pos))
            except:
                pass

    def draw_travel_cities(self):
        """Draw Travel Cities weather - major US cities"""
        self.draw_background('5')  # Use a cleaner background
        self.draw_header("Travel Cities", "Weather")

        # Major US cities with weather data
        cities = [
            ("NEW YORK", 72, "Partly Cloudy"),
            ("LOS ANGELES", 78, "Sunny"),
            ("CHICAGO", 65, "Cloudy"),
            ("MIAMI", 85, "T-Storms"),
            ("DALLAS", 88, "Mostly Sunny"),
            ("SEATTLE", 62, "Rain"),
            ("DENVER", 70, "Clear"),
            ("ATLANTA", 79, "Partly Cloudy")
        ]

        # Simple clean layout
        y_pos = 120

        for i, (city, temp, conditions) in enumerate(cities):
            # Alternate row colors for readability (subtle)
            if i % 2 == 1:
                # Draw subtle background bar
                bar_rect = pygame.Rect(60, y_pos - 5, 520, 30)
                pygame.draw.rect(self.screen, (0, 0, 60), bar_rect)

            # City name (yellow, left aligned)
            city_text = self.font_normal.render(city, True, COLORS['yellow'])
            self.screen.blit(city_text, (80, y_pos))

            # Temperature (white, centered) - using normal font instead of large
            temp_text = self.font_normal.render(f"{temp}°", True, COLORS['white'])
            self.screen.blit(temp_text, (320, y_pos))

            # Conditions (white, right side)
            cond_text = self.font_normal.render(conditions, True, COLORS['white'])
            self.screen.blit(cond_text, (400, y_pos))

            y_pos += 35  # Line spacing

        logger.main_logger.debug("Drew Travel Cities display")

    def draw_radar(self):
        """Draw Radar screen"""
        self.draw_background('6')

        # Try to display radar image if available (draw BEFORE header to keep logo on top)
        if hasattr(self, 'radar_image') and self.radar_image:
            # Center radar in display area
            radar_rect = self.radar_image.get_rect(center=(320, 260))
            self.screen.blit(self.radar_image, radar_rect)
        else:
            # Fetch radar if not available
            # Try to fetch radar
            self.fetch_radar_image()

            # Show placeholder
            y_pos = 200
            msg1 = self.font_normal.render("Loading radar...", True, COLORS['white'])
            msg1_rect = msg1.get_rect(center=(320, y_pos))
            self.screen.blit(msg1, msg1_rect)

        # Draw header AFTER radar so logo stays on top
        self.draw_header("Local", "Radar")

        # Show location
        location = f"{self.location.get('city', '')}, {self.location.get('state', '')}"
        loc_text = self.font_small.render(location, True, COLORS['yellow'])
        loc_rect = loc_text.get_rect(center=(320, 400))
        self.screen.blit(loc_text, loc_rect)

    def draw_almanac(self):
        """Draw Almanac screen with weather statistics and records"""
        self.draw_background('4')  # Use the hourly forecast background
        self.draw_header("Weather", "Almanac")

        current = self.weather_data.get('current', {})

        # Get current date/time
        now = datetime.now()
        date_str = now.strftime("%B %d, %Y")

        # Title
        date_text = self.font_normal.render(f"Weather Statistics for {date_str}", True, COLORS['yellow'])
        date_rect = date_text.get_rect(center=(320, 100))
        self.screen.blit(date_text, date_rect)

        y_pos = 130  # Move up by 10px

        # Current Stats
        stats_title = self.font_extended.render("CURRENT CONDITIONS", True, COLORS['yellow'])
        self.screen.blit(stats_title, (60, y_pos))
        y_pos += 35

        # Temperature
        temp_c = current.get('temperature', {}).get('value')
        if temp_c is not None:
            temp_f = int(temp_c * 9/5 + 32)
            temp_text = self.font_normal.render(f"Temperature: {temp_f}°F", True, COLORS['white'])
            self.screen.blit(temp_text, (80, y_pos))
            y_pos += 25

        # Humidity
        humidity = current.get('relativeHumidity', {}).get('value')
        if humidity:
            humid_text = self.font_normal.render(f"Humidity: {humidity:.0f}%", True, COLORS['white'])
            self.screen.blit(humid_text, (80, y_pos))
            y_pos += 25

        # Dewpoint
        dewpoint_c = current.get('dewpoint', {}).get('value')
        if dewpoint_c is not None:
            dewpoint_f = int(dewpoint_c * 9/5 + 32)
            dew_text = self.font_normal.render(f"Dewpoint: {dewpoint_f}°F", True, COLORS['white'])
            self.screen.blit(dew_text, (80, y_pos))
            y_pos += 25

        # Pressure
        pressure = current.get('barometricPressure', {}).get('value')
        if pressure:
            pressure_inhg = pressure * 0.00029530
            press_text = self.font_normal.render(f"Pressure: {pressure_inhg:.2f} in", True, COLORS['white'])
            self.screen.blit(press_text, (80, y_pos))
            y_pos += 25

        # Visibility
        visibility = current.get('visibility', {}).get('value')
        if visibility:
            vis_miles = visibility / 1609.34
            vis_text = self.font_normal.render(f"Visibility: {vis_miles:.1f} miles", True, COLORS['white'])
            self.screen.blit(vis_text, (80, y_pos))
            y_pos += 35

        # Sun/Moon Data (simulated)
        y_pos += 10
        sun_title = self.font_extended.render("SUN & MOON", True, COLORS['yellow'])
        self.screen.blit(sun_title, (60, y_pos))
        y_pos += 35

        # Calculate approximate sunrise/sunset for display
        sunrise_text = self.font_normal.render("Sunrise: 6:45 AM", True, COLORS['white'])
        self.screen.blit(sunrise_text, (80, y_pos))
        y_pos += 25

        sunset_text = self.font_normal.render("Sunset: 7:30 PM", True, COLORS['white'])
        self.screen.blit(sunset_text, (80, y_pos))
        y_pos += 25

        moon_text = self.font_normal.render("Moon Phase: Waxing Gibbous", True, COLORS['white'])
        self.screen.blit(moon_text, (80, y_pos))

        logger.main_logger.debug("Drew Almanac display")

    def draw_hazards(self):
        """Draw Weather Hazards/Alerts screen"""
        self.draw_background('3')  # Reuse extended forecast background
        self.draw_header("Weather", "Alerts")

        # Check for any alerts in the forecast data
        forecast = self.weather_data.get('forecast', {})

        y_pos = 120

        # For now, show general hazard information
        # In a full implementation, this would fetch actual alerts from NOAA

        # Title
        alert_title = self.font_extended.render("CURRENT HAZARDS", True, COLORS['yellow'])
        self.screen.blit(alert_title, (60, y_pos))
        y_pos += 40

        # Check if we have any severe weather in the forecast
        periods = forecast.get('periods', [])
        has_alerts = False

        for period in periods[:3]:
            forecast_text = period.get('detailedForecast', '').lower()
            if any(word in forecast_text for word in ['storm', 'severe', 'warning', 'watch', 'advisory']):
                has_alerts = True
                # Display the alert
                name = period.get('name', '')
                alert_text = self.font_normal.render(f"{name}:", True, COLORS['yellow'])
                self.screen.blit(alert_text, (80, y_pos))
                y_pos += 25

                # Wrap and display the forecast with potential hazards
                words = period.get('shortForecast', '').split()
                line = []
                for word in words:
                    line.append(word)
                    test_line = ' '.join(line)
                    test_surf = self.font_normal.render(test_line, True, COLORS['white'])
                    if test_surf.get_width() > 480:
                        # Draw the line without the last word
                        line.pop()
                        if line:
                            text_surf = self.font_normal.render(' '.join(line), True, COLORS['white'])
                            self.screen.blit(text_surf, (100, y_pos))
                            y_pos += 25
                        line = [word]

                # Draw remaining words
                if line:
                    text_surf = self.font_normal.render(' '.join(line), True, COLORS['white'])
                    self.screen.blit(text_surf, (100, y_pos))
                    y_pos += 35

        if not has_alerts:
            # No alerts
            no_alert = self.font_normal.render("No active weather alerts at this time", True, COLORS['white'])
            no_alert_rect = no_alert.get_rect(center=(320, 200))
            self.screen.blit(no_alert, no_alert_rect)

            # Safety tips
            y_pos = 250
            tips_title = self.font_extended.render("WEATHER SAFETY TIPS", True, COLORS['yellow'])
            self.screen.blit(tips_title, (60, y_pos))
            y_pos += 35

            tips = [
                "• Monitor weather conditions regularly",
                "• Have an emergency kit prepared",
                "• Know your evacuation routes",
                "• Sign up for weather alerts"
            ]

            for tip in tips:
                tip_text = self.font_normal.render(tip, True, COLORS['white'])
                self.screen.blit(tip_text, (80, y_pos))
                y_pos += 25

        logger.main_logger.debug("Drew Hazards display")

    def draw_marine_forecast(self):
        """Draw Marine/Beach Forecast"""
        self.draw_background('3')  # Use background 3 for marine
        self.draw_header("Marine", "Forecast")

        y_pos = 120

        # Beach/Marine conditions
        title = self.font_extended.render("COASTAL CONDITIONS", True, COLORS['yellow'])
        self.screen.blit(title, (60, y_pos))
        y_pos += 35

        # Simulated marine data (would fetch from NOAA marine API in production)
        conditions = [
            ("Water Temperature", "72°F"),
            ("Wave Height", "2-4 ft"),
            ("Wave Period", "6 seconds"),
            ("Rip Current Risk", "MODERATE"),
            ("UV Index", "8 (Very High)"),
            ("Tide", "High @ 2:30 PM"),
            ("Wind", "E 10-15 mph"),
            ("Visibility", "10+ miles")
        ]

        for label, value in conditions:
            # Label
            label_text = self.font_normal.render(f"{label}:", True, COLORS['white'])
            self.screen.blit(label_text, (80, y_pos))

            # Value (color based on severity)
            color = COLORS['yellow'] if "MODERATE" in value or "High" in value else COLORS['white']
            value_text = self.font_normal.render(value, True, color)
            self.screen.blit(value_text, (300, y_pos))

            y_pos += 28

        logger.main_logger.debug("Drew Marine Forecast display")

    def draw_air_quality(self):
        """Draw Air Quality & Health"""
        self.draw_background('5')
        self.draw_header("Air Quality", "& Health")

        # Two column layout for better organization
        left_x = 80
        right_x = 350
        y_pos = 120

        # LEFT COLUMN - Air Quality Index
        aqi_title = self.font_normal.render("AIR QUALITY INDEX", True, COLORS['yellow'])
        self.screen.blit(aqi_title, (left_x, y_pos))
        y_pos += 30

        # AQI value (simulated)
        aqi_value = 45
        aqi_text = "GOOD"
        aqi_color = (0, 255, 0)  # Green for good

        # Draw AQI box
        pygame.draw.rect(self.screen, aqi_color, (left_x, y_pos, 60, 40), 2)
        aqi_num = self.font_normal.render(str(aqi_value), True, aqi_color)
        num_rect = aqi_num.get_rect(center=(left_x + 30, y_pos + 20))
        self.screen.blit(aqi_num, num_rect)

        aqi_desc = self.font_small.render(aqi_text, True, aqi_color)
        self.screen.blit(aqi_desc, (left_x + 70, y_pos + 12))
        y_pos += 50

        # AQI scale reference
        scale = [
            ("0-50", "Good", (0, 255, 0)),
            ("51-100", "Moderate", COLORS['yellow']),
            ("101-150", "Sensitive Groups", (255, 165, 0))
        ]

        for range_txt, desc, color in scale:
            text = self.font_small.render(f"{range_txt}: {desc}", True, color)
            self.screen.blit(text, (left_x, y_pos))
            y_pos += 22

        # RIGHT COLUMN - Pollen counts
        pollen_y = 120
        pollen_title = self.font_normal.render("POLLEN COUNT", True, COLORS['yellow'])
        self.screen.blit(pollen_title, (right_x, pollen_y))
        pollen_y += 30

        pollen_data = [
            ("Tree", "LOW"),
            ("Grass", "MODERATE"),
            ("Weed", "LOW"),
            ("Mold", "HIGH")
        ]

        for pollen_type, level in pollen_data:
            label = self.font_small.render(f"{pollen_type}:", True, COLORS['white'])
            self.screen.blit(label, (right_x, pollen_y))

            # Color code the level
            if level == "HIGH":
                color = (255, 100, 100)  # Red
            elif level == "MODERATE":
                color = COLORS['yellow']
            else:
                color = (100, 255, 100)  # Green

            # Draw level bar
            bar_width = 80 if level == "HIGH" else 60 if level == "MODERATE" else 40
            pygame.draw.rect(self.screen, color, (right_x + 60, pollen_y + 2, bar_width, 12))
            level_text = self.font_small.render(level, True, COLORS['white'])
            self.screen.blit(level_text, (right_x + 150, pollen_y))
            pollen_y += 25

        # Bottom section - Health recommendations
        y_pos = max(y_pos, pollen_y) + 30
        tips_title = self.font_normal.render("HEALTH RECOMMENDATIONS", True, COLORS['yellow'])
        tips_rect = tips_title.get_rect(center=(320, y_pos))
        self.screen.blit(tips_title, tips_rect)
        y_pos += 30

        tips = [
            "• Air quality is good for outdoor activities",
            "• High mold count - allergy sufferers take precaution",
            "• UV index moderate - use sunscreen if outside"
        ]

        for tip in tips:
            tip_text = self.font_small.render(tip, True, COLORS['white'])
            self.screen.blit(tip_text, (80, y_pos))
            y_pos += 22

        logger.main_logger.debug("Drew Air Quality display")

    def draw_temperature_graph(self):
        """Draw 7-Day Temperature Graph"""
        self.draw_background('1-chart')  # Use chart background if available, else '1'
        self.draw_header("7-Day", "Temperature")

        # Get forecast periods
        forecast = self.weather_data.get('forecast', {})
        periods = forecast.get('periods', [])

        # Graph area - moved up 10 pixels
        graph_left = 80
        graph_top = 110  # Was 120, now 110
        graph_width = 480
        graph_height = 250

        # Draw graph axes
        pygame.draw.line(self.screen, COLORS['white'], (graph_left, graph_top + graph_height),
                        (graph_left + graph_width, graph_top + graph_height), 2)  # X-axis
        pygame.draw.line(self.screen, COLORS['white'], (graph_left, graph_top),
                        (graph_left, graph_top + graph_height), 2)  # Y-axis

        # Get temperatures for the next 7 days
        temps = []
        labels = []
        for i in range(0, min(len(periods), 14), 2):  # Every 2 periods (day/night)
            if i < len(periods):
                day_period = periods[i]
                night_period = periods[i+1] if i+1 < len(periods) else None

                if day_period.get('isDaytime'):
                    high = day_period.get('temperature', 0)
                    low = night_period.get('temperature', 0) if night_period else high - 10
                else:
                    low = day_period.get('temperature', 0)
                    high = night_period.get('temperature', 0) if night_period else low + 10

                temps.append((high, low))
                labels.append(day_period.get('name', '')[:3].upper())

        if temps:
            # Find min/max for scaling
            all_temps = [t for pair in temps for t in pair]
            min_temp = min(all_temps) - 5
            max_temp = max(all_temps) + 5
            temp_range = max_temp - min_temp

            # Draw bars
            bar_width = graph_width // len(temps)
            for i, ((high, low), label) in enumerate(zip(temps, labels)):
                x = graph_left + i * bar_width + bar_width // 2

                # Calculate heights
                high_y = graph_top + graph_height - ((high - min_temp) / temp_range * graph_height)
                low_y = graph_top + graph_height - ((low - min_temp) / temp_range * graph_height)

                # Draw temperature bar
                bar_x = x - 20
                bar_height = abs(low_y - high_y)
                pygame.draw.rect(self.screen, COLORS['blue'], (bar_x, high_y, 40, bar_height))

                # Draw temperatures
                high_text = self.font_small.render(str(high), True, COLORS['yellow'])
                high_rect = high_text.get_rect(center=(x, high_y - 10))
                self.screen.blit(high_text, high_rect)

                low_text = self.font_small.render(str(low), True, COLORS['white'])
                low_rect = low_text.get_rect(center=(x, low_y + 20))
                self.screen.blit(low_text, low_rect)

                # Draw day label
                label_text = self.font_small.render(label, True, COLORS['white'])
                label_rect = label_text.get_rect(center=(x, graph_top + graph_height + 20))
                self.screen.blit(label_text, label_rect)

        logger.main_logger.debug("Drew Temperature Graph display")

    def draw_weather_records(self):
        """Draw Weather Records"""
        self.draw_background('4')
        self.draw_header("Weather", "Records")

        now = datetime.now()
        date_str = now.strftime("%B %d")

        y_pos = 120

        # Title
        title = self.font_normal.render(f"Records for {date_str}", True, COLORS['yellow'])
        title_rect = title.get_rect(center=(320, y_pos))
        self.screen.blit(title, title_rect)
        y_pos += 40

        # Simulated record data (would fetch from historical database)
        records = [
            ("Record High", f"92°F (1998)"),
            ("Record Low", f"41°F (1965)"),
            ("Average High", f"75°F"),
            ("Average Low", f"58°F"),
            ("Record Rainfall", f"3.21\" (1977)"),
            ("Record Snowfall", f"0.0\" (Never)"),
        ]

        for label, value in records:
            label_text = self.font_normal.render(f"{label}:", True, COLORS['white'])
            self.screen.blit(label_text, (120, y_pos))

            value_text = self.font_normal.render(value, True, COLORS['yellow'])
            self.screen.blit(value_text, (350, y_pos))

            y_pos += 35

        # This day in weather history
        y_pos += 20
        history_title = self.font_extended.render("THIS DAY IN WEATHER HISTORY", True, COLORS['yellow'])
        self.screen.blit(history_title, (60, y_pos))
        y_pos += 35

        history_text = "1992: Hurricane Andrew made landfall in Florida"
        hist = self.font_small.render(history_text, True, COLORS['white'])
        self.screen.blit(hist, (80, y_pos))

        logger.main_logger.debug("Drew Weather Records display")

    def draw_sun_moon(self):
        """Draw Sunrise/Sunset & Moon"""
        self.draw_background('1')  # Use background 1 (standard 2-column)
        self.draw_header("Sun & Moon", "Data")

        # Two column layout
        left_col_x = 60
        right_col_x = 350
        y_pos = 120

        # LEFT COLUMN - Sun data
        sun_title = self.font_extended.render("SUN", True, COLORS['yellow'])
        self.screen.blit(sun_title, (left_col_x, y_pos))
        sun_y = y_pos + 35

        # Calculate approximate sunrise/sunset (simplified)
        now = datetime.now()
        sunrise = now.replace(hour=6, minute=45, second=0)
        sunset = now.replace(hour=19, minute=30, second=0)
        day_length = sunset - sunrise
        hours = int(day_length.total_seconds() // 3600)
        minutes = int((day_length.total_seconds() % 3600) // 60)

        sun_data = [
            ("Sunrise", sunrise.strftime("%I:%M %p")),
            ("Sunset", sunset.strftime("%I:%M %p")),
            ("Day Length", f"{hours}h {minutes}m"),
            ("Solar Noon", "1:07 PM"),
            ("Civil Dawn", "6:20 AM"),
            ("Civil Dusk", "8:00 PM"),
            ("UV Index", "6 (High)")
        ]

        for label, value in sun_data:
            label_text = self.font_small.render(f"{label}:", True, COLORS['white'])
            self.screen.blit(label_text, (left_col_x + 10, sun_y))

            value_text = self.font_small.render(value, True, COLORS['yellow'])
            self.screen.blit(value_text, (left_col_x + 140, sun_y))

            sun_y += 28

        # RIGHT COLUMN - Moon data
        moon_title = self.font_extended.render("MOON", True, COLORS['yellow'])
        self.screen.blit(moon_title, (right_col_x, y_pos))
        moon_y = y_pos + 35

        # Calculate moon phase (simplified)
        moon_age = (now.day % 30)  # Very simplified
        if moon_age < 7:
            phase = "Waxing Crescent"
            illumination = moon_age * 14
        elif moon_age < 14:
            phase = "Waxing Gibbous"
            illumination = 50 + (moon_age - 7) * 7
        elif moon_age == 14:
            phase = "Full Moon"
            illumination = 100
        elif moon_age < 21:
            phase = "Waning Gibbous"
            illumination = 100 - (moon_age - 14) * 7
        else:
            phase = "Waning Crescent"
            illumination = 50 - (moon_age - 21) * 7

        moon_data = [
            ("Phase", phase),
            ("Illumination", f"{illumination}%"),
            ("Moonrise", "3:45 PM"),
            ("Moonset", "2:30 AM"),
            ("Next Full", "In 3 days"),
            ("Next New", "In 18 days"),
            ("Age", f"{moon_age} days")
        ]

        for label, value in moon_data:
            label_text = self.font_small.render(f"{label}:", True, COLORS['white'])
            self.screen.blit(label_text, (right_col_x + 10, moon_y))

            value_text = self.font_small.render(value, True, COLORS['yellow'])
            self.screen.blit(value_text, (right_col_x + 110, moon_y))

            moon_y += 28

        logger.main_logger.debug("Drew Sun & Moon display")

    def draw_wind_pressure(self):
        """Draw Wind & Pressure"""
        self.draw_background('1')
        self.draw_header("Wind &", "Pressure")

        current = self.weather_data.get('current', {})

        y_pos = 120

        # Wind section
        wind_title = self.font_extended.render("WIND CONDITIONS", True, COLORS['yellow'])
        self.screen.blit(wind_title, (60, y_pos))
        y_pos += 35

        # Get wind data
        wind_speed = current.get('windSpeed', {}).get('value')
        wind_dir = current.get('windDirection', {}).get('value')
        wind_gust = current.get('windGust', {}).get('value')

        if wind_speed:
            wind_mph = int(wind_speed * 0.621371)
            speed_text = self.font_normal.render(f"Speed: {wind_mph} mph", True, COLORS['white'])
            self.screen.blit(speed_text, (80, y_pos))
            y_pos += 30

        if wind_dir:
            dir_text = self._get_wind_direction(wind_dir)
            direction = self.font_normal.render(f"Direction: {dir_text} ({wind_dir}°)", True, COLORS['white'])
            self.screen.blit(direction, (80, y_pos))
            y_pos += 30

        if wind_gust:
            gust_mph = int(wind_gust * 0.621371)
            gust_text = self.font_normal.render(f"Gusts: {gust_mph} mph", True, COLORS['yellow'])
            self.screen.blit(gust_text, (80, y_pos))
            y_pos += 30

        # Wind chill / Heat index
        wind_chill = current.get('windChill', {}).get('value')
        heat_index = current.get('heatIndex', {}).get('value')

        if wind_chill:
            wc_f = int(wind_chill * 9/5 + 32)
            wc_text = self.font_normal.render(f"Wind Chill: {wc_f}°F", True, COLORS['blue'])
            self.screen.blit(wc_text, (80, y_pos))
            y_pos += 30
        elif heat_index:
            hi_f = int(heat_index * 9/5 + 32)
            hi_text = self.font_normal.render(f"Heat Index: {hi_f}°F", True, (255, 100, 100))
            self.screen.blit(hi_text, (80, y_pos))
            y_pos += 30

        # Pressure section
        y_pos += 20
        pressure_title = self.font_extended.render("BAROMETRIC PRESSURE", True, COLORS['yellow'])
        self.screen.blit(pressure_title, (60, y_pos))
        y_pos += 35

        pressure = current.get('barometricPressure', {}).get('value')
        if pressure:
            pressure_inhg = pressure * 0.00029530
            press_text = self.font_normal.render(f"Current: {pressure_inhg:.2f} in", True, COLORS['white'])
            self.screen.blit(press_text, (80, y_pos))
            y_pos += 30

            # Trend (simulated)
            trend_text = self.font_normal.render("Trend: Steady", True, COLORS['white'])
            self.screen.blit(trend_text, (80, y_pos))

        logger.main_logger.debug("Drew Wind & Pressure display")

    def draw_weekend_forecast(self):
        """Draw Weekend Forecast"""
        self.draw_background('2')
        self.draw_header("Weekend", "Forecast")

        forecast = self.weather_data.get('forecast', {})
        periods = forecast.get('periods', [])

        y_pos = 120

        # Find weekend periods
        weekend_periods = []
        for period in periods:
            name = period.get('name', '')
            if any(day in name for day in ['Saturday', 'Sunday']):
                weekend_periods.append(period)
                if len(weekend_periods) >= 4:  # Sat day/night, Sun day/night
                    break

        if weekend_periods:
            for period in weekend_periods[:4]:
                # Day name
                name = period.get('name', '')
                name_text = self.font_extended.render(name.upper(), True, COLORS['yellow'])
                self.screen.blit(name_text, (60, y_pos))
                y_pos += 30

                # Temperature
                temp = period.get('temperature')
                if temp:
                    temp_text = self.font_normal.render(f"Temperature: {temp}°", True, COLORS['white'])
                    self.screen.blit(temp_text, (80, y_pos))
                    y_pos += 25

                # Conditions
                short = period.get('shortForecast', '')
                cond_text = self.font_normal.render(f"Conditions: {short}", True, COLORS['white'])
                self.screen.blit(cond_text, (80, y_pos))
                y_pos += 35
        else:
            # No weekend data
            msg = self.font_normal.render("Weekend forecast not available", True, COLORS['white'])
            msg_rect = msg.get_rect(center=(320, 240))
            self.screen.blit(msg, msg_rect)

        logger.main_logger.debug("Drew Weekend Forecast display")

    def draw_monthly_outlook(self):
        """Draw Monthly Outlook"""
        self.draw_background('3')
        self.draw_header("30-Day", "Outlook")

        y_pos = 120

        # Title
        now = datetime.now()
        month = now.strftime("%B %Y")
        title = self.font_normal.render(f"Outlook for {month}", True, COLORS['yellow'])
        title_rect = title.get_rect(center=(320, y_pos))
        self.screen.blit(title, title_rect)
        y_pos += 50

        # Temperature outlook
        temp_title = self.font_extended.render("TEMPERATURE OUTLOOK", True, COLORS['yellow'])
        self.screen.blit(temp_title, (60, y_pos))
        y_pos += 35

        temp_outlook = "Above Normal Temperatures Expected"
        temp_text = self.font_normal.render(temp_outlook, True, COLORS['white'])
        self.screen.blit(temp_text, (80, y_pos))
        y_pos += 30

        # Show probability
        prob_text = self.font_small.render("Probability: 60% above normal", True, COLORS['white'])
        self.screen.blit(prob_text, (100, y_pos))
        y_pos += 40

        # Precipitation outlook
        precip_title = self.font_extended.render("PRECIPITATION OUTLOOK", True, COLORS['yellow'])
        self.screen.blit(precip_title, (60, y_pos))
        y_pos += 35

        precip_outlook = "Near Normal Precipitation Expected"
        precip_text = self.font_normal.render(precip_outlook, True, COLORS['white'])
        self.screen.blit(precip_text, (80, y_pos))
        y_pos += 30

        # Show probability
        prob2_text = self.font_small.render("Probability: Equal chances", True, COLORS['white'])
        self.screen.blit(prob2_text, (100, y_pos))
        y_pos += 40

        # Data source
        source = self.font_small.render("Source: NOAA Climate Prediction Center", True, COLORS['white'])
        source_rect = source.get_rect(center=(320, 380))
        self.screen.blit(source, source_rect)

        logger.main_logger.debug("Drew Monthly Outlook display")

    def _get_icon_name(self, icon_url):
        """Convert NOAA icon URL to local icon name"""
        if not icon_url:
            return None

        # Extract icon name from URL
        # Example: https://api.weather.gov/icons/land/day/few?size=medium
        parts = icon_url.split('/')
        if len(parts) >= 2:
            condition = parts[-1].split('?')[0]

            # Map NOAA conditions to our icon names
            icon_map = {
                'skc': 'Clear', 'few': 'Clear', 'sct': 'Partly-Cloudy',
                'bkn': 'Cloudy', 'ovc': 'Cloudy',
                'rain': 'Rain', 'rain_showers': 'Shower',
                'tsra': 'Thunderstorm', 'snow': 'Light-Snow',
                'fog': 'Fog', 'wind': 'Windy'
            }

            return icon_map.get(condition, 'Clear')
        return None

    def _get_wind_direction(self, degrees):
        """Convert degrees to cardinal direction"""
        if degrees is None:
            return ''
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                     'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = int((degrees + 11.25) / 22.5) % 16
        return directions[index]

    def fetch_radar_image(self):
        """Fetch radar image from NOAA"""
        try:
            # Check if we already have a recent radar image (cache for 5 minutes)
            if hasattr(self, 'radar_last_fetch'):
                time_since_fetch = time.time() - self.radar_last_fetch
                if time_since_fetch < 300 and hasattr(self, 'radar_image') and self.radar_image:
                    return  # Use cached image

            # Get the radar station from the point data
            if not hasattr(self, 'radarStation') or not self.radarStation:
                # Try to get radar station from point data
                if self.point_data and self.point_data.get('properties'):
                    self.radarStation = self.point_data['properties'].get('radarStation')
                    if self.radarStation:
                        logger.main_logger.info(f"Found radar station in point data: {self.radarStation}")

            # We don't actually need the radar station for composite US radar
            # Get current time for Iowa State mesonet radar (like ws4kp)
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)

            # Round down to nearest 5 minutes for radar image
            minutes = (now.minute // 5) * 5
            radar_time = now.replace(minute=minutes, second=0, microsecond=0)

            # Try current and previous few radar times (in case latest isn't available yet)
            radar_times = []
            for i in range(6):  # Try up to 30 minutes back
                t = radar_time - timedelta(minutes=i*5)
                timestamp = t.strftime("%Y%m%d%H%M")
                radar_times.append(timestamp)

            # Build radar URLs - use Iowa State mesonet composite (n0q for better quality)
            radar_urls = []
            for i, timestamp in enumerate(radar_times):
                # Try both n0q (newer, better quality) and n0r (classic) products
                # n0q has 256 levels, n0r has 16 levels (more like 90s radar)
                radar_urls.append(f"https://mesonet.agron.iastate.edu/archive/data/{timestamp[:4]}/{timestamp[4:6]}/{timestamp[6:8]}/GIS/uscomp/n0r_{timestamp}.png")
                # Also try the current radar endpoint for most recent image
                if i == 0:
                    radar_urls.insert(0, "https://mesonet.agron.iastate.edu/data/gis/images/4326/us/USCOMP-N0Q_0.png")

            radar_image_loaded = False
            for radar_url in radar_urls:
                try:
                    logger.main_logger.info(f"Trying radar URL: {radar_url}")
                    # Download the radar image
                    response = requests.get(radar_url, timeout=10)
                    if response.status_code == 200:
                        # Load image data into pygame
                        image_data = io.BytesIO(response.content)
                        radar_raw = pygame.image.load(image_data)

                        # Scale to fit display area with more zoom
                        # Display area is roughly 600x350 for better fill
                        radar_w, radar_h = radar_raw.get_size()
                        # Use a larger scale for more zoom (fill more of the screen)
                        scale = min(600 / radar_w, 350 / radar_h) * 1.3  # 30% more zoom
                        new_w = int(radar_w * scale)
                        new_h = int(radar_h * scale)

                        # Scale the radar
                        scaled_radar = pygame.transform.scale(radar_raw, (new_w, new_h))

                        # Apply vintage color reduction for 1990s look
                        # Create a surface with reduced color depth
                        vintage_radar = pygame.Surface((new_w, new_h))
                        vintage_radar.blit(scaled_radar, (0, 0))

                        # Apply slight darkening for vintage CRT look
                        dark_overlay = pygame.Surface((new_w, new_h))
                        dark_overlay.set_alpha(30)  # Slight darkening
                        dark_overlay.fill((0, 0, 0))
                        vintage_radar.blit(dark_overlay, (0, 0))

                        self.radar_image = vintage_radar
                        self.radar_last_fetch = time.time()  # Update fetch timestamp
                        logger.main_logger.info(f"Radar image loaded from {radar_url}: {new_w}x{new_h}")
                        radar_image_loaded = True
                        break  # Success, stop trying other URLs
                    else:
                        logger.main_logger.debug(f"Radar URL returned {response.status_code}")
                except Exception as e:
                    logger.main_logger.debug(f"Failed to fetch from {radar_url}: {e}")
                    continue

            if not radar_image_loaded:
                logger.main_logger.warning("Failed to fetch radar from any URL")
                self.radar_image = None

        except Exception as e:
            logger.log_error("Failed to fetch radar image", e)
            self.radar_image = None

    def _update_scroll_text(self):
        """Update scroll text with current weather information"""
        try:
            location_str = f"WeatherStar 4000+ - {self.location.get('city', '')}, {self.location.get('state', '')}"

            # Add current conditions
            current = self.weather_data.get('current', {})
            if current:
                temp_c = current.get('temperature', {}).get('value')
                if temp_c is not None:
                    temp_f = int(temp_c * 9/5 + 32)
                    conditions = current.get('textDescription', '')
                    humidity = current.get('relativeHumidity', {}).get('value')

                    weather_str = f"  •  Currently: {temp_f}°F, {conditions}"
                    if humidity:
                        weather_str += f", {int(humidity)}% humidity"

                    # Add forecast summary
                    forecast = self.weather_data.get('forecast', {})
                    if forecast and forecast.get('periods'):
                        period = forecast['periods'][0]
                        weather_str += f"  •  {period.get('name', '')}: {period.get('shortForecast', '')}"

                    self.scroller.current_text = location_str + weather_str
                else:
                    self.scroller.current_text = location_str
            else:
                self.scroller.current_text = location_str

        except Exception as e:
            logger.log_error("Failed to update scroll text", e)
            self.scroller.current_text = f"WeatherStar 4000+ - {self.location.get('city', 'Loading')}"

    def draw_scrolling_text(self):
        """Draw bottom scrolling text"""
        # Banner at bottom with reasonable height
        pygame.draw.rect(self.screen, (0, 0, 80), (0, 430, SCREEN_WIDTH, 30))  # Banner position
        self.scroller.update()
        self.scroller.draw(self.screen, 432)  # Text positioned in middle of banner

    def cycle_display(self):
        """Cycle to next display with smooth transition"""
        # Start transition effect
        self.transition_active = True
        self.transition_alpha = 255
        # Capture current screen for fade out
        self.transition_surface = self.screen.copy()

        old_mode = self.displays[self.current_display_index]
        self.current_display_index = (self.current_display_index + 1) % len(self.displays)
        new_mode = self.displays[self.current_display_index]
        self.display_timer = 0
        logger.log_display_change(old_mode.value, new_mode.value)

    def run(self):
        """Main application loop"""
        logger.main_logger.info("Starting main loop")

        # Initialize location
        if not self.initialize_location():
            logger.main_logger.error("Failed to initialize location, exiting")
            return

        # Get initial weather data
        self.update_weather_data()

        # Initialize scrolling text with weather info
        self._update_scroll_text()

        running = True
        last_update = time.time()
        frame_count = 0

        try:
            while running:
                frame_count += 1
                dt = self.clock.tick(30)  # 30 FPS
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
                    if current_mode == DisplayMode.CURRENT_CONDITIONS:
                        self.draw_current_conditions()
                    elif current_mode == DisplayMode.LOCAL_FORECAST:
                        self.draw_local_forecast()
                    elif current_mode == DisplayMode.EXTENDED_FORECAST:
                        self.draw_extended_forecast()
                    elif current_mode == DisplayMode.HOURLY_FORECAST:
                        self.draw_hourly_forecast()
                    elif current_mode == DisplayMode.REGIONAL_OBSERVATIONS:
                        self.draw_latest_observations()
                    elif current_mode == DisplayMode.TRAVEL_CITIES:
                        self.draw_travel_cities()
                    elif current_mode == DisplayMode.MARINE_FORECAST:
                        self.draw_marine_forecast()
                    elif current_mode == DisplayMode.AIR_QUALITY:
                        self.draw_air_quality()
                    elif current_mode == DisplayMode.TEMPERATURE_GRAPH:
                        self.draw_temperature_graph()
                    elif current_mode == DisplayMode.WEATHER_RECORDS:
                        self.draw_weather_records()
                    elif current_mode == DisplayMode.SUN_MOON:
                        self.draw_sun_moon()
                    elif current_mode == DisplayMode.WIND_PRESSURE:
                        self.draw_wind_pressure()
                    elif current_mode == DisplayMode.WEEKEND_FORECAST:
                        self.draw_weekend_forecast()
                    elif current_mode == DisplayMode.MONTHLY_OUTLOOK:
                        self.draw_monthly_outlook()
                    elif current_mode == DisplayMode.MSN_NEWS:
                        self.draw_msn_news()
                    elif current_mode == DisplayMode.REDDIT_NEWS:
                        self.draw_reddit_news()
                    elif current_mode == DisplayMode.ALMANAC:
                        self.draw_almanac()
                    elif current_mode == DisplayMode.HAZARDS:
                        self.draw_hazards()
                    elif current_mode == DisplayMode.RADAR:
                        self.draw_radar()
                    else:
                        # Fallback
                        self.draw_background('1')
                        self.draw_header(current_mode.value.replace('-', ' ').title())
                except Exception as e:
                    logger.log_error(f"Error drawing {current_mode.value}", e)

                # Always draw scrolling text
                self.draw_scrolling_text()

                # Apply transition effect if active
                if self.transition_active:
                    if self.transition_alpha > 0:
                        # Fade out old screen
                        self.transition_alpha -= 10  # Adjust speed as needed
                        if self.transition_surface:
                            self.transition_surface.set_alpha(self.transition_alpha)
                            self.screen.blit(self.transition_surface, (0, 0))
                    else:
                        # Transition complete
                        self.transition_active = False
                        self.transition_surface = None

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
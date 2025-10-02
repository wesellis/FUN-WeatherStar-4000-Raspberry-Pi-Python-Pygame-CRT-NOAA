#!/usr/bin/env python3
"""
WeatherStar 4000+ Display Functions Module

All draw_* methods extracted from the main weatherstar4000.py file
to reduce the main file size and improve organization.
"""

import pygame
import pygame.gfxdraw
import requests
import json
import time
import os
import sys
import io
from datetime import datetime, timedelta
from pathlib import Path
import math
import random
import webbrowser

# Constants from main file
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
DISPLAY_DURATION_MS = 15000
SCROLL_SPEED = 100

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
    'dark_blue': (0, 50, 100),         # Splash screen background
    'orange': (255, 140, 0),           # WeatherStar accent orange
}


class WeatherStarDisplays:
    """Display methods for WeatherStar 4000+"""

    def __init__(self, weatherstar_instance):
        """Initialize with reference to main WeatherStar instance"""
        self.ws = weatherstar_instance
        # Import logger from main module
        from weatherstar_modules.weatherstar_logger import get_logger
        self.logger = get_logger()

    def draw_background(self, bg_name='1'):
        """Draw background image"""
        if bg_name in self.ws.backgrounds:
            self.ws.screen.blit(self.ws.backgrounds[bg_name], (0, 0))
        else:
            bg = list(self.ws.backgrounds.values())[0] if self.ws.backgrounds else None
            if bg:
                self.ws.screen.blit(bg, (0, 0))

    def draw_header(self, title_top, title_bottom=None, has_noaa=False):
        """Draw standard header matching ws4kp exact layout"""
        # Logo at exact position: top: 25px (moved up 5 pixels), left: 50px
        if 'logo-corner' in self.ws.logos:
            self.ws.screen.blit(self.ws.logos['logo-corner'], (50, 25))

        # Title at exact position: left: 170px
        if title_bottom:
            # Dual line title - top: -3px (relative), bottom: 26px (relative)
            text1 = self.ws.font_title.render(title_top.upper(), True, COLORS['yellow'])
            text2 = self.ws.font_title.render(title_bottom.upper(), True, COLORS['yellow'])
            self.ws.screen.blit(text1, (170, 27))  # Adjusted for absolute positioning
            self.ws.screen.blit(text2, (170, 53))  # 26px below the first line
        else:
            # Single line title - top: 40px
            text = self.ws.font_title.render(title_top.upper(), True, COLORS['yellow'])
            self.ws.screen.blit(text, (170, 40))

        # NOAA logo at exact position: top: 39px, left: 356px
        if has_noaa and 'noaa' in self.ws.logos:
            self.ws.screen.blit(self.ws.logos['noaa'], (356, 39))

        # Time at exact position: left: 415px, right-aligned within 170px width
        time_str = datetime.now().strftime("%I:%M %p").lstrip('0')
        time_text = self.ws.font_small.render(time_str, True, COLORS['white'])
        # Right-align within the box from 415 to 585 (415 + 170)
        time_rect = time_text.get_rect(right=585, y=44)
        self.ws.screen.blit(time_text, time_rect)

    def draw_msn_news(self):
        """Display MSN news headlines with scrolling"""
        self.draw_background('1')
        self.draw_header("MSN", "Top Stories")

        # Fetch MSN headlines with URLs (simulated for now - in production would fetch real news)
        headlines = [
            ("Breaking: Major Winter Storm System Moving Across United States Bringing Heavy Snow and Ice", "https://www.msn.com/weather"),
            ("Technology: Apple Announces Revolutionary New Product Line at Annual Developer Conference", "https://www.msn.com/technology"),
            ("Sports: Underdog Team Wins Championship in Dramatic Overtime Victory Against All Odds", "https://www.msn.com/sports"),
            ("World News: Global Climate Summit Concludes with Historic Agreement Among Nations", "https://www.msn.com/world"),
            ("Business: Stock Market Reaches All-Time High as Economic Recovery Continues to Accelerate", "https://www.msn.com/money"),
            ("Entertainment: Surprise Winners at Annual Award Show Leave Audiences Stunned", "https://www.msn.com/entertainment"),
            ("Health: Scientists Announce Major Medical Breakthrough in Cancer Research Treatment", "https://www.msn.com/health"),
            ("Science: Space Mission Successfully Launches New Era of Deep Space Exploration", "https://www.msn.com/news/technology"),
            ("Politics: Congress Passes Landmark Legislation with Bipartisan Support", "https://www.msn.com/politics"),
            ("Local: Community Rallies Together to Support Families Affected by Recent Events", "https://www.msn.com/local"),
            ("Weather: Hurricane Season Expected to Be More Active Than Normal This Year", "https://www.weather.com"),
            ("Technology: Artificial Intelligence Breakthrough Could Transform Daily Life", "https://www.msn.com/technology")
        ]

        self._display_scrolling_headlines(headlines, "msn")
        self.logger.main_logger.debug("Drew MSN news display")

    def draw_local_news(self):
        """Display local news headlines"""
        self.draw_background('1')

        # Draw header without city name
        self.draw_header("Local News")

        # Draw city name with appropriately sized font
        city_name = self.ws.get_cached_city_name()
        # Use normal font for city name (readable size)
        city_text = self.ws.font_normal.render(city_name.upper(), True, COLORS['yellow'])
        # Center it below LOCAL NEWS
        city_rect = city_text.get_rect(centerx=320, y=65)
        self.ws.screen.blit(city_text, city_rect)

        # Get local news headlines - try real news first, fallback to simulated
        try:
            from weatherstar_modules import get_local_news_real
            headlines = get_local_news_real.get_local_news_by_location(self.ws.lat, self.ws.lon)
        except Exception as e:
            # Fallback to simulated news if real news fails
            self.logger.main_logger.debug(f"Using simulated news: {e}")
            from weatherstar_modules import get_local_news
            headlines = get_local_news.get_local_news_by_location(self.ws.lat, self.ws.lon)

        # Display with normal styling
        self._display_scrolling_headlines(headlines, "local")
        self.logger.main_logger.debug("Drew local news display")

    def draw_reddit_news(self):
        """Display Reddit news headlines with scrolling"""
        self.draw_background('1')
        self.draw_header("Reddit", "Headlines")

        # Fetch Reddit headlines with URLs (simulated for now - in production would use Reddit API)
        headlines = [
            ("r/news: Major Storm System Approaching East Coast with Potential for Historic Snowfall Amounts", "https://reddit.com/r/news"),
            ("r/worldnews: International Summit Concludes with Unexpected Alliance Between Former Rivals", "https://reddit.com/r/worldnews"),
            ("r/technology: New AI Breakthrough Could Revolutionize How We Interact with Computers", "https://reddit.com/r/technology"),
            ("r/science: Scientists Discover New Species in Previously Unexplored Deep Ocean Trench", "https://reddit.com/r/science"),
            ("r/gaming: Popular Game Franchise Gets Surprise Major Update After Years of Silence", "https://reddit.com/r/gaming"),
            ("r/movies: Independent Film Breaks Box Office Records in Limited Release", "https://reddit.com/r/movies"),
            ("r/sports: Underdog Team's Cinderella Story Continues with Another Upset Victory", "https://reddit.com/r/sports"),
            ("r/space: New Images from James Webb Space Telescope Reveal Stunning Cosmic Phenomena", "https://reddit.com/r/space"),
            ("r/AskReddit: What's the most interesting historical fact you know that sounds fake?", "https://reddit.com/r/AskReddit"),
            ("r/todayilearned: TIL that honey never spoils and archaeologists have found 3000 year old honey", "https://reddit.com/r/todayilearned"),
            ("r/EarthPorn: Sunrise over the Grand Canyon after fresh snowfall [OC] [4032x3024]", "https://reddit.com/r/EarthPorn"),
            ("r/dataisbeautiful: [OC] Visualization of global temperature changes over the last century", "https://reddit.com/r/dataisbeautiful")
        ]

        self._display_scrolling_headlines(headlines, "reddit")
        self.logger.main_logger.debug("Drew Reddit news display")

    def _display_scrolling_headlines(self, headlines, source):
        """Display news with vertical scrolling from bottom"""
        # Initialize vertical scroll position if not exists
        if not hasattr(self.ws, 'news_vertical_scroll'):
            self.ws.news_vertical_scroll = {}

        # Initialize clickable areas tracking
        if not hasattr(self.ws, 'clickable_headlines'):
            self.ws.clickable_headlines = []

        # Clear clickable areas for this frame
        self.ws.clickable_headlines = []

        if source not in self.ws.news_vertical_scroll:
            self.ws.news_vertical_scroll[source] = 200  # Start 25% up the screen (was 480)

        # Use readable font
        try:
            news_font = pygame.font.Font(self.ws.font_paths.get('small'), 20)
            title_font = pygame.font.Font(self.ws.font_paths.get('normal'), 22)
        except:
            news_font = pygame.font.Font(None, 20)
            title_font = pygame.font.Font(None, 22)

        # Create clipping region for scrolling area (reduced width by 30px total, height by 22px at bottom)
        clip_rect = pygame.Rect(55, 100, 530, 298)  # Was 40, 100, 560, 320 - reduced bottom by 22px total
        self.ws.screen.set_clip(clip_rect)

        # Calculate total height needed for all headlines
        line_height = 28
        headline_spacing = 15  # Extra space between headlines

        # Draw headlines scrolling up
        y_pos = self.ws.news_vertical_scroll[source]

        for i, headline_data in enumerate(headlines[:20], 1):  # Show up to 20 headlines
            # Extract text and URL from tuple
            if isinstance(headline_data, tuple):
                headline_text, headline_url = headline_data
            else:
                # Fallback for old format
                headline_text = headline_data
                headline_url = None

            # Only draw if potentially visible
            if y_pos > -200 and y_pos < 500:
                # Number color based on source
                num_color = COLORS['yellow']  # Always yellow for consistency
                num_text = title_font.render(f"{i}.", True, num_color)
                self.ws.screen.blit(num_text, (65, y_pos))  # Was 50, now 65 (+15px)

                # Word-wrap the headline for better readability
                words = headline_text.split()
                lines = []
                current_line = ""

                for word in words:
                    test_line = current_line + " " + word if current_line else word
                    test_surface = news_font.render(test_line, True, COLORS['white'])

                    if test_surface.get_width() > 470:  # Max width for text (was 500, now 470)
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                    else:
                        current_line = test_line

                if current_line:
                    lines.append(current_line)

                # Track the clickable area if URL is available
                if headline_url and y_pos > 100 and y_pos < 398:
                    # Calculate bounding box for this headline
                    headline_height = len(lines) * line_height
                    clickable_rect = pygame.Rect(65, y_pos, 520, headline_height)
                    self.ws.clickable_headlines.append((clickable_rect, headline_url))

                # Draw wrapped lines with color coding
                line_y = y_pos
                for line in lines:
                    if line_y > 95 and line_y < 398:  # Only draw visible lines within clip region (adjusted for shorter area)
                        # Check if this is a Reddit headline and color-code subreddits
                        if source == "reddit" and ("r/" in line or "/r/" in line):
                            # Split the line to find and color r/ mentions
                            x_pos = 95
                            parts = line.split()
                            for part in parts:
                                if part.startswith("r/") or part.startswith("/r/"):
                                    # Color subreddit mentions in cyan
                                    colored_text = news_font.render(part, True, COLORS['cyan'])
                                    self.ws.screen.blit(colored_text, (x_pos, line_y))
                                    x_pos += colored_text.get_width() + 5
                                elif part.startswith("[") and part.endswith("]"):
                                    # Color bracketed tags in yellow
                                    colored_text = news_font.render(part, True, COLORS['yellow'])
                                    self.ws.screen.blit(colored_text, (x_pos, line_y))
                                    x_pos += colored_text.get_width() + 5
                                else:
                                    # Regular white text
                                    text_part = news_font.render(part, True, COLORS['white'])
                                    self.ws.screen.blit(text_part, (x_pos, line_y))
                                    x_pos += text_part.get_width() + 5
                        elif source == "local":
                            # For local news, color-code like MSN with categories
                            if ":" in line:
                                parts = line.split(":", 1)
                                if len(parts) == 2:
                                    category = parts[0]
                                    # Check for emergency keywords
                                    if any(word in category.upper() for word in ["EMERGENCY", "BREAKING", "ALERT"]):
                                        category_text = news_font.render(category + ":", True, COLORS['red'])
                                        self.ws.screen.blit(category_text, (95, line_y))
                                        rest_text = news_font.render(parts[1], True, COLORS['white'])
                                        self.ws.screen.blit(rest_text, (95 + category_text.get_width(), line_y))
                                    else:
                                        # Regular categories in cyan
                                        category_text = news_font.render(category + ":", True, COLORS['cyan'])
                                        self.ws.screen.blit(category_text, (95, line_y))
                                        rest_text = news_font.render(parts[1], True, COLORS['white'])
                                        self.ws.screen.blit(rest_text, (95 + category_text.get_width(), line_y))
                                else:
                                    # Just draw in white
                                    text_surface = news_font.render(line, True, COLORS['white'])
                                    self.ws.screen.blit(text_surface, (95, line_y))
                            else:
                                # No colon, just draw in white
                                text_surface = news_font.render(line, True, COLORS['white'])
                                self.ws.screen.blit(text_surface, (95, line_y))
                        else:
                            # For MSN or non-Reddit content
                            if source == "msn" and ":" in line:
                                # Color the category (text before first colon) in cyan
                                parts = line.split(":", 1)
                                if len(parts) == 2:
                                    category = parts[0]
                                    rest = ":" + parts[1]

                                    # Special handling for BREAKING
                                    if category == "BREAKING":
                                        category_text = news_font.render(category + ":", True, COLORS['red'])
                                        self.ws.screen.blit(category_text, (95, line_y))
                                        rest_text = news_font.render(parts[1], True, COLORS['white'])
                                        self.ws.screen.blit(rest_text, (95 + category_text.get_width(), line_y))
                                    elif category == "UPDATE":
                                        category_text = news_font.render(category + ":", True, COLORS['yellow'])
                                        self.ws.screen.blit(category_text, (95, line_y))
                                        rest_text = news_font.render(parts[1], True, COLORS['white'])
                                        self.ws.screen.blit(rest_text, (95 + category_text.get_width(), line_y))
                                    else:
                                        # Regular categories in cyan
                                        category_text = news_font.render(category + ":", True, COLORS['cyan'])
                                        self.ws.screen.blit(category_text, (95, line_y))
                                        rest_text = news_font.render(parts[1], True, COLORS['white'])
                                        self.ws.screen.blit(rest_text, (95 + category_text.get_width(), line_y))
                                else:
                                    text_surface = news_font.render(line, True, COLORS['white'])
                                    self.ws.screen.blit(text_surface, (95, line_y))
                            else:
                                # Regular text
                                text_surface = news_font.render(line, True, COLORS['white'])
                                self.ws.screen.blit(text_surface, (95, line_y))
                    line_y += line_height

                # Move to next headline position
                y_pos = line_y + headline_spacing
            else:
                # Still calculate position even if not drawing
                y_pos += line_height * 2 + headline_spacing

        # Remove clipping
        self.ws.screen.set_clip(None)

        # Update scroll position (slow upward scroll)
        self.ws.news_vertical_scroll[source] -= 0.5  # Slow scroll speed

        # Reset when all headlines have scrolled past the top
        if y_pos < 100:
            self.ws.news_vertical_scroll[source] = 440  # Reset to bottom but visible

        # Footer with update time (outside clipping area)
        update_time = datetime.now().strftime("%I:%M %p")
        footer = news_font.render(f"Updated: {update_time}", True, COLORS['yellow'])
        footer_rect = footer.get_rect(center=(320, 440))
        self.ws.screen.blit(footer, footer_rect)

    def draw_current_conditions(self):
        """Draw Current Conditions screen matching ws4kp exact layout"""
        self.draw_background('1')
        self.draw_header("Current", "Conditions", has_noaa=True)

        current = self.ws.weather_data.get('current', {})
        if not current:
            self.logger.main_logger.debug("No current data to display")
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
            temp_text = self.ws.font_large.render(f"{temp_f}°", True, COLORS['white'])
            temp_rect = temp_text.get_rect(center=(left_col_center, 140))
            self.ws.screen.blit(temp_text, temp_rect)

        # Weather condition (below temp)
        description = current.get('textDescription', '')
        if description:
            # Shorten if too long
            if len(description) > 15:
                description = description[:15]
            desc_text = self.ws.font_extended.render(description, True, COLORS['white'])
            desc_rect = desc_text.get_rect(center=(left_col_center, 190))
            self.ws.screen.blit(desc_text, desc_rect)

        # Weather icon (centered below condition) with animation support
        icon_name = self._get_icon_name(current.get('icon', ''))
        icon = None

        # Try animated icon first
        if self.ws.icon_manager:
            icon = self.ws.icon_manager.get_icon(icon_name, 86, 75)  # Standard icon size

        # Fallback to static icon
        if not icon and icon_name and icon_name in self.ws.icons:
            icon = self.ws.icons[icon_name]

        if icon:
            icon_rect = icon.get_rect(center=(left_col_center, 260))
            self.ws.screen.blit(icon, icon_rect)

        # Wind information with flex layout
        wind_y = 320
        wind_speed = current.get('windSpeed', {}).get('value')
        wind_dir = current.get('windDirection', {}).get('value')

        # Wind container - flex with 50% each side
        wind_label = self.ws.font_extended.render("Wind:", True, COLORS['white'])
        self.ws.screen.blit(wind_label, (content_left + 10, wind_y))  # margin-left: 10px

        # Always show wind info, even if None
        if wind_speed is not None and wind_speed > 0:
            wind_mph = int(wind_speed * 0.621371)
            direction = self._get_wind_direction(wind_dir) if wind_dir else ''
            # Format like ws4kp: direction padded to 3, speed right-aligned to 3
            wind_str = f"{direction.ljust(3)}{str(wind_mph).rjust(3)}"
        elif wind_speed is not None and wind_speed == 0:
            wind_str = "Calm"
        else:
            # Show "N/A" if no wind data available
            wind_str = "N/A"

        wind_text = self.ws.font_extended.render(wind_str, True, COLORS['white'])
        # Right side of flex container
        wind_rect = wind_text.get_rect(right=content_left + 245, y=wind_y)
        self.ws.screen.blit(wind_text, wind_rect)

        # Wind gusts (right-aligned below wind)
        wind_gust = current.get('windGust', {}).get('value')
        if wind_gust is not None:
            gust_mph = int(wind_gust * 0.621371)
            gust_text = self.ws.font_normal.render(f"Gusts to {gust_mph}", True, COLORS['white'])
            gust_rect = gust_text.get_rect(right=content_left + 245, y=wind_y + 35)
            self.ws.screen.blit(gust_text, gust_rect)

        # RIGHT COLUMN: starts at 64 + 257 = 321px from left edge
        right_col_x = content_left + 257  # Small gap between columns
        label_x = right_col_x + 20  # Labels have margin-left: 20px
        value_x = 640 - 64 - 10  # Right edge minus margin minus 10px

        # Location in yellow at top
        y_pos = 100
        location_str = f"{self.ws.location.get('city', '')}".strip()[:20]  # Max 20 chars
        if location_str:
            location_text = self.ws.font_normal.render(location_str, True, COLORS['yellow'])
            self.ws.screen.blit(location_text, (right_col_x, y_pos))
            y_pos += 30  # Spacing before date

        # Date below location
        from datetime import datetime
        date_str = datetime.now().strftime("%a %b %d").upper()  # "WED OCT 02"
        date_text = self.ws.font_small.render(date_str, True, COLORS['white'])
        self.ws.screen.blit(date_text, (right_col_x, y_pos))
        y_pos += 30  # Spacing before data rows

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
            if hasattr(self.ws, 'settings') and self.ws.settings.get('show_trends', True):
                if not hasattr(self.ws, 'weather_trends'):
                    self.ws.weather_trends = {'temp': [], 'pressure': []}

                self.ws.weather_trends['pressure'].append(pressure_inhg)
                if len(self.ws.weather_trends['pressure']) > 5:
                    self.ws.weather_trends['pressure'].pop(0)

                if len(self.ws.weather_trends['pressure']) >= 2:
                    pressure_change = self.ws.weather_trends['pressure'][-1] - self.ws.weather_trends['pressure'][0]
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
            label_text = self.ws.font_normal.render(label, True, COLORS['white'])
            self.ws.screen.blit(label_text, (label_x, y_pos))

            # Value right-aligned with margin-right: 10px
            value_text = self.ws.font_normal.render(value, True, COLORS['white'])
            value_rect = value_text.get_rect(right=value_x, y=y_pos)
            self.ws.screen.blit(value_text, value_rect)

            y_pos += 36  # line-height: 24px + margin-bottom: 12px

    def draw_local_forecast(self):
        """Draw Local Forecast screen with 3-day forecast layout"""
        self.draw_background('2')
        self.draw_header("Local", "Forecast", has_noaa=True)

        forecast = self.ws.weather_data.get('forecast', {})
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

        # Column positions - adjust first column right 10px, last column left 10px
        columns = [
            start_x + 10,  # Move TODAY box right 10px
            start_x + col_width + col_spacing,
            start_x + (col_width + col_spacing) * 2 - 10  # Move last column left 10px
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
            name_text = self.ws.font_extended.render(display_name, True, COLORS['yellow'])
            name_rect = name_text.get_rect(center=(col_x + col_width // 2, 120))
            self.ws.screen.blit(name_text, name_rect)

            # Temperature
            temp = period.get('temperature')
            if temp is not None:
                temp_text = self.ws.font_normal.render(f"{temp}°", True, COLORS['white'])
                temp_rect = temp_text.get_rect(center=(col_x + col_width // 2, 150))
                self.ws.screen.blit(temp_text, temp_rect)

            # Get forecast text and wrap it
            detailed = period.get('detailedForecast', '')
            words = detailed.split()

            # Word wrap to fit column - make text area 5px thinner on each side
            lines = []
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                test_surf = self.ws.font_forecast.render(test_line, True, COLORS['white'])

                if test_surf.get_width() > col_width - 20 and current_line:  # Changed from -10 to -20 (5px each side)
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    current_line.append(word)

            if current_line:
                lines.append(' '.join(current_line))

            # Draw forecast text lines with reduced spacing
            y_pos = 180
            for line in lines[:10]:  # Max 10 lines per column
                text_surf = self.ws.font_forecast.render(line, True, COLORS['white'])
                # Center text in column
                text_rect = text_surf.get_rect(center=(col_x + col_width // 2, y_pos))
                self.ws.screen.blit(text_surf, text_rect)
                y_pos += 18  # Reduced from 22 to 18 for tighter spacing

        self.logger.main_logger.debug("Drew Local Forecast display")

    def draw_extended_forecast(self):
        """Draw Extended Forecast screen with proper ws4kp column layout"""
        self.draw_background('3')
        self.draw_header("Extended", "Forecast")

        # Date at top center
        from datetime import datetime
        date_str = datetime.now().strftime("%A, %B %d, %Y")  # "Wednesday, October 02, 2025"
        date_text = self.ws.font_small.render(date_str, True, COLORS['white'])
        date_rect = date_text.get_rect(center=(320, 90))
        self.ws.screen.blit(date_text, date_rect)

        forecast = self.ws.weather_data.get('forecast', {})
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

            name_text = self.ws.font_extended.render(day_name, True, COLORS['yellow'])
            name_rect = name_text.get_rect(center=(col_center, 120))
            self.ws.screen.blit(name_text, name_rect)

            # Icon (with animation support, maintain aspect ratio, max 75px height)
            icon_name = self._get_icon_name(day_period.get('icon', ''))
            original_icon = None

            # Try animated icon first
            if self.ws.icon_manager:
                original_icon = self.ws.icon_manager.get_icon(icon_name)

            # Fallback to static icon
            if not original_icon and icon_name and icon_name in self.ws.icons:
                original_icon = self.ws.icons[icon_name]

            if original_icon:
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
                self.ws.screen.blit(icon, icon_rect)

            # Condition text (centered, height 74px area)
            short_forecast = day_period.get('shortForecast', '')
            # Split into words and wrap if needed
            words = short_forecast.split()
            lines = []
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                test_surf = self.ws.font_small.render(test_line, True, COLORS['white'])
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
                cond_text = self.ws.font_small.render(line, True, COLORS['white'])
                cond_rect = cond_text.get_rect(center=(col_center, cond_y))
                self.ws.screen.blit(cond_text, cond_rect)
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
                lo_label = self.ws.font_small.render("Lo", True, COLORS['blue'])
                lo_label_rect = lo_label.get_rect(center=(lo_x_center, 310))
                self.ws.screen.blit(lo_label, lo_label_rect)

                lo_text = self.ws.font_normal.render(f"{lo_temp}°", True, COLORS['white'])
                lo_text_rect = lo_text.get_rect(center=(lo_x_center, 335))
                self.ws.screen.blit(lo_text, lo_text_rect)

            # Hi temp (right side of temperature area)
            hi_x_center = x_pos + day_width - temp_block_width // 2 - 10
            if hi_temp is not None:
                hi_label = self.ws.font_small.render("Hi", True, COLORS['yellow'])
                hi_label_rect = hi_label.get_rect(center=(hi_x_center, 310))
                self.ws.screen.blit(hi_label, hi_label_rect)

                hi_text = self.ws.font_normal.render(f"{hi_temp}°", True, COLORS['white'])
                hi_text_rect = hi_text.get_rect(center=(hi_x_center, 335))
                self.ws.screen.blit(hi_text, hi_text_rect)

            day_count += 1

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

    def draw_hourly_forecast(self):
        """Draw Hourly Forecast screen with actual hourly data and scrolling"""
        self.ws.draw_background('4')
        self.ws.draw_header("Hourly", "Forecast")

        # Get hourly forecast data
        hourly = self.ws.weather_data.get('hourly', {})
        periods = hourly.get('periods', [])

        if not periods:
            # Fallback to regular forecast if no hourly data
            forecast = self.ws.weather_data.get('forecast', {})
            periods = forecast.get('periods', [])

        # Create continuous scrolling effect
        scroll_time = pygame.time.get_ticks() // 50  # Smooth scroll speed
        content_top = 125  # Content area top
        content_height = 265  # Visible content area height
        line_height = 25

        # Calculate total content height for seamless looping
        total_lines = len(periods[:24]) if periods else 0
        total_content_height = total_lines * line_height

        # Continuous scroll position (loops seamlessly)
        scroll_offset = scroll_time % (total_content_height + content_height)

        # Draw header with adjusted spacing - TIME moved right, TEMP closer
        header_text = self.ws.font_small.render("TIME  TEMP  CONDITIONS", True, COLORS['yellow'])
        self.ws.screen.blit(header_text, (65, content_top))

        # Create clipping region to hide scrolling text outside content area
        clip_rect = pygame.Rect(0, content_top + 30, SCREEN_WIDTH, content_height)
        self.ws.screen.set_clip(clip_rect)

        # Draw hourly periods with continuous scrolling
        base_y = content_top + 30 + content_height - scroll_offset

        # Draw periods twice for seamless loop
        for loop in range(2):
            y_offset = loop * total_content_height

            for i, period in enumerate(periods[:24]):  # Show up to 24 hours
                y_pos = base_y + y_offset + (i * line_height)

                # Only draw if visible in the clipping area
                if y_pos >= content_top and y_pos <= content_top + content_height + 50:
                    # Parse time from period name or startTime
                    if 'startTime' in period:
                        try:
                            # Parse ISO format time
                            time_str = period['startTime']
                            from datetime import datetime
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

                    # Format the line with tighter spacing - TIME and TEMP closer together
                    text = f"{time_display:6}{temp_display:5}{short}"

                    # Use appropriate font
                    period_text = self.ws.font_normal.render(text, True, COLORS['white'])
                    self.ws.screen.blit(period_text, (65, y_pos))

        # Remove clipping
        self.ws.screen.set_clip(None)

        self.logger.main_logger.debug("Drew Hourly Forecast display with scrolling")

    def draw_latest_observations(self):
        """Draw Latest Observations screen"""
        self.ws.draw_background('5')
        self.ws.draw_header("Latest", "Observations")

        # Show current observation
        current = self.ws.weather_data.get('current', {})

        y_pos = 120
        station_name = current.get('stationName', 'Station')
        station_text = self.ws.font_normal.render(f"Station: {station_name}", True, COLORS['yellow'])
        self.ws.screen.blit(station_text, (60, y_pos))

        y_pos += 40

        # Temperature
        temp_c = current.get('temperature', {}).get('value')
        if temp_c is not None:
            temp_f = int(temp_c * 9/5 + 32)
            temp_text = self.ws.font_normal.render(f"Temperature: {temp_f}°", True, COLORS['white'])
            self.ws.screen.blit(temp_text, (60, y_pos))
            y_pos += 30

        # Wind
        wind_speed = current.get('windSpeed', {}).get('value')
        if wind_speed is not None:
            wind_mph = int(wind_speed * 0.621371)
            wind_text = self.ws.font_normal.render(f"Wind: {wind_mph} mph", True, COLORS['white'])
            self.ws.screen.blit(wind_text, (60, y_pos))
            y_pos += 30

        # Observation time
        timestamp = current.get('timestamp')
        if timestamp:
            try:
                from datetime import datetime
                obs_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = obs_time.strftime("%I:%M %p %m/%d").lstrip('0')
                time_text = self.ws.font_normal.render(f"Observed: {time_str}", True, COLORS['white'])
                self.ws.screen.blit(time_text, (60, y_pos))
            except:
                pass

    def draw_travel_cities(self):
        """Draw Travel Cities weather - major US cities"""
        self.ws.draw_background('5')  # Use a cleaner background
        self.ws.draw_header("Travel Cities", "Weather")

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
                pygame.draw.rect(self.ws.screen, (0, 0, 60), bar_rect)

            # City name (yellow, left aligned)
            city_text = self.ws.font_normal.render(city, True, COLORS['yellow'])
            self.ws.screen.blit(city_text, (80, y_pos))

            # Temperature (white, centered) - using normal font instead of large
            temp_text = self.ws.font_normal.render(f"{temp}°", True, COLORS['white'])
            self.ws.screen.blit(temp_text, (320, y_pos))

            # Conditions (white, right side)
            cond_text = self.ws.font_normal.render(conditions, True, COLORS['white'])
            self.ws.screen.blit(cond_text, (400, y_pos))

            y_pos += 35  # Line spacing

        self.logger.main_logger.debug("Drew Travel Cities display")

        # Debug radar function
        self.logger.main_logger.debug("Drew Radar display")

    def draw_radar(self):
        """Draw animated radar display with RainViewer data"""
        # Classic blue background
        self.ws.draw_background('6')
        self.ws.draw_header("Live", "Radar")

        # Radar display area
        radar_rect = pygame.Rect(70, 100, 500, 300)

        # Display animated radar if available
        if hasattr(self.ws, 'radar_frames') and self.ws.radar_frames:
            # Animate through frames
            current_time = pygame.time.get_ticks()

            # Change frame every 500ms for smooth animation
            if not hasattr(self.ws, 'radar_last_update'):
                self.ws.radar_last_update = current_time
                self.ws.radar_frame_index = 0

            if current_time - self.ws.radar_last_update > 500:
                self.ws.radar_frame_index = (self.ws.radar_frame_index + 1) % len(self.ws.radar_frames)
                self.ws.radar_last_update = current_time

            # Display current frame
            frame = self.ws.radar_frames[self.ws.radar_frame_index]
            scaled_frame = pygame.transform.scale(frame, (500, 300))

            # Blit normally without special blending
            self.ws.screen.blit(scaled_frame, radar_rect)

            # Show frame indicator
            frame_text = self.ws.font_tiny.render(f"Frame {self.ws.radar_frame_index + 1}/{len(self.ws.radar_frames)}", True, COLORS['white'])
            self.ws.screen.blit(frame_text, (radar_rect.right - 80, radar_rect.bottom - 20))

        elif hasattr(self.ws, 'radar_image') and self.ws.radar_image:
            # Static radar image
            scaled_img = pygame.transform.scale(self.ws.radar_image, (500, 300))

            # Blit normally without special blending
            self.ws.screen.blit(scaled_img, radar_rect)
        else:
            # Loading message - draw dark background only when no radar
            pygame.draw.rect(self.ws.screen, (0, 20, 40), radar_rect)

            msg = self.ws.font_large.render("RADAR UPDATING", True, COLORS['yellow'])
            msg_rect = msg.get_rect(center=radar_rect.center)
            self.ws.screen.blit(msg, msg_rect)

            msg2 = self.ws.font_normal.render("Connecting to RainViewer...", True, COLORS['white'])
            msg2_rect = msg2.get_rect(center=(radar_rect.centerx, radar_rect.centery + 30))
            self.ws.screen.blit(msg2, msg2_rect)

        # Draw border on top of everything
        pygame.draw.rect(self.ws.screen, COLORS['yellow'], radar_rect, 2)

        # Location and timestamp
        location = f"{self.ws.location.get('city', '')}, {self.ws.location.get('state', '')}"
        loc_text = self.ws.font_normal.render(location.upper(), True, COLORS['yellow'])
        loc_rect = loc_text.get_rect(center=(320, 420))
        self.ws.screen.blit(loc_text, loc_rect)

        # RainViewer attribution (small, authentic style)
        attr_text = self.ws.font_tiny.render("Radar by RainViewer", True, COLORS['white'])
        self.ws.screen.blit(attr_text, (radar_rect.left, radar_rect.bottom + 5))

        # Legend - draw on top layer
        self._draw_radar_legend(radar_rect)

    def _draw_us_map_outline(self, radar_rect):
        """Draw simple US map outline on radar"""
        # Scale coordinates to fit radar rect
        scale_x = radar_rect.width / 512
        scale_y = radar_rect.height / 512

        # US outline points (scaled)
        us_points = [
            (100 * scale_x + radar_rect.x, 200 * scale_y + radar_rect.y),
            (150 * scale_x + radar_rect.x, 180 * scale_y + radar_rect.y),
            (200 * scale_x + radar_rect.x, 170 * scale_y + radar_rect.y),
            (280 * scale_x + radar_rect.x, 165 * scale_y + radar_rect.y),
            (360 * scale_x + radar_rect.x, 170 * scale_y + radar_rect.y),
            (420 * scale_x + radar_rect.x, 180 * scale_y + radar_rect.y),
            (450 * scale_x + radar_rect.x, 200 * scale_y + radar_rect.y),
            (460 * scale_x + radar_rect.x, 250 * scale_y + radar_rect.y),
            (450 * scale_x + radar_rect.x, 300 * scale_y + radar_rect.y),
            (420 * scale_x + radar_rect.x, 330 * scale_y + radar_rect.y),
            (360 * scale_x + radar_rect.x, 340 * scale_y + radar_rect.y),
            (280 * scale_x + radar_rect.x, 345 * scale_y + radar_rect.y),
            (200 * scale_x + radar_rect.x, 340 * scale_y + radar_rect.y),
            (150 * scale_x + radar_rect.x, 320 * scale_y + radar_rect.y),
            (100 * scale_x + radar_rect.x, 280 * scale_y + radar_rect.y),
            (90 * scale_x + radar_rect.x, 240 * scale_y + radar_rect.y),
            (100 * scale_x + radar_rect.x, 200 * scale_y + radar_rect.y)
        ]

        # Draw outline
        pygame.draw.lines(self.ws.screen, (60, 60, 60), True, us_points, 1)

    def _draw_radar_legend(self, radar_rect):
        """Draw radar intensity legend"""
        legend_y = radar_rect.top + 10
        legend_x = radar_rect.left + 10

        # Rain intensity legend (simple colored boxes)
        intensities = [
            ((0, 100, 0), "Light"),
            ((255, 255, 0), "Moderate"),
            ((255, 140, 0), "Heavy"),
            ((255, 0, 0), "Intense")
        ]

        for i, (color, label) in enumerate(intensities):
            # Color box
            box_rect = pygame.Rect(legend_x, legend_y + (i * 20), 15, 15)
            pygame.draw.rect(self.ws.screen, color, box_rect)
            pygame.draw.rect(self.ws.screen, COLORS['white'], box_rect, 1)

            # Label
            label_text = self.ws.font_tiny.render(label, True, COLORS['white'])
            self.ws.screen.blit(label_text, (legend_x + 20, legend_y + (i * 20)))

        self.logger.main_logger.debug("Drew Radar display")

    def draw_almanac(self):
        """Draw Almanac screen with weather statistics and records"""
        self.ws.draw_background('4')  # Use the hourly forecast background
        self.ws.draw_header("Weather", "Almanac")

        current = self.ws.weather_data.get('current', {})

        # Get current date/time
        from datetime import datetime
        now = datetime.now()
        date_str = now.strftime("%B %d, %Y")

        # Title
        date_text = self.ws.font_normal.render(f"Weather Statistics for {date_str}", True, COLORS['yellow'])
        date_rect = date_text.get_rect(center=(320, 100))
        self.ws.screen.blit(date_text, date_rect)

        y_pos = 130  # Move up by 10px

        # Current Stats
        stats_title = self.ws.font_extended.render("CURRENT CONDITIONS", True, COLORS['yellow'])
        self.ws.screen.blit(stats_title, (60, y_pos))
        y_pos += 35

        # Temperature
        temp_c = current.get('temperature', {}).get('value')
        if temp_c is not None:
            temp_f = int(temp_c * 9/5 + 32)
            temp_text = self.ws.font_normal.render(f"Temperature: {temp_f}°F", True, COLORS['white'])
            self.ws.screen.blit(temp_text, (80, y_pos))
            y_pos += 25

        # Humidity
        humidity = current.get('relativeHumidity', {}).get('value')
        if humidity:
            humid_text = self.ws.font_normal.render(f"Humidity: {humidity:.0f}%", True, COLORS['white'])
            self.ws.screen.blit(humid_text, (80, y_pos))
            y_pos += 25

        # Dewpoint
        dewpoint_c = current.get('dewpoint', {}).get('value')
        if dewpoint_c is not None:
            dewpoint_f = int(dewpoint_c * 9/5 + 32)
            dew_text = self.ws.font_normal.render(f"Dewpoint: {dewpoint_f}°F", True, COLORS['white'])
            self.ws.screen.blit(dew_text, (80, y_pos))
            y_pos += 25

        # Pressure
        pressure = current.get('barometricPressure', {}).get('value')
        if pressure:
            pressure_inhg = pressure * 0.00029530
            press_text = self.ws.font_normal.render(f"Pressure: {pressure_inhg:.2f} in", True, COLORS['white'])
            self.ws.screen.blit(press_text, (80, y_pos))
            y_pos += 25

        # Visibility
        visibility = current.get('visibility', {}).get('value')
        if visibility:
            vis_miles = visibility / 1609.34
            vis_text = self.ws.font_normal.render(f"Visibility: {vis_miles:.1f} miles", True, COLORS['white'])
            self.ws.screen.blit(vis_text, (80, y_pos))
            y_pos += 35

        # Sun/Moon Data (simulated)
        y_pos += 10
        sun_title = self.ws.font_extended.render("SUN & MOON", True, COLORS['yellow'])
        self.ws.screen.blit(sun_title, (60, y_pos))
        y_pos += 35

        # Calculate approximate sunrise/sunset for display
        sunrise_text = self.ws.font_normal.render("Sunrise: 6:45 AM", True, COLORS['white'])
        self.ws.screen.blit(sunrise_text, (80, y_pos))
        y_pos += 25

        sunset_text = self.ws.font_normal.render("Sunset: 7:30 PM", True, COLORS['white'])
        self.ws.screen.blit(sunset_text, (80, y_pos))
        y_pos += 25

        moon_text = self.ws.font_normal.render("Moon Phase: Waxing Gibbous", True, COLORS['white'])
        self.ws.screen.blit(moon_text, (80, y_pos))

        self.logger.main_logger.debug("Drew Almanac display")

    def draw_hazards(self):
        """Draw Weather Hazards/Alerts screen"""
        self.ws.draw_background('3')  # Reuse extended forecast background
        self.ws.draw_header("Weather", "Alerts")

        # Check for any alerts in the forecast data
        forecast = self.ws.weather_data.get('forecast', {})

        y_pos = 175  # Moved down 35px from 140 (was 120, then 140, now 175)

        # For now, show general hazard information
        # In a full implementation, this would fetch actual alerts from NOAA

        # Title
        alert_title = self.ws.font_extended.render("CURRENT HAZARDS", True, COLORS['yellow'])
        self.ws.screen.blit(alert_title, (60, y_pos))
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
                alert_text = self.ws.font_normal.render(f"{name}:", True, COLORS['yellow'])
                self.ws.screen.blit(alert_text, (80, y_pos))
                y_pos += 25

                # Wrap and display the forecast with potential hazards
                words = period.get('shortForecast', '').split()
                line = []
                for word in words:
                    line.append(word)
                    test_line = ' '.join(line)
                    test_surf = self.ws.font_normal.render(test_line, True, COLORS['white'])
                    if test_surf.get_width() > 480:
                        # Draw the line without the last word
                        line.pop()
                        if line:
                            text_surf = self.ws.font_normal.render(' '.join(line), True, COLORS['white'])
                            self.ws.screen.blit(text_surf, (100, y_pos))
                            y_pos += 25
                        line = [word]

                # Draw remaining words
                if line:
                    text_surf = self.ws.font_normal.render(' '.join(line), True, COLORS['white'])
                    self.ws.screen.blit(text_surf, (100, y_pos))
                    y_pos += 35

        if not has_alerts:
            # No alerts
            no_alert = self.ws.font_normal.render("No active weather alerts at this time", True, COLORS['white'])
            no_alert_rect = no_alert.get_rect(center=(320, 200))
            self.ws.screen.blit(no_alert, no_alert_rect)

            # Safety tips
            y_pos = 250
            tips_title = self.ws.font_extended.render("WEATHER SAFETY TIPS", True, COLORS['yellow'])
            self.ws.screen.blit(tips_title, (60, y_pos))
            y_pos += 35

            tips = [
                "• Monitor weather conditions regularly",
                "• Have an emergency kit prepared",
                "• Know your evacuation routes",
                "• Sign up for weather alerts"
            ]

            for tip in tips:
                tip_text = self.ws.font_normal.render(tip, True, COLORS['white'])
                self.ws.screen.blit(tip_text, (80, y_pos))
                y_pos += 25

        self.logger.main_logger.debug("Drew Hazards display")

    def draw_marine_forecast(self):
        """Draw Marine/Beach Forecast"""
        self.ws.draw_background('3')  # Use background 3 for marine
        self.ws.draw_header("Marine", "Forecast")

        y_pos = 120

        # Beach/Marine conditions
        title = self.ws.font_extended.render("COASTAL CONDITIONS", True, COLORS['yellow'])
        self.ws.screen.blit(title, (60, y_pos))
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
            label_text = self.ws.font_normal.render(f"{label}:", True, COLORS['white'])
            self.ws.screen.blit(label_text, (80, y_pos))

            # Value (color based on severity)
            color = COLORS['yellow'] if "MODERATE" in value or "High" in value else COLORS['white']
            value_text = self.ws.font_normal.render(value, True, color)
            self.ws.screen.blit(value_text, (300, y_pos))

            y_pos += 28

        self.logger.main_logger.debug("Drew Marine Forecast display")

    def draw_air_quality(self):
        """Draw Air Quality & Health"""
        self.ws.draw_background('5')
        self.ws.draw_header("Air Quality", "& Health")

        # Two column layout for better organization
        left_x = 80
        right_x = 350
        y_pos = 120

        # LEFT COLUMN - Air Quality Index
        aqi_title = self.ws.font_normal.render("AIR QUALITY INDEX", True, COLORS['yellow'])
        self.ws.screen.blit(aqi_title, (left_x, y_pos))
        y_pos += 30

        # AQI value (simulated)
        aqi_value = 45
        aqi_text = "GOOD"
        aqi_color = (0, 255, 0)  # Green for good

        # Draw AQI box
        pygame.draw.rect(self.ws.screen, aqi_color, (left_x, y_pos, 60, 40), 2)
        aqi_num = self.ws.font_normal.render(str(aqi_value), True, aqi_color)
        num_rect = aqi_num.get_rect(center=(left_x + 30, y_pos + 20))
        self.ws.screen.blit(aqi_num, num_rect)

        aqi_desc = self.ws.font_small.render(aqi_text, True, aqi_color)
        self.ws.screen.blit(aqi_desc, (left_x + 70, y_pos + 12))
        y_pos += 50

        # AQI scale reference
        scale = [
            ("0-50", "Good", (0, 255, 0)),
            ("51-100", "Moderate", COLORS['yellow']),
            ("101-150", "Sensitive Groups", (255, 165, 0))
        ]

        for range_txt, desc, color in scale:
            text = self.ws.font_small.render(f"{range_txt}: {desc}", True, color)
            self.ws.screen.blit(text, (left_x, y_pos))
            y_pos += 22

        # RIGHT COLUMN - Pollen counts
        pollen_y = 120
        pollen_title = self.ws.font_normal.render("POLLEN COUNT", True, COLORS['yellow'])
        self.ws.screen.blit(pollen_title, (right_x, pollen_y))
        pollen_y += 30

        pollen_data = [
            ("Tree", "LOW"),
            ("Grass", "MODERATE"),
            ("Weed", "LOW"),
            ("Mold", "HIGH")
        ]

        for pollen_type, level in pollen_data:
            # Use smaller font for better fit
            label = self.ws.font_tiny.render(f"{pollen_type}:", True, COLORS['white'])
            self.ws.screen.blit(label, (right_x, pollen_y))

            # Color code the level
            if level == "HIGH":
                color = (255, 100, 100)  # Red
            elif level == "MODERATE":
                color = COLORS['yellow']
            else:
                color = (100, 255, 100)  # Green

            # Align bars properly - fixed position for all bars
            bar_x = right_x + 70  # Fixed starting position
            bar_width = 80 if level == "HIGH" else 60 if level == "MODERATE" else 40
            pygame.draw.rect(self.ws.screen, color, (bar_x, pollen_y + 2, bar_width, 12))

            # Position level text after the bar
            level_text = self.ws.font_tiny.render(level, True, color)
            text_x = bar_x + bar_width + 10  # 10px after the bar
            self.ws.screen.blit(level_text, (text_x, pollen_y))
            pollen_y += 25

        # Bottom section - Health recommendations with scrolling if needed
        y_pos = max(y_pos, pollen_y) + 20
        tips_title = self.ws.font_normal.render("HEALTH RECOMMENDATIONS", True, COLORS['yellow'])
        tips_rect = tips_title.get_rect(center=(320, y_pos))
        self.ws.screen.blit(tips_title, tips_rect)
        y_pos += 25

        tips = [
            "Air quality is good for outdoor activities",
            "High mold count - allergy sufferers take precaution",
            "UV index moderate - use sunscreen if outside"
        ]

        # Create clipping area for recommendations
        clip_rect = pygame.Rect(60, y_pos, 520, 440 - y_pos)  # Leave some margin at bottom
        self.ws.screen.set_clip(clip_rect)

        # Initialize scroll position if not exists
        if not hasattr(self.ws, 'health_scroll_pos'):
            self.ws.health_scroll_pos = 0
            self.ws.health_scroll_dir = 1

        # Auto-scroll if text is too long
        total_height = len(tips) * 22
        if total_height > (440 - y_pos):
            # Update scroll position
            self.ws.health_scroll_pos += self.ws.health_scroll_dir * 0.5
            if self.ws.health_scroll_pos > 0:
                self.ws.health_scroll_pos = 0
                self.ws.health_scroll_dir = -1
            elif self.ws.health_scroll_pos < -(total_height - (440 - y_pos)):
                self.ws.health_scroll_pos = -(total_height - (440 - y_pos))
                self.ws.health_scroll_dir = 1

        # Draw tips with scroll offset
        tip_y = y_pos + self.ws.health_scroll_pos if hasattr(self.ws, 'health_scroll_pos') else y_pos
        for tip in tips:
            # Use smaller font and proper wrapping
            if self.ws.font_tiny.size(tip)[0] > 500:
                # Word wrap long tips
                words = tip.split()
                lines = []
                current_line = ""
                for word in words:
                    test_line = f"{current_line} {word}".strip()
                    if self.ws.font_tiny.size(test_line)[0] <= 500:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)

                # Draw wrapped lines
                for line in lines:
                    if 0 < tip_y < 440:  # Only draw visible lines
                        tip_text = self.ws.font_tiny.render(f"• {line}", True, COLORS['white'])
                        self.ws.screen.blit(tip_text, (70, tip_y))
                    tip_y += 20
            else:
                if 0 < tip_y < 440:  # Only draw visible lines
                    tip_text = self.ws.font_tiny.render(f"• {tip}", True, COLORS['white'])
                    self.ws.screen.blit(tip_text, (70, tip_y))
                tip_y += 22

        # Reset clipping
        self.ws.screen.set_clip(None)

        self.logger.main_logger.debug("Drew Air Quality display")

    def draw_temperature_graph(self):
        """Draw 7-Day Temperature Graph"""
        self.ws.draw_background('1-chart')  # Use chart background if available, else '1'
        self.ws.draw_header("7-Day", "Temperature")

        # Get forecast periods
        forecast = self.ws.weather_data.get('forecast', {})
        periods = forecast.get('periods', [])

        # Graph area - raised by 5 pixels more
        graph_left = 80
        graph_top = 105  # Was 110, now 105 (raised 5px more)
        graph_width = 480
        graph_height = 250

        # Draw graph axes
        pygame.draw.line(self.ws.screen, COLORS['white'], (graph_left, graph_top + graph_height),
                        (graph_left + graph_width, graph_top + graph_height), 2)  # X-axis
        pygame.draw.line(self.ws.screen, COLORS['white'], (graph_left, graph_top),
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

                # Draw temperature bar with color gradient
                bar_x = x - 20
                bar_height = abs(low_y - high_y)

                # Calculate color based on average temperature
                avg_temp = (high + low) / 2
                # Color gradient from blue (cold) to red (hot)
                if avg_temp < 32:  # Freezing
                    bar_color = (100, 150, 255)  # Light blue
                elif avg_temp < 50:  # Cold
                    bar_color = (150, 200, 255)  # Lighter blue
                elif avg_temp < 65:  # Cool
                    bar_color = (150, 255, 150)  # Light green
                elif avg_temp < 75:  # Mild
                    bar_color = (255, 255, 100)  # Yellow
                elif avg_temp < 85:  # Warm
                    bar_color = (255, 200, 100)  # Orange
                else:  # Hot
                    bar_color = (255, 100, 100)  # Red

                # Draw gradient bar
                # Draw multiple rectangles with slightly different colors for gradient effect
                gradient_steps = 5
                step_height = bar_height / gradient_steps
                for j in range(gradient_steps):
                    # Interpolate color
                    factor = j / gradient_steps
                    r = int(bar_color[0] * (1 - factor * 0.3))  # Darken towards bottom
                    g = int(bar_color[1] * (1 - factor * 0.3))
                    b = int(bar_color[2] * (1 - factor * 0.3))
                    step_color = (min(255, r), min(255, g), min(255, b))

                    pygame.draw.rect(self.ws.screen, step_color,
                                   (bar_x, high_y + j * step_height, 40, step_height + 1))

                # Draw temperatures
                high_text = self.ws.font_small.render(str(high), True, COLORS['yellow'])
                high_rect = high_text.get_rect(center=(x, high_y - 10))
                self.ws.screen.blit(high_text, high_rect)

                low_text = self.ws.font_small.render(str(low), True, COLORS['white'])
                low_rect = low_text.get_rect(center=(x, low_y + 20))
                self.ws.screen.blit(low_text, low_rect)

                # Draw day label - raised by 10px as requested
                label_text = self.ws.font_small.render(label, True, COLORS['white'])
                label_rect = label_text.get_rect(center=(x, graph_top + graph_height + 10))  # Was +20, now +10
                self.ws.screen.blit(label_text, label_rect)

        self.logger.main_logger.debug("Drew Temperature Graph display")

    def draw_weather_records(self):
        """Draw Weather Records"""
        self.ws.draw_background('4')
        self.ws.draw_header("Weather", "Records")

        from datetime import datetime
        now = datetime.now()
        date_str = now.strftime("%B %d")

        y_pos = 120

        # Title
        title = self.ws.font_normal.render(f"Records for {date_str}", True, COLORS['yellow'])
        title_rect = title.get_rect(center=(320, y_pos))
        self.ws.screen.blit(title, title_rect)
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
            label_text = self.ws.font_normal.render(f"{label}:", True, COLORS['white'])
            self.ws.screen.blit(label_text, (120, y_pos))

            value_text = self.ws.font_normal.render(value, True, COLORS['yellow'])
            self.ws.screen.blit(value_text, (350, y_pos))

            y_pos += 35

        # This day in weather history
        y_pos += 20
        history_title = self.ws.font_extended.render("THIS DAY IN WEATHER HISTORY", True, COLORS['yellow'])
        self.ws.screen.blit(history_title, (60, y_pos))
        y_pos += 35

        history_text = "1992: Hurricane Andrew made landfall in Florida"
        hist = self.ws.font_small.render(history_text, True, COLORS['white'])
        self.ws.screen.blit(hist, (80, y_pos))

        self.logger.main_logger.debug("Drew Weather Records display")

    def draw_sun_moon(self):
        """Draw Sunrise/Sunset & Moon"""
        self.ws.draw_background('1')  # Use background 1 (standard 2-column)
        self.ws.draw_header("Sun & Moon", "Data")

        # Two column layout - moved closer together
        left_col_x = 60
        right_col_x = 335  # Moved 15px to the left to close gap
        y_pos = 120

        # LEFT COLUMN - Sun data
        sun_title = self.ws.font_normal.render("SUN", True, COLORS['yellow'])
        self.ws.screen.blit(sun_title, (left_col_x, y_pos))
        sun_y = y_pos + 30

        # Calculate approximate sunrise/sunset (simplified)
        from datetime import datetime
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
            # Use tiny font for better fit
            label_text = self.ws.font_tiny.render(f"{label}:", True, COLORS['white'])
            self.ws.screen.blit(label_text, (left_col_x + 10, sun_y))

            # Calculate proper position for value to avoid overlap - 5px thinner
            label_width = self.ws.font_tiny.size(f"{label}:")[0]
            value_x = left_col_x + 15 + max(110, label_width + 10)  # Reduced from 120 to 110
            value_text = self.ws.font_tiny.render(value, True, COLORS['yellow'])
            self.ws.screen.blit(value_text, (value_x, sun_y))

            sun_y += 24  # Reduced spacing

        # RIGHT COLUMN - Moon data
        moon_title = self.ws.font_normal.render("MOON", True, COLORS['yellow'])
        self.ws.screen.blit(moon_title, (right_col_x, y_pos))
        moon_y = y_pos + 30

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
            # Use tiny font for better fit
            label_text = self.ws.font_tiny.render(f"{label}:", True, COLORS['white'])
            self.ws.screen.blit(label_text, (right_col_x + 10, moon_y))

            # Calculate proper position for value to avoid overlap - 5px thinner
            label_width = self.ws.font_tiny.size(f"{label}:")[0]
            value_x = right_col_x + 15 + max(100, label_width + 10)  # Reduced from 110 to 100
            value_text = self.ws.font_tiny.render(value, True, COLORS['yellow'])
            self.ws.screen.blit(value_text, (value_x, moon_y))

            moon_y += 24  # Reduced spacing

        self.logger.main_logger.debug("Drew Sun & Moon display")

    def draw_wind_pressure(self):
        """Draw Wind & Pressure"""
        self.ws.draw_background('1')
        self.ws.draw_header("Wind &", "Pressure")

        current = self.ws.weather_data.get('current', {})

        y_pos = 120

        # Wind section
        wind_title = self.ws.font_extended.render("WIND CONDITIONS", True, COLORS['yellow'])
        self.ws.screen.blit(wind_title, (60, y_pos))
        y_pos += 35

        # Get wind data
        wind_speed = current.get('windSpeed', {}).get('value')
        wind_dir = current.get('windDirection', {}).get('value')
        wind_gust = current.get('windGust', {}).get('value')

        if wind_speed:
            wind_mph = int(wind_speed * 0.621371)
            speed_text = self.ws.font_normal.render(f"Speed: {wind_mph} mph", True, COLORS['white'])
            self.ws.screen.blit(speed_text, (80, y_pos))
            y_pos += 30

        if wind_dir:
            dir_text = self._get_wind_direction(wind_dir)
            direction = self.ws.font_normal.render(f"Direction: {dir_text} ({wind_dir}°)", True, COLORS['white'])
            self.ws.screen.blit(direction, (80, y_pos))
            y_pos += 30

        if wind_gust:
            gust_mph = int(wind_gust * 0.621371)
            gust_text = self.ws.font_normal.render(f"Gusts: {gust_mph} mph", True, COLORS['yellow'])
            self.ws.screen.blit(gust_text, (80, y_pos))
            y_pos += 30

        # Wind chill / Heat index
        wind_chill = current.get('windChill', {}).get('value')
        heat_index = current.get('heatIndex', {}).get('value')

        if wind_chill:
            wc_f = int(wind_chill * 9/5 + 32)
            wc_text = self.ws.font_normal.render(f"Wind Chill: {wc_f}°F", True, COLORS['blue'])
            self.ws.screen.blit(wc_text, (80, y_pos))
            y_pos += 30
        elif heat_index:
            hi_f = int(heat_index * 9/5 + 32)
            hi_text = self.ws.font_normal.render(f"Heat Index: {hi_f}°F", True, (255, 100, 100))
            self.ws.screen.blit(hi_text, (80, y_pos))
            y_pos += 30

        # Pressure section
        y_pos += 20
        pressure_title = self.ws.font_extended.render("BAROMETRIC PRESSURE", True, COLORS['yellow'])
        self.ws.screen.blit(pressure_title, (60, y_pos))
        y_pos += 35

        pressure = current.get('barometricPressure', {}).get('value')
        if pressure:
            pressure_inhg = pressure * 0.00029530
            press_text = self.ws.font_normal.render(f"Current: {pressure_inhg:.2f} in", True, COLORS['white'])
            self.ws.screen.blit(press_text, (80, y_pos))
            y_pos += 30

            # Trend (simulated)
            trend_text = self.ws.font_normal.render("Trend: Steady", True, COLORS['white'])
            self.ws.screen.blit(trend_text, (80, y_pos))

        self.logger.main_logger.debug("Drew Wind & Pressure display")

    def draw_weekend_forecast(self):
        """Draw Weekend Forecast in 2 columns"""
        self.ws.draw_background('4')  # Use hourly forecast background
        self.ws.draw_header("Weekend", "Forecast")

        forecast = self.ws.weather_data.get('forecast', {})
        periods = forecast.get('periods', [])

        # Two column layout
        left_col_x = 60
        right_col_x = 340
        col_width = 260

        # Find weekend periods
        saturday_periods = []
        sunday_periods = []

        for period in periods:
            name = period.get('name', '')
            if 'Saturday' in name:
                saturday_periods.append(period)
            elif 'Sunday' in name:
                sunday_periods.append(period)

            # Stop when we have both day and night for each
            if len(saturday_periods) >= 2 and len(sunday_periods) >= 2:
                break

        # Draw Saturday column
        if saturday_periods:
            y_pos = 145  # Moved down 25px from 120 to fit better
            # Saturday header
            sat_title = self.ws.font_extended.render("SATURDAY", True, COLORS['yellow'])
            sat_rect = sat_title.get_rect(center=(left_col_x + col_width // 2, y_pos))
            self.ws.screen.blit(sat_title, sat_rect)
            y_pos += 35

            for period in saturday_periods[:2]:  # Day and Night
                # Period name (DAY/NIGHT)
                name = period.get('name', '')
                time_of_day = "DAY" if "Day" in name or not "Night" in name else "NIGHT"
                tod_text = self.ws.font_normal.render(time_of_day, True, COLORS['cyan'])
                self.ws.screen.blit(tod_text, (left_col_x + 10, y_pos))
                y_pos += 25

                # Temperature
                temp = period.get('temperature')
                if temp:
                    temp_text = self.ws.font_normal.render(f"{temp}°", True, COLORS['white'])
                    self.ws.screen.blit(temp_text, (left_col_x + 10, y_pos))
                    y_pos += 25

                # Weather icon (if available) - properly scaled maintaining aspect ratio
                icon_name = self._get_icon_name(period.get('icon', ''))
                if self.ws.icon_manager:
                    # Get icon without forcing size, then scale proportionally
                    orig_icon = self.ws.icon_manager.get_icon(icon_name)
                    if orig_icon:
                        # Scale to fit in 60x60 box while maintaining aspect ratio
                        orig_size = orig_icon.get_size()
                        scale_factor = min(60/orig_size[0], 60/orig_size[1])
                        new_size = (int(orig_size[0] * scale_factor), int(orig_size[1] * scale_factor))
                        icon = pygame.transform.scale(orig_icon, new_size)
                        # Center icon in 60x60 area
                        icon_x = left_col_x + 70 + (60 - new_size[0]) // 2
                        icon_y = y_pos - 50 + (60 - new_size[1]) // 2
                        self.ws.screen.blit(icon, (icon_x, icon_y))

                # Short forecast with word wrap
                short = period.get('shortForecast', '')
                words = short.split()
                lines = []
                current_line = ""

                for word in words:
                    test_line = f"{current_line} {word}".strip()
                    if self.ws.font_tiny.size(test_line)[0] <= col_width - 20:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word

                if current_line:
                    lines.append(current_line)

                # Draw forecast text
                for line in lines[:3]:  # Max 3 lines
                    text = self.ws.font_tiny.render(line, True, COLORS['white'])
                    self.ws.screen.blit(text, (left_col_x + 10, y_pos))
                    y_pos += 18

                y_pos += 15  # Space between day/night

        # Draw Sunday column
        if sunday_periods:
            y_pos = 145  # Moved down 25px from 120 to fit better
            # Sunday header
            sun_title = self.ws.font_extended.render("SUNDAY", True, COLORS['yellow'])
            sun_rect = sun_title.get_rect(center=(right_col_x + col_width // 2, y_pos))
            self.ws.screen.blit(sun_title, sun_rect)
            y_pos += 35

            for period in sunday_periods[:2]:  # Day and Night
                # Period name (DAY/NIGHT)
                name = period.get('name', '')
                time_of_day = "DAY" if "Day" in name or not "Night" in name else "NIGHT"
                tod_text = self.ws.font_normal.render(time_of_day, True, COLORS['cyan'])
                self.ws.screen.blit(tod_text, (right_col_x + 10, y_pos))
                y_pos += 25

                # Temperature
                temp = period.get('temperature')
                if temp:
                    temp_text = self.ws.font_normal.render(f"{temp}°", True, COLORS['white'])
                    self.ws.screen.blit(temp_text, (right_col_x + 10, y_pos))
                    y_pos += 25

                # Weather icon (if available) - properly scaled maintaining aspect ratio
                icon_name = self._get_icon_name(period.get('icon', ''))
                if self.ws.icon_manager:
                    # Get icon without forcing size, then scale proportionally
                    orig_icon = self.ws.icon_manager.get_icon(icon_name)
                    if orig_icon:
                        # Scale to fit in 60x60 box while maintaining aspect ratio
                        orig_size = orig_icon.get_size()
                        scale_factor = min(60/orig_size[0], 60/orig_size[1])
                        new_size = (int(orig_size[0] * scale_factor), int(orig_size[1] * scale_factor))
                        icon = pygame.transform.scale(orig_icon, new_size)
                        # Center icon in 60x60 area
                        icon_x = right_col_x + 70 + (60 - new_size[0]) // 2
                        icon_y = y_pos - 50 + (60 - new_size[1]) // 2
                        self.ws.screen.blit(icon, (icon_x, icon_y))

                # Short forecast with word wrap
                short = period.get('shortForecast', '')
                words = short.split()
                lines = []
                current_line = ""

                for word in words:
                    test_line = f"{current_line} {word}".strip()
                    if self.ws.font_tiny.size(test_line)[0] <= col_width - 20:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word

                if current_line:
                    lines.append(current_line)

                # Draw forecast text
                for line in lines[:3]:  # Max 3 lines
                    text = self.ws.font_tiny.render(line, True, COLORS['white'])
                    self.ws.screen.blit(text, (right_col_x + 10, y_pos))
                    y_pos += 18

                y_pos += 15  # Space between day/night

        if not saturday_periods and not sunday_periods:
            # No weekend data
            msg = self.ws.font_normal.render("Weekend forecast not available", True, COLORS['white'])
            msg_rect = msg.get_rect(center=(320, 240))
            self.ws.screen.blit(msg, msg_rect)

        self.logger.main_logger.debug("Drew Weekend Forecast display")

    def draw_monthly_outlook(self):
        """Draw Monthly Outlook"""
        self.ws.draw_background('4')  # Changed to hourly forecast background
        self.ws.draw_header("30-Day", "Outlook")

        y_pos = 120

        # Title
        from datetime import datetime
        now = datetime.now()
        month = now.strftime("%B %Y")
        title = self.ws.font_normal.render(f"Outlook for {month}", True, COLORS['yellow'])
        title_rect = title.get_rect(center=(320, y_pos))
        self.ws.screen.blit(title, title_rect)
        y_pos += 35  # Moved up 15px (was 50, now 35)

        # Temperature outlook
        temp_title = self.ws.font_extended.render("TEMPERATURE OUTLOOK", True, COLORS['yellow'])
        self.ws.screen.blit(temp_title, (60, y_pos))
        y_pos += 35

        temp_outlook = "Above Normal Temperatures Expected"
        temp_text = self.ws.font_normal.render(temp_outlook, True, COLORS['white'])
        self.ws.screen.blit(temp_text, (80, y_pos))
        y_pos += 30

        # Show probability
        prob_text = self.ws.font_small.render("Probability: 60% above normal", True, COLORS['white'])
        self.ws.screen.blit(prob_text, (100, y_pos))
        y_pos += 40

        # Precipitation outlook
        precip_title = self.ws.font_extended.render("PRECIPITATION OUTLOOK", True, COLORS['yellow'])
        self.ws.screen.blit(precip_title, (60, y_pos))
        y_pos += 35

        precip_outlook = "Near Normal Precipitation Expected"
        precip_text = self.ws.font_normal.render(precip_outlook, True, COLORS['white'])
        self.ws.screen.blit(precip_text, (80, y_pos))
        y_pos += 30

        # Show probability
        prob2_text = self.ws.font_small.render("Probability: Equal chances", True, COLORS['white'])
        self.ws.screen.blit(prob2_text, (100, y_pos))
        y_pos += 40

        # Data source
        source = self.ws.font_small.render("Source: NOAA Climate Prediction Center", True, COLORS['white'])
        source_rect = source.get_rect(center=(320, 380))
        self.ws.screen.blit(source, source_rect)

        self.logger.main_logger.debug("Drew Monthly Outlook display")

    def draw_temperature_history(self):
        """Draw 30-Day Temperature History - 90s style scrolling text"""
        self.ws.draw_background('5')  # Latest Observations background
        self.ws.draw_header("30-Day", "Temperature History")

        # Get history data
        from weatherstar_modules.history_graphs import get_weather_history
        history = get_weather_history()

        if not history.history_data['temperature']:
            # Try to fetch data
            history.fetch_history_data(self.ws.lat, self.ws.lon)

        # Column headers
        y_pos = 120
        header_col1 = self.ws.font_normal.render("DATE", True, COLORS['yellow'])
        header_col2 = self.ws.font_normal.render("HIGH", True, COLORS['yellow'])
        header_col3 = self.ws.font_normal.render("LOW", True, COLORS['yellow'])

        self.ws.screen.blit(header_col1, (60, y_pos))
        self.ws.screen.blit(header_col2, (320, y_pos))
        self.ws.screen.blit(header_col3, (480, y_pos))

        y_pos += 40

        # Draw horizontal line under headers
        pygame.draw.line(self.ws.screen, COLORS['yellow'], (50, y_pos - 5), (590, y_pos - 5), 1)

        # Display data (scrolling if more than 8 rows)
        max_rows = 8
        start_index = int(history.scroll_offset_temp / 30) if hasattr(history, 'scroll_offset_temp') else 0

        row_count = 0
        for i, (date_str, high, low) in enumerate(history.history_data['temperature']):
            if i < start_index:
                continue
            if row_count >= max_rows:
                break

            try:
                # Format date
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                date_display = date_obj.strftime("%a %m/%d")

                # Display row
                date_text = self.ws.font_normal.render(date_display, True, COLORS['white'])
                high_text = self.ws.font_normal.render(f"{int(high)}\u00b0", True, COLORS['white'])
                low_text = self.ws.font_normal.render(f"{int(low)}\u00b0", True, COLORS['white'])

                self.ws.screen.blit(date_text, (60, y_pos))
                self.ws.screen.blit(high_text, (330, y_pos))
                self.ws.screen.blit(low_text, (490, y_pos))

                y_pos += 30
                row_count += 1

            except Exception as e:
                self.logger.main_logger.error(f"Error formatting temperature history row: {e}")
                continue

        # Update scroll for next frame
        if len(history.history_data['temperature']) > max_rows:
            history.update_scroll(time.time())
            # Reset scroll when reaching end
            max_scroll = (len(history.history_data['temperature']) - max_rows) * 30
            if history.scroll_offset_temp > max_scroll:
                history.scroll_offset_temp = 0
                history.last_scroll_time = time.time()

        self.logger.main_logger.debug("Drew Temperature History display")

    def draw_precipitation_history(self):
        """Draw 30-Day Precipitation History - 90s style scrolling text"""
        self.ws.draw_background('5')  # Latest Observations background
        self.ws.draw_header("30-Day", "Precipitation History")

        # Get history data
        from weatherstar_modules.history_graphs import get_weather_history
        history = get_weather_history()

        if not history.history_data['precipitation']:
            # Try to fetch data
            history.fetch_history_data(self.ws.lat, self.ws.lon)

        # Column headers
        y_pos = 120
        header_col1 = self.ws.font_normal.render("DATE", True, COLORS['yellow'])
        header_col2 = self.ws.font_normal.render("AMOUNT", True, COLORS['yellow'])
        header_col3 = self.ws.font_normal.render("STATUS", True, COLORS['yellow'])

        self.ws.screen.blit(header_col1, (60, y_pos))
        self.ws.screen.blit(header_col2, (300, y_pos))
        self.ws.screen.blit(header_col3, (480, y_pos))

        y_pos += 40

        # Draw horizontal line under headers
        pygame.draw.line(self.ws.screen, COLORS['yellow'], (50, y_pos - 5), (590, y_pos - 5), 1)

        # Display data (scrolling if more than 8 rows)
        max_rows = 8
        start_index = int(history.scroll_offset_precip / 30) if hasattr(history, 'scroll_offset_precip') else 0

        row_count = 0
        for i, (date_str, precip) in enumerate(history.history_data['precipitation']):
            if i < start_index:
                continue
            if row_count >= max_rows:
                break

            try:
                # Format date
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                date_display = date_obj.strftime("%a %m/%d")

                # Format precipitation amount
                if precip == 0:
                    amount_display = "Trace"
                    status = "Dry"
                elif precip < 0.1:
                    amount_display = f"{precip:.2f}\""
                    status = "Light"
                elif precip < 0.5:
                    amount_display = f"{precip:.2f}\""
                    status = "Moderate"
                else:
                    amount_display = f"{precip:.2f}\""
                    status = "Heavy"

                # Display row
                date_text = self.ws.font_normal.render(date_display, True, COLORS['white'])
                amount_text = self.ws.font_normal.render(amount_display, True, COLORS['white'])
                status_text = self.ws.font_normal.render(status, True, COLORS['white'])

                self.ws.screen.blit(date_text, (60, y_pos))
                self.ws.screen.blit(amount_text, (310, y_pos))
                self.ws.screen.blit(status_text, (490, y_pos))

                y_pos += 30
                row_count += 1

            except Exception as e:
                self.logger.main_logger.error(f"Error formatting precipitation history row: {e}")
                continue

        # Update scroll for next frame
        if len(history.history_data['precipitation']) > max_rows:
            history.update_scroll(time.time())
            # Reset scroll when reaching end
            max_scroll = (len(history.history_data['precipitation']) - max_rows) * 30
            if history.scroll_offset_precip > max_scroll:
                history.scroll_offset_precip = 0
                history.last_scroll_time = time.time()

        self.logger.main_logger.debug("Drew Precipitation History display")

    def draw_uv_index(self):
        """Draw UV Index Forecast - 90s style scrolling text"""
        self.ws.draw_background('5')  # Latest Observations background
        self.ws.draw_header("UV Index", "Forecast")

        # Fetch UV index data from Open Meteo
        try:
            import requests
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': self.ws.lat,
                'longitude': self.ws.lon,
                'daily': 'uv_index_max',
                'forecast_days': 7,
                'timezone': 'auto'
            }
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                daily = data.get('daily', {})
                dates = daily.get('time', [])
                uv_values = daily.get('uv_index_max', [])

                # Column headers
                y_pos = 120
                header_col1 = self.ws.font_normal.render("DATE", True, COLORS['yellow'])
                header_col2 = self.ws.font_normal.render("UV INDEX", True, COLORS['yellow'])
                header_col3 = self.ws.font_normal.render("PROTECTION", True, COLORS['yellow'])

                self.ws.screen.blit(header_col1, (60, y_pos))
                self.ws.screen.blit(header_col2, (280, y_pos))
                self.ws.screen.blit(header_col3, (450, y_pos))

                y_pos += 40

                # Draw horizontal line under headers
                pygame.draw.line(self.ws.screen, COLORS['yellow'], (50, y_pos - 5), (590, y_pos - 5), 1)

                # Display 7 days of UV data
                for i, (date_str, uv) in enumerate(zip(dates, uv_values)):
                    if i >= 7:
                        break

                    try:
                        # Format date
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        date_display = date_obj.strftime("%a %m/%d")

                        # UV Index level and protection
                        if uv < 3:
                            level = "Low"
                        elif uv < 6:
                            level = "Moderate"
                        elif uv < 8:
                            level = "High"
                        elif uv < 11:
                            level = "Very High"
                        else:
                            level = "Extreme"

                        # Display row
                        date_text = self.ws.font_normal.render(date_display, True, COLORS['white'])
                        uv_text = self.ws.font_normal.render(f"{int(uv)}", True, COLORS['white'])
                        level_text = self.ws.font_normal.render(level, True, COLORS['white'])

                        self.ws.screen.blit(date_text, (60, y_pos))
                        self.ws.screen.blit(uv_text, (300, y_pos))
                        self.ws.screen.blit(level_text, (460, y_pos))

                        y_pos += 30

                    except Exception as e:
                        self.logger.main_logger.error(f"Error formatting UV index row: {e}")
                        continue

        except Exception as e:
            self.logger.main_logger.error(f"Error fetching UV index data: {e}")
            # Show error message
            error_text = self.ws.font_normal.render("UV Index data unavailable", True, COLORS['white'])
            error_rect = error_text.get_rect(center=(320, 240))
            self.ws.screen.blit(error_text, error_rect)

        self.logger.main_logger.debug("Drew UV Index display")

    def draw_recent_earthquakes(self):
        """Draw Recent Earthquakes - USGS data, 90s style scrolling list"""
        self.ws.draw_background('5')  # Latest Observations background
        self.ws.draw_header("Recent", "Earthquakes")

        # Fetch earthquake data from USGS (mag 3.0+, last 7 days)
        try:
            import requests
            url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
            params = {
                'format': 'geojson',
                'minmagnitude': 3.0,
                'orderby': 'time',
                'limit': 10
            }
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                earthquakes = data.get('features', [])

                # Column headers
                y_pos = 120
                header_col1 = self.ws.font_normal.render("MAG", True, COLORS['yellow'])
                header_col2 = self.ws.font_normal.render("LOCATION", True, COLORS['yellow'])
                header_col3 = self.ws.font_normal.render("TIME", True, COLORS['yellow'])

                self.ws.screen.blit(header_col1, (60, y_pos))
                self.ws.screen.blit(header_col2, (160, y_pos))
                self.ws.screen.blit(header_col3, (480, y_pos))

                y_pos += 40

                # Draw horizontal line under headers
                pygame.draw.line(self.ws.screen, COLORS['yellow'], (50, y_pos - 5), (590, y_pos - 5), 1)

                # Display earthquakes
                for quake in earthquakes[:8]:  # Show up to 8
                    try:
                        props = quake.get('properties', {})
                        mag = props.get('mag', 0)
                        place = props.get('place', 'Unknown')[:25]  # Limit length
                        time_ms = props.get('time', 0)

                        # Format time
                        from datetime import datetime
                        quake_time = datetime.fromtimestamp(time_ms / 1000)
                        time_display = quake_time.strftime("%m/%d %H:%M")

                        # Display row
                        mag_text = self.ws.font_normal.render(f"{mag:.1f}", True, COLORS['white'])
                        place_text = self.ws.font_normal.render(place, True, COLORS['white'])
                        time_text = self.ws.font_normal.render(time_display, True, COLORS['white'])

                        self.ws.screen.blit(mag_text, (70, y_pos))
                        self.ws.screen.blit(place_text, (160, y_pos))
                        self.ws.screen.blit(time_text, (490, y_pos))

                        y_pos += 28

                    except Exception as e:
                        self.logger.main_logger.error(f"Error formatting earthquake row: {e}")
                        continue

        except Exception as e:
            self.logger.main_logger.error(f"Error fetching earthquake data: {e}")
            # Show error message
            error_text = self.ws.font_normal.render("Earthquake data unavailable", True, COLORS['white'])
            error_rect = error_text.get_rect(center=(320, 240))
            self.ws.screen.blit(error_text, error_rect)

        self.logger.main_logger.debug("Drew Recent Earthquakes display")

    def draw_stock_market(self):
        """Draw Stock Market Indices - Simple ticker display"""
        self.ws.draw_background('5')  # Latest Observations background
        self.ws.draw_header("Stock Market", "Update")

        # Note: This would require an API key for real data
        # For now, show placeholder with instructions
        y_pos = 150

        title = self.ws.font_extended.render("MARKET INDICES", True, COLORS['yellow'])
        title_rect = title.get_rect(center=(320, y_pos))
        self.ws.screen.blit(title, title_rect)
        y_pos += 50

        # Placeholder indices
        indices = [
            ("DOW JONES", "44,910.65", "+125.50", "green"),
            ("S&P 500", "6,012.28", "+22.18", "green"),
            ("NASDAQ", "19,218.17", "+85.28", "green")
        ]

        for name, value, change, color in indices:
            # Index name
            name_text = self.ws.font_normal.render(name, True, COLORS['white'])
            self.ws.screen.blit(name_text, (100, y_pos))

            # Value
            value_text = self.ws.font_normal.render(value, True, COLORS['white'])
            self.ws.screen.blit(value_text, (320, y_pos))

            # Change
            change_color = COLORS['green'] if '+' in change else COLORS['red']
            change_text = self.ws.font_normal.render(change, True, change_color)
            self.ws.screen.blit(change_text, (480, y_pos))

            y_pos += 40

        # Note about real-time data
        note_y = 380
        note1 = self.ws.font_small.render("Note: Live data requires API key", True, COLORS['white'])
        note1_rect = note1.get_rect(center=(320, note_y))
        self.ws.screen.blit(note1, note1_rect)

        note2 = self.ws.font_small.render("Visit alphavantage.co for free access", True, COLORS['white'])
        note2_rect = note2.get_rect(center=(320, note_y + 20))
        self.ws.screen.blit(note2, note2_rect)

        self.logger.main_logger.debug("Drew Stock Market display")

    def draw_scrolling_text(self):
        """Draw bottom scrolling text"""
        try:
            # Banner positioned 20px from bottom (480 - 30 - 20 = 430)
            banner_height = 30
            banner_y = SCREEN_HEIGHT - banner_height - 20  # 430px (20px from bottom)
            pygame.draw.rect(self.ws.screen, (0, 0, 80), (0, banner_y, SCREEN_WIDTH, banner_height))  # Banner position

            # Check if scroller exists and is properly initialized
            if hasattr(self.ws, 'scroller') and self.ws.scroller:
                self.ws.scroller.update()
                # Center text vertically in the banner
                # Assuming font height is about 16-20px, center it properly
                text_y = banner_y + (banner_height // 2) - 10  # Vertically centered in banner
                self.ws.scroller.draw(self.ws.screen, text_y)
                self.logger.main_logger.debug("Drew scrolling text successfully")
            else:
                # Fallback if scroller not available
                fallback_text = "Weather conditions and forecast information"
                if hasattr(self.ws, 'font_scroller'):
                    text_surface = self.ws.font_scroller.render(fallback_text, True, (255, 255, 255))
                else:
                    text_surface = self.ws.font_normal.render(fallback_text, True, (255, 255, 255))
                # Center text both horizontally and vertically in the banner
                text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, banner_y + banner_height // 2))
                self.ws.screen.blit(text_surface, text_rect)
                self.logger.main_logger.warning("Scroller not available, using fallback text")
        except Exception as e:
            self.logger.main_logger.error(f"Error drawing scrolling text: {e}")
#!/usr/bin/env python3
"""
Weather History Graphs Module
Displays 30-day temperature and precipitation trends
"""

import pygame
import time
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional
import math


class WeatherHistoryGraph:
    """Manages weather history data and graph rendering"""

    def __init__(self):
        self.history_data = {
            'temperature': [],  # List of (date, temp, high, low) tuples
            'precipitation': [],  # List of (date, precip) tuples
        }
        self.cache_time = 0
        self.cache_duration = 3600  # Cache for 1 hour

    def fetch_history_data(self, lat: float, lon: float) -> bool:
        """Fetch 30-day weather history from Open Meteo API"""
        # Check cache
        if time.time() - self.cache_time < self.cache_duration:
            return len(self.history_data['temperature']) > 0

        try:
            import requests

            # Get 30 days of historical data from Open Meteo
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

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

                # Store temperature data
                self.history_data['temperature'] = []
                for i in range(len(dates)):
                    if i < len(temp_max) and i < len(temp_min):
                        avg_temp = (temp_max[i] + temp_min[i]) / 2
                        self.history_data['temperature'].append(
                            (dates[i], avg_temp, temp_max[i], temp_min[i])
                        )

                # Store precipitation data
                self.history_data['precipitation'] = []
                for i in range(len(dates)):
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

    def draw_temperature_graph(self, surface: pygame.Surface, rect: pygame.Rect,
                               theme_colors: dict) -> None:
        """Draw 30-day temperature trend graph"""
        if not self.history_data['temperature']:
            return

        # Colors
        bg_color = theme_colors.get('blue_gradient_2', (0, 16, 64))
        grid_color = theme_colors.get('blue_gradient_1', (16, 32, 128))
        text_color = theme_colors.get('white', (255, 255, 255))
        high_color = (255, 100, 100)  # Red for highs
        low_color = (100, 150, 255)   # Blue for lows
        avg_color = theme_colors.get('yellow', (255, 255, 0))

        # Draw background
        pygame.draw.rect(surface, bg_color, rect)

        # Graph area (leave margins for labels)
        margin_left = 40
        margin_right = 10
        margin_top = 30
        margin_bottom = 30

        graph_x = rect.x + margin_left
        graph_y = rect.y + margin_top
        graph_width = rect.width - margin_left - margin_right
        graph_height = rect.height - margin_top - margin_bottom

        # Get temperature range
        temps = [item[1] for item in self.history_data['temperature']]  # avg temps
        highs = [item[2] for item in self.history_data['temperature']]
        lows = [item[3] for item in self.history_data['temperature']]

        all_temps = temps + highs + lows
        temp_min = min(all_temps)
        temp_max = max(all_temps)
        temp_range = temp_max - temp_min

        if temp_range == 0:
            temp_range = 1  # Avoid division by zero

        # Draw grid lines
        num_grid_lines = 5
        for i in range(num_grid_lines):
            y = graph_y + (graph_height * i / (num_grid_lines - 1))
            pygame.draw.line(surface, grid_color,
                           (graph_x, y), (graph_x + graph_width, y), 1)

            # Temperature label
            temp = temp_max - (temp_range * i / (num_grid_lines - 1))
            font = pygame.font.Font(None, 18)
            label = font.render(f"{int(temp)}°", True, text_color)
            surface.blit(label, (rect.x + 5, y - 8))

        # Plot temperature lines
        points_avg = []
        points_high = []
        points_low = []

        for i, (date, avg, high, low) in enumerate(self.history_data['temperature']):
            x = graph_x + (i * graph_width / max(len(self.history_data['temperature']) - 1, 1))

            # Calculate y positions
            y_avg = graph_y + graph_height - ((avg - temp_min) / temp_range * graph_height)
            y_high = graph_y + graph_height - ((high - temp_min) / temp_range * graph_height)
            y_low = graph_y + graph_height - ((low - temp_min) / temp_range * graph_height)

            points_avg.append((x, y_avg))
            points_high.append((x, y_high))
            points_low.append((x, y_low))

        # Draw lines
        if len(points_high) > 1:
            pygame.draw.lines(surface, high_color, False, points_high, 2)
        if len(points_low) > 1:
            pygame.draw.lines(surface, low_color, False, points_low, 2)
        if len(points_avg) > 1:
            pygame.draw.lines(surface, avg_color, False, points_avg, 3)

        # Title
        title_font = pygame.font.Font(None, 24)
        title = title_font.render("30-Day Temperature Trend", True,
                                 theme_colors.get('yellow', (255, 255, 0)))
        title_rect = title.get_rect(centerx=rect.centerx, y=rect.y + 5)
        surface.blit(title, title_rect)

        # Legend
        legend_font = pygame.font.Font(None, 16)
        legend_y = rect.bottom - 20

        pygame.draw.line(surface, high_color, (graph_x, legend_y), (graph_x + 20, legend_y), 2)
        high_label = legend_font.render("High", True, text_color)
        surface.blit(high_label, (graph_x + 25, legend_y - 6))

        pygame.draw.line(surface, avg_color, (graph_x + 80, legend_y), (graph_x + 100, legend_y), 3)
        avg_label = legend_font.render("Avg", True, text_color)
        surface.blit(avg_label, (graph_x + 105, legend_y - 6))

        pygame.draw.line(surface, low_color, (graph_x + 160, legend_y), (graph_x + 180, legend_y), 2)
        low_label = legend_font.render("Low", True, text_color)
        surface.blit(low_label, (graph_x + 185, legend_y - 6))

    def draw_precipitation_graph(self, surface: pygame.Surface, rect: pygame.Rect,
                                 theme_colors: dict) -> None:
        """Draw 30-day precipitation bar chart"""
        if not self.history_data['precipitation']:
            return

        # Colors
        bg_color = theme_colors.get('blue_gradient_2', (0, 16, 64))
        bar_color = (100, 200, 255)  # Light blue for rain
        text_color = theme_colors.get('white', (255, 255, 255))

        # Draw background
        pygame.draw.rect(surface, bg_color, rect)

        # Graph area
        margin = 30
        graph_x = rect.x + margin
        graph_y = rect.y + margin
        graph_width = rect.width - (2 * margin)
        graph_height = rect.height - (2 * margin) - 20  # Extra space for title

        # Get precipitation range
        precips = [item[1] for item in self.history_data['precipitation']]
        max_precip = max(precips) if precips else 1

        if max_precip == 0:
            max_precip = 1  # Avoid division by zero

        # Draw bars
        bar_width = graph_width / len(self.history_data['precipitation'])

        for i, (date, precip) in enumerate(self.history_data['precipitation']):
            if precip > 0:
                bar_height = (precip / max_precip) * graph_height
                bar_x = graph_x + (i * bar_width)
                bar_y = graph_y + graph_height - bar_height

                pygame.draw.rect(surface, bar_color,
                               (bar_x, bar_y, max(bar_width - 2, 1), bar_height))

        # Title
        title_font = pygame.font.Font(None, 24)
        title = title_font.render("30-Day Precipitation", True,
                                 theme_colors.get('yellow', (255, 255, 0)))
        title_rect = title.get_rect(centerx=rect.centerx, y=rect.y + 5)
        surface.blit(title, title_rect)

        # Max precipitation label
        label_font = pygame.font.Font(None, 16)
        max_label = label_font.render(f"Max: {max_precip:.2f}\"", True, text_color)
        surface.blit(max_label, (graph_x, graph_y - 20))


# Singleton instance
_history_graph_instance = None

def get_history_graph() -> WeatherHistoryGraph:
    """Get singleton instance of weather history graph"""
    global _history_graph_instance
    if _history_graph_instance is None:
        _history_graph_instance = WeatherHistoryGraph()
    return _history_graph_instance

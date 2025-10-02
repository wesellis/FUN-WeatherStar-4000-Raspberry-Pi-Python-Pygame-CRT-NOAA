#!/usr/bin/env python3
"""
History Graph Display Methods
Extends WeatherStar displays with history graph rendering
"""

import pygame


def draw_history_graphs(ws_instance):
    """Draw 30-day temperature and precipitation history graphs"""
    # Fetch history data if needed
    if not ws_instance.history_graph.history_data['temperature']:
        ws_instance.history_graph.fetch_history_data(ws_instance.lat, ws_instance.lon)

    # Draw background
    ws_instance.screen.fill(ws_instance.current_theme.get_color('blue_gradient_2'))

    # Split screen: temperature graph on top, precipitation on bottom
    screen_rect = ws_instance.screen.get_rect()

    temp_rect = pygame.Rect(0, 0, screen_rect.width, screen_rect.height // 2)
    precip_rect = pygame.Rect(0, screen_rect.height // 2, screen_rect.width, screen_rect.height // 2)

    # Draw graphs
    ws_instance.history_graph.draw_temperature_graph(
        ws_instance.screen, temp_rect, ws_instance.current_theme.colors
    )

    ws_instance.history_graph.draw_precipitation_graph(
        ws_instance.screen, precip_rect, ws_instance.current_theme.colors
    )


def draw_severe_weather_alert(ws_instance, dt):
    """Draw animated severe weather alert screen"""
    # Check if there are active alerts
    alerts = []

    if hasattr(ws_instance, 'weather_data') and ws_instance.weather_data:
        properties = ws_instance.weather_data.get('properties', {})
        alerts = properties.get('alerts', [])

    if alerts:
        # Set alerts and draw animated display
        ws_instance.severe_weather_display.set_alerts(alerts)
        ws_instance.severe_weather_display.draw_full_alert_screen(
            ws_instance.screen, dt, ws_instance.current_theme.colors
        )
    else:
        # No alerts - show "All Clear" message
        ws_instance.screen.fill(ws_instance.current_theme.get_color('blue_gradient_2'))

        try:
            font = pygame.font.Font(None, 48)
            text = font.render("NO ACTIVE WEATHER ALERTS", True,
                             ws_instance.current_theme.get_color('white'))
            text_rect = text.get_rect(center=ws_instance.screen.get_rect().center)
            ws_instance.screen.blit(text, text_rect)

            font_small = pygame.font.Font(None, 32)
            subtext = font_small.render("All weather conditions normal", True,
                                       ws_instance.current_theme.get_color('white'))
            subtext_rect = subtext.get_rect(center=(ws_instance.screen.get_rect().centerx,
                                                    ws_instance.screen.get_rect().centery + 50))
            ws_instance.screen.blit(subtext, subtext_rect)
        except:
            pass

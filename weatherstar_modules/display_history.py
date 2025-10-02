#!/usr/bin/env python3
"""
Severe Weather Alert Display Methods
Extends WeatherStar displays with animated alert rendering
"""

import pygame


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

#!/usr/bin/env python3
"""
Emergency Alert Animations Module
Flashing alerts and scrolling warnings for severe weather
"""

import pygame
import time
import math
from typing import List, Tuple, Optional


class EmergencyAlertAnimator:
    """Handles animated emergency weather alerts"""

    def __init__(self):
        self.flash_state = False
        self.last_flash_time = 0
        self.flash_interval = 500  # milliseconds
        self.scroll_offset = 0
        self.last_scroll_time = 0
        self.scroll_speed = 50  # pixels per second
        self.alert_active = False

    def set_alert(self, active: bool):
        """Set whether an alert is active"""
        self.alert_active = active
        if active:
            self.scroll_offset = 0

    def update(self, dt: float):
        """Update animation state (dt in seconds)"""
        current_time = time.time() * 1000  # Convert to milliseconds

        # Update flash state
        if current_time - self.last_flash_time > self.flash_interval:
            self.flash_state = not self.flash_state
            self.last_flash_time = current_time

        # Update scroll offset
        self.scroll_offset += self.scroll_speed * dt

    def draw_flashing_border(self, surface: pygame.Surface, rect: pygame.Rect,
                            color: Tuple[int, int, int] = (255, 0, 0),
                            thickness: int = 5) -> None:
        """Draw flashing border around alert area"""
        if not self.alert_active:
            return

        if self.flash_state:
            # Draw thick border
            pygame.draw.rect(surface, color, rect, thickness)
            # Draw inner border for emphasis
            inner_rect = pygame.Rect(
                rect.x + thickness,
                rect.y + thickness,
                rect.width - (2 * thickness),
                rect.height - (2 * thickness)
            )
            pygame.draw.rect(surface, color, inner_rect, 2)

    def draw_scrolling_text(self, surface: pygame.Surface, rect: pygame.Rect,
                           text: str, font: pygame.font.Font,
                           text_color: Tuple[int, int, int] = (255, 255, 255),
                           bg_color: Tuple[int, int, int] = (139, 0, 0)) -> None:
        """Draw scrolling emergency text"""
        if not self.alert_active or not text:
            return

        # Draw background
        pygame.draw.rect(surface, bg_color, rect)

        # Render text
        text_surface = font.render(text, True, text_color)
        text_width = text_surface.get_width()

        # Calculate scroll position
        scroll_x = rect.x + rect.width - (self.scroll_offset % (text_width + rect.width))

        # Draw scrolling text
        surface.blit(text_surface, (scroll_x, rect.y + (rect.height - text_surface.get_height()) // 2))

        # If text has scrolled partially off screen, draw it again for seamless loop
        if scroll_x < rect.x:
            surface.blit(text_surface, (scroll_x + text_width + rect.width,
                                       rect.y + (rect.height - text_surface.get_height()) // 2))

    def draw_alert_header(self, surface: pygame.Surface, rect: pygame.Rect,
                         alert_title: str, font: pygame.font.Font,
                         text_color: Tuple[int, int, int] = (255, 255, 0),
                         bg_color: Tuple[int, int, int] = (139, 0, 0)) -> None:
        """Draw flashing alert header"""
        if not self.alert_active:
            return

        # Pulsating background intensity
        pulse = abs(math.sin(time.time() * 3))  # Pulsate 3 times per second
        pulsed_bg = tuple(int(c * (0.5 + 0.5 * pulse)) for c in bg_color)

        pygame.draw.rect(surface, pulsed_bg, rect)

        # Draw border
        if self.flash_state:
            pygame.draw.rect(surface, (255, 255, 0), rect, 3)

        # Draw text centered
        text_surface = font.render(alert_title, True, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)

    def draw_blinking_indicator(self, surface: pygame.Surface, pos: Tuple[int, int],
                                radius: int = 10,
                                color: Tuple[int, int, int] = (255, 0, 0)) -> None:
        """Draw blinking indicator dot"""
        if not self.alert_active:
            return

        if self.flash_state:
            pygame.draw.circle(surface, color, pos, radius)
            # Draw glow effect
            glow_color = tuple(min(c + 100, 255) for c in color)
            pygame.draw.circle(surface, glow_color, pos, radius + 3, 2)

    def reset(self):
        """Reset animation state"""
        self.scroll_offset = 0
        self.flash_state = False
        self.alert_active = False


class SevereWeatherDisplay:
    """Complete severe weather alert display with animations"""

    def __init__(self, screen_width: int = 640, screen_height: int = 480):
        self.animator = EmergencyAlertAnimator()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.current_alerts = []
        self.alert_font_large = None
        self.alert_font_medium = None
        self.alert_font_small = None

    def set_alerts(self, alerts: List[dict]):
        """Set current severe weather alerts"""
        self.current_alerts = alerts
        self.animator.set_alert(len(alerts) > 0)

    def load_fonts(self):
        """Load fonts for alert display"""
        try:
            self.alert_font_large = pygame.font.Font(None, 48)
            self.alert_font_medium = pygame.font.Font(None, 32)
            self.alert_font_small = pygame.font.Font(None, 24)
        except:
            self.alert_font_large = pygame.font.SysFont('arial', 48, bold=True)
            self.alert_font_medium = pygame.font.SysFont('arial', 32, bold=True)
            self.alert_font_small = pygame.font.SysFont('arial', 24)

    def draw_full_alert_screen(self, surface: pygame.Surface, dt: float,
                               theme_colors: dict) -> None:
        """Draw full-screen severe weather alert"""
        if not self.current_alerts:
            return

        if not self.alert_font_large:
            self.load_fonts()

        self.animator.update(dt)

        # Dark red background
        surface.fill((80, 0, 0))

        # Draw flashing border
        border_rect = pygame.Rect(0, 0, self.screen_width, self.screen_height)
        self.animator.draw_flashing_border(surface, border_rect, (255, 0, 0), 8)

        # Alert header
        header_rect = pygame.Rect(50, 30, self.screen_width - 100, 80)
        alert = self.current_alerts[0]  # Show first alert

        alert_type = alert.get('event', 'SEVERE WEATHER ALERT')
        self.animator.draw_alert_header(surface, header_rect, alert_type,
                                       self.alert_font_large)

        # Blinking indicators
        self.animator.draw_blinking_indicator(surface, (30, 70), 12)
        self.animator.draw_blinking_indicator(surface, (self.screen_width - 30, 70), 12)

        # Scrolling message at bottom
        message = alert.get('headline', 'SEVERE WEATHER IN YOUR AREA - TAKE SHELTER')
        scroll_rect = pygame.Rect(0, self.screen_height - 60, self.screen_width, 60)
        self.animator.draw_scrolling_text(surface, scroll_rect, message,
                                         self.alert_font_medium)

        # Alert details (static)
        details_y = 150
        line_height = 30

        description = alert.get('description', '')
        # Word wrap description
        words = description.split()
        lines = []
        current_line = []
        max_width = self.screen_width - 100

        for word in words[:50]:  # Limit to first 50 words
            test_line = ' '.join(current_line + [word])
            test_surface = self.alert_font_small.render(test_line, True, (255, 255, 255))
            if test_surface.get_width() > max_width:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
                    current_line = []
            else:
                current_line.append(word)

        if current_line:
            lines.append(' '.join(current_line))

        for i, line in enumerate(lines[:8]):  # Max 8 lines
            text = self.alert_font_small.render(line, True, (255, 255, 255))
            surface.blit(text, (50, details_y + i * line_height))


# Singleton instance
_alert_animator_instance = None

def get_alert_animator() -> EmergencyAlertAnimator:
    """Get singleton instance of emergency alert animator"""
    global _alert_animator_instance
    if _alert_animator_instance is None:
        _alert_animator_instance = EmergencyAlertAnimator()
    return _alert_animator_instance

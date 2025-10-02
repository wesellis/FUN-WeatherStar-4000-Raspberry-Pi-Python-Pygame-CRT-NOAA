#!/usr/bin/env python3
"""
WeatherStar 4000 Color Themes
Authentic and alternate color schemes
"""

from typing import Dict, Tuple


class ColorTheme:
    """Color theme definition"""

    def __init__(self, name: str, colors: Dict[str, Tuple[int, int, int]]):
        self.name = name
        self.colors = colors

    def get_color(self, key: str) -> Tuple[int, int, int]:
        """Get color by key, fallback to white if not found"""
        return self.colors.get(key, (255, 255, 255))


# Authentic WeatherStar 4000 theme (1990s)
CLASSIC_THEME = ColorTheme(
    name="Classic WeatherStar",
    colors={
        'yellow': (255, 255, 0),           # Title color
        'white': (255, 255, 255),          # Main text
        'black': (0, 0, 0),                # Text shadows
        'purple_header': (32, 0, 87),      # Column headers
        'blue_gradient_1': (16, 32, 128),  # Gradient start
        'blue_gradient_2': (0, 16, 64),    # Gradient end
        'light_blue': (128, 128, 255),     # Low temperatures
        'blue': (128, 128, 255),           # Alias for light_blue
        'cyan': (0, 255, 255),             # Reddit subreddits
        'red': (255, 0, 0),                # Breaking news / alerts
    }
)

# Dark modern theme
DARK_THEME = ColorTheme(
    name="Dark Modern",
    colors={
        'yellow': (255, 215, 0),           # Gold title
        'white': (230, 230, 230),          # Off-white text
        'black': (15, 15, 15),             # Near black background
        'purple_header': (88, 24, 131),    # Darker purple
        'blue_gradient_1': (30, 40, 80),   # Dark blue gradient start
        'blue_gradient_2': (10, 15, 35),   # Dark blue gradient end
        'light_blue': (100, 150, 255),     # Lighter blue for contrast
        'blue': (100, 150, 255),           # Alias
        'cyan': (0, 200, 200),             # Muted cyan
        'red': (220, 50, 50),              # Muted red
    }
)

# High contrast theme (accessibility)
HIGH_CONTRAST_THEME = ColorTheme(
    name="High Contrast",
    colors={
        'yellow': (255, 255, 100),         # Bright yellow
        'white': (255, 255, 255),          # Pure white
        'black': (0, 0, 0),                # Pure black
        'purple_header': (150, 0, 200),    # Bright purple
        'blue_gradient_1': (0, 0, 200),    # Pure blue
        'blue_gradient_2': (0, 0, 100),    # Dark blue
        'light_blue': (100, 200, 255),     # Bright cyan-blue
        'blue': (100, 200, 255),           # Alias
        'cyan': (0, 255, 255),             # Pure cyan
        'red': (255, 0, 0),                # Pure red
    }
)

# Retro green monochrome (old terminal style)
RETRO_GREEN_THEME = ColorTheme(
    name="Retro Terminal",
    colors={
        'yellow': (100, 255, 100),         # Bright green
        'white': (0, 255, 0),              # Pure green
        'black': (0, 20, 0),               # Dark green background
        'purple_header': (0, 200, 0),      # Medium green
        'blue_gradient_1': (0, 100, 0),    # Dark green
        'blue_gradient_2': (0, 50, 0),     # Darker green
        'light_blue': (150, 255, 150),     # Light green
        'blue': (150, 255, 150),           # Alias
        'cyan': (100, 255, 100),           # Bright green
        'red': (200, 255, 200),            # Very light green (for alerts)
    }
)

# Amber monochrome (classic IBM terminal)
AMBER_THEME = ColorTheme(
    name="Amber Terminal",
    colors={
        'yellow': (255, 180, 0),           # Bright amber
        'white': (255, 176, 0),            # Pure amber
        'black': (20, 10, 0),              # Dark brown background
        'purple_header': (200, 140, 0),    # Medium amber
        'blue_gradient_1': (100, 70, 0),   # Dark amber
        'blue_gradient_2': (50, 35, 0),    # Darker amber
        'light_blue': (255, 200, 100),     # Light amber
        'blue': (255, 200, 100),           # Alias
        'cyan': (255, 180, 50),            # Bright amber
        'red': (255, 100, 0),              # Orange (for alerts)
    }
)

# All available themes
AVAILABLE_THEMES = {
    'classic': CLASSIC_THEME,
    'dark': DARK_THEME,
    'high_contrast': HIGH_CONTRAST_THEME,
    'retro_green': RETRO_GREEN_THEME,
    'amber': AMBER_THEME,
}

def get_theme(theme_name: str) -> ColorTheme:
    """Get theme by name, fallback to classic"""
    return AVAILABLE_THEMES.get(theme_name, CLASSIC_THEME)


def list_themes() -> list:
    """Get list of available theme names"""
    return list(AVAILABLE_THEMES.keys())

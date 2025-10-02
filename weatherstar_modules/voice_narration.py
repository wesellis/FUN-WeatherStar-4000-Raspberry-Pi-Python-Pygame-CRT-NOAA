#!/usr/bin/env python3
"""
Voice Narration Module
Professional weather announcer voice for accessibility
Maintains authentic 90s Weather Channel vibe
"""

import threading
import time
from typing import Optional, Callable
from datetime import datetime


class VoiceNarrator:
    """Handles text-to-speech narration with audio ducking"""

    def __init__(self):
        self.enabled = False
        self.tts_engine = None
        self.is_speaking = False
        self.duck_callback = None  # Callback to lower music volume
        self.restore_callback = None  # Callback to restore music volume
        self.speech_thread = None
        self.last_announcement_time = 0
        self.min_announcement_interval = 2.0  # Minimum 2 seconds between announcements

        # Try to initialize TTS engine
        self._init_tts()

    def _init_tts(self):
        """Initialize text-to-speech engine"""
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()

            # Configure for professional weather announcer voice
            # Slower rate for clarity (like 90s weather announcers)
            self.tts_engine.setProperty('rate', 150)  # Default is 200

            # Slightly lower volume (0.0 to 1.0)
            self.tts_engine.setProperty('volume', 0.9)

            # Try to set a professional voice (varies by system)
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Prefer male voice for weather announcer authenticity
                for voice in voices:
                    if 'male' in voice.name.lower() and 'female' not in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break

            print("Voice narration initialized successfully")
            return True

        except ImportError:
            print("pyttsx3 not installed. Voice narration disabled.")
            print("Install with: pip install pyttsx3")
            self.tts_engine = None
            return False
        except Exception as e:
            print(f"Error initializing voice narration: {e}")
            self.tts_engine = None
            return False

    def set_audio_callbacks(self, duck_callback: Callable, restore_callback: Callable):
        """Set callbacks for ducking/restoring background music volume"""
        self.duck_callback = duck_callback
        self.restore_callback = restore_callback

    def set_enabled(self, enabled: bool):
        """Enable or disable voice narration"""
        self.enabled = enabled
        if enabled and not self.tts_engine:
            self._init_tts()

    def is_available(self) -> bool:
        """Check if TTS is available"""
        return self.tts_engine is not None

    def _speak_async(self, text: str):
        """Speak text in background thread with audio ducking"""
        if not self.enabled or not self.tts_engine or not text:
            return

        # Prevent rapid-fire announcements
        current_time = time.time()
        if current_time - self.last_announcement_time < self.min_announcement_interval:
            return

        self.last_announcement_time = current_time

        def speak_worker():
            try:
                self.is_speaking = True

                # Duck background music (lower volume to 20%)
                if self.duck_callback:
                    self.duck_callback()

                # Brief pause before speaking (feels more professional)
                time.sleep(0.3)

                # Speak the text
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()

                # Brief pause after speaking
                time.sleep(0.2)

            except Exception as e:
                print(f"Error during speech: {e}")
            finally:
                self.is_speaking = False

                # Restore background music volume
                if self.restore_callback:
                    self.restore_callback()

        # Start speech in background thread
        self.speech_thread = threading.Thread(target=speak_worker, daemon=True)
        self.speech_thread.start()

    def announce_display(self, display_mode: str, weather_data: dict = None):
        """Announce current display with relevant data"""
        if not self.enabled:
            return

        # Generate announcement based on display mode
        announcement = self._generate_announcement(display_mode, weather_data)

        if announcement:
            self._speak_async(announcement)

    def _generate_announcement(self, display_mode: str, weather_data: dict = None) -> str:
        """Generate professional weather announcement text"""

        # Professional 90s-style announcements
        announcements = {
            'current-weather': self._announce_current_conditions(weather_data),
            'current-conditions': self._announce_current_conditions(weather_data),
            'local-forecast': "Now showing your local forecast.",
            'extended-forecast': "Here's your seven day forecast.",
            'hourly-forecast': "Hourly forecast for the next twenty four hours.",
            'latest-observations': "Regional weather observations.",
            'regional-observations': "Regional weather observations.",
            'travel-cities': "Travel forecast for major cities.",
            'almanac': "Weather almanac with record temperatures and sunrise data.",
            'radar': "Local weather radar.",
            'hazards': "Active weather hazards and warnings.",
            'marine-forecast': "Marine forecast for coastal waters.",
            'air-quality': "Air quality and health information.",
            'temperature-graph': "Seven day temperature trend.",
            'history-graphs': "Thirty day weather history.",
            'weather-records': "Record temperatures and precipitation data.",
            'sun-moon': "Sun and moon data.",
            'wind-pressure': "Wind and barometric pressure analysis.",
            'weekend-forecast': "Your weekend forecast.",
            'monthly-outlook': "Monthly weather outlook.",
            'msn-news': "Top news headlines.",
            'reddit-news': "Trending headlines.",
            'local-news': "Local news and information.",
            'severe-weather-alert': "Attention. Severe weather alert in effect.",
        }

        return announcements.get(display_mode, "")

    def _announce_current_conditions(self, weather_data: dict = None) -> str:
        """Generate detailed current conditions announcement"""
        if not weather_data:
            return "Current weather conditions."

        try:
            properties = weather_data.get('properties', {})

            # Build announcement parts
            parts = []

            # Temperature
            temp = properties.get('temperature', {}).get('value')
            if temp is not None:
                temp_f = int(temp * 9/5 + 32)  # Convert C to F if needed
                parts.append(f"Currently {temp_f} degrees")

            # Conditions
            condition = properties.get('textDescription', '')
            if condition:
                parts.append(f"with {condition.lower()}")

            # Wind
            wind_speed = properties.get('windSpeed', {}).get('value')
            wind_dir = properties.get('windDirection', {}).get('value')
            if wind_speed is not None:
                wind_mph = int(wind_speed * 0.621371)  # km/h to mph
                direction = self._wind_direction_to_text(wind_dir)
                parts.append(f"Wind from the {direction} at {wind_mph} miles per hour")

            # Humidity
            humidity = properties.get('relativeHumidity', {}).get('value')
            if humidity is not None:
                parts.append(f"Humidity {int(humidity)} percent")

            if parts:
                return ". ".join(parts) + "."
            else:
                return "Current weather conditions."

        except Exception as e:
            print(f"Error generating conditions announcement: {e}")
            return "Current weather conditions."

    def _wind_direction_to_text(self, degrees: Optional[int]) -> str:
        """Convert wind direction degrees to cardinal direction"""
        if degrees is None:
            return "unknown direction"

        directions = [
            "north", "north northeast", "northeast", "east northeast",
            "east", "east southeast", "southeast", "south southeast",
            "south", "south southwest", "southwest", "west southwest",
            "west", "west northwest", "northwest", "north northwest"
        ]

        index = int((degrees + 11.25) / 22.5) % 16
        return directions[index]

    def announce_alert(self, alert_text: str):
        """Announce severe weather alert (high priority)"""
        if not self.enabled:
            return

        # Format alert professionally
        announcement = f"Attention. {alert_text}"
        self._speak_async(announcement)

    def announce_time(self):
        """Announce current time (like Weather Channel did on the hour)"""
        if not self.enabled:
            return

        now = datetime.now()
        hour = now.strftime("%I").lstrip('0')  # Remove leading zero
        minute = now.strftime("%M")
        am_pm = now.strftime("%p").lower()

        if minute == "00":
            announcement = f"The time is {hour} {am_pm}."
        else:
            announcement = f"The time is {hour} {minute} {am_pm}."

        self._speak_async(announcement)

    def cleanup(self):
        """Clean up TTS resources"""
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass


# Singleton instance
_narrator_instance = None

def get_narrator() -> VoiceNarrator:
    """Get singleton voice narrator instance"""
    global _narrator_instance
    if _narrator_instance is None:
        _narrator_instance = VoiceNarrator()
    return _narrator_instance

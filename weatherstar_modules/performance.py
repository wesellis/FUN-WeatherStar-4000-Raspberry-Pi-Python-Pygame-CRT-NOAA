#!/usr/bin/env python3
"""
Performance Optimization Module for Raspberry Pi
Memory management, caching, and rendering optimizations
"""

import pygame
import gc
import time
from typing import Dict, Optional, Any
from functools import lru_cache
import weakref


class PerformanceMonitor:
    """Monitor FPS, memory usage, and performance metrics"""

    def __init__(self):
        self.frame_times = []
        self.max_samples = 60
        self.last_frame_time = time.time()
        self.fps = 0
        self.frame_count = 0

    def update(self):
        """Update performance metrics"""
        current_time = time.time()
        frame_time = current_time - self.last_frame_time
        self.last_frame_time = current_time

        self.frame_times.append(frame_time)
        if len(self.frame_times) > self.max_samples:
            self.frame_times.pop(0)

        # Calculate FPS
        if self.frame_times:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            self.fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0

        self.frame_count += 1

    def get_fps(self) -> float:
        """Get current FPS"""
        return self.fps

    def get_memory_usage(self) -> int:
        """Get approximate memory usage in MB (basic estimate)"""
        # This is a simple estimate - for detailed profiling use memory_profiler
        gc.collect()
        return len(gc.get_objects()) // 1000  # Rough approximation


class SurfaceCache:
    """Cache rendered surfaces to reduce re-rendering"""

    def __init__(self, max_size: int = 50):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size

    def get(self, key: str) -> Optional[pygame.Surface]:
        """Get cached surface"""
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        return None

    def put(self, key: str, surface: pygame.Surface):
        """Cache a surface"""
        # If cache is full, remove least recently used
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]

        self.cache[key] = surface.copy()
        self.access_times[key] = time.time()

    def clear(self):
        """Clear all cached surfaces"""
        self.cache.clear()
        self.access_times.clear()


class FontCache:
    """Cache font objects to avoid repeated loading"""

    _fonts = {}

    @classmethod
    def get_font(cls, font_path: Optional[str], size: int, bold: bool = False) -> pygame.font.Font:
        """Get cached font or create new one"""
        key = (font_path, size, bold)

        if key not in cls._fonts:
            try:
                if font_path:
                    cls._fonts[key] = pygame.font.Font(font_path, size)
                else:
                    cls._fonts[key] = pygame.font.SysFont('arial', size, bold=bold)
            except:
                cls._fonts[key] = pygame.font.Font(None, size)

        return cls._fonts[key]

    @classmethod
    def clear(cls):
        """Clear font cache"""
        cls._fonts.clear()


class ImageCache:
    """Cache loaded images to reduce disk I/O"""

    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size

    def load_image(self, path: str, scale: Optional[tuple] = None) -> Optional[pygame.Surface]:
        """Load image from cache or disk"""
        cache_key = (path, scale)

        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            image = pygame.image.load(path)
            if scale:
                image = pygame.transform.scale(image, scale)

            # Convert for faster blitting (important for Pi performance)
            if image.get_alpha():
                image = image.convert_alpha()
            else:
                image = image.convert()

            # Cache if space available
            if len(self.cache) < self.max_size:
                self.cache[cache_key] = image

            return image

        except Exception as e:
            print(f"Error loading image {path}: {e}")
            return None

    def clear(self):
        """Clear image cache"""
        self.cache.clear()


class RenderOptimizer:
    """Optimize rendering for Raspberry Pi"""

    def __init__(self):
        self.dirty_rects = []
        self.use_dirty_rects = True  # Only redraw changed areas

    def add_dirty_rect(self, rect: pygame.Rect):
        """Mark rectangle as needing redraw"""
        self.dirty_rects.append(rect)

    def clear_dirty_rects(self):
        """Clear dirty rectangles"""
        self.dirty_rects.clear()

    def get_dirty_rects(self) -> list:
        """Get list of dirty rectangles"""
        return self.dirty_rects

    @staticmethod
    def optimize_surface(surface: pygame.Surface) -> pygame.Surface:
        """Optimize surface for faster blitting"""
        if surface.get_alpha():
            return surface.convert_alpha()
        return surface.convert()

    @staticmethod
    def create_gradient_cached(width: int, height: int,
                              color1: tuple, color2: tuple) -> pygame.Surface:
        """Create optimized gradient surface (cached)"""
        surface = pygame.Surface((width, height))

        # Vertical gradient
        for y in range(height):
            ratio = y / height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

        return surface.convert()


class MemoryManager:
    """Manage memory usage for Raspberry Pi"""

    def __init__(self, gc_interval: int = 300):
        self.gc_interval = gc_interval  # Seconds between forced GC
        self.last_gc_time = time.time()

    def periodic_cleanup(self):
        """Perform periodic garbage collection"""
        current_time = time.time()

        if current_time - self.last_gc_time > self.gc_interval:
            gc.collect()
            self.last_gc_time = current_time

    def emergency_cleanup(self):
        """Emergency memory cleanup"""
        # Clear pygame surface caches
        pygame.font.quit()
        pygame.font.init()

        # Force garbage collection
        gc.collect(2)  # Full collection


class PerformanceOptimizer:
    """Main performance optimization manager"""

    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.surface_cache = SurfaceCache(max_size=30)  # Reduced for Pi
        self.image_cache = ImageCache(max_size=50)  # Reduced for Pi
        self.render_optimizer = RenderOptimizer()
        self.memory_manager = MemoryManager(gc_interval=180)  # GC every 3 mins
        self.frame_skip = 0  # Frame skip counter for low FPS situations

    def update(self, target_fps: int = 30):
        """Update performance systems"""
        self.monitor.update()
        self.memory_manager.periodic_cleanup()

        # Adaptive frame skipping for very low FPS
        current_fps = self.monitor.get_fps()
        if current_fps < target_fps * 0.7:  # If FPS drops below 70% of target
            self.frame_skip = 1  # Skip every other frame
        else:
            self.frame_skip = 0

    def should_skip_frame(self) -> bool:
        """Check if current frame should be skipped"""
        if self.frame_skip > 0:
            self.monitor.frame_count += 1
            return self.monitor.frame_count % 2 == 0
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'fps': round(self.monitor.get_fps(), 1),
            'frame_count': self.monitor.frame_count,
            'memory_estimate': self.monitor.get_memory_usage(),
            'cache_size': len(self.surface_cache.cache),
            'image_cache_size': len(self.image_cache.cache),
        }


# Singleton instance
_performance_optimizer = None

def get_performance_optimizer() -> PerformanceOptimizer:
    """Get singleton performance optimizer"""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer

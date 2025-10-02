#!/usr/bin/env python3
"""
Unit tests for Performance Optimization Module
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from weatherstar_modules.performance import (
    PerformanceMonitor,
    SurfaceCache,
    FontCache,
    ImageCache,
    RenderOptimizer,
    MemoryManager,
    PerformanceOptimizer,
    get_performance_optimizer
)


class TestPerformanceMonitor(unittest.TestCase):
    """Test performance monitoring"""

    def setUp(self):
        self.monitor = PerformanceMonitor()

    def test_initialization(self):
        """Test monitor initializes correctly"""
        self.assertEqual(self.monitor.frame_count, 0)
        self.assertEqual(len(self.monitor.frame_times), 0)

    def test_update(self):
        """Test monitor update"""
        self.monitor.update()
        self.assertEqual(self.monitor.frame_count, 1)
        self.assertEqual(len(self.monitor.frame_times), 1)

    def test_get_fps(self):
        """Test FPS calculation"""
        for _ in range(10):
            self.monitor.update()
        fps = self.monitor.get_fps()
        self.assertGreater(fps, 0)


class TestSurfaceCache(unittest.TestCase):
    """Test surface caching"""

    def setUp(self):
        self.cache = SurfaceCache(max_size=3)

    def test_cache_empty(self):
        """Test empty cache"""
        self.assertIsNone(self.cache.get("nonexistent"))

    def test_cache_put_get(self):
        """Test caching and retrieval"""
        import pygame
        pygame.init()
        surface = pygame.Surface((100, 100))

        self.cache.put("test", surface)
        cached = self.cache.get("test")
        self.assertIsNotNone(cached)

    def test_cache_max_size(self):
        """Test cache size limit"""
        import pygame
        pygame.init()

        for i in range(5):
            surface = pygame.Surface((10, 10))
            self.cache.put(f"key{i}", surface)

        # Should only keep 3 most recent
        self.assertEqual(len(self.cache.cache), 3)

    def test_cache_clear(self):
        """Test cache clearing"""
        import pygame
        pygame.init()
        surface = pygame.Surface((10, 10))

        self.cache.put("test", surface)
        self.cache.clear()
        self.assertEqual(len(self.cache.cache), 0)


class TestFontCache(unittest.TestCase):
    """Test font caching"""

    def test_get_font(self):
        """Test font retrieval"""
        import pygame
        pygame.init()

        font = FontCache.get_font(None, 24)
        self.assertIsInstance(font, pygame.font.Font)

    def test_font_cached(self):
        """Test fonts are cached"""
        import pygame
        pygame.init()

        font1 = FontCache.get_font(None, 24)
        font2 = FontCache.get_font(None, 24)
        self.assertIs(font1, font2)  # Same object


class TestRenderOptimizer(unittest.TestCase):
    """Test render optimization"""

    def setUp(self):
        self.optimizer = RenderOptimizer()

    def test_dirty_rects(self):
        """Test dirty rectangle tracking"""
        import pygame
        rect = pygame.Rect(0, 0, 100, 100)

        self.optimizer.add_dirty_rect(rect)
        self.assertEqual(len(self.optimizer.get_dirty_rects()), 1)

        self.optimizer.clear_dirty_rects()
        self.assertEqual(len(self.optimizer.get_dirty_rects()), 0)


class TestMemoryManager(unittest.TestCase):
    """Test memory management"""

    def test_initialization(self):
        """Test memory manager initialization"""
        manager = MemoryManager(gc_interval=60)
        self.assertEqual(manager.gc_interval, 60)

    def test_periodic_cleanup(self):
        """Test periodic cleanup doesn't crash"""
        manager = MemoryManager(gc_interval=0)
        manager.periodic_cleanup()  # Should trigger GC


class TestPerformanceOptimizer(unittest.TestCase):
    """Test main performance optimizer"""

    def test_initialization(self):
        """Test optimizer initialization"""
        optimizer = PerformanceOptimizer()
        self.assertIsInstance(optimizer.monitor, PerformanceMonitor)
        self.assertIsInstance(optimizer.surface_cache, SurfaceCache)

    def test_update(self):
        """Test optimizer update"""
        optimizer = PerformanceOptimizer()
        optimizer.update(target_fps=30)
        # Should not crash

    def test_get_stats(self):
        """Test stats retrieval"""
        optimizer = PerformanceOptimizer()
        optimizer.update()
        stats = optimizer.get_stats()

        self.assertIn('fps', stats)
        self.assertIn('frame_count', stats)
        self.assertIn('memory_estimate', stats)

    def test_singleton(self):
        """Test singleton pattern"""
        opt1 = get_performance_optimizer()
        opt2 = get_performance_optimizer()
        self.assertIs(opt1, opt2)


if __name__ == '__main__':
    unittest.main()

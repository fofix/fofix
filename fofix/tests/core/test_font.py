#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Tests for the module fofix.core.Font"""

import os
import time
import unittest

import pygame

from fofix.core.Font import Cache
from fofix.core.Font import Font


class CacheTest(unittest.TestCase):

    def setUp(self):
        # init pygame (for ticks)
        pygame.init()

    def test_init(self):
        count = 256
        cache = Cache(count)
        self.assertEqual(cache.elements, dict())
        self.assertEqual(cache.maxCount, count)

    def test_get(self):
        cache = Cache(256)
        # add a key and an element
        key = "my key"
        element = "my element"
        cache.add(key, element)
        # get the element
        elem = cache.get(key)
        self.assertEqual(element, elem)

    def test_add(self):
        count = 2
        cache = Cache(count)

        # add count elements
        keys = [0, 1, 2]
        elements = ["a", "b", "c"]
        for i in range(3):
            key = keys[i]
            element = elements[i]
            cache.add(key, element)
            # check elements
            self.assertIn(key, cache.elements)
            self.assertEqual(cache.get(key), element)
            time.sleep(0.1)

        # check if all (key, element)s are in cache
        self.assertNotIn(keys[0], cache.elements)
        self.assertIn(keys[1], cache.elements)
        self.assertEqual(elements[1], cache.get(keys[1]))
        self.assertIn(keys[2], cache.elements)
        self.assertEqual(elements[2], cache.get(keys[2]))


class FontTest(unittest.TestCase):

    def setUp(self):
        self.filename = os.path.join("data", "fonts", "default.ttf")
        self.size = 2

    def test_get_string_size(self):
        font = Font(self.filename, self.size)
        scale = 1.5
        string_size = font.getStringSize("text", scale)
        self.assertEqual(string_size, (4 * scale, 3 * scale))

    def test_scale_text(self):
        font = Font(self.filename, self.size)
        scale = 1.5
        max_width = 4
        string_size = font.scaleText("text", max_width, scale)
        self.assertEqual(string_size, scale * max_width / 6.0)

    def test_get_height(self):
        font = Font(self.filename, self.size)
        height = font.getHeight()
        self.assertEqual(height, 3)

    def test_get_line_spacing(self):
        font = Font(self.filename, self.size)
        scale = 1.5
        line_spacing = font.getLineSpacing(scale)
        self.assertEqual(line_spacing, 3.0 * scale)

    def test_get_font_ascent(self):
        font = Font(self.filename, self.size)
        scale = 1.5
        height_ascent = font.getFontAscent(scale)
        self.assertEqual(height_ascent, 2.0 * scale)

    def test_get_font_descent(self):
        font = Font(self.filename, self.size)
        scale = 1.5
        height_descent = font.getFontDescent(scale)
        self.assertEqual(height_descent, 0.0)

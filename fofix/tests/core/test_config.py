#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Tests for fofix.core.Config """

import tempfile
import unittest

from fofix.core.Config import MyConfigParser


class MyConfigParserTest(unittest.TestCase):

    def test_write(self):
        config = MyConfigParser()
        items = [
            ("selected_song", "Mötley Crüe".decode("latin1")),
        ]

        with tempfile.TemporaryFile() as tmp:
            # write a complete section manually
            config._writeSection(tmp, "section", items)
            tmp.seek(0)
            lines = tmp.readlines()

        self.assertIn("[section]\n", lines)
        for option, value in items:
            self.assertIn("{} = {}\n".format(option, value.encode("utf-8")), lines)

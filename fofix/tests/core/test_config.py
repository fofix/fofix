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
            # ("selected_song", six.u("Mötley Crüe").encode("latin-1")),
            ("selected_song", "Mötley Crüe"),
        ]

        with tempfile.TemporaryFile(mode='w+') as tmp:
            # write a complete section manually
            config._write_section(tmp, "section", items)
            tmp.seek(0)
            lines = tmp.readlines()

        self.assertIn("[section]\n", lines)
        for option, value in items:
            self.assertIn("{} = {}\n".format(option, value), lines)

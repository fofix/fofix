#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Tests for fofix.core.Config """

import tempfile
import unittest

import six

from fofix.core.Config import MyConfigParser


class MyConfigParserTest(unittest.TestCase):

    def test_write(self):
        config = MyConfigParser()
        items = [
            ("selected_song", six.b("Mötley Crüe").decode("latin-1")),
        ]

        with tempfile.TemporaryFile(mode='w+') as tmp:
            # write a complete section manually
            config._write_section(tmp, "section", items)
            tmp.seek(0)
            lines = tmp.readlines()

        self.assertIn("[section]\n", lines)
        for option, value in items:
            self.assertIn("{} = {}\n".format(option, value.encode("utf-8")), lines)

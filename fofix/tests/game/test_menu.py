#!/usr/bin/python
# -*- coding: utf-8 -*-

# FoFiX
# Copyright (C) 2017 FoFiX team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import unittest

from fofix.core import Config
from fofix.core import Version
from fofix.core.GameEngine import GameEngine
from fofix.game.Menu import Menu


def my_callback():
    print("I'm a callback")


class MenuTest(unittest.TestCase):

    def setUp(self):
        # set config file
        config_file = Version.PROGRAM_UNIXSTYLE_NAME + ".ini"
        self.config = Config.load(config_file, setAsDefault=True)

        # set choices
        choices = [
            ("Choice 1", my_callback),
        ]

        # init the engine
        engine = GameEngine(self.config)

        # init the menu
        self.menu = Menu(engine, choices)

    def test_init(self):
        self.assertGreater(len(self.menu.choices), 0)
        self.assertEqual(self.menu.currentIndex, 0)

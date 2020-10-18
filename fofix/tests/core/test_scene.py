#!/usr/bin/python
# -*- coding: utf-8 -*-

# FoFiX
# Copyright (C) 2020 FoFiX team
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

from fofix.core.GameEngine import GameEngine
from fofix.core.Scene import Scene
from fofix.core import Config
from fofix.core import Version


class SceneTest(unittest.TestCase):

    def setUp(self):
        # set up the engine with a config and a world
        config_filename = Version.PROGRAM_UNIXSTYLE_NAME + ".ini"
        config = Config.load(config_filename, setAsDefault=True)
        self.engine = GameEngine(config)
        self.engine.startWorld(1)

    def test_init(self):
        scene = Scene(self.engine)
        self.assertEqual(scene.engine, self.engine)
        self.assertEqual(scene.time, 0.0)

    def test_add_player(self):
        scene = Scene(self.engine)
        player = "P"
        scene.addPlayer(player)
        self.assertIn(player, scene.players)

    def test_remove_player(self):
        scene = Scene(self.engine)
        player = "P1"
        scene.addPlayer(player)
        self.assertIn(player, scene.players)
        scene.removePlayer(player)
        self.assertNotIn(player, scene.players)

    def test_run(self):
        scene = Scene(self.engine)
        ticks = 1
        scene.run(ticks)
        self.assertEqual(scene.time, ticks / 50.0)

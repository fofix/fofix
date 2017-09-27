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


import tempfile
import unittest

from fretwork import log

from fofix.core import Config
from fofix.core import Version
from fofix.core.GameEngine import GameEngine


class GameEngineTest(unittest.TestCase):

    def setUp(self):
        # set log file
        fp = tempfile.TemporaryFile()
        log.setLogfile(fp)

        # set config file
        config_file = Version.PROGRAM_UNIXSTYLE_NAME + ".ini"
        self.config = Config.load(config_file, setAsDefault=True)

        # init the game engine
        self.engine = GameEngine(self.config)

    def test_init(self):
        self.assertTrue(self.engine.running)

    def test_quit(self):
        self.assertTrue(self.engine.running)
        self.engine.quit()
        self.assertFalse(self.engine.running)

    def tearDown(self):
        self.engine.quit()

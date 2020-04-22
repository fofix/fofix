#!/usr/bin/python
# -*- coding: utf-8 -*-

# FoFiX
# Copyright (C) 2018 FoFiX team
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
from fofix.core.Settings import BasicSettingsMenu
from fofix.core.Settings import SettingsMenu
from fofix.game.MainMenu import MainMenu
from fofix.game.Menu import Menu


class MainMenuTest(unittest.TestCase):

    def setUp(self):
        # set config file
        config_file = Version.PROGRAM_UNIXSTYLE_NAME + ".ini"
        self.config = Config.load(config_file, setAsDefault=True)

        # init the engine
        self.engine = GameEngine(self.config)

        # init the menu
        self.mainmenu = MainMenu(self.engine)

    def tearDown(self):
        self.engine.quit()

    def test_init(self):
        self.assertIsInstance(self.mainmenu.menu, Menu)
        # self.assertIsNotNone(self.mainmenu.menu.mainMenu)
        self.assertFalse(self.mainmenu.shownOnce)  # end of init

    def test_settingsMenu_basic(self):
        self.mainmenu.engine.advSettings = False
        settings_menu = self.mainmenu.settingsMenu()
        self.assertIsInstance(settings_menu, Menu)
        self.assertIsInstance(settings_menu, BasicSettingsMenu)

    def test_settingsMenu_advanced(self):
        self.mainmenu.engine.advSettings = True
        settings_menu = self.mainmenu.settingsMenu()
        self.assertIsInstance(settings_menu, Menu)
        self.assertIsInstance(settings_menu, SettingsMenu)

    def test_runMusic(self):
        self.mainmenu.runMusic()
        #self.assertTrue(self.mainmenu.menumusic)
        if self.mainmenu.menumusic:
            self.assertTrue(self.mainmenu.song.isPlaying())

    def test_setMenuVolume(self):
        self.mainmenu.setMenuVolume()

    def test_cutMusic(self):
        self.mainmenu.cutMusic()
        #time.sleep(1400)
        if self.mainmenu.menumusic:
            self.assertFalse(self.song.isPlaying())

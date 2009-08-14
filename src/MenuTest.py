#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# FoFiX                                                             #
# Copyright (C) 2009 Team FoFiX                                     #
#               2006 Sami Kyöstilä                                  #
#                                                                   #
# This program is free software; you can redistribute it and/or     #
# modify it under the terms of the GNU General Public License       #
# as published by the Free Software Foundation; either version 2    #
# of the License, or (at your option) any later version.            #
#                                                                   #
# This program is distributed in the hope that it will be useful,   #
# but WITHOUT ANY WARRANTY; without even the implied warranty of    #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the     #
# GNU General Public License for more details.                      #
#                                                                   #
# You should have received a copy of the GNU General Public License #
# along with this program; if not, write to the Free Software       #
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,        #
# MA  02110-1301, USA.                                              #
#####################################################################

import unittest
from GameEngine import GameEngine
from Menu import Menu
import Config
import Version

subMenu = [
  ("Bar 1", lambda: 0),
  ("Bar 2", lambda: 0),
  ("Bar 3", lambda: 0),
]

rootMenu = [
  ["Foo", lambda: 0],
  ("Bar >", subMenu),
  ("Baz", lambda: 0),
]

class MenuTest(unittest.TestCase):
  def testMenuNavigation(self):
    m = Menu(self.e, rootMenu)
    self.e.view.pushLayer(m)

  def setUp(self):
    config = Config.load(Version.appName() + ".ini", setAsDefault = True)
    self.e = GameEngine(config)
    
  def tearDown(self):
    self.e.quit()

class MenuTestInteractive(unittest.TestCase):
  def testMenuNavigation(self):
    m = Menu(self.e, rootMenu)
    self.e.view.pushLayer(m)

    while self.e.view.layers:
      self.e.run()

  def setUp(self):
    config = Config.load(Version.appName() + ".ini", setAsDefault = True)
    self.e = GameEngine(config)
    
  def tearDown(self):
    self.e.quit()

if __name__ == "__main__":
  unittest.main()

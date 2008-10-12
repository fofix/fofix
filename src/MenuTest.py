#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
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

    while self.e.view.layers and 0:
      rootMenu[0][0] = "%.1f FPS" % self.e.timer.fpsEstimate
      self.e.run()
    # FIXME: keyboard event injection for testing
     
  def setUp(self):
    self.e = GameEngine()
    
  def tearDown(self):
    self.e.quit()

class MenuTestInteractive(unittest.TestCase):
  def testMenuNavigation(self):
    m = Menu(self.e, rootMenu)
    self.e.view.pushLayer(m)

    while self.e.view.layers:
      rootMenu[0][0] = "%.1f FPS" % self.e.timer.fpsEstimate
      self.e.run()

  def setUp(self):
    self.e = GameEngine()
    
  def tearDown(self):
    self.e.quit()

if __name__ == "__main__":
  unittest.main()

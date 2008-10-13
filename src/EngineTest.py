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
from Engine import Engine
from Player import Player
from World import World
import Network

"""
class EngineTest(unittest.TestCase):
  def testStartup(self):
    e1 = Engine()
    e2 = Engine()
    
    e1.startServer()
    e2.connect("localhost")

    while not e2.isConnected():
      e1.run()
      e2.run()

    while not e2.world:
      e1.run()
      e2.run()

    e1.world.createPlayer("mario")

    while not len(e2.world.players):
      e1.run()
      e2.run()

    assert len(e1.world.players) == 1
    assert len(e2.world.players) == 1

    assert e2.world.players[0].name == "mario"

    assert e1.manager
    assert e2.manager

    assert e1.world
    assert e2.world

    e1.stopServer()
    
    e1.quit()
    e2.quit()
"""

if __name__ == "__main__":
  unittest.main()

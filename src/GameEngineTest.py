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

class EngineTest(unittest.TestCase):
  def testNetworking(self):
    e1 = GameEngine()
    
    e1.startServer()
    session1 = e1.connect("localhost")
    session2 = e1.connect("localhost")

    while not session1.isConnected() or not session2.isConnected():
      e1.run()

    session1.world.createPlayer("mario")
    session2.world.createPlayer("luigi")
    
    for i in range(10):
      e1.run()

    assert len(e1.server.world.players) == 2
    assert len(session1.world.players) == 2
    assert len(session2.world.players) == 2
    
    session3 = e1.connect("localhost")
    
    for i in range(10):
      e1.run()

    assert len(session3.world.players) == 2

    session1.disconnect()
    
    for i in range(10):
      e1.run()

    assert len(e1.server.world.players) == 1
    assert len(session2.world.players) == 1

    e1.quit()

if __name__ == "__main__":
  unittest.main()

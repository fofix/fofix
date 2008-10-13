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
from View import View, Layer

class TestLayer(Layer):
  def __init__(self):
    self.visibility = 0
    self.topMost = False
    
  def render(self, visibility, topMost):
    self.visibility = visibility
    self.topMost = topMost

  def __repr__(self):
    return "Layer(%x)" % abs(id(self))

class ViewTest(unittest.TestCase):
  def testTransition(self):
    l1 = TestLayer()
    l2 = TestLayer()
    l3 = TestLayer()
    v = self.e.view
    
    v.pushLayer(l1)
    v.pushLayer(l2)
    v.pushLayer(l3)
    
    while l3.visibility < 1.0:
      self.e.run()
      
    v.popLayer(l3)
    v.popLayer(l2)
    v.popLayer(l1)
    
    while l1 in v.layers or l2 in v.layers or l3 in v.layers:
      self.e.run()

    assert not v.layers
      
  def setUp(self):
    self.e = GameEngine()
    
  def tearDown(self):
    self.e.quit()

if __name__ == "__main__":
  unittest.main()

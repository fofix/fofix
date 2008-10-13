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
import time
import pygame
from Timer import Timer

class TimerTest(unittest.TestCase):
  def setUp(self):
    pygame.init()

  def tearDown(self):
    pygame.quit()
  
  def testFrameLimiter(self):
    t = Timer(fps = 60)

    fps = []
    while t.frame < 100:
      ticks = list(t.advanceFrame())
      fps.append(t.fpsEstimate)

    fps = fps[30:]
    avgFps = sum(fps) / len(fps)
    assert 0.8 * t.fps < avgFps < 1.2 * t.fps

if __name__ == "__main__":
  unittest.main()

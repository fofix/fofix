#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# FoFiX                                                             #
# Copyright (C) 2009 Pascal Giard <evilynux@gmail.com>              #
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
import Config
import Version
from VideoPlayer import VideoPlayer

# Please change these values to fit your needs.
# Note that video codecs/format supported depends on the gstreamer plugins
# you've installed. On my machine that means pretty much anything e.g. XviD,
# Ogg Theora, Flash, FFmpeg H.264, etc.).
winSize = (800, 600) # Window width and height
framerate = 24       # Number of frames per seconds (-1 = as fast as it can)
# vidSource = "t1.avi" # Path to video; relative to the current directory
# vidSize = (320, 240) # Video width and height
# FIXME: Autodetect video width and height values.

# Other video examples
#=====================
# FFmpeg H.264
vidSource = "t2.m4v"
vidSize = (640, 368)

# Macromedia Flash
# vidSource = "t3.flv"
# vidSize = (320, 240)
# vidSource = "t3.1.flv" # 24 seconds
# vidSize = (320, 214)

# Xiph Ogg Theora
# vidSource = "t4.ogv"
# vidSize = (320, 240)

class VideoPlayerTest(unittest.TestCase):
  def testVideoPlayer(self):
    vidPlayer = VideoPlayer(self.e, framerate, vidSource, vidSize)
    self.e.view.pushLayer(vidPlayer)

    while self.e.view.layers:
      self.e.run()

  def setUp(self):
    config = Config.load(Version.appName() + ".ini", setAsDefault = True)
    self.e = GameEngine(config)
    
  def tearDown(self):
    self.e.quit()

if __name__ == "__main__":
  unittest.main()

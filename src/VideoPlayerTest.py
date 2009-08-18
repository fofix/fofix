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
import os
import pygame
from pygame.locals import *
from OpenGL.GL import *

from GameEngine import GameEngine
import Config
import Version
from VideoPlayer import VideoPlayer

# Please change these values to fit your needs.
# Note that video codecs/format supported depends on the gstreamer plugins
# you've installed. On my machine that means pretty much anything e.g. XviD,
# Ogg Theora, Flash, FFmpeg H.264, etc.).
framerate = 24 # Number of frames per seconds (-1 = as fast as it can)
# vidSource    # Path to video; relative to FoFiX data/ directory

# FIXME: Should autodetect video width and height values.

# Video examples
#=====================
# XviD/MPEG-4
# vidSource = "t1.avi"

# FFmpeg H.264
# vidSource = "t2.m4v"

# Macromedia Flash
# vidSource = "t3.flv"
vidSource = "t3.1.flv" # 24 seconds

# Xiph Ogg Theora
# vidSource = "t4.ogv"

class VideoPlayerTest(unittest.TestCase):
  # Simplest way to use the video player, use it as a Layer
  def testVideoPlayerLayer(self):
    vidPlayer = VideoPlayer(self.e, framerate, self.src, loop = False)
    self.e.view.pushLayer(vidPlayer)
    while not vidPlayer.finished:
      self.e.run()

  # Keep tight control over the video player
  def testVideoPlayerSlave(self):
    winWidth, winHeight = 800, 600
    pygame.init()
    flags = DOUBLEBUF|OPENGL|HWPALETTE|HWSURFACE
    vidPlayer = VideoPlayer(self.e, framerate, self.src, (winWidth, winHeight))
    pygame.display.set_mode((winWidth, winHeight), flags)
    glViewport(0, 0, winWidth, winHeight) # Required as GameEngine changes it
    font = self.e.data.font
    while not vidPlayer.finished:
      vidPlayer.run()
      vidPlayer.render()
      pygame.display.flip()

  # Grab the texture, use the CallList and do whatever we want with it;
  # We could also _just_ use the texture and take care of the polygons ourselves
  def testVideoPlayerSlaveShowOff(self):
    winWidth, winHeight = 500, 500
    pygame.init()
    flags = DOUBLEBUF|OPENGL|HWPALETTE|HWSURFACE
    vidPlayer = VideoPlayer(self.e, -1, self.src, (winWidth, winHeight))
    pygame.display.set_mode((winWidth, winHeight), flags)
    glViewport(0, 0, winWidth, winHeight) # Required as GameEngine changes it
    glClearColor(0, 0, 0, 1.)
    x, y = 0.0, 1.0
    fx, fy, ftheta = 1, 1, 1
    theta = 0.0
    time = 0.0
    clock = pygame.time.Clock()
    while not vidPlayer.finished:
      vidPlayer.run()
      vidPlayer.textureUpdate()
      # Save and clear both transformation matrices
      glMatrixMode(GL_PROJECTION)
      glPushMatrix()
      glLoadIdentity()
      glMatrixMode(GL_MODELVIEW)
      glPushMatrix()
      glLoadIdentity()

      glClear(GL_COLOR_BUFFER_BIT)
      glColor3f(1., 1., 1.)
      glBindTexture(GL_TEXTURE_2D, vidPlayer.videoTex)
      glTranslatef(x, y, 0)
      glRotatef(theta, 0, 0, 1.)
      glScalef(.5, .5, 1.)
      glCallList(vidPlayer.videoList)

      # Restore both transformation matrices
      glPopMatrix()
      glMatrixMode(GL_PROJECTION)
      glPopMatrix()

      pygame.display.flip()

      x = (x + fx*time)
      y = (y + fy*time)
      theta = theta + ftheta
      if x > 1.0 or x < -1.0:
        fx = fx * -1
      if y > 1.0 or y < -1.0:
        fy = fy * -1
      if theta > 90 or theta < -90:
        ftheta = ftheta * -1
      time = time + 0.00001
      clock.tick(60)

  def setUp(self):
    config = Config.load(Version.appName() + ".ini", setAsDefault = True)
    self.e = GameEngine(config)
    self.src = os.path.join(Version.dataPath(), vidSource)
    
  def tearDown(self):
    self.e.quit()

if __name__ == "__main__":
  unittest.main()

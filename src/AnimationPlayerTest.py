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
from AnimationPlayer import AnimationPlayer

# Please change these values to fit your needs.
# FIXME: Specify which image types are supported.
framerate = 24 # Number of frames per seconds (-1 = as fast as it can)
# animPath     # Basename of your animation sequence;
               # relative to FoFiX data/ directory
# animBasename # Image prefix

# FIXME: Should autodetect image width and height values.

# Examples
#=====================
# PNG image, 640 x 480, 8-bit/color RGBA, non-interlaced
# animPath     = "themes/STaRZ/stages/Starz"
# animBasename = "starz"

animPath     = os.path.join("themes","Guitar Hero III", "videos")
animBasename = "loading_flying"

#animPath     = "/tmp/stage"
#animBasename = "starz"

class AnimationPlayerTest(unittest.TestCase):
  # Simplest way to use the Animation player, use it as a Layer
  def testAnimationPlayerLayer(self):
    loop = 10
    config = Config.load(Version.appName() + ".ini", setAsDefault = True)
    self.e = GameEngine(config)
    animPlayer = AnimationPlayer(framerate, self.path, self.basename,
                                 (self.e.view.geometry[2],
                                  self.e.view.geometry[3]), loop = loop)
    print "Rendering as a GameEngine Layer for %d loops." % loop
    self.e.view.pushLayer(animPlayer)
    startTime = pygame.time.get_ticks()
    while not animPlayer.finished:
      self.e.run()
    stopTime = pygame.time.get_ticks()
    totalTime = stopTime - startTime
    print "nbrFrames: %d, nbrLoops: %d, Total time: %.02f s, Average fps: %.02f" % \
          (animPlayer.nbrFrames, loop, totalTime/1000.0, \
           (float(1000.0*animPlayer.nbrFrames*(loop+1)) / float(totalTime)))
    self.e.view.popLayer(animPlayer)
    self.e.quit()

  # Keep tight control over the Animation player
  def testAnimationPlayerSlave(self):
    loop = 5
    winWidth, winHeight = 800, 600
    pygame.init()
    flags = DOUBLEBUF|OPENGL|HWPALETTE|HWSURFACE
    pygame.display.set_mode((winWidth, winHeight), flags)
    animPlayer = AnimationPlayer(framerate, self.path, self.basename,
                                 (winWidth, winHeight), loop = loop)
    glViewport(0, 0, winWidth, winHeight) # Both required as...
    glScissor(0, 0, winWidth, winHeight)  # ...GameEngine changes it
    glClearColor(0, 0, 0, 1.)
    print "Rendering independently and fullscreen for %d loops." % loop
    clock = pygame.time.Clock()
    startTime = pygame.time.get_ticks()
    while not animPlayer.finished:
      ticks = clock.get_time()
      animPlayer.run(ticks)
      animPlayer.render()
      pygame.display.flip()
      clock.tick()
    stopTime = pygame.time.get_ticks()
    totalTime = stopTime - startTime
    print "nbrFrames: %d, nbrLoops: %d, Total time: %.02f s, Average fps: %.02f" % \
          (animPlayer.nbrFrames, loop, totalTime/1000.0,
           1000.0*animPlayer.nbrFrames*(loop+1) / float(totalTime))

    # Testing animation change
    # FIXME: another set of files would be more relevant (e.g. diff. resolution)
    loop = 5
    print "Let's go for another ride of %d loops." % loop
    animPlayer.loop = loop
    animPlayer.loadAnimation(self.path, self.basename)
    startTime = pygame.time.get_ticks()
    while not animPlayer.finished:
      ticks = clock.get_time()
      animPlayer.run(ticks)
      animPlayer.render()
      pygame.display.flip()
      clock.tick()
    stopTime = pygame.time.get_ticks()
    totalTime = stopTime - startTime
    print "nbrFrames: %d, nbrLoops: %d, Total time: %.02f s, Average fps: %.02f" % \
          (animPlayer.nbrFrames, loop, totalTime/1000.0,
           1000.0*animPlayer.nbrFrames*(loop+1) / float(totalTime))
    pygame.quit()

  # Grab the texture, use the CallList and do whatever we want with it;
  # We could also _just_ use the texture and take care of the polygons ourselves
  def testAnimationPlayerSlaveShowOff(self):
    winWidth, winHeight = 500, 500
    loop = 4
    pygame.init()
    flags = DOUBLEBUF|OPENGL|HWPALETTE|HWSURFACE
    pygame.display.set_mode((winWidth, winHeight), flags)
    animPlayer = AnimationPlayer(framerate, self.path, self.basename,
                                 (winWidth, winHeight), loop = loop)
    print "Rendering ourselves, doing what we want with the texture, for %d loops." % loop
    glViewport(0, 0, winWidth, winHeight) # Both required as...
    glScissor(0, 0, winWidth, winHeight)  # ...GameEngine changes it
    glClearColor(0, 0, 0, 1.)
    x, y = 0.0, 1.0
    fx, fy, ftheta = 1, 1, 1
    theta = 0.0
    time = 0.0
    clock = pygame.time.Clock()
    startTime = pygame.time.get_ticks()
    while not animPlayer.finished:
      ticks = clock.get_time()
      animPlayer.run(ticks)
      texture = animPlayer.getTexture()
      # Save and clear both transformation matrices
      glMatrixMode(GL_PROJECTION)
      glPushMatrix()
      glLoadIdentity()
      glMatrixMode(GL_MODELVIEW)
      glPushMatrix()
      glLoadIdentity()

      glClear(GL_COLOR_BUFFER_BIT)
      glColor3f(1., 1., 1.)
      glBindTexture(GL_TEXTURE_2D, texture)
      glTranslatef(x, y, 0)
      glRotatef(theta, 0, 0, 1.)
      glScalef(.5, .5, 1.)
      glCallList(animPlayer.animList)

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
    stopTime = pygame.time.get_ticks()
    totalTime = stopTime - startTime
    print "nbrFrames: %d, nbrLoops %d, Total time: %.02f s, Average fps: %.02f" % \
          (animPlayer.nbrFrames, loop, totalTime/1000.0, \
           (float(1000.0*animPlayer.nbrFrames*(loop+1)) / float(totalTime)))
    
    pygame.quit()

  def setUp(self):
    self.path = os.path.join(Version.dataPath(), animPath)
    self.basename = animBasename
    print "Initializing..."
    
  def tearDown(self):
    pass

suite = unittest.TestLoader().loadTestsFromTestCase(AnimationPlayerTest)
unittest.TextTestRunner(verbosity=2).run(suite)
#if __name__ == "__main__":
#  unittest.main()

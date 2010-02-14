#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#####################################################################
# Animation Layer for FoFiX                                         #
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
import os
import sys

from math import fabs as abs # Absolute value

import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *
# Array-based drawing
from numpy import array, float32

from View import View, BackgroundLayer
import Log

# Simple animation player
class AnimationPlayer(BackgroundLayer):
  def __init__(self, framerate, animSource, animBasename, (winWidth, winHeight) = (None, None), mute = False, loop = 0):
    self.updated = False
    self.animList = None
    self.animTexs = []
    self.animPath = None
    self.animBasename = None
    self.animFiles = []
    self.animImgs = []
    self.mute = mute
    self.loop = loop
    if winWidth is not None and winHeight is not None:
      self.winWidth, self.winHeight = winWidth, winHeight
    else: # default
      self.winWidth, self.winHeight = (640, 480)
      Log.warning("AnimationPlayer: No resolution specified (default %dx%d)",
                  self.winWidth, self.winHeight)
    self.fps = framerate
    self.paused = False
    self.finished = False
    self.ticks = 0
    self.curFrame = 0
    self.nbrFrames = 0

    if not pygame.image.get_extended():
      Log.warn("AnimationPlayer: Your pygame does not support extended image formats.")
    self.loadAnimation(animSource, animBasename) # Load the animation

  # Load a new animation:
  # 1) Detect image resolution
  # 2) Setup OpenGL texture
  def loadAnimation(self, animPath, animBasename):
    if not os.path.exists(animPath):
      Log.error("AnimationPlayer: %s does not exist!" % animPath)
    Log.debug("AnimationPlayer: Found files %s*" % animPath)
    self.finished = False
    self.animPath = animPath
    self.animImgs = []
    self.ticks = 0
    allfiles = os.listdir(self.animPath)
    allfiles.sort()
    nbrFiles = len(allfiles)
    progress = 0
    for name in allfiles:
      progress = progress + 1.0
      if name.startswith(animBasename):
        path = os.path.join(animPath, name)
        try:
          img = pygame.image.load(path)
          if img.get_alpha() is None:
            self.animImgs.append(img.convert())
          else:
            self.animImgs.append(img.convert_alpha())
        except pygame.error, message:
          Log.error("Failed to load %s" % path)
          raise SystemExit, message
      Log.debug("AnimationPlayer progress: %d%%" % \
                ( 100*progress / (2*nbrFiles) ))
    if len(self.animImgs) == 0:
      Log.error("AnimationPlayer: No files found")
    self.nbrFrames = len(self.animImgs)
    self.animBasename = animBasename
    self.textureSetup()

  def textureSetup(self):
    # Free memory if we already allocated space for textures.
    if len(self.animTexs) > 0:
      glDeleteTextures(self.animTexs)

    self.animTexs = glGenTextures(len(self.animImgs))
    for texIdx, img in enumerate(self.animImgs):
      animSize = img.get_size()
      if img.get_alpha is None:
        color = "RGB"
        colorGL = GL_RGB
      else:
        color = "RGBA"
        colorGL = GL_RGBA
      
#       Log.debug("AnimationPlayer: Image %d format: %s (%dx%d)" % (texIdx, color, animSize[0], animSize[1]))
      glBindTexture(GL_TEXTURE_2D, self.animTexs[texIdx])
      surfaceData = pygame.image.tostring(img, color, True)
      # Linear filtering
      glTexImage2D(GL_TEXTURE_2D, 0, 3, animSize[0], animSize[1], 0, colorGL,
                   GL_UNSIGNED_BYTE, surfaceData)
      # MipMapping
#       gluBuild2DMipmaps(GL_TEXTURE_2D, colorGL,
#                         animSize[0], animSize[1], colorGL,
#                         GL_UNSIGNED_BYTE, surfaceData)
      glTexParameteri(GL_TEXTURE_2D, 
                      GL_TEXTURE_MAG_FILTER, GL_LINEAR)
      glTexParameteri(GL_TEXTURE_2D,
                      GL_TEXTURE_MIN_FILTER, GL_LINEAR)
      Log.debug("AnimationPlayer progress: %d%%" % \
                ( 100*(texIdx+1+len(self.animImgs)) / \
                  (2*len(self.animImgs)) ))

    # Resize animation (polygon) to respect resolution ratio
    # (The math is actually simple, take the time to draw it down if required)
    winRes = float(self.winWidth)/float(self.winHeight)
    animWidth = float(self.animImgs[0].get_size()[0])
    animHeight = float(self.animImgs[0].get_size()[1])
    animRes = animWidth/animHeight
    vtxX = 1.0
    vtxY = 1.0
    if winRes > animRes:
      r = float(self.winHeight)/animHeight
      vtxX = 1.0 - abs(self.winWidth-r*animWidth) / (float(self.winWidth))
    elif winRes < animRes:
      r = float(self.winWidth)/animWidth
      vtxY = 1.0 - abs(self.winHeight-r*animHeight) / (float(self.winHeight))

    # Vertices
    animVtx = array([[-vtxX,  vtxY],
                     [ vtxX, -vtxY],
                     [ vtxX,  vtxY],
                     [-vtxX,  vtxY],
                     [-vtxX, -vtxY],
                     [ vtxX, -vtxY]], dtype=float32)
    # Texture coordinates
    texCoord = array([[0.0, 1.0],
                      [1.0, 0.0],
                      [1.0, 1.0],
                      [0.0, 1.0],
                      [0.0, 0.0],
                      [1.0, 0.0]], dtype=float32)
    
    # Create a compiled OpenGL call list and do array-based drawing
    # Could have used GL_QUADS but IIRC triangles are recommended
    self.animList = glGenLists(1)
    glNewList(self.animList, GL_COMPILE)
    glEnable(GL_TEXTURE_2D)
    glColor3f(1., 1., 1.)
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY);
    glVertexPointerf(animVtx)
    glTexCoordPointerf(texCoord)
    glDrawArrays(GL_TRIANGLE_STRIP, 0, animVtx.shape[0])
    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_TEXTURE_COORD_ARRAY);
    glDisable(GL_TEXTURE_2D)
    glEndList()

  def shown(self):
    pass
  
  def hidden(self):
    pass

  def run(self, ticks = None):
    self.ticks = self.ticks + ticks
    
    if not self.paused:
      self.curFrame = self.curFrame + int(self.ticks*self.fps/1000.0)
      self.ticks = self.ticks % (1000.0/self.fps)
#       print "frame: %03d/%03d loop: %d" % (self.curFrame, (self.nbrFrames-1), self.loop)
      if self.loop != -1 and self.curFrame >= ( self.nbrFrames - 1 ):
        if not self.loop or self.loop == 0:
          self.finished = True
        else:
          self.loop = self.loop - 1
      self.curFrame = self.curFrame % ( self.nbrFrames - 1 )
    else:
      self.ticks = 0

  # Return texture
  def getTexture(self):
    return self.animTexs[self.curFrame]
  
  # Render texture to polygon
  # Note: Both visibility and topMost are currently unused.
  def render(self, visibility = 1.0, topMost = False):
    try:
      # Save and clear both transformation matrices
      glMatrixMode(GL_PROJECTION)
      glPushMatrix()
      glLoadIdentity()
      glMatrixMode(GL_MODELVIEW)
      glPushMatrix()
      glLoadIdentity()
      # Draw the polygon and apply texture
      glBindTexture(GL_TEXTURE_2D, self.animTexs[self.curFrame])
      glCallList(self.animList)
      # Restore both transformation matrices
      glPopMatrix()
      glMatrixMode(GL_PROJECTION)
      glPopMatrix()
    except:
      Log.error("AnimationPlayer: Error attempting to play animation")

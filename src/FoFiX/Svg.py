#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X                                                   #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
#               2008 evilynux <evilynux@gmail.com>                  #
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
from OpenGL.GL import *

import numpy as np
from numpy import array, float32
import math

import Log
import Config
from Texture import Texture, TextureException
from PIL import Image

#stump: the last few stubs of DummyAmanith.py are inlined here since this
# is the only place in the whole program that uses it now that we've pruned
# the dead SVG code.
class SvgContext(object):
  def __init__(self, geometry):
    self.geometry = geometry
    self.transform = SvgTransform()
    self.setGeometry(geometry)
    self.setProjection(geometry)
    glMatrixMode(GL_MODELVIEW)
  
  def setGeometry(self, geometry = None):
    glViewport(geometry[0], geometry[1], geometry[2], geometry[3])
    self.transform.reset()
    self.transform.scale(geometry[2] / 640.0, geometry[3] / 480.0)

  def setProjection(self, geometry = None):
    geometry = geometry or self.geometry
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(geometry[0], geometry[0] + geometry[2], geometry[1], geometry[1] + geometry[3], -100, 100)
    glMatrixMode(GL_MODELVIEW)
    self.geometry = geometry

  def clear(self, r = 0, g = 0, b = 0, a = 0):
    glDepthMask(1)
    glEnable(GL_COLOR_MATERIAL)
    glClearColor(r, g, b, a)
    glClear(GL_COLOR_BUFFER_BIT | GL_STENCIL_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


class SvgTransform(object):
  def __init__(self, baseTransform = None):
    self.reset()
    if baseTransform is not None:
      self.ops = baseTransform.ops[:]

  def transform(self, transform):
    self.ops.extend(transform.ops)

  def reset(self):
    self.ops = []

  def translate(self, dx, dy):
    # The old code did this with a matrix addition, not a multiplication.
    # We get the same effect by doing the translations before anything else.
    self.ops.insert(0, lambda: glTranslatef(dx, dy, 0))

  def rotate(self, angle):
    self.ops.append(lambda: glRotatef(math.degrees(angle), 0.0, 0.0, 1.0))

  def scale(self, sx, sy):
    self.ops.append(lambda: glScalef(sx, sy, 1.0))

  def applyGL(self):
    for op in self.ops:
      op()


class ImgDrawing(object):
  def __init__(self, context, ImgData):
    self.ImgData = None
    self.texture = None
    self.context = context
    self.cache = None
    self.transform = SvgTransform()
    self.filename = ImgData
    self.triangVtx = np.zeros((4,2), dtype=float32)
    self.textriangVtx = np.zeros((4,2), dtype=float32)

    # Detect the type of data passed in
    if type(ImgData) == file:
      self.ImgData = ImgData.read()
    elif type(ImgData) == str:
      self.texture = Texture(ImgData)
#      bitmapFile = ImgData.replace(".svg", ".png")
#      # Load PNG files directly
#      if ImgData.endswith(".png"):
#        self.texture = Texture(ImgData)
#      elif ImgData.endswith(".jpg"):
#        self.texture = Texture(ImgData)
#      elif ImgData.endswith(".jpeg"):
#        self.texture = Texture(ImgData)
      # Check whether we have a prerendered bitmap version of the SVG file
#      elif ImgData.endswith(".svg") and os.path.exists(bitmapFile):
#        Log.debug("Loading cached bitmap '%s' instead of '%s'." % (bitmapFile, ImgData))
#        self.texture = Texture(bitmapFile)
#      else:
#        if not haveAmanith:
#          e = "PyAmanith support is deprecated and you are trying to load an SVG file."
#          Log.error(e)
#          raise RuntimeError(e)
#        Log.debug("Loading SVG file '%s'." % (ImgData))
#        self.ImgData = open(ImgData).read()
    elif isinstance(ImgData, Image.Image): #stump: let a PIL image be passed in
      self.texture = Texture()
      self.texture.loadImage(ImgData)

    # Make sure we have a valid texture
    if not self.texture:
      if type(ImgData) == str:
        e = "Unable to load texture for %s." % ImgData
      else:
        e = "Unable to load texture for SVG file."
      Log.error(e)
      raise RuntimeError(e)

  def convertToTexture(self, width, height):
    if self.texture:
      return

    e = "SVG drawing does not have a valid texture image."
    Log.error(e)
    raise RuntimeError(e)

  def _getEffectiveTransform(self):
    transform = SvgTransform(self.transform)
    transform.transform(self.context.transform)
    return transform

  def width1(self):
    width = self.texture.pixelSize[0]
    if not width == None:
      return width
    else:
      return 0

  #myfingershurt:
  def height1(self):
    height = self.texture.pixelSize[1]
    if not height == None:
      return height
    else:
      return 0


  def widthf(self, pixelw):
    width = self.texture.pixelSize[0]
    wfactor = pixelw/width
    if not width == None:
      return wfactor
    else:
      return 0    

  def draw(self, color = (1, 1, 1, 1), rect = (0,1,0,1), lOffset = 0.0, rOffset = 0.0):
    glMatrixMode(GL_TEXTURE)
    glPushMatrix()
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    self.context.setProjection()
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()

    glLoadIdentity()
    self._getEffectiveTransform().applyGL()

    glScalef(self.texture.pixelSize[0], self.texture.pixelSize[1], 1)
    glTranslatef(-.5, -.5, 0)
    glColor4f(*color)


    glEnable(GL_TEXTURE_2D)
    self.texture.bind()
    
    self.triangVtx[0,0] = 0.0-lOffset
    self.triangVtx[0,1] = 1.0
    self.triangVtx[1,0] = 1.0-rOffset
    self.triangVtx[1,1] = 1.0
    self.triangVtx[2,0] = 0.0+lOffset
    self.triangVtx[2,1] = 0.0
    self.triangVtx[3,0] = 1.0+rOffset
    self.triangVtx[3,1] = 0.0
    
    self.textriangVtx[0,0] = rect[0]
    self.textriangVtx[0,1] = rect[3]
    self.textriangVtx[1,0] = rect[1]
    self.textriangVtx[1,1] = rect[3]
    self.textriangVtx[2,0] = rect[0]
    self.textriangVtx[2,1] = rect[2]
    self.textriangVtx[3,0] = rect[1]
    self.textriangVtx[3,1] = rect[2]
    
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)    
    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointerf(self.triangVtx)
    glTexCoordPointerf(self.textriangVtx)
    glDrawArrays(GL_TRIANGLE_STRIP, 0, self.triangVtx.shape[0])
    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_TEXTURE_COORD_ARRAY)
    
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()
    glMatrixMode(GL_TEXTURE)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

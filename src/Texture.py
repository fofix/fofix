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

from __future__ import division

import Log
from PIL import Image
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

class TextureException(Exception):
  pass

# A queue containing (function, args) pairs that clean up deleted OpenGL handles.
# The functions are called in the main OpenGL thread.
#stump: Replaced queue with list to avoid deadlocking under
# certain conditions due to a bug in Python.
cleanupQueue = []

class Texture:
  """Represents an OpenGL texture, optionally loaded from disk in any format supported by PIL"""

  def __init__(self, name = None, target = GL_TEXTURE_2D, useMipmaps = True):
    # Delete all pending textures
    try:
      func, args = cleanupQueue[0]
      del cleanupQueue[0]
      func(*args)
    except IndexError:
      pass
    except Exception, e:    #MFH - to catch "did you call glewInit?" crashes
      Log.error("Texture.py texture deletion exception: %s" % e)
    
    self.texture = glGenTextures(1)
    self.texEnv = GL_MODULATE
    self.glTarget = target
    self.framebuffer = None
    self.useMipmaps = useMipmaps

    self.setDefaults()
    self.name = name

    if name:
      self.loadFile(name)

  def loadFile(self, name):
    """Load the texture from disk, using PIL to open the file"""
    self.loadImage(Image.open(name))
    self.name = name

  def loadImage(self, image):
    """Load the texture from a PIL image"""
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    if image.mode == "RGBA":
      string = image.tostring('raw', 'RGBA', 0, -1)
      self.loadRaw(image.size, string, GL_RGBA, 4)
    elif image.mode == "RGB":
      string = image.tostring('raw', 'RGB', 0, -1)
      self.loadRaw(image.size, string, GL_RGB, 3)
    elif image.mode == "L":
      string = image.tostring('raw', 'L', 0, -1)
      self.loadRaw(image.size, string, GL_LUMINANCE, 1)
    else:
      try:
        image = image.convert('RGB')
        Log.warn("Unsupported image mode '%s' converted to 'RGB'. May have unexpected results." % image.mode)
        string = image.tostring('raw', 'RGB', 0, -1)
        self.loadRaw(image.size, string, GL_RGB, 3)
      except:
        raise TextureException("Unsupported image mode '%s'" % image.mode)

  def nextPowerOfTwo(self, n):
    m = 1
    while m < n:
      m <<= 1
    return m

  def loadSurface(self, surface, monochrome = False, alphaChannel = False):
    """Load the texture from a pygame surface"""

    # make it a power of two
    self.pixelSize = w, h = surface.get_size()
    w2, h2 = [self.nextPowerOfTwo(x) for x in [w, h]]
    if w != w2 or h != h2:
      s = pygame.Surface((w2, h2), pygame.SRCALPHA, 32)
      s.blit(surface, (0, h2 - h))
      surface = s
    
    if monochrome:
      # pygame doesn't support monochrome, so the fastest way
      # appears to be using PIL to do the conversion.
      string = pygame.image.tostring(surface, "RGB")
      image = Image.fromstring("RGB", surface.get_size(), string).convert("L")
      string = image.tostring('raw', 'L', 0, -1)
      self.loadRaw(surface.get_size(), string, GL_LUMINANCE, GL_INTENSITY8)
    else:
      if alphaChannel:
        string = pygame.image.tostring(surface, "RGBA", True)
        self.loadRaw(surface.get_size(), string, GL_RGBA, 4)
      else:
        string = pygame.image.tostring(surface, "RGB", True)
        self.loadRaw(surface.get_size(), string, GL_RGB, 3)
    self.size = (w / w2, h / h2)

  def loadSubsurface(self, surface, position = (0, 0), monochrome = False, alphaChannel = False):
    """Load the texture from a pygame surface"""

    if monochrome:
      # pygame doesn't support monochrome, so the fastest way
      # appears to be using PIL to do the conversion.
      string = pygame.image.tostring(surface, "RGB")
      image = Image.fromstring("RGB", surface.get_size(), string).convert("L")
      string = image.tostring('raw', 'L', 0, -1)
      self.loadSubRaw(surface.get_size(), position, string, GL_INTENSITY8)
    else:
      if alphaChannel:
        string = pygame.image.tostring(surface, "RGBA", True)
        self.loadSubRaw(surface.get_size(), position, string, GL_RGBA)
      else:
        string = pygame.image.tostring(surface, "RGB", True)
        self.loadSubRaw(surface.get_size(), position, string, GL_RGB)

  def loadRaw(self, size, string, format, components):
    """Load a raw image from the given string. 'format' is a constant such as
       GL_RGB or GL_RGBA that can be passed to gluBuild2DMipmaps.
       """
    self.pixelSize = size
    self.size = (1.0, 1.0)
    self.format = format
    self.components = components
    (w, h) = size
    Texture.bind(self)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    if self.useMipmaps:
      gluBuild2DMipmaps(self.glTarget, components, w, h, format, GL_UNSIGNED_BYTE, string)
    else:
      glTexImage2D(self.glTarget, 0, components, w, h, 0, format, GL_UNSIGNED_BYTE, string)

  def loadSubRaw(self, size, position, string, format):
    Texture.bind(self)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexSubImage2D(self.glTarget, 0, position[0], position[1], size[0], size[1], format, GL_UNSIGNED_BYTE, string)

  def loadEmpty(self, size, format):
    self.pixelSize = size
    self.size = (1.0, 1.0)
    self.format = format
    Texture.bind(self)
    glTexImage2D(GL_TEXTURE_2D, 0, format, size[0], size[1], 0,
                 format, GL_UNSIGNED_BYTE, "\x00" * (size[0] * size[1] * 4))

  def setDefaults(self):
    """Set the default OpenGL options for this texture"""
    self.setRepeat()
    self.setFilter()
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

  def setRepeat(self, u=GL_REPEAT, v=GL_REPEAT):
    Texture.bind(self)
    glTexParameteri(self.glTarget, GL_TEXTURE_WRAP_S, u)
    glTexParameteri(self.glTarget, GL_TEXTURE_WRAP_T, v)

  def setFilter(self, min=None, mag=GL_LINEAR):
    Texture.bind(self)
    if min is None:
      if self.useMipmaps:
        min = GL_LINEAR_MIPMAP_LINEAR
      else:
        min = GL_LINEAR
    glTexParameteri(self.glTarget, GL_TEXTURE_MIN_FILTER, min)
    glTexParameteri(self.glTarget, GL_TEXTURE_MAG_FILTER, mag)

  def __del__(self):
    # Queue this texture to be deleted later
    try:
      cleanupQueue.append((glDeleteTextures, [self.texture]))
    except NameError:
      pass

  def bind(self, glTarget = None):
    """Bind this texture to self.glTarget in the current OpenGL context"""
    if not glTarget:
        glTarget = self.glTarget
    glBindTexture(glTarget, self.texture)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, self.texEnv)
#
# Texture atlas
#
TEXTURE_ATLAS_SIZE = 1024

class TextureAtlasFullException(Exception):
  pass

class TextureAtlas(object):
  def __init__(self, size = TEXTURE_ATLAS_SIZE):
    self.texture      = Texture()
    self.cursor       = (0, 0)
    self.rowHeight    = 0
    self.surfaceCount = 0
    self.texture.loadEmpty((size, size), GL_RGBA)

  def add(self, surface, margin = 0):
    w, h = surface.get_size()
    x, y = self.cursor

    w += margin
    h += margin

    if w > self.texture.pixelSize[0] or h > self.texture.pixelSize[1]:
      raise ValueError("Surface is too big to fit into atlas.")

    if x + w >= self.texture.pixelSize[0]:
      x = 0
      y += self.rowHeight
      self.rowHeight = 0

    if y + h >= self.texture.pixelSize[1]:
      Log.debug("Texture atlas %s full after %d surfaces." % (self.texture.pixelSize, self.surfaceCount))
      raise TextureAtlasFullException()

    self.texture.loadSubsurface(surface, position = (x, y), alphaChannel = True)

    self.surfaceCount += 1
    self.rowHeight = max(self.rowHeight, h)
    self.cursor = (x + w, y + h)

    # Return the coordinates for the uploaded texture patch
    w -= margin
    h -= margin
    return  x      / float(self.texture.pixelSize[0]),  y      / float(self.texture.pixelSize[1]), \
           (x + w) / float(self.texture.pixelSize[0]), (y + h) / float(self.texture.pixelSize[1])

  def bind(self):
    self.texture.bind()

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
import Config
import Image
import pygame
import StringIO
import PngImagePlugin
from OpenGL.GL import *
from OpenGL.GLU import *
from Queue import Queue, Empty

Config.define("opengl", "supportfbo", bool, False)

try:
  from glew import *
except ImportError:
  #Log.warn("GLEWpy not found -> Emulating Render to texture functionality.")
  pass

class TextureException(Exception):
  pass

# A queue containing (function, args) pairs that clean up deleted OpenGL handles.
# The functions are called in the main OpenGL thread.
cleanupQueue = Queue()

class Framebuffer:
  fboSupported = None

  def __init__(self, texture, width, height, generateMipmap = False):
    self.emulated       = not self._fboSupported()
    self.size           = (width, height)
    self.colorbuf       = texture
    self.generateMipmap = generateMipmap
    self.fb             = 0
    self.depthbuf       = 0
    self.stencilbuf     = 0
    
    if self.emulated:
      if (width & (width - 1)) or (height & (height - 1)):
        raise TextureException("Only power of two render target textures are supported when frame buffer objects support is missing.")
    else:
      self.fb             = glGenFramebuffersEXT(1)[0]
      self.depthbuf       = glGenRenderbuffersEXT(1)[0]
      self.stencilbuf     = glGenRenderbuffersEXT(1)[0]
      glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, self.fb)
      self._checkError()
      
    glBindTexture(GL_TEXTURE_2D, self.colorbuf)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    # PyOpenGL does not support NULL textures, so we must make a temporary buffer here
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, " " * (width * height * 4))
    self._checkError()
    
    if self.emulated:
      return
    
    glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, self.fb)

    try:
      glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT,
                                GL_COLOR_ATTACHMENT0_EXT,
                                GL_TEXTURE_2D, self.colorbuf, 0)
      self._checkError()
      
      # On current NVIDIA hardware, the stencil buffer must be packed
      # with the depth buffer (GL_NV_packed_depth_stencil) instead of
      # separate binding, so we must check for that extension here
      if glewGetExtension("GL_NV_packed_depth_stencil"):
        GL_DEPTH_STENCIL_EXT = 0x84F9
      
        glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, self.depthbuf)
        glRenderbufferStorageEXT(GL_RENDERBUFFER_EXT,
                                 GL_DEPTH_STENCIL_EXT, width, height)
        glFramebufferRenderbufferEXT(GL_FRAMEBUFFER_EXT,
                                     GL_DEPTH_ATTACHMENT_EXT,
                                     GL_RENDERBUFFER_EXT, self.depthbuf)
        self._checkError()
      else:
        glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, self.depthbuf)
        glRenderbufferStorageEXT(GL_RENDERBUFFER_EXT,
                                 GL_DEPTH_COMPONENT24, width, height)
        glFramebufferRenderbufferEXT(GL_FRAMEBUFFER_EXT,
                                     GL_DEPTH_ATTACHMENT_EXT,
                                     GL_RENDERBUFFER_EXT, self.depthbuf)
        self._checkError()
        glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, self.stencilbuf)
        glRenderbufferStorageEXT(GL_RENDERBUFFER_EXT,
                                 GL_STENCIL_INDEX_EXT, width, height)
        glFramebufferRenderbufferEXT(GL_FRAMEBUFFER_EXT,
                                     GL_STENCIL_ATTACHMENT_EXT,
                                     GL_RENDERBUFFER_EXT, self.stencilbuf)
        self._checkError()
    finally:
      glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0)

  def __del__(self):
    # Queue the buffers to be deleted later
    try:
      cleanupQueue.put((glDeleteBuffers, [3, [self.depthbuf, self.stencilbuf, self.fb]]))
    except NameError:
      pass
      
  def _fboSupported(self):
    if Framebuffer.fboSupported is not None:
      return Framebuffer.fboSupported
    Framebuffer.fboSupported = False
    
    if not Config.get("opengl", "supportfbo"):
      Log.warn("Frame buffer object support disabled in configuration.")
      return False
  
    if not "glewGetExtension" in globals():
      Log.warn("GLEWpy not found, so render to texture functionality disabled.")
      return False

    glewInit()

    if not glewGetExtension("GL_EXT_framebuffer_object"):
      Log.warn("No support for framebuffer objects, so render to texture functionality disabled.")
      return False
      
    if glGetString(GL_VENDOR) == "ATI Technologies Inc.":
      Log.warn("Frame buffer object support disabled until ATI learns to make proper OpenGL drivers (no stencil support).")
      return False
      
    Framebuffer.fboSupported = True
    return True

  def _checkError(self):
    pass
    # No glGetError() anymore...
    #err = glGetError()
    #if (err != GL_NO_ERROR):
    #  raise TextureException(gluErrorString(err))

  def setAsRenderTarget(self):
    if not self.emulated:
      glBindTexture(GL_TEXTURE_2D, 0)
      glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, self.fb)
      self._checkError()

  def resetDefaultRenderTarget(self):
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    if not self.emulated:
      glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0)
      glBindTexture(GL_TEXTURE_2D, self.colorbuf)
      if self.generateMipmap:
        glGenerateMipmapEXT(GL_TEXTURE_2D)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
      else:
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    else:
      glBindTexture(GL_TEXTURE_2D, self.colorbuf)
      glCopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, 0, 0, self.size[0], self.size[1])
      glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
      
class Texture:
  """Represents an OpenGL texture, optionally loaded from disk in any format supported by PIL"""

  def __init__(self, name = None, target = GL_TEXTURE_2D):
    # Delete all pending textures
    try:
      func, args = cleanupQueue.get_nowait()
      func(*args)
    except Empty:
      pass
    
    self.texture = glGenTextures(1)
    self.texEnv = GL_MODULATE
    self.glTarget = target
    self.framebuffer = None

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
      raise TextureException("Unsupported image mode '%s'" % image.mode)

  def prepareRenderTarget(self, width, height, generateMipmap = True):
    self.framebuffer = Framebuffer(self.texture, width, height, generateMipmap)
    self.pixelSize   = (width, height)
    self.size        = (1.0, 1.0)

  def setAsRenderTarget(self):
    assert self.framebuffer
    self.framebuffer.setAsRenderTarget()

  def resetDefaultRenderTarget(self):
    assert self.framebuffer
    self.framebuffer.resetDefaultRenderTarget()

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
    gluBuild2DMipmaps(self.glTarget, components, w, h, format, GL_UNSIGNED_BYTE, string)

  def setDefaults(self):
    """Set the default OpenGL options for this texture"""
    self.setRepeat()
    self.setFilter()
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

  def setRepeat(self, u=GL_REPEAT, v=GL_REPEAT):
    Texture.bind(self)
    glTexParameteri(self.glTarget, GL_TEXTURE_WRAP_S, u)
    glTexParameteri(self.glTarget, GL_TEXTURE_WRAP_T, v)

  def setFilter(self, min=GL_LINEAR_MIPMAP_LINEAR, mag=GL_LINEAR):
    Texture.bind(self)
    glTexParameteri(self.glTarget, GL_TEXTURE_MIN_FILTER, min)
    glTexParameteri(self.glTarget, GL_TEXTURE_MAG_FILTER, mag)

  def __del__(self):
    # Queue this texture to be deleted later
    try:
      cleanupQueue.put((glDeleteTextures, [self.texture]))
    except NameError:
      pass

  def bind(self, glTarget = None):
    """Bind this texture to self.glTarget in the current OpenGL context"""
    if not glTarget:
        glTarget = self.glTarget
    glBindTexture(glTarget, self.texture)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, self.texEnv)

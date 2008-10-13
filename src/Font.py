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

import pygame
from OpenGL.GL import *
import sys

from Texture import Texture

class Font:
  """A texture-mapped font."""
  def __init__(self, fileName, size, bold = False, italic = False, underline = False, outline = True,
               scale = 1.0, reversed = False, systemFont = False, shadow = False):
    pygame.font.init()
    self.size           = size
    self.scale          = scale
    self.glyphCache     = {}
    self.glyphSizeCache = {}
    self.outline        = outline
    self.reversed       = reversed
    self.shadow         = shadow
    # Try loading a system font first if one was requested
    self.font           = None
    if systemFont and sys.platform != "win32":
      try:
        self.font       = pygame.font.SysFont(None, size)
      except:
        pass
    if not self.font:
      self.font         = pygame.font.Font(fileName, size)
    self.font.set_bold(bold)
    self.font.set_italic(italic)
    self.font.set_underline(underline)

  def getStringSize(self, s, scale = 0.002):
    """
    Get the dimensions of a string when rendered with this font.

    @param s:       String
    @param scale:   Scale factor
    @return:        (width, height) tuple
    """
    w = 0
    h = 0
    scale *= self.scale
    for ch in s:
      try:
        s = self.glyphSizeCache[ch]
      except:
        s = self.glyphSizeCache[ch] = self.font.size(ch)
      w += s[0]
      h = max(s[1], h)
    return (w * scale, h * scale)

  def getHeight(self):
    """@return: The height of this font"""
    return self.font.get_height() * self.scale

  def getLineSpacing(self, scale = 0.002):
    """@return: Recommanded line spacing of this font"""
    return self.font.get_linesize() * self.scale * scale
    
  def setCustomGlyph(self, character, texture):
    """
    Replace a character with a texture.

    @param character:   Character to replace
    @param texture:     L{Texture} instance
    """
    texture.setFilter(GL_LINEAR, GL_LINEAR)
    texture.setRepeat(GL_CLAMP, GL_CLAMP)
    self.glyphCache[character]     = texture
    s = .75 * self.getHeight() / float(texture.pixelSize[0])
    self.glyphSizeCache[character] = (texture.pixelSize[0] * s, texture.pixelSize[1] * s)

  def render(self, text, pos = (0, 0), direction = (1, 0, 0), scale = 0.002):
    """
    Draw some text.

    @param text:      Text to draw
    @param pos:       Text coordinate tuple (x, y)
    @param direction: Text direction vector (x, y, z)
    @param scale:     Scale factor
    """
    glEnable(GL_TEXTURE_2D)
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)

    glPushMatrix()
    glTranslatef(pos[0], pos[1], 0)
    
    if self.reversed:
      text = "".join(reversed(text))

    if self.outline:
      glPushAttrib(GL_CURRENT_BIT)
      glPushMatrix()
      glColor4f(0, 0, 0, .25 * glGetDoublev(GL_CURRENT_COLOR)[3])
      for ch in text:
        g = self.getGlyph(ch)
        # evilynux - Fixed bug, self.scaling must not be applied twice!
        w, h = self.getStringSize(ch, scale = scale)
        tw, th = g.size
  
        glVertexPointerf([(0.0, 0.0, 0.0), (w, 0.0, 0.0), (0.0, h, 0.0), (w, h, 0.0)])
        glTexCoordPointerf([(0.0, th), (tw, th), (0.0, 0.0), (tw, 0.0)])
  
        g.bind()
  
        blur = 2 * 0.002
        for offset in [(-.7, -.7), (0, -1), (.7, -.7), (-1, 0), (1, 0), (-.7, .7), (0, 1), (.7, .7)]:
          glPushMatrix()
          glTranslatef( blur * offset[0], blur * offset[1], 0)
          glDrawElementsui(GL_TRIANGLE_STRIP, [0, 1, 2, 3])
          glPopMatrix()

        glTranslatef(w * direction[0],
                     w * direction[1],
                     w * direction[2])

      glPopAttrib()
      glPopMatrix()

    if self.shadow:
      glPushAttrib(GL_CURRENT_BIT)
      glPushMatrix()
      glColor4f(0, 0, 0, 1)
      for ch in text:
        g = self.getGlyph(ch)
        # evilynux - Fixed bug, self.scaling must not be applied twice!
        w, h = self.getStringSize(ch, scale = scale)
        tw, th = g.size
  
        glVertexPointerf([(0.0, 0.0, 0.0), (w, 0.0, 0.0), (0.0, h, 0.0), (w, h, 0.0)])
        glTexCoordPointerf([(0.0, th), (tw, th), (0.0, 0.0), (tw, 0.0)])
  
        g.bind()
  
        glPushMatrix()
        glTranslatef(.0022, .0005, 0)
        glDrawElementsui(GL_TRIANGLE_STRIP, [0, 1, 2, 3])
        glPopMatrix()

        glTranslatef(w * direction[0],
                     w * direction[1],
                     w * direction[2])

      glPopAttrib()
      glPopMatrix()

    for ch in text:
      g = self.getGlyph(ch)
      # evilynux - Fixed bug, self.scaling must not be applied twice!
      w, h = self.getStringSize(ch, scale = scale)
      tw, th = g.size

      glVertexPointerf([(0.0, 0.0, 0.0), (w, 0.0, 0.0), (0.0, h, 0.0), (w, h, 0.0)])
      glTexCoordPointerf([(0.0, th), (tw, th), (0.0, 0.0), (tw, 0.0)])

      g.bind()
      glDrawElementsui(GL_TRIANGLE_STRIP, [0, 1, 2, 3])

      glTranslatef(w * direction[0],
                   w * direction[1],
                   w * direction[2])

    glPopMatrix()

    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_TEXTURE_COORD_ARRAY)
    glDisable(GL_TEXTURE_2D)

  # evilynux
  def loadCache(self):
    """
    Fill in the caches to speedup rendering.
    """
    for ch in "abcdefghijklmnopqrstuvwxyz0123456789":
      try:
        self.glyphCache[ch]
      except:
        self.cacheGlyph(ch)

  # evilynux
  def cacheGlyph(self, ch):
    """
    Add character and size to glyph caches

    @param ch: Character
    @return:   Glyph instance
    """
    # Font size
    self.glyphSizeCache[ch] = self.font.size(ch)
    # Font texture
    s = self.font.render(ch, True, (255, 255, 255))
    t = Texture()
    t.setFilter(GL_LINEAR, GL_LINEAR)
    t.setRepeat(GL_CLAMP, GL_CLAMP)
    t.loadSurface(s, alphaChannel = True)
    del s
    self.glyphCache[ch] = t
    return t

  def getGlyph(self, ch):
    """
    Get the L{Texture} for a given character.

    @param ch:    Character
    @return:      L{Texture} instance
    """
    try:
      return self.glyphCache[ch]
    except KeyError:
      return self.cacheGlyph(ch)


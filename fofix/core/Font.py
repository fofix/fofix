#####################################################################
# -*- coding: utf-8 -*-                                             #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
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
from __future__ import with_statement

import sys

from OpenGL.GL import *
import numpy as np
import pygame

from fofix.core import cmgl
from fofix.core.Texture import Texture
from fofix.core.constants import *

DEFAULT_SCALE = 0.002
SCREEN_BOTTOM = .75


class CacheElement(object):
    def __init__(self, content):
        self.content = content
        self.accessed()

    def accessed(self):
        self.lastUse = pygame.time.get_ticks()


class Cache(object):
    def __init__(self, maxCount=1024):
        self.elements = {}
        self.maxCount = maxCount

    def get(self, key):
        e = self.elements[key]
        e.accessed()
        return e.content

    def add(self, key, element):
        self.elements[key] = CacheElement(element)
        if len(self.elements) > self.maxCount:
            keys = self.elements.keys()
            keys.sort(key=lambda e: -self.elements[e].lastUse)
            for k in keys[self.maxCount:]:
                del self.elements[k]


class Font:
    """A texture-mapped font."""

    def __init__(self, fileName, size, bold=False, italic=False, underline=False, outline=True,
                 scale=1.0, reversed=False, systemFont=False, shadow=False, shadowoffsetx=.0022, shadowoffsety=.0005, aspectRatio=(4.0/3.0)):
        pygame.font.init()
        self.size = size
        self.scale = scale
        self.outline = outline
        self.reversed = reversed
        self.shadow = shadow
        self.shadowoffsetx = shadowoffsetx
        self.shadowoffsety = shadowoffsety
        self.aspectRatioFactor = (4.0 / 3.0) / aspectRatio

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
        self.stringsCache = Cache(256)
        self.square_prim = np.zeros((4, 2), dtype=np.float32)
        self.square_tex = np.zeros((4, 2), dtype=np.float32)

    def getStringSize(self, s, scale=DEFAULT_SCALE):
        """
        Get the dimensions of a string when rendered with this font.

        :param s: String
        :param scale: Scale factor
        :return: (width, height) tuple
        """
        scale *= self.scale

        try:
            t, w, h = self.stringsCache.get(s)
        except KeyError:
            w, h = self.font.size(s)

        return (w * scale * self.aspectRatioFactor, h * scale)

    def loadCache(self):
        pass

    def scaleText(self, text, maxwidth, scale=DEFAULT_SCALE):
        """
        Return scaling factor needed to fit text within maxwidth

        :param text: the text to scale
        :param maxwidth: maximum width
        :param scale: the scale
        :return: the new scale factor
        """
        w, h = self.getStringSize(text, scale)
        if w > maxwidth:
            scale *= maxwidth / w
        return scale

    def getHeight(self):
        """Return the height of this font"""
        return self.font.get_height() * self.scale

    def getLineSpacing(self, scale=DEFAULT_SCALE):
        """Return recommended line spacing of this font"""
        return self.font.get_linesize() * self.scale * scale

    def getFontAscent(self, scale=DEFAULT_SCALE):
        """
        Return the height in pixels for the font ascent.
        The ascent is the number of pixels from the font baseline to the top of the font.
        The goal is to find the centerline of the text.
        """
        return self.font.get_ascent() * self.scale * scale

    def getFontDescent(self, scale=DEFAULT_SCALE):
        """
        Return the height in pixels for the font descent.
        The descent is the number of pixels from the font baseline to the bottom of the font.
        The goal is to find the centerline of the text.
        """
        return self.font.get_descent() * self.scale * scale

    def setCustomGlyph(self, character, texture):
        """
        Replace a character with a texture.

        @param character:   Character to replace
        @param texture:     L{Texture} instance
        """
        pass

    def drawSquare(self, w, h, tw, th):
        """
        New drawing relaying only on pygame.font.render
        Use arrays to increase performance

        :param w: width
        :param h: height
        :param tw: texture width
        :param th: texture height
        """
        self.square_prim[1, 0] = self.square_prim[3, 0] = w
        self.square_prim[2, 1] = self.square_prim[3, 1] = h
        self.square_tex[0, 1] = self.square_tex[1, 1] = th
        self.square_tex[1, 0] = self.square_tex[3, 0] = tw
        cmgl.drawArrays(GL_TRIANGLE_STRIP, vertices=self.square_prim, texcoords=self.square_tex)

    def render(self, text, pos=(0, 0), rotate=0, scale=DEFAULT_SCALE, shadowoffset=(.0022, .0005), align=LEFT, new=False, shadow=False, outline=False, shadowOpacity=1.0):
        """
        Draw some text.

        :param text: Text to draw
        :param pos: Text coordinate tuple (x, y)
        :param rotate: Angle to rotate text, in degrees
        :param scale: Scale factor
        :param shadowoffset: Shadow offset (x, y)
        :param align: how to align the text
        :param shadow: if there will be shadow (default: False)
        :param outline: if there will be outline (default: False)
        :param shadowOpacity: opacity of the shadow (default: 1.0)
        """
        if not text:
            return

        try:
            t, w, h = self.stringsCache.get(text)
        except KeyError:
            s = self.font.render(text, True, (255, 255, 255))
            t = Texture()
            t.setFilter(GL_LINEAR, GL_LINEAR)
            t.setRepeat(GL_CLAMP, GL_CLAMP)
            t.loadSurface(s, alphaChannel=True)
            del s
            w, h = self.font.size(text)
            self.stringsCache.add(text, (t, w, h))

        x, y = pos
        scale *= self.scale
        w, h = w * scale * self.aspectRatioFactor, h * scale
        if align == CENTER:
            x -= (w / 2)
        elif align == RIGHT:
            x -= w
        y -= (h / 2)

        tw, th = t.size
        glEnable(GL_TEXTURE_2D)
        with cmgl.PushedMatrix():
            if rotate:
                if not isinstance(rotate, tuple):
                    glRotatef(rotate, 0, 0, 1.0)
                else:
                    glRotatef(0, *rotate)
            glTranslatef(x, y, 0)
            t.bind()

            # Outline
            if self.outline or outline:
                with cmgl.PushedAttrib(GL_CURRENT_BIT):
                    glColor4f(0, 0, 0, .25 * glGetDoublev(GL_CURRENT_COLOR)[3])

                    blur = 2 * DEFAULT_SCALE
                    for offset in [(-.7, -.7), (0, -1), (.7, -.7), (-1, 0),
                                   (1, 0), (-.7, .7), (0, 1), (.7, .7)]:
                        with cmgl.PushedMatrix():
                            glTranslatef(blur * offset[0], blur * offset[1], 0)
                            self.drawSquare(w, h, tw, th)

            # Shadow
            if self.shadow or shadow:
                with cmgl.PushedAttrib(GL_CURRENT_BIT):
                    glColor4f(0, 0, 0, glGetDoublev(GL_CURRENT_COLOR)[3] * shadowOpacity)
                    with cmgl.PushedMatrix():
                        glTranslatef(shadowoffset[0], shadowoffset[1], 0)
                        self.drawSquare(w, h, tw, th)

            self.drawSquare(w,h,tw,th)

        glDisable(GL_TEXTURE_2D)

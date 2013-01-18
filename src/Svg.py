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
from __future__ import with_statement
from OpenGL.GL import *

import numpy as np
import cmgl

import Log
from Texture import Texture
from PIL import Image
from constants import *

#stump: the last few stubs of DummyAmanith.py are inlined here since this
# is the only place in the whole program that uses it now that we've pruned
# the dead SVG code.
class SvgContext(object):
    def __init__(self, geometry):
        self.geometry = geometry
        self.setGeometry(geometry)
        self.setProjection(geometry)
        glMatrixMode(GL_MODELVIEW)

    def setGeometry(self, geometry = None):
        glViewport(geometry[0], geometry[1], geometry[2], geometry[3])
        glScalef(geometry[2] / SCREEN_WIDTH, geometry[3] / SCREEN_HEIGHT, 1.0)

    def setProjection(self, geometry = None):
        geometry = geometry or self.geometry
        with cmgl.MatrixMode(GL_PROJECTION):
            glLoadIdentity()
            glOrtho(geometry[0], geometry[0] + geometry[2], geometry[1], geometry[1] + geometry[3], -100, 100)
        self.geometry = geometry

    def clear(self, r = 0, g = 0, b = 0, a = 0):
        glDepthMask(1)
        glEnable(GL_COLOR_MATERIAL)
        glClearColor(r, g, b, a)
        glClear(GL_COLOR_BUFFER_BIT | GL_STENCIL_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

class ImgDrawing(object):
    VTX_ARRAY = np.array([[0.0, 1.0], [1.0, 1.0], [1.0, 0.0], [0.0, 0.0]], dtype=np.float32) #hard-coded quad for drawing textures onto

    def drawImage(image, scale = (1.0, -1.0), coord = (0, 0), rot = 0, \
                  color = (1,1,1,1), rect = (0,1,0,1), stretched = 0, fit = 0, \
                  alignment = CENTER, valignment = CENTER):
        """
        Draws the image/surface to screen
        """

        if not isinstance(image, ImgDrawing):
            return False

        image.setRect(rect)
        image.setScale(scale[0], scale[1], stretched)
        image.setPosition(coord[0], coord[1], fit)
        image.setAlignment(alignment)
        image.setVAlignment(valignment)
        image.setAngle(rot)
        image.setColor(color)
        image.draw()

        return True

    def __init__(self, context, ImgData):
        self.ImgData = None
        self.texture = None
        self.context = context
        self.cache = None
        self.filename = ImgData

        # Detect the type of data passed in
        if isinstance(ImgData, file):
            self.ImgData = ImgData.read()
        elif isinstance(ImgData, basestring):
            self.texture = Texture(ImgData)
        elif isinstance(ImgData, Image.Image): #stump: let a PIL image be passed in
            self.texture = Texture()
            self.texture.loadImage(ImgData)

        # Make sure we have a valid texture
        if not self.texture:
            if isinstance(ImgData, basestring):
                e = "Unable to load texture for %s." % ImgData
            else:
                e = "Unable to load texture for SVG file."
            Log.error(e)
            raise RuntimeError(e)

        self.pixelSize = self.texture.pixelSize #the size of the image in pixels (from texture)
        self.position = [0.0,0.0]               #position of the image in the viewport
        self.scale    = [1.0,1.0]               #percentage scaling
        self.angle    = 0                       #angle of rotation (degrees)
        self.color    = (1.0,1.0,1.0,1.0)       #glColor rgba
        self.rect     = (0,1,0,1)               #texture mapping coordinates
        self.shift    = -.5                     #horizontal alignment
        self.vshift   = -.5                     #vertical alignment

        self.path = self.texture.name           #path of the image file

        self.texArray = np.zeros((4,2), dtype=np.float32)

        self.createTex()

    def createTex(self):
        tA = self.texArray
        rect = self.rect

        #topLeft, topRight, bottomRight, bottomLeft
        tA[0,0] = rect[0]; tA[0,1] = rect[3]
        tA[1,0] = rect[1]; tA[1,1] = rect[3]
        tA[2,0] = rect[1]; tA[2,1] = rect[2]
        tA[3,0] = rect[0]; tA[3,1] = rect[2]

    def width1(self):
        """
        @return the width of the texture in pixels
        """
        width = self.pixelSize[0]
        if width:
            return width
        else:
            return 0

    def height1(self):
        """
        @return the height of the texture in pixels
        """
        height = self.pixelSize[1]
        if height is not None:
            return height
        else:
            return 0

    def widthf(self, pixelw):
        """
        @param pixelw - a width in pixels
        @return the scaled ratio of the pixelw divided by the pixel width of the texture
        """
        width = self.pixelSize[0]
        if width is not null:
            wfactor = pixelw/width
            return wfactor
        else:
            return 0

    def setPosition(self, x, y, fit = 0):
        """
        Sets position of this image on screen 

        @param fit:          Adjusts the texture so the coordinate for the y-axis placement can be
                             on the top side (1), bottom side (2), or center point (any other value) of the image
        """
        if fit == 0: #y is center
            pass
        elif fit == 1: #y is on top (not center)
            y = y - ((self.pixelSize[1] * abs(self.scale[1]))*.5*(self.context.geometry[3]/SCREEN_HEIGHT))
        elif fit == 2: #y is on bottom
            y = y + ((self.pixelSize[1] * abs(self.scale[1]))*.5*(self.context.geometry[3]/SCREEN_HEIGHT))

        self.position = [x,y]

    def setScale(self, width, height, stretched = 0):
        """
        @param stretched:    Stretches the image in one of 5 ways according to following passed values
                                 1) fits it to the width of the viewport
                                 2) fits it to the height of the viewport
                                11) fits it to the width of the viewport and scales the height while keeping the aspect ratio
                                12) fits it to the heigh of the viewport and scales the width while keeping the aspect ratio
                                 0) stretches it so it fits the whole viewport
        """
        if stretched == 0: #do nothing
            pass
        elif stretched == 1: # fit to width
            width  = width  / self.pixelSize[0] * self.context.geometry[2]
        elif stretched == 2: # fit to height
            height = height / self.pixelSize[1] * self.context.geometry[3]
        elif stretched == 11: # fit to width and keep ratio
            width  = width  / self.pixelSize[0] * self.context.geometry[2]
            height = height / self.pixelSize[0] * self.context.geometry[2]
        elif stretched == 12: # fit to height and keep ratio
            width  = width  / self.pixelSize[1] * self.context.geometry[3]
            height = height / self.pixelSize[1] * self.context.geometry[3]
        elif not stretched == 0: # fit to screen
            width  = width  / self.pixelSize[0] * self.context.geometry[2]
            height = height / self.pixelSize[1] * self.context.geometry[3]

        self.scale = [width, height]

    def setAngle(self, angle):
        self.angle = angle

    def setRect(self, rect):
        """
        @param rect:         The surface rectangle, this is used for cropping the texture
        """
        if not rect == self.rect:
            self.rect = rect
            self.createTex()

    def setAlignment(self, alignment):
        """
        @param alignment:    Adjusts the texture so the coordinate for x-axis placement can either be
                             on the left side (0), center point (1), or right(2) side of the image
        """
        if alignment == CENTER:#center
            self.shift = -.5
        elif alignment == LEFT:  #left
            self.shift = 0
        elif alignment == RIGHT:#right
            self.shift = -1.0

    def setVAlignment(self, alignment):
        """
        @param valignment:   Adjusts the texture so the coordinate for y-axis placement can either be
                             on the bottom side (0), center point (1), or top(2) side of the image
        """
        if alignment == CENTER:#center
            self.vshift = -.5
        if alignment == TOP:#bottom
            self.vshift = 0
        elif alignment == BOTTOM:#top
            self.vshift = -1.0

    def setColor(self, color):
        if len(color) == 3:
            color = (color[0], color[1], color[2], 1.0)
        self.color = color

    def draw(self):
        with cmgl.PushedSpecificMatrix(GL_TEXTURE):
            with cmgl.PushedSpecificMatrix(GL_PROJECTION):

                with cmgl.MatrixMode(GL_PROJECTION):
                    self.context.setProjection()

                with cmgl.PushedMatrix():
                    glLoadIdentity()

                    glTranslate(self.position[0], self.position[1], 0.0)
                    glRotatef(-self.angle, 0, 0, 1)
                    glScalef(self.scale[0], self.scale[1], 1.0)
                    glScalef(self.pixelSize[0], self.pixelSize[1], 1)
                    glTranslatef(self.shift, self.vshift, 0)

                    glColor4f(*self.color)

                    glEnable(GL_TEXTURE_2D)
                    self.texture.bind()
                    cmgl.drawArrays(GL_QUADS, vertices=ImgDrawing.VTX_ARRAY, texcoords=self.texArray)
                    glDisable(GL_TEXTURE_2D)

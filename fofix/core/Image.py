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

import numpy as np
from PIL import Image
from OpenGL.GL import *

from fofix.core.Texture import Texture
from fofix.core.constants import *
from fofix.core import Log
from fofix.core import cmgl

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

def drawImage(image, scale = (1.0, -1.0), coord = (0, 0), rot = 0, \
                  color = (1,1,1,1), rect = (0,1,0,1), stretched = 0, fit = CENTER, \
                  alignment = CENTER, valignment = CENTER):
        """
        Draws the image/surface to screen

        @param image:        The openGL surface
        @param scale:        Scale factor (between 0.0 and 1.0, second value must be negative due to texture flipping)
        @param coord:        Where the image will be translated to on the screen
        @param rot:          How many degrees it will be rotated
        @param color:        The color of the image
                                 (values are between 0.0 and 1.0)
                                 (can have 3 values or 4, if 3 are given the alpha is automatically set to 1.0)
        @param rect:         The surface rectangle, this is used for cropping the texture

                             Any other values will have the image maintain its size passed by scale
        @param alignment:    Adjusts the texture so the coordinate for x-axis placement can either be
                             on the left side (0), center point (1), or right(2) side of the image
        @param valignment:   Adjusts the texture so the coordinate for y-axis placement can either be
                             on the bottom side (0), center point (1), or top(2) side of the image
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

#blazingamer
def draw3Dtex(image, vertex, texcoord, coord = None, scale = None, rot = None, color = (1,1,1), multiples = False, alpha = False, depth = False, vertscale = 0):
    '''
    Simplifies tex rendering

    @param image: self.xxx - tells the system which image/resource should be mapped to the plane
    @param vertex: (Left, Top, Right, Bottom) - sets the points that define where the plane will be drawn
    @param texcoord: (Left, Top, Right, Bottom) - sets where the texture should be drawn on the plane
    @param coord: (x,y,z) - where on the screen the plane will be rendered within the 3d field
    @param scale: (x,y,z) - scales an glplane how far in each direction

    @param rot: (degrees, x-axis, y-axis, z-axis)
    a digit in the axis is how many times you want to rotate degrees around that axis

    @param color: (r,g,b) - sets the color of the image when rendered
    0 = No Color, 1 = Full color

    @param multiples: True/False
    defines whether or not there should be multiples of the plane drawn at the same time
    only really used with the rendering of the notes, keys, and flames

    @param alpha: True/False - defines whether or not the image should have black turned into transparent
    only really used with hitglows and flames

    @param depth: True/False - sets the depth by which the object is rendered
    only really used by keys and notes

    @param vertscale: # - changes the yscale when setting vertex points
    only really used by notes
    '''


    if not isinstance(image, ImgDrawing):
        return

    if alpha:
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

    if len(color) == 4:
        col_array  = np.array([[color[0],color[1],color[2], color[3]],
                            [color[0],color[1],color[2], color[3]],
                            [color[0],color[1],color[2], color[3]],
                            [color[0],color[1],color[2], color[3]]], dtype=np.float32)
    else:
        col_array  = np.array([[color[0],color[1],color[2], 1],
                            [color[0],color[1],color[2], 1],
                            [color[0],color[1],color[2], 1],
                            [color[0],color[1],color[2], 1]], dtype=np.float32)

    glEnable(GL_TEXTURE_2D)
    image.texture.bind()

    if multiples:
        glPushMatrix()

    if coord is not None:
        glTranslate(coord[0], coord[1], coord[2])
    if rot is not None:
        glRotate(rot[0], rot[1], rot[2], rot[3])
    if scale is not None:
        glScalef(scale[0], scale[1], scale[2])

    if depth:
        glDepthMask(1)

    if not isinstance(vertex, np.ndarray):
        vertex = np.array(
          [[ vertex[0],  vertscale, vertex[1]],
            [ vertex[2],  vertscale, vertex[1]],
            [ vertex[0], -vertscale, vertex[3]],
            [ vertex[2], -vertscale, vertex[3]]], dtype=np.float32)

    if not isinstance(texcoord, np.ndarray):
        texcoord = np.array(
          [[texcoord[0], texcoord[1]],
            [texcoord[2], texcoord[1]],
            [texcoord[0], texcoord[3]],
            [texcoord[2], texcoord[3]]], dtype=np.float32)

    cmgl.drawArrays(GL_TRIANGLE_STRIP, vertices=vertex, colors=col_array, texcoords=texcoord)

    if depth:
        glDepthMask(0)

    if multiples:
        glPopMatrix()

    glDisable(GL_TEXTURE_2D)

    if alpha:
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

class ImgDrawing(object):
    VTX_ARRAY = np.array([[0.0, 1.0], [1.0, 1.0], [1.0, 0.0], [0.0, 0.0]], dtype=np.float32) #hard-coded quad for drawing textures onto

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
        if width is not None:
            wfactor = pixelw/width
            return wfactor
        else:
            return 0

    def setPosition(self, x, y, fit = CENTER):
        """
        Sets position of this image on screen

        @param fit:          Adjusts the texture so the coordinate for the y-axis placement can be
                             on the top side (1), bottom side (2), or center point (any other value) of the image
        """
        if fit == CENTER: #y is center
            pass
        elif fit == TOP: #y is on top (not center)
            y = y - ((self.pixelSize[1] * abs(self.scale[1]))*.5*(self.context.geometry[3]/SCREEN_HEIGHT))
        elif fit == BOTTOM: #y is on bottom
            y = y + ((self.pixelSize[1] * abs(self.scale[1]))*.5*(self.context.geometry[3]/SCREEN_HEIGHT))

        self.position = [x,y]

    def setScale(self, width, height, stretched = 0):
        """
        @param stretched:    Bitmask stretching the image according to the following values
                                 0) does not stretch the image
                                 1) fits it to the width of the viewport
                                 2) fits it to the height of the viewport
                                 3) stretches it so it fits the viewport
                                 4) preserves the aspect ratio while stretching
        """
        if stretched & FULL_SCREEN: # FULL_SCREEN is FIT_WIDTH | FIT_HEIGHT
            xStretch = 1
            yStretch = 1
            if stretched & FIT_WIDTH:
                xStretch = float(self.context.geometry[2]) / self.pixelSize[0]
            if stretched & FIT_HEIGHT:
                yStretch = float(self.context.geometry[3]) / self.pixelSize[1]
            if stretched & KEEP_ASPECT:
                if stretched & FULL_SCREEN == FULL_SCREEN: #Note that on FULL_SCREEN | KEEP_ASPECT we will scale to the larger and clip.
                    if xStretch > yStretch:
                       yStretch = xStretch
                    else:
                       xStretch = yStretch
                else:
                    if stretched & FIT_WIDTH:
                        yStretch = xStretch
                    else:
                        xStretch = yStretch
            width *= xStretch
            height *= yStretch

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

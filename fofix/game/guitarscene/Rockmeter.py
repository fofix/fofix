#####################################################################
# -*- coding: utf-8 -*-                                             #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2009 Blazingamer <n_hydock@comcast.net>             #
#                                                                   #
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
import __future__

import imp
import locale
import logging
import math
import os

from PIL import Image, ImageDraw
import OpenGL.GL as gl

from fofix.core import Version
from fofix.core import cmgl
from fofix.core.Image import ImgDrawing
from fofix.core.Image import drawImage
from fofix.core.Config import MyConfigParser
from fofix.core.Theme import halign, valign
from fofix.core.Theme import hexToColor
from fofix.core.constants import *


FUTURE_DIVISION = __future__.division.compiler_flag
log = logging.getLogger(__name__)

#these are the variables for setting the alignment of text and images
#when setting them up in the rockmeter.ini you do not have
#to put it in all caps, the code will take care of that
#for you; however you do have to spell them right or it will
#give you an error.

#by making these global for the class, all layers that rely on
#these numbers will no longer have to have them be independent per
#instance of the layer.  This also makes it easier to work with the
#variables in the rockmeter.ini for you no longer have to use self
#to refer to theme, instead it has a more friendly and logical setup.
player = None           #instrument object that represents the player
playerNum = 0           #the player number
playerName = ""         #the player's name
part = "Guitar"         #the player's part/instrument

score = 0               #player's score
streak = 0              #player's streak
streakMax = 0           #amount of notes it takes to hit make multiplier
power = 0               #star power fill amount
stars = 0               #how many stars earned
partialStars = 0        #percentage of the current star earned
rock = 0                #rock meter fill amount
coop_rock = 0           #coop rock meter fill amount
multiplier = 0          #player's multiplier
bassgroove = False      #if a player is a bass guitar and their streak is over 30, they enter bass groove, track this
boost = False           #keeps track if a player is boosting their multiplier (star power/overdrive activated)

minutes = 0             #how many minutes into the song it is
seconds = 0             #how many seconds into the song it is (0-59)
minutesCountdown = 1    #how many minutes left
secondsCountdown = 1    #how many seconds left
songLength = 1          #length of the song (milliseconds)
minutesSongLength = 0   #length of the song in minutes
secondsSongLength = 0   #length of the song in seconds (0-59)
position = 0            #millisecond position in the song
countdownPosition = 1   #milliseconds left
progress = 0.0          #this gives a percentage (between 0 and 1)
                        # of how far the song has played

vpc = [640.0, 480.0]    #viewport's constant size, these variables determine how
                        #things are placed on screen in relation to pixel coordinates

_minFPS = 10            #minimum frame limit for effects that allow the theme maker to set
                        #time in milliseconds


class ConfigGetMixin(object):
    """
    Functions for getting config values, optionally as compiled code objects
    ready to eval().
    """
    def __init__(self):
        self.config = None
        self.section = None

    def get(self, value, type=str, default=None):
        if self.config.has_option(self.section, value):
            return type(self.config.get(self.section, value).strip())
        return default

    def getexpr(self, value, default=None):
        if self.config.has_option(self.section, value):
            expr = self.config.get(self.section, value)
            return compile(expr, '<string>', 'eval', FUTURE_DIVISION)
        return compile(default, '<string>', 'eval', FUTURE_DIVISION)

    def getexprs(self, value, default=None, separator='|'):
        if self.config.has_option(self.section, value):
            exprs = [e.strip() for e in self.config.get(self.section, value).split(separator)]
            return [compile(expr, '<string>', 'eval', FUTURE_DIVISION) for expr in exprs]
        return [compile(expr, '<string>', 'eval', FUTURE_DIVISION) for expr in default.split(separator)]


class Layer(ConfigGetMixin):
    """
    A graphical rockmeter layer. This is the base template for all rockmeter
    layer types.
    """

    def __init__(self, stage, section):
        """
        :param stage: the rockmeter stage
        :param section: the section of rockmeter.ini involving this layer
        """
        super(Layer, self).__init__()

        # init vars
        self.stage       = stage  # the rockmeter
        self.engine      = stage.engine  # the game engine
        self.config      = stage.config  # the rockmeter.ini
        self.section     = section  # the section of the rockmeter.ini involving this layer

        self.xposexpr    = self.getexpr("xpos", "0.0")
        self.yposexpr    = self.getexpr("ypos", "0.0")
        self.position    = [0.0, 0.0]       # where on the screen to draw the layer

        self.angleexpr   = self.getexpr("angle", "0.0")
        self.angle       = 0.0              # angle to rotate the layer (in degrees)

        self.xscaleexpr  = self.getexpr("xscale", "1.0")
        self.yscaleexpr  = self.getexpr("yscale", "1.0")
        self.scale       = [1.0, 1.0]       # how much to scale it by (width, height from 0.0 - 1.0)

        # init color vars
        if self.config.has_option(section, "color"):
            # color of the image (#FFFFFF is white on text, on images it is full color)
            self.color = list(hexToColor(self.get("color", str, "#FFFFFF")))
            if len(self.color) == 3:
                self.color.append(1.0)
            self.r, self.g, self.b, self.a = [str(c) for c in self.color]
        else:
            self.r = self.getexpr("r", "1.0")
            self.g = self.getexpr("g", "1.0")
            self.b = self.getexpr("b", "1.0")
            self.a = self.getexpr("a", "1.0")
            self.color = [1.0, 1.0, 1.0, 1.0]

        self.shared = False  # determines if the element is shared between players in multiplayer modes
        self.condition = True  # when should the image be shown (by default it will always be shown)

        # alignment of the image (horizontal)
        self.alignExpr = self.get("alignment", str, "center")
        self.alignment = CENTER

        # alignment of the image (vertical)
        self.valignExpr = self.get("valignment", str, "middle")
        self.valignment = MIDDLE

        # makes sure to properly scale/position the images in pixels instead of percent
        self.inPixels = self.get("inPixels", str, "").split("|")

        self.effects = []  # various effects associated with the layer

    def boardWidth(self, x):
        """
        Calculates the board's width at a certain position

        :param x: position
        :type x: float
        :return: a value not in pixels
        """
        self.engine.view.setViewport(1, 0)
        wFull, hFull = self.engine.view.geometry[2:4]
        scaleCoef = (0.6 + 0.4 * self.stage.scene.numberOfGuitars) * 1.256 * hFull / wFull
        return player.boardWidth / math.sqrt((self.stage.scene.camera.origin[1] + x)**2 + ((self.stage.scene.camera.origin[2] + x) - 0.5)**2) * scaleCoef

    def updateLayer(self, playerNum):
        """ Update vars during the rendering process.

        :param playerNum: the id of the player
        :type playerNum: int
        """
        # position
        self.position = [float(eval(self.xposexpr)), float(eval(self.yposexpr))]
        self.angle = float(eval(self.angleexpr))
        self.scale = [float(eval(self.xscaleexpr)), float(eval(self.yscaleexpr))]

        # color
        self.color = [float(eval(self.r)), float(eval(self.g)),
                      float(eval(self.b)), float(eval(self.a))]
        # makes sure color has an alpha value to consider
        if len(self.color) == 3:
            self.color.append(1.0)

        # alignment
        self.alignment = halign(self.alignExpr)
        self.valignment = valign(self.valignExpr)

    def render(self, visibility, playerNum):
        """ Handle the final step of rendering the image. """
        pass


class ImageLayer(Layer):
    """ A graphical stage layer that is used to render the rockmeter. """

    def __init__(self, stage, section, drawing):
        """
        :param drawing: the filename of the image to draw
        """
        super(ImageLayer, self).__init__(stage, section)

        # these are the images that are drawn when the layer is visible
        self.drawing = self.engine.loadImgDrawing(self, None, drawing)
        self.rectexpr = self.getexpr("rect", "(0.0,1.0,0.0,1.0)")
        # how much of the image do you want rendered
        # (left, right, top, bottom)
        self.rect = [0.0, 1.0, 0.0, 1.0]

    def updateLayer(self, playerNum):
        super(ImageLayer, self).updateLayer(playerNum)

        # don't try to update an image layer if the texture doesn't even exist
        if not self.drawing:
            return

        w, h, = self.engine.view.geometry[2:4]
        texture = self.drawing
        self.rect = [float(i) for i in eval(self.rectexpr)]

        #
        # update the scale
        #
        # all of this has to be repeated instead of using the base method
        # because now things can be calculated in relation to the image's properties
        scale = self.scale
        scale[0] *= (self.rect[1] - self.rect[0])
        scale[1] *= (self.rect[3] - self.rect[2])

        # this allows you to scale images in relation to pixels instead
        # of percentage of the size of the image.
        if "xscale" in self.inPixels:
            scale[0] /= texture.pixelSize[0]
        if "yscale" in self.inPixels:
            scale[1] /= texture.pixelSize[1]

        scale[1] *= -1
        scale[0] *= w / vpc[0]
        scale[1] *= h / vpc[1]
        self.scale = scale

        #
        # update the position
        #
        if "xpos" in self.inPixels:
            self.position[0] *= w / vpc[0]
        else:
            self.position[0] *= w

        if "ypos" in self.inPixels:
            self.position[1] *= h / vpc[1]
        else:
            self.position[1] *= h

    def render(self, visibility, playerNum):
        super(ImageLayer, self).render(visibility, playerNum)

        # don't try to render an image layer if the texture doesn't even exist
        if not self.drawing:
            return

        # get vars
        coord = self.position
        scale = self.scale
        rot = self.angle
        color = self.color
        alignment = self.alignment
        valignment = self.valignment
        drawing = self.drawing
        rect = self.rect

        # render the image
        if bool(eval(self.condition)):
            drawImage(drawing, scale, coord, rot, color, rect, alignment=alignment, valignment=valignment)


class FontLayer(Layer):
    """ Defines layers that are just font instead of images """

    def __init__(self, stage, section, font):
        """
        :param font: the font to use
        """
        super(FontLayer, self).__init__(stage, section)

        self.font        = self.engine.data.fontDict[font]
        self.text        = ""                                       # the text that will be rendered to screen
        self.textexpr    = self.getexpr("text", "''")               # the text from the ini that will be evalutated
        self.replace     = [r.strip() for r in self.get("replace", str, "_").split("_")[:2]]
                                                                    # replace character a character in the string with this
        self.alignment   = halign(self.get("alignment", str, "LEFT"), 'left')
                                                                    # alignment of the text
        self.useComma    = self.get("useComma", bool, False)        # use commas when drawing numbers
        self.shadow      = self.get("shadow",   bool, False)        # show a shadow on the text
        self.outline     = self.get("outline",  bool, False)        # give the text an outline

        self.shadowOpacity = self.get("shadowOpacity", float, 1.0)  # the opacity of the shadow on the text

    def updateLayer(self, playerNum):
        super(FontLayer, self).updateLayer(playerNum)

        #
        # update the text
        #
        text = eval(self.textexpr)

        if self.useComma:
            text = locale.format("%d", text, grouping=True)
        else:
            text = str(text)

        text = text.replace(self.replace[0], self.replace[1])
        wid, hgt = self.font.getStringSize(str(text))
        self.text = text

        #
        # update the position
        #
        if "xpos" in self.inPixels:
            self.position[0] /= vpc[0]
        if "ypos" in self.inPixels:
            self.position[1] /= vpc[1]

        # the viewport code for rendering for is a little awkward
        # instead of the bottom edge being at 1.0 it is at .75
        # by doing this people can use conventional positioning
        # while the code self adjusts the values
        self.position[1] *= .75
        # not only that but it's upside down
        self.position[1] = .75 - self.position[1]

    def render(self, visibility, playerNum):
        position = self.position
        alignment = self.alignment
        color = self.color

        # render the text
        if bool(eval(self.condition)):
            gl.glPushMatrix()
            gl.glColor4f(*color)
            self.font.render(self.text, position, align=alignment, shadow=self.shadow, outline=self.outline, shadowOpacity=self.shadowOpacity)
            gl.glPopMatrix()


class CircleLayer(ImageLayer):
    """ A layer that is shaped like a pie-slice/circle instead of a rectangle """

    def __init__(self, stage, section, drawing):
        super(CircleLayer, self).__init__(stage, section, drawing)

        # this number (between 0 and 1) determines how much
        # of the circle should be filled (0 to 360 degrees)
        self.ratioexpr = self.getexpr("ratio", "1")
        self.ratio     = eval(self.ratioexpr)

        # don't try to create the circle layer if the texture doesn't even exist
        if self.drawing:
            self.createMask(drawing)

    def createMask(self, drawing):
        """ Creates the overlay mask """

        # these determine the size of the PIL pie-slice
        self.centerX   = self.drawing.width1() / 2
        self.centerY   = self.drawing.height1() / 2
        self.inRadius  = 0
        self.outRadius = self.drawing.width1() / 2

        # generates all the images needed for the circle
        self.drawnOverlays = {}
        baseFillImageSize = self.drawing.pixelSize
        for degrees in range(0, 361, 5):
            image = Image.open(self.drawing.path)
            mask = Image.new('RGBA', baseFillImageSize)
            overlay = Image.new('RGBA', baseFillImageSize)
            draw = ImageDraw.Draw(mask)
            draw.pieslice((self.centerX-self.outRadius, self.centerY-self.outRadius,
                           self.centerX+self.outRadius, self.centerY+self.outRadius),
                           -90, degrees-90, outline=(255, 255, 255, 255), fill=(255, 255, 255, 255))
            draw.ellipse((self.centerX-self.inRadius, self.centerY-self.inRadius,
                          self.centerX+self.inRadius, self.centerY+self.inRadius),
                          outline=(0, 0, 0, 0), fill=(0, 0, 0, 0))
            r, g, b, a = mask.split()
            overlay.paste(image, mask=a)
            dispOverlay = ImgDrawing(self.engine.data.svg, overlay)
            self.drawnOverlays[degrees] = dispOverlay

    def updateLayer(self, playerNum):
        super(CircleLayer, self).updateLayer(playerNum)

        ratio = eval(self.ratioexpr)
        self.ratio = ratio

    def render(self, visibility, playerNum):
        # don't try to render image layer if the texture doesn't even exist
        if not self.drawing:
            return

        # get vars
        coord = self.position
        scale = self.scale
        rot = self.angle
        color = self.color
        alignment = self.alignment
        ratio = self.ratio

        # render the circle image
        if bool(eval(self.condition)):
            degrees = int(360 * ratio) - (int(360 * ratio) % 5)
            drawImage(self.drawnOverlays[degrees], scale, coord, rot, color, alignment=alignment)


class Effect(ConfigGetMixin):
    """ A template for effects """

    def __init__(self, layer, section):
        """
        :param layer: the rockmeter layer
        :param section: the section of rockmeter.ini involving this layer
        """
        super(Effect, self).__init__()

        # init vars
        self.layer = layer
        self.stage = layer.stage
        self.engine = layer.engine
        self.config = layer.config
        self.section = section
        self.condition = True

    def _smoothstep(self, x_min, x_max, x):
        def f(x):
            return -2 * x**3 + 3 * x**2

        if x < x_min:
            return 0
        if x > x_max:
            return 1
        return f((x - x_min) / (x_max - x_min))

    def triggerPick(self):
        if not self.stage.lastPickPos:
            return 0.0
        t = position - self.stage.lastPickPos
        return (1.0 - self._smoothstep(0, 500.0, t))

    def triggerMiss(self):
        if not self.stage.lastMissPos:
            return 0.0
        t = position - self.stage.lastMissPos
        return (1.0 - self._smoothstep(0, 500.0, t))

    def update(self):
        pass


class IncrementEffect(Effect):
    """ A base for effects that deal with incrementing values that provide smooth transitions and animations """

    def __init__(self, layer, section):
        super(IncrementEffect, self).__init__(layer, section)

        # determines if the values should increment back when the condition is
        # false or just jump back instantly
        self.reverse = False

        # can hold any number of values, as long as the amount matches
        self.start = []
        self.end = []
        self.current = []

        # rate at which values will increment between start and end
        self.inRates = []  # incoming rates
        self.outRates = []  # outgoing rates (if reverse is enabled)

        # how long it takes for the transition to take place
        self.transitionTime = 512.0
        self.transitionTimeOut = 512.0

    def getTime(self, time):
        """
        Get the rate at which time is passing, usable in finding the rates of
        things in terms of milliseconds instead of frames.
        """
        t = time * (max(1000.0 / self.engine.tickDelta, _minFPS)) / 1000.0
        return max(t, 1.0)

    def updateRates(self):
        """
        Update the rates at which values between start and end should change to
        reach the desired point.
        """
        try:
            # update incoming rates
            t = self.getTime(self.transitionTime)
            for i in range(len(self.start)):
                if self.end[i] < self.start[i]:
                    self.inRates[i] = (self.start[i] - self.end[i]) / t
                else:
                    self.inRates[i] = (self.end[i] - self.start[i]) / t

            # update outcoming rates
            if self.reverse and not bool(eval(self.condition)):
                t = self.getTime(self.transitionTimeOut)
                for i in range(len(self.start)):
                    if self.end[i] < self.start[i]:
                        self.outRates[i] = (self.start[i] - self.end[i]) / t
                    else:
                        self.outRates[i] = (self.end[i] - self.start[i]) / t
        except IndexError:
            # catches if rates have been declared or if they're proper size
            # then tries updating them again now that they're proper
            self.inRates = [0 for i in range(len(self.start))]
            self.outRates = self.inRates[:]
            self.updateRates()

    def updateValues(self):
        """ Update values with rates and returns the current saved value """
        condition = bool(eval(self.condition))
        if condition:
            # slides to the end position
            for i in range(len(self.start)):
                if self.current[i] > self.end[i]:
                    if self.end[i] < self.start[i]:
                        self.current[i] -= self.inRates[i]
                    else:
                        self.current[i] = self.end[i]
                elif self.current[i] < self.end[i]:
                    if self.end[i] > self.start[i]:
                        self.current[i] += self.inRates[i]
                    else:
                        self.current[i] = self.end[i]
                if (self.current[i] > self.end[i] and self.start[i] < self.end[i]) or \
                   (self.current[i] < self.end[i] and self.start[i] > self.end[i]):
                    self.current[i] = self.end[i]
        else:
            # slides back to original position smoothly
            if self.reverse:
                for i in range(len(self.start)):
                    if self.current[i] > self.start[i]:
                        if self.end[i] > self.start[i]:
                            self.current[i] -= self.outRates[i]
                        else:
                            self.current[i] = self.start[i]
                    elif self.current[i] < self.start[i]:
                        if self.end[i] < self.start[i]:
                            self.current[i] += self.outRates[i]
                        else:
                            self.current[i] = self.start[i]
                if (self.current[i] < self.start[i] and self.start[i] < self.end[i]) or \
                   (self.current[i] > self.start[i] and self.start[i] > self.end[i]):
                    self.current[i] = self.start[i]
            else:  #instant jump to starting value
                self.current = self.start[:]

        return self.current

    def update(self):
        """ Update the effect """
        self.updateRates()
        self.updateValues()


class Slide(IncrementEffect):
    """
    Slide the layer from one spot to another in a set period of time when the
    condition is met.
    """

    def __init__(self, layer, section):
        super(Slide, self).__init__(layer, section)

        w, h, = self.engine.view.geometry[2:4]
        # position of the image
        self.start = [eval(self.getexpr("startX", "0.0")), eval(self.getexpr("startY", "0.0"))]
        self.end   = [eval(self.getexpr("endX",   "0.0")), eval(self.getexpr("endY",   "0.0"))]
        self.inPixels = self.get("inPixels", str, "").split("|")  # variables in terms of pixels

        # update the position of the image
        if isinstance(self.layer, FontLayer):
            if "startX" in self.inPixels:
                self.start[0] /= vpc[0]
            if "endX" in self.inPixels:
                self.end[0] /= vpc[0]
            if "startY" in self.inPixels:
                self.start[1] /= vpc[1]
            if "endY" in self.inPixels:
                self.end[1] /= vpc[1]
        else:
            if "startX" in self.inPixels:
                self.start[0] *= w / vpc[0]
            else:
                self.start[0] *= w
            if "startY" in self.inPixels:
                self.start[1] *= h / vpc[1]
            else:
                self.start[1] *= h
            if "endX" in self.inPixels:
                self.end[0] *= w / vpc[0]
            else:
                self.end[0] *= w
            if "endY" in self.inPixels:
                self.end[1] *= h / vpc[1]
            else:
                self.end[1] *= h

        self.current = self.start[:]
        # y position needs to be flipped initially
        if isinstance(self.layer, FontLayer):
            self.current[1] *= .75
            self.current[1] = .75 - self.current[1]

        self.reverse = bool(eval(self.getexpr("reverse", "True")))
        self.condition = self.getexpr("condition", "True")
        self.transitionTime = self.get("transitionTime", float, 512.0)
        self.transitionTimeOut = self.get("transitionTimeOut", float, self.transitionTime)

    def updateValues(self):
        # reverse the processing for font layer handling
        if isinstance(self.layer, FontLayer):
            self.current[1] = .75 - self.current[1]
            self.current[1] /= .75

        super(Slide, self).updateValues()

        # because of the y position being flipped on fonts it needs to be caught
        if isinstance(self.layer, FontLayer):
            self.current[1] *= .75
            self.current[1] = .75 - self.current[1]

    def update(self):
        super(Slide, self).update()

        self.layer.position = self.current[:]


class Scale(IncrementEffect):
    """
    Smoothly scale the layer from one size to another in a set period of time
    when the condition is met.
    """

    def __init__(self, layer, section):
        super(Scale, self).__init__(layer, section)

        # position of the image
        self.start = [eval(self.getexpr("startX", "0.0")), eval(self.getexpr("startY", "0.0"))]
        self.end   = [eval(self.getexpr("endX",   "0.0")), eval(self.getexpr("endY",   "0.0"))]

        self.current = self.start[:]

        self.inPixels = self.get("inPixels", str, "").split("|")  # variables in terms of pixels

        self.transitionTime = self.get("transitionTime", float, 512.0)
        self.transitionTimeOut = self.get("transitionTimeOut", float, self.transitionTime)
        self.condition = self.getexpr("condition", "True")
        self.reverse = bool(eval(self.getexpr("reverse", "True")))

        self.fixedScale = isinstance(self.layer, ImageLayer)

    def fixScale(self):
        w, h, = self.engine.view.geometry[2:4]

        self.start[0] *= (self.layer.rect[1] - self.layer.rect[0])
        self.start[1] *= (self.layer.rect[3] - self.layer.rect[2])
        self.end[0] *= (self.layer.rect[1] - self.layer.rect[0])
        self.end[1] *= (self.layer.rect[3] - self.layer.rect[2])

        if "startX" in self.inPixels:
            self.start[0] /= self.layer.drawing.pixelSize[0]
        if "startY" in self.inPixels:
            self.start[1] /= self.layer.drawing.pixelSize[1]
        if "endX" in self.inPixels:
            self.end[0] /= self.layer.drawing.pixelSize[0]
        if "endY" in self.inPixels:
            self.end[1] /= self.layer.drawing.pixelSize[1]

        self.start[1] *= -1
        self.end[1] *= -1
        self.start[0] *= w / vpc[0]
        self.end[0] *= w / vpc[0]
        self.start[1] *= h / vpc[1]
        self.end[1] *= h / vpc[1]

        self.current = self.start[:]

    def update(self):
        if not self.fixedScale and not isinstance(self.layer, Group):
            self.fixScale()
            self.fixedScale = True

        super(Scale, self).update()

        self.layer.scale = self.current[:]


class Fade(IncrementEffect):
    """
    Fade the color of the layer between this color and its original in a set
    period of time when the condition is met.
    """

    def __init__(self, layer, section):
        super(Fade, self).__init__(layer, section)

        # starting color
        color = list(hexToColor(self.get("color", str, "#FFFFFF")))
        self.start = color
        if len(self.start) == 3:
            self.start.append(1.0)

        # the color to fade to
        self.end = list(hexToColor(self.get("fadeTo", str, "#FFFFFF")))
        # makes sure alpha is added
        if len(self.end) == 3:
            color.append(1.0)

        # the current color of the image
        self.current = self.start[:]

        self.transitionTime = self.get("transitionTime", float, 512.0)
        self.transitionTimeOut = self.get("transitionTimeOut", float, self.transitionTime)
        self.condition = self.getexpr("condition", "True")
        self.reverse = bool(eval(self.getexpr("reverse", "True")))

    def update(self):
        super(Fade, self).update()

        self.layer.color = self.current[:]


class Replace(Effect):
    """ Replace the image of the layer when the condition is met. """

    def __init__(self, layer, section):
        super(Replace, self).__init__(layer, section)

        if isinstance(layer, ImageLayer):
            # load textures
            self.drawings = []
            if self.get("texture") is not None:
                texture = [t.strip() for t in self.get("texture").split("|")]
                for tex in texture:
                    path = os.path.join("themes", layer.stage.themename, "rockmeter", tex)
                    drawing = self.engine.loadImgDrawing(self, None, path)
                    self.drawings.append(drawing)
            self.drawings.append(layer.drawing)

            # load rects
            self.rects = []
            if self.get("rect") is not None:
                rects = self.getexprs("rect", separator="|")
                for rect in rects:
                    self.rects.append(rect)
            self.rects.append(layer.rectexpr)
            self.type = "image"

        elif isinstance(layer, FontLayer):
            self.font = self.engine.data.fontDict[self.get("font")]
            self.text = self.getexprs("text", separator="|")
            self.type = "font"

        self.conditions = self.getexprs("condition", "True", "|")
        self.xscaleexpr = self.layer.getexpr("xscale", "0.5")
        self.yscaleexpr = self.layer.getexpr("yscale", "0.5")

    def fixScale(self):
        """ Fix the scale after the rect is changed. """
        w, h, = self.engine.view.geometry[2:4]

        rect = self.layer.rect
        scale = [eval(self.xscaleexpr), eval(self.yscaleexpr)]
        scale[0] *= (rect[1] - rect[0])
        scale[1] *= (rect[3] - rect[2])
        # this allows you to scale images in relation to pixels instead
        # of percentage of the size of the image.
        if "xscale" in self.layer.inPixels:
            scale[0] /= self.layer.drawing.pixelSize[0]
        if "yscale" in self.layer.inPixels:
            scale[1] /= self.layer.drawing.pixelSize[1]

        scale[1] = -scale[1]
        scale[0] *= w / vpc[0]
        scale[1] *= h / vpc[1]

        self.layer.scale = scale

    def update(self):
        for i, cond in enumerate(self.conditions):
            if bool(eval(cond)):
                if self.type == "font":
                    self.layer.finals[-1] = self.text[i]
                else:
                    if len(self.drawings) > 1:
                        self.layer.drawing = self.drawings[i]
                    if len(self.rects) > 1:
                        self.layer.rect = [float(i) for i in eval(self.rects[i])]
                    self.fixScale()
                break
        else:
            # if no conditions are True
            if self.type == "font":
                self.layer.text = self.text[-1]
            else:
                if len(self.drawings) > 0:
                    self.layer.drawing = self.drawings[-1]
                if len(self.rects) > 0:
                    self.layer.rect = [float(i) for i in eval(self.rects[-1])]
                self.fixScale()


class Animate(Effect):
    """
    Effect that allows one to set the number of frames and have the layer loop
    through an animation.
    """

    def __init__(self, layer, section):
        super(Animate, self).__init__(layer, section)

        self.frames = self.get("frames", int, 1)
        self.fps = self.get("fps", int, 30)

        self.currentFrame = 1
        self.transitionTime = self.get("transitionTime", float, 512.0)

        self.condition = self.getexpr("condition", "True")

    def fixScale(self):
        """ Fix the scale after the rect is changed. """
        scale = [self.layer.scale[0] / self.frames, self.layer.scale[1]]
        self.layer.scale = scale

    def updateRate(self):
        """ Adjust the rate to the current FPS. """
        self.rate = float(self.frames) / (self.transitionTime * (max(1000.0 / self.engine.tickDelta, _minFPS)) / 1000.0)

    def update(self):
        self.updateRate()

        if bool(eval(self.condition)) and self.currentFrame < self.frames:
            self.currentFrame += self.rate
        else:
            self.currentFrame = 1

        rect = self.layer.rect
        rect = [(rect[1] - rect[0]) / self.frames * (int(self.currentFrame) - 1),
                (rect[1] - rect[0]) / self.frames * int(self.currentFrame),
                rect[2], rect[3]]

        self.layer.rect = rect
        self.fixScale()


class Group(Layer):
    """
    Group of layers.

    Groups will allow all layers within to be centered at a certain point, be
    scaled, be hued, and be rotated together. They can even be effected by the
    same effects that layers have minus animate and replace.
    """

    def __init__(self, stage, section):
        super(Group, self).__init__(stage, section)

        self.layers = {}  # the layers the group controls
        for num in self.get("layers", str, "").split(","):
            self.layers[int(num)] = self.stage.layers[int(num)]

    def updateLayer(self, playerNum):
        super(Group, self).updateLayer(playerNum)

        w, h, = self.engine.view.geometry[2:4]

        position = self.position
        if "xpos" in self.inPixels:
            position[0] *= w / vpc[0]
        else:
            position[0] *= w
        if "ypos" in self.inPixels:
            position[1] *= h / vpc[1]
        else:
            position[1] *= h
        self.position = position

    def render(self, visibility, playerNum):
        """ Handle the final step of rendering the image. """

        w, h, = self.engine.view.geometry[2:4]

        # update the layer
        self.updateLayer(playerNum)
        # update effects
        for effect in self.effects:
            effect.update()
        # update each layers and their effects
        for layer in self.layers.values():
            layer.updateLayer(playerNum)
            for effect in layer.effects:
                effect.update()
            if isinstance(layer, FontLayer):
                layer.position = [layer.position[0] + self.position[0] / w, layer.position[1] - (self.position[1] / h) * .75]
            else:
                layer.position = [layer.position[i] + self.position[i] for i in range(2)]
            layer.scale = [layer.scale[i] * self.scale[i] for i in range(2)]
            layer.angle += self.angle
            layer.color = [layer.color[i] * self.color[i] for i in range(4)]
            layer.render(visibility, playerNum)


class Rockmeter(ConfigGetMixin):

    _layerLimit = 99  # limit to how many layers can be loaded
    _groupLimit = 50  # limit to how many groups can be loaded

    def __init__(self, guitarScene, configFileName, coOp=False):
        self.scene = guitarScene
        self.engine = guitarScene.engine
        self.layers = {}          # collection of all the layers in the rockmeter
        self.layersForRender = {} # collection of layers that are rendered separate from any group
        self.layerGroups = {}     # collection of layer groups
        self.sharedLayerGroups = {}
        self.sharedLayers = {}    # these layers are for coOp use only
        self.sharedLayersForRender = {}
        self.sharedGroups = {}

        self.coOp = coOp
        self.config = MyConfigParser()
        self.config.read(configFileName)

        self.themename = self.engine.data.themeLabel

        try:
            themepath = os.path.join(Version.dataPath(), "themes", self.themename)
            fp, pathname, description = imp.find_module("CustomRMLayers", [themepath])
            self.customRMLayers = imp.load_module("CustomRMLayers", fp, pathname, description)
        except ImportError:
            self.customRMLayers = None
            log.info("Custom Rockmeter layers are not available")

        # Build the layers
        types = [
            "Image",
            "Text",
            "Circle",
            "Custom"
        ]
        for i in range(Rockmeter._layerLimit):
            for t in types:
                self.section = "layer%d:%s" % (i, t)
                if not self.config.has_section(self.section):
                    continue
                else:
                    if t == types[1]:
                        self.createFont(self.section, i)
                    elif t == types[2]:
                        self.createCircle(self.section, i)
                    elif t == types[3]:
                        self.createCustom(self.section, i)
                    else:
                        self.createImage(self.section, i)
                    break

        # build groups
        for i in range(Rockmeter._groupLimit):
            self.section = "Group%d" % i
            if not self.config.has_section(self.section):
                continue
            else:
                self.createGroup(self.section, i)

        self.reset()

    def reset(self):
        self.lastMissPos = None
        self.lastPickPos = None
        self.playedNotes = []
        self.averageNotes = [0.0]

    def addLayer(self, layer, number, shared=False):
        """ Add a layer to the rockmeter's list. """
        if shared:
            self.sharedLayers[number] = layer
            self.sharedLayersForRender[number] = layer
        else:
            if layer:
                self.layers[number] = layer
                self.layersForRender[number] = layer

    def loadLayerFX(self, layer, section):
        section = section.split(":")[0]
        types = {
            "Slide": "Slide(layer, fxsection)",
            "Rotate": "Rotate(layer, fxsection)",
            "Replace": "Replace(layer, fxsection)",
            "Fade": "Fade(layer, fxsection)",
            "Animate": "Animate(layer, fxsection)",
            "Scale": "Scale(layer, fxsection)",
        }

        # make sure groups don't load effects they can use
        if isinstance(layer, Group):
            types.pop("Animate")
            types.pop("Replace")

        # maximum of 5 effects per layer
        for i in range(5):
            for t in types.keys():
                fxsection = "%s:fx%d:%s" % (section, i, t)
                if not self.config.has_section(fxsection):
                    continue
                else:
                    layer.effects.append(eval(types[t]))
                    break

    def createCustom(self, section, number):
        if self.customRMLayers:
            classname = self.get("classname")

            layer = eval("self.customRMLayers." + classname + "(self, section)")

            if isinstance(layer, Group):
                self.addGroup(layer, number, layer.shared)
            else:
                self.addLayer(layer, number, layer.shared)

    def createFont(self, section, number):
        font = self.get("font", str, "font")
        layer = FontLayer(self, section, font)

        layer.text      = self.getexpr("text")
        layer.shared    = self.get("shared", bool, False)
        layer.condition = self.getexpr("condition", "True")
        layer.inPixels  = self.get("inPixels", str, "").split("|")

        self.loadLayerFX(layer, section)
        self.addLayer(layer, number, layer.shared)

    def createImage(self, section, number):
        texture = self.get("texture")
        drawing = os.path.join("themes", self.themename, "rockmeter", texture)
        layer = ImageLayer(self, section, drawing)

        layer.shared    = self.get("shared", bool, False)
        layer.condition = self.getexpr("condition", "True")
        layer.inPixels  = self.get("inPixels", str, "").split("|")

        layer.rect = self.getexpr("rect", "(0,1,0,1)")

        self.loadLayerFX(layer, section)
        self.addLayer(layer, number, layer.shared)

    def createCircle(self, section, number):
        texture = self.get("texture")
        drawing = os.path.join("themes", self.themename, "rockmeter", texture)
        layer = CircleLayer(self, section, drawing)

        layer.shared    = self.get("shared", bool, False)
        layer.condition = self.getexpr("condition", "True")
        layer.inPixels  = self.get("inPixels", str, "").split("|")

        layer.rect = self.getexpr("rect", "(0,1,0,1)")

        self.loadLayerFX(layer, section)
        self.addLayer(layer, number, layer.shared)

    def createGroup(self, section, number):
        group = Group(self, section)

        group.shared = self.get("shared", bool, False)

        self.loadLayerFX(group, section)
        self.addGroup(group, number, group.shared)

    def addGroup(self, group, number, shared):
        # remove the layers in the group from the layers to be rendered
        # independent of groups
        if shared:
            for layer in group.layers.keys():
                if layer in self.layersForRender.keys():
                    self.layersForRender.pop(layer)
                self.sharedLayerGroups[number] = group
        else:
            for layer in group.layers.keys():
                if layer in self.layersForRender.keys():
                    self.layersForRender.pop(layer)
                self.layerGroups[number] = group

    def updateTime(self):
        # because time is not player specific it's best to update it only once per cycle
        global songLength, minutesSongLength, secondsSongLength
        global minutesCountdown, secondsCountdown, minutes, seconds
        global position, countdownPosition, progress

        scene = self.scene

        songLength = scene.lastEvent
        position = scene.songTime
        countdownPosition = songLength - position
        progress = float(position) / float(songLength)
        if progress < 0:
            progress = 0
        elif progress > 1:
            progress = 1

        minutesCountdown, secondsCountdown   = (countdownPosition / 60000, (countdownPosition % 60000) / 1000)
        minutes, seconds                     = (position / 60000, (position % 60000) / 1000)
        minutesSongLength, secondsSongLength = (songLength / 60000, (songLength % 60000) / 1000)

    def updateVars(self, p):
        """ Update all global variables that are handled by the rockmeter (player specific). """
        global score, rock, coop_rock, streak, streakMax, power, stars
        global partialStars, multiplier, bassgroove, boost, player, part
        global playerNum
        scene = self.scene
        playerNum = p
        player = scene.instruments[playerNum]
        playerName = self.scene.players[p].name
        part = player.__class__.__name__

        #this is here for when I finally get coOp worked in
        if self.coOp:
            score = scene.coOpScoreCard.score
            stars = scene.coOpScoreCard.stars
            partialStars = scene.coOpScoreCard.starRatio
            coop_rock = scene.rock[scene.coOpPlayerMeter] / scene.rockMax
        else:
            score = scene.scoring[playerNum].score
            stars = scene.scoring[playerNum].stars
            partialStars = scene.scoring[playerNum].starRatio
        rock = scene.rock[playerNum] / scene.rockMax

        streak = scene.scoring[playerNum].streak
        power = player.starPower / 100.0

        # allows for bassgroove
        if player.isBassGuitar:
            streakMax = 50
        else:
            streakMax = 30

        if streak >= streakMax:
            multiplier = int(streakMax * .1) + 1
        else:
            multiplier = int(streak * .1) + 1

        boost = player.starPowerActive

        # doubles the multiplier number when starpower is activated
        if boost:
            multiplier *= 2

        bassgroove = player.isBassGuitar and streak >= 40

        # force bassgroove to false if it's not enabled
        if not scene.bassGrooveEnabled:
            bassgroove = False

    def triggerPick(self, pos, notes):
        if notes:
            self.lastPickPos = pos
            self.playedNotes = self.playedNotes[-3:] + [sum(notes) / float(len(notes))]
            self.averageNotes[-1] = sum(self.playedNotes) / float(len(self.playedNotes))

    def triggerMiss(self, pos):
        self.lastMissPos = pos

    def render(self, visibility):
        self.updateTime()

        with self.engine.view.orthogonalProjection(normalize=True):
            for i, player in enumerate(self.scene.players):
                p = player.number
                self.updateVars(p)
                if p is not None:
                    self.engine.view.setViewportHalf(self.scene.numberOfGuitars, p)
                else:
                    self.engine.view.setViewportHalf(1, 0)
                for group in self.layerGroups.values():
                    group.render(visibility, p)
                for layer in self.layersForRender.values():
                    layer.updateLayer(p)
                    for effect in layer.effects:
                        effect.update()
                    layer.render(visibility, p)

            self.engine.view.setViewportHalf(1, 0)
            for layer in self.sharedLayersForRender.values():
                layer.render(visibility, 0)
            for group in self.sharedLayerGroups.values():
                group.render(visibility, 0)

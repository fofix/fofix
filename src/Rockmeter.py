#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
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

# So we don't get future division in effect but can get the flag for
# compiling the rockmeter expressions with it in effect.
import __future__
FUTURE_DIVISION = __future__.division.compiler_flag

from LinedConfigParser import LinedConfigParser
import os

from Svg import ImgDrawing

import locale

from PIL import Image, ImageDraw
from OpenGL.GL import *

import math
from math import *

from Theme import halign, valign
from constants import *

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
player = None

score = 0               #player's score
streak = 0              #player's streak
streakMax = 0           #amount of notes it takes to hit make multiplier
power = 0               #star power fill amount
stars = 0               #how many stars earned
partialStars = 0        #percentage of the current star earned
rock = 0                #rock meter fill amount
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

# Functions for getting config values, optionally as compiled code objects ready to eval().
class ConfigGetMixin(object):
  def get(self, value, type = str, default = None):
    if self.config.has_option(self.section, value):
      return type(self.config.get(self.section, value).strip())
    return default

  def getexpr(self, value, default=None):
    if self.config.has_option(self.section, value):
      filename, lineno = self.config.getlineno(self.section, value)
      expr = self.config.get(self.section, value)
      return compile('\n' * (lineno - 1) + expr, filename, 'eval', FUTURE_DIVISION)
    return compile(default, '<string>', 'eval', FUTURE_DIVISION)

  def getexprs(self, value, default=None, separator='|'):
    if self.config.has_option(self.section, value):
      filename, lineno = self.config.getlineno(self.section, value)
      exprs = [e.strip() for e in self.config.get(self.section, value).split(separator)]
      return [compile('\n' * (lineno - 1) + expr, filename, 'eval', FUTURE_DIVISION) for expr in exprs]
    return [compile(expr, '<string>', 'eval', FUTURE_DIVISION) for expr in default.split(separator)]


# A graphical rockmeter layer
# This is the base template for all rockmeter layer types
class Layer(ConfigGetMixin):
  #calculates the board's width at a certain position
  #returns a value not in pixels
  def boardWidth(self, x):
      self.engine.view.setViewport(1,0)
      wFull, hFull = self.engine.view.geometry[2:4]
      scaleCoef = (0.6 + 0.4 * self.stage.scene.numberOfGuitars) * 1.256 * hFull / wFull
      return player.boardWidth / math.sqrt((self.stage.scene.camera.origin[1] + x)**2+((self.stage.scene.camera.origin[2] + x)-0.5)**2) * scaleCoef

  def __init__(self, stage, section):
    self.stage       = stage			#The rockmeter
    self.engine      = stage.engine		#Game Engine
    self.config      = stage.config     #the rockmeter.ini
    self.section     = section          #the section of the rockmeter.ini involving this layer

    self.xposexpr    = self.getexpr("xpos", "0.0")
    self.yposexpr    = self.getexpr("ypos", "0.0")
    self.position    = [0.0, 0.0]       #where on the screen to draw the layer
    
    self.angleexpr   = self.getexpr("angle", "0.0")
    self.angle       = 0.0              #angle to rotate the layer (in degrees)
    
    self.xscaleexpr  = self.getexpr("xscale", "1.0")
    self.yscaleexpr  = self.getexpr("yscale", "1.0")
    self.scale       = [1.0, 1.0]       #how much to scale it by (width, height from 0.0 - 1.0)
    
    if self.config.has_option(section, "color"):
                                        #color of the image (#FFFFFF is white on text, on images it is full color)
      self.color   = list(self.engine.theme.hexToColor(self.get("color", str, "#FFFFFF")))
      if len(self.color) == 3:
        self.color.append(1.0)
      self.r, self.g, self.b, self.a = [str(c) for c in self.color]
    else:
      self.r = self.getexpr("r", "1.0")
      self.g = self.getexpr("g", "1.0")
      self.b = self.getexpr("b", "1.0")
      self.a = self.getexpr("a", "1.0")
      self.color = [1.0,1.0,1.0,1.0]
        
    self.condition   = True				#when should the image be shown (by default it will always be shown)
    
    self.alignment   = halign(self.get("alignment", str, "center"))
                                        #alignment of the image (horizontal)
    self.valignment  = valign(self.get("valignment", str, "middle"))
                                        #alignment of the image (vertical)
    self.inPixels    = self.get("inPixels", str, "").split("|")
                                        #makes sure to properly scale/position the images in pixels instead of percent

    self.effects     = []               #various effects associated with the layer
                        
  # all variables that should be updated during the rendering process
  # should be in here just for sake of readablity and organization
  def updateLayer(self, playerNum):
    self.position    = [float(eval(self.xposexpr)), float(eval(self.yposexpr))]
    self.angle       = float(eval(self.angleexpr))
    self.scale       = [float(eval(self.xscaleexpr)), float(eval(self.yscaleexpr))]
    
    self.color       = [float(eval(self.r)), float(eval(self.g)),
                        float(eval(self.b)), float(eval(self.a))]
    
    #makes sure color has an alpha value to consider
    if len(self.color) == 3:
        self.color.append(1.0)
         
  # should handle the final step of rendering the image
  # be sure if you have variables being updated in updateVars
  # to call updateVars and refresh them.  playerNum is *especially*
  # important if there is more than one player present.
  def render(self, visibility, playerNum):
    pass

#A graphical stage layer that is used to render the rockmeter.
class ImageLayer(Layer):
  def __init__(self, stage, section, drawing):
    super(ImageLayer, self).__init__(stage, section)

    #these are the images that are drawn when the layer is visible
    self.drawing = self.engine.loadImgDrawing(self, None, drawing)
    self.rectexpr = self.getexpr("rect", "(0.0,1.0,0.0,1.0)")
                                    #how much of the image do you want rendered
                                    # (left, right, top, bottom)
                                    
  def updateLayer(self, playerNum):
    #don't try to update an image layer if the texture doesn't even exist
    if not self.drawing:
      return
    
    w, h, = self.engine.view.geometry[2:4]
    texture = self.drawing

    super(ImageLayer, self).updateLayer(playerNum)
    
    rect = self.rect = [float(i) for i in eval(self.rectexpr)]
    
    #all of this has to be repeated instead of using the base method
    #because now things can be calculated in relation to the image's properties

    scale = self.scale
    scale[0] *=  (rect[1] - rect[0])
    scale[1] *=  (rect[3] - rect[2])
    
    #this allows you to scale images in relation to pixels instead
    #of percentage of the size of the image.
    if "xscale" in self.inPixels:
      scale[0] /= texture.pixelSize[0]
    if "yscale" in self.inPixels:
      scale[1] /= texture.pixelSize[1]

    scale[1] = -scale[1]
    scale[0] *= w/vpc[0]
    scale[1] *= h/vpc[1]
    
    self.scale = scale
    
    position = self.position
    if "xpos" in self.inPixels:
      position[0] *= w/vpc[0]
    else:        
      position[0] *= w

    if "ypos" in self.inPixels:
      position[1] *= h/vpc[1]
    else:        
      position[1] *= h

    self.position = position

  def render(self, visibility, playerNum):
        
    self.updateLayer(playerNum)
    for effect in self.effects:
      effect.update()

    #don't try to render an image layer if the texture doesn't even exist
    if not self.drawing:
        return
    
    coord      = self.position
    scale      = self.scale
    rot        = self.angle
    color      = self.color
    alignment  = self.alignment
    valignment = self.valignment
    drawing    = self.drawing
    rect       = self.rect
    
    #frameX  = self.frameX
    #frameY  = self.frameY

    if bool(eval(self.condition)):
      self.engine.drawImage(drawing, scale, coord, rot, color, rect, 
                            alignment = alignment, valignment = valignment)

#defines layers that are just font instead of images
class FontLayer(Layer): 
  def __init__(self, stage, section, font):
    super(FontLayer, self).__init__(stage, section)

    self.font        = self.engine.data.fontDict[font]          #the font to use
    self.text        = ""                                       #the text that will be rendered to screen 
    self.textexpr    = self.getexpr("text", "''")               #the text from the ini that will be evalutated
    self.replace     = ""                                       #replace character a character in the string with this
    self.alignment   = halign(self.get("alignment", str, "LEFT"), 'left')
                                                                #alignment of the text
    self.useComma    = self.get("useComma", bool, False)        #use commas when drawing numbers
    self.shadow      = self.get("shadow",   bool, False)        #show a shadow on the text
    self.outline     = self.get("outline",  bool, False)        #give the text an outline

  def updateLayer(self, playerNum):
    w, h, = self.engine.view.geometry[2:4]
    
    text = eval(self.textexpr)

    if self.useComma:
      text = locale.format("%d", text, grouping=True)
    else:
      text = str(text)

    wid, hgt = self.font.getStringSize(str(text))

    #needs to be done later because of values that may be dependant on the text's properties
    super(FontLayer, self).updateLayer(playerNum)

    self.text = text
    
    position = self.position
    if "xpos" in self.inPixels:
      position[0] /= vpc[0]
    if "ypos" in self.inPixels:
      position[1] /= vpc[1]
    
    #the viewport code for rendering for is a little awkward
    #instead of the bottom edge being at 1.0 it is at .75
    #by doing this people can use conventional positioning
    #while the code self adjusts the values
    position[1] *= .75
    #not only that but it's upside down
    position[1] = .75 - position[1]
    
    self.position = position
    
  def render(self, visibility, playerNum):
    w, h, = self.stage.engine.view.geometry[2:4]

    self.updateLayer(playerNum)
    for effect in self.effects:
      effect.update()

    position = self.position
    alignment = self.alignment
    color = self.color

    if bool(eval(self.condition)):
        glColor4f(*color)
        self.font.render(self.text, position, align = alignment, 
                         shadow = self.shadow, outline = self.outline)
    
        
#creates a layer that is shaped like a pie-slice/circle instead of a rectangle
class CircleLayer(ImageLayer): 
  def __init__(self, stage, section, drawing):
    super(CircleLayer, self).__init__(stage, section, drawing)

    #this number (between 0 and 1) determines how much
    #of the circle should be filled (0 to 360 degrees)
    self.ratioexpr = self.getexpr("ratio", "1")
    self.ratio     = eval(self.ratioexpr)

    #don't try to create the circle layer if the texture doesn't even exist
    if self.drawing:
      self.createMask(drawing)
        
  #creates the overlay mask
  def createMask(self, drawing):
      
    #these determine the size of the PIL pie-slice
    self.centerX   = self.drawing.width1()/2
    self.centerY   = self.drawing.height1()/2
    self.inRadius  = 0
    self.outRadius = self.drawing.width1()/2
    
    #generates all the images needed for the circle
    self.drawnOverlays = {}
    baseFillImageSize = self.drawing.pixelSize
    for degrees in range(0, 361, 5):
      image = Image.open(self.drawing.path)
      mask = Image.new('RGBA', baseFillImageSize)
      overlay = Image.new('RGBA', baseFillImageSize)
      draw = ImageDraw.Draw(mask)
      draw.pieslice((self.centerX-self.outRadius, self.centerY-self.outRadius,
                     self.centerX+self.outRadius, self.centerY+self.outRadius),
                     -90, degrees-90, outline=(255,255,255,255), fill=(255,255,255,255))
      draw.ellipse((self.centerX-self.inRadius, self.centerY-self.inRadius,
                    self.centerX+self.inRadius, self.centerY+self.inRadius),
                    outline=(0, 0, 0, 0), fill=(0, 0, 0, 0))
      r,g,b,a = mask.split()
      overlay.paste(image, mask=a)
      dispOverlay = ImgDrawing(self.engine.data.svg, overlay)
      self.drawnOverlays[degrees] = dispOverlay

  def updateLayer(self, playerNum):
    #don't try to update an image layer if the texture doesn't even exist
    if not self.drawing:
      return
    
    ratio = eval(self.ratioexpr)
    self.ratio = ratio
    
    super(CircleLayer, self).updateLayer(playerNum)
    
  def render(self, visibility, playerNum):
    w, h, = self.stage.engine.view.geometry[2:4]

    self.updateLayer(playerNum)
    for effect in self.effects:
      effect.update()

    #don't try to render image layer if the texture doesn't even exist
    if not self.drawing:
      return
    
    coord     = self.position
    scale     = self.scale
    rot       = self.angle
    color     = self.color
    alignment = self.alignment
    ratio     = self.ratio
    
    if bool(eval(self.condition)):
      degrees = int(360*ratio) - (int(360*ratio) % 5)
      self.engine.drawImage(self.drawnOverlays[degrees], scale, 
                            coord, rot, color, alignment = alignment)


#this is just a template for effects                
class Effect(ConfigGetMixin):
  def __init__(self, layer, section):
    self.layer = layer
    self.stage = layer.stage
    self.engine = layer.engine
    self.config = layer.config
    self.section = section
    
    self.condition = True

  def update(self):
    pass

#slides the layer from one spot to another
#in a set period of time when the condition is met
class Slide(Effect):
  def __init__(self, layer, section):
    super(Slide, self).__init__(layer, section)

    self.startCoord = [eval(self.getexpr("startX", "0.0")), eval(self.getexpr("startY", "0.0"))]
                                                                #starting position of the image
    self.endCoord   = [eval(self.getexpr("endX",   "0.0")), eval(self.getexpr("endY",   "0.0"))]
                                                                #ending position of the image
    self.inPixels  = self.get("inPixels", str, "").split("|")   #variables in terms of pixels

    self.condition = self.getexpr("condition", "True")
    
    w, h, = self.engine.view.geometry[2:4]

    if isinstance(self.layer, FontLayer):
      if "startX" in self.inPixels:
        self.startCoord[0] /= vpc[0]
      if "endX" in self.inPixels:
        self.endCoord[0] /= vpc[0]
      if "startY" in self.inPixels:
        self.startCoord[1] /= vpc[1]
      if "endY" in self.inPixels:
        self.endCoord[1] /= vpc[1]
    else:
      if "startX" in self.inPixels:
        self.startCoord[0] *= w/vpc[0]
      else:
        self.startCoord[0] *= w

      if "startY" in self.inPixels:
        self.startCoord[1] *= h/vpc[1]
      else:
        self.startCoord[1] *= h

      if "endX" in self.inPixels:
        self.endCoord[0] *= w/vpc[0]
      else:
        self.endCoord[0] *= w

      if "endY" in self.inPixels:
        self.endCoord[1] *= h/vpc[1]
      else:
        self.endCoord[1] *= h


    self.position = self.startCoord[:]
    #y position needs to be flipped initially
    if isinstance(self.layer, FontLayer):
      self.position[1] *= .75
      self.position[1] = .75 - self.position[1]
    
    self.reverse = bool(eval(self.getexpr("reverse", "True")))

    #how long it takes for the transition to take place
    self.transitionTime = self.get("transitionTime", float, 512.0)

    self.rates = [0,0]
    self.updateRates()
    
  #updates the rate at which the layer will slide
  def updateRates(self):
    t = self.transitionTime * (max(self.engine.clock.get_fps(), _minFPS)) / 1000.0
    for i in range(2):
      if self.endCoord[i] < self.startCoord[i]:
        self.rates[i] = (self.startCoord[i] - self.endCoord[i])/t
      else:
        self.rates[i] = (self.endCoord[i] - self.startCoord[i])/t
              
  def update(self):
    condition = bool(eval(self.condition))

    #reverse the processing for font layer handling
    if isinstance(self.layer, FontLayer):
      self.position[1] = .75 - self.position[1]
      self.position[1] /= .75

    self.updateRates()
        
    if condition:
      for i in range(2):
        if self.position[i] > self.endCoord[i]:
          if self.endCoord[i] < self.startCoord[i]:
            self.position[i] -= self.rates[i]
          else:
            self.position[i] = self.endCoord[i]
        elif self.position[i] < self.endCoord[i]:
          if self.endCoord[i] > self.startCoord[i]:
            self.position[i] += self.rates[i]
          else:
            self.position[i] = self.endCoord[i]
    else:
      if self.reverse:
        for i in range(2):
          if self.position[i] > self.startCoord[i]:
            if self.endCoord[i] > self.startCoord[i]:
              self.position[i] -= self.rates[i]
            else:
              self.position[i] = self.startCoord[i]
          elif self.position[i] < self.startCoord[i]:
            if self.endCoord[i] < self.startCoord[i]:
              self.position[i] += self.rates[i]
            else:
              self.position[i] = self.startCoord[i]
      else:  
        self.position = self.startCoord
        
    #because of the y position being flipped on fonts it needs to be caught
    if isinstance(self.layer, FontLayer):
      self.position[1] *= .75
      self.position[1] = .75 - self.position[1]
    
    self.layer.position = self.position[:]

#fades the color of the layer between this color and its original
#in a set period of time when the condition is met
class Fade(Effect):
  def __init__(self, layer, section):
    super(Fade, self).__init__(layer, section)

    
    #starting color
    color = self.engine.theme.hexToColor(self.get("color", str, "#FFFFFF"))
    
    #the current color of the image
    self.currentColor = list(color)
    if len(self.currentColor) == 3:
      self.currentColor.append(1.0)
    
    #the color to fade to
    color = list(self.engine.theme.hexToColor(self.get("fadeTo", str, "#FFFFFF")))
    #makes sure alpha is added
    if len(color) == 3:
      color.append(1.0)
    
    #the colors to alternate between
    self.colors = [color, self.currentColor]
    
    #how long it takes for the transition to take place
    self.transitionTime = self.get("transitionTime", float, 512.0)

    self.updateRates()
    
    self.condition = self.getexpr("condition", "True")
    self.reverse = bool(eval(self.getexpr("reverse", "True")))

  def updateRates(self):
    t = self.transitionTime * (max(self.engine.clock.get_fps(), _minFPS)) / 1000.0
    self.rates = [(self.colors[0][i] - self.colors[1][i])/t 
                      for i in range(4)]
    
  def update(self):
    condition = bool(eval(self.condition))

    self.updateRates()
    
    if condition:
      for i in range(len(self.currentColor)):
        if self.currentColor[i] > self.colors[0][i]:
          self.currentColor[i] -= self.rates[i]
        elif self.currentColor[i] < self.colors[0][i]:
          self.currentColor[i] += self.rates[i]
    else:
      if self.reverse:
        for i in range(len(self.currentColor)):
          if self.currentColor[i] > self.colors[1][i]:
            self.currentColor[i] -= self.rates[i]
          elif self.currentColor[i] < self.colors[1][i]:
            self.currentColor[i] += self.rates[i]
      else:  
        self.currentColor[i] = self.colors[1]
        
    self.layer.color = self.currentColor

#replaces the image of the layer when the condition is met
class Replace(Effect):
  def __init__(self, layer, section):
    super(Replace, self).__init__(layer, section)

    if isinstance(layer, ImageLayer):
      self.drawings  = []
      self.rects = []
      if not self.get("texture") == None:
        texture   = [t.strip() for t in self.get("texture").split("|")]
        for tex in texture:
          path   = os.path.join("themes", layer.stage.themename, "rockmeter", tex)
          drawing = self.engine.loadImgDrawing(self, None, path)
          self.drawings.append(drawing)
      self.drawings.append(layer.drawing)
      if not self.get("rect") == None:
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
    
  #fixes the scale after the rect is changed
  def fixScale(self):
    w, h, = self.engine.view.geometry[2:4]
    
    rect = self.layer.rect
    scale     = [eval(self.xscaleexpr), eval(self.yscaleexpr)]
    scale[0] *=  (rect[1] - rect[0])
    scale[1] *=  (rect[3] - rect[2])
    #this allows you to scale images in relation to pixels instead
    #of percentage of the size of the image.
    if "xscale" in self.layer.inPixels:
      scale[0] /= self.layer.drawing.pixelSize[0]
    if "yscale" in self.layer.inPixels:
      scale[1] /= self.layer.drawing.pixelSize[1]

    scale[1] = -scale[1]
    scale[0] *= w/vpc[0]
    scale[1] *= h/vpc[1]
    
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
        return
    if self.type == "font":
      self.layer.text = self.text[-1]
    else:
      if len(self.drawings) > 0:
        self.layer.drawing = self.drawings[-1]
      if len(self.rects) > 0:
        self.layer.rect = [float(i) for i in eval(self.rects[-1])]
      self.fixScale()
            
#effect that allows one to set the number of frames and
# have the layer loop through an animation               
class Animate(Effect):
  def __init__(self, layer, section):
    super(Animate, self).__init__(layer, section)
    
    self.frames = self.get("frames", int, 1)
    self.fps = self.get("fps", int, 30)
    
    self.currentFrame = 1
    self.transitionTime = self.get("transitionTime", float, 512.0)
    
    self.condition = self.getexpr("condition", "True")

  #fixes the scale after the rect is changed
  def fixScale(self):
    scale = [self.layer.scale[0]/self.frames, self.layer.scale[1]]
    self.layer.scale = scale
        
  #adjusts the rate to the current fps
  def updateRate(self):
    self.rate = float(self.frames) / (self.transitionTime * (max(self.engine.clock.get_fps(), _minFPS)) / 1000.0)
      
  def update(self):
    
    self.updateRate()
    
    if bool(eval(self.condition)) and self.currentFrame < self.frames:
      self.currentFrame += self.rate
    else:
      self.currentFrame = 1
    
    rect = self.layer.rect
    
    rect = [(rect[1] - rect[0])/self.frames * (int(self.currentFrame) - 1),
            (rect[1] - rect[0])/self.frames * (int(self.currentFrame)),
            rect[2], rect[3]]
            
    self.layer.rect = rect
    
    self.fixScale()
        
class Rockmeter(ConfigGetMixin):
  def __init__(self, guitarScene, configFileName, coOp = False):

    self.scene            = guitarScene
    self.engine           = guitarScene.engine
    self.layers = {}
    self.sharedlayers = [] #these layers are for coOp use only

    self.coOp = coOp
    self.config = LinedConfigParser()
    self.config.read(configFileName)

    self.themename = self.engine.data.themeLabel
    
    # Build the layers
    for i in range(99):
      types = [
               "Image",
               "Text",
               "Circle"
              ]
      for t in types:
        self.section = "layer%d:%s" % (i, t)
        if not self.config.has_section(self.section):
          continue
        else:
          if t == types[1]:
            self.createFont(self.section, i)
          elif t == types[2]:
            self.createCircle(self.section, i)
          else:
            self.createImage(self.section, i)
          break

  #adds a layer to the rockmeter's list
  def addLayer(self, layer, number, shared = False):
    if shared:
      self.sharedlayers.append(layer)
    else:
      if layer:
        self.layers[number] = layer

  def loadLayerFX(self, layer, section):
    section = section.split(":")[0]
    types = ["Slide", "Rotate", "Replace", "Fade", "Animate"]
    for i in range(5):  #maximum of 5 effects per layer
      for t in types:
        fxsection = "%s:fx%d:%s" % (section, i, t)
        if not self.config.has_section(fxsection):
          continue
        else:
          if t == types[0]:
            layer.effects.append(Slide(layer, fxsection))
#          elif t == types[1]:
#            layer.effects.append(Rotate(layer, fxsection))
          elif t == types[2]:
            layer.effects.append(Replace(layer, fxsection))
          elif t == types[3]:
            layer.effects.append(Fade(layer, fxsection))
          else:
            layer.effects.append(Animate(layer, fxsection))
          break #only allow type per effect number
            
      
  def createFont(self, section, number):

    font  = self.get("font", str, "font")
    layer = FontLayer(self, section, font)

    layer.text      = self.getexpr("text")
    layer.shared    = self.get("shared",   bool, False)
    layer.condition = self.getexpr("condition", "True")
    layer.inPixels  = self.get("inPixels", str, "").split("|")
    
    self.loadLayerFX(layer, section)

    self.addLayer(layer, number, layer.shared)

  def createImage(self, section, number):
    
    texture   = self.get("texture")
    drawing   = os.path.join("themes", self.themename, "rockmeter", texture)
    layer     = ImageLayer(self, section, drawing)

    layer.shared    = self.get("shared", bool, False)
    layer.condition = self.getexpr("condition", "True")
    layer.inPixels  = self.get("inPixels", str, "").split("|")

    layer.rect      = self.getexpr("rect", "(0,1,0,1)")

    self.loadLayerFX(layer, section)
            
    self.addLayer(layer, number, layer.shared)

  def createCircle(self, section, number):
    
    texture   = self.get("texture")
    drawing   = os.path.join("themes", self.themename, "rockmeter", texture)
    layer     = CircleLayer(self, section, drawing)

    layer.shared    = self.get("shared", bool, False)
    layer.condition = self.getexpr("condition", "True")
    layer.inPixels  = self.get("inPixels", str, "").split("|")

    layer.rect      = self.getexpr("rect", "(0,1,0,1)")

    self.loadLayerFX(layer, section)

    self.addLayer(layer, number, layer.shared)

  #because time is not player specific it's best to update it only once per cycle
  def updateTime(self):
    global songLength, minutesSongLength, secondsSongLength
    global minutesCountdown, secondsCountdown, minutes, seconds
    global position, countdownPosition, progress

    scene = self.scene

    songLength        = scene.lastEvent
    position          = scene.getSongPosition()
    countdownPosition = songLength - position
    progress          = float(position)/float(songLength)
    if progress < 0:
        progress = 0
    elif progress > 1:
        progress = 1

    minutesCountdown, secondsCountdown   = (countdownPosition / 60000, (countdownPosition % 60000) / 1000)
    minutes, seconds                     = (position / 60000, (position % 60000) / 1000)
    minutesSongLength, secondsSongLength = (songLength / 60000, (songLength % 60000) / 1000)

  #this updates all the usual global variables that are handled by the rockmeter
  #these are all player specific
  def updateVars(self, playerNum):
    global score, rock, streak, streakMax, power, stars, partialStars, multiplier, bassgroove, boost, player
    scene = self.scene
    player = scene.instruments[playerNum]

    #this is here for when I finally get coOp worked in
    if self.coOp:
      score = scene.coOpScoreCard.score
      stars = scene.coOpScoreCard.stars
      partialStars = scene.coOpScoreCard.starRatio
      rock  = scene.rock[scene.coOpPlayerMeter] / scene.rockMax
    else:
      score = scene.scoring[playerNum].score
      stars = scene.scoring[playerNum].stars
      partialStars = scene.scoring[playerNum].starRatio
      rock  = scene.rock[playerNum] / scene.rockMax

    streak = scene.scoring[playerNum].streak
    power  = player.starPower/100.0

    #allows for bassgroove
    if player.isBassGuitar:
      streakMax = 50    
    else:
      streakMax = 30

    if streak >= streakMax:
      multiplier = int(streakMax*.1) + 1
    else:
      multiplier = int(streak*.1) + 1

    boost = player.starPowerActive
    
    #doubles the multiplier number when starpower is activated
    if boost:
      multiplier *= 2
      
    if player.isBassGuitar and streak >= 40:
        bassgroove = True
    else:
        bassgroove = False
        
    #force bassgroove to false if it's not enabled
    if not scene.bassGrooveEnabled:
        bassgroove = False
        
  def render(self, visibility):
    self.updateTime()

    with self.engine.view.orthogonalProjection(normalize = True):
      for i,player in enumerate(self.scene.playerList):
        p = player.number
        self.updateVars(p)
        if p is not None:
          self.engine.view.setViewportHalf(self.scene.numberOfGuitars,p)
        else:
          self.engine.view.setViewportHalf(1,0)  
        for layer in self.layers.values():
          layer.render(visibility, p)

      self.engine.view.setViewportHalf(1,0)
      for layer in self.sharedlayers:
        layer.render(visibility, 0)

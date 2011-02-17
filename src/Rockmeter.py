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

import Config
import os

from Svg import ImgDrawing

import locale

#Blazingamer - new drawing code
#from Draw import *

from PIL import Image, ImageDraw, ImageOps
from OpenGL.GL import glColor3f

import math

#these are the variables for setting the alignment of text and images
#when setting them up in the rockmeter.ini you do not have
#to put it in all caps, the code will take care of that
#for you; however you do have to spell them right or it will
#give you an error.
LEFT   = 0
CENTER = 1
RIGHT  = 2
TOP    = 0
BOTTOM = 2

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

# A graphical rockmeter layer
# This is the base template for all rockmeter layer types
class Layer:
  def get(self, value, type = str, default = None):
    if self.config.has_option(self.section, value):
      return type(self.config.get(self.section, value))
    return default

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

    self.position    = [self.get("xpos", str, "0.0"), self.get("ypos", str, "0.0")]	
                                        #where on the screen to draw the layer
    self.angle       = self.get("angle", str, "0.0")
                                        #angle to rotate the layer (in degrees)
    self.scale       = [self.get("xscale", str, "1.0"), self.get("yscale", str, "1.0")]
                                        #how much to scale it by (width, height from 0.0 - 1.0)
    self.color       = self.get("color", str, "#FFFFFF")
                                        #color of the image (#FFFFFF is white on text, on images it is full color)
    self.condition   = True				#when should the image be shown (by default it will always be shown)
    self.alignment   = self.get("alignment", str, "center").upper()
                                        #alignment of the image (horizontal)
    self.valignment  = self.get("valignment", str, "center").upper()
                                        #alignment of the image (vertical)
    self.inPixels    = self.get("inPixels", str, "").split("|")
                                        #makes sure to properly scale/position the images in pixels instead of percent

    self.effects     = []               #various effects associated with the layer

    #these are the final values for the variables
    self.finals      = [[0,0],          #position
                        [0.0,0.0],      #scale
                        [0.0],          #angle
                        [1.0,1.0,1.0,1.0],
                                        #color
                        [CENTER,CENTER],#alignments
                        [True]]         #condition
                        
  # all variables that should be updated during the rendering process
  # should be in here just for sake of readablity and organization
  def updateLayer(self, playerNum):
    self.finals      = [[eval(self.position[0]),eval(self.position[1])],
                        [eval(self.scale[0]),eval(self.scale[1])],
                        eval(self.angle),
                        self.engine.theme.hexToColor(self.color),
                        [eval(self.alignment),eval(self.valignment)],
                        True]
     
  # should handle the final step of rendering the image
  # be sure if you have variables being updated in updateVars
  # to call updateVars and refresh them.  playerNum is *especially*
  # important if there is more than one player present.
  def render(self, visibility, playerNum):
    pass

 #A graphical stage layer that is used to render the rockmeter.
class ImageLayer(Layer):
  def __init__(self, stage, section, drawing):
    Layer.__init__(self, stage, section)

    #these are the images that are drawn when the layer is visible
    self.drawing = self.engine.loadImgDrawing(self, None, drawing)
    self.rect    = self.get("rect", str, "(0,1,0,1)")
                                #how much of the image do you want rendered (left, right, top, bottom)
    self.finals.append(self.rect)
    
  def updateLayer(self, playerNum):
    w, h, = self.engine.view.geometry[2:4]
    texture = self.drawing

    Layer.updateLayer(self, playerNum)
    
    rect = list(eval(self.rect))
    self.finals.append(rect)
    
    #all of this has to be repeated instead of using the base method
    #because now things can be calculated in relation to the image's properties

    scale = self.finals[1]
    scale[0] *=  (rect[1] - rect[0])
    scale[1] *=  (rect[3] - rect[2])
    
    #this allows you to scale images in relation to pixels instead
    #of percentage of the size of the image.
    if "xscale" in self.inPixels:
      scale[0] /= texture.pixelSize[0]
    if "yscale" in self.inPixels:
      scale[1] /= texture.pixelSize[1]

    scale[1] = -scale[1]
    scale[0] *= w/640.0
    scale[1] *= h/480.0
    
    self.finals[1] = scale
    
    position = self.finals[0]
    if "xpos" in self.inPixels:
      position[0] *= w/640.0
    else:        
      position[0] *= w

    if "ypos" in self.inPixels:
      position[1] *= h/480.0
    else:        
      position[1] *= h

    self.finals[0] = position
    
    self.finals[5] = bool(eval(self.condition))

  def render(self, visibility, playerNum):
    v = 1.0

    self.updateLayer(playerNum)
    for effect in self.effects:
      effect.update()

    coord      = self.finals[0]
    scale      = self.finals[1]
    rot        = self.finals[2]
    color      = self.finals[3]
    alignment  = self.finals[4][0]
    valignment = self.finals[4][1]
    drawing    = self.drawing
    rect       = self.finals[-1]
    
    #frameX  = self.frameX
    #frameY  = self.frameY

    if self.finals[5]:
      self.engine.drawImage(drawing, scale, coord, rot, color, rect, 
                            alignment = alignment, valignment = valignment)

#defines layers that are just font instead of images
class FontLayer(Layer): 
  def __init__(self, stage, section, font):
    Layer.__init__(self, stage, section)

    self.font        = self.engine.data.fontDict[font]
    self.text        = ""
    self.replace     = ""
    self.alignment   = self.get("alignment", str, "LEFT").upper()
    self.useComma    = self.get("useComma", bool, False)

    self.finals.append(self.text)
    
  def updateLayer(self, playerNum):
    w, h, = self.engine.view.geometry[2:4]
    
    text = eval(self.text)

    if self.useComma:
      text = locale.format("%d", text, grouping=True)
    else:
      text = str(text)

    wid, hgt = self.font.getStringSize(str(text))

    Layer.updateLayer(self, playerNum)

    self.finals.append(text)
    
    position = self.finals[0]
    if "xpos" in self.inPixels:
      position[0] /= 640.0
    if "ypos" in self.inPixels:
      position[1] /= 480.0
    
    #the viewport code for rendering for is a little awkward
    #instead of the bottom edge being at 1.0 it is at .75
    #by doing this people can use conventional positioning
    #while the code self adjusts the values
    position[1] *= .75
    #not only that but it's upside down
    position[1] = .75 - position[1]
    
    self.finals[0] = position
    
    self.finals[5] = bool(eval(self.condition))

  def render(self, visibility, playerNum):
    w, h, = self.stage.engine.view.geometry[2:4]
    v = 1.0

    self.updateLayer(playerNum)
    for effect in self.effects:
      effect.update()

    position = self.finals[0]
    alignment = self.finals[4][0]
    color = self.finals[3]
    condition = self.finals[5]
    glColor3f(*color)

    if condition:
      self.font.render(self.finals[-1], position, align = alignment)
        
#creates a layer that is shaped like a pie-slice/circle instead of a rectangle
class CircleLayer(Layer): 
  def __init__(self, stage, section, drawing):
    Layer.__init__(self, stage, section)

    #this number (between 0 and 1) determines how much
    #of the circle should be filled (0 to 360 degrees)
    self.ratio   = self.get("ratio", str, "1")
    self.finals.append(self.ratio)  

    self.engine.loadImgDrawing(self, "drawing", drawing)
  
    #these determine the size of the PIL pie-slice
    self.centerX   = self.drawing.width1()/2
    self.centerY   = self.drawing.height1()/2
    self.inRadius  = 0
    self.outRadius = self.drawing.width1()/2
    
    #generates all the images needed for the circle
    self.drawnOverlays = {}
    baseFillImageSize = self.drawing.pixelSize
    for degrees in range(0, 361, 5):
      image = Image.open(os.path.join("..", "data", drawing))
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
    w, h, = self.engine.view.geometry[2:4]
    texture = self.drawing

    ratio = eval(self.ratio)

    Layer.updateLayer(self, playerNum)
    
    self.finals.append(ratio)
    scale = self.finals[1]
    
    #this allows you to scale images in relation to pixels instead
    #of percentage of the size of the image.
    if "xscale" in self.inPixels:
      scale[0] /= texture.pixelSize[0]
    if "yscale" in self.inPixels:
      scale[1] /= texture.pixelSize[1]

    scale[1] = -scale[1]
    scale[0] *= w/640.0
    scale[1] *= h/480.0
    
    self.finals[1] = scale
    
    position = self.finals[0]
    
    if "xpos" in self.inPixels:
      position[0] *= w/640.0
    else:
      position[0] *= w

    if "ypos" in self.inPixels:
      position[1] *= h/480.0
    else:        
      position[1] *= h

    self.finals[0] = position
    
    self.finals[5] = bool(eval(self.condition))

  def render(self, visibility, playerNum):
    w, h, = self.stage.engine.view.geometry[2:4]
    v = 1.0

    self.updateLayer(playerNum)
    for effect in self.effects:
      effect.update()

    coord     = self.finals[0]
    scale     = self.finals[1]
    rot       = self.finals[2]
    color     = self.finals[3]
    alignment = self.finals[4][0]
    ratio     = self.finals[-1]
    if self.condition:
      degrees = int(360*ratio) - (int(360*ratio) % 5)
      self.engine.drawImage(self.drawnOverlays[degrees], scale, 
                            coord, rot, color, alignment = alignment)


#this is just a template for effects                
class Effect:
  def get(self, value, type = str, default = None):
    if self.config.has_option(self.section, value):
      return type(self.config.get(self.section, value))
    return default

  def __init__(self, layer, section):
    self.layer = layer
    self.config = layer.config
    self.section = section
    
    self.condition = True

  def update(self):
    pass

#slides the layer from one spot to another
#in a set period of time when the condition is met
class Slide(Effect):
  def __init__(self, layer, section):
    Effect.__init__(self, layer, section)

    self.startCoord = [eval(self.get("startX", str, "0.0")), eval(self.get("startY", str, "0.0"))]
    self.endCoord   = [eval(self.get("endX",   str, "0.0")), eval(self.get("endY",   str, "0.0"))]

    self.position = [eval(self.get("startX", str, "0.0")), eval(self.get("startY", str, "0.0"))]

    self.inPixels  = self.get("inPixels", str, "").split("|")

    self.condition = self.get("condition", str, "True")
    
    w, h, = self.layer.engine.view.geometry[2:4]

    if "startX" in self.inPixels:
      self.position[0] *= w/640.0
    else:
      self.position[0] *= w

    if "startY" in self.inPixels:
      self.position[1] *= h/480.0
    else:
      self.position[1] *= h

    if "endX" in self.inPixels:
      self.endCoord[0] *= w/640.0
    else:
      self.endCoord[0] *= w

    if "endY" in self.inPixels:
      self.endCoord[1] *= h/480.0
    else:
      self.endCoord[1] *= h


    self.reverse = bool(eval(self.get("reverse", str, "True")))   

    #how long it takes for the transition to take place
    self.transitionTime = self.get("transitionTime", float, 512.0)

    self.slideX = (self.endCoord[0] - self.startCoord[0])/self.transitionTime
    self.slideY = (self.endCoord[1] - self.startCoord[1])/self.transitionTime

  def update(self):
    condition = bool(eval(self.condition))

    if condition:
      if self.position[0] < self.endCoord[0]:
        self.position[0] += self.slideX
      if self.position[1] < self.endCoord[1]:
        self.position[1] += self.slideY
    else:
      if self.reverse:
        if self.position[0] > self.startCoord[0]:
          self.position[0] -= self.slideX
        if self.position[1] > self.startCoord[1]:
          self.position[1] -= self.slideY
      else:  
        self.position = self.startCoord
    
    self.layer.finals[0] = [self.position[0], self.position[1]]

#replaces the image of the layer when the condition is met
class Replace(Effect):
  def __init__(self, layer, section):
    Effect.__init__(self, layer, section)

    if isinstance(layer, ImageLayer):
      self.drawings  = []
      self.rects = []
      if not self.get("texture") == None:
        texture   = self.get("texture").strip().split("|")
        for tex in texture:
          path   = os.path.join("themes", layer.stage.themename, "rockmeter", tex)
          drawing = layer.engine.loadImgDrawing(self, None, path)
          self.drawings.append(drawing)
      self.drawings.append(layer.drawing)
      if not self.get("rect") == None:
        rects = self.get("rect").split("|")
        for rect in rects:
          self.rects.append(eval(rect))
      self.rects.append(eval(layer.rect))
      self.type = "image"
    elif isinstance(layer, FontLayer):
      self.font = self.engine.data.fontDict[self.get("font")]
      self.text = self.get("text").split("|")
      self.type = "font"

    self.conditions = self.get("condition", str, "True").split("|")
    
  #fixes the scale after the rect is changed
  def fixScale(self):
    w, h, = self.layer.engine.view.geometry[2:4]
    
    rect = self.layer.finals[-1]
    scale     = [eval(self.layer.get("xscale", str, "0.5")), 
                 eval(self.layer.get("yscale", str, "0.5"))]
    scale[0] *=  (rect[1] - rect[0])
    scale[1] *=  (rect[3] - rect[2])
    #this allows you to scale images in relation to pixels instead
    #of percentage of the size of the image.
    if "xscale" in self.layer.inPixels:
      scale[0] /= self.layer.drawing.pixelSize[0]
    if "yscale" in self.layer.inPixels:
      scale[1] /= self.layer.drawing.pixelSize[1]

    scale[1] = -scale[1]
    scale[0] *= w/640.0
    scale[1] *= h/480.0
    
    self.layer.finals[1] = scale
    
  def update(self):

    if self.type == "font":
      self.layer.finals[6] = self.text[-1]
    else:
      self.layer.drawing = self.drawings[-1]
    for i, cond in enumerate(self.conditions):
      if bool(eval(cond)):
        if self.type == "font":
          self.layer.finals[-1] = self.text[i]
        else:
          if len(self.drawings) > 1:
            self.layer.drawing = self.drawings[i]
          if len(self.rects) > 1:
            self.layer.finals[-1] = self.rects[i]
          self.fixScale()
        break
        
class Rockmeter:
  def get(self, value, type = str, default = None):
    if self.config.has_option(self.section, value):
      return type(self.config.get(self.section, value))
    return default

  def __init__(self, guitarScene, configFileName, coOp = False):

    self.scene            = guitarScene
    self.engine           = guitarScene.engine
    self.layers = []
    self.sharedlayers = [] #these layers are for coOp use only

    self.coOp = coOp
    self.config = Config.MyConfigParser()
    self.config.read(configFileName)

    self.themename = self.engine.data.themeLabel
    
    # Build the layers
    for i in range(99):
      types = [
               "Image",
               "Text",
               "Circle"
              ]
      exist = False
      for t in types:
        self.section = "layer%d:%s" % (i, t)
        if not self.config.has_section(self.section):
          continue
        else:
          exist = True
          if t == types[1]:
            self.createFont(self.section)
          elif t == types[2]:
            self.createCircle(self.section)
          else:
            self.createImage(self.section)
          break

  def addLayer(self, layer, shared = False):
    if shared:
      self.sharedlayers.append(layer)
    else:
      if layer:
        self.layers.append(layer)

  def loadLayerFX(self, layer, section):
    section = section.split(":")[0]
    types = ["Slide", "Rotate", "Replace", "Fade"]
    for i in range(5):
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
#          else:
#            layer.effects.append(Fade(layer, fxsection))
      
  def createFont(self, section):

    font  = self.get("font")
    layer = FontLayer(self, section, font)

    layer.text      = self.get("text")
    layer.shared    = self.get("shared",   bool, False)
    layer.condition = self.get("condition", str, "True")
    layer.inPixels  = self.get("inPixels", str, "").split("|")
    
    self.loadLayerFX(layer, section)

    Wid, Hgt = self.engine.data.fontDict[font].getStringSize(layer.text)

    self.addLayer(layer, layer.shared)

  def createImage(self, section):
    
    texture   = self.get("texture")
    drawing   = os.path.join("themes", self.themename, "rockmeter", texture)
    layer     = ImageLayer(self, section, drawing)

    layer.shared    = self.get("shared", bool, False)
    layer.condition = self.get("condition", str, "True")
    layer.inPixels  = self.get("inPixels", str, "").split("|")

    layer.rect      = self.get("rect", str, "(0,1,0,1)")

    self.loadLayerFX(layer, section)
            
    self.addLayer(layer, layer.shared)

  def createCircle(self, section):
    
    texture   = self.get("texture")
    drawing   = os.path.join("themes", self.themename, "rockmeter", texture)
    layer     = CircleLayer(self, section, drawing)

    layer.shared    = self.get("shared", bool, False)
    layer.condition = self.get("condition", str, "True")
    layer.inPixels  = self.get("inPixels", str, "").split("|")

    layer.rect      = self.get("rect", str, "(0,1,0,1)")

    self.loadLayerFX(layer, section)

    self.addLayer(layer, layer.shared)

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
    global score, rock, streak, streakMax, power, stars, partialStars, multiplier, player
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

    #doubles the multiplier number when starpower is activated
    if player.starPowerActive:
      multiplier *= 2

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
        for layer in self.layers:
          layer.render(visibility, p)

      self.engine.view.setViewportHalf(1,0)
      for layer in self.sharedlayers:
        layer.render(visibility, 0)

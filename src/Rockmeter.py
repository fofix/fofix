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

import Config
import os

from OpenGL.GL import *

import locale

#Blazingamer - new drawing code
#from Draw import *

#these are the variables for setting the alignment of text and images
#when setting them up in the rockmeter.ini you do not have
#to put it in all caps, the code will take care of that
#for you; however you do have to spell them right or it will
#give you an error.
LEFT   = 0
CENTER = 1
RIGHT  = 2

#by making these global for the class, all layers that rely on 
#these numbers will no longer have to have them be independent per
#instance of the layer.  This also makes it easier to work with the
#variables in the rockmeter.ini for you no longer have to use self
#to refer to theme, instead it has a more friendly and logical setup.
player = None

score = 0
streak = 0
streakMax = 0
power = 0
stars = 0
partialStars = 0
rock = 0
multiplier = 0

minutes = 0
seconds = 0
minutesCountdown = 1
secondsCountdown = 1
songLength = 1
minutesSongLength = 0
secondsSongLength = 0
position = 0
countdownPosition = 1
progress = 0.0         #this gives a percentage (between 0 and 1) 
                       #of how far the song has played

# A graphical rockmeter layer
# This is the base template for all rockmeter layer types
class Layer:

  def __init__(self, stage, section):
    self.stage       = stage			#The rockmeter
    self.engine      = stage.engine		#Game Engine
    self.config      = stage.config     #the rockmeter.ini
    self.section     = section          #the section of the rockmeter.ini involving this layer

    self.position    = (0.0, 0.0)		#where on the screen to draw the layer
    self.angle       = 0.0				#angle to rotate the layer (in degrees)
    self.scale       = (1.0, 1.0)		#how much to scale it by (width, height from 0.0 - 1.0)
    self.color       = "#FFFFFF"		#color of the image (#FFFFFF is white on text, on images it is full color)
    self.rect        = (0,1,0,1)		#how much of the image do you want rendered (left, right, top, bottom)
    self.condition   = True				#when should the image be shown (by default it will always be shown)
    self.inPixels    = []               #makes sure to properly scale/position the images in pixels instead of percent

    self.effects     = []

  # all variables that should be updated during the rendering process
  # should be in here just for sake of readablity and organization
  def updateLayer(self, playerNum):
    pass
            
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

    def get(value, type = str, default = None):
      if self.config.has_option(self.section, value):
        return type(self.config.get(self.section, value))
      return default
    
    self.engine.loadImgDrawing(self, "drawing", drawing)
    #These are for when I get the ImgObj working
    #frameX        = get("frameX", int, 1)
    #frameY        = get("frameY", int, 1)
    #loadImage(self, "drawing", drawing, frameX, frameY)	#this is the image that is loaded for the layer
    
  def updateLayer(self, playerNum):
    w, h, = self.engine.view.geometry[2:4]
    texture = self.drawing

    def get(value, type = str, default = None):
      if self.config.has_option(self.section, value):
        return type(self.config.get(self.section, value))
      return default

    self.rect        = list(eval(get("rect", str, "(0,1,0,1)")))

    #all of this has to be repeated instead of using the base method
    #because now things can be calculated in relation to the image's properties
    self.position  = [eval(get("xpos", str, "0.0")),    eval(get("ypos", str, "0.0"))]
    self.scale     = [eval(get("xscale", str, "0.5")),  eval(get("yscale", str, "0.5"))]

    self.angle       = get("angle", float, 0.0)
    self.color       = get("color", str, "#FFFFFF")

    self.condition = bool(eval(get("condition", str, "True")))

    self.alignment = eval(get("alignment", str, "center").upper())

    self.scale[0] *=  (self.rect[1] - self.rect[0])
    self.scale[1] *=  (self.rect[3] - self.rect[2])
    #this allows you to scale images in relation to pixels instead
    #of percentage of the size of the image.
    if "xscale" in self.inPixels:
      self.scale[0] /= texture.pixelSize[0]
    if "yscale" in self.inPixels:
      self.scale[1] /= texture.pixelSize[1]

    self.scale[1] = -self.scale[1]
    self.scale[0] *= w/640.0
    self.scale[1] *= h/480.0
    
    if "xpos" in self.inPixels:
      self.position[0] *= w/640.0
    else:
      self.position[0] *= w

    if "ypos" in self.inPixels:
      self.position[1] *= h/480.0
    else:        
      self.position[1] *= h


    #try:
    #    self.frameX      = get("currentFrameX", int, 1)
    #except:
    #    self.frameX      = eval(get("currentFrameX"))

    #try:
    #    self.frameY      = get("currentFrameY", int, 1)
    #except:
    #    self.frameY      = eval(get("currentFrameY"))


  def render(self, visibility, playerNum):
    v = 1.0

    self.updateLayer(playerNum)
    for effect in self.effects:
      effect.update()

    rect    = self.rect

    coord     = self.position
    scale     = self.scale
    rot       = self.angle
    color     = self.engine.theme.hexToColor(self.color)
    alignment = self.alignment
    #frameX  = self.frameX
    #frameY  = self.frameY

    if self.condition:
      self.engine.drawImage(self.drawing, scale, coord, rot, color, rect, alignment = alignment)

#defines layers that are just font instead of images
class FontLayer(Layer): 
  def __init__(self, stage, section, font):
    Layer.__init__(self, stage, section)

    self.font        = self.engine.data.fontDict[font]
    self.text        = ""
    self.replace     = ""
    self.alignment   = LEFT
    self.useComma    = False

    self.color       = "#FFFFFF"

  def updateLayer(self, playerNum):
    w, h, = self.engine.view.geometry[2:4]

    def get(value, type = str, default = None):
      if self.config.has_option(self.section, value):
        return type(self.config.get(self.section, value))
      return default

    self.text = eval(get("text"))
    self.color = get("color", str, "#FFFFFF")

    self.alignment = eval(get("alignment", str, "left").upper())

    if self.useComma:
      self.text = locale.format("%d", self.text, grouping=True)
    else:
      self.text = str(self.text)

    wid, hgt = self.font.getStringSize(str(self.text))

    self.position  = [eval(get("xpos", str, "0.0")),    eval(get("ypos", str, "0.0"))]
    self.scale     = [eval(get("xscale", str, "1.0")),  eval(get("yscale", str, "1.0"))]

    self.angle       = get("angle", float, 0.0)
    self.color       = get("color", str, "#FFFFFF")

    self.condition   = bool(eval(get("condition", str, "True")))

    self.useComma = get("useComma", bool, False)

    if "xpos" in self.inPixels:
      self.position[0] /= 640.0
    if "ypos" in self.inPixels:
      self.position[1] /= 480.0

    #the viewport code for rendering for is a little awkward
    #instead of the bottom edge being at 1.0 it is at .75
    #by doing this people can use conventional positioning
    #while the code self adjusts the values
    self.position[1] *= .75
    #not only that but it's upside down
    self.position[1] = .75 - self.position[1]
  def render(self, visibility, playerNum):
    w, h, = self.stage.engine.view.geometry[2:4]
    v = 1.0

    self.updateLayer(playerNum)
    for effect in self.effects:
      effect.update()
    
    glColor3f(*self.engine.theme.hexToColor(self.color))

    if self.condition:
      self.font.render(self.text, (self.position[0], self.position[1]), align = self.alignment)

#this is just a template for effects                
class Effect:
  def __init__(self, layer, section):
    pass

  def update(self):
    pass

class Slide(Effect):
  def __init__(self, layer, section):
    self.layer = layer
    self.config = layer.config
    self.section = section

    def get(value, type = str, default = None):
      if self.config.has_option(self.section, value):
        return type(self.config.get(self.section, value))
      return default
    
    self.condition = True

    self.startCoord = [eval(get("startX", str, "0.0")), eval(get("startY", str, "0.0"))]
    self.endCoord   = [eval(get("endX",   str, "0.0")), eval(get("endY",   str, "0.0"))]

    self.position = [eval(get("startX", str, "0.0")), eval(get("startY", str, "0.0"))]

    self.inPixels  = get("inPixels", str, "").split("|")

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


    self.reverse = bool(eval(get("reverse", str, "True")))   

    #how long it takes for the transition to take place
    self.transitionTime = get("transitionTime", float, 512.0)

  def update(self):
    def get(value, type = str, default = None):
      if self.config.has_option(self.section, value):
        return type(self.config.get(self.section, value))
      return default

    self.condition = bool(eval(get("condition", str, "True")))

    slideX = (self.endCoord[0] - self.startCoord[0])/self.transitionTime
    slideY = (self.endCoord[1] - self.startCoord[1])/self.transitionTime

    if self.condition:
      if self.position[0] < self.endCoord[0]:
        self.position[0] += slideX
      if self.position[1] < self.endCoord[1]:
        self.position[1] += slideY
    else:
      if self.reverse:
        if self.position[0] > self.startCoord[0]:
          self.position[0] -= slideX
        if self.position[1] > self.startCoord[1]:
          self.position[1] -= slideY
      else:  
        self.position = self.startCoord
    
    self.layer.position = [self.position[0], self.position[1]]

class Rockmeter:
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
               "Text"
              ]
      exist = False
      for t in types:
        section = "layer%d:%s" % (i, t)
        if not self.config.has_section(section):
          continue
        else:
          exist = True
          if t == types[1]:
            self.createFont(section)
          else:
            self.createImage(section)
          break

  def addLayer(self, layer, shared = False):
    if shared:
      self.sharedlayers.append(layer)
    else:
      if layer:
        self.layers.append(layer)

  def createFont(self, section):
    def get(value, type = str, default = None):
      if self.config.has_option(section, value):
        return type(self.config.get(section, value))
      return default

    font  = get("font")
    layer = FontLayer(self, section, font)

    layer.text      = get("text")
    layer.shared    = get("shared",   bool, False)
    layer.condition = get("condition", str, "True")
    layer.inPixels  = get("inPixels", str, "").split("|")

    section = section.split(":")[0]
    types = ["Slide", "Rotate", "Fade"]
    for i in range(5):
      for t in types:
        fxsection = "%s:fx%d:%s" % (section, i, t)
        if not self.config.has_section(fxsection):
          continue
        else:
          if t == types[0]:
            layer.effects.append(Slide(layer, fxsection))
#          else if t == types[1]:
#            layer.effects.append(Rotate(layer, fxsection))
#          else:
#            layer.effects.append(Fade(layer, fxsection))


    Wid, Hgt = self.engine.data.fontDict[font].getStringSize(layer.text)

    self.addLayer(layer, layer.shared)

  def createImage(self, section):
    def get(value, type = str, default = None):
      if self.config.has_option(section, value):
        return type(self.config.get(section, value))
      return default

    
    texture   = get("texture")
    drawing   = os.path.join("themes", self.themename, "rockmeter", texture)
    layer     = ImageLayer(self, section, drawing)

    layer.shared    = get("shared", bool, False)
    layer.condition = get("condition", str, "True")
    layer.inPixels  = get("inPixels", str, "").split("|")

    layer.rect      = eval(get("rect", str, "(0,1,0,1)"))

    section = section.split(":")[0]
    types = ["Slide", "Rotate", "Fade"]
    for i in range(5):
      for t in types:
        fxsection = "%s:fx%d:%s" % (section, i, t)
        if not self.config.has_section(fxsection):
          continue
        else:
          if t == types[0]:
            layer.effects.append(Slide(layer, fxsection))
#          else if t == types[1]:
#            layer.effects.append(Rotate(layer, fxsection))
#          else:
#            layer.effects.append(Fade(layer, fxsection))
            
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
    global score, stars, rock, streak, streakMax, power, multiplier, player
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

    self.engine.view.setOrthogonalProjection(normalize = True)
    try:
      for i,player in enumerate(self.scene.playerList):
        p = player.guitarNum
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

    finally:
      self.engine.view.resetProjection()


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
import math
import Log
import os
import random   #MFH - needed for new stage background handling

import Version # Provides dataPath

from OpenGL.GL import *

#stump: needed for continuous star fillup
from PIL import Image, ImageDraw
from Svg import ImgDrawing

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
score = 0
streak = 0
streakMax = 0
power = 0
stars = 0
rock = 0
multiplier = 0

minutes = 0
seconds = 0
minutesCountdown = 0
secondsCountdown = 0
songLength = 0

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
    w, h, = self.stage.engine.view.geometry[2:4]
    texture = self.drawing

    def get(value, type = str, default = None):
      if self.config.has_option(self.section, value):
        return type(self.config.get(self.section, value))
      return default

    self.rect        = eval(get("rect", str, "(0,1,0,1)"))

    #all of this has to be repeated instead of using the base method
    #because now things can be calculated in relation to the image's properties
    try:    self.position  = [get("xpos",   float, 0.0), get("ypos",   float, 0.0)]
    except: self.position  = [eval(get("xpos")),    eval(get("ypos"))]

    try:    self.scale     = [get("xscale", float, 1.0), get("yscale", float, 1.0)]
    except: self.scale     = [eval(get("xscale")),  eval(get("yscale"))]

    self.angle       = get("angle", float, 0.0)
    self.color       = get("color", str, "#FFFFFF")

    self.condition = bool(eval(get("condition", str, "True")))

    self.alignment = eval(get("alignment", str, "center").upper())

    #this allows you to scale images in relation to pixels instead
    #of percentage of the size of the image.
    if self.scale[0] > 1.0:
      self.scale[0] /= texture.pixelSize[0]
    if self.scale[1] > 1.0:
      self.scale[1] /= texture.pixelSize[1]
    self.scale[0] *=  (self.rect[1] - self.rect[0])
    self.scale[1] *= -(self.rect[3] - self.rect[2])

    if not self.position[0] > 1.0:
      self.position[0] *= w
    if not self.position[1] > 1.0:
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
      #drawImage(self.drawing, coord, scale, rot, color, rect, frameX, frameY)

#defines layers that are just font instead of images
class FontLayer(Layer): 
  def __init__(self, stage, section, font):
    Layer.__init__(self, stage, section)

    self.font        = self.engine.data.fontDict[font]
    self.text        = ""
    self.replace     = ""
    self.alignment   = LEFT

    self.color       = "#FFFFFF"

  def updateLayer(self, playerNum):
    w, h, = self.stage.engine.view.geometry[2:4]

    def get(value, type = str, default = None):
      if self.config.has_option(self.section, value):
        return type(self.config.get(self.section, value))
      return default

    try:    self.position  = [get("xpos",   float, 0.0), get("ypos",   float, 0.0)]
    except: self.position  = [eval(get("xpos")),    eval(get("ypos"))]

    try:    self.scale     = [get("xscale", float, 1.0), get("yscale", float, 1.0)]
    except: self.scale     = [eval(get("xscale")),  eval(get("yscale"))]

    self.angle       = get("angle", float, 0.0)
    self.color       = get("color", str, "#FFFFFF")

    self.condition   = bool(eval(get("condition", str, "True")))

    self.text = str(eval(get("text")))
    self.color = get("color", str, "#FFFFFF")

    if self.position[0] > 1.0:
      self.position[0] /= w
    if self.position[1] > 1.0:
      self.position[1] /= h

  def render(self, visibility, playerNum):
    w, h, = self.stage.engine.view.geometry[2:4]
    v = 1.0

    self.updateLayer(playerNum)
    
    wid, hgt = self.font.getStringSize(str(self.text))

    glColor3f(*self.engine.theme.hexToColor(self.color))

    if self.condition:
      self.font.render(str(self.text), (self.position[0], self.position[1]), align = self.alignment)
                
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
          if t == "Text":
            self.createFont(section)
          else:
            self.createImage(section)
          break

  def addLayer(self, layer, shared = False):
    if shared and self.coOp:
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

    layer.xres      = get("xres", int, 256)
    layer.yres      = get("yres", int, 256)
    layer.text      = get("text")
    layer.shared    = get("shared", bool, False)
    layer.condition = get("condition", str, "True")

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

    layer.xres      = get("xres", int, 256)
    layer.yres      = get("yres", int, 256)
    layer.shared    = get("shared", bool, False)
    layer.condition = get("condition", str, "True")

    layer.rect      = eval(get("rect", str, "(0,1,0,1)"))
            
    self.addLayer(layer, layer.shared)

  #because time is not player specific it's best to update it only once per cycle
  def updateTime(self):
    global songLength, minutesCountdown, secondsCountdown, minutes, seconds    
    scene = self.scene

    songLength = scene.lastEvent
    pos = scene.getSongPosition()
    countdownPos = songLength - pos

    minutesCountdown, secondsCountdown = (countdownPos / 60000, (countdownPos % 60000) / 1000)
    minutes, seconds = (pos / 60000, (pos % 60000) / 1000)

  #this updates all the usual global variables that are handled by the rockmeter
  #these are all player specific
  def updateVars(self, playerNum):
    global score, stars, rock, streak, streakMax, power, multiplier
    scene = self.scene
    player = scene.instruments[playerNum]

    #this is here for when I finally get coOp worked in
    if self.coOp:
      score = scene.coOpScoreCard.score
      stars = scene.coOpScoreCard.stars
      rock  = scene.rock[scene.coOpPlayerMeter] / scene.rockMax
    else:
      score = scene.scoring[playerNum].score
      stars = scene.scoring[playerNum].stars
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


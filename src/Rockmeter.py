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
import Theme
import os
import random   #MFH - needed for new stage background handling

import Version # Provides dataPath

from OpenGL.GL import *

class Layer(object):  #A graphical stage layer that is used to render the rockmeter.
  def __init__(self, stage, drawing):

    self.fontlayer   = False
    self.stage       = stage
    self.engine      = stage.engine
    self.drawing     = drawing
    self.position    = (0.0, 0.0)
    self.angle       = 0.0
    self.scale       = (1.0, 1.0)
    self.color       = "#FFFFFF"
    self.rect        = (0,1,0,1)
    self.effects     = []
    self.canrender   = 0
    self.rendernum   = 1

  def render(self, visibility):
    w, h, = self.stage.engine.view.geometry[2:4]
    v = 1.0
    for i,player in enumerate(self.stage.scene.playerList):
      p = player.guitarNum
      if p is not None:
        self.engine.view.setViewport(self.stage.scene.numberOfGuitars,p)  
      else:
        self.engine.view.setViewport(1,0)  

      if (self.canrender == 0 or (self.canrender == 1 and self.engine.config.get("coffee", "failingEnabled") == True)
      or (self.canrender == 2 and self.engine.config.get("coffee", "failingEnabled") == False)) and self.drawing:
        self.engine.drawImage(self.drawing, scale = (self.scale[0], self.scale[1]), 
                          coord = (self.position[0] * w, self.position[1] * h), 
                          rot = self.angle, color = Theme.hexToColor(self.color), rect = self.rect, 
                          stretched = 0)

      # Blend in all the effects
      for effect in self.effects:
        effect.apply(i)

class FontLayer(object): #defines layers that are just font instead of images
  def __init__(self, stage, section, font):

    self.fontlayer   = True
    self.stage       = stage
    self.engine      = stage.engine
    self.config      = stage.config
    self.section     = section

    score = 0
    streak = 0
    power = 0
    stars = 0
    rock = 0
    multiplier = 0

    self.font        = self.engine.data.fontDict[font]
    self.text        = ""
    self.position    = (0.0, 0.0)
    self.scale       = (1.0, 1.0)
    self.replace     = ""
    self.effects     = []

    def get(value, type = str, default = None):
      if self.config.has_option(self.section, value):
        return type(self.config.get(self.section, value))
      return default

    self.color = get("color",   str, "#FFFFFF")

  def render(self, visibility):
    w, h, = self.stage.engine.view.geometry[2:4]
    v = 1.0

    def get(value, type = str, default = None):
      if self.config.has_option(self.section, value):
        return type(self.config.get(self.section, value))
      return default

    for i,player in enumerate(self.stage.scene.playerList):
      p = player.guitarNum
      if p is not None:
        self.engine.view.setViewport(self.stage.scene.numberOfGuitars,p)  
      else:
        self.engine.view.setViewport(1,0)  

    for i in range(len(self.stage.scene.playerList)):
      score = self.stage.scene.scoring[i].score
      streak = self.stage.scene.scoring[i].streak
      power = self.stage.scene.instruments[i].starPower/100.0
      stars = self.stage.scene.scoring[i].stars
      rock = self.stage.scene.rock[i] / self.stage.scene.rockMax
      if streak >= 30:
        multiplier = 4
      else:
        multiplier = int(streak*.1) + 1

      self.text = eval(get("text"))
      self.replace    = get("replace")

      if self.replace != None:
        self.replace = self.replace.split(";")
        for replace in self.replace:
          self.text = str(self.text).replace(replace.split(",")[0],replace.split(",")[1])

      wid, hgt = self.font.getStringSize(str(self.text))

      try:  self.position    = (get("xpos",   float, 0.0), get("ypos",   float, 0.0))
      except:  self.position    = (eval(get("xpos")), eval(get("ypos")))
      glColor3f(*Theme.hexToColor(self.color))

      self.font.render(str(self.text), self.position)

class SPLightsLayer(object):  #Layer for specifically the SP Lights
  def __init__(self, stage, drawing, playernum):

    self.fontlayer   = False
    self.stage       = stage
    self.engine      = stage.engine
    self.drawing     = drawing

    self.canrender   = 0
    self.rendernum   = 1

    self.xstatic = [0.772, 0.795, 0.822]
    self.ystatic = [0.284, 0.312, 0.329]
    self.xstart = [0.841680344, 0.841680344, 0.851971546]
    self.ystart = [0.202291056, 0.205626286, 0.20994647]
    self.xend = [0.867126494, 0.902359625, 0.943112688]
    self.yend = [0.34490625, 0.333114583, 0.302322917]

    self.x = self.xstatic + self.xstart
    self.y = self.ystatic + self.ystart
      
    self.angle = [.87, .58, .37, 0, -.34, -.70]
    self.scale = (23.0000, 32.0000)
    self.playernum = playernum

  def render(self, visibility):
    w, h, = self.stage.engine.view.geometry[2:4]
    v = 1.0

    starPowerAmount = self.stage.scene.instruments[self.playernum].starPower
    for i in range(0, 6):
      if starPowerAmount >= 100:
        lightVis = 1
      else:
        lightVis = (starPowerAmount-(i*16.6))*.166

      if starPowerAmount >= 50 or self.stage.scene.instruments[self.playernum].starPowerActive:
        self.rect = (0.6666, 1, 0, 1)
      else:
        self.rect = (0.3333, 0.6666, 0, 1)
      
      if i >= 3:
        if starPowerAmount >= 50 or self.stage.scene.instruments[self.playernum].starPowerActive:
          if self.x[i] < self.xend[i-3]:
            self.x[i] += 0.01
            if self.x[i] >= self.xend[i-3]:
              self.x[i] = self.xend[i-3]
          if self.y[i] < self.yend[i-3]:
            self.y[i] += 0.01
            if self.y[i] >= self.yend[i-3]:
              self.y[i] = self.yend[i-3]        
        else:
          if self.x[i] > self.xstart[i-3]:
            self.x[i] -= 0.01
            if self.x[i] >= self.xstart[i-3]:
              self.x[i] = self.xstart[i-3]
          if self.y[i] > self.ystart[i-3]:
            self.y[i] -= 0.01
            if self.y[i] >= self.ystart[i-3]:
              self.y[i] = self.ystart[i-3]
        scale = self.drawing.widthf(pixelw = self.scale[1])

      else:
        scale = self.drawing.widthf(pixelw = self.scale[0])

      self.engine.drawImage(self.drawing, scale = (scale, -scale*3), 
                          coord = (self.x[i] * w, self.y[i] * h), 
                          rot = float(self.angle[i]), color = (1,1,1,1), rect = (0,.3333,0,1), 
                          stretched = 0)

      self.engine.drawImage(self.drawing, scale = (scale, -scale*3), 
                          coord = (self.x[i] * w, self.y[i] * h), 
                          rot = float(self.angle[i]), color = (1,1,1,lightVis), rect = self.rect, 
                          stretched = 0)

class Effect(object): #defines what type of object the layer is
  def __init__(self, layer, options):
    self.layer       = layer
    self.stage       = layer.stage
  def apply(self, i):
    pass

class RockEffect(Effect):
  def __init__(self, layer, options):
    Effect.__init__(self, layer, options)

    self.opt = options

    self.layer.canrender = -1

    self.texture     = self.opt.get("texture")
    if self.texture != None:
      self.drawings = []
      for texture in str(self.texture).split(";"):
        self.drawings.append(self.stage.engine.loadImgDrawing(self, None, os.path.join("themes", self.stage.themename, texture)))

    self.rock        = self.stage.scene.rockMax/2 * .01
    self.failingoff  = int(self.opt.get("failingoff", 0))
    currentRock = 0

    self.position    = (0,0)

    self.scale       = (.5,.5)

    self.arrowRotation    = .5
    arrowRotation = self.arrowRotation

    try: self.angle  = float(self.opt.get("angle", 0))
    except: self.angle       = eval(self.opt.get("angle"))

    self.color       = str(self.opt.get("color", '#FFFFFF')).split(";")
    self.rockmax     = int(self.opt.get("rockmax", 0))

    self.rect       = (0.0, 1.0, 0.0, 1.0)

  def apply(self, i):
    self.layer.canrender = self.failingoff

    currentRock = self.stage.scene.rock[i] / self.stage.scene.rockMax

    self.arrowRotation += (currentRock - self.arrowRotation) / 5.0
    arrowRotation = float(self.arrowRotation)

    try:  self.layer.position    = (float(self.opt.get("xpos",0.0)), float(self.opt.get("ypos", 0.0)))
    except:  self.layer.position    = (eval(self.opt.get("xpos")), eval(self.opt.get("ypos")))

    try:  self.layer.scale = (float(self.opt.get("xscale", 1.0)), float(self.opt.get("yscale", 1.0)))
    except:  self.layer.scale = (eval(self.opt.get("xscale")), eval(self.opt.get("yscale")))

    self.layer.angle = -(eval(self.opt.get("angle", "0.0")))

    self.layer.color = self.color[int(math.ceil(currentRock*len(self.color))-1)]
    if (self.rockmax == 1 and currentRock != 1) or (self.rockmax == 2 and currentRock == 1):
      self.layer.canrender = -1
    vertrect = int(self.opt.get("vertrect", 1))
    if vertrect >= 2:
      self.rect       = (0.0, 1.0, float(currentRock)/vertrect-(1/vertrect), float(currentRock)/vertrect)
    self.layer.rect = self.rect

    if self.texture != None:
      self.layer.drawing = self.drawings[int(math.ceil(currentRock*len(self.drawings))-1)]

class PowerEffect(Effect):
  def __init__(self, layer, options):
    Effect.__init__(self, layer, options)

    self.opt = options

    self.layer.canrender = -1

    currentSP = 0
    oBarScale = 0

    self.position    = (0.0,0.0)
    self.scale       = (0.0,0.0)

    self.color       = str(self.opt.get("color", '#FFFFFF')).split(";")
    self.show        = float(self.opt.get("show", 0))
    self.rect        = eval(str(self.opt.get("rect")))

  def apply(self, i):
    self.layer.canrender = -1

    oBarScale = Theme.oBarHScale * self.stage.scene.instruments[i].boardWidth / math.sqrt(self.stage.scene.camera.origin[1]**2+(self.stage.scene.camera.origin[2]-0.5)**2) * self.stage.scene.oBarScaleCoef
    currentSP = self.stage.scene.instruments[i].starPower/100.0

    try:  self.position    = (float(self.opt.get("xpos",0.0)), float(self.opt.get("ypos", 0.0)))
    except:  self.position    = (eval(self.opt.get("xpos")), eval(self.opt.get("ypos")))

    try:  self.scale       = (float(self.opt.get("xscale", 1.0)), float(self.opt.get("yscale", 1.0)))
    except:  self.scale       = (eval(self.opt.get("xscale")), eval(self.opt.get("yscale")))

    self.color       = str(self.opt.get("color", '#FFFFFF')).split(";")
    self.show        = float(self.opt.get("show", 0))
    self.rect = eval(str(self.opt.get("rect")))

    self.layer.position = self.position
    self.layer.scale = self.scale    
    if currentSP >= self.show:
      self.layer.canrender = 0
      
    self.layer.rect = self.rect

class StreakEffect(Effect):
  def __init__(self, layer, options):
    Effect.__init__(self, layer, options)

    self.opt = options

    multStreak = 0
    multiplier = 1
    streak = 0
    self.layer.canrender = -1

    self.position    = (0.0,0.0)
    self.scale       = (0.0,0.0)
    
    self.multdiv     = bool(self.opt.get("multdiv", False))

    self.angle       = float(self.opt.get("angle", 0.0))

  def apply(self, i):

    multStreak = self.stage.scene.scoring[i].streak
    if multStreak >= 30:
      multiplier = 4
    else:
      multiplier = int(multStreak*.1) + 1
    if multStreak >= 40 or (multStreak - (multiplier-1)*10 == 0 and multStreak != 0):
      streak = 10
    elif multStreak >= 10:
      streak = multStreak - (multiplier-1)*10
    else:
      streak = multStreak

    try:  self.position    = (float(self.opt.get("xpos","0.0")), float(self.opt.get("ypos", "0.0")))
    except:  self.position    = (eval(self.opt.get("xpos")), eval(self.opt.get("ypos")))

    try:  self.scale       = (float(self.opt.get("xscale", 1.0)), float(self.opt.get("yscale", 1.0)))
    except:  self.scale       = (eval(self.opt.get("xscale")), eval(self.opt.get("yscale")))

    self.angle       = float(self.opt.get("angle", 0.0))

    if streak == 0:
      self.layer.canrender = -1
    else:
      self.layer.canrender = 0
      if bool(self.multdiv) == True:
        self.rect       = ((multiplier-1)*.25, multiplier*.25, float(streak-1)*.1, float(streak)*.1)
        self.layer.scale = (self.scale[0]*.25, self.scale[1]*.1)
      else:
        self.rect       = (0.0, 1.0, float(streak-1)*.1, float(streak)*.1)
        self.layer.scale = (self.scale[0], self.scale[1]*.1)
      self.layer.rect = self.rect

    self.layer.position = self.position
    self.layer.angle = -self.angle

class MultEffect(Effect):
  def __init__(self, layer, options):
    Effect.__init__(self, layer, options)

    self.opt = options

    multStreak = 0
    multiplier = 1
    
    try:  self.position    = (float(self.opt.get("xpos",0.0)), float(self.opt.get("ypos", 0.0)))
    except:  self.position    = (eval(self.opt.get("xpos")), eval(self.opt.get("ypos")))

    try:  self.scale       = (float(self.opt.get("xscale", 1.0)), float(self.opt.get("yscale", 1.0)))
    except:  self.scale       = (eval(self.opt.get("xscale")), eval(self.opt.get("yscale")))

    self.angle       = float(self.opt.get("angle", 0.0))

    self.rect       = (0.0, 1.0, 0.0, 1.0)

  def apply(self, i):
    multStreak = self.stage.scene.scoring[i].streak
    if self.stage.scene.instruments[i].isBassGuitar:
      if multStreak >= 50:
        multiplier = 6
      else:
        multiplier = int(multStreak*.1) + 1
      if self.stage.scene.instruments[i].starPowerActive:
        multiplier += 6
    else:
      if multStreak >= 30:
        multiplier = 4
      else:
        multiplier = int(multStreak*.1) + 1

      if self.stage.scene.instruments[i].starPowerActive:
        multiplier += 4 

    try:  self.position    = (float(self.opt.get("xpos",0.0)), float(self.opt.get("ypos", 0.0)))
    except:  self.position    = (eval(self.opt.get("xpos")), eval(self.opt.get("ypos")))

    try:  self.scale       = (float(self.opt.get("xscale", 1.0)), float(self.opt.get("yscale", 1.0)))
    except:  self.scale       = (eval(self.opt.get("xscale")), eval(self.opt.get("yscale")))

    self.angle       = float(self.opt.get("angle", 0.0))
    if self.stage.scene.instruments[i].isBassGuitar:
      self.scale = (self.scale[0], self.scale[1]*0.083333333)
      self.rect       = (0.0, 1.0, float(multiplier-1)*0.083333333, float(multiplier)*0.083333333)
    else:
      self.scale = (self.scale[0], self.scale[1]*0.125)
      self.rect       = (0.0, 1.0, float(multiplier-1)*0.125, float(multiplier)*0.125)


    self.layer.position = self.position
    self.layer.scale = self.scale
    self.layer.rect = self.rect


class Rockmeter:
  def __init__(self, guitarScene, configFileName):

    self.scene            = guitarScene
    self.engine           = guitarScene.engine
    self.layers = []

    self.config = Config.MyConfigParser()
    self.config.read(configFileName)

    self.themename = self.engine.data.themeLabel
    
    # Build the layers
    for i in range(32):
      section = "layer%d" % i
      if self.config.has_section(section):
        def get(value, type = str, default = None):
          if self.config.has_option(section, value):
            return type(self.config.get(section, value))
          return default
        
        xres    = get("xres", int, 256)
        yres    = get("yres", int, 256)
        texture = get("texture")
        text    = get("text")
        font    = get("font")
        part    = get("part")
        issplights  = get("issplights")

        instrument = self.scene.instruments[0]
        if instrument.isDrum and part == "drum": 
          add = True
        elif instrument.isVocal and part == "vocal":
          add = True
        elif instrument.isBassGuitar and part == "bass":
          add = True
        elif (not instrument.isBassGuitar and not instrument.isVocal and not instrument.isDrum) and part == "guitar":
          add = True
        elif part == None:
          add = True
        else:
          add = False

        if texture and add == True and not issplights == "True":           
          drawing = self.engine.loadImgDrawing(self, None, os.path.join("themes", self.themename, texture))
          layer = Layer(self, drawing)
         
          try:
            layer.position    = (get("xpos",   float, 0.0), get("ypos",   float, 0.0))
          except:
            layer.position    = (eval(get("xpos")), eval(get("xpos")))

          try:
            layer.scale       = (get("xscale", float, 1.0), get("yscale", float, 1.0))
          except:
            layer.scale       = (eval(get("xscale")), eval(get("yscale")))

          layer.angle       = get("angle", float, 0.0)
          layer.color       = get("color", str, "#FFFFFF")

          # Load any effects
          fxClasses = {
            "rock":           RockEffect,
            "mult":           MultEffect,
            "streak":         StreakEffect,
            "power":          PowerEffect,
          }
        
          for j in range(32):
            fxSection = "layer%d:fx%d" % (i, j)
            if self.config.has_section(fxSection):
              type = self.config.get(fxSection, "type")

              if not type in fxClasses:
                continue

              options = self.config.options(fxSection)
              options = dict([(opt, self.config.get(fxSection, opt)) for opt in options])

              fx = fxClasses[type](layer, options)
              layer.effects.append(fx)
        elif text:
          layer = FontLayer(self, section, font)
          Wid, Hgt = self.engine.data.fontDict[font].getStringSize(text)
        elif issplights == "True":
          drawing = self.engine.loadImgDrawing(self, None, os.path.join("themes", self.themename, texture)) 
          for i in range(len(self.scene.instruments)):
            layer = SPLightsLayer(self, drawing, i)

          if not get("xstatic") == None:
            xstatic = get("xstatic").split(",")
            layer.xstatic = [float(i) for i in xstatic]
          if not get("ystatic") == None:
            ystatic = get("ystatic").split(",")         
            layer.ystatic = [float(i) for i in ystatic]
          if not get("xstart") == None:
            xstart = get("xstart").split(",")
            layer.xstart = [float(i) for i in xstart]
          if not get("ystart") == None:
            ystart = get("ystart").split(",")
            layer.ystart = [float(i) for i in ystart]
          if not get("xend") == None:
            xend = get("xend").split(",")
            layer.xend = [float(i) for i in xend]
          if not get("yend") == None:
            yend = get("yend").split(",")
            layer.yend = [float(i) for i in yend]
          if not get("scale") == None:
            scale = get("scale").split(",")
            layer.scale = [float(i) for i in scale]
          if not get("angle") == None:
            angle = get("angle").split(",")
            layer.angle = [float(i) for i in angle]

        else:
          layer = None

        if layer != None:
          self.layers.append(layer)

  def render(self, visibility):
    self.engine.view.setOrthogonalProjection(normalize = True)
    try:
      for layer in self.layers:
        layer.render(visibility)
    finally:
      self.engine.view.resetProjection()


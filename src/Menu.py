#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
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

import pygame
from OpenGL.GL import *
import math
import os

from View import Layer
from Input import KeyListener
import Data
import Theme
import Dialogs
import Player

import Log

class Choice:
  def __init__(self, text, callback, name = None, values = None, valueIndex = 0, append_submenu_char = True):
    #Log.debug("Choice class init (Menu.py)...")
    self.text       = unicode(text)
    self.callback   = callback
    self.name       = name
    self.values     = values
    self.valueIndex = valueIndex
    self.append_submenu_char = append_submenu_char

    if self.text.endswith(" >"):
      self.text = text[:-2]
      self.isSubMenu = True
    else:
      self.isSubMenu = isinstance(self.callback, Menu) or isinstance(self.callback, list)
    
  #MFH TODO - add support for passing position values to the callback "next menu"
  def trigger(self, engine = None):
    if engine and isinstance(self.callback, list):
      #MFH 
      if self.values:
        nextMenu = Menu(engine, self.callback, name = self.name, pos = self.values, selectedIndex = self.valueIndex )
      else:
        nextMenu = Menu(engine, self.callback, name = self.name)
    elif engine and isinstance(self.callback, Menu):
      nextMenu = self.callback
    elif self.values:
      nextMenu = self.callback(self.values[self.valueIndex])
    else:
      nextMenu = self.callback()
    if isinstance(nextMenu, Menu):
      engine.view.pushLayer(nextMenu)
      
  def selectNextValue(self):
    if self.values:
      self.valueIndex = (self.valueIndex + 1) % len(self.values)
      self.trigger()

  def selectPreviousValue(self):
    if self.values:
      self.valueIndex = (self.valueIndex - 1) % len(self.values)
      self.trigger()
      
  def getText(self, selected):
    if not self.values:
      if self.isSubMenu and self.append_submenu_char:
        return "%s >" % self.text
      return self.text
    if selected:
      return "%s: %s%s%s" % (self.text, Data.LEFT, self.values[self.valueIndex], Data.RIGHT)
    else:
      return "%s: %s" % (self.text, self.values[self.valueIndex])
          
class Menu(Layer, KeyListener):
  def __init__(self, engine, choices, name = None, onClose = None, onCancel = None, pos = (.2, .66 - .35), viewSize = 6, fadeScreen = False, font = "font", mainMenu = None, textColor = None, selectedColor = None, append_submenu_char = True, selectedIndex = None):
    self.engine       = engine

    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("Menu class init (Menu.py)...")

    #Get theme
    self.themename = self.engine.data.themeLabel
    self.theme = self.engine.data.theme
    
    self.choices      = []
    self.currentIndex = 0
    #MFH
    if selectedIndex:
      self.currentIndex = selectedIndex
    self.time         = 0
    self.onClose      = onClose
    self.onCancel     = onCancel
    self.viewOffset   = 0
    self.name     = name # akedrou - for graphical support
    self.mainMenu = False
    self.graphicMenu = False
    self.useGraphics = self.engine.config.get("game", "use_graphical_submenu")
    self.gfxText = None
    
    self.click = False
    self.scrollUp = False
    self.scrollDown = False
    self.halfTime = 0

    self.textColor = textColor
    self.selectedColor = selectedColor

    #self.sfxVolume    = self.engine.config.get("audio", "SFX_volume")
    self.drumNav = self.engine.config.get("game", "drum_navigation")  #MFH
    
    if self.name and self.useGraphics > 0:
      try:
        self.engine.loadImgDrawing(self, "menuBackground", os.path.join("themes",self.themename,"menu","%s.png" % self.name))
        self.gfxText = "%stext%d" % (self.name, len(choices))
        self.engine.loadImgDrawing(self, "menuText", os.path.join("themes",self.themename,"menu","%s.png" % self.gfxText))
        self.graphicMenu = True
        self.menux = Theme.submenuX[self.gfxText]
        self.menuy = Theme.submenuY[self.gfxText]
        self.menuScale = Theme.submenuScale[self.gfxText]
        self.vSpace = Theme.submenuVSpace[self.gfxText]
        if str(self.menux) != "None" and str(self.menuy) != "None":
          self.menux = float(self.menux)
          self.menuy = float(self.menuy)
        else:
          self.menux = .4
          self.menuy = .4
        if str(self.menuScale) != "None":
          self.menuScale = float(self.menuScale)
        else:
          self.menuScale = .5
        if str(self.vSpace) != "None":
          self.vSpace = float(self.vSpace)
        else:
          self.vSpace = .08
        Log.debug("Graphic menu enabled for submenu: %s" % self.name)
      except IOError:
        self.menuBackground = None
        self.menuText = None


    if pos == (.2, .66 - .35):  #MFH - default position, not called with a special one - this is a submenu:
      self.sub_menu_x = Theme.sub_menu_xVar
      self.sub_menu_y = Theme.sub_menu_yVar
  
      if engine.data.theme == 0:
        if self.sub_menu_x == None:
          self.sub_menu_x = .44
        if self.sub_menu_y == None:
          self.sub_menu_y = .14
      elif engine.data.theme == 1:
        if self.sub_menu_x == None:
          self.sub_menu_x = .38
        if self.sub_menu_y == None:
          self.sub_menu_y = .15
      elif engine.data.theme == 2:
        if self.sub_menu_x == None:
          self.sub_menu_x = .25
        if self.sub_menu_y == None:
          self.sub_menu_y = .14

      pos = (self.sub_menu_x, self.sub_menu_y)

    if viewSize == 6:   #MFH - default viewsize
      if self.theme == 0 or self.theme == 1 or self.theme == 2:#8bit
        viewSize = 10
    
    self.pos          = pos
    self.viewSize     = viewSize
    self.fadeScreen   = fadeScreen
    self.font = font
    self.active = False
    self.mainMenu = mainMenu
    
    for c in choices:
      try:
        text, callback = c
        if isinstance(text, tuple):
          if len(text) == 2: # a submenu's name
            c = Choice(text[0], callback, name = text[1], append_submenu_char = append_submenu_char)
          else: # Dialogs menus - FileChooser, NeckChooser, ItemChooser - this last to be changed soon
            c = Choice(text[0], callback, values = text[2], valueIndex = text[1], append_submenu_char = append_submenu_char)
        else:
          c = Choice(text, callback, append_submenu_char = append_submenu_char)
      except TypeError:
        pass
      self.choices.append(c)
      
  def selectItem(self, index):
    self.currentIndex = index
    
  def shown(self):
    self.engine.input.addKeyListener(self)
    self.engine.input.enableKeyRepeat()
    
  def hidden(self):
    self.engine.input.removeKeyListener(self)
    self.engine.input.disableKeyRepeat()
    if self.onClose:
      self.onClose()

  def updateSelection(self):
    if self.currentIndex > self.viewOffset + self.viewSize - 1:
      self.viewOffset = self.currentIndex - self.viewSize + 1
    if self.currentIndex < self.viewOffset:
      self.viewOffset = self.currentIndex
    
  #MFH added drum navigation conditional here to prevent drum nav if disabled
  #MFH updated SFX play logic to just play the new sound instead of setting volume
  def keyPressed(self, key, unicode): #racer: drum nav.
    self.time = 0
    choice = self.choices[self.currentIndex]
    c = self.engine.input.controls.getMapping(key)
    if c in Player.KEY1S or key == pygame.K_RETURN or (c in Player.DRUM4S and self.drumNav):
      choice.trigger(self.engine)
      #self.engine.data.acceptSound.setVolume(self.sfxVolume)  #MFH
      self.engine.data.acceptSound.play()
    elif c in Player.CANCELS + Player.KEY2S or (c in Player.DRUM1S and self.drumNav):
      if self.onCancel:
        self.onCancel()
      self.engine.view.popLayer(self)
      self.engine.input.removeKeyListener(self)
      #self.engine.data.cancelSound.setVolume(self.sfxVolume)  #MFH
      self.engine.data.cancelSound.play()
    elif c in Player.DOWNS + Player.ACTION2S or (c in Player.DRUM3S and self.drumNav):
      self.scrollDown = True
      self.click = False
    elif c in Player.UPS + Player.ACTION1S or (c in Player.DRUM2S and self.drumNav):
      self.scrollUp = True
      self.click = False
    elif c in Player.RIGHTS + Player.KEY4S:
      choice.selectNextValue()
    elif c in Player.LEFTS + Player.KEY3S:
      choice.selectPreviousValue()
    return True
  
  def scroll(self, dir):
    if not self.click or (self.click and self.time > 10):
      self.engine.data.selectSound.play()
      if dir == 1:
        self.currentIndex = (self.currentIndex + 1) % len(self.choices)
        self.updateSelection()
      elif dir == 0:
        self.currentIndex = (self.currentIndex - 1) % len(self.choices)
        self.updateSelection()
      self.click = True
  
  def keyReleased(self, key):
    c = self.engine.input.controls.getMapping(key)
    if c in Player.UPS + Player.ACTION1S or (c in Player.DRUM2S and self.drumNav):
      self.scrollUp = False
      self.click = False
    elif c in Player.DOWNS + Player.ACTION2S or (c in Player.DRUM3S and self.drumNav):
      self.scrollDown = False
      self.click = False
    else:
      self.click = False
    return True

  def lostFocus(self):
    pass
    
  def run(self, ticks):
    self.time += ticks / 50.0
    self.halfTime = ~self.halfTime
    if self.halfTime == 0:
      if self.scrollUp:
        self.scroll(0)
      elif self.scrollDown:
        self.scroll(1)

  def renderTriangle(self, up = (0, 1), s = .2):
    left = (-up[1], up[0])
    glBegin(GL_TRIANGLES)
    glVertex2f( up[0] * s,  up[1] * s)
    glVertex2f((-up[0] + left[0]) * s, (-up[1] + left[1]) * s)
    glVertex2f((-up[0] - left[0]) * s, (-up[1] - left[1]) * s)
    glEnd()
  
  def render(self, visibility, topMost):
    #MFH - display version in any menu:

    if not visibility:
      self.active = False
      return

    self.active = True
    
    self.engine.view.setOrthogonalProjection(normalize = True)
    try:
      v = (1 - visibility) ** 2
      # Default to this font if none was specified
      if self.font == "font":
        font = self.engine.data.font
      else:
        font = self.font

      if self.fadeScreen:
        Dialogs.fadeScreen(v)
        
      if self.graphicMenu and self.menuBackground:
        w, h, = self.engine.view.geometry[2:4]
        imgwidth = self.menuBackground.width1()
        wfactor = 640.000/imgwidth
        self.menuBackground.transform.reset()
        self.menuBackground.transform.translate(w/2,h/2)
        self.menuBackground.transform.scale(wfactor,-wfactor)
        self.menuBackground.draw()
      else:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_COLOR_MATERIAL)

      n = len(self.choices)
      x, y = self.pos

      for i, choice in enumerate(self.choices[self.viewOffset:self.viewOffset + self.viewSize]):
        if self.graphicMenu:
          if self.currentIndex == i:
            xpos = (.5,1)
          else:
            xpos = (0,.5)
          ypos = float(i+self.viewOffset)
          self.menuText.transform.reset()
          self.menuText.transform.scale(.5*self.menuScale,(-1.0/n*self.menuScale))
          self.menuText.transform.translate(w*self.menux,h*self.menuy+(h*self.vSpace)*i)
          self.menuText.draw(rect = (xpos[0],xpos[1],ypos/n,(ypos+1.0)/n))
        else:
          text = choice.getText(i + self.viewOffset == self.currentIndex)
          glPushMatrix()
          glRotate(v * 45, 0, 0, 1)

          if self.theme == 0 and self.mainMenu:#8bit
            if not i % 2 == 1:
              scale = 0.002
            else:
              scale = 0.0016

          elif self.theme == 1 and self.mainMenu:
            if not i % 2 == 1:
              scale = 0.002
            else:
              scale = 0.0016

          else:
            scale = 0.002

          w, h = font.getStringSize(" ", scale = scale)

          # Draw arrows if scrolling is needed to see all items
          if i == 0 and self.viewOffset > 0:
            Theme.setBaseColor((1 - v) * max(.1, 1 - (1.0 / self.viewOffset) / 3))
            glPushMatrix()
            glTranslatef(x - v / 4 - w * 2, y + h / 2, 0)
            self.renderTriangle(up = (0, -1), s = .015)
            glPopMatrix()
          elif i == self.viewSize - 1 and self.viewOffset + self.viewSize < n:
            Theme.setBaseColor((1 - v) * max(.1, 1 - (1.0 / (n - self.viewOffset - self.viewSize)) / 3))
            glPushMatrix()
            glTranslatef(x - v / 4 - w * 2, y + h / 2, 0)
            self.renderTriangle(up = (0, 1), s = .015)
            glPopMatrix()

          if i + self.viewOffset == self.currentIndex:
            a = (math.sin(self.time) * .15 + .75) * (1 - v * 2)
            Theme.setSelectedColor(a)
            a *= -.005
            glTranslatef(a, a, a)
          else:
            Theme.setBaseColor(1 - v)      
        
          #MFH - settable color through Menu constructor
          if i + self.viewOffset == self.currentIndex and self.selectedColor:
            c1,c2,c3 = self.selectedColor
            glColor3f(c1,c2,c3)
          elif self.textColor:
            c1,c2,c3 = self.textColor
            glColor3f(c1,c2,c3)
        
          #MFH - now to catch " >" main menu options and blank them:
          if text == " >":
            text = ""
        
          font.render(text, (x - v / 4, y), scale = scale)
        
        
          v *= 2
          if self.theme == 1 and self.font == self.engine.data.pauseFont: # evilynux - Ugly workaround for Gh3
            y += h*.65
          else:
            y += h
          glPopMatrix()
    
    
    finally:
      self.engine.view.resetProjection()

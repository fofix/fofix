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
from OpenGL.GLU import *
import math
#evilynux: needed for multi-OS file fetching
import os

#MFH - needed to check if running from compiled app or sources
import sys

from View import Layer
from Input import KeyListener
from Language import _
import Song
import Version
import Player
import Config
import Dialogs
import Theme

#akedrou - Translatable Strings:
bank = {}

bank['intro']      = [_("This mod was built on Alarian's mod,"),
                      _("which was built on UltimateCoffee's Ultimate mod,"),
                      _("which was built on RogueF's RF_mod 4.15,"),\
                      _("which was, of course, built on Frets on Fire 1.2.451,"),
                      _("which was created by Unreal Voodoo")]
bank['noOrder']    = [_("No Particular Order")]
bank['coders']     = [_("Active Coders:")]
bank['pastCoders'] = [_("Past Coders:")]
bank['graphics']   = [_("Main Graphic Contributors:")]
bank['Team Hero']  = [_("Team Hero:")]
bank['careerMode'] = [_("Creators of Career Mode")]
bank['honorary']   = [_("Honorary Credits to:")]
bank['donations']  = [_("Donations to MFH")]
bank['majorDonor'] = [_("Major Donations:")]
bank['otherDonor'] = [_("Other Donations:")]
bank['other']      = [_("Other Credits:")]
bank['tutorial']   = [_("Jurgen FoF tutorial inspired by adam02"),
                      _("Drum test song tutorial by Heka"),
                      _("Bang Bang Mystery Man song tutorial is from the original FoF"),
                      _("Drum Rolls practice tutorial by venom426")]
bank['disclaimer'] = [_("If you see your work included in this game and you aren't"),
                      _("in the credits, please leave a polite post stating what you"),
                      _("did and when, as specific as possible."),
                      _("If you can, please provide a link to your original posting"),
                      _("of the work in question."),
                      _("Then we can properly credit you.")]
bank['thanks']     = [_("Thank you for your contribution.")]
bank['oversight']  = [_("Please keep in mind that it is not easy to trace down and"),
                      _("credit every single person who contributed; if your name is"),
                      _("not included, it was not meant to slight you."),
                      _("It was an oversight.")]


class Element:
  """A basic element in the credits scroller."""
  def getHeight(self):
    """@return: The height of this element in fractions of the screen height"""
    return 0

  def render(self, offset):
    """
    Render this element.
    
    @param offset: Offset in the Y direction in fractions of the screen height
    """
    pass

class Text(Element):
  def __init__(self, font, scale, color, alignment, text):
    self.text      = text
    self.font      = font
    self.color     = color
    self.alignment = alignment
    self.scale     = scale
    self.size      = self.font.getStringSize(self.text, scale = scale)

  def getHeight(self):
    return self.size[1]

  def render(self, offset):
    offset = (offset*4.0)/3.0 # akedrou - font rendering fix
    if self.alignment == "left":
      x = .1
    elif self.alignment == "right":
      x = .9 - self.size[0]
    elif self.alignment == "center":
      x = .5 - self.size[0] / 2
    glColor4f(*self.color)
    self.font.render(self.text, (x, offset), scale = self.scale)

class Picture(Element):
  def __init__(self, engine, fileName, height):
    self.height = height
    self.engine = engine
    engine.loadImgDrawing(self, "drawing", fileName)

  def getHeight(self):
    return self.height

  def render(self, offset):
    self.drawing.transform.reset()
    w, h = self.engine.view.geometry[2:4]
    self.drawing.transform.translate(.5 * w, h - (.5 * self.height + offset) * h * float(w) / float(h))
    self.drawing.transform.scale(1, -1)
    self.drawing.draw()
    
# evilynux - Updated to latest MFH-Alarian mod. Alot changed compared to upstream FoF.
#            Removed song, our revamped MainMenu already provides songs.
class Credits(Layer, KeyListener):
  """Credits scroller."""
  def __init__(self, engine, songName = None):
    self.engine      = engine
    self.time        = 0.0
    self.offset      = 0.5 # akedrou - this seems to fix the delay issue, but I'm not sure why. Return here!
    self.speedDiv    = 20000.0
    self.speedDir    = 1.0
    self.doneList    = []
    self.themename = Config.get("coffee", "themename")
    
    Config.set("game", "selected_library", "songs")

    nf = self.engine.data.font
    bf = self.engine.data.bigFont
    ns = 0.002
    bs = 0.001
    hs = 0.003
    c1 = (1, 1, .5, 1)
    c2 = (1, .75, 0, 1)
    self.text_size = nf.getLineSpacing(scale = hs)
    
    menuPath = os.path.join("data","themes",self.themename,"menu")
    if not hasattr(sys,"frozen"): #MFH - add ".." to path only if running from sources - not if running from EXE
      menuPath = os.path.join("..",menuPath)
    if self.engine.data.fileExists(os.path.join(menuPath,"credits.png")):
      self.engine.loadImgDrawing(self, "background",os.path.join(menuPath,"credits.png"))
      if self.engine.data.fileExists(os.path.join(menuPath,"creditstop.png")): #akedrou - cool effect, but usable to hide credits...
        self.engine.loadImgDrawing(self, "topLayer",os.path.join(menuPath,"creditstop.png"))
      else:
        self.topLayer = None
    else:
      self.background = None
      self.topLayer = None

    space = Text(nf, hs, c1, "center", " ")
    self.credits = [
      Picture(self.engine, "mfhlogo.png", .10), 
      Text(nf, ns, c1, "center", "%s" % self.engine.versionString) ]

    # evilynux: Use CREDITS file as source.
    creditsPath = "CREDITS"
    if not hasattr(sys,"frozen"): #MFH - add ".." to path only if running from sources - not if running from EXE
      creditsPath = os.path.join("..",creditsPath)
    if os.path.exists(creditsPath):
      file = open(creditsPath)
      for line in file:
        line = line.strip("\n")
        if line.startswith("=====") or line.startswith("-----"):
          continue
        if line == "":
          self.credits.append(space)
        elif line.startswith("`") and line.endswith("`"):
          line = line.strip("`")
          if line.startswith("%") and line.endswith("%"):
            line = line.strip("%")
            try:
              for text in bank[line]:
                self.credits.append( Text(nf, bs, c1, "left", "%s" % text) )
            except KeyError:
              self.credits.append( Text(nf, bs, c1, "left", "%s" % line) )
          else:
            self.credits.append( Text(nf, bs, c1, "left", "%s" % line) )
        elif line.startswith("_") and line.endswith("_"):
          line = line.strip("_")
          if line.startswith("%") and line.endswith("%"):
            line = line.strip("%")
            try:
              for text in bank[line]:
                self.credits.append( Text(nf, ns, c2, "center", "%s" % text) )
            except KeyError:
              self.credits.append( Text(nf, ns, c2, "center", "%s" % line) )
          else:
            self.credits.append( Text(nf, ns, c2, "center", "%s" % line) )
        elif line.startswith("=") and line.endswith("="):
          line = line.strip("=")
          if line.startswith("%") and line.endswith("%"):
            line = line.strip("%")
            try:
              for text in bank[line]:
                self.credits.append( Text(nf, ns, c1, "left", "%s" % text) )
            except KeyError:
              self.credits.append( Text(nf, ns, c1, "left", "%s" % line) )
          else:
            self.credits.append( Text(nf, ns, c1, "left", "%s" % line) )
        else:
          if line.startswith("%") and line.endswith("%"):
            line = line.strip("%")
            try:
              for text in bank[line]:
                self.credits.append( Text(nf, ns, c2, "right", "%s" % text) )
            except KeyError:
              self.credits.append( Text(nf, ns, c2, "right", "%s" % line) )
          else:
            self.credits.append( Text(nf, ns, c2, "right", "%s" % line) )
  
    self.credits.extend( [
      space,
      Text(nf, ns, c1, "left",   _("Made with:")),
      Text(nf, ns, c2, "right",  "Python 2.4"),
      Text(nf, bs, c2, "right",  "http://www.python.org"),
      space,
      Text(nf, ns, c2, "right",  "PyGame 1.7.1"),
      Text(nf, bs, c2, "right",  "http://www.pygame.org"),
      space,
      Text(nf, ns, c2, "right",  "PyOpenGL"),
      Text(nf, bs, c2, "right",  "http://pyopengl.sourceforge.net"),
      space,
      #Text(nf, ns, c2, "right",  "Amanith Framework"),
      #Text(nf, bs, c2, "right",  "http://www.amanith.org"),
      #space,
      Text(nf, ns, c2, "right",  "Illusoft Collada module 1.4"),
      Text(nf, bs, c2, "right",  "http://colladablender.illusoft.com"),
      space,
      Text(nf, ns, c2, "right",  "Psyco specializing compiler"),
      Text(nf, bs, c2, "right",  "http://psyco.sourceforge.net"),
      space,
      Text(nf, ns, c2, "right",  "MXM Python Midi Package 0.1.4"),
      Text(nf, bs, c2, "right",  "http://www.mxm.dk/products/public/pythonmidi"),
      space,
      space,
      Text(nf, bs, c1, "center", _("Source Code available under the GNU General Public License")),
      Text(nf, bs, c2, "center", "http://code.google.com/p/fofix"),
      space,
      space,
      Text(nf, bs, c1, "center", _("Copyright 2006, 2007 by Unreal Voodoo")),
      Text(nf, bs, c1, "center", _("Copyright 2008, 2009 by Team FoFiX")),
      space,
      space
    ])

  def shown(self):
    self.engine.input.addKeyListener(self)

  def hidden(self):
    self.engine.input.removeKeyListener(self)
    self.engine.view.pushLayer(self.engine.mainMenu)    #rchiav: use already-existing MainMenu instance

  def quit(self):
    self.engine.view.popLayer(self)

  def keyPressed(self, key, unicode):
    if self.engine.input.controls.getMapping(key) in (Player.menuYes + Player.menuNo) or key == pygame.K_RETURN or key == pygame.K_ESCAPE:
      self.quit()
    elif self.engine.input.controls.getMapping(key) in (Player.menuDown) or key == pygame.K_DOWN: #akedrou: so I was bored.
      if self.speedDiv > 1000.0:
        self.speedDiv -= 1000.0
        if self.speedDiv < 1000.0:
          self.speedDiv = 1000.0
    elif self.engine.input.controls.getMapping(key) in (Player.menuUp) or key == pygame.K_UP:
      if self.speedDiv < 30000.0:
        self.speedDiv += 1000.0
        if self.speedDiv > 30000.0:
          self.speedDiv = 30000.0
    elif self.engine.input.controls.getMapping(key) in (Player.key3s):
      self.speedDir *= -1
    elif self.engine.input.controls.getMapping(key) in (Player.key4s):
      if self.speedDir != 0:
        self.speedDir = 0
      else:
        self.speedDir = 1.0
    return True
  
  def run(self, ticks):
    self.time   += ticks / 50.0
    #self.offset -= ticks / 7500.0 # evilynux - corresponds to scroll speed
    #self.offset -= ticks / 15000.0 #MFH - slowin it down - # evilynux - corresponds to scroll speed
    self.offset -= (ticks / self.speedDiv) * self.speedDir #akedrou - some credits fun.

    # evilynux - approximating the end of the list from the (mostly used font size * lines)
    #if self.offset < -( self.text_size * len(self.credits) ):
    if self.offset < -( self.text_size * len(self.credits) ) or self.offset > 1.5:    #(MFH - adding 5% to estimated font height) undone: using larger scale for estimation.
      self.quit()
    if len(self.credits) == len(self.doneList): #akedrou - goofy workaround for string size glitch.
      self.quit()
  
  def render(self, visibility, topMost):
    v = 1.0 - ((1 - visibility) ** 2)
    
    # render the background    
    t = self.time / 100 + 34
    w, h, = self.engine.view.geometry[2:4]
    
    self.engine.view.setOrthogonalProjection(normalize = True)
    if self.background:
      wFactor = 640.000/self.background.width1()
      self.engine.drawImage(self.background, scale = (wFactor,-wFactor), coord = (w/2,h/2))
    else:
      Dialogs.fadeScreen(.4)
    font = self.engine.data.font
    self.doneList = []

    # render the scroller elements
    y = self.offset
    glTranslatef(-(1 - v), 0, 0)
    try:
      for element in self.credits:
        hE = element.getHeight()
        if y + hE > 0.0 and y < 1.0:
          element.render(y)
        if y + hE < 0.0:
          self.doneList.append(element)
        y += hE
        if y > 1.0:
          break
      if self.topLayer:
        wFactor = 640.000/self.topLayer.width1()
        hPos = h - ((self.topLayer.height1() * wFactor)*.75)
        if hPos < h * .6:
          hPos = h * .6
        self.engine.drawImage(self.topLayer, scale = (wFactor,-wFactor), coord = (w/2,hPos))
    finally:
      self.engine.view.resetProjection()

#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 rchiav                                         #
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
import colorsys

from View import Layer
from Input import KeyListener
from GameTask import GameTask
from Session import MessageHandler
from Language import _
import MainMenu
import Dialogs
import Player
import Song
import Config

class Lobby(Layer, KeyListener, MessageHandler):
  def __init__(self, engine, session, singlePlayer = False, tutorial = False):
    self.engine       = engine
    self.session      = session
    self.time         = 0.0
    self.gameStarted  = False
    self.singlePlayer = singlePlayer
    self.tutorial     = tutorial
    self.session.broker.addMessageHandler(self)

  def shown(self):
    self.engine.input.addKeyListener(self)

    if self.singlePlayer:
      self.session.world.createPlayer(_("Player"))
      self.session.world.createPlayer(_("Player2"))
      if self.tutorial:
        Config.set("game", "selected_library", "songs")
        self.session.world.startGame(libraryName = Song.DEFAULT_LIBRARY, songName = "tutorial")
      else:
        self.session.world.startGame()
    else:
      n = self.session.id or 1
      name = Dialogs.getText(self.engine, _("Enter your name:"), _("Player #%d") % n)
      if name:
        self.session.world.createPlayer(name)
      else:
        self.engine.view.popLayer(self)

  def hidden(self):
    self.engine.input.removeKeyListener(self)
    self.session.broker.removeMessageHandler(self)
    if not self.gameStarted:
      self.session.close()
      #self.engine.view.pushLayer(MainMenu.MainMenu(self.engine))
      self.engine.view.pushLayer(self.engine.mainMenu)    #rchiav: use already-existing MainMenu instance

  def handleGameStarted(self, sender):
    self.gameStarted = True
    self.engine.addTask(GameTask(self.engine, self.session))
    self.engine.view.popLayer(self)

  def keyPressed(self, key, unicode):
    c = self.engine.input.controls.getMapping(key)
    if c in [Player.CANCEL, Player.KEY2]:
      self.engine.view.popLayer(self)
    elif (c in [Player.KEY1] or key == pygame.K_RETURN) and self.canStartGame():
      self.gameStarted = True
      self.session.world.startGame()
    return True

  def keyReleased(self, key):
    pass

  def run(self, ticks):
    self.time += ticks / 50.0

  def canStartGame(self):
    return len(self.session.world.players) > 1 and self.session.isPrimary() and not self.gameStarted
  
  def render(self, visibility, topMost):
    if self.singlePlayer:
      return
    
    self.engine.view.setOrthogonalProjection(normalize = True)
    font = self.engine.data.font

    try:
      v = 1.0 - ((1 - visibility) ** 2)
      
      glEnable(GL_BLEND)
      glBlendFunc(GL_SRC_ALPHA, GL_ONE)
      glEnable(GL_COLOR_MATERIAL)

      text = _("Lobby (%d players)") % len(self.session.world.players)
      w, h = font.getStringSize(text)

      x = .5 - w / 2
      d = 0.0
      c = 1 - .25 * v

      y = .1 - (1.0 - v) * .2
        
      for i, ch in enumerate(text):
        w, h = font.getStringSize(ch)
        c = i * .05
        glColor3f(*colorsys.hsv_to_rgb(.75, c, 1))
        glPushMatrix()
        s = .25 * (math.sin(i / 2 + self.time / 4) + 2)
        glTranslate(-s * w / 2, -s * h / 2, 0)
        font.render(ch, (x, y), scale = 0.002 * s)
        glPopMatrix()
        x += w

      x = .1
      y = .2 + (1 - v) / 4
      glColor4f(1, 1, 1, v)
      
      for player in self.session.world.players:
        font.render(player.name, (x, y))
        y += .08

      if self.canStartGame():
        s = _("Press Enter to Start Game")
        sz = 0.0013
        w, h = font.getStringSize(s, scale = sz)
        font.render(s, (.5 - w / 2, .65), scale = sz)
        
    finally:
      self.engine.view.resetProjection()

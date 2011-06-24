#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2009 FoFiX Team                                     #
#               2009 akedrou                                        #
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

import Player
import SceneFactory
import Dialogs
from Song import SongQueue
from Language import _

STARTUP_SCENE = "SongChoosingScene"

class World:
  def __init__(self, engine, players, maxplayers = None, gameMode = 0, multiMode = 0, allowGuitar = True, allowDrum = True, allowMic = False, tutorial = False):
    self.engine       = engine
    self.players      = []
    self.minPlayers   = players
    self.maxPlayers   = maxplayers or players
    self.gameMode     = gameMode  #Quickplay, Practice, Career
    self.multiMode    = multiMode #Face-Off, Pro FO, Party, Co-Op, RB Co-Op, GH Co-Op, Battle
    self.allowGuitar  = allowGuitar
    self.allowDrum    = allowDrum
    self.allowMic     = allowMic
    self.tutorial     = tutorial
    self.scene        = None
    self.sceneName    = ""
    self.songQueue    = SongQueue()
    self.playingQueue = False
    self.done         = False
    self.setGameName()
  
  def setGameName(self):
    if self.minPlayers > 1:
      if self.gameMode == 0:
        self.gameName = _("Face-Off")
      elif self.gameMode == 1:
        self.gameName = _("Pro Face-Off")
      elif self.gameMode == 2:
        self.gameName = _("Party Mode")
      elif self.gameMode == 3:
        self.gameName = _("FoFiX Co-Op Mode")
      elif self.gameMode == 4:
        self.gameName = _("RB Co-Op Mode")
      elif self.gameMode == 5:
        self.gameName = _("GH Co-Op Mode")
      elif self.gameMode == 6:
        self.gameName = _("Battle Mode")
    else:
      if self.gameMode == 0:
        self.gameName = _("Quickplay")
      elif self.gameMode == 1:
        self.gameName = _("Practice")
      elif self.gameMode == 2:
        self.gameName = _("Career Mode")
  
  def finishGame(self):
    if self.done:
      return
    self.players = []
    if self.scene:
      self.engine.view.popLayer(self.scene)
      self.engine.removeTask(self.scene)
    for layer in self.engine.view.layers:
      if isinstance(layer, Dialogs.LoadingSplashScreen):
        Dialogs.hideLoadingSplashScreen(self.engine, layer)
    self.scene   = None
    self.done    = True
    self.engine.finishGame()
  
  def startGame(self, **args):
    self.createScene(STARTUP_SCENE, **args)
  
  def resetWorld(self):
    if self.scene:
      self.engine.view.popLayer(self.scene)
      self.engine.removeTask(self.scene)
    for layer in self.engine.view.layers:
      if isinstance(layer, Dialogs.LoadingSplashScreen):
        Dialogs.hideLoadingSplashScreen(self.engine, layer)
    self.scene = None
    self.sceneName = ""
    self.players = []
    self.songQueue.reset()
    self.engine.mainMenu.restartGame()
  
  def createPlayer(self, name):
    playerNum = len(self.players)
    player = Player.Player(name, playerNum)
    player.controller = self.engine.input.activeGameControls[playerNum]
    player.controlType = self.engine.input.controls.type[player.controller]
    player.keyList = Player.playerkeys[playerNum]
    player.configController()
    player.practiceMode = (self.gameMode == 1)
    self.players.append(player)
    self.songQueue.parts.append(player.part.id)
    self.songQueue.diffs.append(player.getDifficultyInt())
    if self.scene:
      self.scene.addPlayer(player)
  
  def deletePlayer(self, number):
    player = self.players.pop(number)
    if self.scene:
      self.scene.removePlayer(player)
  
  def createScene(self, name, **args):
    if self.scene:
      self.engine.view.popLayer(self.scene)
      self.engine.removeTask(self.scene)
    scene = SceneFactory.create(engine = self.engine, name = name, **args)
    self.scene = scene
    self.engine.addTask(self.scene)
    self.engine.view.pushLayer(self.scene)

  def getPlayers(self):
    return self.players

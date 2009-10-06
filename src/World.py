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

from Player import Player
import SceneFactory
import Config
import Log
import Dialogs
from Song import SongQueue

STARTUP_SCENE = "SongChoosingScene"

class World:
  def __init__(self, engine):
    self.engine    = engine
    self.players   = []
    self.scene     = None
    self.sceneName = ""
    self.songQueue = SongQueue()
    self.done      = False
  
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
  
  def createPlayer(self, name):
    player = Player(name, len(self.players))
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
    try:
      if self.scene:
        self.engine.view.popLayer(self.scene)
        self.engine.removeTask(self.scene)
      scene = SceneFactory.create(engine = self.engine, name = name, **args)
      self.scene = scene
      self.engine.addTask(self.scene)
      self.engine.view.pushLayer(self.scene)
    except Exception, e:
      self.engine.startupMessages.append(str(e))
      Log.error("%s creation failed: " % name)
      self.finishGame()
  
  def getPlayers(self):
    return self.players

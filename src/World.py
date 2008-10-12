#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
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
from Session import MessageHandler, Message
import Network
import SceneFactory

STARTUP_SCENE = "SongChoosingScene"

# Messages from client to server
class CreatePlayer(Message): pass
class StartGame(Message): pass
class CreateScene(Message): pass
class DeleteScene(Message): pass
class GameFinished(Message): pass

# Messages from server to client
class PlayerJoined(Message): pass
class PlayerLeft(Message): pass
class GameStarted(Message): pass
class SceneCreated(Message): pass
class SceneDeleted(Message): pass
class EnterScene(Message): pass
class LeaveScene(Message): pass

# Internal messages
class SceneEntered(Message): pass
class SceneLeft(Message): pass

class World(MessageHandler):
  # TODO: abstract away the network details somehow
  def __init__(self, engine, broker):
    self.objects = Network.ObjectCollection()
    self.engine = engine
    self.broker = broker
    self.players = []
    self.scenes = []

  def handlePlayerJoined(self, sender, id, owner, name):
    player = Player(owner, name, len(self.players))
    self.players.append(player)
    self.objects[id] = player

  def handlePlayerLeft(self, sender, id):
    player = self.objects[id]
    self.players.remove(player)
    del self.objects[id]
    self.finishGameIfNeeded()

  def finishGameIfNeeded(self):
    if not self.players and not self.scenes:
      self.broker.signalMessage(0, GameFinished())

  def handleSceneDeleted(self, sender, id):
    try:
      scene = self.objects[id]
      self.broker.removeMessageHandler(scene)
      self.engine.removeTask(scene)
      if scene in self.scenes:
        self.scenes.remove(scene)
      del self.objects[id]
    except KeyError:
      pass
    self.finishGameIfNeeded()

  def handleSceneEntered(self, sender, sceneId, playerId):
    scene  = self.objects[sceneId]
    player = self.objects[playerId]
    scene.addPlayer(player)
    
  def handleSceneLeft(self, sender, sceneId, playerId):
    try:
      scene  = self.objects[sceneId]
      player = self.objects[playerId]
      scene.removePlayer(player)
    except KeyError:
      pass
    
class WorldServer(World):
  def __init__(self, engine, server):
    World.__init__(self, engine, server.broker)
    self.server = server

  def handleCreatePlayer(self, sender, name):
    id = self.objects.generateId()
    self.server.broadcastMessage(PlayerJoined(id = id, owner = sender, name = name))
    return id

  def handleCreateScene(self, sender, name, args):
    id = self.objects.generateId()
    self.server.broadcastMessage(SceneCreated(id = id, owner = sender, name = name, args = args))
    return id
  
  def handleDeleteScene(self, sender, id):
    try:
      scene = self.objects[id]
      self.deleteScene(scene)
    except KeyError:
      pass
  
  def deletePlayer(self, player):
    id = self.objects.id(player)
    self.server.broadcastMessage(PlayerLeft(id = id))

  def deleteScene(self, scene):
    id = self.objects.id(scene)
    self.server.broadcastMessage(SceneDeleted(id = id))

  def createScene(self, name, **args):
    id = self.objects.generateId()
    self.server.broadcastMessage(SceneCreated(id = id, owner = None, name = name, args = args))
    return id

  def enterScene(self, scene, player):
    sceneId  = self.objects.id(scene)
    playerId = self.objects.id(player)
    self.server.broadcastMessage(SceneEntered(sceneId = sceneId, playerId = playerId))

  def leaveScene(self, scene, player):
    sceneId  = self.objects.id(scene)
    playerId = self.objects.id(player)
    self.server.broadcastMessage(SceneLeft(sceneId = sceneId, playerId = playerId))

  def handleSessionOpened(self, session):
    # TODO: make this more automatic
    for player in self.players:
      id = self.objects.id(player)
      session.sendMessage(PlayerJoined(id = id, owner = player.owner, name = player.name))
    for scene in self.scenes:
      id = self.objects.id(scene)
      session.sendMessage(SceneCreated(id = id, owner = scene.owner, name = scene.__name__, args = scene.args))

  def handleSessionClosed(self, session):
    # TODO: make this more automatic
    for player in self.players:
      if player.owner == session.id:
        self.deletePlayer(player)
    for scene in self.scenes:
      if scene.owner == session.id:
        self.deleteScene(scene)

  def handleStartGame(self, sender, args):
    self.server.broadcastMessage(GameStarted())
    id = self.createScene(STARTUP_SCENE, **args)
    if id:
      for player in self.players:
        playerId = self.objects.id(player)
        self.server.broadcastMessage(EnterScene(sceneId = id, playerId = playerId))

  def handleEnterScene(self, sender, sceneId, playerId):
    scene  = self.objects[sceneId]
    player = self.objects[playerId]
    self.enterScene(scene, player)

  def handleLeaveScene(self, sender, sceneId, playerId):
    scene  = self.objects[sceneId]
    player = self.objects[playerId]
    self.leaveScene(scene, player)

  def handleSceneCreated(self, sender, id, owner, name, args):
    scene = SceneFactory.create(engine = self.engine, name = name, owner = owner, server = self.server, **args)
    self.broker.addMessageHandler(scene)
    self.engine.addTask(scene)
    self.scenes.append(scene)
    self.objects[id] = scene

  def handleSceneDeleted(self, sender, id):
    try:
      scene = self.objects[id]
      for player in scene.players:
        self.leaveScene(scene, player)
    except KeyError:
      pass
    World.handleSceneDeleted(self, sender, id)
    
  def finishGameIfNeeded(self):
    if not self.players and not self.scenes:
      self.server.broadcastMessage(GameFinished())
    World.finishGameIfNeeded(self)
    
class WorldClient(World):
  def __init__(self, engine, session):
    World.__init__(self, engine, session.broker)
    self.session = session

  def finishGame(self):
    for scene in self.scenes:
      self.deleteScene(scene)
    for player in self.players:
      self.deletePlayer(player)

  def createPlayer(self, name):
    self.session.sendMessage(CreatePlayer(name = name))

  def deletePlayer(self, player):
    id = self.objects.id(player)
    self.session.sendMessage(PlayerLeft(id = id))

  def createScene(self, name, **args):
    self.session.sendMessage(CreateScene(name = name, args = args))

  def enterScene(self, player, scene):
    sceneId  = self.objects.id(scene)
    playerId = self.objects.id(player)
    self.session.sendMessage(EnterScene(sceneId = sceneId, playerId = playerId))

  def leaveScene(self, player, scene):
    sceneId  = self.objects.id(scene)
    playerId = objects.id(player)
    self.session.sendMessage(LeaveScene(sceneId = sceneId, playerId = playerId))

  def deleteScene(self, scene):
    id = self.objects.id(scene)
    self.session.sendMessage(DeleteScene(id = id))

  def startGame(self, **args):
    self.session.sendMessage(StartGame(args = args))

  def getLocalPlayer(self):
    for player in self.players:
      if player.owner == self.session.id:
        return player
      
  def getPlayer2(self):
    return self.players[1]
        
  def handleSceneCreated(self, sender, id, owner, name, args):
    scene = SceneFactory.create(engine = self.engine, name = name, owner = owner, session = self.session, **args)
    self.broker.addMessageHandler(scene)
    self.scenes.append(scene)
    self.objects[id] = scene
    if owner == self.session.id:
      for player in self.players:
        if player.owner == self.session.id:
          self.enterScene(player, scene)

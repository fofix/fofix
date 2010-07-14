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

from Input import KeyListener
from Session import MessageHandler
from Task import Task
from Language import _
import Dialogs

class GameTask(Task, KeyListener): # , MessageHandler
  def __init__(self, engine, drawMiniViews = False):
    # assert self.engine.world.players, "No players in game"
    
    self.engine = engine
    # self.session = session
    self.time = 0.0
    # self.session.broker.addMessageHandler(self)
    # self.player = self.session.world.getLocalPlayer()

  def quit(self):
    # self.session.broker.removeMessageHandler(self)
    self.engine.view.popAllLayers()
    # self.session.close()
    self.engine.view.pushLayer(self.engine.mainMenu)    #rchiav: use already-existing MainMenu instance
    self.engine.removeTask(self)

  # def handleSceneEntered(self, sender, sceneId, playerId):
    # try:
      # scene  = self.session.world.objects[sceneId]
      # player = self.session.world.objects[playerId]
      # self.engine.view.pushLayer(scene)
    # except KeyError:
      # pass

  # def handleSceneLeft(self, sender, sceneId, playerId):
    # try:
      # scene  = self.session.world.objects[sceneId]
      # player = self.session.world.objects[playerId]
      # self.engine.view.popLayer(scene)
    # except KeyError:
      # pass

  # def handleGameFinished(self, sender):
    # self.quit()
    # s            = self.session
    # self.session = None
    # self.engine.disconnect(s)

  # def handleConnectionLost(self, sender):
    # if self.session:
      # Dialogs.showMessage(self.engine, _("Connection lost."))
      # self.quit()

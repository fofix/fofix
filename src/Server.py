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

import Network
import Engine
import Log
import cPickle as pickle

from Session import ServerSession, MessageBroker
from World import WorldServer

class Server(Network.Server, Engine.Task):
  def __init__(self, engine):
    Network.Server.__init__(self)
    self.engine = engine
    self.sessions = {}
    self.broker = MessageBroker()
    self.world = WorldServer(self.engine, server = self)
    self.broker.addMessageHandler(self.world)

  def createConnection(self, sock):
    return ServerSession(self.engine, sock)

  def handleConnectionOpen(self, conn):
    Log.debug("Session #%d connected." % conn.id)
    self.sessions[conn.id] = conn
    self.engine.addTask(conn, synchronized = False)

  def handleConnectionClose(self, conn):
    Network.Server.handleConnectionClose(self, conn)
    self.engine.removeTask(conn)
    try:
      del self.sessions[conn.id]
    except KeyError:
      pass

  def broadcastMessage(self, message, meToo = True, ignore = []):
    for id, session in self.sessions.items():
      if id in ignore: continue
      session.sendMessage(message)
    if meToo:
      session.handleMessage(0, message)

  def sendMessage(self, receiverId, message):
    try:
      self.sessions[receiverId].sendMessage(message)
    except IndexError:
      Log.warning("Tried to send message to nonexistent session #%d." % receiverId)

  def run(self, ticks):
    Network.communicate()

  def stopped(self):
    self.close()

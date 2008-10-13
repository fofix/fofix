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

import pickle
from StringIO import StringIO

import Network
import Engine
import Log
import World
import Task

try:
  reversed
except:
  def reversed(seq):
    seq = seq[:]
    seq.reverse()
    return seq

class Message:
  def __init__(self, **args):
    for key, value in args.items():
      setattr(self, key, value)

  def __repr__(self):
    return "<Message %s %s>" % (str(self.__class__), " ".join(["%s='%s'" % (k, v) for k, v in self.__dict__.items()]))
  
class MessageBroker:
  def __init__(self):
    self.messageHandlers = []

  def addMessageHandler(self, handler):
    if handler not in self.messageHandlers:
      self.messageHandlers.append(handler)
    
  def removeMessageHandler(self, handler):
    if handler in self.messageHandlers:
      self.messageHandlers.remove(handler)

  def signalMessage(self, sender, message):
    #if not Log.quiet and len(str(message)) < 80:
    #  Log.debug("From %s: %s" % (sender, message))
    #  print self.messageHandlers
    for handler in reversed(self.messageHandlers):
      try:
        handler.handleMessage(sender, message)
      except Exception, e:
        import traceback
        traceback.print_exc()

  def signalSessionOpened(self, session):
    for handler in self.messageHandlers:
      handler.handleSessionOpened(session)

  def signalSessionClosed(self, session):
    for handler in self.messageHandlers:
      handler.handleSessionClosed(session)

class MessageHandler:
  def handleMessage(self, sender, message):
    f = None
    try:
      n = "handle" + str(message.__class__).split(".")[-1]
      f = getattr(self, n)
    except AttributeError:
      return None
    return f(sender, **message.__dict__)

  def handleSessionOpened(self, session):
    pass

  def handleSessionClosed(self, session):
    pass

class Phrasebook:
  def __init__(self):
    self.receivedClasses = {}
    self.sentClasses = {}

  def serialize(data):
    s = StringIO()
    pickle.Pickler(s, protocol = 2).dump(data)
    return s.getvalue()
  serialize = staticmethod(serialize)

  def unserialize(data):
    return pickle.loads(data)
  unserialize = staticmethod(unserialize)

  def decode(self, packet):
    data = self.unserialize(packet)
    id = data[0]
    if id < 0:
      self.receivedClasses[-id] = data[1:]
      Log.debug("Learned about %s, %d phrases now known." % (data[1], len(self.receivedClasses)))
    elif id in self.receivedClasses:
      message = self.receivedClasses[id][0]()
      if len(data) > 1:
        message.__dict__.update(dict(zip(self.receivedClasses[id][1], data[1:])))
      return message
    else:
      Log.warn("Message with unknown class received: %d" % id)

  def encode(self, message):
    packets = []
    
    if not message.__class__ in self.sentClasses:
      id = len(self.sentClasses) + 1
      definition = [message.__class__, message.__dict__.keys()]
      self.sentClasses[message.__class__] = [id] + definition
      packets.append(self.serialize([-id] + definition))
      Log.debug("%d phrases taught." % len(self.sentClasses))
    else:
      id = self.sentClasses[message.__class__][0]

    data = [id] + [getattr(message, key) for key in self.sentClasses[message.__class__][2]]
    packets.append(self.serialize(data))
    return packets

class BaseSession(Network.Connection, Task.Task, MessageHandler):
  def __init__(self, engine, broker, sock = None):
    Network.Connection.__init__(self, sock)
    self.engine = engine
    self.broker = broker
    self.phrasebook = Phrasebook()

  def __str__(self):
    return "<Session #%s at %s>" % (self.id, self.addr)
  
  def isPrimary(self):
    return self.id == 1

  def run(self, ticks):
    pass

  def stopped(self):
    self.close()

  def disconnect(self):
    return self.engine.disconnect(self)

  def sendMessage(self, message):
    #print "Sent by %s:%s: %s" % (self.__class__, self.id, message)
    #self.sendPacket(message.serialize())
    for packet in self.phrasebook.encode(message):
      self.sendPacket(packet)

  def handleMessage(self, sender, message):
    #print "Received by %s:%s: %s" % (self.__class__, self.id, message)
    self.broker.signalMessage(sender, message)

  def handleRegistration(self):
    Log.debug("Connected as session #%d." % self.id)

  def isConnected(self):
    return self.id is not None
  
class ServerSession(BaseSession):
  def __init__(self, engine, sock):
    BaseSession.__init__(self, engine = engine, broker = engine.server.broker, sock = sock)
    self.server = engine.server
    self.world = self.server.world

  def handlePacket(self, packet):
    message = self.phrasebook.decode(packet)
    if message:
      self.handleMessage(self.id, message)

  def handleRegistration(self):
    self.broker.signalSessionOpened(self)

  def handleClose(self):
    self.broker.signalSessionClosed(self)
    BaseSession.handleClose(self)
    
class ConnectionLost(Message): pass
    
class ClientSession(BaseSession):
  def __init__(self, engine):
    BaseSession.__init__(self, engine = engine, broker = MessageBroker())
    self.world = World.WorldClient(engine, session = self)
    self.broker.addMessageHandler(self.world)
    self.closed = False

  def handleClose(self):
    if not self.closed:
      self.closed = True
      self.broker.signalMessage(0, ConnectionLost())

  def handlePacket(self, packet):
    message = self.phrasebook.decode(packet)
    if message:
      self.handleMessage(0, message)

  def run(self, ticks):
    Network.communicate()

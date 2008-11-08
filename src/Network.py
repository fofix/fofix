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

import asyncore
import socket
import struct
import time
import StringIO

import Log

PORT = 12345

class ObjectCollection(dict):
  def __init__(self):
    dict.__init__(self)
    self.idCounter = -1
    self.objMap = {}

  def add(self, object, id = None):
    id = id or self.generateId()
    self[id] = object
    return id

  def id(self, object):
    try:
      return self.objMap[object]
    except KeyError:
      pass

  def __delitem__(self, id):
    try:
      del self.objMap[self[id]]
      del self[id]
    except KeyError:
      pass

  def __setitem__(self, id, object):
    self.objMap[object] = id
    dict.__setitem__(self, id, object)

  def generateId(self):
    self.idCounter += 1
    return self.idCounter
  
class Connection(asyncore.dispatcher):
  def __init__(self, sock = None):
    asyncore.dispatcher.__init__(self, sock = sock)
    self.id = None
    self.server = None
    self._buffer = []
    self._sentSizeField = False
    self._receivedSizeField = 0
    self._packet = StringIO.StringIO()

    if not sock:
      self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

  #def __getattr__(self, name):
  #  print ">>>", name
  #  return asyncore.dispatcher.__getattr__(self, name)

  def connect(self, host, port = PORT):
    assert self.id is None

    asyncore.dispatcher.connect(self, (host, port))

    # do a blocking connect
    n = 0
    while not self.connected and n < 600:
      communicate()
      n += 1
      if n > 100:
        time.sleep(.1)

  def accept(self, id):
    assert self.id is None
    
    self.id = id
    self._buffer.append(struct.pack("H", self.id))
    self.handleRegistration()

  def setServer(self, server):
    self.server = server

  def handleConnect(self):
    pass

  def handle_connect(self):
    return self.handleConnect()

  def handle_read(self):
    try:
      if not self._receivedSizeField:
        data = self.recv(2)
        if data:
          self._receivedSizeField = struct.unpack("H", data)[0]
        return
      data = self.recv(self._receivedSizeField)
      if data:
        self._receivedSizeField -= len(data)
        self._packet.write(data)
        if not self._receivedSizeField:
          # The first packet contains the ID
          if self.id is None:
            self.id = struct.unpack("H", self._packet.getvalue())[0]
            self.handleRegistration()
          else:
            self.handlePacket(self._packet.getvalue())
          self._packet.truncate()
          self._packet.seek(0)
    except socket.error, e:
      Log.error("Socket error while receiving: %s" % str(e))

  def writable(self):
    return len(self._buffer) > 0

  def sendPacket(self, packet):
    self._buffer.append(packet)

  def handlePacket(self, packet):
    pass

  def close(self):
    asyncore.dispatcher.close(self)
    self.handle_close()

  def handleClose(self):
    if self.server:
      self.server.handleConnectionClose(self)
    self.id = None

  def handle_close(self):
    return self.handleClose()

  def handleRegistration(self):
    pass

  def handle_write(self):
    try:
      data = self._buffer[0]
      if not self._sentSizeField:
        self.send(struct.pack("H", len(data)))
        self._sentSizeField = True
      sent = self.send(data)
      data = data[sent:]
      if data:
        self._buffer[0] = data
      else:
        self._buffer = self._buffer[1:]
        self._sentSizeField = False
    except socket.error, e:
      Log.error("Socket error while sending: %s" % str(e))

class Server(asyncore.dispatcher):
  def __init__(self, port = PORT, localOnly = True):
    asyncore.dispatcher.__init__(self)
    self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
    self.set_reuse_addr()
    self.bind((localOnly and "localhost" or "", port))
    self.listen(5)
    self.clients = {}
    self.__idCounter = 0
        
  def handle_accept(self):
    sock, addr = self.accept()
    self.__idCounter += 1
    conn = self.createConnection(sock = sock)
    conn.setServer(self)
    conn.accept(self.__idCounter)
    self.clients[self.__idCounter] = conn
    self.handleConnectionOpen(conn)

  def createConnection(self, sock):
    return Connection(sock = sock)

  def handleConnectionOpen(self, connection):
    pass

  def close(self):
    asyncore.dispatcher.close(self)
    self.handle_close()

  def handleClose(self):
    for c in self.clients.values():
      c.close()

  def handle_close(self):
    return self.handleClose()

  def handleConnectionClose(self, connection):
    if connection.id in self.clients:
      del self.clients[connection.id]

  def broadcastPacket(self, packet, ignore = [], meToo = True):
    for c in self.clients.values():
      if not c.id in ignore:
        c.sendPacket(packet)
    if meToo:
      self.clients.values()[0].handlePacket(packet)

  def sendPacket(self, receiverId, packet):
    self.clients[receiverId].sendPacket(packet)

def communicate(cycles = 1):
  while cycles:
    asyncore.poll(0, asyncore.socket_map)
    cycles -= 1

def shutdown():
  asyncore.close_all()

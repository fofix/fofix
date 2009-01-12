#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2009 myfingershurt                                  #
#               2009 John Stumpo                                    #
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

"""Drop-in replacements for socket and asyncore that implement
loopback connections, sans the loopback connections.  Only the
necessary functionality to replace FoFiX's loopback connection
is implemented.

Limitations:
  - TCP only
  - Address connected to/listened to is ignored.
  - EOF doesn't get passed around correctly, but the rest of the code
    seems to be able to deal with it.
  - socket.errors are raised with strings rather than tuples.
  - All sockets are non-blocking.
  - No support for select().
  - Probably rough around the edges in many other ways.
"""

__version__ = '$Id$'

# Keep track of what ports are being listened to.
class FakeTcpStack(object):
  def __init__(self):
    self.openPorts = {}
  def registerOpenPort(self, port, obj):
    if self.openPorts.has_key(port):
      raise socket.error, 'Address already in use.'
    self.openPorts[port] = obj
  def releaseOpenPort(self, port):
    del self.openPorts[port]
  def connectSocket(self, port, sock):
    if not self.openPorts.has_key(port):
      raise socket.error, 'Connection refused.'
    self.openPorts[port].backlog.append(sock)
tcpStack = FakeTcpStack()  # singleton instance
del FakeTcpStack

# Reimplementation of socket.
class socket(object):
  AF_INET = None
  SOCK_STREAM = None
  class error(Exception):
    pass
  def __init__(self, af, socktype, proto):
    self.bindaddr = None
    self.pairedSocket = None
    self.listening = False
    self.buf = ''
  def __del__(self):
    self.close()
  @staticmethod
  def socket(af, socktype, proto):
    return socket(af, socktype, proto)
  def bind(self, addr):
    if self.listening or (self.pairedSocket is not None) or (self.bindaddr is not None):
      raise socket.error, 'Socket already bound.'
    self.bindaddr = addr
  def listen(self, backlog):
    self.backlog = []
    self.listening = True
    tcpStack.registerOpenPort(self.bindaddr[1], self)
  def accept(self):
    if not self.listening:
      raise socket.error, 'Invalid argument.'
    if not len(self.backlog):
      raise socket.error, 'The socket operation could not complete without blocking.'
    s = self.backlog[0]
    del self.backlog[0]
    return s, ('127.0.0.1', 1024)
  def connect(self, addr):
    self.pairedSocket = socket.socket(None, None, None)
    self.pairedSocket.pairedSocket = self
    tcpStack.connectSocket(addr[1], self.pairedSocket)
  def close(self):
    if self.pairedSocket is not None:
      self.pairedSocket = None
    if self.listening:
      try:
        tcpStack.releaseOpenPort(self.bindaddr[1])
      except:
        pass
      del self.backlog
      self.listening = False
    self.bindaddr = None
  def send(self, buf, length=None):
    if self.pairedSocket is None:
      raise socket.error, 'Socket is not connected.'
    try:
      self.pairedSocket.buf += buf
      return len(buf)
    except:
      self.close()
      raise socket.error, 'Connection reset by peer.'
  sendall = send
  def recv(self, length=4096):
    if self.pairedSocket is None:
      raise socket.error, 'Socket is not connected.'
    try:
      if len(self.buf) == 0:
        raise socket.error, 'The socket operation could not complete without blocking.'
      if len(self.buf) < length:
        buf = self.buf
        self.buf = ''
        return buf
      buf = self.buf[:length]
      self.buf = self.buf[length:]
      return buf
    except socket.error:
      raise
    except:
      self.close()
      raise socket.error, 'Connection reset by peer.'
  def readable(self):
    return (len(self.buf) > 0)
  def writable(self):
    return (self.pairedSocket is not None)
  def acceptable(self):
    return (self.listening and len(self.backlog) > 0)

# Reimplementation of asyncore atop the above.
class asyncore(object):
  socket_map = []
  class dispatcher(object):
    def __init__(self, sock=None):
      self._socket = sock
      self.connected = False
      asyncore.socket_map.append(self)
    def __del__(self):
      self.close()
    def create_socket(self, af, socktype):
      self._socket = socket.socket(af, socktype, 0)
    def set_reuse_addr(self):
      pass
    def bind(self, addr):
      self._socket.bind(addr)
    def listen(self, backlog):
      self._socket.listen(backlog)
    def accept(self):
      return self._socket.accept()
    def close(self):
      if self._socket is not None:
        self._socket.close()
      self._socket = None
      try:
        asyncore.socket_map.remove(self)
      except ValueError:
        pass
    def send(self, data):
      return self._socket.send(data)
    def recv(self, length=4096):
      return self._socket.recv(length)
    def connect(self, addr):
      self._socket.connect(addr)
      self.connected = True
    def readable(self):
      if self._socket is None:
        return False
      return self._socket.readable()
    def writable(self):
      if self._socket is None:
        return False
      return self._socket.writable()
    def acceptable(self):
      if self._socket is None:
        return False
      return self._socket.acceptable()
  @classmethod
  def poll(self, arg, lst):
    for d in lst:
      if d.readable():
        if hasattr(d, 'handle_read'):
          d.handle_read()
      if d.writable():
        if hasattr(d, 'handle_write'):
          d.handle_write()
      if d.acceptable():
        if hasattr(d, 'handle_accept'):
          d.handle_accept()
  @classmethod
  def close_all(self):
    pass

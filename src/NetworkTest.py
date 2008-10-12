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

import unittest
import Network
import time

class TestConnection(Network.Connection):
  def handlePacket(self, packet):
    self.packet = packet

class TestServer(Network.Server):
  def createConnection(self, sock):
    return TestConnection(sock)

class NetworkTest(unittest.TestCase):
  def testHandshake(self):
    s = TestServer()
    c = TestConnection()
    c.connect("localhost")

    c.sendPacket("moikka")

    Network.communicate(100)
    client = s.clients.values()[0]
    assert client.packet == "moikka"
    assert client.id == 1

  def tearDown(self):
    Network.shutdown()

if __name__ == "__main__":
  unittest.main()

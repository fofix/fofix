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
import time

from Engine import Engine
from Resource import Resource

def loader():
  return 0xdada

class ResourceTest(unittest.TestCase):
  def testAsynchLoad(self):
    self.r = Resource()
    self.e.addTask(self.r, synchronized = False)

    self.r.load(self, "result", lambda: loader())

    while not self.result:
      self.e.run()
    
    assert self.result == 0xdada
     
  def testSynchLoad(self):
    self.r = Resource()
    self.e.addTask(self.r, synchronized = False)

    assert self.r.load(self, "result2", loader, synch = True) == 0xdada
    assert self.result2 == 0xdada

  def testAsynchLoadSeries(self):
    self.r = Resource()
    self.e.addTask(self.r, synchronized = False)

    for i in range(10):
      self.r.load(self, "result%d" % i, loader)

    while not self.result9:
      self.e.run()

    assert self.result9 == 0xdada
     
  def testCallback(self):
    self.r = Resource()
    self.e.addTask(self.r, synchronized = False)
    
    self.quux = None
    def loaded(r):
      self.quux = r
    
    self.r.load(self, "fuuba", loader, onLoad = loaded).join()
    
    while not self.fuuba:
      self.e.run()
    
    assert self.fuuba == self.quux
     
  def setUp(self):
    self.e = Engine()
    
  def tearDown(self):
    self.e.quit()

if __name__ == "__main__":
  unittest.main()

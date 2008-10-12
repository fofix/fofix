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
import Object

class TestMessage(Object.Message):
  pass

manager = Object.Manager()

class TestObject(Object.Object):
  def __init__(self, id = None, name = "unnamed", manager = manager):
    Object.Object.__init__(self, id, name = name, manager = manager)
    self.x = 1
    self.y = 2
    self.z = 3
    self.name = name
    self.share("x", "y", "z", "name")
    self.connect(TestMessage, self.message)

  def message(self, message):
    self.lastMessage = message

class ObjectTest(unittest.TestCase):
  def testAttributes(self):
    o = TestObject()
    o.x = 1234
    data = o.getChanges()
    assert data
    assert not o.getChanges()
    o.applyChanges(data)
    
    o2 = TestObject()
    o2.applyChanges(data)
    assert o.x == o2.x
    o2.x = 5678
    o.applyChanges(o2.getChanges())
    assert not o.getChanges()
    assert not o2.getChanges()
    assert o.x == o2.x

  def testMessaging(self):
    o = TestObject()
    o2 = TestObject()

    o.emit(TestMessage())
    o2.applyChanges(o.getChanges())

    assert isinstance(o.lastMessage, TestMessage)
    assert isinstance(o2.lastMessage, TestMessage)
    
  def testManagerStateMigration(self):
    o = TestObject(name = "first")
    o.x = 31337

    id = manager.id
    objId = o.id
    data = manager.getChanges(everything = True)
    assert data

    manager.reset()
    manager.setId(1)
    manager.applyChanges(id, data)

    o2 = manager.objects[objId]
    assert o2.x == o.x
    assert o2 is not o

    o3 = TestObject(name = "third")
    obj3Id = o3.id
    o3.x = 0xdada
    
    o4 = TestObject(name = "fourth")
    obj4Id = o4.id
    o4.delete()

    # read the differential states
    manager.getChanges()
    
    data = manager.getChanges(everything = True)
    
    manager.reset()
    manager.setId(2)
    manager.applyChanges(id, data)

    assert objId in manager.objects
    assert obj3Id in manager.objects
    assert obj4Id not in manager.objects
    assert manager.objects[obj3Id].x == 0xdada

  def testReferences(self):
    o = TestObject(name = "bag")
    o2 = TestObject(name = "apple")
    o.x = [o2]
    ids = [o.id, o2.id]

    data = manager.getChanges()
    manager.reset()
    manager.setId(1)
    manager.applyChanges(id, data)

    o = manager.objects[ids[0]]
    o2 = manager.objects[ids[1]]

    assert o.name == "bag"
    assert o2.name == "apple"
    assert o2 in o.x

  def testMultipleManagers(self):
    m1 = Object.Manager(1000)
    m2 = Object.Manager(2000)

    o1 = TestObject(manager = m1)
    o2 = TestObject(manager = m2)

    m1.applyChanges(m2.id, m2.getChanges())
    m2.applyChanges(m1.id, m1.getChanges())

    assert len(m1.objects) == 2
    assert len(m2.objects) == 2

  def tearDown(self):
    manager.reset()

if __name__ == "__main__":
  unittest.main()

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

class Serializer(pickle.Pickler):
  def persistent_id(self, obj):
    return getattr(obj, "id", None)

class Unserializer(pickle.Unpickler):
  def __init__(self, manager, data):
    pickle.Unpickler.__init__(self, data)
    self.manager = manager
    
  def persistent_load(self, id):
    return self.manager.getObject(id)

def serialize(data):
  file = StringIO()
  Serializer(file, protocol = 2).dump(data)
  return file.getvalue()

def unserialize(manager, data):
  return Unserializer(manager, StringIO(data)).load()

class Manager:
  MSG_CREATE = 0
  MSG_CHANGE = 1
  MSG_DELETE = 2
  
  def __init__(self, id = 0):
    self.id = id
    self.reset()

  def setId(self, id):
    self.id = id

  def reset(self):
    self.objects = {}
    self.__creationData = {}
    self.__created = []
    self.__changed = []
    self.__deleted = []
    self.__idCounter = 0

  def createObject(self, instance, *args, **kwargs):
    self.__idCounter += 1
    id = self.globalObjectId(self.__idCounter)
    self.objects[id] = instance
    self.__creationData[id] = (instance.__class__, args, kwargs)
    self.__created.append(instance)
    return id

  def setChanged(self, obj):
    if not obj in self.__changed:
      self.__changed.append(obj)

  def deleteObject(self, obj):
    del self.objects[obj.id]
    del self.__creationData[obj.id]
    if obj in self.__created: self.__created.remove(obj)
    self.__deleted.append(obj.id)

  def getObject(self, id):
    return self.objects.get(id, None)

  def getChanges(self, everything = False):
    data = []
    if everything:
      data += [(self.MSG_CREATE, [(id, data) for id, data in self.__creationData.items()])]
      data += [(self.MSG_CHANGE, [(o.id, o.getChanges(everything = True)) for o in self.objects.values()])]
    else:
      if self.__created: data += [(self.MSG_CREATE, [(o.id, self.__creationData[o.id]) for o in self.__created])]
      if self.__changed: data += [(self.MSG_CHANGE, [(o.id, o.getChanges()) for o in self.__changed])]
      if self.__deleted: data += [(self.MSG_DELETE, self.__deleted)]
      self.__created = []
      self.__changed = []
      self.__deleted = []
    return [serialize(d) for d in data]

  def globalObjectId(self, objId):
    return (self.id << 20) + objId

  def applyChanges(self, managerId, data):
    for d in data:
      try:
        msg, data = unserialize(self, d)
        if msg == self.MSG_CREATE:
          for id, data in data:
            objectClass, args, kwargs = data
            self.__creationData[id] = data
            self.objects[id] = objectClass(id = id, manager = self, *args, **kwargs)
        elif msg == self.MSG_CHANGE:
          for id, data in data:
            if data: self.objects[id].applyChanges(data)
        elif msg == self.MSG_DELETE:
          id = data
          del self.__creationData[id]
          del self.objects[id]
      except Exception, e:
        print "Exception %s while processing incoming changes from manager %s." % (str(e), managerId)
        raise

def enableGlobalManager():
  global manager
  manager = Manager()

class Message:
  classes = {}
  
  def __init__(self):
    if not self.__class__ in self.classes:
      self.classes[self.__class__] = len(self.classes)
    self.id = self.classes[self.__class__]

class ObjectCreated(Message):
  pass    

class ObjectDeleted(Message):
  def __init__(self, obj):
    self.object = obj

class Object(object):
  def __init__(self, id = None, manager = None, *args, **kwargs):
    self.__modified = {}
    self.__messages = []
    self.__messageMap = {}
    self.__shared = []
    #if not manager: manager = globals()["manager"]
    self.manager = manager
    self.id = id or manager.createObject(self, *args, **kwargs)

  def share(self, *attr):
    [(self.__shared.append(str(a)), self.__modified.__setitem__(a, self.__dict__[a])) for a in attr]

  def __setattr__(self, attr, value):
    if attr in getattr(self, "_Object__shared", {}):
      self.__modified[attr] = value
      self.manager.setChanged(self)
    object.__setattr__(self, attr, value)

  def delete(self):
    self.emit(ObjectDeleted(self))
    self.manager.deleteObject(self)

  def getChanges(self, everything = False):
    if self.__messages:
      self.__modified["_Object__messages"] = self.__messages
    
    self.__processMessages()

    if everything:
      return dict([(k, getattr(self, k)) for k in self.__shared])

    if self.__modified:
      (data, self.__modified) = (self.__modified, {})
      return data

  def applyChanges(self, data):
    self.__dict__.update(data)
    self.__processMessages()
    
  def emit(self, message):
    self.__messages.append(message)

  def connect(self, messageClass, callback):
    if not messageClass in self.__messageMap:
      self.__messageMap[messageClass] = []
    self.__messageMap[messageClass].append(callback)

  def disconnect(self, messageClass, callback):
    if messageClass in self.__messageMap:
      self.__messageMap[messageClass].remove(callback)

  def __processMessages(self):
    for m in self.__messages:
      if m.__class__ in self.__messageMap:
        for c in self.__messageMap[m.__class__]:
          c(m)
    self.__messages = []

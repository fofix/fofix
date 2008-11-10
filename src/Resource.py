#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
#               2008 evilynux <evilynux@gmail.com>                  #
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

import os
from Queue import Queue, Empty
from threading import Thread, BoundedSemaphore
import time
import shutil
import stat
import Config

from Task import Task
import Log
import Version

class Loader(Thread):
  def __init__(self, target, name, function, resultQueue, loaderSemaphore, onLoad = None):
    Thread.__init__(self)
    self.semaphore   = loaderSemaphore
    self.target      = target
    self.name        = name
    self.function    = function
    self.resultQueue = resultQueue
    self.result      = None
    self.onLoad      = onLoad
    self.exception   = None
    self.time        = 0.0
    self.canceled    = False

    #myfingershurt: the following should be global and done ONCE:
    #self.game_priority = Config.get("performance", "game_priority")


    if target and name:
      setattr(target, name, None)

  def run(self):
    self.semaphore.acquire()
    game_priority = Config.get("performance", "game_priority")
    # Reduce priority on posix
    if os.name == "posix":
      # evilynux - Beware, os.nice _decreases_ priority, hence the reverse logic
      os.nice(5 - game_priority)
    elif os.name == "nt":
      #myfingershurt: the following should be global and done ONCE:
      #self.setPriority(priority = self.game_priority)

      #...or maybe not at all...
      self.setPriority(priority = game_priority)
      
      #wont work without ctypes
      #self.enableScreenSaver(0)

    self.load()
    self.semaphore.release()
    self.resultQueue.put(self)

  def __str__(self):
    return "%s(%s) %s" % (self.function.__name__, self.name, self.canceled and "(canceled)" or "")

  def setPriority(self, pid = None, priority = 2):
    """ Set The Priority of a Windows Process.  Priority is a value between 0-5 where
        2 is normal priority.  Default sets the priority of the current
        python process but can take any valid process ID. """
        
    import win32api, win32process, win32con
    
    priorityClasses = [win32process.IDLE_PRIORITY_CLASS,
                       win32process.BELOW_NORMAL_PRIORITY_CLASS,
                       win32process.NORMAL_PRIORITY_CLASS,
                       win32process.ABOVE_NORMAL_PRIORITY_CLASS,
                       win32process.HIGH_PRIORITY_CLASS,
                       win32process.REALTIME_PRIORITY_CLASS]

    pid = win32api.GetCurrentProcessId()
    handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
    win32process.SetPriorityClass(handle, priorityClasses[priority])
    win32process.SetProcessAffinityMask(handle, 1)

#  def enableScreenSaver(self, on):
#    import ctypes
#    SPI_SETSCREENSAVEACTIVE = 17
#    ctypes.windll.user32.SystemParametersInfoA(SPI_SETSCREENSAVEACTIVE, on, None, 0)
    
  def cancel(self):
    self.canceled = True

  def load(self):
    try:
      start = time.time()
      self.result = self.function()
      self.time = time.time() - start
    except:
      import sys
      self.exception = sys.exc_info()

  def finish(self):
    if self.canceled:
      return
    
    Log.notice("Loaded %s.%s in %.3f seconds" % (self.target.__class__.__name__, self.name, self.time))
    
    if self.exception:
      raise self.exception[0], self.exception[1], self.exception[2]
    if self.target and self.name:
      setattr(self.target, self.name, self.result)
    if self.onLoad:
      self.onLoad(self.result)
    return self.result

  def __call__(self):
    self.join()
    return self.result

class Resource(Task):
  def __init__(self, dataPath = os.path.join("..", "data")):
    self.resultQueue = Queue()
    self.dataPaths = [dataPath]
    self.loaderSemaphore = BoundedSemaphore(value = 1)
    self.loaders = []

    #myfingershurt: the following should be global, and only done at startup.  Not every damn time a file is loaded.
    self.songPath = []
    self.baseLibrary = Config.get("game", "base_library")
    #evilynux - Support for songs in ~/.fretsonfire/songs (GNU/Linux and MacOS X)
    if self.baseLibrary == "None" and os.name == "posix":
      path = os.path.expanduser("~/." + Version.appName())
      if os.path.isdir(path):
        self.baseLibrary = path
        Config.set("game", "base_library", path)

    if self.baseLibrary and os.path.isdir(self.baseLibrary):
      self.songPath = [self.baseLibrary]


  #myfingershurt: Need a function to refresh the base library after a new one is selected:
  def refreshBaseLib(self):
    self.baseLibrary = Config.get("game", "base_library")
    if self.baseLibrary and os.path.isdir(self.baseLibrary):
      self.songPath = [self.baseLibrary]
  
      

  def addDataPath(self, path):
    if not path in self.dataPaths:
      self.dataPaths = [path] + self.dataPaths

  def removeDataPath(self, path):
    if path in self.dataPaths:
      self.dataPaths.remove(path)

  def fileName(self, *name, **args):
    
    #myfingershurt: the following should be global, and only done at startup.  Not every damn time a file is loaded.
    #songPath = []
    #baseLibrary = Config.get("game", "base_library")
    #if baseLibrary and os.path.isdir(baseLibrary):
    #  songPath = [baseLibrary]
    baseLibrary = self.baseLibrary
    songPath = self.songPath
      
    if not args.get("writable", False):
      for dataPath in self.dataPaths + songPath:
        readOnlyPath = os.path.join(dataPath, *name)
        # If the requested file is in the read-write path and not in the
        # read-only path, use the existing read-write one.
        if os.path.isfile(readOnlyPath):
          return readOnlyPath
        elif os.path.isdir(readOnlyPath):
          return readOnlyPath
        readWritePath = os.path.join(getWritableResourcePath(), *name)
        if os.path.isfile(readWritePath):
          return readWritePath
      return readOnlyPath
    else:
      for dataPath in [self.dataPaths[-1]] + songPath:
        readOnlyPath = os.path.join(dataPath, *name)
        if not (os.path.isfile(readOnlyPath) or os.path.isdir(readOnlyPath)):
          continue
        try:
          # First see if we can write to the original file
          if os.access(readOnlyPath, os.W_OK):
            return readOnlyPath
          # If the original file does not exist, see if we can write to its directory
          if not os.path.isfile(readOnlyPath) and os.access(os.path.dirname(readOnlyPath), os.W_OK):
            pass
            #return readOnlyPath
        except:
          raise
        # If the resource exists in the read-only path, make a copy to the
        # read-write path.
        readWritePath = os.path.join(getWritableResourcePath(), *name)
        if not os.path.isfile(readWritePath) and os.path.isfile(readOnlyPath):
          Log.notice("Copying '%s' to writable data directory." % "/".join(name))
          try:
            os.makedirs(os.path.dirname(readWritePath))
          except:
            pass
          shutil.copy(readOnlyPath, readWritePath)
          self.makeWritable(readWritePath)
        # Create directories if needed
        if not os.path.isdir(readWritePath) and os.path.isdir(readOnlyPath):
          Log.notice("Creating writable directory '%s'." % "/".join(name))
          os.makedirs(readWritePath)
          self.makeWritable(readWritePath)
        return readWritePath
      return readOnlyPath
    
  def makeWritable(self, path):
    os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
  
  def load(self, target = None, name = None, function = lambda: None, synch = False, onLoad = None):
    Log.notice("Loading %s.%s %s" % (target.__class__.__name__, name, synch and "synchronously" or "asynchronously"))
    l = Loader(target, name, function, self.resultQueue, self.loaderSemaphore, onLoad = onLoad)
    if synch:
      l.load()
      return l.finish()
    else:
      self.loaders.append(l)
      l.start()
      return l

  def run(self, ticks):
    try:
      loader = self.resultQueue.get_nowait()
      loader.finish()
      self.loaders.remove(loader)
    except Empty:
      pass

def getWritableResourcePath():
  """
  Returns a path that holds the configuration for the application.
  """
  path = "."
  appname = Version.appName()
  if os.name == "posix":
    path = os.path.expanduser("~/." + appname)
  elif os.name == "nt":
    try:
      path = os.path.join(os.environ["APPDATA"], appname)
    except:
      pass
  try:
    os.mkdir(path)
  except:
    pass
  return path

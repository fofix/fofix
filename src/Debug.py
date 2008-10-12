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

from OpenGL.GL import *
from View import Layer

import gc
import threading
import Log
import Version
import os
import datetime
import zipfile
import Theme
import Stage

class DebugLayer(Layer):
  """A layer for showing some debug information."""
  def __init__(self, engine):
    self.engine = engine
    #gc.set_debug(gc.DEBUG_LEAK)

  def className(self, instance):
    return str(instance.__class__).split(".")[1]
  
  def render(self, visibility, topMost):
    self.engine.view.setOrthogonalProjection(normalize = True)
    
    try:
      font = self.engine.data.font
      scale = 0.0008
      glColor3f(.25, 1, .25)

      x, y = (.05, .05)
      h = font.getHeight() * scale
      
      font.render("Tasks:", (x, y), scale = scale)
      for task in self.engine.tasks + self.engine.frameTasks:
        font.render(self.className(task), (x + .1, y), scale = scale)
        y += h
        
      x, y = (.5, .05)
      font.render("Layers:", (x, y), scale = scale)
      for layer in self.engine.view.layers + self.engine.view.incoming + self.engine.view.outgoing + self.engine.view.visibility.keys():
        font.render(self.className(layer), (x + .1, y), scale = scale)
        y += h
        
      x, y = (.05, .4)
      font.render("Scenes:", (x, y), scale = scale)
      if "world" in dir(self.engine.server):
        for scene in self.engine.server.world.scenes:
          font.render(self.className(scene), (x + .1, y), scale = scale)
          y += h
        
      x, y = (.5, .4)
      font.render("Loaders:", (x, y), scale = scale)
      for loader in self.engine.resource.loaders:
        font.render(str(loader), (x + .1, y), scale = scale)
        y += h
        
      x, y = (.5, .55)
      font.render("Input:", (x, y), scale = scale)
      for listener in self.engine.input.mouseListeners + \
                      self.engine.input.keyListeners + \
                      self.engine.input.systemListeners + \
                      self.engine.input.priorityKeyListeners:
        font.render(self.className(listener), (x + .1, y), scale = scale)
        y += h
        
      x, y = (.05, .55)
      font.render("System:", (x, y), scale = scale)
      font.render("%d threads" % threading.activeCount(), (x + .1, y), scale = scale)
      y += h
      font.render("%.2f fps" % self.engine.timer.fpsEstimate, (x + .1, y), scale = scale)
      y += h
      font.render("%d sessions, server %s" % (len(self.engine.sessions), self.engine.server and "on" or "off"), (x + .1, y), scale = scale)
      #y += h
      #font.render("%d gc objects" % len(gc.get_objects()), (x + .1, y), scale = scale)
      #y += h
      #font.render("%d collected" % gc.collect(), (x + .1, y), scale = scale)

    finally:
      self.engine.view.resetProjection()

  def gcDump(self):
    import World
    before = len(gc.get_objects())
    coll   = gc.collect()
    after  = len(gc.get_objects())
    Log.debug("%d GC objects collected, total %d -> %d." % (coll, before, after))
    fn = "gcdump.txt"
    f = open(fn, "w")
    n = 0
    gc.collect()
    for obj in gc.garbage:
      try:
        print >>f, obj
        n += 1
      except:
        pass
    f.close()
    Log.debug("Wrote a dump of %d GC garbage objects to %s." % (n, fn))

  def debugOut(self, engine):
    f = open("debug.txt", "w+")
    version = Version.version()
    currentDir = os.getcwd()
    dataDir = Version.dataPath()
    translationDir = dataDir + "/translations"
    modsDir = dataDir + "/mods"

    f.write("Date = %s\n" % datetime.datetime.now())   
    f.write("\nVersion = %s\n" %  version)
    f.write("\nOS = %s\n" % os.name)

    f.write("\nCurrent Directory = %s\n" % currentDir)
    self.directoryList(f, currentDir)

    f.write("\nData Directory = %s\n" % dataDir)
    self.directoryList(f, dataDir)

    f.write("\nLibrary.zip\n")
    zip = zipfile.ZipFile(dataDir + "/library.zip", 'r')
    for info in zip.infolist():
      fileName = info.filename
      fileCSize = info.compress_size
      fileSize = info.file_size
      fileDate = datetime.datetime(*(info.date_time))
      f.write("%s, %s, %s, %s\n" % (fileName, fileCSize, fileSize, fileDate))

    
    f.write("\nTranslation Directory = %s\n" % translationDir)
    self.directoryList(f, translationDir)
    
    f.write("\nMods Directory = %s\n" % modsDir)
    self.directoryList(f, modsDir)

    mods = os.listdir(modsDir)

    for mod in mods:
      modDir = os.path.join(modsDir, mod)
      if os.path.isdir(modDir):
        f.write("\nMod Directory = %s\n" % modDir)
        self.directoryList(f, modDir)

    f.write("\nFretsonfire.ini\n")   
    engine.config.config.write(f)

    f.write("\nTheme.ini\n")   
    Theme.write(f, engine.config)

    f.write("\nStage.ini\n")
    stage = Stage.Stage(self, self.engine.resource.fileName("stage.ini"))
    stage.config.write(f)
    f.close()

  def directoryList(self, f, root):
    files = os.listdir(root)
    
    for fileName in files:
      fileSize = os.path.getsize(os.path.join(root, fileName))
      mTime = datetime.datetime.utcfromtimestamp(os.path.getmtime(os.path.join(root, fileName)))
      cTime = datetime.datetime.utcfromtimestamp(os.path.getctime(os.path.join(root, fileName)))
      aTime = datetime.datetime.utcfromtimestamp(os.path.getatime(os.path.join(root, fileName)))

      f.write("%s, %s, %s, %s, %s\n" % (fileName, fileSize, mTime, cTime, aTime))

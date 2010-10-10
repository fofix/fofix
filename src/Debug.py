#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2006 Sami Kyöstilä                                  #
# Copyright (C) 2009 FoFiX Team                                     #
# Copyright (C) 2009 akedrou                                        #                                     
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

from __future__ import with_statement

from View import Layer
from OpenGL.GL import glColor3f
import gc
import threading
import Log




class DebugLayer(Layer):
  """A layer for showing some debug information."""
  def __init__(self, engine):
    self.engine = engine
    #gc.set_debug(gc.DEBUG_LEAK)

  def className(self, instance):
    return str(instance.__class__).split(".")[1]
  
  def render(self, visibility, topMost):
    with self.engine.view.orthogonalProjection(normalize = True):
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
      for layer in self.engine.view.layers:
        try:
          v = self.engine.view.visibility[layer]
        except KeyError:
          v = -1
        font.render("%s - v = %.2f" % (self.className(layer), v), (x + .1, y), scale = scale)
        y += h
      glColor3f(.25, 1, .75)
      for layer in self.engine.view.incoming:
        font.render("Adding %s..."%self.className(layer), (x + .1, y), scale = scale)
        y += h
      glColor3f(1, .25, .25)
      for layer in self.engine.view.outgoing:
        font.render("Removing %s..."%self.className(layer), (x + .1, y), scale = scale)
        y += h
      
      glColor3f(.25, 1, .25)
      x, y = (.05, .4)
      font.render("Current Scene:", (x, y), scale = scale)
      if self.engine.world:
        text = self.engine.world.sceneName
        if text == "":
          text = "None (In Lobby)"
      else:
        text = "None (In Menu)"
      font.render(text, (x + .1, y), scale = scale)
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
                      self.engine.input.systemListeners:
        font.render(self.className(listener), (x + .1, y), scale = scale)
        y += h
      for listener in self.engine.input.priorityKeyListeners:
        font.render(self.className(listener)+" (Priority)", (x + .1, y), scale = scale)
        y += h
        
      x, y = (.05, .55)
      font.render("System:", (x, y), scale = scale)
      font.render("%d threads" % threading.activeCount(), (x + .1, y), scale = scale)
      y += h
      font.render("%.2f fps" % self.engine.fpsEstimate, (x + .1, y), scale = scale)
      #y += h
      #font.render("%d sessions, server %s" % (len(self.engine.sessions), self.engine.server and "on" or "off"), (x + .1, y), scale = scale)
      #y += h
      #font.render("%d gc objects" % len(gc.get_objects()), (x + .1, y), scale = scale)
      #y += h
      #font.render("%d collected" % gc.collect(), (x + .1, y), scale = scale)

  def gcDump(self):
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

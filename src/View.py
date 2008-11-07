#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 QQStarS                                        #
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

from __future__ import division
from OpenGL.GL import *
from OpenGL.GLU import *

import Log

from Task import Task

class Layer(Task):
  def render(self, visibility, topMost):
    pass
    
  def shown(self):
    pass
  
  def hidden(self):
    pass

  def run(self, ticks):
    pass

  def isBackgroundLayer(self):
    return False

class BackgroundLayer(Layer):
  def isBackgroundLayer(self):
    return True

class View(Task):
  def __init__(self, engine, geometry = None, screens = 1):
    Task.__init__(self)
    self.layers = []
    self.incoming = []
    self.outgoing = []
    self.visibility = {}
    self.transitionTime = 512.0
    self.geometry = geometry or glGetIntegerv(GL_VIEWPORT)
    self.savedGeometry = None
    self.engine = engine
    w = self.geometry[2] - self.geometry[0]
    h = self.geometry[3] - self.geometry[1]
    self.aspectRatio = float(w) / float(h)

  def pushLayer(self, layer):
    Log.debug("View: Push: %s" % layer.__class__.__name__)
    
    if not layer in self.layers:
      self.layers.append(layer)
      self.incoming.append(layer)
      self.visibility[layer] = 0.0
      layer.shown()
    elif layer in self.outgoing:
      layer.hidden()
      layer.shown()
      self.outgoing.remove(layer)
    self.engine.addTask(layer)

  def topLayer(self):
    layers = list(self.layers)
    layers.reverse()
    for layer in layers:
      if layer not in self.outgoing:
        return layer

  def popLayer(self, layer):
    Log.debug("View: Pop: %s" % layer.__class__.__name__)
    
    if layer in self.incoming:
      self.incoming.remove(layer)
    if layer in self.layers and not layer in self.outgoing:
      self.outgoing.append(layer)

  def popAllLayers(self):
    Log.debug("View: Pop all")
    [self.popLayer(l) for l in list(self.layers)]

  def isTransitionInProgress(self):
    return self.incoming or self.outgoing
    
  def run(self, ticks):
    if not self.layers:
      return

    topLayer = self.topLayer()
    t = ticks / self.transitionTime
    for layer in list(self.layers):
      if not layer in self.visibility:
        continue
      if layer in self.outgoing or (layer is not topLayer and not layer.isBackgroundLayer()):
        if self.visibility[layer] > 0.0:
          self.visibility[layer] = max(0.0, self.visibility[layer] - t)
        else:
          self.visibility[layer] = 0.0
          if layer in self.outgoing:
            self.outgoing.remove(layer)
            self.layers.remove(layer)
            del self.visibility[layer]
            self.engine.removeTask(layer)
            layer.hidden()
          if layer in self.incoming:
            self.incoming.remove(layer)
      elif layer in self.incoming or layer is topLayer:
        if self.visibility[layer] < 1.0:
          self.visibility[layer] = min(1.0, self.visibility[layer] + t)
        else:
          self.visibility[layer] = 1.0
          if layer in self.incoming:
            self.incoming.remove(layer)

  def setOrthogonalProjection(self, normalize = True, yIsDown = True):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    viewport = glGetIntegerv(GL_VIEWPORT)
    if normalize:
      w = viewport[2] - viewport[0]
      h = viewport[3] - viewport[1]
      # aspect ratio correction
      h *= (float(w) / float(h)) / (4.0 / 3.0)
      viewport = [0, 0, 1, h / w]
  
    if yIsDown:
      glOrtho(viewport[0], viewport[2] - viewport[0],
              viewport[3] - viewport[1], viewport[1], -100, 100);
    else:
      glOrtho(viewport[0], viewport[2] - viewport[0],
              viewport[1], viewport[3] - viewport[1], -100, 100);
    glMatrixMode(GL_MODELVIEW);
    glPushMatrix();
    glLoadIdentity();
  
  def resetProjection(self):
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

  def setGeometry(self, geometry, screens=1):
    viewport = glGetIntegerv(GL_VIEWPORT)
    w = viewport[2] - viewport[0]
    h = viewport[3] - viewport[1]
    s = (w, h, w, h)

    geometry = tuple([(type(coord) == float) and int(s[i] * coord) or int(coord) for i, coord in enumerate(geometry)])
#    geometry[0] = int(geometry[0] / screens)
#    geometry[2] = int(geometry[2] / screens)
#    geometry = tuple(geometry)
    self.savedGeometry, self.geometry = viewport, geometry
    glViewport(int(geometry[0]), int(geometry[1]), int(geometry[2]), int(geometry[3]))
    glScissor(int(geometry[0]), int(geometry[1]), int(geometry[2]), int(geometry[3]))

  def setViewport(self, screens=1, screen=0):
    geometry = list(self.savedGeometry)
    if screens != 1:
      geometry[0] = int(geometry[0]+((screen-0.2)*geometry[2]/screens))
      geometry[2] = int(geometry[2]*1.4/screens)
      geometry[1] = int(geometry[1]) #QQstarS:
      geometry[3] = int(geometry[3]*1.6/screens)  #QQstarS
    geometry = tuple(geometry)
    self.geometry = geometry

    glViewport(int(geometry[0]), int(geometry[1]), int(geometry[2]), int(geometry[3]))
    glScissor(int(geometry[0]), int(geometry[1]), int(geometry[2]), int(geometry[3]))

  def setViewportHalf(self, screens=1, screen=0):
    geometry = list(self.savedGeometry)
    if screens != 1:
      geometry[0] = int(geometry[0]+(screen*geometry[2]/screens))
      geometry[2] = int(geometry[2]/screens) 
      geometry[1] = int(geometry[1])#+(geometry[3]/screens*2/3)) #QQstarS
      geometry[3] = int((geometry[3]/screens)*1.5) #QQstarS: make the Y postion smaller
    geometry = tuple(geometry)
    self.geometry = geometry

    glViewport(int(geometry[0]), int(geometry[1]), int(geometry[2]), int(geometry[3]))
    glScissor(int(geometry[0]), int(geometry[1]), int(geometry[2]), int(geometry[3]))    

  def resetGeometry(self):
    assert self.savedGeometry
    
    self.savedGeometry, geometry = None, self.savedGeometry
    self.geometry = geometry
    glViewport(int(geometry[0]), int(geometry[1]), int(geometry[2]), int(geometry[3]))
    glScissor(int(geometry[0]), int(geometry[1]), int(geometry[2]), int(geometry[3]))

  def render(self):
    #print [(str(m.__class__), v) for m, v in self.visibility.items()]
    for layer in self.layers:
      layer.render(self.visibility[layer], layer == self.layers[-1])

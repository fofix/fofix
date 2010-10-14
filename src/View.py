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
from contextlib import contextmanager

import numpy as np

import Log

from Task import Task

class Layer(Task):
  def __getattr__(self, name):  #for new out-themed rendering
    if name.startswith("img_"): #rather than try-except, just expect None on no image.
      return None
    else:
      e = str(self.__class__).split(".")[1] + " has no attribute '%s'" % name
      raise AttributeError(e)
  
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
    self.engine = engine
    if geometry:
      self.geometry = list(geometry)
    else:
      self.geometry = list(glGetIntegerv(GL_VIEWPORT))
    w = self.geometry[2] - self.geometry[0]
    h = self.geometry[3] - self.geometry[1]
    self.aspectRatio = float(w) / float(h)
    self.geometryNormalized = [0,0,0,0]
    self.setNormalizedGeometry()
    self.geometryAll = None
    self.initGeometryAll()
    self.geometryAllHalf = None
    self.initGeometryAllHalf()

  def initGeometryAll(self):
    #precalculate geometry for all screens
    maxScreens = 4
    screensArray = np.zeros((maxScreens,maxScreens,4))
    for screens in range(1,maxScreens+1):
      screenArray = np.zeros((screens,4))
      for screen in range(0,screens):
        if screens == 1:
          screenArray[screen][0] = self.geometry[0]
          screenArray[screen][1] = self.geometry[1]
          screenArray[screen][2] = self.geometry[2]
          screenArray[screen][3] = self.geometry[3]
        else:
          screenArray[screen][0] = int(self.geometry[0]+((screen-0.2)*self.geometry[2]/screens))
          screenArray[screen][2] = int(self.geometry[2]*1.4/screens)
          screenArray[screen][1] = int(self.geometry[1]) #QQstarS:
          screenArray[screen][3] = int(self.geometry[3]*1.6/screens)  #QQstarS
        screensArray[screens-1][screen][:] = screenArray[screen]

    self.geometryAll = screensArray

  def initGeometryAllHalf(self):
    #precalculate geometryHalf for all screens
    maxScreens = 4
    screensArray = np.zeros((maxScreens,maxScreens,4))
    for screens in range(1,maxScreens+1):
      screenArray = np.zeros((screens,4))
      for screen in range(0,screens):
        if screens == 1:
          screenArray[screen][0] = self.geometry[0]
          screenArray[screen][1] = self.geometry[1]
          screenArray[screen][2] = self.geometry[2]
          screenArray[screen][3] = self.geometry[3]
        else: 
          screenArray[screen][0] = int(self.geometry[0]+(screen*self.geometry[2]/screens))
          screenArray[screen][2] = int(self.geometry[2]/screens) 
          screenArray[screen][1] = int(self.geometry[1])#+(geometry[3]/screens*2/3)) #QQstarS
          screenArray[screen][3] = int((self.geometry[3]/screens)*1.5) #QQstarS: make the Y postion smaller
        screensArray[screens-1][screen][:] = screenArray[screen]

    self.geometryAllHalf = screensArray

  def setNormalizedGeometry(self):
    w = self.geometry[2] - self.geometry[0]
    h = self.geometry[3] - self.geometry[1]
    # aspect ratio correction
    h *= (float(w) / float(h)) / (4.0 / 3.0)
    self.geometryNormalized[0] = 0
    self.geometryNormalized[1] = 0
    self.geometryNormalized[2] = 1
    self.geometryNormalized[3] = h / w

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
    layer = self.layers[-1]
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

    topLayer = self.layers[-1]
    
    t = self.engine.clock.get_time() / self.transitionTime
    
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
      elif layer in self.incoming or layer is topLayer or layer.isBackgroundLayer():
        if self.visibility[layer] < 1.0:
          self.visibility[layer] = min(1.0, self.visibility[layer] + t)
        else:
          self.visibility[layer] = 1.0
          if layer in self.incoming:
            self.incoming.remove(layer)

  @contextmanager
  def orthogonalProjection(self, normalize = True, yIsDown = True):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    if normalize:
      if yIsDown:
        glOrtho(self.geometryNormalized[0], self.geometryNormalized[2] - self.geometryNormalized[0],
                self.geometryNormalized[3] - self.geometryNormalized[1], self.geometryNormalized[1], -100, 100);
      else:
        glOrtho(self.geometryNormalized[0], self.geometryNormalized[2] - self.geometryNormalized[0],
                self.geometryNormalized[1], self.geometryNormalized[3] - self.geometryNormalized[1], -100, 100);
    else:
      glOrtho(self.geometry[0], self.geometry[2] - self.geometry[0],
            self.geometry[1], self.geometry[3] - self.geometry[1], -100, 100);

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    try:
      yield
    finally:
      glMatrixMode(GL_PROJECTION)
      glPopMatrix()
      glMatrixMode(GL_MODELVIEW)
      glPopMatrix()

  def setGeometry(self, geometry, screens=1):
    self.geometry[0] = int(geometry[0])
    self.geometry[1] = int(geometry[1])
    self.geometry[2] = int(geometry[2])
    self.geometry[3] = int(geometry[3])
    self.initGeometryAll()
    self.initGeometryAllHalf()
    self.setViewport(screens)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

  def setViewport(self, screens=1, screen=0):
    viewport = [int(self.geometryAll[screens-1,screen,0]), 
                int(self.geometryAll[screens-1,screen,1]),
                int(self.geometryAll[screens-1,screen,2]),
                int(self.geometryAll[screens-1,screen,3])]
    
    glViewport(*viewport)
    glScissor (*viewport)

  def setViewportHalf(self, screens=1, screen=0):
    viewport = [int(self.geometryAllHalf[screens-1,screen,0]),
                int(self.geometryAllHalf[screens-1,screen,1]),
                int(self.geometryAllHalf[screens-1,screen,2]),
                int(self.geometryAllHalf[screens-1,screen,3])]
    glViewport(*viewport)
    glScissor (*viewport)
    
  def render(self):
    for layer in self.layers:
      layer.render(self.visibility[layer], layer == self.layers[-1])

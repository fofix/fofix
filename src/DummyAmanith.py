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

"""Mock amanith implementation that does next to nothing."""

from OpenGL.GL import *

G_LOW_RENDERING_QUALITY    = 0
G_NORMAL_RENDERING_QUALITY = 1
G_HIGH_RENDERING_QUALITY   = 2

class GKernel:
  pass

class GMatrix33:
  pass

class GOpenGLBoard:
  def __init__(*a, **b):
    pass

  def SetShadersEnabled(self, foo):
    pass

  def SetViewport(self, x, y, w, h):
    glViewport(int(x), int(y), int(w), int(h))

  def SetProjection(self, left, right, bottom, top):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(left, right, bottom, top, -100, 100)
    glMatrixMode(GL_MODELVIEW)

  def SetRenderingQuality(self, q):
    pass

  def Clear(self, r, g, b, a):
    glDepthMask(1)
    glEnable(GL_COLOR_MATERIAL)
    glClearColor(r, g, b, a)
    glClear(GL_COLOR_BUFFER_BIT | GL_STENCIL_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

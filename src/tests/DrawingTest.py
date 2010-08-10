#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#####################################################################
# Drawing methods comparison (part of FoFiX)                        #
# Copyright (C) 2009 Pascal Giard <evilynux@gmail.com>              #
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
try:
  from cmgl import *
  cmgl_support = True
except ImportError:
  cmgl_support = False
try:
  from OpenGL.arrays import vbo
  vbo_support = True
except:
  vbo_support = False
import numpy as np
from numpy import array, float32
import pygame
from pygame.locals import *
from math import cos, sin, sqrt

rot = 0.0
scale = 1.0
mode = 1

def init():
    global mode, triangVbo, triangVtx, triangCol
    global spiralVtx, spiralVbo, spiralCol
    triangVtx = array(
        [[ 0,  1, 0],
         [-1, -1, 0],
         [ 1, -1, 0]], dtype=float32)
    triangCol = array(
        [[ 0,  1, 0],
         [ 1,  0, 0],
         [ 0,  0, 1]], dtype=float32)

    nbSteps = 400.0
    
    #np.append changes dtype=f to dtype=d -> don't use it
    spiralVtx = np.zeros((nbSteps, 3), dtype=float32)
    spiralCol = np.zeros((nbSteps, 3), dtype=float32)
    for i in range(0, int(nbSteps), 2):
      ratio = i/nbSteps;
      angle = 21*ratio
      c = cos(angle)
      s = sin(angle);
      r1 = 1.0 - 0.8*ratio;
      r2 = 0.8 - 0.8*ratio;
      alt = ratio - 0.5
      nor = 0.5
      up = sqrt(1.0-nor*nor)
      np.put(spiralVtx[i], [0,1,2] ,[r1*c, alt, r1*s])
      np.put(spiralCol[i], [0,1,2] ,[1.0-ratio, 0.2, ratio])
      np.put(spiralVtx[i+1], [0,1,2] ,[r2*c, alt+0.05, r2*s])
      np.put(spiralCol[i+1], [0,1,2] ,[1.0-ratio, 0.2, ratio])

    if vbo_support:
      #after hstack array isn't contiguous -> make it contiguous
      triangArray = np.ascontiguousarray(np.hstack((triangVtx, triangCol)))
      spiralArray = np.ascontiguousarray(np.hstack((spiralVtx, spiralCol)))
      #print "triangArray cont: ", triangArray.flags['C_CONTIGUOUS']
      #print "triangArray dtype: ", triangArray.dtype.char
      triangVbo = vbo.VBO( triangArray, usage='GL_STATIC_DRAW' )
      spiralVbo = vbo.VBO( spiralArray, usage='GL_STATIC_DRAW' )
    else:
      print "VBO not supported, fallbacking to cmgl."
      mode = 1

    if mode == 1 and not cmgl_support:
      print "cmgl not supported, fallbacking to array-based drawing."
      mode = 2

def draw():
    global mode, triangVbo, triangVtx, triangCol
    global spiralVtx, spiralVbo, spiralCol, rot, scale
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glPushMatrix()
    glColor(1,1,1) # triangle color
    glScale(scale,scale,scale)
    glRotate(rot,0,1,0)

    # VBO drawing
    if mode == 0 and vbo_support:
      drawVBO()

    elif mode == 1 and cmgl_support:
      drawCmgl()

    # Array-based drawing
    elif mode == 2:
      drawArray()

    # Direct drawing
    else: # mode == 3
      drawDirect()

    glPopMatrix()

def drawDirect():
    # With pyopengl3.x, glVertex3fv() is much slower than glVertex3f().
    glBegin(GL_TRIANGLES)
    for i in range(triangVtx.shape[0]):
      #glColor(triangCol[i])
      #glVertex3fv(triangVtx[i])
      glColor3f(triangCol[i][0],triangCol[i][1],triangCol[i][2])
      glVertex3f(triangVtx[i][0],triangVtx[i][1],triangVtx[i][2])
    glEnd()

    # Draw spiral
    glBegin(GL_TRIANGLE_STRIP);
    for i in range(spiralVtx.shape[0]):
      #glColor(spiralCol[i])
      #glVertex3fv(spiralVtx[i])
      glColor3f(spiralCol[i][0],spiralCol[i][1],spiralCol[i][2])
      glVertex3f(spiralVtx[i][0],spiralVtx[i][1],spiralVtx[i][2])
    glEnd()

def drawCmgl():
    cmglDrawArrays(GL_TRIANGLES, vertices=triangVtx, colors=triangCol)
    cmglDrawArrays(GL_TRIANGLE_STRIP, vertices=spiralVtx, colors=spiralCol)

def drawArray():
    # Draw triangle
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_COLOR_ARRAY)
    glColorPointerf(triangCol)
    glVertexPointerf(triangVtx)
    glDrawArrays(GL_TRIANGLES, 0, triangVtx.shape[0])
    # Draw spiral
    glColorPointerf(spiralCol)
    glVertexPointerf(spiralVtx)
    glDrawArrays(GL_TRIANGLE_STRIP, 0, spiralVtx.shape[0])
    glDisableClientState(GL_COLOR_ARRAY)
    glDisableClientState(GL_VERTEX_ARRAY)
    
def drawVBO():
    # Draw triangle
    triangVbo.bind()
    glEnableClientState(GL_VERTEX_ARRAY);
    glEnableClientState(GL_COLOR_ARRAY);
    glVertexPointer(3, GL_FLOAT, 24, triangVbo )
    glColorPointer(3, GL_FLOAT, 24, triangVbo+12 )
    glDrawArrays(GL_TRIANGLES, 0, triangVtx.shape[0])
    glDisableClientState(GL_VERTEX_ARRAY);
    glDisableClientState(GL_COLOR_ARRAY);
    triangVbo.unbind()
    # Draw spiral
    # evilynux - FIXME: The following doesn't work... why?
    spiralVbo.bind()
    glEnableClientState(GL_VERTEX_ARRAY);
    glEnableClientState(GL_COLOR_ARRAY)
    glVertexPointer(3, GL_FLOAT, 24, spiralVbo )
    glColorPointer(3, GL_FLOAT, 24, spiralVbo+12 )
    glDrawArrays(GL_TRIANGLE_STRIP, 0, spiralVtx.shape[0])
    glDisableClientState(GL_COLOR_ARRAY)
    glDisableClientState(GL_VERTEX_ARRAY)
    spiralVbo.unbind()
    
def main():
    global rot, scale, mode
    scale_dir = -1
    modeName = ["VBO", "cmgl", "Array-based", "Direct-mode"]
    fps = 0
    video_flags = DOUBLEBUF|OPENGL|HWPALETTE|HWSURFACE
    
    pygame.init()
    pygame.display.set_mode((640,480), video_flags)
    init()

    frames = 0
    ticks = pygame.time.get_ticks()
    clock = pygame.time.Clock()
    while 1:
      event = pygame.event.poll()
      if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
        break
      elif event.type == KEYDOWN and event.key == K_RIGHT:
        mode = (mode + 1) % 4
        if mode == 0 and not vbo_support:
          mode = (mode + 1) % 4
          print "VBO not supported, fallbacking to %s drawing." % modeName[mode]
        if mode == 1 and not cmgl_support:
          mode = (mode + 1) % 4
          print "cmgl not supported, fallbacking to %s drawing." % modeName[mode]
      elif event.type == KEYDOWN and event.key == K_LEFT:
        mode = (mode - 1) % 4
        if mode == 0 and not vbo_support:
          mode = (mode - 1) % 4
          print "VBO not supported, fallbacking to %s drawing." % modeName[mode]
        if mode == 1 and not cmgl_support:
          mode = (mode - 1) % 4
          print "cmgl not supported, fallbacking to %s drawing." % modeName[mode]
        
      ticksDiff = pygame.time.get_ticks()-ticks

      # draw all objects
      draw()
        
      # update rotation counters
      rot += 0.2
      scale += scale_dir*0.0002
      if scale > 1.0 or scale < 0.5:
        scale_dir = scale_dir*-1

      # make changes visible
      pygame.display.flip()

      frames = frames+1
      if( ticksDiff > 2000 ):
        fps = ((frames*1000)/(ticksDiff))
        ticks = pygame.time.get_ticks()
        frames = 0
        print "mode: %s, %.2f fps" % (modeName[mode], fps)
      # evilynux - commented the following so we go as fast as we can
      #clock.tick(60)

if __name__ == '__main__': main()

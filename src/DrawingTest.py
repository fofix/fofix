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
  from OpenGL.arrays import vbo
  vbo_support = True
except:
  vbo_support = False
from numpy import array, float32, append, hstack
import pygame
from pygame.locals import *
from math import cos, sin, sqrt

rtri = 0.0
mode = 2

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

    nbSteps = 200.0
    for i in range(int(nbSteps)):
      ratio = i/nbSteps;
      angle = 21*ratio
      c = cos(angle)
      s = sin(angle);
      r1 = 1.0 - 0.8*ratio;
      r2 = 0.8 - 0.8*ratio;
      alt = ratio - 0.5
      nor = 0.5
      up = sqrt(1.0-nor*nor)
      if i == 0:
        spiralVtx = array([[r1*c, alt, r1*s]],dtype=float32)
        spiralCol = array([[1.0-ratio, 0.2, ratio]],dtype=float32)
      else:
        spiralVtx = append(spiralVtx,[[r1*c, alt, r1*s]],axis=0)
        spiralCol = append(spiralCol,[[1.0-ratio, 0.2, ratio]],axis=0)
      spiralVtx = append(spiralVtx,[[r2*c, alt+0.05, r2*s]],axis=0)
      spiralCol = append(spiralCol,[[1.0-ratio, 0.2, ratio]],axis=0)

    if vbo_support:
      triangArray = hstack((triangVtx, triangCol))
      spiralArray = hstack((spiralVtx, spiralCol))
      triangVbo = vbo.VBO( triangArray, usage='GL_STATIC_DRAW' )
      spiralVbo = vbo.VBO( spiralArray, usage='GL_STATIC_DRAW' )
    else:
      print "VBO not supported, fallbacking to array-based drawing."
      mode = 1

def draw():
    global mode, triangVbo, triangVtx, triangCol
    global spiralVtx, spiralVbo, spiralCol, rtri
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glPushMatrix()
    glColor(1,1,1) # triangle color
    glScale(.5,.5,.5)
    glRotate(rtri,0,1,0)

    # VBO drawing
    if mode == 0 and vbo_support:
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

    # Array-based drawing
    elif mode == 1:
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

    # Direct drawing
    else: # mode == 2
      glBegin(GL_TRIANGLES)
      for i in range(triangVtx.shape[0]):
        glColor(triangCol[i])
        glVertex(triangVtx[i])
      glEnd()

      # Draw spiral
      glBegin(GL_TRIANGLE_STRIP);
      for i in range(spiralVtx.shape[0]):
        glColor(spiralCol[i])
        glVertex(spiralVtx[i])
      glEnd()

    glPopMatrix()
    
def main():
    global rtri, mode
    modeName = ["VBO", "Array-based", "Direct-mode"]
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
        mode = (mode + 1) % 3
        if mode == 0 and not vbo_support:
          mode = (mode + 1) % 3
          print "VBO not supported, fallbacking to %s drawing." % modeName[mode]
      elif event.type == KEYDOWN and event.key == K_LEFT:
        mode = (mode - 1) % 3
        if mode == 0 and not vbo_support:
          mode = (mode - 1) % 3
          print "VBO not supported, fallbacking to %s drawing." % modeName[mode]
        
      ticksDiff = pygame.time.get_ticks()-ticks

      # draw all objects
      draw()
        
      # update rotation counters
      rtri += 0.2

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


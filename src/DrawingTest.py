#!/usr/bin/env python
# Drawing methods comparison for FoFiX by Pascal Giard <evilynux@gmail.com>
from OpenGL.GL import *
from OpenGL.arrays import vbo
from numpy import array, float32
import pygame
from pygame.locals import *

rtri = 0.0
mode = 0

def init():
    global mode, triangVbo, triangVtx
    triangVtx = array(
        [[ 0,  1, 0],
         [-1, -1, 0],
         [ 1, -1, 0]], dtype=float32)
    triangVbo = vbo.VBO( triangVtx, usage='GL_STATIC_DRAW' )

def draw():
    global mode, triangVbo, triangVtx, rtri
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glPushMatrix()
    # draw triangle
    glScale(.5,.5,.5)
    glRotate(rtri,0,1,0)
    # VBO drawing
    if mode == 0:
      triangVbo.bind()
      glEnableClientState(GL_VERTEX_ARRAY);
      glVertexPointerf( triangVbo )
      glDrawArrays(GL_TRIANGLES, 0, 3)
      glDisableClientState(GL_VERTEX_ARRAY)
      triangVbo.unbind()
    # Array-based
    elif mode == 1:
      glEnableClientState(GL_VERTEX_ARRAY)
      glVertexPointerf(triangVtx)
      glDrawArrays(GL_TRIANGLES, 0, 3)
      glDisableClientState(GL_VERTEX_ARRAY)
    # Direct drawing
    else: # mode == 2
      glBegin(GL_TRIANGLES)
      glVertex( 0, 1,0)
      glVertex(-1,-1,0)
      glVertex( 1,-1,0)
      glEnd()
    glPopMatrix()

def main():
    global rtri, mode
    modeName = ["VBO", "Array", "Direct"]
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
      elif event.type == KEYDOWN and (event.key == K_RIGHT or event.key == K_LEFT):
        mode = (mode + 1) % 3
        
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


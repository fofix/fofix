#!/usr/bin/env python
# demo of laminar.PanelOverlaySurface, by
#  David Keeney 2006
# based on version of Nehe's OpenGL lesson04
#  by Paul Furber 2001 - m@verick.co.za

# you need the Ocemp GUI to be installed.

from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
from pygame.locals import *

import sys
sys.path.insert( 0, '..' )

import lamina

rtri = rquad = 0.0

triOn = quadOn = True

def resize((width, height)):
    if height==0:
        height=1
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 1.0*width/height, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def init():
    glShadeModel(GL_SMOOTH)
    glClearColor(0.0, 0.5, 0.0, 0.0)
    glClearDepth(1.0)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

def draw():

    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glTranslatef(-1.5, 0.0, -6.0)

    # draw triangle
    global rtri
    glRotatef(rtri, 0.0, 1.0, 0.0)

    glBegin(GL_TRIANGLES)
    glColor3f(1.0, 0.0, 0.0)
    glVertex3f(0.0, 1.0, 0.0)
    glColor3f(0.0, 1.0, 0.0)
    glVertex3f(-1.0, -1.0, 0)
    glColor3f(0.0, 0.0, 1.0)
    glVertex3f(1.0, -1.0, 0)
    glEnd()

    # draw quad
    glLoadIdentity()
    glTranslatef(1.5, 0.0, -6.0)
    global rquad
    glRotatef(rquad, 1.0, 0.0, 0.0)

    glColor3f(0.5, 0.5, 1.0)
    glBegin(GL_QUADS)
    glVertex3f(-1.0, 1.0, 0)
    glVertex3f(1.0, 1.0, 0)
    glVertex3f(1.0, -1.0, 0)
    glVertex3f(-1.0, -1.0, 0)
    glEnd()

    # draw gui
    glLoadIdentity()
    global gui_screen
    gui_screen.display()


def main():

    global rtri, rquad, gui_screen
    video_flags = OPENGL|DOUBLEBUF
    
    pygame.init()
    pygame.display.set_mode((640,480), video_flags)

    resize((640,480))
    init()


    # create PanelOverlaySurface
    gui_screen = lamina.LaminaScreenSurface(0.985)
    
    pointlist = [(200,200), (400,200), (400,400), (200,400)]
    pygame.draw.polygon(gui_screen.surf, (200,0,0), pointlist, 0)
    pointlist1 = [(250,250), (350,250), (350,350), (250,350)]
    pygame.draw.polygon(gui_screen.surf, (0,0,100), pointlist1, 0)
    # draw text on a new Surface
    font = pygame.font.Font(None,40)
    txt = font.render('Pygame Text', 1, (0,0,0), (200,0,0))
    gui_screen.surf.blit(txt, (205, 205))

    gui_screen.refresh()
    gui_screen.refreshPosition()

    frames = 0
    ticks = pygame.time.get_ticks()
    clock = pygame.time.Clock()
    while 1:
        event = pygame.event.poll()
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            break
        
        # draw all objects
        draw()
        
        # update rotation counters
        if triOn:
            rtri += 0.2
        if quadOn:
            rquad+= 0.2

        # make changes visible
        pygame.display.flip()
        frames = frames+1
        sys.stdout.write("fps:  %d\r" % ((frames*1000)/(pygame.time.get_ticks()-ticks)))
        clock.tick(60)


if __name__ == '__main__': main()


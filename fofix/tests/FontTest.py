#!/usr/bin/env python
# Font tests for FoFiX by Pascal Giard <evilynux@gmail.com>
# based on the demo of laminar.PanelOverlaySurface, by
#  David Keeney 2006 which is
# based on version of Nehe's OpenGL lesson04
#  by Paul Furber 2001 - m@verick.co.za

from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
from pygame.locals import *
import sys
import os
sys.path.insert( 0, '..' )
from Font import Font
from Texture import Texture
import lamina

rtri = rquad = 0.0

triOn = quadOn = True

def resize((width, height)):
    if height == 0:
        height = 1
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 1.0*width/height, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def init():
    global fofixFont, mode, pygameFont, pygameChar

    glShadeModel(GL_SMOOTH)
    glClearColor(0.0, 0.5, 0.0, 0.0)
    glClearDepth(1.0)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
    mode = 0 # evilynux - Start with lamina
    # FoFiX font rendering
    fofixFont = Font(None, 24, outline = False)
    # pygame font rendering
    pygameFont = pygame.font.Font(None, 24)
    pygameChar = []
    for c in range(256):
        pygameChar.append(createCharacter(chr(c)))
    pygameChar = tuple(pygameChar)

def draw():
    global mode, fps
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    resize((640,480))

    glPushMatrix()
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
    glPopMatrix()

    # Lamina font rendering
    glLoadIdentity()
    s = str('Mode: %d, FPS: %.2f' % (mode, fps))
    if mode == 0:
        global gui_screen, font
        txt = font.render(s, 1, (0,0,0), (200,0,0))
        gui_screen.surf.blit(txt, (640 - txt.get_size()[0], 0))
        gui_screen.display()
    # FoFiX font rendering
    if mode == 1:
        global fofixFont
        size = fofixFont.getStringSize(s)
        # Text invisible unless i put a negative Z position, wtf?!
        glTranslatef(-size[0], .0, -1.0)
        fofixFont.render(s, (0, 0), (1,0))
    # Nelson Rush method for font rendering
    if mode == 2:
        global pygameFont, pygameChar
        i = 0
        lx = 0
        length = len(s)
        x = 640 - pygameChar[ord('0')][1]*length
        y = 480 - pygameChar[ord('0')][2]
        textView(640,480)
        glPushMatrix()
        while i < length:
            glRasterPos2i(x + lx, y)
            ch = pygameChar[ ord( s[i] ) ]
            glDrawPixels(ch[1], ch[2], GL_RGBA, GL_UNSIGNED_BYTE, ch[0])
            lx += ch[1]
            i += 1
        glPopMatrix()

def textView(w = 640, h = 480):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, w - 1.0, 0.0, h - 1.0, -1.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def createCharacter(s):
    global pygameFont
    try:
        letter_render = pygameFont.render(s, 1, (255,255,255), (0,0,0))
        letter = pygame.image.tostring(letter_render, 'RGBA', 1)
        letter_w, letter_h = letter_render.get_size()
    except:
        letter = None
        letter_w = 0
        letter_h = 0
    return (letter, letter_w, letter_h)


def main():
    global rtri, rquad, gui_screen
    global font, fofixFont, fps, mode
    fps = 0
    #video_flags = OPENGL|DOUBLEBUF
    video_flags = DOUBLEBUF|OPENGL|HWPALETTE|HWSURFACE

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
    font = pygame.font.Font(None, 40)
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
        elif event.type == KEYDOWN and (event.key == K_RIGHT or event.key == K_LEFT):
            mode = (mode + 1) % 3

        ticksDiff = pygame.time.get_ticks()-ticks
        if ticksDiff > 200 and mode == 0:
            gui_screen.refresh()

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
        if ticksDiff > 200:
            fps = ((frames*1000)/(ticksDiff))
            ticks = pygame.time.get_ticks()
            frames = 0
            print "mode: %s, %.2f fps" % (mode, fps)
        # evilynux - commented the following so we go as fast as we can
        #clock.tick(60)


if __name__ == '__main__': main()

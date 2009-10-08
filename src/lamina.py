"""
Lamina module

When you set the display mode for OpenGL, you enable all the coolness of 3D rendering, 
but you disable the bread-and-butter raster SDL functionality like fill() and blit(). 
Since the GUI libraries use those surface methods extensively, they cannot readily be 
used in OpenGL displays.

Lamina provides the LaminaPanelSurface and LaminaScreenSurface classes, which bridge 
between the two.

The 'surf' attribute is a surface, and can be drawn on, blitted to, and passed to GUI 
rendering functions for alteration. The 'display' method displays the surface as a 
transparent textured quad in the OpenGL model-space. The 'refresh' method indicates that 
the surface has changed, and that the texture needs regeneration. The 'clear' method 
restores the blank and transparent original condition.

Usage is vaguely like this incomplete pseudocode:
    
    # create gui with appropriate constructor
    gui = GUI_Constructor()
    
    # create LaminaPanelSurface
    gui_screen = lamina.LaminaPanelSurface( (640,480), (-1,1,2,2) )

    # draw widgets on surface
    gui.draw( gui_screen.surf ) 

    # hide mouse cursor
    pygame.mouse.set_visible(0)
    
    while 1:
        
        # do input events ....
        # pass events to gui
        gui.doevent(...)

        # detect changes to surface
        changed = gui.update( gui_screen.surf )
        if changed:            
            # and mark for update
            gui_screen.refresh()   

        # draw opengl geometry .....

        # display gui
        # opengl code to set modelview matrix for desired gui surface pos
        gui_screen.display()


If your gui screen is not sized to match the display, hide the system 
mouse cursor, and use the convertMousePos method to position your own
OpenGL mouse cursor (a cone or something).  The result of the 
convertMousePos is 2D, (x,y) so you need to draw the mouse with the same
modelview matrix as drawing the LaminaPanelSurface itself.        
        
        mouse_pos = gui_screen.convertMousePos(mouseX, mouseY)
        glTranslate(*mouse_pos)
        # opengl code to display your mouse object (a cone?)
        
        
The distribution package includes several demo scripts which are functional.  Refer
to them for details of working code.
"""

import OpenGL.GLU as oglu
import OpenGL.GL as ogl

import pygame
import math

def load_texture(surf):
    """Load surface into texture object. Return texture object. 
    @param surf: surface to make texture from.
    """
    txtr = ogl.glGenTextures(1)
    textureData = pygame.image.tostring(surf, "RGBA", 1)

    ogl.glEnable(ogl.GL_TEXTURE_2D)
    ogl.glBindTexture(ogl.GL_TEXTURE_2D, txtr)
    width, height = surf.get_size()
    ogl.glTexImage2D( ogl.GL_TEXTURE_2D, 0, ogl.GL_RGBA, width, height, 0, 
      ogl.GL_RGBA, ogl.GL_UNSIGNED_BYTE, textureData )
    ogl.glTexParameterf(ogl.GL_TEXTURE_2D, ogl.GL_TEXTURE_MAG_FILTER, ogl.GL_NEAREST)
    ogl.glTexParameterf(ogl.GL_TEXTURE_2D, ogl.GL_TEXTURE_MIN_FILTER, ogl.GL_NEAREST)
    ogl.glDisable(ogl.GL_TEXTURE_2D)
    return txtr

def overlay_texture(txtr, surf, r):
    """Load surface into texture object, replacing part of txtr
    given by rect r. 
    @param txtr: texture to add to
    @param surf: surface to copy from
    @param r: rectangle indicating area to overlay.
    """
    subsurf = surf.subsurface(r)
    textureData = pygame.image.tostring(subsurf, "RGBA", 1) 

    hS, wS = surf.get_size()
    rect = pygame.Rect(r.x,hS-(r.y+r.height),r.width,r.height)
    
    ogl.glEnable(ogl.GL_TEXTURE_2D)
    ogl.glBindTexture(ogl.GL_TEXTURE_2D, txtr)
    ogl.glTexSubImage2D(ogl.GL_TEXTURE_2D, 0, rect.x, rect.y, rect.width, rect.height,  
      ogl.GL_RGBA, ogl.GL_UNSIGNED_BYTE, textureData )
    ogl.glDisable(ogl.GL_TEXTURE_2D)

class LaminaPanelSurface(object): 
    """Surface for imagery to overlay. 
    @ivar surf: surface
    @ivar dims: tuple with corners of quad
    """

    def __init__(self, quadDims=(-1,-1,2,2), winSize=None):
        """Initialize new instance. 
        @param winSize: tuple (width, height)
        @param quadDims: tuple (left, top, width, height)
        """
        if not winSize:
            winSize = pygame.display.get_surface().get_size()
        self._txtr = None
        self._winSize = winSize
        left, top, width, height = quadDims
        right, bottom = left+width, top-height
        self._qdims = quadDims
        self.dims = (left,top,0), (right,top,0), (right,bottom,0), (left,bottom,0) 
        self.clear()
        
    def clear(self):
        """Restore the total transparency to the surface. """
        powerOfTwo = 64
        while powerOfTwo < max(*self._winSize):
            powerOfTwo *= 2
        raw = pygame.Surface((powerOfTwo, powerOfTwo), pygame.SRCALPHA, 32)
        self._surfTotal = raw.convert_alpha()
        self._usable = 1.0*self._winSize[0]/powerOfTwo, 1.0*self._winSize[1]/powerOfTwo
        self.surf = self._surfTotal.subsurface(0,0,self._winSize[0],self._winSize[1])
        self.regen()
    
    def regen(self):
        """Force regen of texture object. Call after change to the GUI appearance. """
        if self._txtr:
            ogl.glDeleteTextures([self._txtr])
        self._txtr = None

    def refresh(self, dirty=None):
        """Refresh the texture from the surface. 
        @param dirty: list of rectangles to update, None for whole panel
        """
        if not self._txtr:
            self._txtr = load_texture(self._surfTotal)
        else:
            wS, hS = self._surfTotal.get_size()
            if dirty is None:
                dirty = [pygame.Rect(0,0,wS,hS)]
            for r in dirty:
                overlay_texture(self._txtr,self._surfTotal,r)
                
    def convertMousePos(self, pos):
        """Converts 2d pixel mouse pos to 2d gl units. 
        @param pos: 2-tuple with x,y of mouse
        """
        x0, y0 = pos
        x = x0/self._winSize[0]*self._qdims[2] + self._qdims[0]
        y = y0/self._winSize[1]*self._qdims[3] + self._qdims[1]
        return x, y
    
    def display(self):
        """Draw surface to a quad. Call as part of OpenGL rendering code."""
        ogl.glEnable(ogl.GL_BLEND)
        ogl.glBlendFunc(ogl.GL_SRC_ALPHA, ogl.GL_ONE_MINUS_SRC_ALPHA)  
        ogl.glEnable(ogl.GL_TEXTURE_2D)
        ogl.glBindTexture(ogl.GL_TEXTURE_2D, self._txtr)
        ogl.glTexEnvf(ogl.GL_TEXTURE_ENV, ogl.GL_TEXTURE_ENV_MODE, ogl.GL_REPLACE)
        
        ogl.glBegin(ogl.GL_QUADS)
        ogl.glTexCoord2f(0.0, 1.0)
        ogl.glVertex3f(*self.dims[0])
        ogl.glTexCoord2f(self._usable[0], 1.0)
        ogl.glVertex3f(*self.dims[1])
        ogl.glTexCoord2f(self._usable[0], 1-self._usable[1])
        ogl.glVertex3f(*self.dims[2])
        ogl.glTexCoord2f(0.0, 1-self._usable[1])
        ogl.glVertex3f(*self.dims[3])
        ogl.glEnd()
        ogl.glDisable(ogl.GL_BLEND)
        ogl.glDisable(ogl.GL_TEXTURE_2D)
        
    def testMode(self):
        """Draw red/transparent checkerboard. """
        w, h = self._winSize[0]*0.25, self._winSize[1]*0.25
        Rect = pygame.Rect
        pygame.draw.rect(self.surf, (250,0,0), Rect(0,0,w,h), 0)
        pygame.draw.rect(self.surf, (250,0,0), Rect(2*w,0,w,h), 0)
        
        pygame.draw.rect(self.surf, (250,0,0), Rect(w,h,w,h), 0)
        pygame.draw.rect(self.surf, (250,0,0), Rect(3*w,h,w,h), 0)
        
        pygame.draw.rect(self.surf, (250,0,0), Rect(0,2*h,w,h), 0)
        pygame.draw.rect(self.surf, (250,0,0), Rect(2*w,2*h,w,h), 0)
        
        pygame.draw.rect(self.surf, (250,0,0), Rect(w,3*h,w,h), 0)
        pygame.draw.rect(self.surf, (250,0,0), Rect(3*w,3*h,w,h), 0)
        self.clear = None


class LaminaScreenSurface(LaminaPanelSurface): 
    """Surface for imagery to overlay.  Autofits to actual display. 
    @ivar surf: surface
    @ivar dims: tuple with corners of quad
    """

    def __init__(self, depth=0):
        """Initialize new instance. 
        @param depth: (0-1) z-value, if you want to draw your own 3D
        cursor, set this to a small non-zero value to allow room in 
        front of this overlay to draw the cursor. (0.1 is a first guess)
        """
        self._txtr = None
        self._depth = depth
        self.setup()

    def setup(self):
        """Setup stuff, after pygame is inited. """
        self._winSize = pygame.display.get_surface().get_size()
        self.refreshPosition()
        self.clear()
        
    def refreshPosition(self):
        """Recalc where in modelspace quad needs to be to fill screen."""
        depth = self._depth
        bottomleft = oglu.gluUnProject(0, 0, depth)
        bottomright = oglu.gluUnProject(self._winSize[0], 0, depth)
        topleft = oglu.gluUnProject(0, self._winSize[1], depth)
        topright = oglu.gluUnProject(self._winSize[0], self._winSize[1], depth)
        self.dims = topleft, topright, bottomright, bottomleft 
        width = topright[0] - topleft[0]
        height = topright[1] - bottomright[1]
        self._qdims = topleft[0], topleft[1], width, height
        

class LaminaScreenSurface2(LaminaScreenSurface):
    """Surface that defers initialization to setup method. """
    
    def __init__(self, depth=0):
        """Initialize new instance. """
        self._txtr = None
        self._depth = depth        

    def refreshPosition(self):
        """Recalc where in modelspace quad needs to be to fill screen."""
        self._dirty = True
        self._qdims = None, None
     
    def getPoint(self, pt):
        """Get x,y coords of pt in 3d space."""
        pt2 = oglu.gluProject(*pt)
        return int(pt2[0]), int(pt2[1]), pt2[2]
     
    def update(self):
        pass
        
    def commit(self):
        pass
        
    def display(self):
        """Display texture. """
        if self._dirty:
            depth = self._depth
            topleft = oglu.gluUnProject(0,self._winSize[1],depth)
            assert topleft, topleft
            if topleft[0:2] != self._qdims[0:2]:
                bottomleft = oglu.gluUnProject(0,0,depth)
                bottomright = oglu.gluUnProject(self._winSize[0],0,depth)
                topright = oglu.gluUnProject(self._winSize[0],self._winSize[1],depth)
                self.dims = topleft, topright, bottomright, bottomleft 
                width = topright[0] - topleft[0]
                height = topright[1] - bottomright[1]
                self._qdims = topleft[0], topleft[1], width, height
        LaminaScreenSurface.display(self)


class LaminaScreenSurface3(LaminaScreenSurface):
    """Surface that accepts a 3d point to constructor, and
    locates surface parallel to screen through given point.
    
    Defers initialization to setup method, like LSS2. 
    """
    
    def __init__(self, point=(0,0,0)):
        """Initialize new instance. """
        self._txtr = None
        self._point = point        
        self._depth = None

    def refreshPosition(self):
        """Recalc where in modelspace quad needs to be to fill screen."""
        self._dirty = True

    def getPoint(self, pt):
        """Get x,y coords of pt in 3d space."""
        pt2 = oglu.gluProject(*pt)
        return pt2[0], pt2[1]
     
    def update(self):
        pass
        
    def commit(self):
        pass
        
    def display(self):
        """Display texture. """
        if self._dirty:
            depth = oglu.gluProject(*self._point)[2]
            if depth != self._depth:
                bottomleft = oglu.gluUnProject(0,0,depth)
                bottomright = oglu.gluUnProject(self._winSize[0],0,depth)
                topleft = oglu.gluUnProject(0,self._winSize[1],depth)
                topright = oglu.gluUnProject(self._winSize[0],self._winSize[1],depth)
                self.dims = topleft, topright, bottomright, bottomleft 
                width = topright[0] - topleft[0]
                height = topright[1] - bottomright[1]
                self._qdims = topleft[0], topleft[1], width, height
                self._depth = depth
        LaminaScreenSurface.display(self)

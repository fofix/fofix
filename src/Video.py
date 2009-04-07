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

import pygame
import os
import sys
import Shader
from OpenGL.GL import *
from OpenGL.GL.ARB.multisample import *
import Log

class Video:
  def __init__(self, caption = "Game"):
    self.screen     = None
    self.caption    = caption
    self.fullscreen = False
    self.flags      = True
    self.shaders    = Shader.shaderList()

  def setMode(self, resolution, fullscreen = False, flags = pygame.OPENGL | pygame.DOUBLEBUF,
              multisamples = 0):
    if fullscreen:
      flags |= pygame.FULLSCREEN
      
    self.flags      = flags
    self.fullscreen = fullscreen

    try:    
      pygame.display.quit()
    except:
      pass
      
    pygame.display.init()
    
    pygame.display.gl_set_attribute(pygame.GL_RED_SIZE,   8)
    pygame.display.gl_set_attribute(pygame.GL_GREEN_SIZE, 8)
    pygame.display.gl_set_attribute(pygame.GL_BLUE_SIZE,  8)
    pygame.display.gl_set_attribute(pygame.GL_ALPHA_SIZE, 8)
      
    if multisamples:
      pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1);
      pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, multisamples);

    try:
      self.screen = pygame.display.set_mode(resolution, flags)
    except Exception, e:
      Log.error(str(e))
      if multisamples:
        Log.warn("Video setup failed. Trying without antialiasing.")
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 0);
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 0);
        multisamples = 0
        self.screen = pygame.display.set_mode(resolution, flags)
      else:
        Log.error("Video setup failed. Make sure your graphics card supports 32 bit display modes.")
        raise
        
    pygame.display.set_caption(self.caption)
    pygame.mouse.set_visible(False)

    #stump: fix the window icon under Windows
    # Yes, I do know about pygame.display.set_icon (and the inherent cross-platformness),
    # but PIL won't load anything but the biggest icon from the ICO, and it looks like
    # complete garbage when scaled down to 16x16.
    if os.name == 'nt':
      import win32api
      import win32gui
      import win32con
      hwnd = pygame.display.get_wm_info()['window']
      if os.path.isfile('fof.ico'):
        # case: running from source code with fof.ico present - use it
        hicon_big = win32gui.LoadImage(0, 'fof.ico', win32gui.IMAGE_ICON, 32, 32, win32gui.LR_LOADFROMFILE)
        win32api.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon_big)
        hicon_small = win32gui.LoadImage(0, 'fof.ico', win32gui.IMAGE_ICON, 16, 16, win32gui.LR_LOADFROMFILE)
        win32api.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon_small)
      elif hasattr(sys, 'frozen') and sys.frozen == 'windows_exe':
        # case: running from py2exe'd exe - use the icon embedded in us
        hicon_big = win32gui.LoadImage(win32api.GetModuleHandle(None), 1, win32gui.IMAGE_ICON, 32, 32, 0)
        win32api.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon_big)
        hicon_small = win32gui.LoadImage(win32api.GetModuleHandle(None), 1, win32gui.IMAGE_ICON, 16, 16, 0)
        win32api.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon_small)

    if multisamples:
      try:
        glEnable(GL_MULTISAMPLE_ARB)
      except:
        pass

    return bool(self.screen)
    
  def toggleFullscreen(self):
    assert self.screen
    
    return pygame.display.toggle_fullscreen()

  def flip(self):
    pygame.display.flip()

  def getVideoModes(self):
    return pygame.display.list_modes()
    
  def setShaders(self, dir):
    try:
      Shader.list.build(dir)
      Shader.multiTex = (GL_TEXTURE0_ARB,GL_TEXTURE1_ARB,GL_TEXTURE2_ARB,GL_TEXTURE3_ARB)
    except:
      Log.warn("Multitexturing failed. Upgrade to PyOpenGL 3.00!")
    else:
      Shader.list.setVar("mult",0.1,False,"neck")
      Shader.list.setVar("fade",0.7,False,"neck")
      Shader.list.setVar("F1",-100.0,False,"neck")
      Shader.list.setVar("F2",-100.0,False,"neck")
      Shader.list.setVar("F3",-100.0,False,"neck")
      Shader.list.setVar("F4",-100.0,False,"neck")
      Shader.list.setVar("F5",-100.0,False,"neck")

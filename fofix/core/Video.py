##################################################################
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

import os
import struct

import pygame
from PIL import Image
from OpenGL.GL import *
from OpenGL.GL.ARB.multisample import *

from fretwork import log

from fofix.core.Language import _

class Video:
    def __init__(self, caption = "Game", icon = None):
        self.screen       = None
        self.caption      = caption
        self.icon         = icon
        self.fullscreen   = False
        self.flags        = True
        self.multisamples = 0
        self.error        = []
        self.default      = False

    def setMode(self, resolution, fullscreen = False, flags = pygame.OPENGL | pygame.DOUBLEBUF,
                multisamples = 0):
        if fullscreen:
            flags |= pygame.FULLSCREEN

        self.flags        = flags
        self.fullscreen   = fullscreen
        self.multisamples = multisamples

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
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, multisamples)

        # evilynux - Setting window icon for platforms other than MS Windows.
        #            pygame claims that some window manager requires this to be
        #            before display.set_mode(), so there it is!
        #            Note: For the MS Windows icon, see below.
        if not os.name == "nt" and self.icon is not None:
            pygame.display.set_icon(pygame.image.load(self.icon))

        try:
            self.screen = pygame.display.set_mode(resolution, flags)
        except Exception as e:
            errortype = str(e)
            if "video mode" in errortype:
                self.resolutionReset()
            else: # "Couldn't find matching GLX visual"
                self.multisampleReset(resolution)

        pygame.display.set_caption(self.caption)
        pygame.mouse.set_visible(False)

        #stump: fix the window icon under Windows
        # We would use pygame.display.set_icon(), but due to what appears to be
        # a bug in SDL, the alpha channel is lost and some parts of the image are
        # corrupted.  As a result, we go the long way and load and set the icon
        # by hand to work around the bug.
        if os.name == 'nt':
            import win32api
            import win32gui
            import win32con
            hwnd = pygame.display.get_wm_info()['window']

            # The Windows icon functions want the byte order in memory to be "BGRx"
            # for some reason.  Use the alpha channel as a placeholder for the "x"
            # and swap the channels to fit.  Also turn the image upside down as the
            # API wants.
            icon = Image.open(self.icon)
            icon.load() #fculpo - needed for PIL 1.1.7 stable
            iconFixedUp = Image.merge('RGBA', [icon.split()[i] for i in (2, 1, 0, 3)]).transpose(Image.FLIP_TOP_BOTTOM)

            # Scale the images to the icon sizes needed.
            bigIcon = iconFixedUp.resize((32, 32), Image.BICUBIC)
            smallIcon = iconFixedUp.resize((16, 16), Image.BICUBIC)

            # The icon resources hold two bitmaps: the first is 32-bit pixel data
            # (which for some reason doesn't hold the alpha, though we used the alpha
            # channel to fill up that space - the fourth channel is ignored) and the
            # second is a 1-bit alpha mask.  For some reason, we need to invert the
            # alpha channel before turning it into the mask.
            bigIconColorData = bigIcon.tobytes()
            bigIconMaskData = bigIcon.split()[3].point(lambda p: 255 - p).convert('1').tobytes()
            smallIconColorData = smallIcon.tobytes()
            smallIconMaskData = smallIcon.split()[3].point(lambda p: 255 - p).convert('1').tobytes()

            # Put together icon resource structures - a header, then the pixel data,
            # then the alpha mask.  See documentation for the BITMAPINFOHEADER
            # structure for what the fields mean.  Not all fields are used -
            # http://msdn.microsoft.com/en-us/library/ms997538.aspx says which ones
            # don't matter and says to set them to zero.  We double the height for
            # reasons mentioned on that page, too.
            bigIconData = struct.pack('<LllHHLLllLL', 40, 32, 64, 1, 32, 0, len(bigIconColorData+bigIconMaskData), 0, 0, 0, 0) + bigIconColorData + bigIconMaskData
            smallIconData = struct.pack('<LllHHLLllLL', 40, 16, 32, 1, 32, 0, len(smallIconColorData+smallIconMaskData), 0, 0, 0, 0) + smallIconColorData + smallIconMaskData

            # Finally actually create the icons from the icon resource structures.
            hIconBig = win32gui.CreateIconFromResource(bigIconData, True, 0x00030000)
            hIconSmall = win32gui.CreateIconFromResource(smallIconData, True, 0x00030000)

            # And set the window's icon to our fresh new icon handles.
            win32api.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hIconBig)
            win32api.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hIconSmall)

        if multisamples:
            try:
                glEnable(GL_MULTISAMPLE_ARB)
            except:
                pass

        return bool(self.screen)

    def screenError(self):
        log.error("Video setup failed. Make sure your graphics card supports 32-bit display modes.")
        raise

    def resolutionReset(self):
        log.warn("Video setup failed. Trying default windowed resolution.")
        self.error.append(_("Video setup failed with your resolution settings, and so were reset to defaults."))
        if self.fullscreen:
            self.flags ^= pygame.FULLSCREEN
            self.fullscreen = False
        try:
            self.screen = pygame.display.set_mode((800,600), self.flags)
            self.default = True
        except Exception:
            if self.multisamples:
                self.multisampleReset((800, 600))
            else:
                self.screenError()

    def multisampleReset(self, resolution):
        log.warn("Video setup failed. Trying without antialiasing.")
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 0)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 0)
        self.multisamples = 0
        try:
            self.screen = pygame.display.set_mode(resolution, self.flags)
        except Exception as e:
            if "video mode" in str(e):
                self.resolutionReset()
            else:
                self.screenError()

    def toggleFullscreen(self):
        assert self.screen

        return pygame.display.toggle_fullscreen()

    def flip(self):
        pygame.display.flip()

    def getVideoModes(self):
        return pygame.display.list_modes()

    #stump
    def disableScreensaver(self):
        if os.name == 'nt':
            # See the DisableScreensaver and RestoreScreensaver functions in
            # modules/video_output/msw/common.c in the source code for VLC.
            import win32gui
            import win32con
            import atexit

            log.debug('Disabling screensaver.')

            old_lowpowertimeout = win32gui.SystemParametersInfo(win32con.SPI_GETLOWPOWERTIMEOUT)
            if old_lowpowertimeout != 0:
                atexit.register(lambda: win32gui.SystemParametersInfo(win32con.SPI_SETLOWPOWERTIMEOUT, old_lowpowertimeout))
                win32gui.SystemParametersInfo(win32con.SPI_SETLOWPOWERTIMEOUT, 0)

            old_powerofftimeout = win32gui.SystemParametersInfo(win32con.SPI_GETPOWEROFFTIMEOUT)
            if old_powerofftimeout != 0:
                atexit.register(lambda: win32gui.SystemParametersInfo(win32con.SPI_SETPOWEROFFTIMEOUT, old_powerofftimeout))
                win32gui.SystemParametersInfo(win32con.SPI_SETPOWEROFFTIMEOUT, 0)

            old_screensavetimeout = win32gui.SystemParametersInfo(win32con.SPI_GETSCREENSAVETIMEOUT)
            if old_screensavetimeout != 0:
                atexit.register(lambda: win32gui.SystemParametersInfo(win32con.SPI_SETSCREENSAVETIMEOUT, old_screensavetimeout))
                win32gui.SystemParametersInfo(win32con.SPI_SETSCREENSAVETIMEOUT, 0)

        else:
            log.debug('Screensaver disabling is not implemented on this platform.')

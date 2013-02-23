#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
#               2008 Glorandwarf                                    #
#               2008 ShiekOdaSandz                                  #
#               2008 QQStarS                                        #
#               2008 Blazingamer                                    #
#               2008 evilynux <evilynux@gmail.com>                  #
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

"""A bunch of dialog functions for interacting with the user."""

from __future__ import with_statement

import pygame
from OpenGL.GL import *
import math
import os
import fnmatch

from View import Layer, BackgroundLayer
from Input import KeyListener
from Menu import Menu
from Language import _
import Log
import Player
from Unicode import unicodify

#stump: vocals
import Microphone

# evilynux - MFH-Alarian Mod credits
from Credits import Credits

import Config

from constants import *

#MFH - for loading phrases
def wrapCenteredText(font, pos, text, rightMargin = 1.0, scale = 0.002, visibility = 0.0, linespace = 1.0, allowshadowoffset = False, shadowoffset = (.0022, .0005)):
    """
    Wrap a piece of text inside given margins.

    @param pos:         (x, y) tuple, x defines the centerline
    @param text:        Text to wrap
    @param rightMargin: Right margin
    @param scale:       Text scale
    @param visibility:  Visibility factor [0..1], 0 is fully visible
    """


    x, y = pos

    #MFH: rewriting WrapCenteredText function to properly wrap lines in a centered fashion around a defined centerline (x)
    sentence = ""
    for n, word in enumerate(text.split(" ")):
        w, h = font.getStringSize(sentence + " " + word, scale = scale)
        if x + (w/2) > rightMargin or word == "\n":
            w, h = font.getStringSize(sentence, scale = scale)
            glPushMatrix()
            glRotate(visibility * (n + 1) * -45, 0, 0, 1)
            if allowshadowoffset == True:
                font.render(sentence, (x - (w/2), y + visibility * n), scale = scale, shadowoffset = shadowoffset)
            else:
                font.render(sentence, (x - (w/2), y + visibility * n), scale = scale)
            glPopMatrix()
            sentence = word
            y += h * linespace
        else:
            if sentence == "" or sentence == "\n":
                sentence = word
            else:
                sentence = sentence + " " + word
    else:
        w, h = font.getStringSize(sentence, scale = scale)
        glPushMatrix()
        glRotate(visibility * (n + 1) * -45, 0, 0, 1)
        if allowshadowoffset == True:
            font.render(sentence, (x - (w/2), y + visibility * n), scale = scale, shadowoffset = shadowoffset)
        else:
            font.render(sentence, (x - (w/2), y + visibility * n), scale = scale)
        glPopMatrix()
        y += h * linespace

    return (x, y)

def wrapText(font, pos, text, rightMargin = 0.9, scale = 0.002, visibility = 0.0):
    """
    Wrap a piece of text inside given margins.

    @param pos:         (x, y) tuple, x defines the left margin
    @param text:        Text to wrap
    @param rightMargin: Right margin
    @param scale:       Text scale
    @param visibility:  Visibility factor [0..1], 0 is fully visible
    """
    x, y = pos
    w = h = 0
    space = font.getStringSize(" ", scale = scale)[0]

    # evilynux - No longer requires "\n" to be in between spaces
    for n, sentence in enumerate(text.split("\n")):
        y += h
        x = pos[0]
        if n == 0:
            y = pos[1]
        for n, word in enumerate(sentence.strip().split(" ")):
            w, h = font.getStringSize(word, scale = scale)
            if x + w > rightMargin:
                x = pos[0]
                y += h
            glPushMatrix()
            glRotate(visibility * (n + 1) * -45, 0, 0, 1)
            font.render(word, (x, y + visibility * n), scale = scale)
            glPopMatrix()
            x += w + space
    return (x - space, y)


class MainDialog(Layer, KeyListener):
    def __init__(self, engine):
        self.engine           = engine
        self.fontDict         = self.engine.data.fontDict
        self.geometry         = self.engine.view.geometry[2:4]
        self.fontScreenBottom = self.engine.data.fontScreenBottom
        self.aspectRatio      = self.engine.view.aspectRatio
        self.drawImage        = self.engine.drawImage
        self.drawStarScore    = self.engine.drawStarScore

    def shown(self):
        self.engine.input.addKeyListener(self, priority = True)

    def hidden(self):
        self.engine.input.removeKeyListener(self)

class GetText(Layer, KeyListener):
    """Text input layer."""
    def __init__(self, engine, prompt = "", text = ""):
        self.text = text
        self.prompt = prompt
        self.engine = engine
        self.time = 0
        self.accepted = False

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("GetText class init (Dialogs.py)...")

        self.sfxVolume    = self.engine.config.get("audio", "SFX_volume")

        self.drumHighScoreNav = self.engine.config.get("game", "drum_navigation")  #MFH



    def shown(self):
        self.engine.input.addKeyListener(self, priority = True)
        self.engine.input.enableKeyRepeat()

    def hidden(self):
        self.engine.input.removeKeyListener(self)
        self.engine.input.disableKeyRepeat()

    def keyPressed(self, key, unicode):
        self.time = 0
        c = self.engine.input.controls.getMapping(key)
        if key == pygame.K_BACKSPACE and not self.accepted:
            self.text = self.text[:-1]
        elif unicode and ord(unicode) > 31 and not self.accepted:
            self.text += unicode
        elif key == pygame.K_LSHIFT or key == pygame.K_RSHIFT:
            return True
        elif (c in Player.menuYes or key == pygame.K_RETURN) and not self.accepted:   #MFH - adding support for green drum "OK"
            self.engine.view.popLayer(self)
            self.accepted = True
            if c in Player.key1s:
                self.engine.data.acceptSound.setVolume(self.sfxVolume)  #MFH
                self.engine.data.acceptSound.play()
        elif (c in Player.menuNo or key == pygame.K_ESCAPE) and not self.accepted:
            self.text = ""
            self.engine.view.popLayer(self)
            self.accepted = True
            if c in Player.key2s:
                self.engine.data.cancelSound.setVolume(self.sfxVolume)  #MFH
                self.engine.data.cancelSound.play()
        elif c in Player.key4s and not self.accepted:
            self.text = self.text[:-1]
            if c in Player.key4s:
                self.engine.data.cancelSound.setVolume(self.sfxVolume)  #MFH
                self.engine.data.cancelSound.play()
        elif c in Player.key3s and not self.accepted:
            self.text += self.text[len(self.text) - 1]
            self.engine.data.acceptSound.setVolume(self.sfxVolume)  #MFH
            self.engine.data.acceptSound.play()
        elif c in Player.action1s and not self.accepted:
            if len(self.text) == 0:
                self.text = "A"
                return True
            letter = self.text[len(self.text)-1]
            letterNum = ord(letter)
            if letterNum == ord('A'):
                letterNum = ord(' ')
            elif letterNum == ord(' '):
                letterNum = ord('_')
            elif letterNum == ord('_'):
                letterNum = ord('-')
            elif letterNum == ord('-'):
                letterNum = ord('9')
            elif letterNum == ord('0'):
                letterNum = ord('z')
            elif letterNum == ord('a'):
                letterNum = ord('Z')
            else:
                letterNum -= 1
            self.text = self.text[:-1] + chr(letterNum)
            self.engine.data.selectSound.setVolume(self.sfxVolume)  #MFH
            self.engine.data.selectSound.play()
        elif c in Player.action2s and not self.accepted:
            if len(self.text) == 0:
                self.text = "A"
                return True
            letter = self.text[len(self.text)-1]
            letterNum = ord(letter)
            if letterNum == ord('Z'):
                letterNum = ord('a')
            elif letterNum == ord('z'):
                letterNum = ord('0')
            elif letterNum == ord('9'):
                letterNum = ord('-')
            elif letterNum == ord('-'):
                letterNum = ord('_')
            elif letterNum == ord('_'):
                letterNum = ord(' ')
            elif letterNum == ord(' '):
                letterNum = ord('A')
            else:
                letterNum += 1
            self.text = self.text[:-1] + chr(letterNum)
            self.engine.data.selectSound.setVolume(self.sfxVolume)  #MFH
            self.engine.data.selectSound.play()
        return True

    def run(self, ticks):
        self.time += ticks / 50.0

    def render(self, visibility, topMost):
        self.engine.view.setViewport(1,0)
        font = self.engine.data.font
        with self.engine.view.orthogonalProjection(normalize = True):
            v = (1 - visibility) ** 2

            self.engine.fadeScreen(v)
            self.engine.theme.setBaseColor(1 - v)

            if (self.time % 10) < 5 and visibility > .9:
                cursor = "|"
            else:
                cursor = ""

            pos = wrapText(font, (.1, .33 - v), self.prompt)

            self.engine.theme.setSelectedColor(1 - v)

            if self.text is not None:
                pos = wrapText(font, (.1, (pos[1] + v) + .08 + v / 4), self.text)
                font.render(cursor, pos)

class GetKey(Layer, KeyListener):
    """Key choosing layer."""
    def __init__(self, engine, prompt = "", key = None, noKey = False, specialKeyList = []):
        self.key = key
        self.prompt = prompt
        self.engine = engine
        self.time = 0
        self.accepted  = False
        self.noKey     = noKey
        self.toggleEsc = False
        self.escTimer  = 1000
        self.specialKeyList = specialKeyList

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("GetKey class init (Dialogs.py)...")

    def shown(self):
        self.engine.input.addKeyListener(self, priority = True)

    def hidden(self):
        self.engine.input.removeKeyListener(self)

    def keyPressed(self, key, unicode):
        if key == pygame.K_ESCAPE and not self.accepted:
            self.toggleEsc = True
        elif not self.accepted and key not in self.specialKeyList:
            self.key = key
            self.engine.view.popLayer(self)
            self.accepted = True
        return True

    def keyReleased(self, key):
        if key == pygame.K_ESCAPE and self.toggleEsc:
            if key in self.specialKeyList:
                self.escTimer = 1000
                self.toggleEsc = False
            else:
                self.key = key
                self.engine.view.popLayer(self)
                self.accepted = True

    def run(self, ticks):
        self.time += ticks / 50.0
        if self.toggleEsc:
            self.escTimer -= ticks
            if self.escTimer < 0:
                self.key = None
                self.engine.view.popLayer(self)
                self.accepted = True

    def render(self, visibility, topMost):
        self.engine.view.setViewport(1,0)
        font = self.engine.data.font

        with self.engine.view.orthogonalProjection(normalize = True):
            v = (1 - visibility) ** 2

            self.engine.fadeScreen(v)
            self.engine.theme.setBaseColor(1 - v)

            pos = wrapText(font, (.1, .33 - v), self.prompt)

            self.engine.theme.setSelectedColor(1 - v)

            if self.key is not None:
                text = pygame.key.name(self.key).capitalize()
                pos = wrapText(font, (.1, (pos[1] + v) + .08 + v / 4), text)

class LoadingScreen(Layer, KeyListener):
    """Loading screen layer."""
    def __init__(self, engine, condition, text, allowCancel = False):
        self.engine       = engine
        self.text         = text
        self.condition    = condition
        self.ready        = False
        self.allowCancel  = allowCancel
        self.time         = 0.0

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("LoadingScreen class init (Dialogs.py)...")

        self.loadingx = self.engine.theme.loadingX
        self.loadingy = self.engine.theme.loadingY
        self.allowtext = self.engine.config.get("game", "lphrases")

        #Get theme
        self.theme = self.engine.data.theme

    def shown(self):
        self.engine.input.addKeyListener(self, priority = True)

    def keyPressed(self, key, unicode):
        c = self.engine.input.controls.getMapping(key)
        if self.allowCancel and c in Player.menuNo:
            self.engine.view.popLayer(self)
        return True

    def hidden(self):
        self.engine.input.removeKeyListener(self)

    def run(self, ticks):
        self.time += ticks / 50.0
        if not self.ready and self.condition():
            self.engine.view.popLayer(self)
            self.ready = True

    def render(self, visibility, topMost):
        self.engine.view.setViewport(1,0)
        font = self.engine.data.loadingFont

        if not font:
            return

        with self.engine.view.orthogonalProjection(normalize = True):
            v = (1 - visibility) ** 2
            self.engine.fadeScreen(v)

            w, h = self.engine.view.geometry[2:4]
            self.loadingImg = self.engine.data.loadingImage

            #MFH - auto-scaling of loading screen
            #Volshebnyi - fit to screen applied
            if self.loadingImg:
                self.engine.drawImage(self.loadingImg, scale = (1.0,-1.0), coord = (w/2,h/2), stretched = FULL_SCREEN)

            self.engine.theme.setBaseColor(1 - v)
            w, h = font.getStringSize(self.text)

            if self.loadingx != None:
                if self.loadingy != None:
                    x = self.loadingx - w / 2
                    y = self.loadingy - h / 2 + v * .5
                else:
                    x = self.loadingx - w / 2
                    y = .6 - h / 2 + v * .5
            elif self.loadingy != None:
                x = .5 - w / 2
                y = .6 - h / 2 + v * .5
            else:
                x = .5 - w / 2
                y = .6 - h / 2 + v * .5

            if self.allowtext:
                if self.theme == 1:
                    font.render(self.text, (x, y), shadowoffset = (self.engine.theme.shadowoffsetx, self.engine.theme.shadowoffsety))
                else:
                    font.render(self.text, (x, y))

class MessageScreen(Layer, KeyListener):
    """Message screen layer."""
    def __init__(self, engine, text, prompt = _("<OK>")):
        self.engine = engine
        self.text = text
        self.time = 0.0
        self.prompt = prompt

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("MessageScreen class init (Dialogs.py)...")


    def shown(self):
        self.engine.input.addKeyListener(self, priority = True)

    def keyPressed(self, key, unicode):
        c = self.engine.input.controls.getMapping(key)
        if c in (Player.menuYes + Player.menuNo) or key in [pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_LCTRL, pygame.K_RCTRL]:
            self.engine.view.popLayer(self)
        return True

    def hidden(self):
        self.engine.input.removeKeyListener(self)

    def run(self, ticks):
        self.time += ticks / 50.0

    def render(self, visibility, topMost):
        self.engine.view.setViewport(1,0)
        font = self.engine.data.font

        if not font:
            return

        with self.engine.view.orthogonalProjection(normalize = True):
            v = (1 - visibility) ** 2
            self.engine.fadeScreen(v)

            x = .1
            y = .3 + v * 2
            self.engine.theme.setBaseColor(1 - v)
            pos = wrapText(font, (x, y), self.text, visibility = v)

            w, h = font.getStringSize(self.prompt, scale = 0.001)
            x = .5 - w / 2
            y = pos[1] + 3 * h + v * 2
            self.engine.theme.setSelectedColor(1 - v)
            font.render(self.prompt, (x, y), scale = 0.001)

class FileChooser(BackgroundLayer, KeyListener):
    """File choosing layer."""
    def __init__(self, engine, masks, path, prompt = "", dirSelect = False):
        self.masks          = masks
        self.path           = unicodify(path)
        self.prompt         = prompt
        self.engine         = engine
        self.accepted       = False
        self.selectedFile   = None
        self.time           = 0.0
        self.menu           = None

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("FileChooser class init (Dialogs.py)...")


        self.dirSelect      = dirSelect

        #Get theme
        #now theme determination logic is only in data.py:
        self.theme = self.engine.data.theme

       #MFH - added simple black background to place in front of Options background, behind Neck BG, for transparent neck displays
        if not self.engine.loadImgDrawing(self, "neckBlackBack", ("neckblackback.png")):
            self.neckBlackBack = None

    def _getFileCallback(self, fileName):
        return lambda: self.chooseFile(fileName)

    def _getFileText(self, fileName):
        f = os.path.join(self.path, fileName)
        if fileName == "..":
            return _("[Parent Folder]")
        if self.dirSelect == True:
            for mask in self.masks:
                if fnmatch.fnmatch(fileName, mask):
                    return _("[Accept Folder]")
        if os.path.isdir(f):
            return _("%s [Folder]") % fileName
        return fileName

    def getFiles(self):
        files = [u".."]
        for fn in os.listdir(self.path):
            if fn.startswith("."): continue
            f = os.path.join(self.path, fn)
            for mask in self.masks:
                if fnmatch.fnmatch(fn, mask):
                    break
            else:
                if not os.path.isdir(f):
                    continue
            files.append(fn)
        files.sort()
        if self.dirSelect == True and (fnmatch.fnmatch(self.path, self.masks[0])):
            files.insert(0, self.path)
        return files

    def getDisks(self):
        import win32file, string
        driveLetters=[]
        for drive in string.letters[len(string.letters) / 2:]:
            if win32file.GetDriveType(drive + ":") == win32file.DRIVE_FIXED:
                driveLetters.append(drive + u":\\")
        return driveLetters

    def updateFiles(self):
        if self.menu:
            self.engine.view.popLayer(self.menu)

        if self.path == u"toplevel" and os.name != "nt":
            self.path = u"/"

        if self.path == u"toplevel":
            self.menu = Menu(self.engine, choices = [(self._getFileText(f), self._getFileCallback(f)) for f in self.getDisks()], onClose = self.close, onCancel = self.cancel)
        else:
            self.menu = Menu(self.engine, choices = [(self._getFileText(f), self._getFileCallback(f)) for f in self.getFiles()], onClose = self.close, onCancel = self.cancel)
        self.engine.view.pushLayer(self.menu)

    def chooseFile(self, fileName):
        if self.dirSelect == True:
            for mask in self.masks:
                if fnmatch.fnmatch(fileName, mask):
                    self.selectedFile = fileName
                    self.engine.view.popLayer(self.menu)
                    self.engine.view.popLayer(self)
                    self.menu = None
                    return

        if self.path == u"toplevel":
            self.path = u""
        path = os.path.abspath(os.path.join(self.path, fileName))

        if os.path.isdir(path):

            if path == self.path and fileName == u"..":
                self.path = u"toplevel"
            else:
                self.path = path
            self.updateFiles()
            return
        self.selectedFile = path
        self.engine.view.popLayer(self.menu)
        self.engine.view.popLayer(self)
        self.menu = None

    def cancel(self):
        self.accepted = True
        self.engine.view.popLayer(self)

    def close(self):
        if not self.menu:
            self.accepted = True
            self.engine.view.popLayer(self)

    def shown(self):
        self.updateFiles()

    def getSelectedFile(self):
        return self.selectedFile

    def run(self, ticks):
        self.time += ticks / 50.0

    def render(self, visibility, topMost):
        v = (1 - visibility) ** 2

        # render the background

        self.engine.view.setViewport(1,0)
        w, h, = self.engine.view.geometry[2:4]

        #MFH - draw neck black BG in for transparent areas (covers options BG):
        if self.neckBlackBack != None:
            #MFH - auto background scaling
            self.engine.drawImage(self.neckBlackBack, scale = (1.0,-1.0), coord = (w/2,h/2), stretched = FULL_SCREEN)


        #MFH - auto background scaling
        if self.engine.data.optionsBG:
            self.engine.drawImage(self.engine.data.optionsBG, scale = (1.0,-1.0), coord = (w/2,h/2), stretched = FULL_SCREEN)


        font = self.engine.data.font
        with self.engine.view.orthogonalProjection(normalize = True):
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_COLOR_MATERIAL)
            self.engine.theme.setBaseColor(1 - v)
            wrapText(font, (.1, .05 - v), self.prompt)

class NeckChooser(Layer, KeyListener):
    """
    Item menu layer.
    on-demand Neck Select menu
    """
    def __init__(self, engine, selected = None, prompt = _("Yellow (#3) / Blue (#4) to change, Green (#1) to confirm:"), player = "default", owner = None):
        self.prompt   = prompt
        self.prompt_x = engine.theme.neck_prompt_x
        self.prompt_y = engine.theme.neck_prompt_y
        self.engine   = engine
        self.player   = player
        self.owner    = owner

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("%s NeckChooser class init (Dialogs.py)..." % (self.player))

        splash = showLoadingSplashScreen(self.engine, _("Loading necks..."))

        self.neck = []
        self.necks = ["2none", "none"]
        self.maxNeck = 0

        defaultNeck = self.engine.config.get("game", "default_neck")
        self.selectedNeck = 0
        for i, name in enumerate(Player.playername):
            if name == player:
                playerNeck = Player.playerpref[i][6]
                if playerNeck == "":
                    playerNeck = defaultNeck
                break
        else:
            playerNeck = defaultNeck

        # evilynux - improved loading logic to support arbitrary filenames
        #          - os.listdir is not guaranteed to return a sorted list, so sort it!
        path = self.engine.resource.fileName("necks")
        # only list files
        neckfiles = [ f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) ]
        neckfiles.sort()

        for i in neckfiles:   #MFH - first go through and find the random neck
            if ( os.path.splitext(i)[0] == "randomneck" ):    #MFH
                exists = 1

                neckImage = engine.loadImgDrawing(self, "neck"+str(i), os.path.join("necks",str(i)))
                if not neckImage:
                    # evilynux - Warning, Thumbs.db won't fail at engine.loadImgDrawing
                    exists = 0
                    continue
                else:
                    exists = 1

                if exists == 1:
                    self.neck.append(str(i)[:-4]) # evilynux - filename w/o extension
                    self.necks.append(neckImage)
                    break

        for i in neckfiles:
            # evilynux - Special cases, ignore these...
            if( os.path.splitext(i)[0] == "randomneck" or os.path.splitext(i)[0] == "overdriveneck" ):    #MFH
                exists = 0
                continue

            neckImage = engine.loadImgDrawing(self, "neck"+str(i), os.path.join("necks",str(i)))
            if not neckImage:
                # evilynux - Warning, Thumbs.db won't fail at engine.loadImgDrawing
                exists = 0
                continue
            else:
                exists = 1

            if exists == 1:
                self.neck.append(str(i)[:-4]) # evilynux - filename w/o extension
                self.necks.append(neckImage)
                self.maxNeck += 1

        self.maxNeck -= 1 # evilynux - confusing, but there's an offset of -1
        Config.define("player",   "neck",  str,  0,  text = _("Neck"), options = self.neck)

        for i, neck in enumerate(self.neck):
            if neck == playerNeck:
                self.selectedNeck = i
                break
        else:
            for i, neck in enumerate(self.neck):
                if neck == defaultNeck:
                    self.selectedNeck = i
            else:
                self.selectedNeck = 0

        self.necks.append("none")
        self.necks.append("2none")

        self.accepted       = False
        self.time           = 0.0


        #Get theme
        self.themename = self.engine.data.themeLabel
        self.theme = self.engine.data.theme

        #MFH - added simple black background to place in front of Options background, behind Neck BG, for transparent neck displays
        if not self.engine.loadImgDrawing(self, "neckBlackBack", ("neckblackback.png")):
            self.neckBlackBack = None



        self.engine.loadImgDrawing(self, "neckBG", os.path.join("themes",self.themename,"menu","neckchoosebg.png"))
        self.engine.loadImgDrawing(self, "neckSelect", os.path.join("themes",self.themename,"menu","neckchooseselect.png"))

        # ready... hide the splash screen
        hideLoadingSplashScreen(self.engine, splash)
        splash = None

    def shown(self):
        self.engine.input.addKeyListener(self, priority = True)

    def hidden(self):
        self.engine.input.removeKeyListener(self)

    def chooseNeck(self):
        if self.player == "default":
            self.engine.config.set("game","default_neck",self.neck[self.selectedNeck])
        if self.owner: #rather hard-coded...
            if self.player != "default":
                self.owner.neck  = self.neck[self.selectedNeck]
        self.engine.view.popLayer(self)

    def cancel(self):
        self.accepted = False
        self.engine.view.popLayer(self)

    def keyPressed(self, key, unicode):
        c = self.engine.input.controls.getMapping(key)
        if c in Player.key1s or key == pygame.K_RETURN:
            self.chooseNeck()
        elif c in Player.key2s + Player.cancels or key == pygame.K_ESCAPE:
            self.cancel()
        elif c in Player.key3s + Player.ups + Player.action1s + Player.lefts or key == pygame.K_UP or key == pygame.K_LEFT:
            self.selectedNeck -= 1
            if self.selectedNeck < 0:
                self.selectedNeck = len(self.neck) - 1
        elif c in Player.key4s + Player.downs + Player.action2s + Player.rights or key == pygame.K_DOWN or key == pygame.K_RIGHT:
            self.selectedNeck += 1
            if self.selectedNeck >= len(self.neck):
                self.selectedNeck = 0
        return True

    def keyReleased(self, key):
        return

    def getSelectedNeck(self):
        return self.selectedNeck

    def run(self, ticks):
        self.time += ticks / 50.0

    def render(self, visibility, topMost):
        v = (1 - visibility) ** 2
        # render the background
        self.engine.view.setViewport(1,0)
        w, h, = self.engine.view.geometry[2:4]


        #MFH - draw neck black BG in for transparent necks (covers options BG):
        if self.neckBlackBack != None:
            #MFH - auto background scaling
            self.engine.drawImage(self.neckBlackBack, scale = (1.0,-1.0), coord = (w/2,h/2), stretched = FULL_SCREEN)

        currentNeck = self.necks[int(self.selectedNeck)+2]
        lastNeck1 = self.necks[int(self.selectedNeck)]
        if lastNeck1 == "none":
            lastNeck1 = self.necks[self.maxNeck+2]
        elif lastNeck1 == "2none":
            lastNeck1 = self.necks[self.maxNeck+1]
        lastNeck = self.necks[int(self.selectedNeck)+1]
        if lastNeck == "none":
            lastNeck = self.necks[self.maxNeck+2]

        nextNeck = self.necks[int(self.selectedNeck)+3]
        if nextNeck == "none":
            nextNeck = self.necks[2]

        nextNeck1 = self.necks[int(self.selectedNeck)+4]
        if nextNeck1 == "none":
            nextNeck1 = self.necks[2]
        elif nextNeck1 == "2none":
            nextNeck1 = self.necks[3]

        if self.theme == 2:
            self.x1 = w*0.067
            self.x2 = w*0.187
            self.x3 = w*0.307
            self.x4 = w*0.427
            self.x5 = w*0.547
            self.x6 = w*0.296
            self.y1 = h*0.420
            self.y2 = h*0.420
            self.y3 = h*0.420
            self.y4 = h*0.420
            self.y5 = h*0.420
            self.y6 = h*0.420
            self.wfac = 384.000
            self.wfac2 = 124.000
        else:
            self.x1 = w*0.05
            self.x2 = w*0.175
            self.x3 = w*0.296
            self.x4 = w*0.42
            self.x5 = w*0.539
            self.x6 = w*0.296
            self.y1 = h*0.420
            self.y2 = h*0.554
            self.y3 = h*0.415
            self.y4 = h*0.554
            self.y5 = h*0.402
            self.y6 = h*0.423
            self.wfac = 374.000
            self.wfac2 = 128.000



        wfactor = currentNeck.widthf(pixelw = self.wfac)
        if self.theme != 2:
            neckcoord = (w/1.31,h/2)
        else:
            neckcoord = (w/1.22,h/2)
        self.engine.drawImage(currentNeck, scale = (-wfactor,wfactor), coord = neckcoord)


        wfactor = lastNeck1.widthf(pixelw = self.wfac2)
        self.engine.drawImage(lastNeck1, scale = (-wfactor,wfactor), coord = (self.x1,self.y1))
        wfactor = lastNeck.widthf(pixelw = self.wfac2)
        self.engine.drawImage(lastNeck, scale = (-wfactor,wfactor), coord = (self.x2,self.y2))
        wfactor = currentNeck.widthf(pixelw = self.wfac2)
        self.engine.drawImage(currentNeck, scale = (-wfactor,wfactor), coord = (self.x3,self.y3))
        wfactor = nextNeck.widthf(pixelw = self.wfac2)
        self.engine.drawImage(nextNeck, scale = (-wfactor,wfactor), coord = (self.x4,self.y4))
        wfactor = nextNeck1.widthf(pixelw = self.wfac2)
        self.engine.drawImage(nextNeck1, scale = (-wfactor,wfactor), coord = (self.x5,self.y5))

        if self.selectedNeck:
            self.engine.drawImage(self.neckSelect, scale = (-1.0,1.0), coord = (self.x6, self.y6))

        #MFH - draw neck BG on top of necks
        #MFH - auto background scaling
        self.engine.drawImage(self.neckBG, scale = (1.0,-1.0), coord = (w/2,h/2), stretched = FULL_SCREEN)


        font = self.engine.data.font
        with self.engine.view.orthogonalProjection(normalize = True):
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_COLOR_MATERIAL)
            self.engine.theme.setBaseColor(1 - v)
            wrapText(font, (self.prompt_x, self.prompt_y - v), self.prompt)
        #==============================================================



class AvatarChooser(Layer, KeyListener):
    """Avatar choosing layer"""
    def __init__(self, engine):
        self.engine   = engine

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("AvatarChooser class init (Dialogs.py)...")

        splash = showLoadingSplashScreen(self.engine, _("Loading avatars..."))

        #Get theme
        self.themename = self.engine.data.themeLabel
        self.theme = self.engine.data.theme

        self.avatar = []
        self.avatars = []
        self.maxAv = 0
        self.themeAvs = 0

        self.selectedAv = 0

        self.scrolling = 0
        self.delay     = 0
        self.rate      = 0
        self.scroller  = [0, self.scrollUp, self.scrollDown]

        # evilynux - improved loading logic to support arbitrary filenames
        #          - os.listdir is not guaranteed to return a sorted list, so sort it!
        avatarpath = self.engine.resource.fileName("avatars")
        avatarfiles = [ f for f in os.listdir(avatarpath) if os.path.isfile(os.path.join(avatarpath, f)) ]
        avatarfiles.sort()

        themeavatarfiles = []
        themeavatarpath = self.engine.resource.fileName(os.path.join("themes",self.themename,"avatars"))
        if os.path.exists(themeavatarpath):
            themeavatarfiles = [ f for f in os.listdir(themeavatarpath) if os.path.isfile(os.path.join(themeavatarpath, f)) ]
            themeavatarfiles.sort()

        for i in themeavatarfiles:
            image = engine.loadImgDrawing(self, "av"+str(i), os.path.join("themes",self.themename,"avatars",str(i)))
            if not image:
                exists = 0
                continue
            else:
                exists = 1

            if exists == 1:
                self.avatar.append(str(i)[:-4]) # evilynux - filename w/o extension
                self.avatars.append(image)
                self.maxAv += 1
        self.themeAvs = len(self.avatars)

        for i in avatarfiles:
            image = engine.loadImgDrawing(self, "av"+str(i), os.path.join("avatars",str(i)))
            if not image:
                exists = 0
                continue
            else:
                exists = 1

            if exists == 1:
                self.avatar.append(str(i)[:-4]) # evilynux - filename w/o extension
                self.avatars.append(image)
                self.maxAv += 1

        Log.debug("%d Theme Avatars found; %d total." % (self.themeAvs, len(self.avatars)))
        self.avScale = []
        for avatar in self.avatars:
            imgheight = avatar.height1()
            imgwidth  = avatar.width1()
            hFactor = 110.00/imgheight
            wFactor = 178.00/imgwidth
            self.avScale.append(min(hFactor, wFactor))
        self.maxAv -= 1 # evilynux - confusing, but there's an offset of -1

        self.accepted       = False
        self.time           = 0.0
        self.dist           = 1.0


        #MFH - added simple black background to place in front of Options background, behind Neck BG, for transparent neck displays
        if not self.engine.loadImgDrawing(self, "avFrame", os.path.join("themes",self.themename,"lobby","avatarframe.png")):
            self.avFrame = None

        if not self.engine.loadImgDrawing(self, "avSelFrame", os.path.join("themes",self.themename,"lobby","avatarselectframe.png")):
            self.avSelFrame = self.avFrame

        if not self.engine.loadImgDrawing(self, "avBigFrame", os.path.join("themes",self.themename,"lobby","avatarmainframe.png")):
            self.avBigFrame = self.avFrame

        if not self.engine.loadImgDrawing(self, "avText", os.path.join("themes",self.themename,"lobby","avatartext.png")):
            self.avText = None

        self.avFrameScale = None
        if self.avFrame:
            imgheight = self.avFrame.height1()
            imgwidth  = self.avFrame.width1()
            hFactor = 110.00/imgheight
            wFactor = 178.00/imgwidth
            self.avFrameScale = (wFactor, -hFactor)

        self.avSelFrameScale = None
        if self.avSelFrame:
            imgheight = self.avSelFrame.height1()
            imgwidth  = self.avSelFrame.width1()
            hFactor = 110.00/imgheight
            wFactor = 178.00/imgwidth
            self.avSelFrameScale = (wFactor, -hFactor)

        self.avBigFrameScale = None
        if self.avBigFrame:
            imgheight = self.avBigFrame.height1()
            imgwidth  = self.avBigFrame.width1()
            hFactor = 110.00/imgheight
            wFactor = 178.00/imgwidth
            self.avBigFrameScale = (wFactor, -hFactor)

        self.avatarText = _("Select Your Avatar:")

        if not self.engine.loadImgDrawing(self, "background", os.path.join("themes",self.themename,"lobby","avatarbg.png")):
            self.background = None

        hideLoadingSplashScreen(self.engine, splash)
        splash = None

    def shown(self):
        self.engine.input.addKeyListener(self, priority = True)

    def hidden(self):
        self.engine.input.removeKeyListener(self)

    def cancel(self):
        self.accepted = False
        self.engine.view.popLayer(self)

    def keyPressed(self, key, unicode):
        c = self.engine.input.controls.getMapping(key)
        if c in Player.key1s or key == pygame.K_RETURN:
            self.accepted = True
            self.engine.data.acceptSound.play()
            self.engine.view.popLayer(self)
        elif c in Player.key2s + Player.cancels or key == pygame.K_ESCAPE:
            self.engine.data.cancelSound.play()
            self.cancel()
        elif c in Player.key3s + Player.ups + Player.action1s + Player.lefts or key == pygame.K_UP or key == pygame.K_LEFT:
            self.scrolling = 1
            self.delay = self.engine.scrollDelay
            self.scrollUp()
        elif c in Player.key4s + Player.downs + Player.action2s + Player.rights or key == pygame.K_DOWN or key == pygame.K_RIGHT:
            self.scrolling = 2
            self.delay = self.engine.scrollDelay
            self.scrollDown()
        return True

    def scrollUp(self):
        self.engine.data.selectSound.play()
        self.selectedAv -= 1
        if self.selectedAv < 0:
            self.selectedAv = len(self.avatars) - 1

    def scrollDown(self):
        self.engine.data.selectSound.play()
        self.selectedAv += 1
        if self.selectedAv >= len(self.avatars):
            self.selectedAv = 0

    def keyReleased(self, key):
        self.scrolling = 0

    def getAvatar(self):
        if self.accepted:
            t = self.selectedAv < self.themeAvs and self.avatars[self.selectedAv].filename
            return t
        else:
            return None

    def run(self, ticks):
        self.time += ticks / 50.0
        if self.dist > 0:
            self.dist -= ticks / 750.0
            if self.dist < 0:
                self.dist = 0
        if self.scrolling > 0:
            self.delay -= ticks
            self.rate += ticks
            if self.delay <= 0 and self.rate >= self.engine.scrollRate:
                self.rate = 0
                self.scroller[self.scrolling]()

    def render(self, visibility, topMost):
        v = (1 - visibility) ** 2
        self.engine.view.setViewport(1,0)
        w, h, = self.engine.view.geometry[2:4]

        with self.engine.view.orthogonalProjection(normalize = True):
            if self.background:
                self.engine.drawImage(self.background, scale = (1.0, -1.0), coord = (w/2,h/2), stretched = FULL_SCREEN)
            else:
                self.engine.fadeScreen(v)
            self.engine.theme.setBaseColor(1 - v)
            if len(self.avatars) > 1:
                lastAv2i  = (int(self.selectedAv)-2) % len(self.avatars)
                lastAvi   = (int(self.selectedAv)-1) % len(self.avatars)
                nextAvi   = (int(self.selectedAv)+1) % len(self.avatars)
                nextAv2i  = (int(self.selectedAv)+2) % len(self.avatars)
            else:
                lastAv2i  = 0
                lastAvi   = 0
                nextAvi   = 0
                nextAv2i  = 0
            lastAv2   = self.avatars[lastAv2i]
            lastAv    = self.avatars[lastAvi]
            currentAv = self.avatars[int(self.selectedAv)]
            nextAv    = self.avatars[nextAvi]
            nextAv2   = self.avatars[nextAv2i]

            self.x1 = w*(0.07-self.dist/2)
            self.x2 = w*(0.17-self.dist/2)
            self.x3 = w*(0.24-self.dist/2)
            self.x4 = w*(0.17-self.dist/2)
            self.x5 = w*(0.07-self.dist/2)
            self.y1 = h*(0.75+self.engine.theme.avatarSelectWheelY)
            self.y2 = h*(0.68+self.engine.theme.avatarSelectWheelY)
            self.y3 = h*(0.5+self.engine.theme.avatarSelectWheelY)
            self.y4 = h*(0.32+self.engine.theme.avatarSelectWheelY)
            self.y5 = h*(0.25+self.engine.theme.avatarSelectWheelY)
            bigCoord = (w*(self.engine.theme.avatarSelectAvX+self.dist),h*self.engine.theme.avatarSelectAvY)

            if self.avBigFrame:
                self.engine.drawImage(self.avFrame, scale = (self.avBigFrameScale[0]*1.75,self.avBigFrameScale[1]*1.75), coord = bigCoord)
            self.engine.drawImage(currentAv, scale = (self.avScale[self.selectedAv]*1.75,-self.avScale[self.selectedAv]*1.75), coord = bigCoord)

            if self.avFrame:
                self.engine.drawImage(self.avFrame, scale = self.avFrameScale, coord = (self.x1,self.y1))
            self.engine.drawImage(lastAv2, scale = (self.avScale[lastAv2i],-self.avScale[lastAv2i]), coord = (self.x1,self.y1))
            if self.avFrame:
                self.engine.drawImage(self.avFrame, scale = self.avFrameScale, coord = (self.x2,self.y2))
            self.engine.drawImage(lastAv, scale = (self.avScale[lastAvi], -self.avScale[lastAvi]), coord = (self.x2,self.y2))
            if self.avFrame:
                self.engine.drawImage(self.avFrame, scale = self.avFrameScale, coord = (self.x5,self.y5))
            self.engine.drawImage(nextAv2, scale = (self.avScale[nextAv2i],-self.avScale[nextAv2i]), coord = (self.x5,self.y5))
            if self.avFrame:
                self.engine.drawImage(self.avFrame, scale = self.avFrameScale, coord = (self.x4,self.y4))
            self.engine.drawImage(nextAv, scale = (self.avScale[nextAvi],-self.avScale[nextAvi]), coord = (self.x4,self.y4))
            if self.avSelFrame:
                self.engine.drawImage(self.avSelFrame, scale = self.avSelFrameScale, coord = (self.x3,self.y3))
            self.engine.drawImage(currentAv, scale = (self.avScale[int(self.selectedAv)],-self.avScale[int(self.selectedAv)]), coord = (self.x3,self.y3))

            try:
                font = self.engine.data.fontDict[self.engine.theme.avatarSelectFont]
            except:
                font = self.engine.data.font
            if self.avText:
                self.engine.drawImage(self.avText, scale = (self.engine.theme.avatarSelectTextScale, -self.engine.theme.avatarSelectTextScale), coord = (self.engine.theme.avatarSelectTextX, self.engine.theme.avatarSelectTextY - v))
            else:
                font.render(self.avatarText, (self.engine.theme.avatarSelectTextX, self.engine.theme.avatarSelectTextY - v), scale = self.engine.theme.avatarSelectTextScale)
        #==============================================================

class PartDiffChooser(MainDialog):
    """Part and difficulty select layer"""
    def __init__(self, engine, parts, info, players, back = False):
        MainDialog.__init__(self, engine)
        self.parts   = parts
        self.info    = info
        self.players = players
        self.theme   = engine.theme

        self.retVal  = None

        self.gameModeText = self.engine.world.gameName

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("PartDiffChooser class init (Dialogs.py)...")
        self.time    = 0.0

        self.yes        = []
        self.no         = []
        self.conf       = []
        self.up         = []
        self.down       = []

        for player in self.players:
            self.yes.extend(player.yes)
            self.no.extend(player.no)
            self.conf.extend(player.conf)
            self.up.extend(player.up)
            self.down.extend(player.down)

        self.partImages     = self.engine.data.partImages
        self.keyControl     = 0
        self.scrolling      = [0 for i in self.players]
        self.rate           = [0 for i in self.players]
        self.delay          = [0 for i in self.players]
        self.scroller       = [0, self.scrollUp, self.scrollDown]
        self.selected       = []
        self.mode           = [back and 1 or 0 for i in self.players]
        self.readyPlayers   = []
        for i in range(len(self.players)):
            if self.mode[i] == 1:
                if len(self.info.partDifficulties[self.players[i].part.id]) == 1:
                    self.mode[i] -= 1
                else:
                    for j, d in enumerate(self.info.partDifficulties[self.players[i].part]):
                        if d == self.players[i].difficulty:
                            self.selected.append(j)
                            break
                    else:
                        self.selected.append(0)
            if self.mode[i] == 0:
                if len(self.parts[i]) == 1:
                    self.players[i].part = self.parts[i][0]
                    self.mode[i] += 1
                    if len(self.info.partDifficulties[self.players[i].part.id]) == 1:
                        self.players[i].difficulty = self.info.partDifficulties[self.players[i].part.id][0]
                        self.readyPlayers.append(i)
                        self.selected.append(0)
                    else:
                        for j, d in enumerate(self.info.partDifficulties[self.players[i].part.id]):
                            if d == self.players[i].difficulty:
                                self.selected.append(j)
                                break
                        else:
                            self.selected.append(0)
                else:
                    for j, p in enumerate(self.parts[i]):
                        if p == self.players[i].part:
                            self.selected.append(j)
                            break
                    else:
                        self.selected.append(0)
        if len(self.readyPlayers) == len(self.players):
            self.retval = True
            self.engine.view.popLayer(self)
            return

        if os.path.isdir(os.path.join(self.engine.data.path,"themes",self.engine.data.themeLabel,"setlist","parts")):
            self.engine.data.loadAllImages(self, os.path.join("themes",self.engine.data.themeLabel,"setlist","parts"))

    def scrollUp(self, i):
        self.selected[i] -= 1
        if self.selected[i] < 0:
            if self.mode[i] == 0:
                self.selected[i] = len(self.parts[i]) - 1
            elif self.mode[i] == 1:
                self.selected[i] = len(self.info.partDifficulties[self.players[i].part.id]) - 1

    def scrollDown(self, i):
        self.selected[i] += 1
        if self.mode[i] == 0:
            if self.selected[i] == len(self.parts[i]):
                self.selected[i] = 0
        elif self.mode[i] == 1:
            if self.selected[i] == len(self.info.partDifficulties[self.players[i].part.id]):
                self.selected[i] = 0

    def keyPressed(self, key, unicode):
        c = self.engine.input.controls.getMapping(key)
        for i in range(len(self.players)):
            if key in [pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_UP, pygame.K_DOWN, pygame.K_RIGHT, pygame.K_LEFT, pygame.K_SPACE]:
                continue
            if c and c in self.players[i].keyList:
                break
        else:
            i = self.keyControl
        if c in self.yes + [self.players[i].keyList[Player.UP]] or key == pygame.K_RETURN:
            if self.mode[i] == 0:
                self.players[i].part = self.parts[i][self.selected[i]]
                for j, d in enumerate(self.info.partDifficulties[self.players[i].part.id]):
                    if d == self.players[i].difficulty:
                        self.selected[i] = j
                else:
                    self.selected[i] = 0
                self.mode[i] += 1
            elif self.mode[i] == 1:
                self.players[i].difficulty = self.info.partDifficulties[self.players[i].part.id][self.selected[i]]
                if i not in self.readyPlayers:
                    self.engine.data.acceptSound.play()
                    self.readyPlayers.append(i)
                if len(self.readyPlayers) == len(self.players):
                    self.retVal = True
                    self.engine.view.popLayer(self)
            return True
        elif c in self.no + [self.players[i].keyList[Player.KEY2]] or key == pygame.K_ESCAPE:
            if self.mode[i] == 0:
                if c in Player.menuNo:
                    self.engine.data.cancelSound.play()
                    self.retVal = False
                    self.engine.view.popLayer(self)
            elif self.mode[i] == 1:
                self.engine.data.cancelSound.play()
                if i in self.readyPlayers:
                    self.readyPlayers.remove(i)
                else:
                    self.mode[i] = 0
                    for j, p in enumerate(self.parts[i]):
                        if p == self.players[i].part:
                            self.selected[i] = j
                            break
                    else:
                        self.selected[i] = 0
            return True
        elif i in self.readyPlayers:
            return True
        elif c in self.up + [self.players[i].keyList[Player.UP]] or key == pygame.K_LEFT or key == pygame.K_UP:
            self.scrolling[i] = 1
            self.scrollUp(i)
            self.delay[i] = self.engine.scrollDelay
        elif c in self.down + [self.players[i].keyList[Player.DOWN]] or key == pygame.K_RIGHT or key == pygame.K_DOWN:
            self.scrolling[i] = 2
            self.scrollDown(i)
            self.delay[i] = self.engine.scrollDelay
        elif key == pygame.K_SPACE:
            pass
        return True

    def keyReleased(self, key):
        c = self.engine.input.controls.getMapping(key)
        for i in range(len(self.players)):
            if key in [pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_UP, pygame.K_DOWN, pygame.K_RIGHT, pygame.K_LEFT]:
                continue
            if c and c in self.players[i].keyList:
                break
        else:
            i = self.keyControl
        self.scrolling[i] = 0

    def run(self, ticks):
        self.time += ticks/50.0
        for i in range(len(self.players)):
            if self.scrolling[i] > 0:
                self.delay[i] -= ticks
                self.rate[i] += ticks
                if self.delay[i] <= 0 and self.rate[i] >= self.engine.scrollRate:
                    self.rate[i] = 0
                    self.scroller[self.scrolling[i]](i)
        self.engine.theme.partDiff.run(ticks)

    def render(self, visibility, topMost):
        self.engine.view.setViewport(1,0)
        w, h = self.geometry

        with self.engine.view.orthogonalProjection(normalize = True):
            if self.img_background:
                self.engine.drawImage(self.img_background, scale = (1.0, -1.0), coord = (w/2,h/2), stretched = FULL_SCREEN)
            self.theme.partDiff.renderPanels(self)

class ItemChooser(BackgroundLayer, KeyListener):
    """Item menu layer."""
    def __init__(self, engine, items, selected = None, prompt = "", pos = None):    #MFH
        self.prompt         = prompt
        self.engine         = engine

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("ItemChooser class init (Dialogs.py)...")

        self.accepted       = False
        self.selectedItem   = None
        self.time           = 0.0

        self.font = self.engine.data.streakFont2
        self.promptScale = 0.002
        self.promptWidth, self.promptHeight = self.font.getStringSize(self.prompt, scale=self.promptScale)
        widthOfSpace, heightOfSpace = self.font.getStringSize(" ", scale=self.promptScale)

        if pos: #MFH
            self.songSelectSubmenuOffsetLines = self.engine.theme.songSelectSubmenuOffsetLines
            self.songSelectSubmenuOffsetSpaces = self.engine.theme.songSelectSubmenuOffsetSpaces
            self.posX, self.posY = pos
            wrapX, wrapY = wrapText(self.font, (self.posX, self.posY), self.prompt, scale = self.promptScale)
            self.menu = Menu(self.engine, choices = [(c, self._callbackForItem(c)) for c in items], onClose = self.close, onCancel = self.cancel, font = self.engine.data.streakFont2, pos = (self.posX + widthOfSpace*(self.songSelectSubmenuOffsetSpaces+1), wrapY + self.promptHeight*(self.songSelectSubmenuOffsetLines+1)) )
        else:
            self.posX = .1    #MFH - default
            self.posY = .05   #MFH - default
            self.menu = Menu(self.engine, choices = [(c, self._callbackForItem(c)) for c in items], onClose = self.close, onCancel = self.cancel, font = self.engine.data.streakFont2)

        if selected and selected in items:
            self.menu.selectItem(items.index(selected))

        #Get theme
        self.theme = self.engine.data.theme

    def _callbackForItem(self, item):
        def cb():
            self.chooseItem(item)
        return cb

    def chooseItem(self, item):
        self.selectedItem = item
        self.engine.view.popLayer(self.menu)
        self.engine.view.popLayer(self)

    def cancel(self):
        self.accepted = True
        self.engine.view.popLayer(self)

    def close(self):
        self.accepted = True
        self.engine.view.popLayer(self)

    def shown(self):
        self.engine.view.pushLayer(self.menu)

    def getSelectedItem(self):
        return self.selectedItem

    def run(self, ticks):
        self.time += ticks / 50.0

    def render(self, visibility, topMost):
        v = (1 - visibility) ** 2

        # render the background
        self.engine.view.setViewport(1,0)
        w, h, = self.engine.view.geometry[2:4]

        #MFH - auto background scaling
        if self.engine.data.optionsBG:
            self.engine.drawImage(self.engine.data.optionsBG, scale = (1.0, -1.0), coord = (w/2,h/2), stretched = FULL_SCREEN)

        with self.engine.view.orthogonalProjection(normalize = True):
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_COLOR_MATERIAL)
            self.engine.theme.setBaseColor(1 - v)
            wrapText(self.font, (self.posX, self.posY - v), self.prompt, scale = self.promptScale)

class KeyTester(Layer, KeyListener):
    """Keyboard configuration testing layer."""
    def __init__(self, engine, control, prompt = ""):
        self.prompt         = prompt
        self.engine         = engine

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("KeyTester class init (Dialogs.py)...")


        self.accepted       = False
        self.time           = 0.0
        self.controls       = self.engine.input.controls
        self.controlNum     = control
        self.keyList        = Player.CONTROLS[control]
        self.type           = self.controls.type[control]
        self.analogKillMode = self.controls.analogKill[control]
        self.analogSPMode   = self.controls.analogSP[control]
        self.analogSPThresh = self.controls.analogSPThresh[control]
        self.analogSPSense  = self.controls.analogSPSense[control]
        self.analogDrumMode = self.controls.analogDrum[control] #FIXME: Analog Drum
        self.analogSlideMode = self.controls.analogSlide[control]

        if self.type < 2 or self.type == 4:
            self.fretColors     = self.engine.theme.noteColors
            self.names          = [_("Left"), _("Right"), _("Up"), _("Down"), _("Start"), \
                                   _("Select"), _("Fret #1"), _("Solo #1"), _("Fret #2"), _("Solo #2"), \
                                   _("Fret #3"), _("Solo #3"), _("Fret #4"), _("Solo #4"), _("Fret #5"), \
                                   _("Solo #5"), _("Pick!"), _("Pick!"), _("Starpower!"), _("Whammy")]
        elif self.type == 2:
            colors              = self.engine.theme.noteColors
            self.fretColors     = [colors[1], colors[2], colors[3], colors[0]]
            self.bassColor      = colors[4]
            self.names          = [_("Left"), _("Right"), _("Up"), _("Down"), _("Start"), \
                                   _("Select"), _("Drum #1"), None, _("Drum #2"), None, \
                                   _("Drum #3"), None, None, None, _("Drum #4"), \
                                   None, _("Bass Drum"), None, _("Starpower!"), _("None")]
        elif self.type == 5:
            self.names          = [_("Left"), _("Right"), _("Up"), _("Down"), _("Start"), \
                                   _("Select"), None, None, None, None, \
                                   None, None, None, None, None, \
                                   None, None, None, _("Starpower!"), None]
        else:
            colors              = self.engine.theme.noteColors
            self.fretColors     = [colors[1], colors[2], colors[3], colors[4], colors[0]]
            self.bassColor      = self.engine.theme.colors[5]
            self.names          = [_("Left"), _("Right"), _("Up"), _("Down"), _("Start"), \
                                   _("Select"), _("Drum #1"), None, _("Cymbal #2"), None, \
                                   _("Drum #3"), None, _("Cymbal #4"), None, _("Drum #5"), \
                                   None, _("Bass Drum"), None, _("Starpower!"), _("None")]

        self.tsFret  = _("Fret")
        self.tsSolo  = _("Solo")
        self.tsDrum  = _("Drum")
        self.tsSlide = _("Slide~")

        self.engine.loadImgDrawing(self, "arrow", "arrow.png")
        self.engine.loadImgDrawing(self, "circle", "test.png")
        self.engine.loadImgDrawing(self, "analogBar", "analog.png")
        self.engine.loadImgDrawing(self, "analogBox", "analogback.png")
        self.engine.loadImgDrawing(self, "analogThresh", "analogthresh.png")
        self.analogBoxScale = 1.0/6.0
        self.analogBarScale = 1.0/6.0
        self.analogThreshScale = 5.000/self.analogThresh.width1()

        #evilynux - Get killswitch mode (analog or digital?)
        # If analog, get and show attenuation. Most code taken from GuitarScene.
        self.isKillAnalog = False
        self.isSPAnalog = False
        self.isSlideAnalog = False
        self.areDrumsAnalog = False
        self.whichJoyKill = 0
        self.whichAxisKill = 0
        self.whichJoyStar = 0
        self.whichAxisStar = 0
        self.whichJoySlide = 0
        self.whichAxisSlide = 0
        self.whichJoyDrum1 = 0
        self.whichAxisDrum1 = 0
        self.whichJoyDrum2 = 0
        self.whichAxisDrum2 = 0
        self.whichJoyDrum3 = 0
        self.whichAxisDrum3 = 0
        self.whichJoyDrum4 = 0
        self.whichAxisDrum4 = 0
        self.whichJoyDrum5 = 0
        self.whichAxisDrum5 = 0
        self.whammy = 0
        self.starpower = 0
        self.slideActive = -1
        self.midFret = False

        if len(self.engine.input.joysticks) != 0 and self.type < 2 or self.type == 4:
            if self.analogKillMode > 0:
                KillKeyCode = self.controls.getReverseMapping(self.keyList[Player.KILL])
                self.isKillAnalog, self.whichJoyKill, self.whichAxisKill = self.engine.input.getWhammyAxis(KillKeyCode)
            if self.analogSPMode > 0:
                StarKeyCode = self.controls.getReverseMapping(self.keyList[Player.STAR])
                self.isSPAnalog, self.whichJoyStar, self.whichAxisStar = self.engine.input.getWhammyAxis(StarKeyCode)
            if self.type == 4:
                SlideKeyCode = self.controls.getReverseMapping(self.keyList[Player.KEY1A])
                self.isSlideAnalog, self.whichJoySlide, self.whichAxisSlide = self.engine.input.getWhammyAxis(SlideKeyCode)

    def shown(self):
        if self.type == 5:
            self.mic = Microphone.Microphone(self.engine, self.controlNum)
            self.mic.start()
        self.engine.input.addKeyListener(self, priority = True)

    def hidden(self):
        if hasattr(self, 'mic'):
            self.mic.stop()
            del self.mic
        self.engine.input.removeKeyListener(self)

    def keyPressed(self, key, unicode):
        if self.accepted:
            return True
        if key == pygame.K_ESCAPE:
            self.engine.view.popLayer(self)
            self.accepted = True
            return True
        c = self.engine.input.controls.getMapping(key)
        self.controls.keyPressed(key)
        if self.type > 1 and self.type not in (4, 5):
            if c == self.keyList[Player.DRUM1]:
                self.engine.data.T1DrumSound.play()
            elif c == self.keyList[Player.DRUM2]:
                if self.type == 2:
                    self.engine.data.T2DrumSound.play()
                else:
                    self.engine.data.CDrumSound.play()
            elif c == self.keyList[Player.DRUM3]:
                if self.type == 2:
                    self.engine.data.T3DrumSound.play()
                else:
                    self.engine.data.T2DrumSound.play()
            elif c == self.keyList[Player.DRUM4]:
                self.engine.data.CDrumSound.play()
            elif c == self.keyList[Player.DRUM5]:
                if self.type == 2:
                    self.engine.data.CDrumSound.play()
                else:
                    self.engine.data.T3DrumSound.play()
        return True

    def keyReleased(self, key):
        self.controls.keyReleased(key)

    def run(self, ticks):
        self.time += ticks
        if self.isSPAnalog:
            if self.starpower > (self.analogSPThresh/100.0):
                if self.starDelay == 0 and not self.starpowerActive:
                    self.starDelay = (10-self.analogSPSense)*25
                else:
                    self.starDelay -= ticks
                    if self.starDelay <= 0:
                        self.starpowerActive = True
            else:
                self.starpowerActive = False
                self.starDelay = 0

    def render(self, visibility, topMost):
        v = (1 - visibility) ** 2

        self.engine.view.setViewport(1,0)
        font = self.engine.data.font
        w, h = self.engine.view.geometry[2:4]

        with self.engine.view.orthogonalProjection(normalize = True):
            if self.controls.getState(self.keyList[Player.UP]):
                if self.controls.getState(self.keyList[Player.LEFT]):
                    rotateArrow = math.pi/4
                elif self.controls.getState(self.keyList[Player.RIGHT]):
                    rotateArrow = -math.pi/4
                else:
                    rotateArrow = 0.0
            elif self.controls.getState(self.keyList[Player.DOWN]):
                if self.controls.getState(self.keyList[Player.LEFT]):
                    rotateArrow = 3*math.pi/4
                elif self.controls.getState(self.keyList[Player.RIGHT]):
                    rotateArrow = -3*math.pi/4
                else:
                    rotateArrow = math.pi
            elif self.controls.getState(self.keyList[Player.LEFT]):
                rotateArrow = math.pi/2
            elif self.controls.getState(self.keyList[Player.RIGHT]):
                rotateArrow = -math.pi/2
            else:
                rotateArrow = None

            self.engine.fadeScreen(v)

            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_COLOR_MATERIAL)
            self.engine.theme.setBaseColor(1 - v)
            wrapText(font, (.1, .2 - v), self.prompt)

            self.engine.drawImage(self.circle, scale = (.5, -.5), coord = (w*.5,h*.6))
            if rotateArrow is not None:
                self.engine.drawImage(self.arrow,  scale = (.5, -.5), coord = (w*.5,h*.6), rot = rotateArrow)

            if self.type != 5:
                #akedrou - analog starpower, analog slider
                text = self.names[Player.STAR]
                wText, hText = font.getStringSize(text)

                if self.isSlideAnalog:
                    if self.analogSlideMode == 1:  #Inverted mode
                        slideVal = -(self.engine.input.joysticks[self.whichJoySlide].get_axis(self.whichAxisSlide)+1.0)/2.0
                    else:  #Default
                        slideVal = (self.engine.input.joysticks[self.whichJoySlide].get_axis(self.whichAxisSlide)+1.0)/2.0
                    if slideVal > 0.9 or slideVal < 0.01:
                        self.slideActive = 4
                        self.midFret = False
                    elif slideVal > 0.77:
                        self.slideActive = 4
                        self.midFret = True
                    elif slideVal > 0.68:
                        self.slideActive = 3
                        self.midFret = False
                    elif slideVal > 0.60:
                        self.slideActive = 3
                        self.midFret = True
                    elif slideVal > 0.54:
                        self.slideActive = 2
                        self.midFret = False
                    elif slideVal > 0.43:
                        self.slideActive = -1
                        self.midFret = False
                    elif slideVal > 0.34:
                        self.slideActive = 2
                        self.midFret = True
                    elif slideVal > 0.28:
                        self.slideActive = 1
                        self.midFret = False
                    elif slideVal > 0.16:
                        self.slideActive = 1
                        self.midFret = True
                    else:
                        self.slideActive = 0
                        self.midFret = False

                if self.isSPAnalog:
                    starThresh = (self.analogSPThresh/100.0)*(w/6.0)-(w/12.0)
                    self.engine.drawImage(self.analogThresh, scale = (self.analogThreshScale, -self.analogThreshScale), coord = ((w*.25)+starThresh, h*.3))
                    #(0.0 at level, -1 upright; 1 upside down)
                    self.starpower = abs(self.engine.input.joysticks[self.whichJoyStar].get_axis(self.whichAxisStar))

                if self.starpower > 0:
                    if self.starpowerActive:
                        self.engine.theme.setSelectedColor(1 - v)
                    else:
                        glColor3f(.4, .4, .4)
                    font.render(text, (.25-wText/2, .45 + v))
                    starC = (1-self.starpower)*.5*w*self.analogBarScale
                    self.engine.drawImage(self.analogBar, scale = (self.analogBarScale*self.starpower, -self.analogBarScale), coord = ((w*.25)-starC, h*.3), rect = (0, self.starpower, 0, 1), stretched = KEEP_ASPECT | FIT_WIDTH)
                    self.engine.drawImage(self.analogBox, scale = (self.analogBoxScale, -self.analogBoxScale), coord = (w*.25, h*.3), stretched = KEEP_ASPECT | FIT_WIDTH)
                else:
                    if self.controls.getState(self.keyList[Player.STAR]):
                        self.engine.theme.setSelectedColor(1 - v)
                    else:
                        glColor3f(.4, .4, .4)
                    font.render(text, (.25-wText/2, .45 + v))

            if self.controls.getState(self.keyList[Player.CANCEL]):
                glColor3f(.6, 0, 0)
            else:
                glColor3f(.4, .4, .4)
            text = self.names[5]
            wText, hText = font.getStringSize(text)
            font.render(text, (.333-wText/2, .28 + v))

            if self.controls.getState(self.keyList[Player.START]):
                glColor3f(0, .6, 0)
            else:
                glColor3f(.4, .4, .4)
            text = self.names[4]
            wText, hText = font.getStringSize(text)
            font.render(text, (.667-wText/2, .28 + v))

            if self.type < 2 or self.type == 4:

                if self.type == 0:
                    for i in range(5):
                        if self.controls.getState(self.keyList[(2*i)+Player.KEY1]):
                            glColor3f(*self.fretColors[i%5])
                            text = self.tsFret
                        elif self.controls.getState(self.keyList[(2*i)+1+Player.KEY1]):
                            glColor3f(*self.fretColors[i%5])
                            text = self.tsSolo
                        else:
                            glColor3f(.4, .4, .4)
                            text = self.tsFret
                        text = "%s #%d" % (text, (i + 1))
                        wText, hText = font.getStringSize(text)
                        font.render(text, ((.2 + .15 * i)-wText/2, .4 + v))
                else:
                    for i in range(5):
                        if self.slideActive == i or (self.midFret and self.slideActive == i + 1) or (self.controls.getState(self.keyList[Player.KEY1A]) and self.type == 1):
                            text = self.tsSolo
                        else:
                            text = self.tsFret
                        if self.controls.getState(self.keyList[(2*i)+Player.KEY1]) or self.slideActive == i or (self.midFret and self.slideActive == i + 1):
                            glColor3f(*self.fretColors[i%5])
                        else:
                            glColor3f(.4, .4, .4)
                        text = "%s #%d" % (text, (i + 1))
                        wText, hText = font.getStringSize(text)
                        font.render(text, ((.2 + .15 * i)-wText/2, .4 + v))
                        if self.midFret and self.slideActive == i:
                            self.engine.theme.setSelectedColor(1 - v)
                            text = self.tsSlide
                            wText, hText = font.getStringSize(text)
                            font.render(text, ((.125 + .15 * i)-wText/2, .35 + v))

                #evilynux - Compute analog killswitch value
                wText, hText = font.getStringSize(self.names[Player.KILL])
                if self.isKillAnalog:
                    if self.analogKillMode == 2:  #XBOX mode: (1.0 at rest, -1.0 fully depressed)
                        self.whammy = 1.0 - ((self.engine.input.joysticks[self.whichJoyKill].get_axis(self.whichAxisKill)+1.0) / 2.0)

                    elif self.analogKillMode == 3:  #XBOX Inverted mode: (-1.0 at rest, 1.0 fully depressed)
                        self.whammy = (self.engine.input.joysticks[self.whichJoyKill].get_axis(self.whichAxisKill)+1.0) / 2.0

                    else: #PS2 mode: (0.0 at rest, fluctuates between 1.0 and -1.0 when pressed)
                        self.whammy = abs(self.engine.input.joysticks[self.whichJoyKill].get_axis(self.whichAxisKill))

                #evilynux - analog killswitch rendering
                if self.whammy > 0:
                    if self.whammy > 0.1:
                        self.engine.theme.setSelectedColor(1 - v)
                    else:
                        glColor3f(.4, .4, .4)
                    font.render(self.names[Player.KILL], (.75-wText/2, .45 + v))
                    whammyC = (1-self.whammy)*.5*w*self.analogBarScale
                    self.engine.drawImage(self.analogBar, scale = (self.analogBarScale*self.whammy, -self.analogBarScale), coord = (w*.75-whammyC, h*.3), rect = (0, self.whammy, 0, 1), stretched = KEEP_ASPECT | FIT_WIDTH)
                else:
                    if self.controls.getState(self.keyList[Player.KILL]):
                        self.engine.theme.setSelectedColor(1 - v)
                    else:
                        glColor3f(.4, .4, .4)
                    font.render(self.names[Player.KILL], (.75-wText/2, .45 + v))

                self.engine.drawImage(self.analogBox, scale = (self.analogBoxScale, -self.analogBoxScale), coord = (w*.75, h*.3), stretched = KEEP_ASPECT | FIT_WIDTH)
                if self.controls.getState(self.keyList[Player.ACTION1]) or self.controls.getState(self.keyList[Player.ACTION2]):
                    self.engine.theme.setSelectedColor(1 - v)
                else:
                    glColor3f(.4, .4, .4)
                wText, hText = font.getStringSize(self.names[Player.ACTION1])
                font.render(self.names[Player.ACTION1], (.5-wText/2, .55 + v))

            elif self.type == 5:
                self.engine.theme.setBaseColor(1 - v)
                font.render(_('Level:'), (.3, .4 + v))
                font.render(_('Note:'), (.3, .6 + v))

                peakvol = self.mic.getPeak()
                if peakvol < -5.0:
                    colorval = min(1.0, .4 + max(0.0, (peakvol+30.0) * .6 / 25.0))
                    glColor3f(colorval, colorval, colorval)
                else:
                    glColor3f(1.0, max(0.0, min(1.0, (peakvol/-5.0))), max(0.0, min(1.0, (peakvol/-5.0))))
                font.render('%5.3f dB' % peakvol, (.55, .4 + v))

                if self.mic.getTap():
                    self.engine.theme.setBaseColor(1 - v)
                else:
                    glColor3f(.4, .4, .4)
                font.render(_('Tap'), (.55, .5 + v))

                semitones = self.mic.getSemitones()
                if semitones is None:
                    glColor3f(.4, .4, .4)
                    font.render(_('None'), (.55, .6 + v))
                else:
                    self.engine.theme.setBaseColor(1 - v)
                    font.render(Microphone.getNoteName(semitones), (.55, .6 + v))

                f = self.mic.getFormants()
                if f[0] is not None:
                    self.engine.theme.setBaseColor(1 - v)
                    font.render("%.2f Hz" % f[0], (.45, .65 + v))
                else:
                    glColor3f(.4, .4, .4)
                    font.render("None", (.45, .65 + v))
                if f[1] is not None:
                    self.engine.theme.setBaseColor(1 - v)
                    font.render("%.2f Hz" % f[1], (.65, .65 + v))
                else:
                    glColor3f(.4, .4, .4)
                    font.render("None", (.65, .65 + v))

            elif self.type > 1:
                if self.type == 2:
                    drumList = [self.keyList[Player.DRUM1], self.keyList[Player.DRUM1A], self.keyList[Player.DRUM2], self.keyList[Player.DRUM2A], \
                                self.keyList[Player.DRUM3], self.keyList[Player.DRUM3A], self.keyList[Player.DRUM5], self.keyList[Player.DRUM5A]]
                    for i in range(4):
                        if self.controls.getState(drumList[(2*i)]) or self.controls.getState(drumList[(2*i)+1]):
                            glColor3f(*self.fretColors[i%5])
                        else:
                            glColor3f(.4, .4, .4)
                        text = self.tsDrum
                        text = "%s #%d" % (text, (i + 1))
                        wText, hText = font.getStringSize(text)
                        font.render(text, ((.2 + .2 * i)-wText/2, .4 + v))
                else:
                    drumList = [self.keyList[Player.DRUM1], self.keyList[Player.DRUM1A], self.keyList[Player.DRUM2], self.keyList[Player.DRUM2A], \
                                self.keyList[Player.DRUM3], self.keyList[Player.DRUM3A], self.keyList[Player.DRUM4], self.keyList[Player.DRUM4A], \
                                self.keyList[Player.DRUM5], self.keyList[Player.DRUM5A]]
                    for i in range(5):
                        if self.controls.getState(drumList[(2*i)]) or self.controls.getState(drumList[(2*i)+1]):
                            glColor3f(*self.fretColors[i%5])
                        else:
                            glColor3f(.4, .4, .4)
                        text = self.tsDrum
                        text = "%s #%d" % (text, (i + 1))
                        wText, hText = font.getStringSize(text)
                        font.render(text, ((.2 + .15 * i)-wText/2, .4 + v))

                if self.controls.getState(self.keyList[Player.DRUMBASS]) or self.controls.getState(self.keyList[Player.DRUMBASSA]):
                    glColor3f(*self.bassColor)
                else:
                    glColor3f(.4, .4, .4)
                wText, hText = font.getStringSize(self.names[Player.DRUMBASS])
                font.render(self.names[Player.DRUMBASS], (.5-wText/2, .5 + v))

def _runDialog(engine, dialog):
    """Run a dialog in a sub event loop until it is finished."""
    if not engine.running:
        return

    engine.view.pushLayer(dialog)

    while engine.running and dialog in engine.view.layers:
        engine.run()

def getText(engine, prompt, text = ""):
    """
    Get a string of text from the user.

    @param engine:  Game engine
    @param prompt:  Prompt shown to the user
    @param text:    Default text
    """
    d = GetText(engine, prompt, text)
    _runDialog(engine, d)
    return d.text

def getKey(engine, prompt, key = None, specialKeyList = []):
    """
    Ask the user to choose a key.

    @param engine:          Game engine
    @param prompt:          Prompt shown to the user
    @param key:             Default key
    @param specialKeyList:  A list of keys that are ineligible.
    """
    d = GetKey(engine, prompt, key, specialKeyList = specialKeyList)
    _runDialog(engine, d)
    return d.key

def chooseFile(engine, masks = ["*.*"], path = u".", prompt = _("Choose a File"), dirSelect = False):
    """
    Ask the user to select a file.

    @param engine:  Game engine
    @param masks:   List of glob masks for files that are acceptable
    @param path:    Initial path
    @param prompt:  Prompt shown to the user
    """
    d = FileChooser(engine, masks, path, prompt, dirSelect)
    _runDialog(engine, d)
    return d.getSelectedFile()

def chooseItem(engine, items, prompt = "", selected = None, pos = None):   #MFH
    """
    Ask the user to choose one item from a list.

    @param engine:    Game engine
    @param items:     List of items
    @param prompt:    Prompt shown to the user
    @param selected:  Item selected by default
    @param pos:       Position tuple (x,y) for placing the menu
    """
    d = ItemChooser(engine, items, prompt = prompt, selected = selected, pos = pos)
    _runDialog(engine, d)
    return d.getSelectedItem()

#MFH - on-demand Neck Chooser
def chooseNeck(engine, player = "default"):
    """
    Ask the user to choose their in-game neck.

    @param engine:    Game engine
    @type  player:    str
    @param player:    The active player
    """
    d = NeckChooser(engine, player = player)
    _runDialog(engine, d)
    return d.getSelectedNeck()

def chooseAvatar(engine):
    """
    Have the user select an avatar.

    @param engine:   Game engine
    """
    d = AvatarChooser(engine)
    _runDialog(engine, d)
    return d.getAvatar()

def choosePartDiffs(engine, parts, info, players):
    """
    Have the user select their part and difficulty.

    """
    d = PartDiffChooser(engine, parts, info, players)
    _runDialog(engine, d)
    return d.retVal

# evilynux - Show credits
def showCredits(engine):
    d = Credits(engine)
    _runDialog(engine, d)

def testKeys(engine, control, prompt = _("Play with the keys and press Escape when you're done.")):
    """
    Have the user test the current keyboard configuration.

    @param engine:  Game engine
    @param prompt:  Prompt shown to the user
    """
    if engine.input.controls.type[control] == 5 and not Microphone.supported:
        showMessage(engine, 'A required module for microphone support is missing.')
    else:
        d = KeyTester(engine, control, prompt = prompt)
        _runDialog(engine, d)

def showLoadingScreen(engine, condition, text = _("Loading..."), allowCancel = False):
    """
    Show a loading screen until a condition is met.

    @param engine:      Game engine
    @param condition:   A function that will be polled until it returns a true value
    @param text:        Text shown to the user
    @type  allowCancel: bool
    @param allowCancel: Can the loading be canceled
    @return:            True if the condition was met, False if the loading was canceled.
    """

    # poll the condition first for some time
    n = 0
    while n < 32:
        n += 1
        if condition():
            return True
        engine.run()

    d = LoadingScreen(engine, condition, text, allowCancel)
    _runDialog(engine, d)
    return d.ready

def showMessage(engine, text):
    """
    Show a message to the user.

    @param engine:  Game engine
    @param text:    Message text
    """
    Log.notice("%s" % text)
    d = MessageScreen(engine, text)
    _runDialog(engine, d)

# glorandwarf: added derived class LoadingSplashScreen
class LoadingSplashScreen(Layer, KeyListener):
    """Loading splash screen layer"""
    def __init__(self, engine, text):
        self.engine       = engine
        self.text         = text
        self.time         = 0.0
        self.loadingx = self.engine.theme.loadingX
        self.loadingy = self.engine.theme.loadingY
        self.textColor = self.engine.theme.loadingColor
        self.allowtext = self.engine.config.get("game", "lphrases")
        self.fScale = self.engine.theme.loadingFScale
        self.rMargin = self.engine.theme.loadingRMargin
        self.lspacing = self.engine.theme.loadingLSpacing
        self.loadingImg = self.engine.data.loadingImage

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("LoadingSplashScreen class init (Dialogs.py)...")

        #Get theme
        self.theme = self.engine.data.theme

    def shown(self):
        self.engine.input.addKeyListener(self, priority = True)

    def keyPressed(self, key, unicode):
        return True

    def hidden(self):
        self.engine.input.removeKeyListener(self)

    def run(self, ticks):
        self.time += ticks / 50.0

    def render(self, visibility, topMost):
        self.engine.view.setViewport(1,0)
        font = self.engine.data.loadingFont   #MFH - new font support

        if not font:
            return

        with self.engine.view.orthogonalProjection(normalize = True):
            v = (1 - visibility) ** 2
            self.engine.fadeScreen(v)
            w, h = self.engine.view.geometry[2:4]
            if self.loadingImg:
                self.engine.drawImage(self.loadingImg, scale = (1.0,-1.0), coord = (w/2,h/2), stretched = FULL_SCREEN)

            self.engine.theme.setBaseColor(1 - v)
            w, h = font.getStringSize(self.text, scale=self.fScale)

            x = self.loadingx
            y = self.loadingy - h / 2 + v * .5

            #akedrou - support for Loading Text Color
            c1,c2,c3 = self.textColor
            glColor3f(c1,c2,c3)

            # evilynux - Made text about 2 times smaller (as requested by worldrave)
            if self.allowtext:
                if self.theme == 1:
                    wrapCenteredText(font, (x,y), self.text, scale = self.fScale, rightMargin = self.rMargin, linespace = self.lspacing, allowshadowoffset = True, shadowoffset = (self.engine.theme.shadowoffsetx, self.engine.theme.shadowoffsety))
                else:
                    wrapCenteredText(font, (x,y), self.text, scale = self.fScale, rightMargin = self.rMargin, linespace = self.lspacing)

#nhydock - expanding on LoadingSplashScreen so there can be overlay and song dependant backgrounds
class SongLoadingSplashScreen(LoadingSplashScreen):
    def __init__(self, engine, text, songName, libraryName):
        super(SongLoadingSplashScreen, self).__init__(engine, text)

        self.engine.loadImgDrawing(self, "songBack", os.path.join(libraryName, songName, "loading.png"))
        if self.songBack:
            self.engine.loadImgDrawing(self, "loadingImg", os.path.join("themes", self.engine.data.themeLabel, "loading_overlay.png"))

    def render(self, visibility, topMost):
        self.engine.view.setViewport(1,0)
        font = self.engine.data.loadingFont   #MFH - new font support

        if not font:
            return

        with self.engine.view.orthogonalProjection(normalize = True):
            v = (1 - visibility) ** 2
            self.engine.fadeScreen(v)
            w, h = self.engine.view.geometry[2:4]

            self.engine.theme.setBaseColor(1 - v)
            if self.songBack:
                self.engine.drawImage(self.songBack, scale = (1.0,-1.0), coord = (w/2,h/2), stretched = FULL_SCREEN)
            self.engine.drawImage(self.loadingImg, scale = (1.0,-1.0), coord = (w/2,h/2), stretched = FULL_SCREEN)
            w, h = font.getStringSize(self.text, scale=self.fScale)

            x = self.loadingx
            y = self.loadingy - h / 2 + v * .5

            #akedrou - support for Loading Text Color
            c1,c2,c3 = self.textColor
            glColor3f(c1,c2,c3)

            # evilynux - Made text about 2 times smaller (as requested by worldrave)
            if self.allowtext:
                if self.theme == 1:
                    wrapCenteredText(font, (x,y), self.text, scale = self.fScale, rightMargin = self.rMargin, linespace = self.lspacing, allowshadowoffset = True, shadowoffset = (self.engine.theme.shadowoffsetx, self.engine.theme.shadowoffsety))
                else:
                    wrapCenteredText(font, (x,y), self.text, scale = self.fScale, rightMargin = self.rMargin, linespace = self.lspacing)

def showLoadingSplashScreen(engine, text = _("Loading...")):
    splash = LoadingSplashScreen(engine, text)
    engine.view.pushLayer(splash)
    engine.run()
    return splash

def showSongLoadingSplashScreen(engine, songName, libraryName, text = _("Loading...")):
    splash = SongLoadingSplashScreen(engine, text,  songName, libraryName)
    engine.view.pushLayer(splash)
    engine.run()
    return splash

def changeLoadingSplashScreenText(engine, splash, text=_("Loading...")):
    splash.text = text
    engine.run()

def hideLoadingSplashScreen(engine, splash):
    engine.view.popLayer(splash)

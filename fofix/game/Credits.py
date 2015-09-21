#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
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

from __future__ import with_statement

import os
import sys
import pygame

from OpenGL.GL import OpenGL, glColor4f, glTranslatef

from fretwork import log

from fofix.core.VideoPlayer import VideoLayer, VideoPlayerError
from fofix.core.Input import KeyListener
from fofix.core.Image import drawImage
from fofix.core.constants import *
from fofix.core.Language import _
from fofix.core.View import Layer
from fofix.core import Version
from fofix.core import Player
from fofix.core import Config



class Element:
    """A basic element in the credits scroller."""
    def getHeight(self):
        """@return: The height of this element in fractions of the screen height"""
        return 0

    def render(self, offset):
        """
        Render this element.

        @param offset: Offset in the Y direction in fractions of the screen height
        """
        pass

class Text(Element):
    def __init__(self, font, scale, color, alignment, text):
        self.text      = text
        self.font      = font
        self.color     = color
        self.alignment = alignment
        self.scale     = scale
        self.size      = self.font.getStringSize(self.text, scale = scale)

    def getHeight(self):
        return self.size[1]

    def render(self, offset):
        offset = (offset*4.0)/3.0 # akedrou - font rendering fix
        if self.alignment == "left":
            x = .1
        elif self.alignment == "right":
            x = .9 - self.size[0]
        elif self.alignment == "center":
            x = .5 - self.size[0] / 2
        glColor4f(*self.color)
        self.font.render(self.text, (x, offset), scale = self.scale)

class Picture(Element):
    def __init__(self, engine, fileName, height):
        self.height = height
        self.engine = engine
        self.engine = engine
        self.engine.loadImgDrawing(self, "drawing", fileName)

    def getHeight(self):
        return self.height

    def render(self, offset):
        offset = (offset*4.0)/3.0  #stump: get it back into alignment...
        w, h = self.engine.view.geometry[2:4]
        drawImage(self.drawing, scale = (1, -1),
                              coord = (.5 * w, h - (.5 * self.height + offset) * h * float(w) / float(h)))

# evilynux - Updated to latest MFH-Alarian mod. Alot changed compared to upstream FoF.
#            Removed song, our revamped MainMenu already provides songs.
class Credits(Layer, KeyListener):
    """Credits scroller."""
    def __init__(self, engine, songName = None):
        self.engine      = engine
        self.time        = 0.0
        self.offset      = 0.5 # akedrou - this seems to fix the delay issue, but I'm not sure why. Return here!
        self.speedDiv    = 20000.0
        self.speedDir    = 1.0
        self.doneList    = []
        self.themename = Config.get("coffee", "themename")

        nf = self.engine.data.font
        ns = 0.002
        bs = 0.001
        hs = 0.003
        c1 = (1, 1, .5, 1)
        c2 = (1, .75, 0, 1)
        self.text_size = nf.getLineSpacing(scale = hs)

        #akedrou - Translatable Strings:
        self.bank = {}
        self.bank['intro']      = [_("Frets on Fire X is a progression of MFH-mod,"),
                                   _("which was built on Alarian's mod,"),
                                   _("which was built on UltimateCoffee's Ultimate mod,"),
                                   _("which was built on RogueF's RF_mod 4.15,"),
                                   _("which was, of course, built on Frets on Fire 1.2.451,"),
                                   _("which was created by Unreal Voodoo")]
        self.bank['noOrder']    = [_("No particular order")]
        self.bank['accessOrder']= [_("In order of project commit access")]
        self.bank['coders']     = [_("Active Coders")]
        self.bank['otherCoding']= [_("Programming")]
        self.bank['graphics']   = [_("Graphic Design")]
        self.bank['3d']         = [_("3D Textures")]
        self.bank['logo']       = [_("FoFiX Logo Design")]
        self.bank['hollowmind'] = [_("Hollowmind Necks")]
        self.bank['themes']     = [_("Included Themes")]
        self.bank['shaders']    = [_("Shaders")]
        self.bank['sounds']     = [_("Sound Design")]
        self.bank['translators']= [_("Translators")]
        self.bank['honorary']   = [_("Honorary Credits")]
        self.bank['codeHonor']  = [_("Without whom this game would not exist")]
        self.bank['giveThanks'] = [_("Special Thanks to")]
        self.bank['community']  = [_("nwru and all of the community at fretsonfire.net")]
        self.bank['other']      = [_("Other Contributors:")]
        self.bank['tutorial']   = [_("Jurgen FoF tutorial inspired by adam02"),
                                   _("Drum test song tutorial by Heka"),
                                   _("Drum Rolls practice tutorial by venom426")]
        self.bank['disclaimer'] = [_("If you have contributed to this game and are not credited,"),
                                   _("please let us know what and when you contributed.")]
        self.bank['thanks']     = [_("Thank you for your contribution.")]
        self.bank['oversight']  = [_("Please keep in mind that it is not easy to trace down and"),
                                   _("credit every single person who contributed; if your name is"),
                                   _("not included, it was not meant to slight you."),
                                   _("It was an oversight.")]
        # evilynux - Theme strings
        self.bank['themeCreators'] = [_("%s theme credits:") % self.themename]
        self.bank['themeThanks']   = [_("%s theme specific thanks:") % self.themename]
        # Languages
        self.bank['french']        = [_("French")]
        self.bank['french90']      = [_("French (reform 1990)")]
        self.bank['german']        = [_("German")]
        self.bank['italian']       = [_("Italian")]
        self.bank['piglatin']      = [_("Pig Latin")]
        self.bank['portuguese-b']  = [_("Portuguese (Brazilian)")]
        self.bank['russian']       = [_("Russian")]
        self.bank['spanish']       = [_("Spanish")]
        self.bank['swedish']       = [_("Swedish")]

        self.videoLayer = False
        self.background = None

        vidSource = os.path.join(Version.dataPath(), 'themes', self.themename,
                                 'menu', 'credits.ogv')
        if os.path.isfile(vidSource):
            try:
                self.vidPlayer = VideoLayer(self.engine, vidSource, mute = True, loop = True)
            except (IOError, VideoPlayerError):
                log.error('Error loading credits video:')
            else:
                self.vidPlayer.play()
                self.engine.view.pushLayer(self.vidPlayer)
                self.videoLayer = True

        if not self.videoLayer and \
           not self.engine.loadImgDrawing(self, 'background', os.path.join('themes', self.themename, 'menu', 'credits.png')):
            self.background = None

        if not self.engine.loadImgDrawing(self, 'topLayer', os.path.join('themes', self.themename, 'menu', 'creditstop.png')):
            self.topLayer = None

        space = Text(nf, hs, c1, "center", " ")
        self.credits = [
          Picture(self.engine, "fofix_logo.png", .10),
          Text(nf, ns, c1, "center", "%s" % Version.version()), space]

        # evilynux: Main FoFiX credits (taken from CREDITS).
        self.parseText("CREDITS")
        self.credits.extend([space, space, space])
        # evilynux: Theme credits (taken from data/themes/<theme name>/CREDITS).
        self.parseText(os.path.join('data', 'themes', self.themename, 'CREDITS'))

        self.credits.extend( [
          space, space,
          Text(nf, ns, c1, "left",   _("Made with:")),
          Text(nf, ns, c2, "right",  "Python " + sys.version.split(' ')[0]),  #stump: the version that's actually in use
          Text(nf, bs, c2, "right",  "http://www.python.org"),
          space,
          Text(nf, ns, c2, "right",  "PyGame " + pygame.version.ver.replace('release', '')),  #stump: the version that's actually in use
          Text(nf, bs, c2, "right",  "http://www.pygame.org"),
          space,
          Text(nf, ns, c2, "right",  "PyOpenGL " + OpenGL.__version__), #evilynux: the version that's actually in use
          Text(nf, bs, c2, "right",  "http://pyopengl.sourceforge.net"),
          space,
          Text(nf, ns, c2, "right",  "Illusoft Collada module 0.3.159"),
          Text(nf, bs, c2, "right",  "http://colladablender.illusoft.com"),
          space,
          Text(nf, ns, c2, "right",  "MXM Python Midi Package 0.1.4"),
          Text(nf, bs, c2, "right",  "http://www.mxm.dk/products/public/pythonmidi"),
          space,
          space,
          Text(nf, bs, c1, "center", _("Source Code available under the GNU General Public License")),
          Text(nf, bs, c2, "center", "http://code.google.com/p/fofix"),
          space,
          space,
          Text(nf, bs, c1, "center", _("Copyright 2006, 2007 by Unreal Voodoo")),
          Text(nf, bs, c1, "center", _("Copyright 2008-2013 by Team FoFiX")),
          space,
          space
        ])

    # evilynux - Text parsing method. Provides some style functionalities.
    def parseText(self, filename):
        nf = self.engine.data.font
        ns = 0.002
        bs = 0.001
        hs = 0.003
        c1 = (1, 1, .5, 1)
        c2 = (1, .75, 0, 1)
        space = Text(nf, hs, c1, "center", " ")
        scale = 1

        path = filename
        if not hasattr(sys,"frozen"): #MFH - add ".." to path only if running from sources - not if running from EXE
            path = os.path.join("..", path)
        if not os.path.exists(path):
            return

        file = open(path)
        for line in file:
            line = line.strip("\n")
            if line.startswith("=====") or line.startswith("-----"):
                continue
            try:
                if line.startswith("!") and line.endswith("!"):
                    scale = float(line.strip("!"))
                    continue
            except ValueError:
                log.warn("CREDITS file does not parse properly")
            if line == "":
                self.credits.append(space)
            elif line.startswith("`") and line.endswith("`"):
                line = line.strip("`")
                if line.startswith("%") and line.endswith("%"):
                    line = line.strip("%")
                    try:
                        for text in self.bank[line]:
                            self.credits.append( Text(nf, bs*scale, c1, "left", "%s" % text) )
                    except KeyError:
                        self.credits.append( Text(nf, bs*scale, c1, "left", "%s" % line) )
                else:
                    self.credits.append( Text(nf, bs*scale, c1, "left", "%s" % line) )
            elif line.startswith("_") and line.endswith("_"):
                line = line.strip("_")
                if line.startswith("%") and line.endswith("%"):
                    line = line.strip("%")
                    try:
                        for text in self.bank[line]:
                            self.credits.append( Text(nf, ns*scale, c2, "center", "%s" % text) )
                    except KeyError:
                        self.credits.append( Text(nf, ns*scale, c2, "center", "%s" % line) )
                else:
                    self.credits.append( Text(nf, ns*scale, c2, "center", "%s" % line) )
            elif line.startswith("=") and line.endswith("="):
                line = line.strip("=")
                if line.startswith("%") and line.endswith("%"):
                    line = line.strip("%")
                    try:
                        for text in self.bank[line]:
                            self.credits.append( Text(nf, ns*scale, c1, "left", "%s" % text) )
                    except KeyError:
                        self.credits.append( Text(nf, ns*scale, c1, "left", "%s" % line) )
                else:
                    self.credits.append( Text(nf, ns*scale, c1, "left", "%s" % line) )
            else:
                if line.startswith("%") and line.endswith("%"):
                    line = line.strip("%")
                    try:
                        for text in self.bank[line]:
                            self.credits.append( Text(nf, ns*scale, c2, "right", "%s" % text) )
                    except KeyError:
                        self.credits.append( Text(nf, ns*scale, c2, "right", "%s" % line) )
                else:
                    self.credits.append( Text(nf, ns*scale, c2, "right", "%s" % line) )

    def shown(self):
        self.engine.input.addKeyListener(self)

    def hidden(self):
        self.engine.input.removeKeyListener(self)
        self.engine.view.pushLayer(self.engine.mainMenu)    #rchiav: use already-existing MainMenu instance

    def quit(self):
        if self.videoLayer:
            self.engine.view.popLayer(self.vidPlayer)
        self.engine.view.popLayer(self)

    def keyPressed(self, key, unicode):
        if self.engine.input.controls.getMapping(key) in (Player.menuYes + Player.menuNo) or key == pygame.K_RETURN or key == pygame.K_ESCAPE:
            self.quit()
        elif self.engine.input.controls.getMapping(key) in (Player.menuDown) or key == pygame.K_DOWN: #akedrou: so I was bored.
            if self.speedDiv > 1000.0:
                self.speedDiv -= 1000.0
                if self.speedDiv < 1000.0:
                    self.speedDiv = 1000.0
        elif self.engine.input.controls.getMapping(key) in (Player.menuUp) or key == pygame.K_UP:
            if self.speedDiv < 30000.0:
                self.speedDiv += 1000.0
                if self.speedDiv > 30000.0:
                    self.speedDiv = 30000.0
        elif self.engine.input.controls.getMapping(key) in (Player.key3s):
            self.speedDir *= -1
        elif self.engine.input.controls.getMapping(key) in (Player.key4s):
            if self.speedDir != 0:
                self.speedDir = 0
            else:
                self.speedDir = 1.0
        return True

    def run(self, ticks):
        self.time   += ticks / 50.0
        #self.offset -= ticks / 7500.0 # evilynux - corresponds to scroll speed
        #self.offset -= ticks / 15000.0 #MFH - slowin it down - # evilynux - corresponds to scroll speed
        self.offset -= (ticks / self.speedDiv) * self.speedDir #akedrou - some credits fun.

        # evilynux - approximating the end of the list from the (mostly used font size * lines)
        if self.offset < -( self.text_size * len(self.credits) ) or self.offset > 1.5:    #(MFH - adding 5% to estimated font height) undone: using larger scale for estimation.
            self.quit()
        if len(self.credits) == len(self.doneList): #akedrou - goofy workaround for string size glitch.
            self.quit()

    def render(self, visibility, topMost):
        v = 1.0 - ((1 - visibility) ** 2)

        # render the background
        w, h = self.engine.view.geometry[2:4]

        with self.engine.view.orthogonalProjection(normalize = True):
            if self.background:
                drawImage(self.background, scale = (1.0,-1.0), coord = (w/2,h/2), stretched = FULL_SCREEN)
            else:
                self.engine.fadeScreen(.4)
            self.doneList = []

            # render the scroller elements
            y = self.offset
            glTranslatef(-(1 - v), 0, 0)
            for element in self.credits:
                hE = element.getHeight()
                if y + hE > 0.0 and y < 1.0:
                    element.render(y)
                if y + hE < 0.0:
                    self.doneList.append(element)
                y += hE
                if y > 1.0:
                    break
            if self.topLayer:
                wFactor = 640.000/self.topLayer.width1()
                hPos = h - ((self.topLayer.height1() * wFactor)*.75)
                if hPos < h * .6:
                    hPos = h * .6
                drawImage(self.topLayer, scale = (wFactor,-wFactor), coord = (w/2,hPos))

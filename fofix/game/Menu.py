#####################################################################
# -*- coding: utf-8 -*-                                             #
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

import logging
import math
import os

from OpenGL.GL import *
import pygame

from fofix.core.Input import KeyListener
from fofix.core.Image import drawImage
from fofix.core.View import Layer
from fofix.core import Player
from fofix.core import Data
from fofix.core.constants import *


log = logging.getLogger(__name__)


class Choice:
    """ Choice constructor """

    def __init__(self, text, callback, name=None, values=None, valueIndex=0, append_submenu_char=True, tipText=None):
        """
        Initialise an item in the menu

        :param text: name of the item (ending with ' >' if it is a submenu)
        :type text: string
        :param callback: function to call when the item is chosen
        :param name: name of the submenu
        :type name: string
        :param values: (x, y) position
        :param valueIndex: the index of the first (current) selected value
        :type valueIndex: integer
        :param append_submenu_char:
        :type append_submenu_char: boolean
        :param tipText: the tip for the item
        :type tipText: string
        """
        self.text       = unicode(text)
        self.callback   = callback
        self.name       = name
        self.values     = values
        self.valueIndex = valueIndex
        self.append_submenu_char = append_submenu_char
        self.tipText    = tipText

        if self.text.endswith(" >"):
            self.text = text[:-2]
            self.isSubMenu = True
        else:
            self.isSubMenu = isinstance(self.callback, Menu) or isinstance(self.callback, list)

    def trigger(self, engine=None):
        """
        Trigger action

        :param engine: the engine
        """
        # select the action (submenu or callback)
        if engine and isinstance(self.callback, list):
            if self.values:
                nextMenu = Menu(engine, self.callback, name=self.name, pos=self.values, selectedIndex=self.valueIndex)
            else:
                nextMenu = Menu(engine, self.callback, name=self.name)
        elif engine and isinstance(self.callback, Menu):
            nextMenu = self.callback
        elif self.values:
            nextMenu = self.callback(self.values[self.valueIndex])
        else:
            nextMenu = self.callback()

        # display the new menu if necessary
        if isinstance(nextMenu, Menu):
            engine.view.pushLayer(nextMenu)

    def selectNextValue(self):
        """ Select the next value """
        if self.values:
            self.valueIndex = (self.valueIndex + 1) % len(self.values)
            self.trigger()

    def selectPreviousValue(self):
        """ Select the previous value """
        if self.values:
            self.valueIndex = (self.valueIndex - 1) % len(self.values)
            self.trigger()

    def getText(self, selected):
        if not self.values:
            if self.isSubMenu and self.append_submenu_char:
                return "%s >" % self.text
            return self.text
        if selected:
            return "%s: %s%s%s" % (self.text, Data.LEFT, self.values[self.valueIndex], Data.RIGHT)
        else:
            return "%s: %s" % (self.text, self.values[self.valueIndex])


class Menu(Layer, KeyListener):
    """ Menu constructor """

    def __init__(self, engine, choices, name=None, onClose=None, onCancel=None, pos=(.2, .31), viewSize=6, fadeScreen=False, font="font", mainMenu=None, textColor=None, selectedColor=None, append_submenu_char=True, selectedIndex=None, showTips=True, selectedBox=False):
        """
        Initialise the menu

        :param engine: the engine
        :param choices: choices for the menu
        :type choices: list of tuples (item name, callback, tiptext)
        :param name: the name of the menu
        :type name: string
        :param onClose: function to call when closing the menu
        :param onCancel: function to call when cancelling
        :param pos: (x, y) position
        :type pos: tuple of floats (x, y)
        :param viewSize:
        :type viewSize: integer
        :param fadeScreen: fade the screen
        :type fadeScreen: boolean
        :param font: the font for the text
        :param mainMenu:
        :param textColor: the color of the text
        :param selectedColor:
        :param append_submenu_char:
        :type append_submenu_char: boolean
        :param selectedIndex: the index of the first (current) selected value
        :type selectedIndex: integer
        :param showTips: display tips
        :type showTips: boolean
        :param selectedBox:
        """
        self.engine = engine

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            log.debug("Menu class init (Menu.py)...")

        # Get theme
        self.themename = self.engine.data.themeLabel
        self.theme = self.engine.data.theme

        self.choices = []
        self.currentIndex = selectedIndex if selectedIndex else 0
        self.time         = 0
        self.onClose      = onClose
        self.onCancel     = onCancel
        self.viewOffset   = 0
        self.name = name  # for graphical support
        self.mainMenu = False
        self.graphicMenu = False
        self.useSelectedBox = selectedBox
        self.useGraphics = self.engine.config.get("game", "use_graphical_submenu")
        self.gfxText = None

        self.scrolling = 0
        self.delay     = 0
        self.rate      = 0
        self.scroller  = [0, self.scrollUp, self.scrollDown, self.scrollLeft, self.scrollRight]

        self.textColor = textColor
        self.selectedColor = selectedColor
        self.tipColor = self.engine.theme.menuTipTextColor

        self.drumNav = self.engine.config.get("game", "drum_navigation")

        if self.name and self.useGraphics > 0:
            try:
                # try to load the background menu image
                if self.engine.loadImgDrawing(self, "menuBackground", os.path.join("themes", self.themename, "menu", "%s.png" % self.name)):
                    if self.menuBackground.height1() == 1:
                        raise KeyError
                else:
                    raise KeyError

                # try to load the text menu image
                self.gfxText = "%stext%d" % (self.name, len(choices))
                if not self.engine.loadImgDrawing(self, "menuText", os.path.join("themes", self.themename, "menu", "%s.png" % self.gfxText)):
                    raise KeyError

                self.graphicMenu = True
                self.menux = self.engine.theme.submenuX[self.gfxText]
                self.menuy = self.engine.theme.submenuY[self.gfxText]
                self.menuScale = self.engine.theme.submenuScale[self.gfxText]
                self.vSpace = self.engine.theme.submenuVSpace[self.gfxText]
                if str(self.menux) != "None" and str(self.menuy) != "None":
                    self.menux = float(self.menux)
                    self.menuy = float(self.menuy)
                else:
                    self.menux = .4
                    self.menuy = .4
                if str(self.menuScale) != "None":
                    self.menuScale = float(self.menuScale)
                else:
                    self.menuScale = .5
                if str(self.vSpace) != "None":
                    self.vSpace = float(self.vSpace)
                else:
                    self.vSpace = .08
                log.debug("Graphic menu enabled for submenu: %s" % self.name)
            except KeyError:
                log.warn("Your theme does not appear to properly support the %s graphical submenu. Check to be sure you have the latest version of your theme." % self.name)
                self.menuBackground = None
                self.menuText = None

        # default position, not called with a special one - this is a submenu
        if pos == (.2, .66 - .35):
            self.sub_menu_x = self.engine.theme.sub_menu_xVar
            self.sub_menu_y = self.engine.theme.sub_menu_yVar

            if engine.data.theme == 0:
                if self.sub_menu_x is None:
                    self.sub_menu_x = .44
                if self.sub_menu_y is None:
                    self.sub_menu_y = .14
            elif engine.data.theme == 1:
                if self.sub_menu_x is None:
                    self.sub_menu_x = .38
                if self.sub_menu_y is None:
                    self.sub_menu_y = .15
            elif engine.data.theme == 2:
                if self.sub_menu_x is None:
                    self.sub_menu_x = .25
                if self.sub_menu_y is None:
                    self.sub_menu_y = .14

            pos = (self.sub_menu_x, self.sub_menu_y)

        # default viewsize
        if viewSize == 6:
            # 8bit
            if self.theme in [0, 1, 2]:
                viewSize = 10

        self.pos          = pos
        self.viewSize     = viewSize
        self.fadeScreen   = fadeScreen
        self.font         = font
        if self.font == "font":
            self.font = self.engine.data.font
        self.tipFont = self.engine.theme.menuTipTextFont
        if self.tipFont == "None":
            self.tipFont = self.font
        else:
            self.tipFont = self.engine.data.fontDict[self.tipFont]
        self.active = False
        self.mainMenu = mainMenu

        self.showTips = showTips
        if self.showTips:
            self.showTips = self.engine.theme.menuTipTextDisplay
        self.tipDelay = 700
        self.tipTimerEnabled = False
        self.tipScroll = 0
        self.tipScrollB = None
        self.tipScrollSpace = self.engine.theme.menuTipTextScrollSpace
        self.tipScale = self.engine.theme.menuTipTextScale
        self.tipDir = 0
        self.tipSize = 0
        self.tipY = self.engine.theme.menuTipTextY
        self.tipScrollMode = self.engine.theme.menuTipTextScrollMode  # 0 for constant scroll; 1 for back and forth

        # get the list of items
        for c in choices:
            try:
                text, callback = c
                if isinstance(text, tuple):
                    if len(text) == 2:
                        # a submenu's name
                        c = Choice(text[0], callback, name=text[1], append_submenu_char=append_submenu_char)
                    else:
                        # Dialogs menus - FileChooser, NeckChooser, ItemChooser - this last to be changed soon
                        c = Choice(text[0], callback, values=text[2], valueIndex=text[1], append_submenu_char=append_submenu_char)
                else:
                    c = Choice(text, callback, append_submenu_char=append_submenu_char)
            except ValueError:
                text, callback, tipText = c
                if isinstance(text, tuple):
                    if len(text) == 2:
                        # a submenu's name
                        c = Choice(text[0], callback, name=text[1], append_submenu_char=append_submenu_char, tipText=tipText)
                    else:
                        # Dialogs menus - FileChooser, NeckChooser, ItemChooser - this last to be changed soon
                        c = Choice(text[0], callback, values=text[2], valueIndex=text[1], append_submenu_char=append_submenu_char, tipText=tipText)
                else:
                    c = Choice(text, callback, append_submenu_char=append_submenu_char, tipText=tipText)
            except TypeError:
                pass
            self.choices.append(c)

        self.setTipScroll()

    def selectItem(self, index):
        """
        Select an item

        :param index: the index of the selected item
        :type index: integer
        """
        self.currentIndex = index

    def shown(self):
        self.engine.input.addKeyListener(self)

    def hidden(self):
        self.engine.input.removeKeyListener(self)
        if self.onClose:
            self.onClose()

    def updateSelection(self):
        """ Update the selection of an item """
        self.setTipScroll()
        if self.currentIndex > self.viewOffset + self.viewSize - 1:
            self.viewOffset = self.currentIndex - self.viewSize + 1
        if self.currentIndex < self.viewOffset:
            self.viewOffset = self.currentIndex

    # XXX: unicode param is deprecated
    def keyPressed(self, key, unicode):
        """
        Manage action when a key is pressed (drum navigation supported)

        :param key: the key pressed
        :param unicode: deprecated (not used)
        :return: always True
        """
        choice = self.choices[self.currentIndex]
        c = self.engine.input.controls.getMapping(key)
        if c in Player.menuYes or key == pygame.K_RETURN:
            self.scrolling = 0
            choice.trigger(self.engine)
            self.engine.data.acceptSound.play()
        elif c in Player.menuNo or key == pygame.K_ESCAPE:
            if self.onCancel:
                self.onCancel()
            self.engine.view.popLayer(self)
            self.engine.input.removeKeyListener(self)
            self.engine.data.cancelSound.play()
        elif c in Player.menuDown or key == pygame.K_DOWN:
            self.scrolling = 2
            self.delay = self.engine.scrollDelay
            self.scrollDown()
        elif c in Player.menuUp or key == pygame.K_UP:
            self.scrolling = 1
            self.delay = self.engine.scrollDelay
            self.scrollUp()
        elif c in Player.menuNext or key == pygame.K_RIGHT:
            self.scrolling = 4
            self.delay = self.engine.scrollDelay
            self.scrollRight()
        elif c in Player.menuPrev or key == pygame.K_LEFT:
            self.scrolling = 3
            self.delay = self.engine.scrollDelay
            self.scrollLeft()
        return True

    def scrollDown(self):
        """ Scroll down """
        self.engine.data.selectSound.play()
        self.currentIndex = (self.currentIndex + 1) % len(self.choices)
        self.updateSelection()

    def scrollUp(self):
        """ Scroll up """
        self.engine.data.selectSound.play()
        self.currentIndex = (self.currentIndex - 1) % len(self.choices)
        self.updateSelection()

    def scrollLeft(self):
        """ Scroll left """
        self.choices[self.currentIndex].selectPreviousValue()

    def scrollRight(self):
        """ Scroll right """
        self.choices[self.currentIndex].selectNextValue()

    def keyReleased(self, key):
        self.scrolling = 0

    def run(self, ticks):
        self.time += ticks / 50.0
        if self.scrolling > 0:
            self.delay -= ticks
            self.rate += ticks
            if self.delay <= 0 and self.rate >= self.engine.scrollRate:
                self.rate = 0
                self.scroller[self.scrolling]()
        if self.tipTimerEnabled:
            if self.tipDelay > 0:
                self.tipDelay -= ticks
                if self.tipDelay <= 0:
                    self.tipDelay = 0
                    self.tipDir = (self.tipDir+1)&1
            elif self.tipDir == 1 and self.tipScrollMode == 1:
                self.tipScroll -= ticks / 8000.0
                if self.tipScroll < -(self.tipSize - .98):
                    self.tipScroll = -(self.tipSize - .98)
                    self.tipDelay = 900
            elif self.tipDir == 0 and self.tipScrollMode == 1:
                self.tipScroll += ticks / 8000.0
                if self.tipScroll > .02:
                    self.tipScroll = .02
                    self.tipDelay = 900
            elif self.tipScrollMode == 0:
                self.tipScroll  -= ticks / 8000.0
                self.tipScrollB -= ticks / 8000.0
                if self.tipScroll < -(self.tipSize):
                    self.tipScroll = self.tipScrollB + self.tipSize + self.tipScrollSpace
                if self.tipScrollB < -(self.tipSize):
                    self.tipScrollB = self.tipScroll + self.tipSize + self.tipScrollSpace

    def renderTriangle(self, up=(0, 1), s=.2):
        left = (-up[1], up[0])
        glBegin(GL_TRIANGLES)
        glVertex2f(up[0] * s, up[1] * s)
        glVertex2f((-up[0] + left[0]) * s, (-up[1] + left[1]) * s)
        glVertex2f((-up[0] - left[0]) * s, (-up[1] - left[1]) * s)
        glEnd()

    def setTipScroll(self):
        if self.choices[self.currentIndex].tipText is None:
            return
        tipW, tipH = self.tipFont.getStringSize(self.choices[self.currentIndex].tipText, self.tipScale)
        if tipW > .99:
            self.tipSize = tipW
            self.tipDelay = 1000
            self.tipTimerEnabled = True
            self.tipScroll = 0.02
            self.tipScrollB = 0.02 + self.tipSize + self.tipScrollSpace
            self.tipWait = False
            self.tipDir = 0
        else:
            self.tipScroll = .5 - tipW / 2
            self.tipScrollB = None
            self.tipTimerEnabled = False
            self.tipDir = 0
            self.tipSize = tipW

    def render(self, visibility, topMost):
        # display version in any menu
        if not visibility:
            self.active = False
            return

        self.active = True
        if self.graphicMenu and self.menuBackground:
            self.engine.graphicMenuShown = True
        else:
            self.engine.graphicMenuShown = False

        with self.engine.view.orthogonalProjection(normalize=True):
            v = (1 - visibility) ** 2

            # Default to this font if none was specified
            font = self.font
            tipFont = self.tipFont

            # Fade
            if self.fadeScreen:
                self.engine.fadeScreen(v)

            wS, hS = self.engine.view.geometry[2:4]

            if self.graphicMenu and self.menuBackground:
                # better menu scaling
                drawImage(self.menuBackground, scale=(1.0, -1.0), coord=(wS/2, hS/2), stretched=FULL_SCREEN)
            else:
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glEnable(GL_COLOR_MATERIAL)

            n = len(self.choices)
            x, y = self.pos

            for i, choice in enumerate(self.choices[self.viewOffset:self.viewOffset + self.viewSize]):
                if self.graphicMenu:
                    if self.currentIndex == i:
                        xpos = (.5, 1)
                    else:
                        xpos = (0, .5)
                    ypos = float(i + self.viewOffset)
                    drawImage(self.menuText, scale=(.5*self.menuScale, (-1.0/n*self.menuScale)),
                              coord=(wS*self.menux, (hS*self.menuy)-(hS*self.vSpace)*i),
                              rect=(xpos[0], xpos[1], ypos/n, (ypos+1.0)/n), stretched=KEEP_ASPECT | FIT_WIDTH)
                else:
                    text = choice.getText(i + self.viewOffset == self.currentIndex)
                    glPushMatrix()
                    glRotate(v * 45, 0, 0, 1)

                    scale = self.engine.theme.settingsmenuScale

                    w, h = font.getStringSize(" ", scale=scale)

                    # Draw arrows if scrolling is needed to see all items
                    if i == 0 and self.viewOffset > 0:
                        self.engine.theme.setBaseColor((1 - v) * max(.1, 1 - (1.0 / self.viewOffset) / 3))
                        glPushMatrix()
                        glTranslatef(x - v / 4 - w * 2, y + h / 2, 0)
                        self.renderTriangle(up=(0, -1), s=.015)
                        glPopMatrix()
                    elif i == self.viewSize - 1 and self.viewOffset + self.viewSize < n:
                        self.engine.theme.setBaseColor((1 - v) * max(.1, 1 - (1.0 / (n - self.viewOffset - self.viewSize)) / 3))
                        glPushMatrix()
                        glTranslatef(x - v / 4 - w * 2, y + h / 2, 0)
                        self.renderTriangle(up=(0, 1), s=.015)
                        glPopMatrix()

                    if i + self.viewOffset == self.currentIndex:
                        if choice.tipText and self.showTips:
                            if self.tipColor:
                                c1, c2, c3 = self.tipColor
                                glColor3f(c1, c2, c3)
                            elif self.textColor:
                                c1, c2, c3 = self.textColor
                                glColor3f(c1, c2, c3)
                            else:
                                self.engine.theme.setBaseColor(1 - v)
                            tipScale = self.tipScale
                            if self.tipScroll > -(self.tipSize) and self.tipScroll < 1:
                                tipFont.render(choice.tipText, (self.tipScroll, self.tipY), scale=tipScale)
                            if self.tipScrollMode == 0:
                                if self.tipScrollB > -(self.tipSize) and self.tipScrollB < 1:
                                    tipFont.render(choice.tipText, (self.tipScrollB, self.tipY), scale=tipScale)
                        a = (math.sin(self.time) * .15 + .75) * (1 - v * 2)
                        self.engine.theme.setSelectedColor(a)
                        a *= -.005
                        glTranslatef(a, a, a)
                    else:
                        self.engine.theme.setBaseColor(1 - v)

                    # settable color through Menu constructor
                    if i + self.viewOffset == self.currentIndex and self.selectedColor:
                        c1, c2, c3 = self.selectedColor
                        glColor3f(c1, c2, c3)
                    elif self.textColor:
                        c1, c2, c3 = self.textColor
                        glColor3f(c1, c2, c3)

                    # now to catch " >" main menu options and blank them
                    if text == " >":
                        text = ""

                    if self.engine.data.submenuSelectFound and len(text) > 0 and not self.mainMenu and self.useSelectedBox:
                        Tw, Th = font.getStringSize(text, scale)
                        boxXOffset = (x + (Tw / 2)) * wS
                        boxYOffset = (1.0 - (y * 4.0 / 3.0) - (Th * 1.2 / 2)) * hS
                        drawImage(self.engine.data.submenuSelect,
                                  scale=(tempWScale, tempHScale),  #FIXME
                                  coord=(boxXOffset, boxYOffset))

                    font.render(text, (x - v / 4, y), scale=scale)

                    v *= 2
                    if self.theme == 1 and self.font == self.engine.data.pauseFont:
                        # Ugly workaround for Gh3
                        y += h * .70  # Changed Pause menu spacing back to .70 from .65 for now.
                    else:
                        y += h
                    glPopMatrix()

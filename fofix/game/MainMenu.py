#!/usr/bin/python
# -*- coding: utf-8 -*-

#####################################################################
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
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

import logging
import os
import random
import warnings

from fretwork.audio import Music

from fofix.core import Config
from fofix.core import Settings
from fofix.core.Image import drawImage
from fofix.core.Language import _
from fofix.core.Shader import shaders
from fofix.core.View import BackgroundLayer
from fofix.core.constants import *
from fofix.game import Dialogs
from fofix.game.Lobby import Lobby
from fofix.game.Menu import Menu


log = logging.getLogger(__name__)


class MainMenu(BackgroundLayer):
    """ The main menu """

    def __init__(self, engine):
        """Initialise the main menu

        :param engine: the engine
        """
        log.debug("MainMenu class init (MainMenu.py)...")

        self.engine = engine

        self.time       = 0.0
        self.nextLayer  = None
        self.visibility = 0.0
        self.active     = False

        self.showStartupMessages = False

        self.gfxVersionTag = Config.get("game", "gfx_version_tag")

        # Neck
        self.chosenNeck = Config.get("game", "default_neck")
        exists = 0
        if engine.loadImgDrawing(self, "ok", os.path.join("necks", self.chosenNeck + ".png")):
            exists = 1
        elif engine.loadImgDrawing(self, "ok", os.path.join("necks", "Neck_" + self.chosenNeck + ".png")):
            exists = 1

        ## check for the default Neck_1
        if exists == 0:
            if engine.loadImgDrawing(self, "ok", os.path.join("necks", "Neck_1.png")):
                Config.set("game", "default_neck", "1")
                log.warning("Default chosen neck not valid; fallback Neck_1.png forced.")
                exists = 1

        ## check for defaultneck
        if exists == 0:
            if engine.loadImgDrawing(self, "ok", os.path.join("necks", "defaultneck.png")):
                log.warning("Default chosen neck not valid; fallback defaultneck.png forced.")
                Config.set("game", "default_neck", "defaultneck")
                exists = 1
            else:
                log.error("Default chosen neck not valid; fallbacks Neck_1.png and defaultneck.png also not valid!")

        # Get theme
        self.theme       = self.engine.data.theme
        self.themeCoOp   = self.engine.data.themeCoOp
        self.themename   = self.engine.data.themeLabel
        self.useSoloMenu = self.engine.theme.use_solo_submenu

        allowMic = True

        self.menux = self.engine.theme.menuPos[0]
        self.menuy = self.engine.theme.menuPos[1]

        self.rbmenu = self.engine.theme.menuRB

        self.main_menu_scale = self.engine.theme.main_menu_scaleVar
        self.main_menu_vspacing = self.engine.theme.main_menu_vspacingVar

        # Background
        if not self.engine.loadImgDrawing(self, "background", os.path.join("themes", self.themename, "menu", "mainbg.png")):
            self.background = None
        self.engine.loadImgDrawing(self, "BGText", os.path.join("themes", self.themename, "menu", "maintext.png"))
        self.engine.loadImgDrawing(self, "optionsBG", os.path.join("themes", self.themename, "menu", "optionsbg.png"))
        self.engine.loadImgDrawing(self, "optionsPanel", os.path.join("themes", self.themename, "menu", "optionspanel.png"))

        # Version tag
        if self.gfxVersionTag or self.engine.theme.versiontag:
            if not self.engine.loadImgDrawing(self, "version", os.path.join("themes", self.themename, "menu", "versiontag.png")):
                # falls back on default versiontag.png in 'data' folder
                if not self.engine.loadImgDrawing(self, "version", "versiontag.png"):
                    self.version = None
        else:
            self.version = None

        # Main menu music
        ## get all muics: menu.ogg and menuXX.ogg (any filename with "menu" as the first 4 letters)
        self.files = None
        filepath = self.engine.getPath(os.path.join("themes", self.themename, "sounds"))
        if os.path.isdir(filepath):
            self.files = []
            allfiles = os.listdir(filepath)
            for name in allfiles:
                if os.path.splitext(name)[1] == ".ogg":
                    if name.find("menu") > -1:
                        self.files.append(name)

        ## get a random music
        if self.files:
            i = random.randint(0, len(self.files)-1)
            filename = self.files[i]
            sound = os.path.join("themes", self.themename, "sounds", filename)
            self.menumusic = True
            engine.menuMusic = True

            self.song = Music(self.engine.resource.fileName(sound))
            self.song.setVolume(self.engine.config.get("audio", "menu_volume"))
            self.song.play(0)  # no loop
        else:
            self.menumusic = False

        # Items
        self.opt_text_color     = self.engine.theme.opt_text_colorVar
        self.opt_selected_color = self.engine.theme.opt_selected_colorVar

        trainingMenu = [
            (_("Tutorials"), self.showTutorial),
            (_("Practice"), lambda: self.newLocalGame(mode1p=1)),
        ]

        self.opt_bkg_size = [float(i) for i in self.engine.theme.opt_bkg_size]
        self.opt_text_color = self.engine.theme.opt_text_colorVar
        self.opt_selected_color = self.engine.theme.opt_selected_colorVar

        if self.BGText:
            strCareer = ""
            strQuickplay = ""
            strSolo = ""
            strMultiplayer = ""
            strTraining = ""
            strSettings = ""
            strQuit = ""
        else:
            strCareer = _("Career")
            strQuickplay = _("Quickplay")
            strSolo = _("Solo")
            strMultiplayer = _("Multiplayer")
            strTraining = _("Training")
            strSettings = _("Settings")
            strQuit = _("Quit")

        multPlayerMenu = [
            (_("Face-Off"),     lambda: self.newLocalGame(players=2,           maxplayers=4)),
            (_("Pro Face-Off"), lambda: self.newLocalGame(players=2, mode2p=1, maxplayers=4)),
            (_("FoFiX Co-Op"),  lambda: self.newLocalGame(players=2, mode2p=3, maxplayers=4, allowMic=allowMic)),
            (_("RB Co-Op"),     lambda: self.newLocalGame(players=2, mode2p=4, maxplayers=4, allowMic=allowMic)),
        ]

        if not self.useSoloMenu:
            mainMenu = [
                (strCareer, lambda: self.newLocalGame(mode1p=2, allowMic=allowMic)),
                (strQuickplay, lambda: self.newLocalGame(allowMic=allowMic)),
                ((strMultiplayer, "multiplayer"), multPlayerMenu),
                ((strTraining, "training"), trainingMenu),
                ((strSettings, "settings"), self.settingsMenu),
                (strQuit, self.quit),
            ]
        else:
            soloMenu = [
                (_("Solo Tour"), lambda: self.newLocalGame(mode1p=2, allowMic=allowMic)),
                (_("Quickplay"), lambda: self.newLocalGame(allowMic=allowMic)),
            ]

            mainMenu = [
                ((strSolo, "solo"), soloMenu),
                ((strMultiplayer, "multiplayer"), multPlayerMenu),
                ((strTraining, "training"), trainingMenu),
                ((strSettings, "settings"), self.settingsMenu),
                (strQuit, self.quit),
            ]

        w, h, = self.engine.view.geometry[2:4]

        self.menu = Menu(self.engine, mainMenu, onClose=lambda: self.engine.view.popLayer(self), pos=(self.menux, .75-(.75*self.menuy)))

        engine.mainMenu = self  # Points engine.mainMenu to the one and only MainMenu object instance

        # whether the main menu has come into view at least once
        self.shownOnce = False

    def settingsMenu(self):
        """
        Callback to launch the settings menu

        :return: the settings menu objet
        """
        if self.engine.advSettings:
            self.settingsMenuObject = Settings.SettingsMenu(self.engine)
        else:
            self.settingsMenuObject = Settings.BasicSettingsMenu(self.engine)
        return self.settingsMenuObject

    def shown(self):
        self.engine.view.pushLayer(self.menu)
        shaders.checkIfEnabled()

    def runMusic(self):
        """ Run a random theme music in background """
        if self.menumusic and not self.song.isPlaying():
            # re-randomize
            if self.files:
                i = random.randint(0, len(self.files)-1)
                filename = self.files[i]
                sound = os.path.join("themes", self.themename, "sounds", filename)
                self.menumusic = True
                self.engine.menuMusic = True

                self.song = Music(self.engine.resource.fileName(sound))
                self.song.setVolume(self.engine.config.get("audio", "menu_volume"))
                self.song.play(0)
            else:
                self.menumusic = False
                self.engine.menuMusic = False

    def setMenuVolume(self):
        """ Set the volume of the menu song """
        if self.menumusic and self.song.isPlaying():
            self.song.setVolume(self.engine.config.get("audio", "menu_volume"))

    def cutMusic(self):
        """ Fade out the volume of the song before stopping """
        if self.menumusic:
            if self.song and not self.engine.menuMusic:
                self.song.fadeout(1400)

    def hidden(self):
        self.engine.view.popLayer(self.menu)
        self.cutMusic()
        if self.nextLayer:
            self.engine.view.pushLayer(self.nextLayer())
            self.nextLayer = None
        else:
            self.engine.quit()

    def quit(self):
        self.engine.view.popLayer(self.menu)

    def launchLayer(self, layerFunc):
        if not self.nextLayer:
            self.nextLayer = layerFunc
            self.engine.view.popAllLayers()

    def showTutorial(self):
        """ Callback to show the tutorial menu """
        # Make sure tutorial exists before launching
        tutorialpath = self.engine.tutorialFolder
        if not os.path.isdir(self.engine.resource.fileName(tutorialpath)):
            log.info("No folder found: %s" % tutorialpath)
            Dialogs.showMessage(self.engine, _("No tutorials found!"))
            return

        self.engine.startWorld(1, None, 0, 0, tutorial=True)

        self.launchLayer(lambda: Lobby(self.engine))

    def newSinglePlayerGame(self):
        """ Deprecated: start the game in 1p quickplay mode (to test a song) """
        warnings.warn("fofix.game.MainMenu.newSinglePlayerGame is not used anymore.", PendingDeprecationWarning)
        self.newLocalGame()

    def newLocalGame(self, players=1, mode1p=0, mode2p=0, maxplayers=None, allowGuitar=True, allowDrum=True, allowMic=False): #mode1p=0(quickplay),1(practice),2(career) / mode2p=0(faceoff),1(profaceoff)
        """
        Callback to start the game

        :param players: number of players (default: 1)
        :param mode1p: game mode 1p (default: quickplay, practice, career)
        :param mode2p: game mode 2p (default: Face-Off, Pro FO, Co-Op, RB Co-Op)
        :param maxplayers: max number of players (default: None)
        :param allowGuitar: if a guitar is allowed or not (default: True)
        :param allowDrum: if a drum is allowed or not (default: True)
        :param allowMic: if a mic is allowed or not (default: False)
        """
        self.engine.startWorld(players, maxplayers, mode1p, mode2p, allowGuitar, allowDrum, allowMic)
        self.launchLayer(lambda: Lobby(self.engine))

    def restartGame(self):
        """ Restart the game: go to the main menu again """
        splash = Dialogs.showLoadingSplashScreen(self.engine, "")
        self.engine.view.pushLayer(Lobby(self.engine))
        Dialogs.hideLoadingSplashScreen(self.engine, splash)

    def showMessages(self):
        """ Show a message at start up """
        msg = self.engine.startupMessages.pop()
        self.showStartupMessages = False
        Dialogs.showMessage(self.engine, msg)

    def run(self, ticks):
        self.time += ticks / 50.0
        if self.showStartupMessages:
            self.showMessages()
        if len(self.engine.startupMessages) > 0:
            self.showStartupMessages = True

        if (not self.engine.world) or (not self.engine.world.scene):
            self.runMusic()

    def render(self, visibility, topMost):
        self.engine.view.setViewport(1, 0)
        self.visibility = visibility
        if self.rbmenu:
            v = 1.0 - ((1 - visibility) ** 2)
        else:
            v = 1
        if v == 1:
            self.engine.view.transitionTime = 1

        if self.menu.active and not self.active:
            self.active = True

        w, h, = self.engine.view.geometry[2:4]

        if self.active:
            if self.engine.view.topLayer() is not None:
                if self.optionsBG:
                    drawImage(self.optionsBG, (self.opt_bkg_size[2], -self.opt_bkg_size[3]), (w*self.opt_bkg_size[0], h*self.opt_bkg_size[1]), stretched=FULL_SCREEN)
                if self.optionsPanel:
                    drawImage(self.optionsPanel, (1.0, -1.0), (w/2, h/2), stretched=FULL_SCREEN)
            else:
                drawImage(self.engine.data.loadingImage, (1.0, -1.0), (w/2, h/2), stretched=FULL_SCREEN)

        if self.menu.active:
            if self.background is not None:
                # auto-scaling
                drawImage(self.background, (1.0, -1.0), (w/2, h/2), stretched=FULL_SCREEN)

            if self.BGText:
                numOfChoices = len(self.menu.choices)
                for i in range(numOfChoices):
                    # Item selected
                    if self.menu.currentIndex == i:
                        xpos = (.5, 1)
                    # Item unselected
                    else:
                        xpos = (0, .5)
                    # which item?
                    ypos = (1/float(numOfChoices) * i, 1/float(numOfChoices) * (i + 1))

                    textcoord = (w*self.menux, h*self.menuy-(h*self.main_menu_vspacing)*i)
                    sFactor = self.main_menu_scale
                    wFactor = xpos[1] - xpos[0]
                    hFactor = ypos[1] - ypos[0]
                    drawImage(self.BGText,
                        scale=(wFactor*sFactor, -hFactor*sFactor),
                        coord=textcoord,
                        rect=(xpos[0], xpos[1], ypos[0], ypos[1]), stretched=KEEP_ASPECT | FIT_WIDTH)

        # added version tag to main menu
        if self.version is not None:
            # Added theme settings to control X+Y positions of versiontag.
            wfactor = (w * self.engine.theme.versiontagScale) / self.version.width1()
            drawImage(self.version, (wfactor, -wfactor), (w*self.engine.theme.versiontagposX, h*self.engine.theme.versiontagposY))

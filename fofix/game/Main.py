#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#####################################################################
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 evilynux <evilynux@gmail.com>                  #
#               2012 FoFiX Team                                     #
#               2009 akedrou                                        #
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

'''
Main game object.
'''
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os

import pygame

from fretwork import log

from fofix.core import Version
from fofix.core import VFS

from fofix.core.VideoPlayer import VideoLayer, VideoPlayerError
from fofix.core.GameEngine import GameEngine
from fofix.game.MainMenu import MainMenu
from fofix.core.Language import _
from fofix.core import Config


class Main(object):
    def __init__(self, a):
        self.args = a

        self.playing = self.args['song']
        self.configFile = self.args['config']
        self.fullscreen = self.args['fullscreen']
        self.resolution = self.args['resolution']
        self.theme = self.args['theme']
        self.diff = self.args['diff']
        self.part = self.args['part']
        self.mode = self.args['mode']
        self.players = self.args['players']

        self.config = self.load_config(self.configFile)

        # Lysdestic - Allow support for manipulating fullscreen via CLI
        if self.fullscreen is not None:
            Config.set("video", "fullscreen", self.fullscreen)

        # Lysdestic - Change resolution from CLI
        if self.resolution is not None:
            Config.set("video", "resolution", self.resolution)

        # Lysdestic - Alter theme from CLI
        if self.theme is not None:
            Config.set("coffee", "themename", self.theme)

        self.engine = GameEngine(self.config)

        self.init_oneshot()

        self.videoLayer = False
        self.restartRequested = False

    @staticmethod
    def load_config(configPath):
        ''' Load the configuration file. '''
        if configPath is not None:
            if configPath.lower() == "reset":

                # Get os specific location of config file, and remove it.
                fileName = os.path.join(VFS.getWritableResourcePath(), Version.PROGRAM_UNIXSTYLE_NAME + ".ini")
                os.remove(fileName)

                # Recreate it
                config = Config.load(Version.PROGRAM_UNIXSTYLE_NAME + ".ini", setAsDefault=True)

            else:
                # Load specified config file
                config = Config.load(configPath, setAsDefault=True)
        else:
            # Use default configuration file
            config = Config.load(Version.PROGRAM_UNIXSTYLE_NAME + ".ini", setAsDefault=True)

        return config

    def init_oneshot(self):
        ''' Determine if oneshot mode is valid. '''
        # I think this code can be moved elsewhere...
        self.engine.cmdPlay = 0

        # Check for a valid invocation of one-shot mode.
        if self.playing is not None:
            log.debug('Validating song directory for one-shot mode.')

            library = Config.get("setlist","base_library")
            basefolder = os.path.join(Version.dataPath(),library,"songs",self.playing)

            if not os.path.exists(os.path.join(basefolder, "song.ini")):

                if not (os.path.exists(os.path.join(basefolder, "notes.mid")) or
                        os.path.exists(os.path.join(basefolder, "notes-unedited.mid"))):

                    if not (os.path.exists(os.path.join(basefolder, "song.ogg")) or
                            os.path.exists(os.path.join(basefolder, "guitar.ogg"))):

                        log.warn("Song directory provided ('%s') is not a valid song directory. Starting up FoFiX in standard mode." % self.playing)
                        self.engine.startupMessages.append(_("Song directory provided ('%s') is not a valid song directory. Starting up FoFiX in standard mode.") % self.playing)
                        return

            # Set up one-shot mode
            log.debug('Entering one-shot mode.')
            Config.set("setlist", "selected_song", self.playing)

            self.engine.cmdPlay = 1

            if self.diff is not None:
                self.engine.cmdDiff = int(self.diff)
            if self.part is not None:
                self.engine.cmdPart = int(self.part)

            if self.players == 1:
                self.engine.cmdMode = self.players, self.mode, 0
            else:
                self.engine.cmdMode = self.players, 0, self.mode

    def restart(self):
        log.notice("Restarting.")
        self.engine.audio.close()
        self.restartRequested = True

    def run(self):

        # Perhapse this could be implemented in a better way...
        # Play the intro video if it is present, we have the capability, and
        # we are not in one-shot mode.
        if not self.engine.cmdPlay:
            themename = Config.get("coffee", "themename")
            vidSource = os.path.join(Version.dataPath(), 'themes', themename, 'menu', 'intro.ogv')
            if os.path.isfile(vidSource):
                try:
                    vidPlayer = VideoLayer(self.engine, vidSource, cancellable=True)
                except (IOError, VideoPlayerError):
                    log.error("Error loading intro video:")
                else:
                    vidPlayer.play()
                    self.engine.view.pushLayer(vidPlayer)
                    self.videoLayer = True
                    self.engine.ticksAtStart = pygame.time.get_ticks()
                    while not vidPlayer.finished:
                        self.engine.run()
                    self.engine.view.popLayer(vidPlayer)
                    self.engine.view.pushLayer(MainMenu(self.engine))
        if not self.videoLayer:
            self.engine.setStartupLayer(MainMenu(self.engine))

        # Run the main game loop.
        try:
            self.engine.ticksAtStart = pygame.time.get_ticks()
            while self.engine.run():
                pass
        except KeyboardInterrupt:
            log.notice("Left mainloop due to KeyboardInterrupt.")
            # don't reraise

        # Restart the program if the engine is asking that we do so.
        if self.engine.restartRequested:
            self.restart()

        # evilynux - MainMenu class already calls this - useless?
        self.engine.quit()

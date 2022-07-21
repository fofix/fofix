#!/usr/bin/python
# -*- coding: utf-8 -*-

#####################################################################
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 evilynux <evilynux@gmail.com>                  #
#               2009-2019 FoFiX Team                                #
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

import logging
import os

import pygame

from fofix.core import Version
from fofix.core import VFS

from fofix.core.videolayer import VideoLayer
from fofix.core.videolayer import VideoPlayerError
from fofix.core.GameEngine import GameEngine
from fofix.game.MainMenu import MainMenu
from fofix.core import Config


log = logging.getLogger(__name__)


class Main(object):
    def __init__(self, a):
        self.args = a

        self.configfile = self.args['config']
        self.fullscreen = self.args['fullscreen']
        self.resolution = self.args['resolution']
        self.theme = self.args['theme']

        self.config = self.load_config(self.configfile)

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

    def restart(self):
        log.info("Restarting.")
        self.engine.audio.close()
        self.restartRequested = True

    def run(self):
        # Perhaps this could be implemented in a better way...
        # Play the intro video if it is present, we have the capability
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
            log.info("Left mainloop due to KeyboardInterrupt.")
            # don't reraise

        # Restart the program if the engine is asking that we do so.
        if self.engine.restartRequested:
            self.restart()

        # MainMenu class already calls this - useless?
        self.engine.quit()

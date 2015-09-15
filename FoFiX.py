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
Main game executable.
'''

import argparse
import sys
import os
import platform
import subprocess
import atexit

def run_command(command):
    command = command.split(' ')
    cmd = subprocess.Popen(command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE)

    output, err = cmd.communicate()
    data = output.strip()

    return data

pisSet = None
# This prevents the following message being displayed on osx:
# ApplePersistenceIgnoreState: Existing state will not be touched. New state will be written to *path*
if 'Darwin' in platform.platform():
    data = run_command('defaults read org.python.python ApplePersistenceIgnoreState')

    if data in ['1', 'ON']:
        run_command('defaults write org.python.python ApplePersistenceIgnoreState 0')
        atexit.register(run_command, 'defaults write org.python.python ApplePersistenceIgnoreState %s' % data)
        apisSet = True
    else:
        apisSet = False

# Add the directory of DLL dependencies to the PATH if we're running
# from source on Windows so we pick them up when those bits are imported.
if os.name == 'nt' and not hasattr(sys, 'frozen'):
    os.environ['PATH'] = os.path.abspath(os.path.join('.', 'win32', 'deps', 'bin')) + os.pathsep + os.environ['PATH']

def disable_gl_checks():
    assert 'OpenGL' not in sys.modules
    
    import OpenGL
    if OpenGL.__version__ >= '3':
        OpenGL.ERROR_CHECKING = False
        OpenGL.ARRAY_SIZE_CHECKING = False
        OpenGL.ERROR_ON_COPY = True
        OpenGL.FORWARD_COMPATIBLE_ONLY = True
        OpenGL.SIZE_1_ARRAY_UNPACK = False
        OpenGL.STORE_POINTERS = False

def cmd_args():
    parser = argparse.ArgumentParser(description='Frets On Fire X (FoFiX)')
    # Where the name automatically assigned to the metavar option is to long i used x in its place.
    # Might go back and 
    options = parser.add_argument_group('Options')
    options.add_argument('-r', '--resolution', type=str,  metavar='x',    help='Force a specific resolution to be used.')
    options.add_argument('-f', '--fullscreen',  action='store_true',       help='Force usage of full-screen mode.')
    options.add_argument('-c', '--config',     type=str,  metavar='x',     help='Use this configuration file instead of the fofix.ini in its default location.  Use "reset" to use the usual fofix.ini but clear it first.')
    options.add_argument('-t', '--theme',      type=str,  metavar='x', help='Force the specified theme to be used. Remember to quote the theme name if it contains spaces (e.g. %(prog)s -t "Guitar Hero III")')
    options.add_argument('-s', '--song',       type=str,                  help='Play a song in one-shot mode. (See "One-shot mode options" below.)')

    osm = parser.add_argument_group('One-Shot Mode')
    osm.add_argument('-p', '--part',    type=int, help='0: Guitar, 1: Rhythm, 2: Bass, 3: Lead')
    osm.add_argument('-d', '--diff',    type=int, help='0: Expert, 1: Hard, 2: Medium, 3: Easy (Only applies if "part" is set)')
    osm.add_argument('-m', '--mode',    type=int, help='0: Quickplay, 1: Practice, 2: Career')
    osm.add_argument('-n', '--players', type=int, help='Number of multiplayer players.')

    adv = parser.add_argument_group('Advanced')
    adv.add_argument('-v', '--verbose',        action='store_true', help='Verbose messages')
    adv.add_argument('-g', '--gl-error-check', action='store_true', help='Enable OpenGL error checking.')

    return vars(parser.parse_args())

args = cmd_args()

#stump: disable pyOpenGL error checking if we are not asked for it.
# This must be before *anything* that may import pyOpenGL!
if args['gl_error_check']:
    disable_gl_checks()

import traceback

import pygame

from fofix.core.VideoPlayer import VideoLayer, VideoPlayerError
from fofix.core.GameEngine import GameEngine
from fofix.game.MainMenu import MainMenu
from fofix.core.Language import _
from fofix.core import Version
from fofix.core import Log, VFS
from fofix.core import Config

class Main():
    def __init__(self):
        global args
        self.args = args

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

        #Lysdestic - Allow support for manipulating fullscreen via CLI
        if self.fullscreen is not None:
            Config.set("video", "fullscreen", self.fullscreen)

        #Lysdestic - Change resolution from CLI
        if self.resolution is not None:
            Config.set("video", "resolution", self.resolution)

        #Lysdestic - Alter theme from CLI
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
                config = Config.load(Version.PROGRAM_UNIXSTYLE_NAME + ".ini", setAsDefault = True)

            else:
                # Load specified config file
                config = Config.load(configPath, setAsDefault = True)
        else:
            # Use default configuration file
            config = Config.load(Version.PROGRAM_UNIXSTYLE_NAME + ".ini", setAsDefault = True)

        return config

    def init_oneshot(self):
        ''' Determine if oneshot mode is valid. '''
        # I think this code can be moved elsewhere...
        self.engine.cmdPlay = 0

        # Check for a valid invocation of one-shot mode.
        if self.playing is not None:
            Log.debug('Validating song directory for one-shot mode.')

            library = Config.get("setlist","base_library")
            basefolder = os.path.join(Version.dataPath(),library,"songs",self.playing)


            if not os.path.exists(os.path.join(basefolder, "song.ini")):

                if not (os.path.exists(os.path.join(basefolder, "notes.mid")) or
                        os.path.exists(os.path.join(basefolder, "notes-unedited.mid"))):

                    if not (os.path.exists(os.path.join(basefolder, "song.ogg")) or
                            os.path.exists(os.path.join(basefolder, "guitar.ogg"))):

                        Log.warn("Song directory provided ('%s') is not a valid song directory. Starting up FoFiX in standard mode." % self.playing)
                        self.engine.startupMessages.append(_("Song directory provided ('%s') is not a valid song directory. Starting up FoFiX in standard mode.") % self.playing)
                        return

            # Set up one-shot mode
            Log.debug('Entering one-shot mode.')
            Config.set("setlist", "selected_song", playing)

            self.engine.cmdPlay = 1

            if diff is not None:
                self.engine.cmdDiff = int(diff)
            if part is not None:
                self.engine.cmdPart = int(part)

            if players == 1:
                self.engine.cmdMode = players, mode, 0
            else:
                self.engine.cmdMode = players, 0, mode

    def restart(self):
        Log.notice("Restarting.")
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
                    Log.error("Error loading intro video:")
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
            Log.notice("Left mainloop due to KeyboardInterrupt.")
            # don't reraise

        # Restart the program if the engine is asking that we do so.
        if self.engine.restartRequested:
            self.restart()

        # evilynux - MainMenu class already calls this - useless?
        self.engine.quit()

if __name__ == '__main__':
    try:
        # This loop restarts the game if a restart is requested
        while True:
            main = Main()
            main.run()
            if not main.restartRequested:
                break

    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        Log.error("Terminating due to unhandled exception: ")
        _logname = os.path.abspath(Log.logFile.name)
        _errmsg = "%s\n\n%s\n%s\n%s\n%s" % (
          _("Terminating due to unhandled exception:"),
          traceback.format_exc(),
          _("If you make a bug report about this error, please include the contents of the following log file:"),
          _logname,
          _("The log file already includes the traceback given above."))

        if os.name == 'nt':
            # If we move to PySDL2 we can replace this with a call to SDL_ShowSimpleMessageBox
            import win32api
            import win32con
            if win32api.MessageBox(0, "%s\n\n%s" % (_errmsg, _("Open the logfile now?")), "%s %s" % (Version.PROGRAM_NAME, Version.version()), win32con.MB_YESNO|win32con.MB_ICONSTOP) == win32con.IDYES:
                Log.logFile.close()
                os.startfile(_logname)
            if hasattr(sys, 'frozen'):
                sys.exit(1)  # don't reraise if py2exe'd so the "Errors occurred" box won't appear after this and confuse the user as to which logfile we actually want
        else:
            print >>sys.stderr, _errmsg
        raise

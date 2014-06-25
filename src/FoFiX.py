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

# Add the directory of DLL dependencies to the PATH if we're running
# from source on Windows so we pick them up when those bits are imported.
if os.name == 'nt' and not hasattr(sys, 'frozen'):
    os.environ['PATH'] = os.path.abspath(os.path.join('..', 'win32', 'deps', 'bin')) + os.pathsep + os.environ['PATH']

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

import Version
from util import Log, VFS
from configuration import Config
from core.GameEngine import GameEngine
from views.MainMenu.MainMenu import MainMenu
from core.Language import _
import pygame
import traceback
from graphics.VideoPlayer import VideoLayer, VideoPlayerError


def main():
    global args

    playing = args['song']
    configFile = args['config']
    fullscreen = args['fullscreen']
    resolution = args['resolution']
    theme = args['theme']
    diff = args['diff']
    part = args['part']
    mode = args['mode']
    players = args['players']

    # Load the configuration file.
    if configFile is not None:
        if configFile.lower() == "reset":
            fileName = os.path.join(VFS.getWritableResourcePath(), Version.PROGRAM_UNIXSTYLE_NAME + ".ini")
            os.remove(fileName)
            config = Config.load(Version.PROGRAM_UNIXSTYLE_NAME + ".ini", setAsDefault = True)
        else:
            config = Config.load(configFile, setAsDefault = True)
    else:
        config = Config.load(Version.PROGRAM_UNIXSTYLE_NAME + ".ini", setAsDefault = True)

    #Lysdestic - Allow support for manipulating fullscreen via CLI
    if fullscreen is not None:
        Config.set("video", "fullscreen", fullscreen)

    #Lysdestic - Change resolution from CLI
    if resolution is not None:
        Config.set("video", "resolution", resolution)

    #Lysdestic - Alter theme from CLI
    if theme is not None:
        Config.set("coffee", "themename", theme)

    engine = GameEngine(config)
    engine.cmdPlay = 0

    # Check for a valid invocation of one-shot mode.
    if playing is not None:
        Log.debug('Validating song directory for one-shot mode.')
        library = Config.get("setlist","base_library")
        basefolder = os.path.join(Version.dataPath(),library,"songs",playing)
        if not (os.path.exists(os.path.join(basefolder, "song.ini")) and (os.path.exists(os.path.join(basefolder, "notes.mid")) or os.path.exists(os.path.join(basefolder, "notes-unedited.mid"))) and (os.path.exists(os.path.join(basefolder, "song.ogg")) or os.path.exists(os.path.join(basefolder, "guitar.ogg")))):
            Log.warn("Song directory provided ('%s') is not a valid song directory. Starting up FoFiX in standard mode." % playing)
            engine.startupMessages.append(_("Song directory provided ('%s') is not a valid song directory. Starting up FoFiX in standard mode.") % playing)
            playing = None

    # Set up one-shot mode if the invocation is valid for it.
    if playing is not None:
        Log.debug('Entering one-shot mode.')
        Config.set("setlist", "selected_song", playing)
        engine.cmdPlay = 1
        if diff is not None:
            engine.cmdDiff = int(diff)
        if part is not None:
            engine.cmdPart = int(part)
        #evilynux - Multiplayer and mode selection support
        if players == 1:
            engine.cmdMode = players, mode, 0
        else:
            engine.cmdMode = players, 0, mode

    # Play the intro video if it is present, we have the capability, and
    # we are not in one-shot mode.
    videoLayer = False
    if not engine.cmdPlay:
        themename = Config.get("coffee", "themename")
        vidSource = os.path.join(Version.dataPath(), 'themes', themename, \
                                 'menu', 'intro.ogv')
        if os.path.isfile(vidSource):
            try:
                vidPlayer = VideoLayer(engine, vidSource, cancellable=True)
            except (IOError, VideoPlayerError):
                Log.error("Error loading intro video:")
            else:
                vidPlayer.play()
                engine.view.pushLayer(vidPlayer)
                videoLayer = True
                engine.ticksAtStart = pygame.time.get_ticks()
                while not vidPlayer.finished:
                    engine.run()
                engine.view.popLayer(vidPlayer)
                engine.view.pushLayer(MainMenu(engine))
    if not videoLayer:
        engine.setStartupLayer(MainMenu(engine))

    # Run the main game loop.
    try:
        engine.ticksAtStart = pygame.time.get_ticks()
        while engine.run():
            pass
    except KeyboardInterrupt:
        Log.notice("Left mainloop due to KeyboardInterrupt.")
        # don't reraise

    # Restart the program if the engine is asking that we do so.
    if engine.restartRequested:
        Log.notice("Restarting.")
        engine.audio.close()
        try:
            # Extra arguments to insert between the executable we call and our
            # command line arguments.
            args = []
            # Figure out what executable to call.
            if hasattr(sys, "frozen"):
                if os.name == "nt":
                    # When py2exe'd, sys.executable is the name of the EXE.
                    exe = os.path.abspath(unicode(sys.executable, sys.getfilesystemencoding()))
                elif sys.frozen == "macosx_app":
                    # When py2app'd, sys.executable is a Python interpreter copied
                    # into the same dir where we live.
                    exe = os.path.join(os.path.dirname(sys.executable), 'FoFiX')  # FIXME: don't hard-code "FoFiX" here
                else:
                    raise RuntimeError, "Don't know how to restart when sys.frozen is %s" % repr(sys.frozen)
            else:
                # When running from source, sys.executable is the Python interpreter
                # being used to run the program.
                exe = sys.executable
                # Pass the optimization level on if python version >= 2.6.0 as
                # sys.flags has been introduced in 2.6.0.
                if sys.version_info[:3] >= (2,6,0) and sys.flags.optimize > 0:
                    args.append('-%s' % ('O' * sys.flags.optimize))
                args.append(sys.argv[0])
            os.execv(exe, [sys.executable] + args + sys.argv[1:])
        except:
            Log.error("Restart failed: ")
            raise

    # evilynux - MainMenu class already calls this - useless?
    engine.quit()


if __name__ == '__main__':
    try:
        main()
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

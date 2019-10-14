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
Main game executable.
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# DO NOT GROUP IMPORTS!
# Imports are sprinkled throughout this file, and they must stay where they are!

import argparse
import atexit
import logging
import os
import subprocess
import sys
import traceback


def run_command(command):
    command = command.split(' ')
    cmd = subprocess.Popen(command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE)

    output, __ = cmd.communicate()
    data = output.strip()

    return data


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

    options = parser.add_argument_group('Options')
    options.add_argument('-r', '--resolution', type=str, metavar='x', help='Force a specific resolution to be used.', default=None)
    options.add_argument('-f', '--fullscreen', action='store_true', help='Force usage of full-screen mode.', default=None)
    options.add_argument('-c', '--config', type=str, metavar='x', help='Use this configuration file instead of the fofix.ini in its default location.  Use "reset" to use the usual fofix.ini but clear it first.')
    options.add_argument('-t', '--theme', type=str, metavar='x', help='Force the specified theme to be used. Remember to quote the theme name if it contains spaces (e.g. %(prog)s -t "Guitar Hero III")', default=None)

    adv = parser.add_argument_group('Advanced')
    adv.add_argument('-v', '--verbose', action='store_true', help='Verbose messages')
    adv.add_argument('-g', '--gl-error-check', action='store_true', help='Enable OpenGL error checking.')

    return vars(parser.parse_args())


args = cmd_args()

# Disable pyOpenGL error checking if we are not asked for it.
# This must be before *anything* that may import pyOpenGL!
if not args['gl_error_check']:
    disable_gl_checks()


from fofix.core import Version
from fofix.core import VFS
from fofix.core.VideoPlayer import VideoLayer, VideoPlayerError
from fofix.core.GameEngine import GameEngine
from fofix.game.MainMenu import MainMenu
from fofix.core.Language import _
from fofix.core import Config
from fofix.game.Main import Main

import fretwork
from fretwork import log

# PIL doesn't init correctly when inside py2exe, so here we kick it in butt.
# Web search results all point to this solution:
# http://www.py2exe.org/index.cgi/py2exeAndPIL
import PIL.Image
import PIL.BmpImagePlugin
import PIL.GifImagePlugin
import PIL.JpegImagePlugin
import PIL.MpoImagePlugin
import PIL.PpmImagePlugin
import PIL.TiffImagePlugin
import PIL.PngImagePlugin


if __name__ == '__main__':
    is_windows = (os.name == 'nt')
    is_macos = sys.platform.startswith('darwin')

    # This prevents the following message being displayed on macOS:
    # ApplePersistenceIgnoreState: Existing state will not be touched. New state will be written to *path*
    if is_macos:
        data = run_command('defaults read org.python.python ApplePersistenceIgnoreState')
        if data in ['1', 'ON']:
            run_command('defaults write org.python.python ApplePersistenceIgnoreState 0')
            atexit.register(run_command, 'defaults write org.python.python ApplePersistenceIgnoreState %s' % data)

    # Add the directory of DLL dependencies to the PATH if we're running
    # from source on Windows so we pick them up when those bits are imported.
    if is_windows and not hasattr(sys, 'frozen'):
        os.environ['PATH'] = os.path.abspath(os.path.join('.', 'win32', 'deps', 'bin')) + os.pathsep + os.environ['PATH']

    # setup the logfile
    # File object representing the logfile
    if is_macos:
        # Under MacOS X, put the logs in ~/Library/Logs
        logfile = os.path.expanduser('~/Library/Logs/%s.log' % Version.PROGRAM_UNIXSTYLE_NAME)
    else:
        # Unix: ~/.fofix/
        logfile = VFS.resolveWrite('/userdata/%s.log' % Version.PROGRAM_UNIXSTYLE_NAME)

    log.configure(logfile)
    logger = logging.getLogger(__name__)

    fretworkRequired = (0, 4, 0)
    reqVerStr = '.'.join([str(i) for i in fretworkRequired])
    fretworkErrorStr = '''

    The version of fretwork installed is old. Please install the latest version from github.
    https://github.com/fofix/fretwork/releases/
    Installed: {0}
    Required: {1}
    '''
    # The first version of fretwork didn't have __version__
    if hasattr(fretwork, '__version__'):
        version = fretwork.__version__.split('-')[0]  # remove 'dev' from ver
        version = tuple([int(i) for i in version.split('.')])

        if version < fretworkRequired:
            fwErrStr = fretworkErrorStr.format(fretwork.__version__, reqVerStr)
            raise RuntimeError(fwErrStr)
    else:
        version = '0.1.0'
        fwErrStr = fretworkErrorStr.format(version, reqVerStr)
        raise RuntimeError(fwErrStr)

    try:
        # This loop restarts the game if a restart is requested
        while True:
            main = Main(args)
            main.run()
            if not main.restartRequested:
                break

    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        logger.error("Terminating due to unhandled exception: ")
        _logname = os.path.abspath(logfile)
        _errmsg = "%s\n\n%s\n%s\n%s\n%s" % (
          _("Terminating due to unhandled exception:"),
          traceback.format_exc(),
          _("If you make a bug report about this error, please include the contents of the following log file:"),
          _logname,
          _("The log file already includes the traceback given above."))

        if is_windows:
            # If we move to PySDL2 we can replace this with a call to SDL_ShowSimpleMessageBox
            import win32api
            import win32con
            if win32api.MessageBox(0, "%s\n\n%s" % (_errmsg, _("Open the logfile now?")), "%s %s" % (Version.PROGRAM_NAME, Version.version()), win32con.MB_YESNO|win32con.MB_ICONSTOP) == win32con.IDYES:
                os.startfile(_logname)
            if hasattr(sys, 'frozen'):
                sys.exit(1)  # don't reraise if py2exe'd so the "Errors occurred" box won't appear after this and confuse the user as to which logfile we actually want
        else:
            logger.error(_errmsg)
        raise

#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#####################################################################
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2006 Sami Kyöstilä                                  #
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

"""
Main game executable.
"""

# Register the latin-1 encoding
import codecs
import encodings.iso8859_1
import encodings.utf_8
codecs.register(lambda encoding: encodings.iso8859_1.getregentry())
codecs.register(lambda encoding: encodings.utf_8.getregentry())
assert codecs.lookup("iso-8859-1")
assert codecs.lookup("utf-8")

import Config
from GameEngine import GameEngine
from MainMenu import MainMenu
import Log
import Version

import getopt
import sys
import os
import codecs
import Resource
import pygame

usage = """%(prog)s [options]
Options:
  --verbose, -v                       Verbose messages
  --debug,   -d                       Write Debug file
  --config=, -c [configfile]          Use this instead of fofix.ini
  --fullscreen=, -f [true/false]      Change fullscreen settings in fofix.ini
  --resolution=, -r [resolution]      Change game resolution from commandline.
  --song=,   -s [songdir]             Play a song from the commandline
  --diff=,   -l [level of difficulty] Use this difficulty level
  --part=,   -p [part number]         Use this part
  --mode=,   -m [game mode]           1P: 0-Quickplay, 1-Practice,     2-Career
                                      2P: 0-Face-off,  1-Pro Face-off, 2-Party mode
  --nbrplayers=,-n [1 - 4]            Number of players (1 - 4)
  --theme,   -t (theme)               Starts using this theme. Needs to be in " " marks. (IE- -t "Guitar Hero III")     
""" % {"prog": sys.argv[0] }

debuglevel = 0    #MFH - experimental, leave at 0
import linecache

#if __name__ == "__main__":
def main():
  """Main thread"""

  try:
    opts, args = getopt.getopt(sys.argv[1:], "vdc:f:r:t:s:l:p:m:n:", ["verbose", "debug", "config=", "fullscreen=", "resolution=", "theme=", "song=", "diff=", "part=", "mode=", "nbrplayers="])
  except getopt.GetoptError:
    print usage
    sys.exit(1)
    
  playing = None
  configFile = None
  fullscreen = None
  resolution = None
  theme = None
  debug = False
  difficulty = 0
  part = 0
  mode = 0
  nbrplayers = 1
  for opt, arg in opts:
    if opt in ["--verbose", "-v"]:
      Log.quiet = False
    if opt in ["--debug", "-d"]:
      debug = True
    if opt in ["--config", "-c"]:
      configFile = arg
    if opt in ["--fullscreen", "-f"]:
      fullscreen = arg
    if opt in ["--resolution", "-r"]:
      resolution = arg
    if opt in ["--theme", "-t"]:
      theme = arg
    if opt in ["--song", "-s"]:
      playing = arg
    if opt in ["--diff", "-l"]:
      difficulty = arg      
    if opt in ["--part", "-p"]:
      part = arg
    #evilynux - Multiplayer and mode selection support
    if opt in ["--mode", "-m"]:
      mode = int(arg)
    if opt in ["--nbrplayers", "-n"]:
      nbrplayers = int(arg)
      
  while True:
    if configFile != None:
      if configFile.lower() == "reset":
        fileName = os.path.join(Resource.getWritableResourcePath(), Version.appName() + ".ini")
        os.remove(fileName)
        config = Config.load(Version.appName() + ".ini", setAsDefault = True)
      else:
        config = Config.load(configFile, setAsDefault = True)
    else:
      config = Config.load(Version.appName() + ".ini", setAsDefault = True)

    #Lysdestic - Allow support for manipulating fullscreen via CLI
    if fullscreen != None:
      Config.set("video", "fullscreen", fullscreen)

    #Lysdestic - Change resolution from CLI
    if resolution != None:
      Config.set("video", "resolution", resolution)

    #Lysdestic - Alter theme from CLI
    if theme != None:
      Config.set("coffee", "themename", theme)

    engine = GameEngine(config)
    engine.cmdPlay = 0
    
    if playing != None:
      Config.set("game", "selected_library", "songs")
      Config.set("game", "selected_song", playing)
      engine.cmdPlay = 1
      engine.cmdDiff = int(difficulty)
      engine.cmdPart = int(part)
      #evilynux - Multiplayer and mode selection support
      Config.set("game", "players", nbrplayers)
      Config.set("game", "game_mode", mode)
      Config.set("game", "multiplayer_mode", mode)

    if debug == True:
      engine.setDebugModeEnabled(not engine.isDebugModeEnabled())
      engine.debugLayer.debugOut(engine)
      engine.quit()
      break
      
    encoding = Config.get("game", "encoding")
    if encoding != None:
      reload(sys)
      sys.setdefaultencoding(encoding)
    engine.setStartupLayer(MainMenu(engine))

    #stump: make psyco optional
    if Config.get("performance", "use_psyco"):
      try:
        import psyco
        psyco.profile()
      except:
        Log.warn("Unable to enable psyco.")

    try:
      engine.ticksAtStart = pygame.time.get_ticks()
      while engine.run():
        pass
    except KeyboardInterrupt:
        pass
    if engine.restartRequested:
      Log.notice("Restarting.")
      engine.audio.close()
      try:
        # Determine whether were running from an exe or not
        if hasattr(sys, "frozen"):
          if os.name == "nt":
            os.execl("FoFiX.exe", "FoFiX.exe", *sys.argv[1:])
          elif sys.frozen == "macosx_app":
            import string
            import subprocess
            appname = string.join(string.split(sys.executable, '/')[:-1], '/')
            appname = appname+"/FoFiX"
            subprocess.Popen(`appname`, shell=True)
          else:
            os.execl("./FoFiX", "./FoFiX", *sys.argv[1:])
        else:
          # stump: sys.executable points to the active python interpreter
          os.execl(sys.executable, sys.executable, "FoFiX.py", *sys.argv[1:])
      except:
        Log.warn("Restart failed.")
        raise
      break
    else:
      break
  # evilynux - MainMenu class already calls this - useless?
  engine.quit()

class Trace:
    """Class for tracing script
    
    This class is developed by cyke64.
    Lisenced under GNU GPL.
    """
    def __init__(self, runfile, f_all=u'traceit.txt',
                 f_main=u'traceitmain.txt'):
        self.out_all=open(f_all, 'w')
        self.out_main=open(f_main, 'w')
        self.runfile = runfile
      
    def go(self):
        sys.settrace(self.traceit)
    
    def stop(self):    
        sys.settrace(None)
        self.out_all.close()
        self.out_main.close()
 
    def traceit(self, frame, event, arg):
        lineno = frame.f_lineno
        name = frame.f_globals['__name__']
        if (frame.f_globals).has_key('__file__'):
            file_trace=frame.f_globals['__file__']
            line = linecache.getline(file_trace, lineno)
        else:
            file_trace = self.runfile
            line = linecache.getline(file_trace, lineno)
            self.out_main.write('%s*%s*\n*%s*\n' \
              % (event, lineno, line.rstrip()))
            self.out_all.write('%s*%s*of %s(%s)\n*%s*\n' \
              %(event, lineno, name, file_trace, line.rstrip()))
            e32.ao_sleep(0)
        return self.traceit
 
def call_callback(func):
    """Catch exception
    
    This function is developed by jethro.fn.
    """
    def call_func(*args, **kwds):
        import traceback
        #global exceptions
        #global script_lock
        try:
            return func(*args, **kwds)
        except:
            # Collect Exceptions
            #exception = ''.join(traceback.format_exception(*sys.exc_info()))
            #exceptions.append(exception)
            
            Log.error("Exception traceback: " + str(traceback.format_exception(*sys.exc_info())) )
            
            # Signal lock in main thread (immediate termination)
            #if debuglevel == 2: script_lock.signal()
    return call_func
 

if __name__ == '__main__':
    try:
        if debuglevel == 2:
            trace = Trace('FoFiX.py')
            trace.go()
            call_callback(main())
            trace.stop()
        elif debuglevel == 1:
            call_callback(main())
        else:
            main()
    except:
        raise

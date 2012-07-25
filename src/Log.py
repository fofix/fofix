#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2009 John Stumpo                                    #
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
Functions for writing to the logfile.
'''

import sys
import os
import Resource
import Version
import traceback
import time
import warnings

# Whether to output log entries to stdout in addition to the logfile.
quiet = True

# File object representing the logfile.
if os.name == "posix": # evilynux - logfile in ~/.fofix/ for GNU/Linux and MacOS X
    # evilynux - Under MacOS X, put the logs in ~/Library/Logs
    if os.uname()[0] == "Darwin":
        logFile = open(os.path.join(Resource.getWritableResourcePath(),
                                    "..", "..", "Logs",
                                    Version.PROGRAM_UNIXSTYLE_NAME + ".log"), "w")
    else: # GNU/Linux et al.
        logFile = open(os.path.join(Resource.getWritableResourcePath(), Version.PROGRAM_UNIXSTYLE_NAME + ".log"), "w")
elif os.name == "nt":
    logFile = open(os.path.join(Resource.getWritableResourcePath(), Version.PROGRAM_UNIXSTYLE_NAME + ".log"), "w")
else:
    logFile = open(Version.PROGRAM_UNIXSTYLE_NAME + ".log", "w")  #MFH - local logfile!

# Character encoding to use for logging.
encoding = "iso-8859-1"

if "-v" in sys.argv or "--verbose" in sys.argv:
    quiet = False

# Labels for different priorities, as output to the logfile.
labels = {
  "warn":   "(W)",
  "debug":  "(D)",
  "notice": "(N)",
  "error":  "(E)",
}

# Labels for different priorities, as output to stdout.
if os.name == "posix":
    displaylabels = {
      "warn":   "\033[1;33m(W)\033[0m",
      "debug":  "\033[1;34m(D)\033[0m",
      "notice": "\033[1;32m(N)\033[0m",
      "error":  "\033[1;31m(E)\033[0m",
    }
else:
    displaylabels = labels

def _log(cls, msg):
    '''
    Generic logging function.
    @param cls:   Priority class for the message
    @param msg:   Log message text
    '''
    if not isinstance(msg, unicode):
        msg = unicode(msg, encoding)
    msg = msg.encode(encoding, "replace") # fculpo - proper encoding
    timeprefix = "[%12.6f] " % (time.time() - _initTime)
    if not quiet:
        print timeprefix + displaylabels[cls] + " " + msg
    print >>logFile, timeprefix + labels[cls] + " " + msg
    logFile.flush()  #stump: truncated logfiles be gone!

def error(msg):
    '''
    Log a major error.
    If this is called while handling an exception, the traceback will
    be automatically included in the log.
    @param msg:   Error message text
    '''
    if sys.exc_info() == (None, None, None):
        #warnings.warn("Log.error() called without an active exception", UserWarning, 2)  #stump: should we enforce this?
        _log("error", msg)
    else:
        _log("error", msg + "\n" + traceback.format_exc())

def warn(msg):
    '''
    Log a warning.
    @param msg:   Warning message text
    '''
    _log("warn", msg)

def notice(msg):
    '''
    Log a notice.
    @param msg:   Notice message text
    '''
    _log("notice", msg)

def debug(msg):
    '''
    Log a debug message.
    @param msg:   Debug message text
    '''
    _log("debug", msg)

def _showwarning(*args, **kw):
    '''A hook to catch Python warnings.'''
    warn("A Python warning was issued:\n" + warnings.formatwarning(*args, **kw))
    _old_showwarning(*args, **kw)
_old_showwarning = warnings.showwarning
warnings.showwarning = _showwarning

_initTime = time.time()
debug("Logging initialized: " + time.asctime())
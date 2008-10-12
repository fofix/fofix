#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
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

import sys
import os
import Resource

quiet = True
logFile = open(os.path.join(Resource.getWritableResourcePath(), "fretsonfire.log"), "w")
encoding = "iso-8859-1"

if "-v" in sys.argv:
  quiet = False
  
if os.name == "posix":
  labels = {
    "warn":   "\033[1;33m(W)\033[0m",
    "debug":  "\033[1;34m(D)\033[0m",
    "notice": "\033[1;32m(N)\033[0m",
    "error":  "\033[1;31m(E)\033[0m",
  }
else:
  labels = {
    "warn":   "(W)",
    "debug":  "(D)",
    "notice": "(N)",
    "error":  "(E)",
  }

def log(cls, msg):
  msg = unicode(msg).encode(encoding, "ignore")
  if not quiet:
    print labels[cls] + " " + msg
  print >>logFile, labels[cls] + " " + msg

warn   = lambda msg: log("warn", msg)
debug  = lambda msg: log("debug", msg)
notice = lambda msg: log("notice", msg)
error  = lambda msg: log("error", msg)

#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Ky�stil�                                  #
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
import re
import os
VERSION = '3.122'
RELEASE_ID = 'Final'
URL = 'https://fofix.org'

def _getTagLine():
    # Look for a git repository.
    gameRoot = os.path.dirname(__file__).rsplit(os.path.sep, 1)[0] # game root dir
    gitDir = '{0}{1}.git'.format(gameRoot, os.path.sep)
    if os.path.isdir(gitDir):
        shortref = None
        headhash = None

        # HEAD is in the form "ref: refs/heads/master\n" if a branch is
        # checked out, or just the hash if HEAD is detached.
        refline = open('{0}{1}HEAD'.format(gitDir, os.path.sep)).read().strip()

        if refline[0:5] == "ref: ":
            headref = refline[5:]
            if os.path.isfile('{0}{1}.git{1}{2}'.format(gameRoot, os.path.sep, headref)):
                # The ref is in the form "sha1-hash\n"
                headRefPath = gitDir + os.path.sep + headref
                headhash = open(headRefPath).read().strip()
            else:
                # It's a packed ref.
                for line in open('{0}{1}}packed-refs'.format(gitDir, os.path.sep)):
                    if line.strip().endswith(headref):
                        headhash = line[:40]
                        break
            shortref = re.sub('^refs/(heads/)?', '', headref)
        else:
            shortref = "(detached)"
            headhash = refline

        return 'development (git %s %s)' % (shortref or "(unknown)",
                                            headhash and headhash[:7] or "(unknown)")

    else:
        return None

def appName():
  return "fofix"

def appNameSexy():
  return "FoFiX"

def revision():
  revision = _getTagLine()
  if revision is None:
      revision = RELEASE_ID
  return revision

def versionNum():
    return version


# evilynux: Returns version number w.r.t. frozen state
def version():
  if hasattr(sys, 'frozen'):
    # stump: if we've been py2exe'd, read our version string from the exe.
    if sys.frozen == 'windows_exe':
      import win32api
      us = os.path.abspath(unicode(sys.executable, sys.getfilesystemencoding()))
      version = win32api.GetFileVersionInfo(us, r'\StringFileInfo\%04x%04x\ProductVersion' % win32api.GetFileVersionInfo(us, r'\VarFileInfo\Translation')[0])
    else:
      version = "%s %s" % ( VERSION, revision() )
  else:
    version = "%s %s" % ( VERSION, revision() )
  return version

def dataPath():
  # Determine whether were running from an exe or not
  if hasattr(sys, "frozen"):
    if os.name == "posix":
      dataPath = os.path.join(os.path.dirname(sys.argv[0]), "../lib/fofix")
      if not os.path.isdir(dataPath):
        dataPath = "data"
    else:
      dataPath = "data"
  else:
    dataPath = os.path.join("..", "data")
  return dataPath

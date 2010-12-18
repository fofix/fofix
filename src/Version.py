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
import re

MAJOR_VERSION = 4
MINOR_VERSION = 0
MICRO_VERSION = 0
PROGRAM_NAME = 'FoFiX'
PROGRAM_UNIXSTYLE_NAME = 'fofix'
URL = 'http://fofix.googlecode.com'
RELEASE_ID = 'alpha 1'

def _getTagLine():
  import VFS  # can't be done at top level due to circular import issues...

  # Look for a git repository.
  if VFS.isdir('/gameroot/.git'):
    # HEAD is in the form "ref: refs/heads/master\n"
    headref = VFS.open('/gameroot/.git/HEAD').read()[5:].strip()
    if VFS.isfile('/gameroot/.git/' + headref):
      # The ref is in the form "sha1-hash\n"
      headhash = VFS.open('/gameroot/.git/' + headref).read().strip()
    else:
      # It's a packed ref.
      for line in VFS.open('/gameroot/.git/packed-refs'):
        if line.strip().endswith(headref):
          headhash = line[:40]
          break
    shortref = re.sub('^refs/(heads/)?', '', headref)
    return 'development (git %s %s)' % (shortref, headhash[:7])

  # Look for the svn administrative directory.
  elif VFS.isdir('/gameroot/src/.svn'):
    revision = VFS.open('/gameroot/src/.svn/entries').readlines()[3].strip()
    return 'development (svn r%s)' % revision

  else:
    return None

def revision():
  rev = _getTagLine()
  if rev is None:
    rev = RELEASE_ID
  return rev

def versionNum():
  return "%d.%d.%d" % (MAJOR_VERSION, MINOR_VERSION, MICRO_VERSION)

def isWindowsExe():
  '''
  Are we running from a py2exe'd Windows executable?
  @return: boolean for whether this is the Windows executable
  '''
  return hasattr(sys, 'frozen') and sys.frozen == 'windows_exe'

# evilynux: Returns version number w.r.t. frozen state
def version():
  if isWindowsExe():
    # stump: if we've been py2exe'd, read our version string from the exe.
    import win32api
    us = os.path.abspath(unicode(sys.executable, sys.getfilesystemencoding()))
    version = win32api.GetFileVersionInfo(us, r'\StringFileInfo\%04x%04x\ProductVersion' % win32api.GetFileVersionInfo(us, r'\VarFileInfo\Translation')[0])
  else:
    version = "%s %s" % (versionNum(), revision())
  return version

#stump: VFS will take care of this
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
  dataPath = os.path.abspath(dataPath)
  return dataPath

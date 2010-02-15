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
import subprocess

MAJOR_VERSION = 4
MINOR_VERSION = 0
MICRO_VERSION = 0
PROGRAM_NAME = 'FoFiX'
PROGRAM_UNIXSTYLE_NAME = 'fofix'
URL = 'http://fofix.googlecode.com'
RELEASE_ID = 'development'

## Get svn revision info by examining .svn/entries directly.
def _getSvnTagLine():
  entriesFile = os.path.join('.svn', 'entries')
  if not os.path.isfile(entriesFile):
    return None
  rev = int(open(entriesFile).read().splitlines()[3])
  return 'development (r%d)' % rev

## Get git revision info by calling the git executable.
def _getGitTagLine():
  # Get the commit hash for the current HEAD.
  try:
    revparse = subprocess.Popen(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  except OSError:  # if git was not found
    return None
  head = revparse.communicate()[0].strip()
  if revparse.returncode != 0:
    return None

  # Find the latest git-svn commit that is an ancestor of the current HEAD
  # and pull the svn revision number (injected by git-svn) out of the
  # commit message.
  latestSvnLog = subprocess.Popen(['git', 'log', '--grep=git-svn-id:', '-1'], stdout=subprocess.PIPE).communicate()[0]
  if latestSvnLog.strip() != '':
    svnRevision = 'r%d+' % int(latestSvnLog.splitlines()[-1].split('@')[1].split()[0])
  else:
    svnRevision = ''

  return 'development (%sgit %s)' % (svnRevision, head[:7])

def _getTagLine():
  tagline = _getGitTagLine()
  if tagline is None:
    tagline = _getSvnTagLine()
  return tagline

def revision():
  rev = _getGitTagLine()
  if rev is None:
    rev = _getSvnTagLine()
  if rev is None:
    rev = RELEASE_ID
  return rev

def versionNum():
  return "%d.%d.%d" % (MAJOR_VERSION, MINOR_VERSION, MICRO_VERSION)

## Are we running from a py2exe'd Windows executable? (Because typing the
# test out explicitly everywhere detracts from code readability.)
# @return boolean for whether this is the Windows executable
def isWindowsExe():
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

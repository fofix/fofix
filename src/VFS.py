#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2009 John Stumpo                                    #
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

##@package VFS
# Functions providing a convenient virtual filesystem.
#
# Among other things, this is how themes and mods will be implemented.
# Note that *all* VFS functions use slash-delimited paths, relieving
# other code of the need to os.path.join().  All VFS paths must also
# be absolute (i.e. start with a slash) and may not contain "." or "..".
#
# Files or directories may be mounted in the root of the VFS read-only
# or read-write.  Mounting multiple things onto the same mountpoint
# overlays the newer mount's contents on the old mount's contents, but
# read-write mounts always prevail over read-only mounts in the resolution
# order.  All write attempts to a given mountpoint go to the most recent
# read-write mount on that mountpoint; trying to write to a mountpoint
# that has no writable mounts raises OSError(EROFS).  Modification of
# files existing in lower layers but not the most recent writable mount
# uses copy-on-write semantics.  There is no way to make something in
# a lower layer appear to have been deleted, however.

import Version

import os
import re
import errno
import sys
import shutil
import time
from stat import S_IFDIR, S_ISDIR, S_ISREG

_mountTable = {}

## Implementation of a mount point in the VFS root.
# @private
class Mount(object):
  def __init__(self):
    ## List of read-only backing directories, in decreasing order of priority.
    self.readOnly = []
    ## List of writable backing directories, in decreasing order of priority.
    self.writable = []

  ## Resolve a path to a file that the user wants to read.
  # @param path    Virtual path within this mount
  # @return        Physical path to the file
  # @throws        OSError(ENOENT) if file does not exist
  def resolveRead(self, path):
    for p in (self.writable + self.readOnly):
      candidate = os.path.join(p, path).rstrip(os.sep)
      if os.path.exists(candidate):
        return candidate
    raise OSError(errno.ENOENT, os.strerror(errno.ENOENT))

  ## Resolve a path to a file that the user wants to create or modify.
  # Copies files to the most recently mounted writable directory if
  # necessary.  If a path is returned, it is guaranteed to be in the
  # most recently mounted writable directory.
  # @param path    Virtual path within this mount
  # @return        Physical path to the file
  # @throws        OSError(EROFS) if all mounted directories are read-only
  def resolveWrite(self, path):
    if len(self.writable) == 0:
      raise OSError(errno.EROFS, os.strerror(errno.EROFS))

    wpath = os.path.join(self.writable[0], path).rstrip(os.sep)
    if os.path.exists(wpath):
      return wpath

    try:
      rpath = self.resolveRead(path)
    except OSError, e:
      if e.errno != errno.ENOENT:
        raise
      rpath = None

    if rpath is not None:
      if not os.path.isdir(os.path.dirname(wpath)):
        os.makedirs(os.path.dirname(wpath))
      shutil.copy2(rpath, wpath)
    return wpath

  ## List the contents of a directory within this mountpoint.
  # @param path    Virtual path within this mount to list
  # @return        List of entries (excluding '.' and '..')
  def listdir(self, path):
    contents = set()
    for p in (self.writable + self.readOnly):
      candidate = os.path.join(p, path)
      if os.path.isdir(candidate):
        contents.update(os.listdir(candidate))
    return list(contents)


## Mount a directory read-only.
# The virtual directory provides the union of the contents of all
# directories mounted on it.
# @param dir        Directory to mount
# @param mountpt    Virtual directory to mount it onto
def mount(dir, mountpt):
  if mountpt not in _mountTable:
    _mountTable[mountpt] = Mount()
  _mountTable[mountpt].readOnly.append(dir)

## Mount a directory and allow writing.
# The most recent writable-mounted directory on a given
# mountpoint receives all writes made to the mountpoint.
# @param dir        Directory to mount
# @param mountpt    Virtual directory to mount it onto
def mountWritable(dir, mountpt):
  if mountpt not in _mountTable:
    _mountTable[mountpt] = Mount()
  _mountTable[mountpt].writable.append(dir)

## Validate and convert a VFS path to a mount point and a native path
# fragment suitable for passing to the mount point's methods.
# @param path   VFS path
# @return       2-tuple of mount and native path fragment to pass to the mount
# @throws       OSError(EINVAL) on syntactically invalid VFS path
def _convertPath(path):
  if re.match('^/[^:\\\\]*$', path) is None or re.match('/\\.\\.?(/|$)', path) is not None:
    raise OSError(errno.EINVAL, os.strerror(errno.EINVAL))
  while '//' in path:
    path = path.replace('//', '/')
  components = path.lstrip('/').split('/')
  if components[0] not in _mountTable:
    raise OSError(errno.ENOENT, os.strerror(errno.ENOENT))
  return _mountTable[components[0]], os.sep.join(components[1:])

## Convert a VFS path into a real path that is usable to access an
# already-existing file or directory.
# @param path     VFS path
# @return         Real path
# @throws         OSError(ENOENT) if path does not exist
def resolveRead(path):
  mount, frag = _convertPath(path)
  return mount.resolveRead(frag)

## Convert a VFS path that the user wishes to write a file to into a real
# writable path.  Copies a file from a read-only area to a read-write area
# if necessary.
# @param path    VFS path
# @return        Real path
def resolveWrite(path):
  mount, frag = _convertPath(path)
  return mount.resolveWrite(frag)

## stat() result for an object in the virtual filesystem.
# This was originally a hack to give synthesized stat() results for / so
# things worked right in the test code, but it's left in because if you
# can stat anything else in the VFS, you should be able to stat / too.
class StatResult(object):

  ## Set the object up with os.stat() results of path or
  # synthesized properties if the VFS root is statted.
  # @param path    Path to operate on
  def __init__(self, path):
    self._attrs = ('st_mode', 'st_ino', 'st_dev', 'st_nlink', 'st_uid',
      'st_gid', 'st_size', 'st_atime', 'st_mtime', 'st_ctime')
    if path == '/':
      self.st_mode = S_IFDIR | 0555
      self.st_ino = 0
      self.st_dev = 0
      self.st_nlink = 2 + len(_mountTable)
      self.st_uid = 0
      self.st_gid = 0
      self.st_size = 4096
      self.st_atime = time.time()
      self.st_mtime = self.st_atime
      self.st_ctime = self.st_atime
    else:
      s = os.stat(resolveRead(path))
      for a in self._attrs:
        setattr(self, a, getattr(s, a))

  ## Sequence protocol (os.stat() returns a tuple-like object)
  def __len__(self):
    return len(self._attrs)
  ## Sequence protocol (os.stat() returns a tuple-like object)
  def __getitem__(self, idx):
    return getattr(self, self._attrs[idx])
  ## Show our contents when repr()'d.
  def __repr__(self):
    return str(tuple(self))

## Get some properties of the specified path, much like os.stat().
# @param path    Path to operate on
# @return        StatResult for the path
def stat(path):
  return StatResult(path)

## List the contents of a virtual directory, much like os.listdir().
# @param path    Path to list
# @return        List of names of objects in the directory
#                (excludes '.' and '..')
def listdir(path):
  if path == '/':
    return list(_mountTable.keys())
  else:
    mount, frag = _convertPath(path)
    return mount.listdir(frag)

## Delete a virtual file.
#
# Note: If the virtual file exists in one of the read-only backing
# directories of the mount in which the file is deleted, the file
# will instead appear to revert to the read-only version.
# @param path    Path to delete
def unlink(path):
  os.unlink(resolveWrite(path))

## Create a virtual directory.  Also creates any directories leading
# up to it that are missing (like os.makedirs()).
# @param path    Path at which to create a directory
def mkdir(path):
  os.makedirs(resolveWrite(path))

## Remove a virtual directory.  The directory must be empty.
# @param path    Path to directory to remove
def rmdir(path):
  os.rmdir(resolveWrite(path))

## Check the existence of a virtual object at a given path.
# @param path    Path to check for existence
# @return        True if object exists, False otherwise
def exists(path):
  try:
    stat(path)
    return True
  except OSError, e:
    if e.errno == errno.ENOENT:
      return False
    raise

## Check whether a virtual path represents a file.
# @param path    Path to check for file-ness
# @return        True if it is a file, False otherwise
def isfile(path):
  try:
    return S_ISREG(stat(path).st_mode)
  except OSError, e:
    if e.errno == errno.ENOENT:
      return False
    raise

## Check whether a virtual path represents a directory.
# @param path    Path to check for dir-ness
# @return        True if it is a dir, False otherwise
def isdir(path):
  try:
    return S_ISDIR(stat(path).st_mode)
  except OSError, e:
    if e.errno == errno.ENOENT:
      return False
    raise

_realopen = open
## Open a virtual file, much like the built-in open() function.
# @param path    Path to open
# @param mode    File mode (defaults to 'r')
# @return        File object of the appropriate physical file
def open(path, mode='r'):
  if mode in ('r', 'rb'):
    return _realopen(resolveRead(path), mode)
  else:
    return _realopen(resolveWrite(path), mode)

# TODO: Function to perform all overlay mounts called for by the
# active configuration: /data will become /data overlaid by the
# current theme overlaid by any active mods and /songs will be the
# song folder.  Note that said function is fully intended to be
# called again if said configuration is modified in such a way that
# it changes what should appear in /data or /songs.  Other code
# shouldn't really care if the VFS changes out from under it (the
# testing code might, but that's kind of a special case...) -
# VFS.open() returns real file objects that aren't tied to the
# current VFS state.
#
# There are some decisions that must be made before doing this;
# hence, we're leaving it undone presently.
#
# Note that unless the mount tables are modified directly, /data
# and /userdata are guaranteed to exist and point to the proper
# places: /data contains at least the contents of the main /data
# and is read-only, and /userdata points to the user-specific
# configuration area (%APPDATA%\fofix, ~/Library/Preferences/fofix,
# ~/.fofix, or what-have-you) and is read-write.

if os.name == 'nt':
  # Find the path to Application Data, and do it the Right Way(tm).
  # The APPDATA envvar isn't guaranteed to be reliable.
  # Use ctypes so we don't have to drag in win32com.
  import ctypes
  import ctypes.wintypes
  _appdata = (ctypes.c_char * ctypes.wintypes.MAX_PATH)()
  # [WinSDK]/include/shlobj.h: #define CSIDL_APPDATA 26
  ctypes.windll.shell32.SHGetFolderPathA(None, 26, None, None, _appdata)
  _writePath = os.path.join(_appdata.value, Version.appName())
elif sys.platform == 'darwin':
  _writePath = os.path.expanduser(os.path.join('~', 'Library', 'Preferences', Version.appName()))
else:
  _writePath = os.path.expanduser(os.path.join('~', '.'+Version.appName()))
mountWritable(_writePath, 'userdata')
if not isdir('/userdata'):
  mkdir('/userdata')

if hasattr(sys, 'frozen'):
  _readPath = os.path.abspath('data')
else:
  _readPath = os.path.abspath(os.path.join('..', 'data'))
mount(_readPath, 'data')

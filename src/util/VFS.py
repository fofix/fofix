#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2009-2010 John Stumpo                               #
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
Functions providing a convenient virtual filesystem.

Among other things, this is how themes and mods will be implemented.
Note that B{all} VFS functions use slash-delimited paths, relieving
other code of the need to C{os.path.join()}.  All VFS paths must also
be absolute (i.e. start with a slash) and may not contain "." or "..".

Files or directories may be mounted in the root of the VFS read-only
or read-write.  Mounting multiple things onto the same mountpoint
overlays the newer mount's contents on the old mount's contents, but
read-write mounts always prevail over read-only mounts in the resolution
order.  All write attempts to a given mountpoint go to the most recent
read-write mount on that mountpoint; trying to write to a mountpoint
that has no writable mounts raises C{OSError(EROFS)}.  Modification of
files existing in lower layers but not the most recent writable mount
uses copy-on-write semantics.  There is no way to make something in
a lower layer appear to have been deleted, however.
'''

import Version

import os
import re
import errno
import sys
import shutil
import time
from stat import S_IFDIR, S_ISDIR, S_ISREG
from fnmatch import fnmatch
import sqlite3

_mountTable = {}

class Mount(object):
    '''Implementation of a mount point in the VFS root.'''

    def __init__(self):
        # List of read-only backing directories, in decreasing order of priority.
        self.readOnly = []
        # List of writable backing directories, in decreasing order of priority.
        self.writable = []

    def resolveRead(self, path):
        '''
        Resolve a path to a file that the user wants to read.
        @param path:   Virtual path within this mount
        @return:       Physical path to the file
        @raise OSError(ENOENT): if file does not exist
        '''
        for p in (self.writable + self.readOnly):
            candidate = os.path.join(p, path).rstrip(os.sep)
            if os.path.exists(candidate):
                return candidate
        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT))

    def resolveWrite(self, path):
        '''
        Resolve a path to a file that the user wants to create or modify.
        Copies files to the most recently mounted writable directory if
        necessary.  If a path is returned, it is guaranteed to be in the
        most recently mounted writable directory.
        @param path:   Virtual path within this mount
        @return:       Physical path to the file
        @raise OSError(EROFS): if all mounted directories are read-only
        '''
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

        if not os.path.isdir(os.path.dirname(wpath)):
            os.makedirs(os.path.dirname(wpath))
        if rpath is not None:
            shutil.copy2(rpath, wpath)
        return wpath

    def listdir(self, path):
        '''
        List the contents of a directory within this mountpoint.
        @param path:   Virtual path within this mount to list
        @return:       List of entries (excluding '.' and '..')
        '''
        contents = set()
        for p in (self.writable + self.readOnly):
            candidate = os.path.join(p, path)
            if os.path.isdir(candidate):
                contents.update(os.listdir(candidate))
        return list(contents)


def mount(dir, mountpt):
    '''
    Mount a directory read-only.
    The virtual directory provides the union of the contents of all
    directories mounted on it.
    @param dir:       Directory to mount
    @param mountpt:   Virtual directory to mount it onto
    '''
    if mountpt not in _mountTable:
        _mountTable[mountpt] = Mount()
    _mountTable[mountpt].readOnly.append(dir)


def mountWritable(dir, mountpt):
    '''
    Mount a directory and allow writing.
    The most recent writable-mounted directory on a given
    mountpoint receives all writes made to the mountpoint.
    @param dir:       Directory to mount
    @param mountpt:   Virtual directory to mount it onto
    '''
    if mountpt not in _mountTable:
        _mountTable[mountpt] = Mount()
    _mountTable[mountpt].writable.append(dir)


def _convertPath(path):
    '''
    Validate and convert a VFS path to a mount point and a native path
    fragment suitable for passing to the mount point's methods.
    @param path:  VFS path
    @return:      2-tuple of mount and native path fragment to pass to the mount
    @raise OSError(EINVAL): on syntactically invalid VFS path
    '''
    if re.match('^/[^:\\\\]*$', path) is None or re.match('/\\.\\.?(/|$)', path) is not None:
        raise OSError(errno.EINVAL, os.strerror(errno.EINVAL))
    while '//' in path:
        path = path.replace('//', '/')
    components = path.lstrip('/').split('/')
    if components[0] not in _mountTable:
        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT))
    return _mountTable[components[0]], os.sep.join(components[1:])


def resolveRead(path):
    '''
    Convert a VFS path into a real path that is usable to access an
    already-existing file or directory.
    @param path:    VFS path
    @return:        Real path
    @raise OSError(ENOENT): if path does not exist
    '''
    mount, frag = _convertPath(path)
    return mount.resolveRead(frag)


def resolveWrite(path):
    '''
    Convert a VFS path that the user wishes to write a file to into a real
    writable path.  Copies a file from a read-only area to a read-write area
    if necessary.
    @param path:   VFS path
    @return:       Real path
    '''
    mount, frag = _convertPath(path)
    return mount.resolveWrite(frag)


class StatResult(object):
    '''
    C{stat()} result for an object in the virtual filesystem.
    This was originally a hack to give synthesized C{stat()} results for / so
    things worked right in the test code, but it's left in because if you
    can stat anything else in the VFS, you should be able to stat / too.

    For all practical purposes, this object is compatible with the return type
    of C{os.stat()}.  Fields of the result can be accessed either as attributes
    or via numeric indices.
    '''

    def __init__(self, path):
        '''
        Set the object up with C{os.stat()} results of C{path} or
        synthesized properties if the VFS root is statted.
        @param path:   Path to operate on
        '''
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

    # Implement the sequence protocol (os.stat() returns a tuple-like object)
    def __len__(self):
        return len(self._attrs)

    def __getitem__(self, idx):
        return getattr(self, self._attrs[idx])

    # Show our contents when repr()'d.
    def __repr__(self):
        return str(tuple(self))


def stat(path):
    '''
    Get some properties of the specified path, much like C{os.stat()}.
    @param path:   Path to operate on
    @return:       L{StatResult} for the path
    '''
    return StatResult(path)


def listdir(path):
    '''
    List the contents of a virtual directory, much like C{os.listdir()}.
    @param path:   Path to list
    @return:       List of names of objects in the directory
                   (excludes '.' and '..')
    '''
    if path == '/':
        return list(_mountTable.keys())
    else:
        mount, frag = _convertPath(path)
        return mount.listdir(frag)


def glob(pattern):
    '''
    List object names that match a glob pattern.

    Only the portion after the final slash will be treated as a glob pattern.
    @param pattern: The glob pattern
    @return:        List of matching names
    '''
    rmatch = re.match('^(/(?:.*/)?)(.*?)$', pattern)
    if rmatch is None:
        raise OSError(errno.EINVAL, os.strerror(errno.EINVAL))
    dirname, basename = rmatch.group(1), rmatch.group(2)
    return [dirname + name for name in listdir(dirname) if fnmatch(name, basename)]


def unlink(path):
    '''
    Delete a virtual file.

    Note: If the virtual file exists in one of the read-only backing
    directories of the mount in which the file is deleted, the file
    will instead appear to revert to the read-only version.
    @param path:   Path to delete
    '''
    os.unlink(resolveWrite(path))


def mkdir(path):
    '''
    Create a virtual directory.  Also creates any directories leading
    up to it that are missing (like C{os.makedirs()}).
    @param path:   Path at which to create a directory
    '''
    os.makedirs(resolveWrite(path))


def rmdir(path):
    '''
    Remove a virtual directory.  The directory must be empty.
    @param path:   Path to directory to remove
    '''
    os.rmdir(resolveWrite(path))


def rename(src, dest):
    '''
    Rename or move a virtual object.
    @param src:    Path to rename from
    @param dest:   Path to rename to
    '''
    os.rename(resolveWrite(src), resolveWrite(dest))


def exists(path):
    '''
    Check the existence of a virtual object at a given path.
    @param path:   Path to check for existence
    @return:       True if object exists, False otherwise
    '''
    try:
        stat(path)
        return True
    except OSError, e:
        if e.errno == errno.ENOENT:
            return False
        raise


def isfile(path):
    '''
    Check whether a virtual path represents a file.
    @param path:   Path to check for file-ness
    @return:       True if it is a file, False otherwise
    '''
    try:
        return S_ISREG(stat(path).st_mode)
    except OSError, e:
        if e.errno == errno.ENOENT:
            return False
        raise


def isdir(path):
    '''
    Check whether a virtual path represents a directory.
    @param path:   Path to check for dir-ness
    @return:       True if it is a dir, False otherwise
    '''
    try:
        return S_ISDIR(stat(path).st_mode)
    except OSError, e:
        if e.errno == errno.ENOENT:
            return False
        raise


_realopen = open
def open(path, mode='r'):
    '''
    Open a virtual file, much like the built-in C{open()} function.
    @param path:   Path to open
    @param mode:   File mode
    @return:       File object of the appropriate physical file
    '''
    if mode in ('r', 'rb'):
        return _realopen(resolveRead(path), mode)
    else:
        return _realopen(resolveWrite(path), mode)


def openSqlite3(path):
    '''
    Open a virtual file as a writable SQLite database.
    @param path:  Path to open
    @return:      C{sqlite3.Connection} object for the file
    '''

    # There is a bug in the sqlite3 module's handling of path names containing
    # unicode characters, so work around that by temporarily changing directory
    # so we access the file with just its base name.
    oldcwd = os.getcwd()
    try:
        dbName = resolveWrite(path)
        os.chdir(os.path.dirname(dbName))
        return sqlite3.Connection(os.path.basename(dbName))
    finally:
        os.chdir(oldcwd)

#stump: VFS does this now too; it's just a case of converting stuff to use it
def getWritableResourcePath():
    """
    Returns a path that holds the configuration for the application.
    """
    path = "."
    appname = Version.PROGRAM_UNIXSTYLE_NAME
    if os.name == "posix":
        path = os.path.expanduser("~/." + appname)
        # evilynux - MacOS X, putting config files in the standard folder
        if( os.uname()[0] == "Darwin" ):
            path = os.path.expanduser("~/Library/Preferences/" + appname)
    elif os.name == "nt":
        try:
            path = os.path.join(os.environ["APPDATA"], appname)
        except:
            pass
    try:
        os.mkdir(path)
    except:
        pass
    return path

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
# ~/.fofix, or what-have-you) and is read-write.  /gameroot also
# always points (read-only) to the root of the game installation
# (though please try to avoid using it directly when the data you
# want is available elsewhere in the VFS!)

# Figure out where to map /userdata to.
if os.name == 'nt':
    # Find the path to Application Data, and do it the Right Way(tm).
    # The APPDATA envvar isn't guaranteed to be reliable.
    # Use ctypes so we don't have to drag in win32com.
    import ctypes
    import ctypes.wintypes
    _appdata = (ctypes.c_char * ctypes.wintypes.MAX_PATH)()
    # [WinSDK]/include/shlobj.h: #define CSIDL_APPDATA 26
    ctypes.windll.shell32.SHGetFolderPathA(None, 26, None, None, _appdata)
    _writePath = os.path.join(_appdata.value, Version.PROGRAM_UNIXSTYLE_NAME)
elif sys.platform == 'darwin':
    _writePath = os.path.expanduser(os.path.join('~', 'Library', 'Preferences', Version.PROGRAM_UNIXSTYLE_NAME))
else:
    _writePath = os.path.expanduser(os.path.join('~', '.'+Version.PROGRAM_UNIXSTYLE_NAME))
mountWritable(_writePath, 'userdata')
if not isdir('/userdata'):
    mkdir('/userdata')

# Map /data and /gameroot.
if Version.isWindowsExe():
    _gameRoot = os.path.abspath('.')
else:
    _gameRoot = os.path.abspath('..')
mount(_gameRoot, 'gameroot')
mount(os.path.join(_gameRoot, 'data'), 'data')

#!/usr/bin/python
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

# Allow some testing of the VFS by mounting it in its default state
# as a FUSE filesystem.  There are some limitations, such as only
# supporting one simultaneous open of a given file, but this isn't
# really intended for hard-core use anyway, just simple testing.

import VFS
import fuse
import os
import errno
import stat
import Version

fuse.fuse_python_api = (0, 2)

class VFSFuse(fuse.Fuse):

  def __init__(self, *args, **kw):
    self._openFiles = {}
    fuse.Fuse.__init__(self, *args, **kw)

  def getattr(self, path):
    return VFS.stat(path)

  def readdir(self, path, offset):
    for e in (['.', '..'] + list(VFS.listdir(path)))[offset:]:
      yield fuse.Direntry(e)

  def unlink(self, path):
    VFS.unlink(path)

  def mkdir(self, path, mode):
    VFS.mkdir(path)

  def rmdir(self, path):
    VFS.rmdir(path)

  def rename(self, src, dest):
    VFS.rename(src, dest)

  def mknod(self, path, mode, devno):
    if not stat.S_ISREG(mode):
      return -errno.EINVAL
    VFS.open(path, 'ab').close()

  def utime(self, path, times):
    # We don't want to bloat the VFS code with support for this,
    # but we want to be able to use touch(1) in the test fs without
    # it complaining and still have it do the right thing.
    os.utime(VFS.resolveWrite(path), times)

  def open(self, path, flags, mode=None):
    if path in self._openFiles:
      return -errno.EAGAIN
    access = flags & (os.O_RDONLY | os.O_RDWR | os.O_WRONLY)
    if access == os.O_RDONLY:
      omode = 'rb'
    elif flags & os.O_TRUNC:
      omode = 'w+b'
    elif flags & os.O_APPEND:
      omode = 'a+b'
    else:
      omode = 'r+b'
    self._openFiles[path] = VFS.open(path, omode)

  def release(self, path, flags):
    self._openFiles[path].close()
    del self._openFiles[path]

  def read(self, path, length, offset):
    self._openFiles[path].seek(offset)
    return self._openFiles[path].read(length)

  def write(self, path, buf, offset):
    self._openFiles[path].seek(offset)
    self._openFiles[path].write(buf)
    return len(buf)

  def truncate(self, path, offset):
    f = VFS.open(path, 'ab')
    f.truncate(offset)
    f.close()

if __name__ == '__main__':
  fs = VFSFuse(usage='FoFiX VFS Layer Test Filesystem\n\n' + fuse.Fuse.fusage,
               dash_s_do='setsingle')
  fs.flags = 0
  fs.multithreaded = 0
  fs.parse(errex=1)
  fs.main()

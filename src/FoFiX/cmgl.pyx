# cmgl - context-manager-based OpenGL for Python
# Copyright (C) 2010 John Stumpo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

##@package cmgl
# cmgl - context-managed OpenGL for Python
#
# Yet another Python binding for OpenGL; this one is in the form of
# extension modules for maximum efficiency and uses context managers
# (that is, support for Python 2.5+'s "with" statement) wherever it
# makes sense, and even some places where it doesn't...

cdef extern from "GL/gl.h":
  void glPushMatrix()
  void glPopMatrix()

cdef class cmglPushedMatrix(object):
  def __enter__(self):
    glPushMatrix()
  def __exit__(self, etype, evalue, tb):
    glPopMatrix()

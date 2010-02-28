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
  ctypedef unsigned int GLuint
  ctypedef unsigned int GLsizei
  ctypedef int GLenum

  enum:
    GL_COMPILE

  void glPushMatrix()
  void glPopMatrix()

  GLuint glGenLists(GLsizei)
  void glDeleteLists(GLuint, GLsizei)
  void glNewList(GLuint, GLenum)
  void glEndList()
  void glCallList(GLuint)

## Context manager for a matrix push.
# Inside its context, the active matrix is pushed.
# It is popped upon leaving the context.
cdef class cmglPushedMatrix(object):
  def __enter__(self):
    glPushMatrix()
  def __exit__(self, etype, evalue, tb):
    glPopMatrix()

## Abstraction of a display list.
#
# The list is automatically created and destroyed with the object.
# To compile operations into the list, enter the list's context.
# To call the list, call the object.
cdef class cmglList(object):
  cdef GLuint gl_list

  def __cinit__(self):
    self.gl_list = glGenLists(1)
  def __dealloc__(self):
    glDeleteLists(self.gl_list, 1)

  def __enter__(self):
    glNewList(self.gl_list, GL_COMPILE)
  def __exit__(self, etype, evalue, tb):
    glEndList()

  def __call__(self):
    glCallList(self.gl_list)

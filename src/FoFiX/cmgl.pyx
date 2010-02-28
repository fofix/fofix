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

import numpy
cimport numpy

cdef extern from "GL/gl.h":
  ctypedef int GLint
  ctypedef unsigned int GLuint
  ctypedef unsigned int GLsizei
  ctypedef int GLenum
  ctypedef float GLfloat
  ctypedef void GLvoid

  enum:
    GL_COMPILE
    GL_FLOAT
    GL_VERTEX_ARRAY
    GL_COLOR_ARRAY
    GL_TEXTURE_COORD_ARRAY
    GL_NORMAL_ARRAY

  void glPushMatrix()
  void glPopMatrix()

  GLuint glGenLists(GLsizei)
  void glDeleteLists(GLuint, GLsizei)
  void glNewList(GLuint, GLenum)
  void glEndList()
  void glCallList(GLuint)

  void glVertexPointer(GLint, GLenum, GLsizei, GLvoid*)
  void glColorPointer(GLint, GLenum, GLsizei, GLvoid*)
  void glTexCoordPointer(GLint, GLenum, GLsizei, GLvoid*)
  void glNormalPointer(GLenum, GLsizei, GLvoid*)
  void glEnableClientState(GLenum)
  void glDisableClientState(GLenum)
  void glDrawArrays(GLenum, GLint, GLsizei)

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

## Wrapper for drawing from an arbitrary set of numpy arrays.
def cmglDrawArrays(GLenum mode,
                   numpy.ndarray[numpy.float32_t, ndim=2] vertices,
                   numpy.ndarray[numpy.float32_t, ndim=2] colors=None,
                   numpy.ndarray[numpy.float32_t, ndim=2] texcoords=None,
                   numpy.ndarray[numpy.float32_t, ndim=2] normals=None):
  try:
    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(vertices.shape[1], GL_FLOAT, 0, vertices.data)
    if colors is not None:
      if colors.shape[0] != vertices.shape[0]:
        raise TypeError, 'colors and vertices must be the same length'
      glEnableClientState(GL_COLOR_ARRAY)
      glColorPointer(colors.shape[1], GL_FLOAT, 0, colors.data)
    if texcoords is not None:
      if texcoords.shape[0] != vertices.shape[0]:
        raise TypeError, 'texcoords and vertices must be the same length'
      glEnableClientState(GL_TEXTURE_COORD_ARRAY)
      glTexCoordPointer(texcoords.shape[1], GL_FLOAT, 0, texcoords.data)
    if normals is not None:
      if normals.shape[0] != vertices.shape[0]:
        raise TypeError, 'normals and vertices must be the same length'
      if normals.shape[1] != 3:
        raise TypeError, 'normal vectors must have exactly 3 components'
      glEnableClientState(GL_NORMAL_ARRAY)
      glNormalPointer(GL_FLOAT, 0, texcoords.data)
    glDrawArrays(mode, 0, vertices.shape[0])
  finally:
    glNormalPointer(GL_FLOAT, 0, NULL)
    glTexCoordPointer(4, GL_FLOAT, 0, NULL)
    glColorPointer(4, GL_FLOAT, 0, NULL)
    glVertexPointer(4, GL_FLOAT, 0, NULL)
    glDisableClientState(GL_NORMAL_ARRAY)
    glDisableClientState(GL_TEXTURE_COORD_ARRAY)
    glDisableClientState(GL_COLOR_ARRAY)
    glDisableClientState(GL_VERTEX_ARRAY)

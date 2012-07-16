#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2010 FoFiX Team                                     #
#               2010 John Stumpo                                    #
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
Cython include file for binding to OpenGL
'''

cdef extern from "glwrap.h":
    ctypedef unsigned int GLbitfield
    ctypedef unsigned int GLenum
    ctypedef float GLfloat
    ctypedef int GLint
    ctypedef int GLsizei
    ctypedef unsigned int GLuint
    ctypedef void GLvoid

    enum:
        GL_COLOR_ARRAY
        GL_COMPILE
        GL_FLOAT
        GL_MATRIX_MODE
        GL_MODELVIEW
        GL_NORMAL_ARRAY
        GL_PROJECTION
        GL_QUADS
        GL_TEXTURE_2D
        GL_TEXTURE_COORD_ARRAY
        GL_VERTEX_ARRAY

    void glCallList(GLuint)
    void glColor4f(GLfloat, GLfloat, GLfloat, GLfloat)
    void glColorPointer(GLint, GLenum, GLsizei, GLvoid*)
    void glDeleteLists(GLuint, GLsizei)
    void glDisable(GLenum)
    void glDisableClientState(GLenum)
    void glDrawArrays(GLenum, GLint, GLsizei)
    void glEnable(GLenum)
    void glEnableClientState(GLenum)
    void glEndList()
    GLuint glGenLists(GLsizei)
    void glGetIntegerv(GLenum, GLint*)
    void glLoadIdentity()
    void glMatrixMode(GLenum)
    void glNewList(GLuint, GLenum)
    void glNormalPointer(GLenum, GLsizei, GLvoid*)
    void glPushAttrib(GLbitfield)
    void glPushMatrix()
    void glPopAttrib()
    void glPopMatrix()
    void glTexCoordPointer(GLint, GLenum, GLsizei, GLvoid*)
    void glVertexPointer(GLint, GLenum, GLsizei, GLvoid*)

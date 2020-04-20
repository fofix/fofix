#####################################################################
# -*- coding: utf-8 -*-                                             #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2010 John Stumpo                                    #
#               2020 Linkid                                         #
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

"""
cmgl - context-managed OpenGL for Python

Yet another Python binding for OpenGL, that uses context managers.
"""


from OpenGL import GL as gl


def draw_arrays(mode, vertices, colors=None, texcoords=None):
    """ Draw a triangle

    :param mode: mode to render (triangle, etc.)
    :param vertices: an array of vertex data
    :param colors: an array of colors (optional)
    :param texcoords: an array of texture coordinates (optional)
    """
    # define vertices array
    gl.glVertexPointerf(vertices)
    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

    # define textures array
    if texcoords is not None:
        if texcoords.shape[0] != vertices.shape[0]:
            raise TypeError('Texcoords and vertices must be the same length')
        gl.glTexCoordPointerf(texcoords)
        gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)

    # define colors array
    if colors is not None:
        if colors.shape[0] != vertices.shape[0]:
            raise TypeError('Colors and vertices must be the same length')
        gl.glColorPointerf(colors)
        gl.glEnableClientState(gl.GL_COLOR_ARRAY)

    # draw arrays
    first = 0
    count = vertices.shape[0]
    gl.glDrawArrays(mode, first, count)

    # disable client-side capabilities
    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
    gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
    gl.glDisableClientState(gl.GL_COLOR_ARRAY)


class PushedMatrix():
    """ Context manager for a matrix push.

    Inside its context, the active matrix is pushed.
    It is popped upon leaving the context.
    """

    def __enter__(self):
        gl.glPushMatrix()

    def __exit__(self, etype, evalue, traceback):
        gl.glPopMatrix()


class PushedAttrib():
    """ Context manager for an attribute push.

    Inside its context, the chosen attributes are pushed.
    They are popped upon leaving the context.
    """

    def __init__(self, gl_mask):
        self.gl_mask = gl_mask

    def __enter__(self):
        gl.glPushAttrib(self.gl_mask)

    def __exit__(self, etype, evalue, traceback):
        gl.glPopAttrib()


class MatrixMode():
    """ Context manager for switching the matrix mode.

    Inside its context, the chosen matrix is active.
    It is restored to its original value upon leaving the context.
    """

    def __init__(self, new_mode):
        self.new_mode = new_mode
        self.old_mode = gl. GL_MODELVIEW

    def __enter__(self):
        gl.glGetIntegerv(gl.GL_MATRIX_MODE, self.old_mode)
        gl.glMatrixMode(self.new_mode)

    def __exit__(self, etype, evalue, traceback):
        gl.glMatrixMode(self.old_mode)


class PushedSpecificMatrix():
    """ Context manager for pushing a specific matrix.

    Inside its context, that matrix is pushed, but the active matrix is not changed.
    It is popped upon leaving the context.
    """

    def __init__(self, mode):
        self.gl_mode = mode
        self.old_mode = gl. GL_MODELVIEW

    def __enter__(self):
        gl.glGetIntegerv(gl.GL_MATRIX_MODE, self.old_mode)
        gl.glMatrixMode(self.gl_mode)
        gl.glPushMatrix()
        gl.glMatrixMode(self.old_mode)

    def __exit__(self, etype, evalue, traceback):
        gl.glGetIntegerv(gl.GL_MATRIX_MODE, self.old_mode)
        gl.glMatrixMode(self.gl_mode)
        gl.glPopMatrix()
        gl.glMatrixMode(self.old_mode)


class GList():
    """ Abstraction of a display list.

    The list is automatically created and destroyed with the object.
    To compile operations into the list, enter the list's context.
    To call the list, call the object.
    """

    def __init__(self):
        self.gl_list = gl.glGenLists(1)

    def __del__(self):
        gl.glDeleteLists(self.gl_list, 1)

    def __enter__(self):
        gl.glNewList(self.gl_list, gl.GL_COMPILE)

    def __exit__(self, etype, evalue, traceback):
        gl.glEndList()

    def __call__(self):
        gl.glCallList(self.gl_list)

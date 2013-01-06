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

# First a thin wrapper around VideoPlayer from VideoPlayer.c...

cdef extern from "VideoPlayer.h":
    ctypedef struct CVideoPlayer "VideoPlayer":
        pass

    ctypedef int GQuark
    ctypedef struct GError:
        GQuark domain
        char* message
    GQuark G_FILE_ERROR
    GQuark VIDEO_PLAYER_ERROR
    void g_error_free(GError*)

    CVideoPlayer* video_player_new(char*, GError**)
    void video_player_destroy(CVideoPlayer*)
    void video_player_play(CVideoPlayer*)
    void video_player_pause(CVideoPlayer*)
    bint video_player_advance(CVideoPlayer*, double, GError**)
    bint video_player_bind_frame(CVideoPlayer*, GError**)
    bint video_player_eof(CVideoPlayer*)
    double video_player_aspect_ratio(CVideoPlayer*)

class VideoPlayerError(Exception):
    pass

cdef object raise_from_gerror(GError* err):
    assert err is not NULL
    if err.domain == VIDEO_PLAYER_ERROR:
        exc = VideoPlayerError(err.message)
    elif err.domain == G_FILE_ERROR:
        exc = IOError(err.message)
    else:
        exc = Exception(err.message)
    g_error_free(err)
    raise exc

cdef class VideoPlayer(object):
    cdef CVideoPlayer* player

    def __cinit__(self, char* filename):
        cdef GError* err = NULL
        self.player = video_player_new(filename, &err)
        if self.player is NULL:
            raise_from_gerror(err)

    def __dealloc__(self):
        if self.player is not NULL:
            video_player_destroy(self.player)

    def play(self):
        video_player_play(self.player)

    def pause(self):
        video_player_pause(self.player)

    def advance(self, double newpos):
        cdef GError* err = NULL
        if not video_player_advance(self.player, newpos, &err):
            raise_from_gerror(err)

    def bind_frame(self):
        cdef GError* err = NULL
        if not video_player_bind_frame(self.player, &err):
            raise_from_gerror(err)

    def eof(self):
        return video_player_eof(self.player)

    def aspect_ratio(self):
        return video_player_aspect_ratio(self.player)


# And now, a layer for playing a video.

from View import BackgroundLayer
from Input import KeyListener
import numpy as np
import cmgl

# This is Cython after all, so we may as well directly bind to OpenGL for the video layer implementation.
include "../gl.pxi"

class VideoLayer(BackgroundLayer, KeyListener):
    def __init__(self, engine, filename, mute = False, loop = False, cancellable = False):
        self.engine = engine
        self.filename = filename
        self.mute = mute  # TODO: audio
        self.loop = loop  # TODO: seeking
        self.cancellable = cancellable

        self.finished = False

        self.player = VideoPlayer(self.filename)

    def shown(self):
        if self.cancellable:
            self.engine.input.addKeyListener(self)

    def hidden(self):
        if self.cancellable:
            self.engine.input.removeKeyListener(self)

    def keyPressed(self, key, unicode):
        self.finished = True

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()

    def advance(self, newpos):
        self.player.advance(newpos)

    def restart(self):
        # XXX: do this less hackishly
        del self.player
        self.player = VideoPlayer(self.filename)
        self.player.play()

    def render(self, visibility, topMost):
        screen_aspect_ratio = float(self.engine.view.geometry[2]) / self.engine.view.geometry[3]
        video_aspect_ratio = self.player.aspect_ratio()

        # Figure out the area of the acreen to cover with video.
        if screen_aspect_ratio > video_aspect_ratio:
            width_fraction = video_aspect_ratio / screen_aspect_ratio
            height_fraction = 1.0
        else:
            width_fraction = 1.0
            height_fraction = screen_aspect_ratio / video_aspect_ratio

        self.player.bind_frame()

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Prepare to draw the video over a black rectangle that will fill the rest of the space.
        background_vertices = np.array([[ 1.0,  1.0],
                                        [-1.0,  1.0],
                                        [-1.0, -1.0],
                                        [ 1.0, -1.0]], dtype=np.float32)
        video_vertices = np.array([[ width_fraction,  height_fraction],
                                   [-width_fraction,  height_fraction],
                                   [-width_fraction, -height_fraction],
                                   [ width_fraction, -height_fraction]], dtype=np.float32)
        texcoords = np.array([[1.0, 0.0],
                              [0.0, 0.0],
                              [0.0, 1.0],
                              [1.0, 1.0]], dtype=np.float32)

        # The black rectangle.
        glColor4f(0.0, 0.0, 0.0, 1.0)
        cmgl.drawArrays(GL_QUADS, vertices=background_vertices)

        # The actual video.
        glEnable(GL_TEXTURE_2D)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        cmgl.drawArrays(GL_QUADS, vertices=video_vertices, texcoords=texcoords)
        glDisable(GL_TEXTURE_2D)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        if self.player.eof():
            if self.loop:
                self.restart()
            else:
                self.finished = True

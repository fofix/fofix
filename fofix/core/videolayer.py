#####################################################################
# -*- coding: utf-8 -*-                                             #
#                                                                   #
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2010 John Stumpo                                    #
#               2010-2020 FoFiX Team                                #
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

""" A layer for playing a video """


import numpy as np
from OpenGL import GL as gl
from videoplayer._VideoPlayer import VideoPlayer
from videoplayer._VideoPlayer import VideoPlayerError

from fofix.core.View import BackgroundLayer
from fofix.core.Input import KeyListener
from fofix.core import cmgl


class VideoLayer(BackgroundLayer, KeyListener):

    def __init__(self, engine, filename, mute=False, loop=False, cancellable=False):
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

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()

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
        gl.glColor4f(0.0, 0.0, 0.0, 1.0)
        cmgl.draw_arrays(gl.GL_QUADS, vertices=background_vertices)

        # The actual video.
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        cmgl.draw_arrays(gl.GL_QUADS, vertices=video_vertices, texcoords=texcoords)
        gl.glDisable(gl.GL_TEXTURE_2D)

        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)

        if self.player.eof():
            if self.loop:
                self.restart()
            else:
                self.finished = True

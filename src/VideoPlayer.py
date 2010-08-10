#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#####################################################################
# Video Playback Layer for FoFiX                                    #
# Copyright (C) 2009 Pascal Giard <evilynux@gmail.com>              #
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
import os
import sys

# Twiddle the appropriate envvars under Windows so we can load gstreamer
# directly from [FoFiX root]/gstreamer and not have the ugliness of
# requiring the user to install and configure it separately...
if os.name == 'nt':
  if hasattr(sys, 'frozen'):
    _gstpath = 'gstreamer'
  else:
    _gstpath = os.path.join('..', 'gstreamer')
  if os.path.isdir(_gstpath):
    os.environ['PATH'] = os.path.abspath(os.path.join(_gstpath, 'bin')) + os.pathsep + os.environ['PATH']
    os.environ['GST_PLUGIN_PATH'] = os.path.abspath(os.path.join(_gstpath, 'lib', 'gstreamer-0.10'))

# Almighty GStreamer
import gobject
import pygst
pygst.require('0.10')
import gst
from gst.extend import discoverer # Video property detection

import pygame

from OpenGL.GL import *
from OpenGL.GLU import *
# Array-based drawing
from numpy import array, float32

from FoFiX.cmgl import *

from View import View, BackgroundLayer
import Log
from Texture import Texture

# Simple video player
class VideoPlayer(BackgroundLayer):
  def __init__(self, framerate, vidSource, (winWidth, winHeight) = (None, None), mute = False, loop = False, startTime = None, endTime = None):
    self.updated = False
    self.videoList = None
    self.videoTex = None
    self.videoBuffer = None
    self.videoSrc = vidSource
    self.mute = mute
    self.loop = loop
    self.startTime = startTime
    self.endTime = endTime
    if winWidth is not None and winHeight is not None:
      self.winWidth, self.winHeight = winWidth, winHeight
    else: # default
      self.winWidth, self.winHeight = (640, 480)
      Log.warn("VideoPlayer: No resolution specified (default %dx%d)" %
               (self.winWidth, self.winHeight))
    self.vidWidth, self.vidHeight = -1, -1
    self.fps = framerate
    self.clock = pygame.time.Clock()
    self.paused = False
    self.finished = False
    self.discovered = False
    self.timeFormat = gst.Format(gst.FORMAT_TIME)

    self.loadVideo(vidSource) # Load the video

  # Load a new video:
  # 1) Detect video resolution
  # 2) Setup OpenGL texture
  # 3) Setup GStreamer pipeline
  def loadVideo(self, vidSource):
    Log.debug("Attempting to load video: %s" % self.videoSrc)
    if not os.path.exists(vidSource):
      Log.error("Video %s does not exist!" % vidSource)
    self.videoSrc = vidSource
    d = discoverer.Discoverer(self.videoSrc)
    d.connect('discovered', self.videoDiscover)
    d.discover()
    gobject.threads_init() # Start C threads
    while not self.discovered:
      # Force C threads iteration
      gobject.MainLoop().get_context().iteration(True)
    if not self.validFile:
      Log.error("Invalid video file: %s\n" % self.videoSrc)
      return False
    self.textureSetup()
    self.videoSetup()
    return True

  # Use GStreamer's video discoverer to autodetect video properties
  def videoDiscover(self, d, isMedia):
    self.validFile = True
    if isMedia and d.is_video:
      self.vidWidth, self.vidHeight = d.videowidth, d.videoheight
      # Force mute if no sound track is available or
      # else you'll get nothing but a black screen!
      if not d.is_audio and not self.mute:
        Log.warn("Video has no sound ==> forcing mute.")
        self.mute = True
    else:
      self.validFile = False

    self.discovered = True

  def textureSetup(self):
    if not self.validFile:
      return

    self.videoTex = Texture(useMipmaps=False)
    self.videoBuffer = '\x00\x00\x00' * self.vidWidth * self.vidHeight
    self.updated = True
    self.textureUpdate()

    # Resize video (polygon) to respect resolution ratio
    # (The math is actually simple, take the time to draw it down if required)
    winRes = float(self.winWidth)/float(self.winHeight)
    vidRes = float(self.vidWidth)/float(self.vidHeight)
    vtxX = 1.0
    vtxY = 1.0
    if winRes > vidRes:
      r = float(self.winHeight)/float(self.vidHeight)
      vtxX = 1.0 - abs(self.winWidth-r*self.vidWidth) / (float(self.winWidth))
    elif winRes < vidRes:
      r = float(self.winWidth)/float(self.vidWidth)
      vtxY = 1.0 - abs(self.winHeight-r*self.vidHeight) / (float(self.winHeight))

    # Vertices
    videoVtx = array([[-vtxX,  vtxY],
                      [ vtxX, -vtxY],
                      [ vtxX,  vtxY],
                      [-vtxX,  vtxY],
                      [-vtxX, -vtxY],
                      [ vtxX, -vtxY]], dtype=float32)
    backVtx =  array([[-1.0,  1.0],
                      [ 1.0, -1.0],
                      [ 1.0,  1.0],
                      [-1.0,  1.0],
                      [-1.0, -1.0],
                      [ 1.0, -1.0]], dtype=float32)
    # Texture coordinates
    videoTex = array([[0.0,                   self.videoTex.size[1]],
                      [self.videoTex.size[0], 0.0],
                      [self.videoTex.size[0], self.videoTex.size[1]],
                      [0.0,                   self.videoTex.size[1]],
                      [0.0,                   0.0],
                      [self.videoTex.size[0], 0.0]], dtype=float32)

    # Create a compiled OpenGL call list and do array-based drawing
    # Could have used GL_QUADS but IIRC triangles are recommended
    self.videoList = cmglList()
    with self.videoList:
      # Draw borders where video aspect is different than specified width/height
      glColor3f(0., 0., 0.)
      cmglDrawArrays(GL_TRIANGLE_STRIP, vertices=backVtx)
      # Draw video
      glEnable(GL_TEXTURE_2D)
      glColor3f(1., 1., 1.)
      cmglDrawArrays(GL_TRIANGLE_STRIP, vertices=videoVtx, texcoords=videoTex)
      glDisable(GL_TEXTURE_2D)

  # Setup GStreamer's pipeline
  # Note: playbin2 seems also suitable, we might want to experiment with it
  #       if decodebin is proven problematic
  def videoSetup(self):
    if self.startTime is not None or self.endTime is not None:
      self.setTime = True
    else:
      self.setTime = False
    if self.startTime is not None:
      self.startNs = self.startTime * 1000000 # From ms to ns
    else:
      self.startNs = 0
    if self.endTime is not None:
      self.endNs = self.endTime * 1000000
    else:
      self.endNs = -1

    with_audio = ""
    if not self.mute:
      with_audio = "! queue ! audioconvert ! audiorate ! audioresample ! autoaudiosink"
    s = "filesrc name=input ! decodebin2 name=dbin dbin. ! ffmpegcolorspace ! video/x-raw-rgb ! fakesink name=output signal-handoffs=true sync=true dbin. %s" % with_audio
    self.player = gst.parse_launch(s)
    self.input  = self.player.get_by_name('input')
    self.fakeSink = self.player.get_by_name('output')
    self.input.set_property("location", self.videoSrc)
    self.fakeSink.connect ("handoff", self.newFrame)

    # Catch the end of file as well as errors
    # FIXME:
    #  Messages are sent if i use the following in run():
    #   gobject.MainLoop().get_context().iteration(True)
    #  BUT the main python thread then freezes after ~5 seconds...
    #  unless we use gobject.idle_add(self.player.elements)
    bus = self.player.get_bus()
    bus.add_signal_watch()
    bus.enable_sync_message_emission()
    bus.connect("message", self.onMessage)
    # Required to prevent the main python thread from freezing, why?!
    # Thanks to max26199 for finding this!
    gobject.idle_add(self.player.elements)

  # Handle bus event e.g. end of video or unsupported formats/codecs
  def onMessage(self, bus, message):
    type = message.type
#    print "Message %s" % type
    # End of video
    if type == gst.MESSAGE_EOS:
      if self.loop:
        # Seek back to start time and set end time
        self.player.seek(1, self.timeFormat, gst.SEEK_FLAG_FLUSH,
                         gst.SEEK_TYPE_SET, self.startNs,
                         gst.SEEK_TYPE_SET, self.endNs)
      else:
        self.player.set_state(gst.STATE_NULL)
        self.finished = True
    # Error
    elif type == gst.MESSAGE_ERROR:
      err = message.parse_error()
      Log.error("GStreamer error: %s" % err)
      self.player.set_state(gst.STATE_NULL)
      self.finished = True
#      raise NameError("GStreamer error: %s" % err)
    elif type == gst.MESSAGE_WARNING:
      warning, debug = message.parse_warning()
      Log.warn("GStreamer warning: %s\n(---) %s" % (warning, debug))
    elif type == gst.MESSAGE_STATE_CHANGED:
      oldstate, newstate, pending = message.parse_state_changed()
#       Log.debug("GStreamer state: %s" % newstate)
      if newstate == gst.STATE_READY:
        # Set start and end time
        if self.setTime:
          # Note: Weirdly, contrary to loop logic, i need a wait here!
          #       Moreover, at the beginning, we're ready more than once!?
          pygame.time.wait(1000) # Why, oh why... isn't ready, READY?!
          self.player.seek(1, self.timeFormat, gst.SEEK_FLAG_FLUSH,
                           gst.SEEK_TYPE_SET, self.startNs,
                           gst.SEEK_TYPE_SET, self.endNs)
          self.setTime = False # Execute just once

  # Handle new video frames coming from the decoder
  def newFrame(self, sink, buffer, pad):
    self.videoBuffer = buffer
    self.updated = True

  def textureUpdate(self):
    if self.updated:
      img = pygame.image.frombuffer(self.videoBuffer,
                                    (self.vidWidth, self.vidHeight),
                                    'RGB')
      self.videoTex.loadSurface(img)
      self.videoTex.setFilter()
      self.updated = False

  def shown(self):
    gobject.threads_init()

  def hidden(self):
    self.player.set_state(gst.STATE_NULL)

  def run(self, ticks = None):
    if not self.validFile:
      return
    if self.paused == True:
      self.player.set_state(gst.STATE_PAUSED)
    else:
      self.player.set_state(gst.STATE_PLAYING)
      self.finished = False
    gobject.MainLoop().get_context().iteration(True)
    self.clock.tick(self.fps)

  # Render texture to polygon
  # Note: Both visibility and topMost are currently unused.
  def render(self, visibility = 1.0, topMost = False):
    try:
      self.textureUpdate()
      # Save and clear both transformation matrices
      glMatrixMode(GL_PROJECTION)
      glPushMatrix()
      glLoadIdentity()
      glMatrixMode(GL_MODELVIEW)
      glPushMatrix()
      glLoadIdentity()
      # Draw the polygon and apply texture
      self.videoTex.bind()
      self.videoList()
      # Restore both transformation matrices
      glPopMatrix()
      glMatrixMode(GL_PROJECTION)
      glPopMatrix()
    except Exception:
      Log.error("Error attempting to play video")

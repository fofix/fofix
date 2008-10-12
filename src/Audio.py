#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
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

import pygame
import Log
import time
from Task import Task

try:
  import ogg.vorbis
except ImportError:
  Log.warn("PyOGG not found. OGG files will be fully decoded prior to playing; expect absurd memory usage.")
  ogg = None

class Audio:
  def pre_open(self, frequency = 22050, bits = 16, stereo = True, bufferSize = 1024):
    pygame.mixer.pre_init(frequency, -bits, stereo and 2 or 1, bufferSize)
    return True

  def open(self, frequency = 22050, bits = 16, stereo = True, bufferSize = 1024):
    try:
      pygame.mixer.quit()
    except:
      pass

    try:
      pygame.mixer.init(frequency, -bits, stereo and 2 or 1, bufferSize)
    except:
      Log.warn("Audio setup failed. Trying with default configuration.")
      pygame.mixer.init()

    Log.debug("Audio configuration: %s" % str(pygame.mixer.get_init()))

    #myfingershurt: ensuring we have enough audio channels!
    pygame.mixer.set_num_channels(10)

    return True

  #myfingershurt:
  def findChannel(self):
    return pygame.mixer.find_channel()


  def getChannelCount(self):
    return pygame.mixer.get_num_channels()

  def getChannel(self, n):
    return Channel(n)

  def close(self):
    pygame.mixer.quit()

  def pause(self):
    pygame.mixer.pause()

  def unpause(self):
    pygame.mixer.unpause()

class Music(object):
  def __init__(self, fileName):
    pygame.mixer.music.load(fileName)

  @staticmethod
  def setEndEvent(event):
    pygame.mixer.music.set_endevent(event)

  def play(self, loops = -1, pos = 0.0):
    pygame.mixer.music.play(loops, pos)

  def stop(self):
    pygame.mixer.music.stop()

  def rewind(self):
    pygame.mixer.music.rewind()

  def pause(self):
    pygame.mixer.music.pause()

  def unpause(self):
    pygame.mixer.music.unpause()

  def setVolume(self, volume):
    pygame.mixer.music.set_volume(volume)

  def fadeout(self, time):
    pygame.mixer.music.fadeout(time)

  def isPlaying(self):
    return pygame.mixer.music.get_busy()

  def getPosition(self):
    return pygame.mixer.music.get_pos()

class Channel(object):
  def __init__(self, id):
    self.channel = pygame.mixer.Channel(id)

  def play(self, sound):
    self.channel.play(sound.sound)

  def stop(self):
    self.channel.stop()

  def setVolume(self, volume):
    self.channel.set_volume(volume)

  def fadeout(self, time):
    self.channel.fadeout(time)

class Sound(object):
  def __init__(self, fileName):
    self.sound   = pygame.mixer.Sound(fileName)

  def isPlaying(self):  #MFH - adding function to check if sound is playing
    return self.sound.get_num_channels()

  def play(self, loops = 0):
    self.sound.play(loops)

  def stop(self):
    self.sound.stop()

  def setVolume(self, volume):
    self.sound.set_volume(volume)

  def fadeout(self, time):
    self.sound.fadeout(time)

if ogg:
  import struct
  # Must use Numeric instead of numpy, since PyGame 1.7.1 is not compatible with the former
  import Numeric

  class OggStream(object):
    def __init__(self, inputFileName):
      self.file = ogg.vorbis.VorbisFile(inputFileName)

    def read(self, bytes = 4096):
      (data, bytes, bit) = self.file.read(bytes)
      return data[:bytes]

  class StreamingOggSound(Sound, Task):
    def __init__(self, engine, channel, fileName):
      Task.__init__(self)
      self.engine       = engine
      self.fileName     = fileName
      self.channel      = channel.channel
      self.playing      = False
      self.bufferSize   = 1024 * 64
      self.bufferCount  = 8
      self.volume       = 1.0

        #myfingershurt: buffer is 2D array (one D for each channel) of 16-bit UNSIGNED integers / samples
        #  2*1024*64 = 131072 samples per channel
      self.buffer       = Numeric.zeros((2 * self.bufferSize, 2), typecode = "s")   #myfingershurt: typecode s = short = int16

      self.decodingRate = 4
      self._reset()

    def _reset(self):
      self.stream        = OggStream(self.fileName)

        #myfingershurt: 2D buffer (L,R) of 16-bit unsigned integer samples, each channel 65536 samples long
        #.... buffersIn = a list of 9 of these.
      self.buffersIn     = [pygame.sndarray.make_sound(Numeric.zeros((self.bufferSize, 2), typecode = "s")) for i in range(self.bufferCount + 1)]

      self.buffersOut    = []
      self.buffersBusy   = []
      self.bufferPos     = 0
      self.done          = False
      self.lastQueueTime = time.time()

      while len(self.buffersOut) < self.bufferCount and not self.done:
        #myfingershurt: while there are less than 8 sets of 65k sample 2 channel buffers in the buffersOut list,
        # continue to decode and fill them.
        self._produceSoundBuffers()

    def __del__(self):
      self.engine.removeTask(self)

    def play(self):
      if self.playing:
        return

      self.engine.addTask(self, synchronized = False)
      self.playing = True

      while len(self.buffersOut) < self.bufferCount and not self.done:
        #myfingershurt: while there are less than 8 sets of 65k sample 2 channel buffers in the buffersOut list,
        # continue to decode and fill them.
        self._produceSoundBuffers()

      
      #once all 8 output buffers are filled, play the first one.
      self.channel.play(self.buffersOut.pop())

    def stop(self):
      self.playing = False
      self.channel.stop()
      self.engine.removeTask(self)
      self._reset()

    def setVolume(self, volume):
      self.volume = volume
      #myfingershurt: apply volume changes IMMEDIATELY:
      self.channel.set_volume(self.volume)

    def fadeout(self, time):
      self.stop()

    def _decodeStream(self):
      # No available buffers to fill?
      if not self.buffersIn or self.done:
        return

      data = self.stream.read()

      if not data:
        self.done = True
      else:
        data = struct.unpack("%dh" % (len(data) / 2), data)
        samples = len(data) / 2
        self.buffer[self.bufferPos:self.bufferPos + samples, 0] = data[0::2]
        self.buffer[self.bufferPos:self.bufferPos + samples, 1] = data[1::2]
        self.bufferPos += samples

      # If we have at least one full buffer decode, claim a buffer and copy the
      # data over to it.
      if self.bufferPos >= self.bufferSize or (self.done and self.bufferPos):
        # Claim the sound buffer and copy the data
        if self.bufferPos < self.bufferSize:
          self.buffer[self.bufferPos:]  = 0
        soundBuffer = self.buffersIn.pop()
        pygame.sndarray.samples(soundBuffer)[:] = self.buffer[0:self.bufferSize]

        # Discard the copied sound data
        n = max(0, self.bufferPos - self.bufferSize)
        self.buffer[0:n] = self.buffer[self.bufferSize:self.bufferSize+n]
        self.bufferPos   = n

        return soundBuffer

    def _produceSoundBuffers(self):
      # Decode enough that we have at least one full sound buffer
      # ready in the queue if possible
      while not self.done:
        for i in xrange(self.decodingRate):
          soundBuffer = self._decodeStream()
          if soundBuffer:
            self.buffersOut.insert(0, soundBuffer)
        if self.buffersOut:
          break

    def run(self, ticks):
      if not self.playing:
        return

      #myfingershurt: this is now done directly when called.
      #self.channel.set_volume(self.volume)

      if len(self.buffersOut) < self.bufferCount:
        self._produceSoundBuffers()

      if not self.channel.get_queue() and self.buffersOut:
        # Queue one decoded sound buffer and mark the previously played buffer as free
        soundBuffer = self.buffersOut.pop()
        self.buffersBusy.insert(0, soundBuffer)
        self.lastQueueTime = time.time()
        self.channel.queue(soundBuffer)
        if len(self.buffersBusy) > 2:
          self.buffersIn.insert(0, self.buffersBusy.pop())
      
      if not self.buffersOut and self.done and time.time() - self.lastQueueTime > 4:
        self.stop()

class StreamingSound(Sound, Task):
  def __init__(self, engine, channel, fileName):
    Task.__init__(self)
    Sound.__init__(self, fileName)
    self.channel = channel

  def __new__(cls, engine, channel, fileName):
    frequency, format, stereo = pygame.mixer.get_init()
    if fileName.lower().endswith(".ogg"):
      if frequency == 44100 and format == -16 and stereo:
        return StreamingOggSound(engine, channel, fileName)
      else:
        Log.warn("Audio settings must match stereo 16 bits at 44100 Hz in order to stream OGG files.")
    return super(StreamingSound, cls).__new__(cls, engine, channel, fileName)

  def play(self):
    self.channel.play(self)

  def stop(self):
    Sound.stop(self)
    self.channel.stop()

  def setVolume(self, volume):
    Sound.setVolume(self, volume)
    self.channel.setVolume(volume)

  def fadeout(self, time):
    Sound.fadeout(self, time)
    self.channel.fadeout(time)


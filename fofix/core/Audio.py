#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
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
import numpy as np

from fofix.core import Log
from fofix.core.Task import Task
from fofix.core.MixStream import VorbisFileMixStream

#stump: get around some strangeness in pygame when py2exe'd...
if not hasattr(pygame.mixer, 'music'):
    import sys
    __import__('pygame.mixer_music')
    pygame.mixer.music = sys.modules['pygame.mixer_music']


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
        try:
            pygame.mixer.quit()
        except:
            pass

    def pause(self):
        pygame.mixer.pause()

    def unpause(self):
        pygame.mixer.unpause()

class Music(object):
    def __init__(self, fileName):
        pygame.mixer.music.load(fileName)

    @staticmethod
    def setEndEvent(event = None):
        if event:
            pygame.mixer.music.set_endevent(event)
        else:
            pygame.mixer.music.set_endevent()   #MFH - to set NO event.

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
        self.id = id

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


#stump: mic passthrough
class MicrophonePassthroughStream(Sound, Task):
    def __init__(self, engine, mic):
        Task.__init__(self)
        self.engine = engine
        self.channel = None
        self.mic = mic
        self.playing = False
        self.volume = 1.0
    def __del__(self):
        self.stop()
    def play(self):
        if not self.playing:
            self.engine.addTask(self)
            self.playing = True
    def stop(self):
        if self.playing:
            self.channel.stop()
            self.engine.removeTask(self)
            self.playing = False
    def setVolume(self, vol):
        self.volume = vol
    def run(self, ticks):
        chunk = ''.join(self.mic.passthroughQueue)
        self.mic.passthroughQueue = []
        if chunk == '':
            return
        data = np.frombuffer(chunk, dtype=np.float32) * 32767.0
        playbuf = np.zeros((len(data), 2), dtype=np.int16)
        playbuf[:, 0] = data
        playbuf[:, 1] = data
        snd = pygame.mixer.Sound(buffer(playbuf))
        if self.channel is None or not self.channel.get_busy():
            self.channel = snd.play()
        else:
            self.channel.queue(snd)
        self.channel.set_volume(self.volume)


class StreamingSound(object):
    def __init__(self, channel, fileName):
        self._mixstream = VorbisFileMixStream(fileName)
        self._channel = channel

    def play(self):
        self._mixstream.play(self._channel.id)

    def stop(self):
        self._mixstream.stop()
        self._channel.stop()

    def setVolume(self, volume):
        self._channel.setVolume(volume)

    def isPlaying(self):
        return self._mixstream.is_playing()

    def fadeout(self, time):
        # TODO
        self.stop()

    def getPosition(self):
        return self._mixstream.get_position()

    def setPosition(self, position):
        return self._mixstream.seek(position)

    def setPitchBendSemitones(self, semitones):
        self._mixstream.set_pitch_semitones(semitones)

    def setSpeed(self, factor):
        self._mixstream.set_speed(factor)

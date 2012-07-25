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
import Log
import struct
from Task import Task
import Config
import OggStreamer

#stump: check for pitch bending support
try:
    import pygame.pitchbend
    pitchBendSupported = True
    if not hasattr(pygame.pitchbend, 'ALL'):
        Log.warn("Your pitchbend module is too old; upgrade it to r7 or higher for pitch bending to work.")
        pitchBendSupported = False
except ImportError:
    Log.warn("Pitch bending is not supported; install john.stumpo's pitchbend module (r7 or higher) if you want it.")
    pitchBendSupported = False

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

    def isMixerInit(self):
        return pygame.mixer.get_init()

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
        self.pausePos = 0.0
        self.isPause = False
        self.toUnpause = False
        self.buffersize = Config.get("audio","buffersize")

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
        self.pausePos = pygame.mixer.music.get_pos()
        self.isPause = True

    def unpause(self):
        self.isPause = False
        pygame.mixer.music.unpause()

    def setVolume(self, volume):
        pygame.mixer.music.set_volume(volume)

    #stump: pitch bending
    # SDL_mixer doesn't support callback processing of the music stream.
    # Thus, as a workaround, we must bend the whole output.
    def setPitchBend(self, factor):
        pygame.pitchbend.start(pygame.pitchbend.ALL)
        pygame.pitchbend.setFactor(pygame.pitchbend.ALL, factor)

    def stopPitchBend(self):
        pygame.pitchbend.stop(pygame.pitchbend.ALL)

    def fadeout(self, time):
        pygame.mixer.music.fadeout(time)

    def isPlaying(self):
        #MFH - gotta catch case when mixer not initialized yet...
        try:
            busy = pygame.mixer.music.get_busy()
        except Exception:
            busy = True
        return busy

    def getPosition(self):
        if self.isPause:
            self.toUnpause = True
            return self.pausePos
        elif self.toUnpause:
            if pygame.mixer.music.get_pos() < (self.pausePos + 60 + (self.buffersize/32)): #this should technically be buffersize*1000/samplerate; 32 keeps it integer, 60 allows for processing time
                self.toUnpause = False
                return pygame.mixer.music.get_pos()
            else:
                return self.pausePos
        else:
            return pygame.mixer.music.get_pos()

class Channel(object):
    def __init__(self, id):
        self.channel = pygame.mixer.Channel(id)
        self.id = id

    def __del__(self):
        if pitchBendSupported:
            pygame.pitchbend.stop(self.id)

    def play(self, sound):
        self.channel.play(sound.sound)

    def stop(self):
        self.channel.stop()
        if pitchBendSupported:
            pygame.pitchbend.stop(self.id)

    def setVolume(self, volume):
        self.channel.set_volume(volume)

    def fadeout(self, time):
        self.channel.fadeout(time)

    #stump: pitch bending
    def setPitchBend(self, factor):
        pygame.pitchbend.start(self.id)
        pygame.pitchbend.setFactor(self.id, factor)

    def stopPitchBend(self):
        pygame.pitchbend.stop(self.id)

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

if tuple(int(i) for i in pygame.__version__[:5].split('.')) < (1, 9, 0):
    # Must use Numeric instead of numpy, since PyGame 1.7.1 is
    # not compatible with the latter, and 1.8.x isn't either (though it claims to be).
    import Numeric
    def zeros(size):
        return Numeric.zeros(size, typecode='s')   #myfingershurt: typecode s = short = int16
else:
    import numpy as np
    def zeros(size):
        return np.zeros(size, dtype='h')

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
            self.engine.addTask(self, synchronized=False)
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
        samples = len(chunk)/4
        data = tuple(int(s * 32767) for s in struct.unpack('%df' % samples, chunk))
        playbuf = zeros((samples, 2))
        playbuf[:, 0] = data
        playbuf[:, 1] = data
        snd = pygame.sndarray.make_sound(playbuf)
        if self.channel is None or not self.channel.get_busy():
            self.channel = snd.play()
        else:
            self.channel.queue(snd)
        self.channel.set_volume(self.volume)


class StreamingSound(Sound, Task):
    def __init__(self, engine, channel, fileName):
        Task.__init__(self)
        Sound.__init__(self, fileName)
        self.channel = channel

    def __new__(cls, engine, channel, fileName):
        return OggStreamer.StreamingOggSound(channel.id, fileName)

    def play(self):
        self.channel.play(self)

    def stop(self):
        Sound.stop(self)
        self.channel.stop()

    def setVolume(self, volume):
        Sound.setVolume(self, volume)
        self.channel.setVolume(volume)

    def streamIsPlaying(self):  #MFH - adding function to check if sound is playing
        return Sound.get_num_channels()


    def fadeout(self, time):
        Sound.fadeout(self, time)
        self.channel.fadeout(time)

    #stump: pitch bending
    def setPitchBend(self, factor):
        self.channel.setPitchBend(factor)

    def stopPitchBend(self):
        self.channel.stopPitchBend()

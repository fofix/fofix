#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2009 Team FoFiX                                     #
#               2009 John Stumpo                                    #
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

import Log
import Audio
import math
import numpy as np

try:
  import pyaudio
  import pypitch
  supported = True
except ImportError:
  Log.warn('Missing pyaudio or pypitch - microphone support will not be possible')
  supported = False

from Task import Task
from Language import _

if supported:
  pa = pyaudio.PyAudio()

  # Precompute these in the interest of saving CPU time in the note analysis loop
  LN_2 = math.log(2.0)
  LN_440 = math.log(440.0)

  #stump: return dictionary mapping indices to device names
  # -1 is magic for the default device and will be replaced by None when actually opening the mic.
  def getAvailableMics():
    result = {-1: _('[Default Microphone]')}
    for devnum in range(pa.get_device_count()):
      devinfo = pa.get_device_info_by_index(devnum)
      if devinfo['maxInputChannels'] > 0:
        result[devnum] = devinfo['name']
    return result

  class Microphone(Task):
    def __init__(self, engine, controlnum, samprate=44100):
      Task.__init__(self)
      self.engine = engine
      self.controlnum = controlnum
      devnum = self.engine.input.controls.micDevice[controlnum]
      if devnum == -1:
        devnum = None
        self.devname = pa.get_default_input_device_info()['name']
      else:
        self.devname = pa.get_device_info_by_index(devnum)['name']
      self.mic = pa.open(samprate, 1, pyaudio.paFloat32, input=True, input_device_index=devnum, start=False)
      self.analyzer = pypitch.Analyzer(samprate)
      self.mic_started = False
      self.lastPeak    = 0
      self.detectTaps  = True
      self.tapStatus   = False
      self.tapThreshold = -self.engine.input.controls.micTapSensitivity[controlnum]
      self.passthroughQueue = []
      passthroughVolume = self.engine.input.controls.micPassthroughVolume[controlnum]
      if passthroughVolume > 0.0:
        Log.debug('Microphone: creating passthrough stream at %d%% volume' % round(passthroughVolume * 100))
        self.passthroughStream = Audio.MicrophonePassthroughStream(engine, self)
        self.passthroughStream.setVolume(passthroughVolume)
      else:
        Log.debug('Microphone: not creating passthrough stream')
        self.passthroughStream = None

    def __del__(self):
      self.stop()
      self.mic.close()

    def start(self):
      if not self.mic_started:
        self.mic_started = True
        self.mic.start_stream()
        self.engine.addTask(self, synchronized=False)
        Log.debug('Microphone: started %s' % self.devname)
        if self.passthroughStream is not None:
          Log.debug('Microphone: starting passthrough stream')
          self.passthroughStream.play()

    def stop(self):
      if self.mic_started:
        if self.passthroughStream is not None:
          Log.debug('Microphone: stopping passthrough stream')
          self.passthroughStream.stop()
        self.engine.removeTask(self)
        self.mic.stop_stream()
        self.mic_started = False
        Log.debug('Microphone: stopped %s' % self.devname)

    # Called by the Task machinery: pump the mic and shove the data through the analyzer.
    def run(self, ticks):
      while self.mic.get_read_available() > 1024:
        try:
          chunk = self.mic.read(1024)
        except IOError, e:
          if e.args[1] == pyaudio.paInputOverflowed:
            Log.notice('Microphone: ignoring input buffer overflow')
            chunk = '\x00' * 4096
          else:
            raise
        if self.passthroughStream is not None:
          self.passthroughQueue.append(chunk)
        self.analyzer.input(np.frombuffer(chunk, dtype=np.float32))
        self.analyzer.process()
        pk = self.analyzer.getPeak()
        if self.detectTaps:
          if pk > self.tapThreshold and pk > self.lastPeak + 5.0:
            self.tapStatus = True
        self.lastPeak = pk

    # Get the amplitude (in dB) of the peak of the most recent input window.
    def getPeak(self):
      return self.analyzer.getPeak()

    # Get the microphone tap status.
    # When a tap occurs, it is remembered until this function is called.
    def getTap(self):
      retval = self.tapStatus
      self.tapStatus = False
      return retval
    
    def getFormants(self):
      return self.analyzer.getFormants()
    
    # Get the note currently being sung.
    # Returns None if there isn't one or a pypitch.Tone object if there is.
    def getTone(self):
      return self.analyzer.findTone()
    
    # Get the note currently being sung, as an integer number of semitones above A.
    # The frequency is rounded to the nearest semitone, then shifted by octaves until
    # the result is between 0 and 11 (inclusive).  Returns None is no note is being sung.
    def getSemitones(self):
      tone = self.analyzer.findTone()
      if tone is None:
        return tone
      return int(round((math.log(tone.freq) - LN_440) * 12.0 / LN_2) % 12)

    # Work out how accurately the note (passed in as a MIDI note number) is being
    # sung.  Return a float in the range [-6.0, 6.0] representing the number of
    # semitones difference there is from the nearest occurrence of the note.  The
    # octave doesn't matter.  Or return None if there's no note being sung.
    def getDeviation(self, midiNote):
      tone = self.analyzer.findTone()
      if tone is None:
        return tone

      # Convert to semitones from A-440.
      semitonesFromA440 = (math.log(tone.freq) - LN_440) * 12.0 / LN_2
      # midiNote % 12 = semitones above C, which is 3 semitones above A
      semitoneDifference = (semitonesFromA440 - 3.0) - float(midiNote % 12)
      # Adjust to the proper range.
      acc = math.fmod(semitoneDifference, 12.0)
      if acc > 6.0:
        acc -= 12.0
      elif acc < -6.0:
        acc += 12.0
      return acc


else:
  def getAvailableMics():
    return {-1: _('[Microphones not supported]')}

  class Microphone(object):
    def __new__(self, *args, **kw):
      raise RuntimeError, 'Tried to instantiate Microphone when it is unsupported!'

# Turn a number of semitones above A into a human-readable note name.
def getNoteName(semitones):
  return ['A', 'Bb', 'B', 'C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab'][semitones]


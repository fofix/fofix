#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2009 John Stumpo                                    #
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

# Most of this code is derived from the pitch analyzer in Performous,
# which is licensed under the GPL version 2 or later.

# This code performs very close to as well as pypitch did; it started as
# a direct Python translation of the C++ code (except for stuff like the
# fast Fourier transform) and was then optimized by hand to remove quite
# a bit of unnecessary stuff and to make numpy do all the heavy lifting.
# (Four lines of commentary that align perfectly... what about a fifth?)

import math
import numpy

FORMANT_RANGE = [(300, 1300), (700, 2400), (1800, 3300), (3000, 4400)]

try:
  # This is only guaranteed to do the right thing under Python 2.6 or later
  # (see PEP 754).  Otherwise, we must hope that the underlying C runtime
  # will let this work...
  NEGINF = float('-inf')
except:
  # Another way to do it, but it's not anywhere near as elegant.
  NEGINF = -1e300000

# Limit range to avoid noise and useless computation
FFT_MINFREQ = 45.0
FFT_MAXFREQ = 5000.0

class Tone(object):
  MAXHARM = 48  # maximum harmonics
  MINAGE = 2    # minimum age

  def __init__(self):
    self.freq = 0.0
    self.db = NEGINF
    self.stabledb = NEGINF
    self.harmonics = [NEGINF] * self.MAXHARM
    self.age = 0

  def __str__(self):
    if self.age >= self.MINAGE:
      return '%.1f Hz, age %f, dB: %f %f %f %f %f %f %f %f' % ([self.freq, self.age, self.db] + self.harmonics[:8])
    else:
      return ''

  def __cmp__(self, rhs):
    if isinstance(rhs, float):
      diff = self.freq / rhs - 1.0
      if abs(diff) < 0.05:
        return 0
      elif diff < 0.0:
        return -1
      else:
        return 1
    elif isinstance(rhs, Tone):
      return self.__cmp__(rhs.freq)
    else:
      return NotImplemented


FFT_P = 10
FFT_N = 1 << FFT_P

class Analyzer(object):
  def __init__(self, rate, step=200):
    self.step = step
    self.rate = rate
    self.peak = 0.0
    self.oldfreq = 0.0
    self.inputBuffer = []
    self.tones = []

    # Use a Hamming window.
    # The numpy function to make one isn't this precise.
    self.window = numpy.array([0.53836 - 0.46164 * math.cos(2.0 * math.pi * i / (FFT_N - 1)) for i in range(FFT_N)])

    # Precalculate some constants used in the analysis code.
    self.freqPerBin = self.rate / FFT_N
    self.phaseStep = 2.0 * math.pi * self.step / FFT_N
    self.normCoeff = 1.0 / FFT_N
    self.minMagnitude = pow(10, -100.0 / 20.0) / self.normCoeff  # -100 dB
    # Limit the frequency range processed.
    self.kMin = max(1, int(FFT_MINFREQ / self.freqPerBin))
    self.kMax = min(FFT_N / 2, int(FFT_MAXFREQ / self.freqPerBin))
    self.fftLastPhase = numpy.zeros(self.kMax)

    self.peakDecayFactor = numpy.power(0.999, numpy.arange(4096, -1, -1))  # 4097 elements on purpose

  def input(self, ary):
    '''Add input data to buffer.'''

    if len(ary) > 4096:
      raise ValueError, 'Input array is too long (4096 samples max)'

    # Update the peak dB level.
    peakary = numpy.concatenate((numpy.array([self.peak]), numpy.square(ary)))
    self.peak = (peakary * self.peakDecayFactor[-len(peakary):]).max()

    if len(self.inputBuffer) > 0 and len(self.inputBuffer[0]) < FFT_N:
      deficit = FFT_N - len(self.inputBuffer[0])
      if len(ary) <= deficit:
        self.inputBuffer[0] = numpy.concatenate((self.inputBuffer[0], ary))
        return
      else:
        self.inputBuffer[0] = numpy.concatenate((self.inputBuffer[0], ary[:deficit]))
        remainingInput = ary[deficit:]
    else:
      remainingInput = ary[:]

    while len(remainingInput) >= FFT_N:
      self.inputBuffer.insert(0, remainingInput[:FFT_N])
      remainingInput = remainingInput[FFT_N:]
    if len(remainingInput) > 0:
      self.inputBuffer.insert(0, remainingInput[:])

  def getPeak(self):
    '''Get the peak level in dB (negative value; 0.0 = clipping).'''
    try:
      return 10.0 * math.log10(self.peak)
    except (OverflowError, ValueError):
      return NEGINF

  def getTones(self):
    '''Get a list of all tones detected.'''
    return self.tones

  def getFormants(self):
    if len(self.tones) == 0:
      return [None] *3
    formants = [0]
    for fNum in range(3):
      minfreq = FORMANT_RANGE[fNum][0]
      maxfreq = FORMANT_RANGE[fNum][1]
      maxtone = None
      for t in self.tones:
        if t.freq < minfreq or t.freq > maxfreq or t.age < Tone.MINAGE:
          continue
        if t.freq < formants[fNum]:
          continue
        if maxtone:
          if t.db > maxtone.db:
            maxtone = t
        else:
          maxtone = t
      if maxtone:
        formants.append(maxtone.freq)
      else:
        formants.append(None)
    formants.remove(0)
    return formants

  def findTone(self, minfreq=70.0, maxfreq=700.0):
    '''Find a tone within the singing range; prefer strong tones around 200-400 Hz.'''

    if len(self.tones) == 0:
      self.oldfreq = 0.0
      return None

    db = max(tone.db for tone in self.tones)
    best = None
    bestscore = 0.0
    for t in self.tones:
      if t.db < db - 20.0 or t.freq < minfreq or t.age < Tone.MINAGE:
        continue
      if t.freq > maxfreq:
        break
      score = t.db - max(180.0, abs(t.freq - 300.0)) / 10.0
      if self.oldfreq != 0.0 and abs(t.freq / self.oldfreq - 1.0) < 0.05:
        score += 10.0
      if best is not None and bestscore > score:
        break
      best = t
      bestscore = score

    if best is not None:
      self.oldfreq = best.freq
    else:
      self.oldfreq = 0.0

    return best

  def process(self):
    '''Process all data input so far.'''

    # Instead of Peak objects, two numpy arrays (peakFreqs and peakDbs) are used.

    def match(peakDbs, pos):
      best = pos
      if peakDbs[pos-1] > peakDbs[best]:
        best = pos - 1
      if peakDbs[pos+1] > peakDbs[best]:
        best = pos + 1
      return best

    while len(self.inputBuffer) > 0 and len(self.inputBuffer[-1]) == FFT_N:
      self.fft = numpy.fft.fft(self.inputBuffer.pop() * self.window)
      magnitudes = numpy.absolute(self.fft[1:self.kMax+1])
      phases = numpy.angle(self.fft[1:self.kMax+1])

      # Process the phase difference.
      deltas = phases - self.fftLastPhase
      self.fftLastPhase = phases
      deltas -= numpy.arange(1, self.kMax+1) * self.phaseStep  # expected phase difference
      deltas = numpy.fmod(deltas, 2.0 * math.pi)  # map into (-2pi,2pi)
      deltas /= self.phaseStep  # difference from bin center frequency
      peakFreqs = numpy.zeros(self.kMax+1)
      peakDbs = numpy.zeros(self.kMax+1)
      # Also prefilter peaks.
      prevdb = 0.0
      for k in range(1, self.kMax+1):
        freq = (k + deltas[k-1]) * self.freqPerBin  # true frequency
        db = magnitudes[k-1]  # 20.0 * log10(this value * self.normCoeff) comes a bit later
        if freq > 1.0 and magnitudes[k-1] > self.minMagnitude:
          if db > prevdb:
            peakFreqs[k-1], peakDbs[k-1] = 0.0, 0.0
            peakFreqs[k], peakDbs[k] = freq, db
          else:
            peakFreqs[k], peakDbs[k] = 0.0, 0.0
          prevdb = db
        else:
          peakFreqs[k], peakDbs[k] = 0.0, 0.0
          prevdb = 0.0
      peakDbs = numpy.log10(peakDbs * self.normCoeff) * 20.0
      # Find the tones (collections of harmonics) from the array of peaks.
      tones = []
      for k in range(self.kMax-1, self.kMin-1, -1):
        if peakDbs[k] < -70.0:
          continue
        # Find the best divisor for getting the fundamental from peaks[k].
        bestDiv = 1
        bestScore = 0
        for div in range(2, Tone.MAXHARM + 1):
          if k / div > 1:
            break
          freq = peakFreqs[k] / div  # fundamental
          score = 0
          for n in range(1, min(div, 8)):
            p = match(peakDbs, k * n / div)
            score -= 1
            if peakDbs[p] < -90.0 or abs(peakFreqs[p] / n / freq - 1.0) > 0.03:
              continue
            if n == 1:  # bonus for fundamental
              score += 4
            score += 2
          if score > bestScore:
            bestScore = score
            bestDiv = div
        # Make the Tone object from the fundamental (freq) and all harmonics.
        t = Tone()
        count = 0
        freq = peakFreqs[k] / bestDiv
        t.db = peakDbs[k]
        for n in range(1, bestDiv+1):
          # Find the peak for the nth harmonic.
          p = match(peakDbs, k * n / bestDiv)
          if abs(peakFreqs[p] / n / freq - 1.0) > 0.03:  # fundamental?
            continue
          if peakDbs[p] > t.db - 10.0:
            t.db = max(t.db, peakDbs[p])
            count += 1
            t.freq += peakFreqs[p] / n
          t.harmonics[n-1] = peakDbs[p]
          peakFreqs[p], peakDbs[p] = 0.0, NEGINF
        t.freq /= count
        # If the tone seems strong enough, add it.
        # (-3 dB compensation for each harmonic)
        if t.db > -50.0 - 3.0 * count:
          t.stabledb = t.db
          tones.append(t)
      tones.sort()
      i = 0
      for oldtone in self.tones:
        while i < len(tones) and tones[i] < oldtone:
          i += 1
        if i == len(tones) or tones[i] != oldtone:
          if oldtone.db > -80.0:
            tones.insert(i, oldtone)
            tones[i].db -= 5.0
            tones[i].stabledb -= 0.1
            i += 1
        elif tones[i] == oldtone:
          tones[i].age = oldtone.age + 1
          tones[i].stabledb = 0.8 * oldtone.stabledb + 0.2 * tones[i].db
          tones[i].freq = (oldtone.freq + tones[i].freq) / 2.0
      self.tones = tones

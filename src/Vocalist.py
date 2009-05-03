#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2009 Team FoFiX                                     #
#               2009 myfingershurt                                  #
#               2009 akedrou                                        #
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
from Language import _

from Microphone import Microphone, getNoteName
from Song import VocalNote, VocalBar
from OpenGL.GL import *

class Vocalist:
  def __init__(self, engine, playerObj, editorMode = False, player = 0):
    self.engine = engine
    self.mic = Microphone(self.engine, playerObj.controller)
    
    #Get theme
    themename = self.engine.data.themeLabel
    #now theme determination logic is only in data.py:
    self.theme = self.engine.data.theme
    
    self.lateMargin  = 0
    self.earlyMargin = 0
    self.currentNote = None
    self.requiredNote = (0, 0)
    self.phraseRange = 0
    self.phraseTimes = []
    
    #scoring variables
    self.phraseGreat = 0
    self.phraseGood  = 0
    self.phraseOK    = 0
    self.phraseBad   = 0
    self.phraseFail  = 0
    self.scoreMultiplier = 1
    self.totalPhrases = 0
    self.starPhrases  = []
    
    self.phraseIndex = 0
    
    self.tempo = 120.0 #needs to actually get the real tempo...
    
    #akedrou
    self.coOpFailed = False
    self.coOpRestart = False
    self.coOpRescueTime = 0.0
    
    self.time = 0.0
    self.tap  = 0
    self.tapBuffer = 0
    self.starPowerDecreaseDivisor = 200.0/self.engine.audioSpeedFactor
    self.starPower = 0
    self.starPowerActive = False
    self.paused = False
    
    self.difficulty      = playerObj.getDifficultyInt()
    self.tapMargin       = 100 + (100 * self.difficulty)
    self.tapBufferMargin = 300 - (50 * self.difficulty)
    self.accuracy        = 5000 - (self.difficulty * 1000)
  
  def readPitch(self):
    if not self.mic.mic_started:
      return
    self.currentNote = self.mic.getSemitones()
  
  def render(self, visibility, song):
    font = self.engine.data.font
    if self.currentNote is None:
      font.render(_('None'), (.55, .25))
    else:
      font.render(getNoteName(self.currentNote), (.55, .25))
    if self.requiredNote is None:
      font.render(_('None'), (.25, .25))
    else:
      if self.requiredNote[0] is None:
        if self.tap > 0:
          glColor3f(0,1,0)
        font.render(_("Tap!"), (.25, .25))
      else:
        if self.currentNote == self.requiredNote[0]:
          glColor3f(0,1,0)
        font.render(getNoteName(self.requiredNote[0]), (.25, .25))
        font.render("MIDI note %d" % self.requiredNote[1], (.25, .29))
  
  def getCurrentPhrase(self, pos):
    pass
  
  def getCurrentNote(self, pos, song):
    track = song.vocalEventTrack
    notes = [(time, event) for time, event in track.getEvents(pos - 240000.0, pos) if isinstance(event, VocalNote)]
    
    for note in notes:
      if note[0] <= pos and note[0] + note[1].length > pos:
        return (note[1].pitch, note[1].note)
    else:
      return None
  
  def run(self, ticks, pos):
    if not self.paused:
      self.time += ticks
      if self.tap > 0:
        self.tap -= ticks
      if self.tap < 0:
        self.tap = 0
      if self.tapBuffer > 0:
        self.tapBuffer -= ticks
      if self.tapBuffer < 0:
        self.tapBuffer = 0
    
    if self.mic.getTap() and self.tapBuffer == 0:
      self.tap = (self.tapMargin*120)/self.tempo #test only
      self.tapBuffer = (self.tapBufferMargin*120)/self.tempo
    #myfingershurt: must not decrease SP if paused.
    if self.starPowerActive == True and self.paused == False:
      self.starPower -= ticks/self.starPowerDecreaseDivisor 
      if self.starPower <= 0:
        self.starPower = 0
        self.starPowerActive = False
        #MFH - call to play star power deactivation sound, if it exists (if not play nothing)
        if self.engine.data.starDeActivateSoundFound:
          #self.engine.data.starDeActivateSound.setVolume(self.sfxVolume)
          self.engine.data.starDeActivateSound.play()
    
    self.readPitch()
    
    
    return True

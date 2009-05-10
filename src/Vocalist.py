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
import os
from Language import _

from Microphone import Microphone, getNoteName
from Song import VocalNote, VocalPhrase
from OpenGL.GL import *

#stump: needed for continuous star fillup (akedrou - stealing for vocals)
import Image
import ImageDraw
from Svg import ImgDrawing

diffMod = {0: 1, 1: 1.25, 2: 1.5, 3: 1.75}

class Vocalist:
  def __init__(self, engine, playerObj, editorMode = False, player = 0):
    self.engine = engine
    self.mic = Microphone(self.engine, playerObj.controller)
    
    #Get theme
    themename = self.engine.data.themeLabel
    #now theme determination logic is only in data.py:
    self.theme = self.engine.data.theme
    self.showData = self.engine.config.get("debug", "show_raw_vocal_data")
    
    self.isDrum = False
    self.isBassGuitar = False
    self.isVocal = True
    
    self.lateMargin  = 0
    self.earlyMargin = 0
    self.currentNote = None
    self.currentNoteItem = None
    self.currentLyric = None
    self.requiredNote = None
    self.lastPhrase = None
    self.phrase = None
    self.tapping = False
    self.activePhrase = None
    self.nextPhrase = None
    self.currentPhraseTime = 0
    self.currentPhraseLength = 0
    self.phraseMin   = 0
    self.phraseMax   = 0
    self.phraseTimes = []
    
    #scoring variables
    self.allowedDeviation = 1.4
    self.scoreThresholds = [.95, .80, .60, .40, .20, 0]
    self.scoredPhrases   = [0 for i in self.scoreThresholds]
    self.scoreMultiplier = 1
    self.totalPhrases   = 0
    self.starPhrases    = []
    self.phraseInTune   = 0
    self.phraseNoteTime = 0
    self.phraseTaps     = 0
    self.lastPos        = 0
    
    self.showText = 0
    self.scoreBox  = (0,1)
    self.lastScore = -1
    
    self.phraseIndex = 0
    
    self.lyricMode  = self.engine.config.get("game", "midi_lyric_mode")
    self.nstype = self.engine.config.get("game", "vocal_scroll")
    self.speed = self.engine.config.get("game", "vocal_speed")*0.01
    self.actualBpm  = 0
    self.currentBpm = 120.0
    self.lastBpmChange = -1.0
    self.baseBeat = 0.0
    self.currentPeriod = 60000.0
    self.oldTime = 0
    self.oldLength = 0
    self.useOld = False
    
    self.arrowVis = 0
    
    self.minPitch = 0
    self.maxPitch = 0
    self.pitchRange = 0
    
    #akedrou
    self.coOpFailed = False
    self.coOpRestart = False
    self.coOpRescueTime = 0.0
    
    self.lyricScale = .00170
    
    self.engine.loadImgDrawing(self, "vocalLyricSheet", os.path.join("themes",themename,"vocals","lyricsheet.png"))
    imgwidth = self.vocalLyricSheet.width1()
    self.vocalLyricSheetWFactor = 640.000/imgwidth
    try:
      self.engine.loadImgDrawing(self, "vocalLyricSheetGlow", os.path.join("themes",themename,"vocals","lyricsheetglow.png"))
      imgwidth = self.vocalLyricSheetGlow.width1()
      self.vocalLyricSheetGlowWFactor = 640.000/imgwidth
    except:
      self.vocalLyricSheetGlow = None
    self.engine.loadImgDrawing(self, "vocalArrow", os.path.join("themes",themename,"vocals","arrow.png"))
    self.engine.loadImgDrawing(self, "vocalBar", os.path.join("themes",themename,"vocals","beatline.png"))
    self.arrowW = self.vocalArrow.width1()
    try:
      self.engine.loadImgDrawing(self, "vocalMult", os.path.join("themes",themename,"vocals","mult.png"))
    except IOError:
      self.vocalMult = None
    try:
      self.engine.loadImgDrawing(self, "vocalMeter", os.path.join("themes",themename,"vocals","meter.png"))
    except IOError:
      self.vocalMeter = None
    try:
      self.engine.loadImgDrawing(self, "vocalFill", os.path.join("themes",themename,"vocals","fill.png"))
    except IOError:
      self.vocalODFill = None
    try:
      self.engine.loadImgDrawing(self, "vocalGlow", os.path.join("themes",themename,"vocals","meter_glow.png"))
    except IOError:
      self.vocalGlow = None
    self.engine.loadImgDrawing(self, "vocalTap", os.path.join("themes",themename,"vocals","tap.png"))
    self.engine.loadImgDrawing(self, "vocalTapNote", os.path.join("themes",themename,"vocals","tap_note.png"))
    try:
      self.engine.loadImgDrawing(self, "vocalText", os.path.join("themes",themename,"vocals","text.png"))
    except IOError:
      self.vocalText = None
    try:
      self.engine.loadImgDrawing(self, "vocalODBottom", os.path.join("themes",themename,"vocals","bottom.png"))
    except IOError:
      self.vocalODBottom = None
    try:
      self.engine.loadImgDrawing(self, "vocalODFill", os.path.join("themes",themename,"vocals","fill.png"))
    except IOError:
      self.vocalODFill = None
    try:
      self.engine.loadImgDrawing(self, "vocalODTop", os.path.join("themes",themename,"vocals","top.png"))
    except IOError:
      self.vocalODTop = None
    try:
      self.engine.loadImgDrawing(self, "vocalODGlow", os.path.join("themes",themename,"vocals","glow.png"))
    except IOError:
      self.vocalODGlow = None
    height = self.vocalMeter.height1()
    self.vocalMeterScale = 60.000/height
    olFactor = height/300.000
    self.vocalFillupCenterX = int(139*olFactor)
    self.vocalFillupCenterY = int(151*olFactor)
    self.vocalFillupInRadius = int(25*olFactor)
    self.vocalFillupOutRadius = int(139*olFactor)
    self.vocalFillupColor = "#DFDFDE"
    self.vocalContinuousAvailable = self.engine.config.get("performance", "star_continuous_fillup") and \
      None not in (self.vocalFillupCenterX, self.vocalFillupCenterY, self.vocalFillupInRadius, self.vocalFillupOutRadius, self.vocalFillupColor)
    if self.engine.data.themeLabel == "MegaLight":
      self.vocalContinuousAvailable = False
    if self.vocalContinuousAvailable:
      try:
        self.drawnVocalOverlays = {}
        baseVocalFillImageSize = Image.open(self.vocalMeter.texture.name).size
        for degrees in range(0, 361, 5):
          overlay = Image.new('RGBA', baseVocalFillImageSize)
          draw = ImageDraw.Draw(overlay)
          draw.pieslice((self.vocalFillupCenterX-self.vocalFillupOutRadius, self.vocalFillupCenterY-self.vocalFillupOutRadius,
                         self.vocalFillupCenterX+self.vocalFillupOutRadius, self.vocalFillupCenterY+self.vocalFillupOutRadius),
                        -90, degrees-90, outline=self.vocalFillupColor, fill=self.vocalFillupColor)
          draw.ellipse((self.vocalFillupCenterX-self.vocalFillupInRadius, self.vocalFillupCenterY-self.vocalFillupInRadius,
                        self.vocalFillupCenterX+self.vocalFillupInRadius, self.vocalFillupCenterY+self.vocalFillupInRadius),
                       outline=(0, 0, 0, 0), fill=(0, 0, 0, 0))
          dispOverlay = ImgDrawing(self.engine.data.svg, overlay)
          self.drawnVocalOverlays[degrees] = dispOverlay
      except:
        Log.error('Could not prebuild vocal overlay textures: ')
        self.vocalContinuousAvailable = False

    self.time = 0.0
    self.tap  = 0
    self.tapBuffer = 0
    self.peak = -100.0
    self.starPowerDecreaseDivisor = 200.0/self.engine.audioSpeedFactor
    self.starPower = 0
    self.starPowerActive = False
    self.paused = False
    
    self.difficulty      = playerObj.getDifficultyInt()
    self.tapMargin       = 100 + (100 * self.difficulty)
    self.tapBufferMargin = 300 - (50 * self.difficulty)
    self.accuracy        = 5000 - (self.difficulty * 1000)
    self.difficultyModifier = diffMod[self.difficulty]
  
  def setBPM(self, bpm):
    if bpm > 200:
      bpm = 200
    self.currentBpm = bpm
    if self.nstype == 0:    #BPM mode
      self.currentPeriod = (60000.0/bpm)/self.speed
    elif self.nstype == 1:   #Difficulty mode
      if self.difficulty == 0:    #expert
        self.currentPeriod = 333/self.speed
      elif self.difficulty == 1:
        self.currentPeriod = 417/self.speed
      elif self.difficulty == 2:
        self.currentPeriod = 500/self.speed
      else:   #easy
        self.currentPeriod = 583/self.speed
    elif self.nstype == 2:   #BPM & Diff mode
      if self.difficulty == 0:    #expert
        self.currentPeriod = (40000.0/bpm)/self.speed
      elif self.difficulty == 1:
        self.currentPeriod = (50000.0/bpm)/self.speed
      elif self.difficulty == 2:
        self.currentPeriod = (60000.0/bpm)/self.speed
      else:   #easy
        self.currentPeriod = (70000.0/bpm)/self.speed

  def getScoreChange(self):
    if self.lastScore > -1:
      score = 5 - self.lastScore
      self.lastScore = -1
      return score
    else:
      return False
  
  def getCurrentNote(self, pos):
    if not self.mic.mic_started:
      return
    self.peak = self.mic.getPeak()
    if self.peak < -15:
      self.currentNote = None
    if self.requiredNote is not None and self.requiredNote > 0:
      self.currentNote = self.mic.getDeviation(self.requiredNote)
      if self.currentNote:
        if abs(self.currentNote) < self.allowedDeviation:
          duration = pos - self.lastPos
          self.currentNoteItem.accuracy += duration
          self.phraseInTune += duration*self.difficultyModifier
    elif self.requiredNote is not None and self.requiredNote == 0:
      self.currentNote = 0
    else:
      self.currentNote = self.mic.getDeviation(6)
    self.lastPos = pos
  
  def render(self, visibility, song, pos):
    font = self.engine.data.font
    w, h = self.engine.view.geometry[2:4]
    if not song:
      return
    glColor4f(1,1,1,1)
    if self.showData:
      if self.currentNote is None:
        font.render(_('None'), (.55, .25))
      else:
        if abs(self.currentNote) < .5:
          glColor3f(0,1,0)
        font.render(str(self.currentNote), (.55, .25))
      if self.requiredNote is None:
        font.render(_('None'), (.25, .25))
      else:
        if self.requiredNote == -1:
          if self.tap > 0:
            glColor3f(0,1,0)
          font.render(_("Tap!"), (.25, .25))
        else:
          font.render("MIDI note %d" % self.requiredNote, (.25, .25))
    
    height = (self.vocalLyricSheet.height1()*1.2)/2
    self.engine.drawImage(self.vocalLyricSheet, scale = (self.vocalLyricSheetWFactor,-self.vocalLyricSheetWFactor), coord = (w*.5,h-height))
    if self.useOld:
      phraseTime   = self.oldTime
      phraseLength = self.oldLength
    else:
      phraseTime   = self.currentPhraseTime
      phraseLength = self.currentPhraseLength
    
    if self.activePhrase:
      if self.lastPhrase:
        lastnotes = [(time, event) for time, event in self.lastPhrase[1].getAllEvents() if isinstance(event, VocalNote)]
      else:
        lastnotes = []
      notes = [(time, event) for time, event in self.activePhrase.getAllEvents() if isinstance(event, VocalNote)]
      if self.nextPhrase:
        nextnotes = [(time, event) for time, event in self.nextPhrase[1].getAllEvents() if isinstance(event, VocalNote)]
      else:
        nextnotes = []
      for time, event in notes:
        if self.activePhrase.tapPhrase:
          if self.lyricMode == 0:
            x = time - pos
            if x < self.currentPeriod * 6 and x > -(self.currentPeriod * 2):
              noteX = (x/(self.currentPeriod * 8))+.25
              self.engine.drawImage(self.vocalTapNote, scale = (.5,-.5), coord = (w*noteX,h-height))
          elif self.lyricMode == 1 or self.lyricMode == 2:
            noteX = (.75*(time - phraseTime)/phraseLength)+.12
            self.engine.drawImage(self.vocalTapNote, scale = (.5,-.5), coord = (w*noteX,h-height))
        else:
          now = False
          if time <= pos and time + event.length > pos:
            now = True
          elif time > pos:
            if self.activePhrase.star:
              glColor4f(1,1,0,1)
            else:
              glColor4f(1,1,1,1)
          if self.lyricMode == 0: #scrolling
            x = time - pos
            if x < self.currentPeriod * 6 and x > -(self.currentPeriod * 2):
              xPos = (x/(self.currentPeriod * 8))+.25
              val = float(event.note-self.minPitch)/float(self.pitchRange)
              if time < pos:
                v = (xPos*4)
                if now:
                  glColor4f(0,1,0,v)
                else:
                  glColor4f(.5,.5,.5,v)
              font.render("X", (xPos, .057-(.05*val)), scale = self.lyricScale)
              font.render(event.lyric, (xPos, .085), scale = self.lyricScale)
          elif self.lyricMode == 1 or self.lyricMode == 2: #line-by-line
            if time <= pos:
              if time + event.length > pos:
                glColor4f(0,1,0,1)
              else:
                glColor4f(.5,.5,.5,1)
            else:
              glColor4f(1,1,1,1)
            if not event.heldNote:
              xPos = (.75*(time - phraseTime)/phraseLength)+.12
              font.render(event.lyric, (xPos, .085), scale = self.lyricScale)
      if self.lyricMode == 0:
        for time, event in lastnotes:
          if self.activePhrase.tapPhrase:
            x = time - pos
            if x > -(self.currentPeriod * 2):
              noteX = (x/(self.currentPeriod * 8))+.25
              self.engine.drawImage(self.vocalTapNote, scale = (.5,-.5), coord = (w*noteX,h-height))
          else:
            x = time - pos
            if x > -(self.currentPeriod * 2):
              xPos = (x/(self.currentPeriod * 8))+.25
              v = (xPos*4)
              glColor4f(.5,.5,.5,v)
              font.render(event.lyric, (xPos, .085), scale = self.lyricScale)
        for time, event in nextnotes:
          if self.activePhrase.tapPhrase:
            x = time - pos
            if x < self.currentPeriod * 6:
              noteX = (x/(self.currentPeriod * 8))+.25
              self.engine.drawImage(self.vocalTapNote, scale = (.5,-.5), coord = (w*noteX,h-height))
          else:
            glColor4f(1, 1, 1, 1)
            x = time - pos
            if x < self.currentPeriod * 6:
              xPos = (x/(self.currentPeriod * 8))+.25
              font.render(event.lyric, (xPos, .085), scale = self.lyricScale)
    if self.currentNote:
      currentOffset = .05*(self.currentNote/6)
    else:
      currentOffset = 0
    if self.lyricMode == 1 or self.lyricMode == 2:
      self.engine.drawImage(self.vocalBar, scale = (.5,-.5), coord = (w*.87,h-height))
      if self.activePhrase: #this checks the previous phrase or the current
        noteX = (.75*(pos - phraseTime)/phraseLength)+.12
        if self.activePhrase.tapPhrase:
          self.engine.drawImage(self.vocalTap, scale = (.5,-.5), coord = (w*noteX,h-height))
        else:
          self.engine.drawImage(self.vocalArrow, scale = (self.vocalLyricSheetWFactor,-self.vocalLyricSheetWFactor), coord = (w*noteX-(self.arrowW/2),h*(.92+currentOffset)), color = (1,1,1,self.arrowVis/500.0))
        self.engine.drawImage(self.vocalBar, scale = (.5,-.5), coord = (w*noteX,h-height))
    elif self.lyricMode == 0:
      if self.phrase and self.phrase[1].tapPhrase: #this checks the next phrase /or/ the current
        self.engine.drawImage(self.vocalTap, scale = (.5,-.5), coord = (w*.25,h-height))
      else:
        self.engine.drawImage(self.vocalArrow, scale = (self.vocalLyricSheetWFactor,-self.vocalLyricSheetWFactor), coord = (w*.25-(self.arrowW/2),h*(.92+currentOffset)), color = (1,1,1,self.arrowVis/500.0))
      a = []
      if self.lastPhrase:
        a.extend([self.lastPhrase[0], self.lastPhrase[1].length])
      if self.phrase:
        a.extend([self.phrase[0], self.phrase[1].length])
      if self.nextPhrase:
        a.extend([self.nextPhrase[0], self.nextPhrase[1].length])
      for t in a:
        x = t - pos
        if x < self.currentPeriod * 6 and x > -(self.currentPeriod * 2):
          xPos = (x/(self.currentPeriod * 8))+.25
          if t < pos:
            v = (xPos*4)
          else:
            v = 1
          self.engine.drawImage(self.vocalBar, scale = (.5,-.5), coord = (w*xPos,h-height), color = (1,1,1,v))
    
    if self.showText > 0:
      self.engine.drawImage(self.vocalText, scale = (.5, -.5/6.0), coord = (w*.27,h*.9), rect = (0, 1, self.scoreBox[0], self.scoreBox[1]))
    
    self.engine.drawImage(self.vocalMeter, scale = (self.vocalMeterScale,-self.vocalMeterScale), coord = (w*0.25,h*0.82))
    self.engine.drawImage(self.vocalMult, scale = (.5,-.5/8.0), coord = (w*0.28,h*0.82), rect = (0, 1, float(self.scoreMultiplier-1)/9.0, float(self.scoreMultiplier)/9.0))
    if self.phraseNoteTime > 0:
      ratio = self.phraseInTune/float(self.phraseNoteTime)
      if ratio > 1:
        ratio = 1
      if self.vocalContinuousAvailable:
        degrees = int(360*ratio) - (int(360*ratio) % 5)
        self.engine.drawImage(self.drawnVocalOverlays[degrees], scale = (self.vocalMeterScale,-self.vocalMeterScale), coord = (w*0.25,h*0.82))
      else:
        width = self.vocalFill.width1()
        self.engine.drawImage(self.vocalFill, scale = (self.vocalMeterScale*ratio, -self.vocalMeterScale), coord = (w*.25-(width*ratio*self.vocalMeterScale*.5), h*.82), rect = (0,ratio,0,1))
  
  def stopMic(self):
    self.mic.stop()
  
  def startMic(self):
    self.mic.start()
  
  def addMult(self):
    if self.scoreMultiplier < 4:
      self.scoreMultiplier += 1
  
  def resetMult(self):
    self.scoreMultiplier = 1
  
  def getRequiredNote(self, pos, song, lyric = False):
    track = song.vocalEventTrack
    if pos > self.currentPhraseTime + self.currentPhraseLength - 20:
      if self.phraseIndex < len(track):
        if self.phraseIndex > 0:
          self.lastPhrase = track.allEvents[self.phraseIndex-1]
          self.phraseNoteTime = max(self.phraseNoteTime, 1)
          score = (self.phraseInTune/self.phraseNoteTime)
          for i, thresh in enumerate(self.scoreThresholds):
            if score >= thresh:
              if i < 2:
                if self.phrase[1].star:
                  self.starPower += 25
                self.addMult()
              if i > 2:
                self.resetMult()
              self.lastScore = i
              self.scoredPhrases[i] += 1
              self.showText = 1000
              self.scoreBox = (i/6.0, float(i+1)/6.0)
              break
        else:
          self.minPitch = track.minPitch
          self.maxPitch = track.maxPitch
          self.pitchRange = self.maxPitch-self.minPitch
        self.phrase = track.allEvents[self.phraseIndex]
        self.phraseInTune = 0
        self.phraseNoteTime = 0
        if self.phrase[1].tapPhrase:
          self.phraseTaps = len(self.phrase[1])
        else:
          for time, note in self.phrase[1]:
            self.phraseNoteTime += note.length
        self.phraseIndex += 1
        if self.phraseIndex < len(track):
          self.nextPhrase = track.allEvents[self.phraseIndex]
        else:
          self.nextPhrase = None
      self.currentPhraseTime = self.phrase[0]
      self.currentPhraseLength = self.phrase[1].length
    self.useOld = False
    if self.lyricMode == 1 or self.lyricMode == 2:
      if pos >= self.currentPhraseTime and pos < self.currentPhraseTime + self.currentPhraseLength:
        self.activePhrase = self.phrase[1]
      else:
        oldPhraseNum = self.phraseIndex - 2
        if oldPhraseNum >= 0:
          oldPhrase = track.allEvents[oldPhraseNum]
          if pos < oldPhrase[0] + oldPhrase[1].length + (self.currentPeriod/2):
            self.activePhrase = oldPhrase[1]
            self.oldTime = oldPhrase[0]
            self.oldLength = oldPhrase[1].length
            self.useOld = True
          else:
            self.activePhrase = None
        else:
          self.activePhrase = None
    elif self.lyricMode == 0:
      if self.phrase:
        self.activePhrase = self.phrase[1]
      else:
        self.activePhrase = None
    
    if self.activePhrase:
      notes = [(time, event) for time, event in self.activePhrase.getAllEvents() if isinstance(event, VocalNote)]
      for note in notes:
        if note[0] <= pos and note[0] + note[1].length > pos:
          self.currentNoteItem = note[1]
          if not note[1].heldNote:
            self.currentLyric = note[1].lyric
          if note[1].tap:
            return -1
          if note[1].speak or note[1].extra: # with # or ^ markers
            return 0
          return note[1].note
      else:
        self.currentLyric = None
        return None
    else:
      self.currentLyric = None
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
      
      if self.showText > 0:
        self.showText -= ticks
        if self.showText < 0:
          self.showText = 0
      
      if self.currentNote is None:
        self.arrowVis -= ticks
        if self.arrowVis < 0:
          self.arrowVis = 0
      else:
        self.arrowVis = 500
      
      if self.mic.getTap() and self.tapBuffer == 0:
        self.tap = (self.tapMargin*120)/self.currentBpm #test only
        self.tapBuffer = (self.tapBufferMargin*120)/self.currentBpm
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
      
      self.getCurrentNote(pos)
    
    return True

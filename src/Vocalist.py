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

class Vocalist:
  def __init__(self, engine, playerObj, editorMode = False, player = 0):
    self.engine = engine
    self.mic = Microphone(self.engine, playerObj.controller)
    
    #Get theme
    themename = self.engine.data.themeLabel
    #now theme determination logic is only in data.py:
    self.theme = self.engine.data.theme
    
    self.isDrum = False
    self.isBassGuitar = False
    self.isVocal = True
    
    self.lateMargin  = 0
    self.earlyMargin = 0
    self.currentNote = None
    self.currentLyric = None
    self.requiredNote = (0, 0)
    self.lastPhrase = None
    self.phrase = None
    self.tapping = False
    self.activePhrase = None
    self.nextPhrase = None
    self.currentPhraseTime = 0
    self.currentPhraseLength = 0
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
    
    self.vtype  = self.engine.config.get("game", "vocal_mode")
    self.nstype = self.engine.config.get("game", "vocal_scroll")
    if self.nstype < 3:
      self.speed = self.engine.config.get("game", "vocal_speed")*0.01
    else:
      self.speed = 410 - self.engine.config.get("game", "vocal_speed")
    self.actualBpm  = 0
    self.currentBpm = 120.0
    self.lastBpmChange = -1.0
    self.baseBeat = 0.0
    self.currentPeriod = 60000.0
    self.neckSpeed = 0 #this will be used for the scrolling
    
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
    try:
      self.engine.loadImgDrawing(self, "vocalMult", os.path.join("themes",themename,"vocals","mult.png"))
    except IOError:
      self.vocalMult = None
    try:
      self.engine.loadImgDrawing(self, "vocalMeter", os.path.join("themes",themename,"vocals","meter.png"))
    except IOError:
      self.vocalMeter = None
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

    self.vocalFillupCenterX = 139
    self.vocalFillupCenterY = 151
    self.vocalFillupInRadius = 105
    self.vocalFillupOutRadius = 139
    self.vocalFillupColor = "#A6A6A6"
    self.vocalContinuousAvailable = self.engine.config.get("performance", "star_continuous_fillup") and \
      None not in (self.vocalFillupCenterX, self.vocalFillupCenterY, self.vocalFillupInRadius, self.vocalFillupOutRadius, self.vocalFillupColor)
    if self.vocalContinuousAvailable:
      try:
        self.drawnVocalOverlays = {}
        baseVocalFillImageSize = Image.open(self.vocalMeter.texture.name).size
        for degrees in range(0, 360, 5):
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
    self.starPowerDecreaseDivisor = 200.0/self.engine.audioSpeedFactor
    self.starPower = 0
    self.starPowerActive = False
    self.paused = False
    
    self.difficulty      = playerObj.getDifficultyInt()
    self.tapMargin       = 100 + (100 * self.difficulty)
    self.tapBufferMargin = 300 - (50 * self.difficulty)
    self.accuracy        = 5000 - (self.difficulty * 1000)
  
  def setBPM(self, bpm):
    if bpm > 200:
      bpm = 200
    self.currentBpm = bpm
    self.currentPeriod = 60000.0/bpm
    if self.nstype == 0:    #BPM mode
      self.neckSpeed = (340 - bpm)/self.speed
    elif self.nstype == 1:   #Difficulty mode
      if self.difficulty == 0:    #expert
        self.neckSpeed = 220/self.speed
      elif self.difficulty == 1:
        self.neckSpeed = 250/self.speed
      elif self.difficulty == 2:
        self.neckSpeed = 280/self.speed
      else:   #easy
        self.neckSpeed = 300/self.speed
    elif self.nstype == 2:   #BPM & Diff mode
      if self.difficulty == 0:    #expert
        self.neckSpeed = (226-(bpm/10))/self.speed
      elif self.difficulty == 1:
        self.neckSpeed = (256-(bpm/10))/self.speed
      elif self.difficulty == 2:
        self.neckSpeed = (286-(bpm/10))/self.speed
      else:   #easy
        self.neckSpeed = (306-(bpm/10))/self.speed
    else: #Percentage mode - pre-calculated
      self.neckSpeed = self.speed

  
  def readPitch(self):
    if not self.mic.mic_started:
      return
    self.currentNote = self.mic.getSemitones()
  
  def render(self, visibility, song, pos):
    font = self.engine.data.font
    w, h = self.engine.view.geometry[2:4]
    if not song:
      return
    glColor4f(1,1,1,1)
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
    
    height = (self.vocalLyricSheet.height1()*1.2)/2
    self.engine.drawImage(self.vocalLyricSheet, scale = (self.vocalLyricSheetWFactor,-self.vocalLyricSheetWFactor), coord = (w*.5,h-height))
    
    if self.activePhrase:
      lastnotes = [(time, event) for time, event in self.lastPhrase[1].getAllEvents() if isinstance(event, VocalNote)]
      notes = [(time, event) for time, event in self.activePhrase.getAllEvents() if isinstance(event, VocalNote)]
      nextnotes = [(time, event) for time, event in self.nextPhrase[1].getAllEvents() if isinstance(event, VocalNote)]
      for time, event in notes:
        if self.activePhrase.tapPhrase:
          x = time - pos
          if x < self.currentPeriod * 4 and x > -(self.currentPeriod * 2):
            noteX = (x/(self.currentPeriod * 8))+.25
            self.engine.drawImage(self.vocalTapNote, scale = (.5,-.5), coord = (w*noteX,h-height))
        else:
          if time <= pos and time + event.length > pos:
            glColor3f(0,1,0)
          elif time < pos:
            glColor3f(.5,.5,.5)
          else:
            glColor3f(1,1,1)
          if not event.heldNote:
            xPos = (.5*(time - self.currentPhraseTime)/self.currentPhraseLength)+.25
            font.render(event.lyric, (xPos, .085), scale = self.lyricScale)
    if self.phrase and self.phrase[1].tapPhrase: #this checks the /next/ phrase (or the current)
      self.engine.drawImage(self.vocalTap, scale = (.5,-.5), coord = (w*.25,h-height))
    else:
      self.engine.drawImage(self.vocalArrow, scale = (.5,-.5), coord = (w*.25,h-height))
      self.engine.drawImage(self.vocalBar, scale = (.5,-.5), coord = (w*.75,h-height))
  
  def stopMic(self):
    self.mic.stop()
  
  def startMic(self):
    self.mic.start()
  
  def getCurrentNote(self, pos, song, lyric = False):
    track = song.vocalEventTrack
    if pos > self.currentPhraseTime + self.currentPhraseLength - 20:
      if self.phraseIndex < len(track):
        self.lastPhrase = track.allEvents[self.phraseIndex-1]
        self.phrase = track.allEvents[self.phraseIndex]
        self.phraseIndex += 1
        if self.phraseIndex < len(track):
          self.nextPhrase = track.allEvents[self.phraseIndex]
        else:
          self.nextPhrase = None
      self.currentPhraseTime = self.phrase[0]
      self.currentPhraseLength = self.phrase[1].length
    
    if pos >= self.currentPhraseTime and pos < self.currentPhraseTime + self.currentPhraseLength:
      self.activePhrase = self.phrase[1]
    else:
      oldPhraseNum = self.phraseIndex - 2
      if oldPhraseNum >= 0:
        oldPhrase = track.allEvents[oldPhraseNum]
        if pos < oldPhrase[0] + oldPhrase[1].length + 400:
          self.activePhrase = oldPhrase[1]
        else:
          self.activePhrase = None
      else:
        self.activePhrase = None
    
    if self.activePhrase:
      notes = [(time, event) for time, event in self.activePhrase.getAllEvents() if isinstance(event, VocalNote)]
      for note in notes:
        if note[0] <= pos and note[0] + note[1].length > pos:
          if not note[1].heldNote:
            self.currentLyric = note[1].lyric
          return (note[1].pitch, note[1].note)
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
      
      self.readPitch()
    
    return True

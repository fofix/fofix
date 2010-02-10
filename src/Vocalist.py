#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2009 Team FoFiX                                     #
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
from numpy import array, float32
from random import random

#stump: needed for continuous star fillup (akedrou - stealing for vocals)
from PIL import Image, ImageDraw
from Svg import ImgDrawing

diffMod    = {0: 1.4, 1: 1.6, 2: 1.75, 3: 1.9}
baseScores = {0: 1000, 1: 800, 2: 400, 3: 200}

class Vocalist:
  def __init__(self, engine, playerObj, editorMode = False, player = 0):
    self.engine = engine
    self.mic = Microphone(self.engine, playerObj.controller)
    
    #Get theme
    themename = self.engine.data.themeLabel
    #now theme determination logic is only in data.py:
    self.theme = self.engine.data.theme
    self.showData = self.engine.config.get("debug", "show_raw_vocal_data")
    
    #unused variables for compatibility with other instrument classes
    self.isDrum = False
    self.isBassGuitar = False
    self.isVocal = True
    self.neck = None
    self.canGuitarSolo = False
    self.guitarSolo    = False
    self.useMidiSoloMarkers = False
    self.earlyHitWindowSizeFactor = 0
    self.starNotesSet = True
    self.spEnabled = False
    self.bigRockEndingMarkerSeen = False
    self.freestyleStart = 0 
    self.freestyleFirstHit = 0 
    self.freestyleLength = 0
    self.freestyleBonusFret = 0
    self.freestyleLastFretHitTime = [0 for i in range(5)]
    self.twoChord = False
    self.leftyMode = False
    self.drumFlip = False
    self.keys = []
    self.actions = []
    self.neckSpeed = 0.0
    
    self.hitw = 1.4
    
    self.lateMargin  = 100.0
    self.earlyMargin = 100.0
    self.oldNote = 2.0
    self.pitchFudge = 0
    self.barFudge = 600
    self.stayEnd  = 0
    self.awardEnd = True
    self.formants = [None] * 3
    self.currentNote = None
    self.currentNoteItem = None
    self.currentNoteTime = 0
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
    self.doneLastPhrase = False
    
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
    self.phraseTapsHit  = 0
    self.lastPos        = 0
    
    self.showText = 0
    self.textTrans = 0
    self.scoreBox  = (0,1)
    self.scorePhrases = [_("Amazing!"), _("Great!"), _("Decent"), _("Average"), _("Meh"), _("Bad"), _("Terrible...")]
    self.textScore = -1
    self.lastScore = None
    self.coOpRB = False
    
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
    self.coOpRescueTime = 0
    
    self.lyricScale = .00170
    
    self.engine.loadImgDrawing(self, "vocalLyricSheet", os.path.join(self.engine.data.vocalPath,"lyricsheet.png"))
    imgwidth = self.vocalLyricSheet.width1()
    self.vocalLyricSheetWFactor = 640.000/imgwidth

    if self.engine.loadImgDrawing(self, "vocalLyricSheetGlow", os.path.join(self.engine.data.vocalPath,"lyricsheetglow.png")):
      imgwidth = self.vocalLyricSheetGlow.width1()
      self.vocalLyricSheetGlowWFactor = 640.000/imgwidth
    else:
      self.vocalLyricSheetGlow = None

    if self.engine.loadImgDrawing(self, "vocalLyricSheetSP", os.path.join(self.engine.data.vocalPath,"lyricsheetactivate.png")):
      self.vocalSheetSPWidth = float(self.vocalLyricSheetSP.width1()*self.vocalLyricSheetWFactor)*(self.engine.view.geometry[2]/640.0)
    else:
      self.vocalLyricSheetSP = None

    self.engine.loadImgDrawing(self, "vocalArrow", os.path.join(self.engine.data.vocalPath,"arrow.png"))
    if not self.engine.loadImgDrawing(self, "vocalSplitArrow", os.path.join(self.engine.data.vocalPath,"split_arrow.png")):
      self.vocalSplitArrow = self.vocalArrow

    self.engine.loadImgDrawing(self, "vocalBar", os.path.join(self.engine.data.vocalPath,"beatline.png"))
    self.arrowW = self.vocalArrow.width1()
    self.engine.loadImgDrawing(self, "vocalMult", os.path.join(self.engine.data.vocalPath,"mult.png"))
    self.engine.loadImgDrawing(self, "vocalMeter", os.path.join(self.engine.data.vocalPath,"meter.png"))
    if not self.engine.loadImgDrawing(self, "vocalFill", os.path.join(self.engine.data.vocalPath,"meter_fill.png")):
      self.vocalFill = self.vocalMeter
    if not self.engine.loadImgDrawing(self, "vocalGlow", os.path.join(self.engine.data.vocalPath,"meter_glow.png")):
      self.vocalGlow = None
    self.engine.loadImgDrawing(self, "vocalTap", os.path.join(self.engine.data.vocalPath,"tap.png"))
    self.engine.loadImgDrawing(self, "vocalTapNote", os.path.join(self.engine.data.vocalPath,"tap_note.png"))

    if not self.engine.loadImgDrawing(self, "vocalText", os.path.join(self.engine.data.vocalPath,"text.png")):
      self.vocalText = None
    self.engine.loadImgDrawing(self, "vocalODBottom", os.path.join(self.engine.data.vocalPath,"bottom.png"))
    self.engine.loadImgDrawing(self, "vocalODFill", os.path.join(self.engine.data.vocalPath,"fill.png"))
    self.vocalODFillWidth = self.vocalODFill.width1()/1280.000

    if not self.engine.loadImgDrawing(self, "vocalODTop", os.path.join(self.engine.data.vocalPath,"top.png")):
      self.vocalODTop = None

    if not self.engine.loadImgDrawing(self, "vocalODGlow", os.path.join(self.engine.data.vocalPath,"glow.png")):
      self.vocalODGlow = None
    
    height = self.vocalMeter.height1()
    vocalSize = self.engine.theme.vocalMeterSize
    self.vocalMeterScale = (vocalSize/height)*.5
    self.vocalFillWidth = self.vocalFill.width1()*self.vocalMeterScale/640.000
    olFactor = height/self.engine.theme.vocalFillupFactor
    self.vocalFillupCenterX = int(self.engine.theme.vocalFillupCenterX*olFactor)
    self.vocalFillupCenterY = int(self.engine.theme.vocalFillupCenterY*olFactor)
    self.vocalFillupInRadius = int(self.engine.theme.vocalFillupInRadius*olFactor)
    self.vocalFillupOutRadius = int(self.engine.theme.vocalFillupOutRadius*olFactor)
    self.vocalFillupColor = self.engine.theme.colorToHex(self.engine.theme.vocalFillupColor)
    self.vocalContinuousAvailable = self.engine.theme.vocalCircularFillup and \
      None not in (self.vocalFillupCenterX, self.vocalFillupCenterY, self.vocalFillupInRadius, self.vocalFillupOutRadius, self.vocalFillupColor)
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
    
    self.vocalLaneSize        = self.engine.theme.vocalLaneSize
    self.vocalGlowSize        = self.engine.theme.vocalGlowSize
    self.vocalGlowFade        = self.engine.theme.vocalGlowFade
    self.vocalLaneColor       = list(self.engine.theme.vocalLaneColor)
    self.vocalShadowColor     = list(self.engine.theme.vocalShadowColor)
    self.vocalGlowColor       = list(self.engine.theme.vocalGlowColor)
    self.vocalLaneColorStar   = list(self.engine.theme.vocalLaneColorStar)
    self.vocalShadowColorStar = list(self.engine.theme.vocalShadowColorStar)
    self.vocalGlowColorStar   = list(self.engine.theme.vocalGlowColorStar)
    
    self.lastVal     = 0
    self.vocalMeterX = self.engine.theme.vocalMeterX
    self.vocalMeterY = self.engine.theme.vocalMeterY
    self.vocalMultX  = self.engine.theme.vocalMultX
    self.vocalMultY  = self.engine.theme.vocalMultY
    self.vocalPowerX = self.engine.theme.vocalPowerX
    self.vocalPowerY = self.engine.theme.vocalPowerY
    
    self.time = 0.0
    self.tap  = 0
    self.tapBuffer = 0
    self.peak = -100.0
    self.starPowerDecreaseDivisor = 400.0/self.engine.audioSpeedFactor
    self.starPower = 0
    self.starPowerActive = False
    self.starPowerGained = False
    self.starPowerEnable = False
    self.starPowerCountdown = False
    self.starPowerTimer  = 200
    self.starPowerActivate = False
    self.paused = False
    self.player = player
    
    self.tapPartStart     = []
    self.tapPartLength    = []
    self.tapNoteTotals    = []
    self.tapNoteHits      = []
    self.tapPhraseActive  = False
    self.currentTapPhrase = -1
    
    self.difficulty      = playerObj.getDifficultyInt()
    self.tapMargin       = 100 + (100 * self.difficulty)
    self.tapBufferMargin = 300 - (50 * self.difficulty)
    self.accuracy        = 5000 - (self.difficulty * 1000)
    self.difficultyModifier = diffMod[self.difficulty]
    self.baseScore        = 50
    self.vocalBaseScore   = baseScores[self.difficulty]
    
    #Controls Jurgen in vocal parts
    self.jurgenEnabled   = False
    self.jurgenSkill     = 5
  
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
    self.neckSpeed         = self.currentPeriod
    self.earlyMargin       = 250 - bpm/5 - 70*self.hitw
    self.lateMargin        = 250 - bpm/5 - 70*self.hitw
  
  def getMultVals(self):
    if not self.starPowerActive:
      return (self.scoreMultiplier-1, self.scoreMultiplier)
    elif not self.coOpRB:
      multDict = {1: (4,5), 2: (6,7), 3: (7,8), 4: (8,9)}
      return multDict[self.scoreMultiplier]
    else:
      multDict = {1: (0,1), 2: (4,5), 3: (5,6), 4: (6,7)}
      return multDict[self.scoreMultiplier]
  
  def getScoreChange(self):
    if self.lastScore is not None:
      score = self.lastScore
      self.lastScore = None
      return score
    else:
      return None
  
  def getJurgenPct(self):
    #Controls Jurgen in vocal parts
    j = self.jurgenSkill
    if not self.jurgenEnabled:
      return 1
    if j == 0:
      return min((.70 + (.05*self.difficulty*random())), 1)
    elif j == 1:
      return min((.80 + (.05*self.difficulty*random())), 1)
    elif j == 2:
      return min((.85 + (.05*self.difficulty*random())), 1)
    elif j == 3:
      return min((.90 + (.05*self.difficulty*random())), 1)
    elif j == 4:
      return min((.95 + (.05*self.difficulty*random())), 1)
    else:
      return 1
  
  def getCurrentNote(self, pos):
    if not self.mic.mic_started:
      return
    if self.tapPhraseActive:
      if self.requiredNote is not None:
        if (self.tap > 0 or self.jurgenEnabled) and not self.currentNoteItem.played:
          self.tapNoteHits[self.currentTapPhrase] += 1
          self.phraseTapsHit += 1
          self.currentNoteItem.played = True
      self.lastPos = pos
      self.currentNote = self.tap
      return
    if not self.jurgenEnabled:
      self.peak = self.mic.getPeak()
      self.formants = self.mic.getFormants()
    else:
      self.peak = -10
      self.formants = [100, 600]
    if self.currentNote is not None:
      if abs(self.currentNote) < self.allowedDeviation:
        self.oldNote = self.currentNote
    if self.peak < -15:
      self.starPowerCountdown = False
      self.starPowerTimer = 200
    elif self.requiredNote is not None:
      if self.jurgenEnabled:
        self.currentNote = 0.0
      else:
        self.currentNote = self.mic.getDeviation(self.requiredNote)
      #if self.awardEnd:
      #  mult = .8
      #else:
      mult = 1
      if self.currentNote is not None:
        if self.currentNoteItem.speak or self.currentNoteItem.extra:
          self.currentNote = 0
        if abs(self.currentNote) < self.allowedDeviation and self.formants[1] is not None:
          duration = pos - self.lastPos
          self.currentNoteItem.accuracy += duration*mult*self.getJurgenPct()
          self.phraseInTune += duration*self.difficultyModifier*mult*self.getJurgenPct()
          self.pitchFudge = 70.0
        # elif self.currentNoteItem.played and self.stayEnd <= 0 and self.awardEnd:
          # self.currentNoteItem.accuracy += self.currentNoteItem.length * (1-mult)
          # self.phraseInTune += self.currentNoteItem.length * (1-mult) *self.difficultyModifier
          # self.pitchFudge = 0.0
        elif abs(self.oldNote) < self.allowedDeviation and self.pitchFudge > 0:
          duration = pos - self.lastPos
          self.currentNoteItem.accuracy += duration * (self.pitchFudge/100.0)
          self.phraseInTune += duration*self.difficultyModifier
    else:
      if self.starPowerEnable:
        self.starPowerCountdown = True
      self.currentNote = self.mic.getDeviation(6)
    self.lastPos = pos

  #stump: draw a vocal note lane, vaguely RB2-style
  def drawNoteLane(self, colors, xStartPos, xEndPos, yStartPos, yEndPos):
    colorArray = array([colors[i] for i in (4, 5, 6, 6, 0, 1, 1, 0, 2, 3, 3, 2, 6, 6, 5, 4)], dtype=float32)
    vertexArray = array([[xStartPos,                    yStartPos-self.vocalLaneSize, 0],
                         [xEndPos,                      yEndPos  -self.vocalLaneSize, 0],
                         [xEndPos,                      yEndPos  -self.vocalGlowSize, 0],
                         [xStartPos,                    yStartPos-self.vocalGlowSize, 0],
                         [xStartPos-self.vocalLaneSize, yStartPos,                    0],
                         [xEndPos  +self.vocalLaneSize, yEndPos,                      0],
                         [xEndPos,                      yEndPos  -self.vocalLaneSize, 0],
                         [xStartPos,                    yStartPos-self.vocalLaneSize, 0],
                         [xStartPos,                    yStartPos+self.vocalLaneSize, 0],
                         [xEndPos,                      yEndPos  +self.vocalLaneSize, 0],
                         [xEndPos  +self.vocalLaneSize, yEndPos,                      0],
                         [xStartPos-self.vocalLaneSize, yStartPos,                    0],
                         [xStartPos,                    yStartPos+self.vocalGlowSize, 0],
                         [xEndPos,                      yEndPos  +self.vocalGlowSize, 0],
                         [xEndPos,                      yEndPos  +self.vocalLaneSize, 0],
                         [xStartPos,                    yStartPos+self.vocalLaneSize, 0]],
                           dtype=float32)
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_COLOR_ARRAY)
    glVertexPointerf(vertexArray)
    glColorPointerf(colorArray)
    glDrawArrays(GL_QUADS, 0, len(colorArray))
    glDisableClientState(GL_COLOR_ARRAY)
    glDisableClientState(GL_VERTEX_ARRAY)
  
  def coOpRescue(self, pos):
    self.coOpRestart = True #initializes Restart Timer
    self.coOpRescueTime  = 3000
    self.starPower  = 0
    Log.debug("Rescued at " + str(pos))

  def render(self, visibility, song, pos, players):
    font = self.engine.data.font
    w, h = self.engine.view.geometry[2:4]
    height = (self.vocalLyricSheet.height1())/480.000
    if players == 1:
      addY = .7
      addYText = .725*self.engine.data.fontScreenBottom
      vsheetpos = (h*(1-addY))-(h*(height/2))
      tappos = (h*(1-(addY-.02)))-(h*(height/2))
    else:
      addY = 0
      addYText = .025*self.engine.data.fontScreenBottom
      vsheetpos = (h*(1-addY))-(h*(height/2))
      tappos = (h*(1-(addY-.02)))-(h*(height/2))
    if not song:
      return
    glColor4f(1,1,1,1)
    if self.showData:
      if self.currentNote is None:
        font.render(_('None'), (.55, .25))
      else:
        if abs(self.currentNote) < .5 and not self.tapPhraseActive:
          glColor3f(0,1,0)
        font.render(str(self.currentNote), (.55, .25))
      if self.requiredNote is None:
        font.render(_('None'), (.25, .25))
      else:
        if self.tapPhraseActive:
          if self.tap > 0:
            glColor3f(0,1,0)
          font.render(_("Tap!"), (.25, .25))
        else:
          font.render("MIDI note %d" % self.requiredNote, (.25, .25))
      if self.formants[1] is not None:
        font.render("Second Formant: %.2f Hz" % self.formants[1], (.35, .4))
    
    self.engine.drawImage(self.vocalLyricSheet, scale = (self.vocalLyricSheetWFactor,-self.vocalLyricSheetWFactor), coord = (w*.5,vsheetpos))
    if self.coOpFailed:
      if self.coOpRestart:
        self.coOpFailed = False
        self.coOpRestart = False
        Log.debug("Turning off coOpFailed. Rescue successful.")
      else:
        return
    if self.useOld:
      phraseTime   = self.oldTime
      phraseLength = self.oldLength
    else:
      phraseTime   = self.currentPhraseTime
      phraseLength = self.currentPhraseLength
    
    if self.activePhrase:
      if self.lastPhrase and not self.coOpRestart:
        lastnotes = self.lastPhrase[1].getAllEvents()
      else:
        lastnotes = []
      if self.coOpRestart:
        notes = []
      else:
        notes = self.activePhrase.getAllEvents()
      if self.nextPhrase:
        if self.nextPhrase[0]-pos > self.coOpRescueTime:
          nextnotes = self.nextPhrase[1].getAllEvents()
        else:
          nextnotes = []
      else:
        nextnotes = []
      lastNoteEnd = None  #stump
      for time, event in notes:
        if self.activePhrase.tapPhrase:
          if not event.played:
            if self.lyricMode == 0:
              x = time - pos
              if x < self.currentPeriod * 6 and x > -(self.currentPeriod * 2):
                noteX = (x/(self.currentPeriod * 8))+.25
                self.engine.drawImage(self.vocalTapNote, scale = (.5,-.5), coord = (w*noteX,tappos))
            elif self.lyricMode == 1 or self.lyricMode == 2:
              noteX = (.75*(time - phraseTime)/phraseLength)+.12
              self.engine.drawImage(self.vocalTapNote, scale = (.5,-.5), coord = (w*noteX,tappos))
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
            xStart = time - pos
            xEnd = time + event.length - pos
            if xStart < self.currentPeriod * 6 and xEnd > -(self.currentPeriod * 2):
              xStartPos = (xStart/(self.currentPeriod * 8))+.25
              xEndPos = (xEnd/(self.currentPeriod * 8))+.25
              if event.speak or event.extra:
                val = .5
              else:
                val = float(event.note-self.minPitch)/float(self.pitchRange)
              vStart = (xStartPos*4)
              vEnd = (xEndPos*4)
              if time < pos:
                if now:
                  glColor4f(0,1,0,vStart)
                else:
                  glColor4f(.5,.5,.5,vStart)
              font.render(event.lyric, (xStartPos, .085+addYText), scale = self.lyricScale)
              if not (event.speak or event.extra):
                #font.render("X", (xStartPos, .057-(.05*val)+addYText), scale = self.lyricScale)
                #stump: note lanes with RB2-like glow
                if players == 1:
                  baseY = -.1-(.05*val)+addY
                else:
                  baseY = .075-(.05*val)+addY
                if self.activePhrase.star:
                  colors = [self.vocalLaneColorStar + [vStart],
                            self.vocalLaneColorStar + [vEnd],
                            self.vocalShadowColorStar + [vStart],
                            self.vocalShadowColorStar + [vEnd],
                            self.vocalGlowColorStar + [vStart*self.vocalGlowFade],
                            self.vocalGlowColorStar + [vEnd*self.vocalGlowFade],
                            self.vocalGlowColorStar + [0.0]]
                else:
                  colors = [self.vocalLaneColor + [vStart],
                            self.vocalLaneColor + [vEnd],
                            self.vocalShadowColor + [vStart],
                            self.vocalShadowColor + [vEnd],
                            self.vocalGlowColor + [vStart*self.vocalGlowFade],
                            self.vocalGlowColor + [vEnd*self.vocalGlowFade],
                            self.vocalGlowColor + [0.0]]
                #stump: apparently we don't necessarily get the notes in strict chronological order.
                # This lane-connecting code would work nicely if not for that, but under these conditions it tends to make a big mess.
                # (Seriously, uncomment it and see for yourself.)
                if event.lyric is None and lastNoteEnd is not None:
                  self.drawNoteLane(colors, lastNoteEnd[0], xStartPos, lastNoteEnd[1], baseY)
                self.drawNoteLane(colors, xStartPos, xEndPos, baseY, baseY)
                lastNoteEnd = (xEndPos, baseY)
          elif self.lyricMode == 1 or self.lyricMode == 2: #line-by-line
            xStart = time - phraseTime
            xEnd = time - phraseTime + event.length
            if xStart < self.currentPeriod * 6 and xEnd > -(self.currentPeriod * 2):
              xStartPos = (.75*(xStart/phraseLength))+.12
              xEndPos = (.75*xEnd/phraseLength)+.12
              if event.speak or event.extra:
                val = .5
              else:
                val = float(event.note-self.minPitch)/float(self.pitchRange)
              vStart = (xStartPos*4)
              vEnd = (xEndPos*4)
              if time < pos:
                if now:
                  glColor4f(0,1,0,vStart)
                else:
                  glColor4f(.5,.5,.5,vStart)
              font.render(event.lyric, (xStartPos, .085+addYText), scale = self.lyricScale)
              if not (event.speak or event.extra):
                #font.render("X", (xStartPos, .057-(.05*val)+addYText), scale = self.lyricScale)
                #stump: note lanes with RB2-like glow
                if players == 1:
                  baseY = -.1-(.05*val)+addY
                else:
                  baseY = .075-(.05*val)+addY
                if self.activePhrase.star:
                  colors = [self.vocalLaneColorStar + [vStart],
                            self.vocalLaneColorStar + [vEnd],
                            self.vocalShadowColorStar + [vStart],
                            self.vocalShadowColorStar + [vEnd],
                            self.vocalGlowColorStar + [vStart*self.vocalGlowFade],
                            self.vocalGlowColorStar + [vEnd*self.vocalGlowFade],
                            self.vocalGlowColorStar + [0.0]]
                else:
                  colors = [self.vocalLaneColor + [vStart],
                            self.vocalLaneColor + [vEnd],
                            self.vocalShadowColor + [vStart],
                            self.vocalShadowColor + [vEnd],
                            self.vocalGlowColor + [vStart*self.vocalGlowFade],
                            self.vocalGlowColor + [vEnd*self.vocalGlowFade],
                            self.vocalGlowColor + [0.0]]
                if event.lyric is None and lastNoteEnd is not None:
                  self.drawNoteLane(colors, lastNoteEnd[0], xStartPos, lastNoteEnd[1], baseY)
                self.drawNoteLane(colors, xStartPos, xEndPos, baseY, baseY)
                lastNoteEnd = (xEndPos, baseY)
      if self.lyricMode == 0:
        lastNoteEnd = None
        for time, event in lastnotes:
          if self.lastPhrase[1].tapPhrase:
            if not event.played:
              x = time - pos
              if x > -(self.currentPeriod * 2):
                noteX = (x/(self.currentPeriod * 8))+.25
                self.engine.drawImage(self.vocalTapNote, scale = (.5,-.5), coord = (w*noteX,tappos))
          else:
            xStart = time - pos
            xEnd = time + event.length - pos
            if xEnd > -(self.currentPeriod * 2):
              xStartPos = (xStart/(self.currentPeriod * 8))+.25
              xEndPos = (xEnd/(self.currentPeriod * 8))+.25
              if event.speak or event.extra:
                val = .5
              else:
                val = float(event.note-self.minPitch)/float(self.pitchRange)
              vStart = (xStartPos*4)
              vEnd = (xEndPos*4)
              glColor4f(.5,.5,.5,vStart)
              font.render(event.lyric, (xStartPos, .085+addYText), scale = self.lyricScale)
              if not (event.speak or event.extra):
                #font.render("X", (xStartPos, .057-(.05*val)+addYText), scale = self.lyricScale)
                #stump: note lanes with RB2-like glow
                if players == 1:
                  baseY = -.1-(.05*val)+addY
                else:
                  baseY = .075-(.05*val)+addY
                if self.lastPhrase[1].star:
                  colors = [self.vocalLaneColorStar + [vStart],
                            self.vocalLaneColorStar + [vEnd],
                            self.vocalShadowColorStar + [vStart],
                            self.vocalShadowColorStar + [vEnd],
                            self.vocalGlowColorStar + [vStart*self.vocalGlowFade],
                            self.vocalGlowColorStar + [vEnd*self.vocalGlowFade],
                            self.vocalGlowColorStar + [0.0]]
                else:
                  colors = [self.vocalLaneColor + [vStart],
                            self.vocalLaneColor + [vEnd],
                            self.vocalShadowColor + [vStart],
                            self.vocalShadowColor + [vEnd],
                            self.vocalGlowColor + [vStart*self.vocalGlowFade],
                            self.vocalGlowColor + [vEnd*self.vocalGlowFade],
                            self.vocalGlowColor + [0.0]]
                if event.lyric is None and lastNoteEnd is not None:
                  self.drawNoteLane(colors, lastNoteEnd[0], xStartPos, lastNoteEnd[1], baseY)
                self.drawNoteLane(colors, xStartPos, xEndPos, baseY, baseY)
                lastNoteEnd = (xEndPos, baseY)
        lastNoteEnd = None
        for time, event in nextnotes:
          if self.nextPhrase[1].tapPhrase:
            x = time - pos
            if x < self.currentPeriod * 6:
              noteX = (x/(self.currentPeriod * 8))+.25
              self.engine.drawImage(self.vocalTapNote, scale = (.5,-.5), coord = (w*noteX,tappos))
          else:
            if self.nextPhrase[1].star:
              glColor4f(1,1,0,1)
            else:
              glColor4f(1,1,1,1)
            xStart = time - pos
            xEnd = time + event.length - pos
            if xStart < self.currentPeriod * 6:
              xStartPos = (xStart/(self.currentPeriod * 8))+.25
              xEndPos = (xEnd/(self.currentPeriod * 8))+.25
              if event.speak or event.extra:
                val = .5
              else:
                val = float(event.note-self.minPitch)/float(self.pitchRange)
              vStart = (xStartPos*4)
              vEnd = (xEndPos*4)
              font.render(event.lyric, (xStartPos, .085+addYText), scale = self.lyricScale)
              if not (event.speak or event.extra):
                #stump: note lanes with RB2-like glow
                if players == 1:
                  baseY = -.1-(.05*val)+addY
                else:
                  baseY = .075-(.05*val)+addY
                if self.nextPhrase[1].star:
                  colors = [self.vocalLaneColorStar + [vStart],
                            self.vocalLaneColorStar + [vEnd],
                            self.vocalShadowColorStar + [vStart],
                            self.vocalShadowColorStar + [vEnd],
                            self.vocalGlowColorStar + [vStart*self.vocalGlowFade],
                            self.vocalGlowColorStar + [vEnd*self.vocalGlowFade],
                            self.vocalGlowColorStar + [0.0]]
                else:
                  colors = [self.vocalLaneColor + [vStart],
                            self.vocalLaneColor + [vEnd],
                            self.vocalShadowColor + [vStart],
                            self.vocalShadowColor + [vEnd],
                            self.vocalGlowColor + [vStart*self.vocalGlowFade],
                            self.vocalGlowColor + [vEnd*self.vocalGlowFade],
                            self.vocalGlowColor + [0.0]]
                if event.lyric is None and lastNoteEnd is not None:
                  self.drawNoteLane(colors, lastNoteEnd[0], xStartPos, lastNoteEnd[1], baseY)
                self.drawNoteLane(colors, xStartPos, xEndPos, baseY, baseY)
                lastNoteEnd = (xEndPos, baseY)
    if self.currentNote is not None:
      rotate = 0
      if self.requiredNote:
        val = float(self.requiredNote-self.minPitch)/(self.pitchRange)
        self.lastVal = val
      else:
        val = self.lastVal
      if abs(self.currentNote) < self.allowedDeviation:
        currentOffset = 0
        rotate = 0
      elif self.pitchFudge > 0:
        if self.currentNote > self.oldNote:
          rotate = .2
          currentOffset = .005
        else:
          rotate = -.2
          currentOffset = -.005
      else:
        currentOffset = (self.currentNote/12.0)
      val += currentOffset
      if val > 1:
        val -= 1
      elif val < 0:
        val += 1
    else:
      val = .5
      rotate = 0
    if players == 1:
      baseY = .89+(.05*val)-addY
    else:
      baseY = .92+(.05*val)-addY
    if self.lyricMode == 1 or self.lyricMode == 2:
      self.engine.drawImage(self.vocalBar, scale = (.5,-.5), coord = (w*.87,tappos))
      if self.activePhrase: #this checks the previous phrase or the current
        noteX = (.75*(pos - phraseTime)/phraseLength)+.12
        if self.activePhrase.tapPhrase:
          self.engine.drawImage(self.vocalTap, scale = (.5,-.5), coord = (w*noteX,tappos))
        else:
          self.engine.drawImage(self.vocalArrow, scale = (self.vocalLyricSheetWFactor,-self.vocalLyricSheetWFactor), coord = (w*noteX-(self.arrowW/2),h*baseY), color = (1,1,1,self.arrowVis/500.0))
        self.engine.drawImage(self.vocalBar, scale = (.5,-.5), coord = (w*noteX,tappos))
    elif self.lyricMode == 0:
      if self.phrase and self.tapPhraseActive: #this checks the next phrase /or/ the current
        self.engine.drawImage(self.vocalTap, scale = (.5,-.5), coord = (w*.25,tappos))
      else:
        if self.currentNoteItem and (self.currentNoteItem.speak or self.currentNoteItem.extra):
          self.engine.drawImage(self.vocalSplitArrow, scale = (self.vocalLyricSheetWFactor,-self.vocalLyricSheetWFactor), coord = (w*.25-(self.arrowW/2),h*(.8355-addY)), color = (1,1,1,self.arrowVis/500.0))
        else:
          self.engine.drawImage(self.vocalArrow, scale = (self.vocalLyricSheetWFactor,-self.vocalLyricSheetWFactor), coord = (w*.25-(self.arrowW/2),h*baseY), rot = rotate, color = (1,1,1,self.arrowVis/500.0))
      a = [0] #this sticks a bar in at the beginning, so at least you know the vocal code is aware the song started.
      if self.lastPhrase:
        a.extend([self.lastPhrase[0], self.lastPhrase[0]+self.lastPhrase[1].length])
      if self.phrase:
        a.extend([self.phrase[0], self.phrase[0]+self.phrase[1].length])
      if self.nextPhrase:
        a.extend([self.nextPhrase[0], self.nextPhrase[0]+self.nextPhrase[1].length])
      tLast = -1001 #needs to be further negative than barfudge
      for t in a:
        if t-tLast<self.barFudge: #prevents ending/starting phrase bars from appearing too close together
          continue
        tLast = t
        x = t - pos
        if x < self.currentPeriod * 6 and x > -(self.currentPeriod * 2):
          xPos = (x/(self.currentPeriod * 8))+.25
          if t < pos:
            v = (xPos*4)
          else:
            v = 1
          self.engine.drawImage(self.vocalBar, scale = (.5,-.5), coord = (w*xPos,tappos), color = (1,1,1,v))
    spActPhrases = []
    if self.starPower >= 50 and not self.starPowerActive:
      if self.lastPhrase and self.phrase:
        if not self.lastPhrase[1].tapPhrase and not self.phrase[1].tapPhrase:
          spActPhrases.append((self.lastPhrase[0]+self.lastPhrase[1].length,self.phrase[0]))
      if self.phrase and self.nextPhrase:
        if not self.phrase[1].tapPhrase and not self.nextPhrase[1].tapPhrase:
          spActPhrases.append((self.phrase[0]+self.phrase[1].length,self.nextPhrase[0]))
    self.starPowerEnable = False
    for startTime,endTime in spActPhrases:
      if endTime - startTime < 1000: continue
      xStart = startTime - pos
      xEnd = endTime - pos
      if pos > startTime and pos < endTime:
        self.starPowerEnable = True
      else:
        if self.lyricMode == 1 or self.lyricMode == 2:
          continue
      if self.lyricMode == 1 or self.lyricMode == 2:
        xStart = -(self.currentPeriod*2)
        xEnd   = self.currentPeriod*6
        noteX = (.75*(pos - startTime)/(endTime - startTime))+.12
      if xStart < self.currentPeriod * 6 or xEnd > -(self.currentPeriod*2):
        xStartPos = (xStart/(self.currentPeriod*8))+.25
        xEndPos = (xEnd/(self.currentPeriod*8))+.25
        if self.vocalLyricSheetSP:
          width = (xEndPos-xStartPos)*w
          widthImg = self.vocalSheetSPWidth
          if width > widthImg*50: width = widthImg*50 #prevents too many loops. theme makers should make sure this image is reasonably sized. (note: 'light' themes)
          xStartPos *= w
          while width > 0:
            if xStartPos > w:
              break
            if xStartPos < -widthImg:
              xStartPos += widthImg
              width -= widthImg
              continue
            if widthImg < width:
              partUsed = 1
              width -= widthImg
            else:
              partUsed = float(width)/float(widthImg)
              width = 0
            self.engine.drawImage(self.vocalLyricSheetSP, scale = (self.vocalLyricSheetWFactor*partUsed,-self.vocalLyricSheetWFactor), coord = (xStartPos+(widthImg*partUsed/2),vsheetpos), rect = (0,partUsed,0,1))
            xStartPos += widthImg
        if self.lyricMode == 1 or self.lyricMode == 2:
          self.engine.drawImage(self.vocalBar, scale = (.5,-.5), coord = (w*noteX,tappos))
    if self.showText > 0:
      if self.vocalText:
        self.engine.drawImage(self.vocalText, scale = (.5, (-.5/6.0)*(1-self.textTrans)), coord = (w*self.vocalMeterX,h*(self.vocalMeterY-addY)), rect = (0, 1, self.scoreBox[0], self.scoreBox[1]-(self.textTrans/6.0)), color = (1,1,1,1-self.textTrans))
      else:
        glColor4f(1,1,1,1-self.textTrans)
        font.render(self.scorePhrases[self.textScore],(self.vocalMeterX,((1-self.vocalMeterY)*self.engine.data.fontScreenBottom+addYText)), .002)
    if self.showText <= 0 or self.textTrans > 0:
      val1,val2 = self.getMultVals()
      self.engine.drawImage(self.vocalMeter, scale = (self.vocalMeterScale,-self.vocalMeterScale), coord = (w*self.vocalMeterX,h*(self.vocalMeterY-addY)), color = (1,1,1,self.textTrans))
      if self.vocalGlow and self.starPowerActive:
        self.engine.drawImage(self.vocalGlow, scale = (self.vocalMeterScale,-self.vocalMeterScale), coord = (w*self.vocalMeterX,h*(self.vocalMeterY-addY)), color = (1,1,1,self.textTrans))
      self.engine.drawImage(self.vocalMult, scale = (.5,-.5/8.0), coord = (w*self.vocalMultX,h*(self.vocalMultY-addY)), rect = (0, 1, float(val1)/9.0, float(val2)/9.0), color = (1,1,1,self.textTrans))
      if self.phraseNoteTime > 0 and self.phraseInTune > 0 and not self.tapPhraseActive:
        ratio = self.phraseInTune/float(self.phraseNoteTime)
        if ratio > 1:
          ratio = 1
        if self.vocalContinuousAvailable:
          degrees = int(360*ratio) - (int(360*ratio) % 5)
          self.engine.drawImage(self.drawnVocalOverlays[degrees], scale = (self.vocalMeterScale,-self.vocalMeterScale), coord = (w*self.vocalMeterX,h*(self.vocalMeterY-addY)), color = (1,1,1,self.textTrans))
        else:
          self.engine.drawImage(self.vocalFill, scale = (self.vocalFillWidth*ratio, -self.vocalFillWidth), coord = (w*self.vocalMeterX-(ratio*self.vocalFillWidth*w*.5), h*(self.vocalMeterY-addY)), rect = (0,ratio,0,1), color = (1,1,1,self.textTrans), stretched = 11)
    self.engine.drawImage(self.vocalODBottom, scale = (.5,-.5), coord = (w*self.vocalPowerX,h*(self.vocalPowerY-addY)))
    if self.starPower > 0:
      currentSP = self.starPower/100.0
      self.engine.drawImage(self.vocalODFill, scale = (self.vocalODFillWidth*currentSP,-self.vocalODFillWidth), coord = (w*self.vocalPowerX-((1-currentSP)*self.vocalODFillWidth*w*.5),h*(self.vocalPowerY-addY)), rect = (0,currentSP,0,1), stretched = 11)
    if self.vocalODTop:
      self.engine.drawImage(self.vocalODTop, scale = (.5,-.5), coord = (w*self.vocalPowerX,h*(self.vocalPowerY-addY)))
    if self.starPowerActive:
      if self.vocalLyricSheetGlow:
        self.engine.drawImage(self.vocalLyricSheetGlow, scale = (self.vocalLyricSheetWFactor,-self.vocalLyricSheetWFactor), coord = (w*.5,vsheetpos))
      if self.vocalODGlow:
        self.engine.drawImage(self.vocalODGlow, scale = (.5,-.5), coord = (w*self.vocalPowerX,h*(self.vocalPowerY-addY)))
    if self.tapPhraseActive:
      font.render("%d / %d" % (self.tapNoteHits[self.currentTapPhrase], self.tapNoteTotals[self.currentTapPhrase]), (.25, .065+addYText), scale = self.lyricScale)
  
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
    track = song.track[self.player]
    if self.doneLastPhrase:
      return
    if pos > self.currentPhraseTime + self.currentPhraseLength - 20:
      if self.phraseIndex < len(track):
        if self.phraseIndex > 0:
          self.lastPhrase = track.allEvents[self.phraseIndex-1]
          self.phraseNoteTime = max(self.phraseNoteTime, 1)
          if self.activePhrase.tapPhrase:
            score = float(self.phraseTapsHit)/float(self.phraseTaps)
            scorePt = self.phraseTapsHit * self.baseScore
            taps = self.phraseTapsHit
          else:
            score = (self.phraseInTune/self.phraseNoteTime)
            scorePt = int(score * self.vocalBaseScore)
            taps = 0
          if not self.coOpRestart and not self.coOpFailed:
            for i, thresh in enumerate(self.scoreThresholds):
              if score >= thresh:
                if i < 2:
                  if self.phrase[1].star:
                    self.starPower += 25
                    self.starPowerGained = True
                    if self.starPower > 100:
                      self.starPower = 100
                  self.addMult()
                if i >= 2:
                  self.resetMult()
                self.lastScore = (scorePt, i, taps)
                self.textScore = i
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
        self.phraseTaps = 0
        self.phraseTapsHit = 0
        if self.phrase[1].tapPhrase:
          for note in self.phrase[1]:
            self.phraseTaps += 1
          if not self.tapPhraseActive:
            self.mic.detectTaps  = True
            self.tapPhraseActive = True
            self.currentTapPhrase += 1
        else:
          self.tapPhraseActive = False
          self.mic.detectTaps  = False
          self.mic.getTap()
          for time, note in self.phrase[1]:
            self.phraseNoteTime += note.length
        self.phraseIndex += 1
        if self.phraseIndex < len(track):
          self.nextPhrase = track.allEvents[self.phraseIndex]
        else:
          self.nextPhrase = None
      elif self.phraseIndex == len(track):
        self.phraseNoteTime = max(self.phraseNoteTime, 1)
        if self.activePhrase.tapPhrase:
          score = float(self.phraseTapsHit)/float(self.phraseTaps)
          scorePt = self.phraseTapsHit * self.baseScore
          taps = self.phraseTapsHit
        else:
          score = (self.phraseInTune/self.phraseNoteTime)
          scorePt = int(score * self.vocalBaseScore)
          taps = 0
        if not self.coOpFailed and not self.coOpRestart:
          for i, thresh in enumerate(self.scoreThresholds):
            if score >= thresh:
              if i < 2:
                if self.phrase[1].star:
                  self.starPower += 25
                  self.starPowerGained = True
                  if self.starPower > 100:
                    self.starPower = 100
                self.addMult()
              if i >= 2:
                self.resetMult()
              self.lastScore = (scorePt, i, taps)
              self.textScore = i
              self.scoredPhrases[i] += 1
              self.showText = 1000
              self.scoreBox = (i/6.0, float(i+1)/6.0)
              break
        self.phraseInTune = 0
        self.phraseNoteTime = 0
        self.phraseTaps = 0
        self.phraseTapsHit = 0
        self.doneLastPhrase = True
      if self.coOpFailed and self.coOpRestart:
        self.coOpFailed = False
      if self.coOpRestart and self.coOpRescueTime == 0:
        self.coOpRestart = False
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
      lateMargin = 0
      if self.activePhrase.tapPhrase:
        lateMargin = self.lateMargin
      notes = [(time, event) for time, event in self.activePhrase.getAllEvents() if isinstance(event, VocalNote)]
      retval = None
      for note in notes:
        if retval is not None: #this checks if the note is a held note - if it is, do not award points based on cutting off.
          if note[1].heldNote:
            self.awardEnd = False
          else:
            self.awardEnd = True
          break
        if note[0] <= pos and note[0] + note[1].length + lateMargin > pos:
          self.currentNoteTime = note[0]
          self.currentNoteItem = note[1]
          if not note[1].heldNote:
            self.currentLyric = note[1].lyric
          if note[1].tap:
            retval = 1
          elif note[1].speak or note[1].extra: # with # or ^ markers
            retval = 0
          else:
            retval = note[1].note
        else:
          self.currentNoteItem = None
      else:
        self.awardEnd = True
        if retval is None:
          self.currentLyric = None
          self.currentNoteItem = None
      return retval
    else:
      self.awardEnd = True
      self.currentLyric = None
      self.currentNoteItem = None
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
      
      if self.pitchFudge > 0:
        self.pitchFudge -= ticks
      if self.stayEnd > 0 and self.formants[1] is None:
        self.stayEnd -= ticks
      
      if self.showText > 0:
        self.showText -= ticks
        if self.showText < 0:
          self.showText = 0
        if self.textTrans > 0:
          self.textTrans -= ticks/400.0
          if self.textTrans < 0:
            self.textTrans = 0
      else:
        self.textTrans = 1
      
      if self.coOpRescueTime > 0:
        self.coOpRescueTime -= ticks
        if self.coOpRescueTime < 0:
          self.coOpRescueTime = 0
      
      if not self.starPowerEnable:
        self.starPowerCountdown = False
        self.starPowerTimer = 200
      if self.starPowerCountdown:
        self.starPowerTimer -= ticks
        if self.starPowerTimer <= 0:
          self.starPowerActivate = True
      
      if self.currentNote is None or (self.formants[1] is None and self.pitchFudge <= 0):
        self.arrowVis -= ticks
        if self.arrowVis < 0:
          self.arrowVis = 0
      else:
        self.arrowVis = 500
      if self.activePhrase:
        if self.activePhrase.tapPhrase:
          if self.mic.getTap() and self.tapBuffer == 0:
            self.tap = self.earlyMargin #test only
            self.tapBuffer = 0 #(self.tapBufferMargin*120)/self.currentBpm
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

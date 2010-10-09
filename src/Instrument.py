#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2009 Blazingamer                                    #
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


from OpenGL.GL import *

#myfingershurt: needed for multi-OS file fetching
import os
import Log

import math

from Song import Note, Tempo
import Song   #need the base song defines as well

class Instrument:
  def __init__(self, engine, playerObj, player = 0):
    self.engine         = engine

    self.starPowerDecreaseDivisor = 200.0/self.engine.audioSpeedFactor

    self.bigRockEndingMarkerSeen = False

    self.strings        = 5

    self.isStarPhrase = False
    self.finalStarSeen = False

    self.selectedString = 0
    self.time           = 0.0
    self.pickStartPos   = 0
    self.leftyMode      = False
    self.drumFlip       = False

    self.freestyleHitFlameCounts = [0 for n in range(self.strings+1)]    #MFH

    self.freestyleActive = False
    self.drumFillsActive = False
    
    self.incomingNeckMode = self.engine.config.get("game", "incoming_neck_mode")
    self.guitarSoloNeckMode = self.engine.config.get("game", "guitar_solo_neck")
    self.bigRockEndings = self.engine.config.get("game", "big_rock_endings")

    # Volshebnyi - BRE scoring variables
    self.freestyleEnabled = False
    self.freestyleStart = 0
    self.freestyleFirstHit = 0
    self.freestyleLength = 0
    self.freestyleLastHit = 0
    self.freestyleBonusFret = -2
    self.freestyleLastFretHitTime = range(5)
    self.freestyleBaseScore = 750
    self.freestylePeriod = 1000
    self.freestylePercent = 50

    self.freestyleReady = False
    self.freestyleOffset = 5
    self.freestyleSP = False

    #empty variables for class compatibility
    self.totalPhrases = 0

    self.accThresholdWorstLate = 0
    self.accThresholdVeryLate = 0
    self.accThresholdLate = 0
    self.accThresholdSlightlyLate = 0
    self.accThresholdExcellentLate = 0
    self.accThresholdPerfect = 0
    self.accThresholdExcellentEarly = 0
    self.accThresholdSlightlyEarly = 0
    self.accThresholdEarly = 0
    self.accThresholdVeryEarly = 0


    self.tempoBpm = 120   #MFH - default is NEEDED here...

    self.beatsPerBoard  = 5.0
    self.boardWidth = self.engine.theme.neckWidth
    self.boardLength = self.engine.theme.neckLength
    self.beatsPerUnit   = self.beatsPerBoard / self.boardLength
    self.strings        = 5
    self.fretWeight     = [0.0] * self.strings
    self.fretActivity   = [0.0] * self.strings
    self.fretColors     = self.engine.theme.noteColors
    self.spColor        = self.engine.theme.spNoteColor
    self.killColor      = self.engine.theme.killNoteColor
    self.useFretColors  = self.engine.theme.use_fret_colors

    self.playedNotes    = []
    self.missedNotes    = []

    self.useMidiSoloMarkers = False
    self.canGuitarSolo = False
    self.guitarSolo = False
    self.sameNoteHopoString = False
    self.hopoProblemNoteNum = -1
    self.currentGuitarSoloHitNotes = 0

    self.cappedScoreMult = 0

    self.battleSuddenDeath  = False
    self.battleObjectsEnabled = []
    self.battleSDObjectsEnabled = []
    if self.engine.config.get("game", "battle_Whammy") == 1:
      self.battleObjectsEnabled.append(4)
    if self.engine.config.get("game", "battle_Diff_Up") == 1:
      self.battleObjectsEnabled.append(2)
    if self.engine.config.get("game", "battle_String_Break") == 1:
      self.battleObjectsEnabled.append(3)
    if self.engine.config.get("game", "battle_Double") == 1:
      self.battleObjectsEnabled.append(7)
    if self.engine.config.get("game", "battle_Death_Drain") == 1:
      self.battleObjectsEnabled.append(1)
    if self.engine.config.get("game", "battle_Amp_Overload") == 1:
      self.battleObjectsEnabled.append(8)
    if self.engine.config.get("game", "battle_Switch_Controls") == 1:
      self.battleObjectsEnabled.append(6)
    if self.engine.config.get("game", "battle_Steal") == 1:
      self.battleObjectsEnabled.append(5)
    #if self.engine.config.get("game", "battle_Tune") == 1:
    #  self.battleObjectsEnabled.append(9)

    Log.debug("Battle Objects Enabled: "+str(self.battleObjectsEnabled))
    self.battleNextObject   = 0
    self.battleObjects      = [0] * 3
    self.battleBeingUsed    = [0] * 2
    self.battleStatus       = [False] * 9
    self.battleStartTimes    = [0] * 9
    self.battleGetTime      = 0
    self.battleTarget       = 0

    self.battleLeftyLength  = 8000#
    self.battleDiffUpLength = 15000
    self.battleDiffUpValue  = playerObj.getDifficultyInt()
    self.battleDoubleLength = 8000
    self.battleAmpLength    = 8000
    self.battleWhammyLimit  = 6#
    self.battleWhammyNow    = 0
    self.battleWhammyDown   = False
    self.battleBreakLimit   = 8.0
    self.battleBreakNow     = 0.0
    self.battleBreakString  = 0
    self.battleObjectGained = 0
    self.battleSuddenDeath  = False
    self.battleDrainStart   = 0
    self.battleDrainLength  = 8000

    #self.actualBpm = 0.0
    self.currentBpm     = 120.0   #MFH - need a default 120BPM to be set in case a custom song has no tempo events.
    self.currentPeriod  = 60000.0 / self.currentBpm
    self.targetBpm      = self.currentBpm
    self.targetPeriod   = 60000.0 / self.targetBpm
    self.lastBpmChange  = -1.0
    self.baseBeat       = 0.0


    self.indexFps       = self.engine.config.get("video", "fps")

    #########For Animations
    self.Animspeed      = 30#Lower value = Faster animations
    #For Animated Starnotes
    self.indexCount     = 0
    #Alarian, For animated hitglow
    self.HCount         = 0
    self.HCount2        = 0
    self.Hitanim        = True
    self.Hitanim2       = True

    #myfingershurt: to keep track of pause status here as well
    self.paused = False

    self.spEnabled = True
    self.starPower = 0
    self.starPowerGained = False

    self.starpowerMode = self.engine.config.get("game", "starpower_mode") #MFH
    self.killPoints = False

    #get difficulty
    self.difficulty = playerObj.getDifficultyInt()
    self.controlType = playerObj.controlType

    self.scoreMultiplier = 1

    #MFH - I do not understand fully how the handicap scorecard works at the moment, nor do I have the time to figure it out.
    #... so for now, I'm just writing some extra code here for the early hitwindow size handicap.
    self.earlyHitWindowSizeFactor = 0.5

    self.hitw = self.engine.config.get("game", "note_hit_window")  #this should be global, not retrieved every BPM change.
    if self.hitw == 0: 
      self.hitw = 2.3
    elif self.hitw == 1: 
      self.hitw = 1.9
    elif self.hitw == 2: 
      self.hitw = 1.2
    elif self.hitw == 3:  
      self.hitw = 1.0
    elif self.hitw == 4:  
      self.hitw = 0.70
    else:
      self.hitw = 1.2

    #myfingershurt: need a separate variable to track whether or not hopos are actually active
    self.wasLastNoteHopod = False
    
    
    self.hopoLast       = -1
    self.hopoColor      = (0, .5, .5)
    self.player         = player

    self.hit = [False, False, False, False, False]
    
    self.freestyleHit = [False, False, False, False, False]

    #myfingershurt: this should be retrieved once at init, not repeatedly in-game whenever tails are rendered.
    self.notedisappear = self.engine.config.get("game", "notedisappear")
    self.fretsUnderNotes  = self.engine.config.get("game", "frets_under_notes")
    self.staticStrings  = self.engine.config.get("performance", "static_strings")

    self.muteSustainReleases = self.engine.config.get("game", "sustain_muting") #MFH

    
    self.twoChord       = 0
    self.twoChordApply  = False
    self.hopoActive     = 0
    
    self.LastStrumWasChord = False

    self.vbpmLogicType = self.engine.config.get("debug",   "use_new_vbpm_beta")

    #Get theme
    themename = self.engine.data.themeLabel
    #now theme determination logic is only in data.py:
    self.theme = self.engine.data.theme

    self.spRefillMode = self.engine.config.get("game","sp_notes_while_active")
    self.hitglow_color = self.engine.config.get("video", "hitglow_color") #this should be global, not retrieved every fret render.

    #check if BRE enabled
    if self.bigRockEndings == 2 or (self.theme == 2 and self.bigRockEndings == 1):
      self.freestyleEnabled = True

    #blazingamer
    self.nstype = self.engine.config.get("game", "nstype")
    self.twoDnote = self.engine.theme.twoDnote
    self.twoDkeys = self.engine.theme.twoDkeys 
    self.threeDspin = self.engine.theme.threeDspin 
    self.noterotate = self.engine.config.get("coffee", "noterotate")

    #MFH- fixing neck speed
    if self.nstype < 3:   #not constant mode: 
      self.speed = self.engine.config.get("coffee", "neckSpeed")*0.01
    else:   #constant mode
      #self.speed = self.engine.config.get("coffee", "neckSpeed")
      self.speed = 410 - self.engine.config.get("coffee", "neckSpeed")    #invert this value

    self.boardScaleX    = self.boardWidth/3.0
    self.boardScaleY    = self.boardLength/9.0

    self.fretPress      = self.engine.theme.fret_press

    #akedrou
    self.coOpFailed = False
    self.coOpRestart = False
    self.coOpRescueTime = 0.0

    self.setBPM(self.currentBpm)


    if self.starpowerMode == 1:
      self.starNotesSet = False
    else:
      self.starNotesSet = True

    self.maxStars = []
    self.starNotes = []
    self.totalNotes = 0

    self.keys = []
    self.actions = []
    self.soloKey = []

    engine.loadImgDrawing(self, "glowDrawing", "glow.png")

    #MFH - making hitflames optional
    if engine.loadImgDrawing(self, "hitflames1Drawing", os.path.join("themes",themename,"hitflames1.png"),  textureSize = (128, 128)):
      if engine.loadImgDrawing(self, "hitflames2Drawing", os.path.join("themes",themename,"hitflames2.png"),  textureSize = (128, 128)):
        self.hitFlamesPresent = True
      else:
        self.hitflames2Drawing = None
    else:
      self.hitflames1Drawing = None
      self.hitflames2Drawing = None

    if not engine.loadImgDrawing(self, "hitflamesAnim", os.path.join("themes",themename,"hitflamesanimation.png"),  textureSize = (128, 128)):
      self.Hitanim2 = False

    if not engine.loadImgDrawing(self, "hitglowAnim", os.path.join("themes",themename,"hitglowanimation.png"),  textureSize = (128, 128)):
      if engine.loadImgDrawing(self, "hitglowDrawing", os.path.join("themes",themename,"hitglow.png"),  textureSize = (128, 128)):
        if not engine.loadImgDrawing(self, "hitglow2Drawing", os.path.join("themes",themename,"hitglow2.png"),  textureSize = (128, 128)):
          self.hitglow2Drawing = None
          self.disableFlameSFX = True
      else:
        self.hitglowDrawing = None
        self.disableFlameSFX   #MFH - shut down all flames if these are missing.
      self.Hitanim = False

    engine.loadImgDrawing(self, "hitlightning", os.path.join("themes",themename,"lightning.png"),  textureSize = (128, 128))

    self.meshColor  = self.engine.theme.meshColor
    self.hopoColor  = self.engine.theme.hopoColor
    self.spotColor = self.engine.theme.spotColor   
    self.keyColor = self.engine.theme.keyColor
    self.key2Color = self.engine.theme.key2Color
    fC = [(.84, 1, .51), (1, .53, .5), (.98, .96, .42), (.64, .97, 1), (1, .87, .55)]
    self.flameColors = [fC,fC,fC,fC]
    self.gh3flameColor = (.75,.36,.02)
    fS = [.075]*5
    self.flameSizes = [fS,fS,fS,fS]
    self.glowColor  = self.engine.theme.glowColor
    self.disableVBPM  = self.engine.config.get("game", "disable_vbpm")
    self.disableNoteSFX  = self.engine.config.get("video", "disable_notesfx")
    self.disableFretSFX  = self.engine.config.get("video", "disable_fretsfx")
    self.disableFlameSFX  = self.engine.config.get("video", "disable_flamesfx")

    self.twoChordMax = False

    self.canGuitarSolo = False
    self.guitarSolo = False
    self.fretboardHop = 0.00  #stump
    self.scoreMultiplier = 1
    self.coOpFailed = False #akedrou
    self.coOpRestart = False #akedrou
    self.starPowerActive = False

  #this checks to see if there is a "drum" or "bass" folder
  #inside the subdirectory for image replacement
  def checkPath(self, subdirectory, file):
    #Get theme
    themename = self.engine.data.themeLabel
    
    defaultpath = os.path.join("themes", themename, subdirectory)
    themepath = os.path.join("themes", themename, subdirectory)
    if self.isDrum:
      themepath = os.path.join(themepath, "drum")
    elif self.isBassGuitar:
      themepath = os.path.join(themepath, "bass")
          
    if self.engine.fileExists(os.path.join(themepath, file)):
      print themepath + " exists!"
      return os.path.join(themepath, file)
    else:
      return os.path.join(defaultpath, file)

  def loadNotes(self):
      pass
      
  def loadFrets(self):
      pass
      
  def loadTails(self):
      pass

  def setMultiplier(self, multiplier):
    self.scoreMultiplier = multiplier
    self.neck.scoreMultiplier = multiplier

  def setBPM(self, bpm):
    if bpm > 200:
      bpm = 200

    #MFH - Filter out unnecessary BPM settings (when currentBPM is already set!)
    #if self.actualBpm != bpm:
    #  self.actualBpm = bpm
    self.currentBpm = bpm   #update current BPM as well

    #MFH - Neck speed determination:
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

    self.earlyMargin       = 250 - bpm/5 - 70*self.hitw
    self.lateMargin        = 250 - bpm/5 - 70*self.hitw
    #self.earlyMargin = self.lateMargin * self.earlyHitWindowSizeFactor    #MFH - scale early hit window here

    #self.noteReleaseMargin = 200 - bpm/5 - 70*self.hitw
    #if (self.noteReleaseMargin < (200 - bpm/5 - 70*1.2)):   #MFH - enforce "tight" hitwindow minimum note release margin
    #  self.noteReleaseMargin = (200 - bpm/5 - 70*1.2)
    if self.muteSustainReleases == 4:   #tight
      self.noteReleaseMargin = (200 - bpm/5 - 70*1.2)
    elif self.muteSustainReleases == 3: #standard
      self.noteReleaseMargin = (200 - bpm/5 - 70*1.0)
    elif self.muteSustainReleases == 2: #wide
      self.noteReleaseMargin = (200 - bpm/5 - 70*0.7)
    else:  #ultra-wide 
      self.noteReleaseMargin = (200 - bpm/5 - 70*0.5)

    #MFH - TODO - only calculate the below values if the realtime hit accuracy feedback display is enabled - otherwise this is a waste!
    self.accThresholdWorstLate = (0-self.lateMargin)
    self.accThresholdVeryLate = (0-(3*self.lateMargin/4))
    self.accThresholdLate = (0-(2*self.lateMargin/4))
    self.accThresholdSlightlyLate = (0-(1*self.lateMargin/4))
    self.accThresholdExcellentLate = -1.0
    self.accThresholdPerfect = 1.0
    self.accThresholdExcellentEarly = (1*self.lateMargin/4)
    self.accThresholdSlightlyEarly = (2*self.lateMargin/4)
    self.accThresholdEarly = (3*self.lateMargin/4)
    self.accThresholdVeryEarly = (4*self.lateMargin/4)



  def getRequiredNotes(self, song, pos):
    return self.getRequiredNotesMFH(song, pos)

  def getRequiredNotes2(self, song, pos, hopo = False):
    return self.getRequiredNotesMFH(song, pos)

  def getRequiredNotes3(self, song, pos, hopo = False):
    return self.getRequiredNotesMFH(song, pos)

  def getMissedNotes(self, song, pos, catchup = False):
    return self.getMissedNotesMFH(song, pos, catchup)

  def getMissedNotesMFH(self, song, pos, catchup = False):
    if not song:
      return
    if not song.readyToGo:
      return

    m1      = self.lateMargin
    m2      = self.lateMargin * 2
      
    track   = song.track[self.player]
    notes   = [(time, event) for time, event in track.getEvents(pos - m2, pos - m1) if isinstance(event, Note)]   #was out of order
    
    #MFH - this additional filtration step removes sustains whose Note On event time is now outside the hitwindow.
    notes   = [(time, event) for time, event in notes if (time >= (pos - m2)) and (time <= (pos - m1))] 
    notes   = [(time, event) for time, event in notes if not event.played and not event.hopod and not event.skipped]

    if catchup:
      for time, event in notes:
        event.skipped = True
      
    return sorted(notes, key=lambda x: x[0])    #MFH - what the hell, this should be sorted by TIME not note number....


  #Renders the tail glow hitflame
  def renderHitTrails(self, visibility, song, pos, controls):
    if not song or self.flameColors[0][0][0] == -1 or self.disableFlameSFX == True:
      return

    w = self.boardWidth / self.strings
    track = song.track[self.player]

    size = (.22, .22)
    v = 1.0 - visibility
     
    if (self.HCountAni == True and self.HCount2 > 12):
      for n in range(self.strings):
        f = self.fretWeight[n]
        c = self.fretColors[n]
        if f and (controls.getState(self.actions[0]) or controls.getState(self.actions[1])):
          f += 0.25      
        y = v + f / 6
        x = (self.strings / 2 - n) * w
        f = self.fretActivity[n]

        ms = math.sin(self.time) * .25 + 1
        ff = f
        ff += 1.2
          
          
        #myfingershurt: need to cap flameSizes use of scoreMultiplier to 4x, the 5x and 6x bass groove mults cause crash:
        self.cappedScoreMult = min(self.scoreMultiplier,4)
        flameSize = self.flameSizes[self.cappedScoreMult - 1][n]
        if self.theme == 0 or self.theme == 1: #THIS SETS UP GH3 COLOR, ELSE ROCKBAND(which is DEFAULT in Theme.py)
          flameColor = self.gh3flameColor
        else:
          flameColor = self.flameColors[self.cappedScoreMult - 1][n]

        flameColorMod = (1.19, 1.97, 10.59)
        flamecol = tuple([flameColor[ifc]*flameColorMod[ifc] for ifc in range(3)])

        if self.starPowerActive:
          if self.theme == 0 or self.theme == 1: #GH3 starcolor
            flamecol = self.spColor
          else: #Default starcolor (Rockband)
            flamecol = (.9,.9,.9)
              
        #Alarian: Animated hitflames
        if self.Hitanim:
          self.HCount = self.HCount + 1
          if self.HCount > self.Animspeed-1:
            self.HCount = 0
          HIndex = (self.HCount * 16 - (self.HCount * 16) % self.Animspeed) / self.Animspeed
          if HIndex > 15:
            HIndex = 0
          texX = (HIndex*(1/16.0), HIndex*(1/16.0)+(1/16.0))

          self.engine.draw3Dtex(self.hitglowAnim, coord = (x, y + .225, 0), rot = (90, 1, 0, 0), scale = (2.4, 1, 3.3),
                                vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                texcoord = (texX[0],0.0,texX[1],1.0), multiples = True, alpha = True, color = (1,1,1))


        else:   
          ff += .3
         
          flameColorMod = (1.19, 1.78, 12.22)
          flamecol = tuple([flameColor[ifc]*flameColorMod[ifc] for ifc in range(3)])
  
          if self.starPowerActive:
            if self.theme == 0 or self.theme == 1: #GH3 starcolor
              flamecol = self.spColor
            else: #Default starcolor (Rockband)
              flamecol = (.8,.8,.8)

          self.engine.draw3Dtex(self.hitglowDrawing, coord = (x, y + .125, 0), rot = (90, 1, 0, 0),
                                scale = (0.5 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff),
                                vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)

          self.engine.draw3Dtex(self.hitglow2Drawing, coord = (x, y + .25, .05), rot = (90, 1, 0, 0),
                                scale = (.40 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff),
                                vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)


  #renders the flames that appear when a note is struck
  def renderFlames(self, visibility, song, pos, controls):
    if not song or self.flameColors[0][0][0] == -1 or self.disableFlameSFX == True:
      return

    w = self.boardWidth / self.strings
    track = song.track[self.player]

    size = (.22, .22)
    v = 1.0 - visibility
     

    flameLimit = 10.0
    flameLimitHalf = round(flameLimit/2.0)
    renderedNotes = self.getRequiredNotesForRender(song,pos)
    for time, event in renderedNotes:
      if isinstance(event, Tempo):
        continue
        
      if not isinstance(event, Note):
        continue
        
      if (event.played or event.hopod) and event.flameCount < flameLimit:
        ms = math.sin(self.time) * .25 + 1
        x  = (self.strings / 2 - event.number) * w
        xlightning = (self.strings / 2 - event.number)*2.2*w
        ff = 1 + 0.25       
        y = v + ff / 6

        if self.theme == 2:
          y -= 0.5
          
        flameSize = self.flameSizes[self.cappedScoreMult - 1][event.number]
        if self.theme == 0 or self.theme == 1: #THIS SETS UP GH3 COLOR, ELSE ROCKBAND(which is DEFAULT in Theme.py)
          flameColor = self.gh3flameColor
        else:
          flameColor = self.flameColors[self.cappedScoreMult - 1][event.number]
        if flameColor[0] == -2:
          flameColor = self.fretColors[event.number]
          
        ff += 1.5 #ff first time is 2.75 after this
        if self.Hitanim2 == True:
          self.HCount2 = self.HCount2 + 1
          self.HCountAni = False
          if self.HCount2 > 12:
            if not event.length > (1.4 * (60000.0 / event.noteBpm) / 4):
              self.HCount2 = 0
            else:
              self.HCountAni = True
          if event.flameCount < flameLimitHalf:
        
              HIndex = (self.HCount2 * 13 - (self.HCount2 * 13) % 13) / 13
              if HIndex > 12 and self.HCountAni != True:
                HIndex = 0
                  
              texX = (HIndex*(1/13.0), HIndex*(1/13.0)+(1/13.0))

              self.engine.draw3Dtex(self.hitflamesAnim, coord = (x, y + .665, 0), rot = (90, 1, 0, 0), scale = (1.6, 1.6, 4.9),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                    texcoord = (texX[0],0.0,texX[1],1.0), multiples = True, alpha = True, color = (1,1,1))

          else:
            flameColorMod = 0.1 * (flameLimit - event.flameCount)
            flamecol = tuple([ifc*flameColorMod for ifc in flameColor])
            scaleChange = (3.0,2.5,2.0,1.7)
            yOffset = (.35, .405, .355, .355)
            vtx = flameSize * ff
            scaleMod = .6 * ms * ff

            for step in range(4):              
              if step == 0:
                yzscaleMod = event.flameCount/ scaleChange[step]
              else:
                yzscaleMod = (event.flameCount + 1)/ scaleChange[step]
                  
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: 
                  spcolmod = .7+step*.1
                  flamecol = tuple([isp*spcolmod for isp in self.spColor])
                else:
                  flamecol = (.4+step*.1,)*3#Default starcolor (Rockband)
                
              if self.hitFlamesPresent == True:
                self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x - .005, y + yOffset[step], 0), rot = (90, 1, 0, 0),
                                scale = (.25 + step*.05 + scaleMod, yzscaleMod + scaleMod, yzscaleMod + scaleMod),
                                vertex = (-vtx,-vtx,vtx,vtx), texcoord = (0.0,0.0,1.0,1.0),
                                multiples = True, alpha = True, color = flamecol)
                                    
        elif self.Hitanim2 == False:
          self.HCount2 = 13
          self.HCountAni = True
          if event.flameCount < flameLimitHalf:
            
            flamecol = flameColor
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                spcolmod = .3
                flamecol = tuple([isp*spcolmod for isp in self.spColor])
              else: #Default starcolor (Rockband)
                flamecol = (.1,.1,.1)
                
            self.engine.draw3Dtex(self.hitflames2Drawing, coord = (x, y + .20, 0), rot = (90, 1, 0, 0),
                                  scale = (.25 + .6 * ms * ff, event.flameCount/6.0 + .6 * ms * ff, event.flameCount / 6.0 + .6 * ms * ff),
                                  vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                  multiples = True, alpha = True, color = flamecol)
              
                   
            for i in range(3):
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  spcolmod = 0.4+i*0.1
                  flamecol = tuple([isp*spcolmod for isp in self.spColor])
                else: #Default starcolor (Rockband)
                  flamecol = (0.1+i*0.1,)*3
              self.engine.draw3Dtex(self.hitflames2Drawing, coord = (x-.005, y + .255, 0), rot = (90, 1, 0, 0),
                                    scale = (.30 + i*0.05 + .6 * ms * ff, event.flameCount/(5.5 - i*0.4) + .6 * ms * ff, event.flameCount / (5.5 - i*0.4) + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                    multiples = True, alpha = True, color = flamecol)

          else:
            flameColorMod = 0.1 * (flameLimit - event.flameCount)
            flamecol = tuple([ifc*flameColorMod for ifc in flameColor])
            scaleChange = (3.0,2.5,2.0,1.7)
            yOffset = (.35, .405, .355, .355)
            vtx = flameSize * ff
            scaleMod = .6 * ms * ff

            for step in range(4):
              
              if step == 0:
                yzscaleMod = event.flameCount/ scaleChange[step]
              else:
                yzscaleMod = (event.flameCount + 1)/ scaleChange[step]
                  
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: 
                  spcolmod = .7+step*.1
                  flamecol = tuple([isp*spcolmod for isp in self.spColor])
                else:
                  flamecol = (.4+step*.1,)*3#Default starcolor (Rockband)
                
              self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x - .005, y + yOffset[step], 0), rot = (90, 1, 0, 0),
                              scale = (.25 + step*.05 + scaleMod, yzscaleMod + scaleMod, yzscaleMod + scaleMod),
                              vertex = (-vtx,-vtx,vtx,vtx), texcoord = (0.0,0.0,1.0,1.0),
                              multiples = True, alpha = True, color = flamecol)
          event.flameCount += 1

      for step in range(4):
      #draw lightning in GH themes on SP gain
        if step == 0 and self.hitlightning and event.finalStar and self.spEnabled:
          self.engine.draw3Dtex(self.hitlightning, coord = (xlightning, y, 3.3), rot = (90, 1, 0, 0),
                                scale = (.15 + .5 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, 2),
                                vertex = (.4,-2,-.4,2), texcoord = (0.0,0.0,1.0,1.0),
                                multiples = True, alpha = True, color = (1,1,1))
          continue


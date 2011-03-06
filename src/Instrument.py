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





from Song import Note, Tempo
from Mesh import Mesh
from Shader import shaders
from OpenGL.GL import *
import Song
import Log
import math
import os #myfingershurt: needed for multi-OS file fetching
import numpy as np


class Instrument:
  def __init__(self, engine, playerObj, player = 0):
    self.engine         = engine

    self.starPowerDecreaseDivisor = 200.0/self.engine.audioSpeedFactor

    self.bigRockEndingMarkerSeen = False

    self.isStarPhrase = False
    self.finalStarSeen = False

    self.selectedString = 0
    self.time           = 0.0
    self.pickStartPos   = 0
    self.leftyMode      = False
    self.drumFlip       = False

    self.freestyleActive = False
    self.drumFillsActive = False
    
    self.incomingNeckMode = self.engine.config.get("game", "incoming_neck_mode")
    self.guitarSoloNeckMode = self.engine.config.get("game", "guitar_solo_neck")
    self.bigRockEndings = self.engine.config.get("game", "big_rock_endings")

    #For Animated notes
    self.noteSpinFrames = 16
    self.Animspeed      = 30 #Lower value = Faster animations
    self.indexCount     = 0
    self.noteSpinFrameIndex = 0

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

    self.currentBpm     = 120.0   #MFH - need a default 120BPM to be set in case a custom song has no tempo events.
    self.currentPeriod  = 60000.0 / self.currentBpm
    self.targetBpm      = self.currentBpm
    self.targetPeriod   = 60000.0 / self.targetBpm
    self.lastBpmChange  = -1.0
    self.baseBeat       = 0.0


    self.indexFps       = self.engine.config.get("video", "fps")

    self.Animspeed      = 30#Lower value = Faster animations
    #For Animated Starnotes
    self.indexCount     = 0
    #Alarian, For animated hitglow
    self.HCount         = 0
    self.HCount2        = 0
    self.Hitanim        = True
    self.Hitanim2       = True
    self.HCountAni      = False
    
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

    self.disableVBPM  = self.engine.config.get("game", "disable_vbpm")
    self.disableNoteSFX  = self.engine.config.get("video", "disable_notesfx")
    self.disableFretSFX  = self.engine.config.get("video", "disable_fretsfx")
    self.disableFlameSFX  = self.engine.config.get("video", "disable_flamesfx")

    # make glow.png optional, theme dependent
    if self.disableFretSFX != False:
      self.glowDrawing = None
    else:
      engine.loadImgDrawing(self, "glowDrawing", os.path.join("themes",themename,"glow.png"),  textureSize = (128, 128))
      if not self.glowDrawing:
        engine.loadImgDrawing(self, "glowDrawing", "glow.png")

    #MFH - making hitflames optional
    self.hitFlamesPresent = False
    if self.disableFlameSFX == True:
      self.hitFlamesPresent = True
      self.hitglow2Drawing = None
      self.hitglowDrawing = None
      self.hitglowAnim = None
      self.hitflamesAnim = None
      self.hitflames2Drawing = None
      self.hitflames1Drawing = None
    else:
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
            self.hitFlamesPresent = False   #MFH - shut down all flames if these are missing.
        else:
          self.hitglowDrawing = None
          self.hitFlamesPresent = False   #MFH - shut down all flames if these are missing.
        self.Hitanim = False

    engine.loadImgDrawing(self, "hitlightning", os.path.join("themes",themename,"lightning.png"),  textureSize = (128, 128))

    self.meshColor  = self.engine.theme.meshColor
    self.hopoColor  = self.engine.theme.hopoColor
    self.spotColor = self.engine.theme.spotColor   
    self.keyColor = self.engine.theme.keyColor
    self.key2Color = self.engine.theme.key2Color
    fC = [(.84, 1, .51), (1, .53, .5), (.98, .96, .42), (.64, .97, 1), (1, .87, .55)]
    if not self.engine.theme.glowColor == "frets":
      gC = self.engine.theme.glowColor
      fC = [gC, gC, gC, gC, gC]
    self.flameColors = [fC,fC,fC,fC]
    self.gh3flameColor = (.75,.36,.02)
    fS = [.075]*5
    self.flameSizes = [fS,fS,fS,fS]
    self.glowColor  = self.engine.theme.glowColor

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
  def checkPath(self, subdirectory, file, lastResort = False):
  #  parameters
  #     @subdirectory       the folder in the theme to search
  #                           if the instrument is drum or bass it will extend this
  #     @file               the file to search for
  #     @lastResort         if the file isn't even found in the default path then
  #                           resort to using the file in the data folder
  
    #Get theme
    themename = self.engine.data.themeLabel
    
    defaultpath = os.path.join("themes", themename, subdirectory)
    themepath = os.path.join("themes", themename, subdirectory)
    if self.isDrum:
      themepath = os.path.join(themepath, "drum")
    elif self.isBassGuitar:
      themepath = os.path.join(themepath, "bass")
          
    if self.engine.fileExists(os.path.join(themepath, file)):
      return os.path.join(themepath, file)
    else:
      if lastResort and not self.engine.fileExists(os.path.join(defaultpath, file)):
        return file
      return os.path.join(defaultpath, file)

  def loadNotes(self):
    engine = self.engine
    themename = self.engine.data.themeLabel

    get = lambda file: self.checkPath("notes", file)

    self.noteSpin = self.engine.config.get("performance", "animated_notes")

    self.spActTex = None
    self.noteTex = None
    self.noteButtons = None

    if self.twoDnote == True:
      if self.noteSpin:
        self.starSpinFrames = 16
        engine.loadImgDrawing(self, "noteAnimatedNormal", get("animated_normal.png"))
        engine.loadImgDrawing(self, "noteAnimatedHOPO", get("animated_hopo.png"))
        engine.loadImgDrawing(self, "noteAnimatedPower", get("animated_power.png"))
        engine.loadImgDrawing(self, "noteAnimatedPowerHOPO", get("animated_power_hopo.png"))
        engine.loadImgDrawing(self, "noteAnimatedPowerActive", get("animated_power_active.png"))
        engine.loadImgDrawing(self, "noteAnimatedPowerActiveHOPO", get("animated_power_active_hopo.png"))
        
        if self.isDrum:
          engine.loadImgDrawing(self, "noteOpenAnimatedPowerActive", get("animated_open_power_active.png"))
          engine.loadImgDrawing(self, "noteOpenAnimatedPower", get("animated_open_power.png"))
          engine.loadImgDrawing(self, "noteOpenAnimated", get("animated_open.png"))
        
        if self.gameMode2p == 6: #battle multiplayer
          if engine.loadImgDrawing(self, "noteButtons", get("spinnotesbattle.png")):
            self.starSpinFrames = 8

      if not self.isDrum and self.gameMode2p == 6: #battle multiplayer
        if not self.engine.loadImgDrawing(self, "noteButtons", get("notesbattle.png")):
          engine.loadImgDrawing(self, "noteButtons", get("notes.png"))
      else:
        engine.loadImgDrawing(self, "noteButtons", get("notes.png"))
        
    else:
      defaultNote = False
      defaultOpenNote = False

      #MFH - can't use IOError for fallback logic for a Mesh() call... 
      if self.engine.fileExists(get("note.dae")): #look in the notes folder for files
        self.engine.resource.load(self,  "noteMesh",  lambda: Mesh(engine.resource.fileName(get("note.dae"))))
      else: #default to files in data folder
        self.engine.resource.load(self,  "noteMesh",  lambda: Mesh(engine.resource.fileName("note.dae")))
        defaultNote = True

      if self.engine.fileExists(get("star.dae")): #look in the notes folder for files
        self.engine.resource.load(self,  "starMesh",  lambda: Mesh(self.engine.resource.fileName(get("star.dae"))))
      else: #No mesh for star notes
        self.starMesh = None

      if self.isDrum:
        if self.engine.fileExists(get("open.dae")): #load from notes folder
          self.engine.resource.load(self,  "openMesh",  lambda: Mesh(self.engine.resource.fileName(get("open.dae"))))
        else: #fallback to the default in the data folder
          self.engine.resource.load(self,  "openMesh",  lambda: Mesh(self.engine.resource.fileName("open.dae")))
          defualtOpenNote = True

      if defaultNote:
        self.notetex = False

      else:
        self.notetex = True
        self.startex = True
        self.staratex = True
        
        for i in range(5):
          if not engine.loadImgDrawing(self,  "notetex"+chr(97+i),  get("notetex_"+chr(97+i)+".png")):
            self.notetex = False
            break
            
        for i in range(5):
          if not self.engine.loadImgDrawing(self,  "startex"+chr(97+i),  get("startex_"+chr(97+i)+".png")):
            self.startex = False
            break
            
        for i in range(5):
          if not self.engine.loadImgDrawing(self,  "staratex"+chr(97+i),  get("staratex_"+chr(97+i)+".png")):
            self.staratex = False
            break


      if self.isDrum: 
        engine.loadImgDrawing(self, "spActTex", get("spacttex.png"))
        

      if defaultOpenNote:
        self.opentexture = False
        self.opentexture_star = False
        self.opentexture_stara = False
      else:
        self.engine.loadImgDrawing(self, "opentexture", get("opentex.png"))
        self.engine.loadImgDrawing(self, "opentexture_star", get("opentex_star.png"))
        self.engine.loadImgDrawing(self, "opentexture_stara", get("opentex_stara.png"))
        
  def loadFrets(self):
    engine = self.engine
    themename = self.engine.data.themeLabel

    get = lambda file: self.checkPath("frets", file)

    if self.twoDkeys == True: #death_au

      if self.gameMode2p == 6:
        engine.loadImgDrawing(self, "battleFrets", get("battle_frets.png"))
        
      #death_au: adding drumfrets.png (with bass drum frets separate)
      if self.isDrum and engine.loadImgDrawing(self, "fretButtons", os.path.join("themes",themename, "frets", "drum", "fretbuttons.png")):
        self.drumFretButtons = True
      elif engine.loadImgDrawing(self, "fretButtons", get("fretbuttons.png")):
        self.drumFretButtons = None

    else:
      defaultKey = False
      defaultOpenKey = False

      #MFH - can't use IOError for fallback logic for a Mesh() call...
      if self.engine.fileExists(get("key.dae")): #look in the frets folder for files
        engine.resource.load(self,  "keyMesh",  lambda: Mesh(engine.resource.fileName(get("key.dae"))))
      else: #default to files in data folder
        engine.resource.load(self,  "keyMesh",  lambda: Mesh(engine.resource.fileName("key.dae")))
        defaultKey = True

      if self.isDrum:
        if self.engine.fileExists(get("open.dae")): #look in the frets folder for files
          engine.resource.load(self,  "keyMeshOpen",  lambda: Mesh(engine.resource.fileName(get("open.dae"))))
        else: #default to files in data folder
          engine.resource.load(self,  "keyMeshOpen",  lambda: Mesh(engine.resource.fileName("key_open.dae")))
          defaultOpenKey = True


      if defaultKey:
        self.keytex = False
      else:
        self.keytex = True
        for i in range(5):
          if not engine.loadImgDrawing(self,  "keytex"+chr(97+i),  get("keytex_"+chr(97+i)+".png")):
            self.keytex = False
            break

      if defaultOpenKey:
        self.keytexopen = False
      else:
        engine.loadImgDrawing(self, "keytexopen", get("keytex_open.png"))
        
  def loadTails(self):
    engine = self.engine
    themename = self.engine.data.themeLabel

    get = lambda file: self.checkPath("tails", file)
    getD = lambda file: self.checkPath("tails", file, True) #resorts to checking data
    
    #MFH - freestyle tails (for drum fills & BREs)
    engine.loadImgDrawing(self, "freestyle1", getD("freestyletail1.png"),  textureSize = (128, 128))
    engine.loadImgDrawing(self, "freestyle2", getD("freestyletail2.png"),  textureSize = (128, 128))

    if self.tailsEnabled == True:
      self.simpleTails = False
      for i in range(0,7):
        if not engine.loadImgDrawing(self, "tail"+str(i), get("tail"+str(i)+".png"),  textureSize = (128, 128)):
          self.simpleTails = True
          break
        if not engine.loadImgDrawing(self, "taile"+str(i), get("taile"+str(i)+".png"),  textureSize = (128, 128)):
          self.simpleTails = True
          break
        if not engine.loadImgDrawing(self, "btail"+str(i), get("btail"+str(i)+".png"),  textureSize = (128, 128)):
          self.simpleTails = True
          break
        if not engine.loadImgDrawing(self, "btaile"+str(i), get("btaile"+str(i)+".png"),  textureSize = (128, 128)):
          self.simpleTails = True
          break

      if self.simpleTails:
        Log.debug("Simple tails used; complex tail loading error...")
        engine.loadImgDrawing(self, "tail1", getD("tail1.png"),  textureSize = (128, 128))
        engine.loadImgDrawing(self, "tail2", getD("tail2.png"),  textureSize = (128, 128))
        engine.loadImgDrawing(self, "bigTail1", getD("bigtail1.png"),  textureSize = (128, 128))
        engine.loadImgDrawing(self, "bigTail2", getD("bigtail2.png"),  textureSize = (128, 128))
    
      engine.loadImgDrawing(self, "kill1", getD("kill1.png"),  textureSize = (128, 128))
      engine.loadImgDrawing(self, "kill2", getD("kill2.png"),  textureSize = (128, 128))

    else:
      self.tail1 = None
      self.tail2 = None
      self.bigTail1 = None
      self.bigTail2 = None
      self.kill1 = None
      self.kill2 = None

  def selectPreviousString(self):
    self.selectedString = (self.selectedString - 1) % self.strings

  def selectString(self, string):
    self.selectedString = string % self.strings

  def selectNextString(self):
    self.selectedString = (self.selectedString + 1) % self.strings

  def setMultiplier(self, multiplier):
    self.scoreMultiplier = multiplier
    self.neck.scoreMultiplier = multiplier

  def hitNote(self, time, note):
    self.pickStartPos = max(self.pickStartPos, time)
    self.playedNotes = [(time, note)]
    note.played       = True
    return True

  def endPick(self, pos):
    if not self.isDrum:
      for time, note in self.playedNotes:
        if time + note.length > pos + self.noteReleaseMargin:
          self.playedNotes = []
          return False
      
    self.playedNotes = []
    return True


  def setBPM(self, bpm):
    if bpm > 200:
      bpm = 200

    #MFH - Filter out unnecessary BPM settings (when currentBPM is already set!)
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

  #MFH - corrected and optimized:
  def getRequiredNotesMFH(self, song, pos, hopoTroubleCheck = False):
    if self.battleStatus[2] and self.difficulty != 0:
      if pos < self.battleStartTimes[2] + self.currentPeriod * self.beatsPerBoard or pos > self.battleStartTimes[2] - self.currentPeriod * self.beatsPerBoard + self.battleDiffUpLength:
        song.difficulty[self.player] = Song.difficulties[self.battleDiffUpValue]
      else:
        song.difficulty[self.player] = Song.difficulties[self.battleDiffUpValue - 1]

    track   = song.track[self.player]
    if hopoTroubleCheck:
      notes = [(time, event) for time, event in track.getEvents(pos, pos + (self.earlyMargin*2)) if isinstance(event, Note)]
      notes = [(time, event) for time, event in notes if not time==pos] #MFH - filter out the problem note that caused this check!
    else:
      notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + self.earlyMargin) if isinstance(event, Note)]
      notes = [(time, event) for time, event in notes if not (event.hopod or event.played or event.skipped)]
      notes = [(time, event) for time, event in notes if (time >= (pos - self.lateMargin)) and (time <= (pos + self.earlyMargin))]

    sorted(notes, key=lambda x: x[0])
    if self.battleStatus[7]:
      notes = self.getDoubleNotes(notes)
    return sorted(notes, key=lambda x: x[0])    #MFH - what the hell, this should be sorted by TIME not note number....

  #MFH - corrected and optimized:
  def getRequiredNotesForJurgenOnTime(self, song, pos):
    track   = song.track[self.player]
    notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + 30) if isinstance(event, Note)]
    notes = [(time, event) for time, event in notes if not (event.hopod or event.played or event.skipped)]

    if not self.isDrum:
      if self.battleStatus[7]:
        notes = self.getDoubleNotes(notes)
    return sorted(notes, key=lambda x: x[0])    #MFH - what the hell, this should be sorted by TIME not note number....

  def areNotesTappable(self, notes):
    if not notes:
      return
    for time, note in notes:
      if note.tappable > 1:
        return True
    return False

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
    if not song or self.flameColors[0][0][0] == -1:
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

        if f:
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
              
          if self.Hitanim != True and self.disableFlameSFX != True:
            self.engine.draw3Dtex(self.hitglowDrawing, coord = (x, y + .125, 0), rot = (90, 1, 0, 0),
                                  scale = (0.5 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff),
                                  vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                  texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)
            #Alarian: Animated hitflames
          else:
            self.HCount = self.HCount + 1
            if self.HCount > self.Animspeed-1:
              self.HCount = 0
            HIndex = (self.HCount * 16 - (self.HCount * 16) % self.Animspeed) / self.Animspeed
            if HIndex > 15:
              HIndex = 0
            texX = (HIndex*(1/16.0), HIndex*(1/16.0)+(1/16.0))
            if self.disableFlameSFX != True:
              self.engine.draw3Dtex(self.hitglowAnim, coord = (x, y + .225, 0), rot = (90, 1, 0, 0), scale = (2.4, 1, 3.3),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                    texcoord = (texX[0],0.0,texX[1],1.0), multiples = True, alpha = True, color = (1,1,1))

          ff += .3
          
          flameColorMod = (1.19, 1.78, 12.22)
          flamecol = tuple([flameColor[ifc]*flameColorMod[ifc] for ifc in range(3)])

          if self.starPowerActive:
            if self.theme == 0 or self.theme == 1: #GH3 starcolor
              flamecol = self.spColor
            else: #Default starcolor (Rockband)
              flamecol = (.8,.8,.8)

          if self.Hitanim != True and self.disableFlameSFX != True:
            self.engine.draw3Dtex(self.hitglow2Drawing, coord = (x, y + .25, .05), rot = (90, 1, 0, 0),
                                  scale = (.40 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff),
                                  vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                  texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)

    
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
              if self.disableFlameSFX != True:
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
              #draw lightning in GH themes on SP gain
              if step == 0 and event.finalStar and self.spEnabled and self.disableFlameSFX != True and self.hitlightning:
                self.engine.draw3Dtex(self.hitlightning, coord = (xlightning, y, 3.3), rot = (90, 1, 0, 0),
                                      scale = (.15 + .5 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, 2), vertex = (.4,-2,-.4,2),
                                      texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = (1,1,1))
                continue
            
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
              
              if self.hitFlamesPresent == True and self.disableFlameSFX != True:
                self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x - .005, y + yOffset[step], 0), rot = (90, 1, 0, 0),
                              scale = (.25 + step*.05 + scaleMod, yzscaleMod + scaleMod, yzscaleMod + scaleMod),
                              vertex = (-vtx,-vtx,vtx,vtx), texcoord = (0.0,0.0,1.0,1.0),
                              multiples = True, alpha = True, color = flamecol)
                                  
        elif self.hitFlamesPresent == True and self.Hitanim2 == False:
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
            if self.disableFlameSFX != True:  
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
              if self.disableFlameSFX != True:
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
              #draw lightning in GH themes on SP gain
              if step == 0 and event.finalStar and self.spEnabled and self.hitlightning:
                self.engine.draw3Dtex(self.hitlightning, coord = (xlightning, y, 3.3), rot = (90, 1, 0, 0),
                                    scale = (.15 + .5 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, 2), vertex = (.4,-2,-.4,2),
                                    texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = (1,1,1))
                continue
            
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
              if self.disableFlameSFX != True:
                self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x - .005, y + yOffset[step], 0), rot = (90, 1, 0, 0),
                                scale = (.25 + step*.05 + scaleMod, yzscaleMod + scaleMod, yzscaleMod + scaleMod),
                                vertex = (-vtx,-vtx,vtx,vtx), texcoord = (0.0,0.0,1.0,1.0),
                                multiples = True, alpha = True, color = flamecol)
        event.flameCount += 1

  def getRequiredNotesForRender(self, song, pos):
    if self.battleStatus[2] and self.difficulty != 0:
      Log.debug(self.battleDiffUpValue)
      song.difficulty[self.player] = Song.difficulties[self.battleDiffUpValue]
      track0 = song.track[self.player]
      notes0 = [(time, event) for time, event in track0.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard)]
    
      song.difficulty[self.player] = Song.difficulties[self.battleDiffUpValue - 1]
      track1   = song.track[self.player]
      notes1 = [(time, event) for time, event in track1.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard)]
      
      notes = []
      for time,note in notes0:
        if time < self.battleStartTimes[2] + self.currentPeriod * self.beatsPerBoard or time > self.battleStartTimes[2] - self.currentPeriod * self.beatsPerBoard + self.battleDiffUpLength:
          notes.append((time,note))
      for time,note in notes1:
        if time > self.battleStartTimes[2] + self.currentPeriod * self.beatsPerBoard and time < self.battleStartTimes[2] - self.currentPeriod * self.beatsPerBoard + self.battleDiffUpLength:
          notes.append((time,note))
      notes0 = None
      notes1 = None
      track0 = None
      track1 = None
      notes = sorted(notes, key=lambda x: x[0])
    else:
      track   = song.track[self.player]
      notes = [(time, event) for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard)]
    
    if self.battleStatus[7]:
      notes = self.getDoubleNotes(notes)
    return notes

  def renderNote(self, length, sustain, color, flat = False, tailOnly = False, isTappable = False, fret = 0, spNote = False, isOpen = False, spAct = False):

    if flat:
      glScalef(1, .1, 1)

    if tailOnly:
      return

    if self.isDrum:
      self.strings        = 4
    else:
      self.strings        = 5
	

    #myfingershurt: this should be retrieved once at init, not repeatedly in-game whenever tails are rendered.

    if self.twoDnote == True:

      noteImage = self.noteButtons

      if self.notedisappear ==0:#Notes keep on going when missed
        notecol = (1,1,1)#capo
      elif self.notedisappear == 1:#Notes disappear when missed
        notecol = (.1,.1,.1)
      elif self.notedisappear == 2: #Notes Turn Red when missed
        notecol = (1,0,0,1) 

      tailOnly = True

      if isOpen:
        size = (self.boardWidth/1.9, (self.boardWidth/self.strings)/3.0)
        texSize = (0,1)
        if spNote == True:
          if self.noteOpenAnimatedPower:
            noteImage = self.noteDrumOpenAnimatedPower
            texY = (self.noteSpinFrameIndex*.066667, (self.noteSpinFrameIndex - 1)*.066667)
          else:
            texY = (3.0*0.166667,4.0*0.166667)

        elif self.starPowerActive == True: #death_au: drum sp active notes.
          if self.noteOpenAnimatedPowerActive:
            noteImage = self.noteDrumOpenAnimatedPowerActive
            texY = (self.noteSpinFrameIndex*.066667, (self.noteSpinFrameIndex - 1)*.066667)
          else:
            texY = (5.0*0.166667,1.0)

        else:
          if self.noteOpenAnimated:
            noteImage = self.noteDrumOpenAnimated
            texY = (self.noteSpinFrameIndex*.066667, (self.noteSpinFrameIndex - 1)*.066667)
          else:
            texY = (1.0*0.166667,2.0*0.166667)

      else:
        size = (self.boardWidth/self.strings/2, self.boardWidth/self.strings/2)
        if self.isDrum:
          fret -= 1
        texSize = (fret/self.lanenumber,fret/self.lanenumber+1/self.lanenumber)
        if spNote == True:
          if isTappable:
            if self.noteAnimatedPowerHOPO:
              noteImage = self.noteAnimatedPowerHOPO
              texY = (self.noteSpinFrameIndex*.066667, (self.noteSpinFrameIndex - 1)*.066667)
            else:
              texY = (3*0.166667, 4*0.166667)
          else:
            if self.noteAnimatedPower:
              noteImage = self.noteAnimatedPower
              texY = (self.noteSpinFrameIndex*.066667, (self.noteSpinFrameIndex - 1)*.066667)
            else:
              texY = (2*0.166667, 3*0.166667)

        elif self.starPowerActive:
          if isTappable:
            if self.noteAnimatedPowerActiveHOPO:
              noteImage = self.noteAnimatedPowerActiveHOPO
              texY = (self.noteSpinFrameIndex*.066667, (self.noteSpinFrameIndex - 1)*.066667)
            else:
              texY = (5*0.166667, 1)
          else:
            if self.noteAnimatedPowerActive:
              noteImage = self.noteAnimatedPowerActive
              texY = (self.noteSpinFrameIndex*.066667, (self.noteSpinFrameIndex - 1)*.066667)
            else:
              texY = (4*0.166667, 5*0.166667)

        else:
          if isTappable:
            if self.noteAnimatedHOPO:
              noteImage = self.noteAnimatedHOPO
              texY = (self.noteSpinFrameIndex*.066667, (self.noteSpinFrameIndex - 1)*.066667)
            else:
              texY = (1*0.166667, 2*0.166667)
          else:
            if self.noteAnimatedNormal:
              noteImage = self.noteAnimatedNormal
              texY = (self.noteSpinFrameIndex*.066667, (self.noteSpinFrameIndex - 1)*.066667)
            else:
              texY = (0, 1*0.166667)

      self.engine.draw3Dtex(noteImage, vertex = (-size[0],size[1],size[0],-size[1]), texcoord = (texSize[0],texY[0],texSize[1],texY[1]),
                            scale = (1,1,0), rot = (30,1,0,0), multiples = False, color = color, vertscale = .27)

    else: #3d Notes
      shaders.setVar("Material",color,"notes")

      if self.isDrum:
        self.notepos = self.engine.theme.drumnotepos
        self.noterot = self.engine.theme.drumnoterot
      else:
        self.notepos = self.engine.theme.notepos
        self.noterot = self.engine.theme.noterot

      #mesh = outer ring (black) 
      #mesh_001 = main note (key color) 
      #mesh_002 = top (spot or hopo if no mesh_003) 
      #mesh_003 = hopo bump (hopo color)

      if self.isDrum:
        if fret == 0:
          fret = 4     #fret 4 is angled, get fret 2 :)
          #fret = 2    #compensating for this in drum.
        elif fret == 4:
          fret = 0

      if spNote == True and self.starMesh is not None and isOpen == False:
        meshObj = self.starMesh
      elif isOpen == True and self.openMesh is not None:
        meshObj = self.openMesh
      else:
        meshObj = self.noteMesh

      glPushMatrix()
      glEnable(GL_DEPTH_TEST)
      glDepthMask(1)
      glShadeModel(GL_SMOOTH)

      if spNote == True and self.threeDspin == True and isOpen == False:
        glRotate(90 + self.time/3, 0, 1, 0)
      if isOpen == False and spNote == False and self.noterotate == True:
        glRotatef(90, 0, 1, 0)
        glRotatef(-90, 1, 0, 0)

      if fret == 0: # green note/ drums open note
        glRotate(self.noterot[0], 0, 0, 1), glTranslatef(0, self.notepos[0], 0)
      elif fret == 1: # red note
        glRotate(self.noterot[1], 0, 0, 1), glTranslatef(0, self.notepos[1], 0)
      elif fret == 2: # yellow
        glRotate(self.noterot[2], 0, 0, 1), glTranslatef(0, self.notepos[2], 0)
      elif fret == 3:# blue note
        glRotate(self.noterot[3], 0, 0, 1), glTranslatef(0, self.notepos[3], 0)
      elif fret == 4:# orange note / green on drums
        glRotate(self.noterot[4], 0, 0, 1), glTranslatef(0, self.notepos[4], 0)

      if isOpen:
        if self.opentexture_stara and spNote==False and self.starPowerActive:
          self.noteTex = self.opentexture_stara
		  
        elif self.opentexture and spNote==False:
          self.noteTex = self.opentexture

        elif self.opentexture_star and spNote==True:
          self.noteTex = self.opentexture_star

      elif self.spActTex and isOpen == False and spNote == False and spAct and self.isDrum:
        self.noteTex = self.spActTex

      elif self.staratex == True and self.starPowerActive and spNote == False and isOpen == False:
        self.noteTex = getattr(self,"staratex"+chr(97+fret))

      elif self.notetex == True and spNote == False and isOpen == False:
        self.noteTex = getattr(self,"notetex"+chr(97+fret))

      elif self.startex == True and spNote == True and isOpen == False:
        self.noteTex = getattr(self,"startex"+chr(97+fret))


      glColor3f(1,1,1)
      glEnable(GL_TEXTURE_2D)
      self.noteTex.texture.bind()
      glMatrixMode(GL_TEXTURE)
      glScalef(1, -1, 1)
      glMatrixMode(GL_MODELVIEW)
      glScalef(self.boardScaleX, self.boardScaleY, 1)

      if isTappable:
        mesh = "Mesh_001"
      else:
        mesh = "Mesh"

      meshObj.render(mesh)

      if shaders.enable("notes"):
        shaders.setVar("isTextured",True)
        meshObj.render(mesh)
        shaders.disable() 

      glMatrixMode(GL_TEXTURE)
      glLoadIdentity()
      glMatrixMode(GL_MODELVIEW)
      glDisable(GL_TEXTURE_2D)


      if not self.noteTex: 
        #death_au: fixed 3D note colours
        glColor4f(*color)
        if isOpen == True and self.starPowerActive == False:
          glColor4f(self.opencolor[0],self.opencolor[1],self.opencolor[2], 1)
        if shaders.enable("notes"):
          shaders.setVar("isTextured",False)
        meshObj.render("Mesh_001")
        shaders.disable()
        glColor3f(self.spotColor[0], self.spotColor[1], self.spotColor[2])
        if isTappable:
          if self.hopoColor[0] == -2:
            glColor4f(*color)
          else:
            glColor3f(self.hopoColor[0], self.hopoColor[1], self.hopoColor[2])
          if(meshObj.find("Mesh_003")) == True:
            meshObj.render("Mesh_003")
            glColor3f(self.spotColor[0], self.spotColor[1], self.spotColor[2])
        meshObj.render("Mesh_002")
        glColor3f(self.meshColor[0], self.meshColor[1], self.meshColor[2])
        meshObj.render("Mesh")


      glDepthMask(0)
      glPopMatrix()
      glDisable(GL_DEPTH_TEST)

  def renderNotes(self, visibility, song, pos):
    if not song:
      return
    if not song.readyToGo:
      return

    self.bigMax = 0

    # Update dynamic period
    self.currentPeriod = self.neckSpeed
    self.targetPeriod  = self.neckSpeed

    self.killPoints = False

    w = self.boardWidth / self.strings
    track = song.track[self.player]

    num = 0
    enable = True
    self.starNotesInView = False
    self.openStarNotesInView = False

    if self.isDrum:
      self.strings        = 4
    else:
      self.strings        = 5

    renderedNotes = reversed(self.getRequiredNotesForRender(song,pos))
    for time, event in renderedNotes:

      if isinstance(event, Tempo):

        self.tempoBpm = event.bpm
        if self.lastBpmChange > 0 and self.disableVBPM == True:
          continue
        if (pos - time > self.currentPeriod or self.lastBpmChange < 0) and time > self.lastBpmChange:
          self.baseBeat          += (time - self.lastBpmChange) / self.currentPeriod
          self.targetBpm          = event.bpm
          self.lastBpmChange      = time
          self.neck.lastBpmChange = time
          self.neck.baseBeat      = self.baseBeat
        continue

      if not isinstance(event, Note):
        continue

      if (event.noteBpm == 0.0):
        event.noteBpm = self.tempoBpm

      if event.number == 0 and self.isDrum: #MFH - skip all open notes
        continue
      
      if self.coOpFailed:
        if self.coOpRestart:
          if time - self.coOpRescueTime < (self.currentPeriod * self.beatsPerBoard * 2):
            continue
          elif self.coOpRescueTime + (self.currentPeriod * self.beatsPerBoard * 2) < pos:
            self.coOpFailed = False
            self.coOpRestart = False
            Log.debug("Turning off coOpFailed. Rescue successful.")
        else:
          continue #can't break. Tempo.

      if self.isDrum:
        x  = (self.strings / 2 - .5 - (event.number - 1)) * w
        isOpen = False
        c = self.fretColors[event.number]
      else:
        x  = (self.strings / 2 - (event.number)) * w
        isOpen = False
        c = self.fretColors[event.number]

      if event.number == 4 and self.isDrum:
        c = self.fretColors[0]        #myfingershurt: need to swap note 0 and note 4 colors for drums:

      z  = ((time - pos) / self.currentPeriod) / self.beatsPerUnit
      z2 = ((time + event.length - pos) / self.currentPeriod) / self.beatsPerUnit

      if z > self.boardLength * .8:
        f = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        f = min(1, max(0, 1 + z2))
      else:
        f = 1.0

      #volshebnyi - hide notes in BRE zone if BRE enabled  
      if self.freestyleEnabled:
        if self.isDrum:
          if self.drumFillsReady or self.freestyleReady:  
            if time > self.freestyleStart - self.freestyleOffset and time < self.freestyleStart + self.freestyleOffset + self.freestyleLength:
              z = -2.0
        else:
          if time > self.freestyleStart - self.freestyleOffset and time < self.freestyleStart + self.freestyleOffset + self.freestyleLength:
            z = -2.0

      if self.twoDnote == True and not self.useFretColors:
        color      = (1,1,1, 1 * visibility * f)
      else:
        color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1 * visibility * f)

      if self.isDrum:
        length     = 0
      else:
        if event.length > 120:
          length     = (event.length - 50) / self.currentPeriod / self.beatsPerUnit
        else:
          length     = 0

      flat       = False
      tailOnly   = False
      spNote = False

      #myfingershurt: user setting for starpower refill / replenish notes
      if self.starPowerActive:
        if self.spRefillMode == 0:    #mode 0 = no starpower / overdrive refill notes
          self.spEnabled = False
        elif self.spRefillMode == 1 and self.theme != 2:  #mode 1 = overdrive refill notes in RB themes only
          self.spEnabled = False
        elif self.spRefillMode == 2 and song.midiStyle != 1: #mode 2 = refill based on MIDI type
          self.spEnabled = False

      if event.star:
        self.starNotesInView = True
      if event.finalStar:
        self.finalStarSeen = True
        self.starNotesInView = True

      if event.star and self.spEnabled:
        spNote = True
      if event.finalStar and self.spEnabled:
        spNote = True
        if event.played or event.hopod:
          if event.flameCount < 1 and not self.starPowerGained:
            if self.starPower < 50:   #not enough starpower to activate yet, kill existing drumfills
              for dfEvent in self.drumFillEvents:
                dfEvent.happened = True
            Log.debug("star power added")
            if self.gameMode2p == 6 and not self.isDrum:
              if self.battleSuddenDeath:
                self.battleObjects = [1] + self.battleObjects[:2]
              else:
                self.battleObjects = [self.battleObjectsEnabled[random.randint(0,len(self.battleObjectsEnabled)-1)]] + self.battleObjects[:2]
              self.battleGetTime = pos
              self.battleObjectGained = True
              Log.debug("Battle Object Gained, Objects %s" % str(self.battleObjects))
            else:
              if self.starPower < 100:
                self.starPower += 25
              if self.starPower > 100:
                self.starPower = 100
            self.overdriveFlashCount = 0  #MFH - this triggers the oFlash strings & timer
            self.starPowerGained = True


      if event.tappable < 2 or self.isDrum:
        isTappable = False
      else:
        isTappable = True

      if self.notedisappear == 0:#Notes keep on going when missed
        if event.played or event.hopod:#if the note isnt missed
          tailOnly = True
          length += z
          z = 0
          if length <= 0:
            continue
        if z < 0 and not (event.played or event.hopod):#if the note is missed 
          color = (.6, .6, .6, .5 * visibility * f)
          flat  = False
      elif self.notedisappear == 1:#Notes disappear when missed
        if z < 0:#if note past frets
          if event.played or event.hopod:#if note was hit
            tailOnly = True
            length += z
            z = 0
            if length <= 0:
              continue
          else:#note missed
            color = (.6, .6, .6, .5 * visibility * f)
            flat  = False
      if self.notedisappear == 2:#turn red when missed
        if event.played or event.hopod:  #if the note isnt missed
          tailOnly = True
          length += z
          z = 0
          if length <= 0:
            continue
        if z < 0 and not (event.played or event.hopod): #if the note is missed 
          color = (1, 0, 0, 1)#turn note red
          flat  = False

      if self.isDrum:
        sustain = False

        glPushMatrix()
        glTranslatef(x, 0, z)
        self.renderNote(length, sustain = sustain, color = color, flat = flat, tailOnly = tailOnly, isTappable = isTappable, fret = event.number, spNote = spNote, isOpen = isOpen)
        glPopMatrix()
      else:
        if z + length < -1.0:
          continue
        if event.length <= 120:
         length = None

        sustain = False
        if event.length > (1.4 * (60000.0 / event.noteBpm) / 4):
          sustain = True
        
        glPushMatrix()
        glTranslatef(x, 0, z)
      
        if shaders.turnon:
          shaders.setVar("note_position",(x, (1.0 - visibility) ** (event.number + 1), z),"notes")

        if self.battleStatus[8]:
          renderNote = random.randint(0,2)
        else:
          renderNote = 0
        if renderNote == 0:
          self.renderNote(length, sustain = sustain, color = color, flat = flat, tailOnly = tailOnly, isTappable = isTappable, fret = event.number, spNote = spNote)
        glPopMatrix()

    #myfingershurt: end FOR loop / note rendering loop       
    if (not self.openStarNotesInView) and (not self.starNotesInView) and self.finalStarSeen:
      self.spEnabled = True
      self.isStarPhrase = False
      self.finalStarSeen = False

  def renderOpenNotes(self, visibility, song, pos):
    if not song:
      return
    if not song.readyToGo:
      return

    self.bigMax = 0

    self.currentPeriod = self.neckSpeed
    self.targetPeriod  = self.neckSpeed

    self.killPoints = False

    w = self.boardWidth / self.strings
    track = song.track[self.player]

    num = 0
    enable = True
    self.openStarNotesInView = False

    if self.isDrum:
      self.strings        = 4
    else:
      self.strings        = 5

    renderedNotes = reversed(self.getRequiredNotesForRender(song,pos))
    for time, event in renderedNotes:

      if isinstance(event, Tempo):

        self.tempoBpm = event.bpm
        if self.lastBpmChange > 0 and self.disableVBPM == True:
          continue
        if (pos - time > self.currentPeriod or self.lastBpmChange < 0) and time > self.lastBpmChange:
          self.baseBeat          += (time - self.lastBpmChange) / self.currentPeriod
          self.targetBpm          = event.bpm
          self.lastBpmChange      = time
          self.neck.lastBpmChange = time
          self.neck.baseBeat      = self.baseBeat
        continue

      if not isinstance(event, Note):
        continue

      if (event.noteBpm == 0.0):
        event.noteBpm = self.tempoBpm
      
      if self.coOpFailed:
        if self.coOpRestart:
          if time - self.coOpRescueTime < (self.currentPeriod * self.beatsPerBoard * 2):
            continue
          elif self.coOpRescueTime + (self.currentPeriod * self.beatsPerBoard * 2) < pos:
            self.coOpFailed = False
            self.coOpRestart = False
            Log.debug("Turning off coOpFailed. Rescue successful.")
        else:
          continue #can't break. Tempo.

      if not event.number == 0: #if Normal note exit
        continue

      isOpen     = True
      x  = 0
      c = self.openFretColor
      z  = ((time - pos) / self.currentPeriod) / self.beatsPerUnit

      if z > self.boardLength * .8:
        f = (self.boardLength - z) / (self.boardLength * .2)
      else:
        f = 1.0

      #volshebnyi - hide notes in BRE zone if BRE enabled  
      if self.freestyleEnabled:
        if self.isDrum:
          if self.drumFillsReady or self.freestyleReady:  
            if time > self.freestyleStart - self.freestyleOffset and time < self.freestyleStart + self.freestyleOffset + self.freestyleLength:
              z = -2.0
        else:
          if time > self.freestyleStart - self.freestyleOffset and time < self.freestyleStart + self.freestyleOffset + self.freestyleLength:
            z = -2.0

      if self.twoDnote == True and not self.useFretColors:
        color      = (1,1,1, 1 * visibility * f)
      else:
        color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1 * visibility * f)

      length     = 0

      flat       = False
      tailOnly   = False
      spNote = False

      #myfingershurt: user setting for starpower refill / replenish notes
      if self.starPowerActive:
        if self.spRefillMode == 0:    #mode 0 = no starpower / overdrive refill notes
          self.spEnabled = False
        elif self.spRefillMode == 1 and self.theme != 2:  #mode 1 = overdrive refill notes in RB themes only
          self.spEnabled = False
        elif self.spRefillMode == 2 and song.midiStyle != 1: #mode 2 = refill based on MIDI type
          self.spEnabled = False

      if event.star:
        self.openStarNotesInView = True
      if event.finalStar:
        self.finalStarSeen = True
        self.openStarNotesInView = True

      if event.star and self.spEnabled:
        spNote = True
      if event.finalStar and self.spEnabled:
        spNote = True
        if event.played or event.hopod:
          if event.flameCount < 1 and not self.starPowerGained:

            if self.starPower < 50:   #not enough starpower to activate yet, kill existing drumfills
              for dfEvent in self.drumFillEvents:
                dfEvent.happened = True

            if self.starPower < 100:
              self.starPower += 25
            if self.starPower > 100:
              self.starPower = 100
            self.overdriveFlashCount = 0  #MFH - this triggers the oFlash strings & timer
            self.starPowerGained = True


      isTappable = False
      if (event.played or event.hopod):
	    continue
      if self.notedisappear == 0:#Notes keep on going when missed
        if z < 0 and not (event.played or event.hopod):#if the note is missed 
          color = (.6, .6, .6, .5 * visibility * f)
          flat  = False 
      elif self.notedisappear == 1:#Notes disappear when missed
        if z < 0 and not (event.played or event.hopod):
              continue
      if self.notedisappear == 2:#turn red when missed
        if z < 0 and not (event.played or event.hopod): #if the note is missed 
          color = (1, 0, 0, 1)#turn note red
          flat  = False

      sustain = False

      glPushMatrix()
      glTranslatef(x, 0, z)
      self.renderNote(length, sustain = sustain, color = color, flat = flat, tailOnly = tailOnly, isTappable = isTappable, fret = event.number, spNote = spNote, isOpen = isOpen)
      glPopMatrix()

    #myfingershurt: end FOR loop / note rendering loop       
    if (not self.openStarNotesInView) and (not self.starNotesInView) and self.finalStarSeen:
      self.spEnabled = True
      self.finalStarSeen = False
      self.isStarPhrase = Fals

  def coOpRescue(self, pos):
    self.coOpRestart = True #initializes Restart Timer
    self.coOpRescueTime  = pos
    self.starPower  = 0
    Log.debug("Rescued at " + str(pos))

  def renderFrets(self, visibility, song, controls):
    w = self.boardWidth / self.strings
    size = (.22, .22)
    v = 1.0 - visibility

    if self.isDrum:
      self.strings2      = self.strings + 1 #+1 is for the bass drum fret
    else:
      self.strings2      = self.strings

    #weirdpeople - If depth test is on, the drums bass fret will not be seen as death_au said (his comment below)
    #If it is off and 3d frets and notes are used it messes several things up, things flash 
	#on fretboard, and 3d frets / notes go through the fretboard (half of the note/fret is through the fretboard)
	#was tested with fuzions 4x theme

    #death_au:
    #if we leave the depth test enabled, it thinks that the bass drum images
    #are under the other frets and openGL culls them. So I just leave it disabled
	
    glEnable(GL_DEPTH_TEST)
	
    for n in range(self.strings2):
      if self.isDrum:
        if n == 4:
          keyNumb = 0
        else:
          keyNumb = n + 1
      if self.isDrum:#Drum related fret press things
        f = self.drumsHeldDown[keyNumb]/200.0
        pressed = self.drumsHeldDown[keyNumb]

        if not n == 4: #Set colors of frets
          if n == 3:
            c = self.fretColors[0]
          else:
            c = self.fretColors[n + 1]

      else: #Guitar fret colors and things
        pressed = None #to make sure guitar doesnt crash
        keyNumb = n
        f = self.fretWeight[keyNumb]
        c = self.fretColors[keyNumb]

      glColor4f(.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, visibility)


      if self.isDrum and n == 4:
        y = v + f / 6
      else:
        y = v / 6

      if self.isDrum and n == 4:#bass fret x position
        x = 0

      elif self.isDrum: #drum fret x position
        x = (self.strings / 2 - .5 - n) * w

      else: #guitar fret x position
        x = (self.strings / 2 - n) * w

      if self.twoDkeys == True:

        if self.isDrum and n == 4: #Weirdpeople - so the drum bass fret can be seen with 2d frets
          glDisable(GL_DEPTH_TEST)
	  
        fretColor = (1,1,1,1)

        if self.isDrum and n == 4:
          size = (self.boardWidth/2, self.boardWidth/self.strings/2.4)
        else:
         size = (self.boardWidth / self.strings / 2, self.boardWidth / self.strings / 2.4)

        if self.isDrum and n == 4:
          texSize = (0.0,1.0)
        else:
          texSize = (n / self.lanenumber, n / self.lanenumber + 1 / self.lanenumber)

        if self.drumFretButtons == None and self.isDrum:
          if n == 4:
            continue
          whichFret = n+1
          if whichFret == 4:
            whichFret = 0
            #reversing fret 0 since it's angled in Rock Band
            texSize = (whichFret/5.0+0.2,whichFret/5.0)

          else:
            texSize = (whichFret/5.0,whichFret/5.0+0.2)

          texY = (0.0,1.0/3.0)
          if pressed:
            texY = (1.0/3.0,2.0/3.0)
          if self.hit[n]:
            texY = (2.0/3.0,1.0)

        elif self.battleStatus[3] and self.battleFrets != None and self.battleBreakString == n:
          texSize = (n/5.0+.042,n/5.0+0.158)
          size = (.30, .40)
          fretPos = 8 - round((self.battleBreakNow/self.battleBreakLimit) * 8)
          texY = (fretPos/8.0,(fretPos + 1.0)/8)

        else:
          if self.isDrum and n == 4: #fret normal bass drum
            texY = (1.0 / self.fretImgColNumber, 2.0 / self.fretImgColNumber)
          else:#fret normall all other's (guitar, drums normal frets)
            texY = (0.0, 1.0 / self.fretImgColNumber)#fret normal guitar/bass/drums

          if self.isDrum and n == 4 and pressed:#drums bass fret press
            texY = (3.0 / self.fretImgColNumber, 4.0 / self.fretImgColNumber)

          elif controls.getState(self.keys[n]) or controls.getState(self.keys[n+5]) or (self.isDrum and pressed):#fret press
            if self.isDrum: #drum
              texY = (2.0 / self.fretImgColNumber, 3.0 / self.fretImgColNumber)
            else: #guitar / bass 
		      texY = (1.0 / self.fretImgColNumber, 2.0 / self.fretImgColNumber)

          elif self.isDrum and n == 4 and self.hit[0]:#drum bass hit fret
            texY = (5.0 / self.fretImgColNumber, 1.0)

          elif self.hit[n] or (self.battleStatus[3] and self.battleBreakString == n):#frets on note hit
            if self.isDrum: #drum
              texY = (4.0 / self.fretImgColNumber, 5.0 / self.fretImgColNumber)
            else: #guitar / bass
              texY = (2.0 / self.fretImgColNumber,1.0)

        self.engine.draw3Dtex(self.fretButtons, vertex = (size[0],size[1],-size[0],-size[1]), texcoord = (texSize[0], texY[0], texSize[1], texY[1]),
                                coord = (x,v,0), multiples = True,color = fretColor, depth = True)

  
      else:
        if self.isDrum:
          self.keypos = self.engine.theme.drumkeypos
          self.keyrot = self.engine.theme.drumkeyrot
        else:
          self.keypos = self.engine.theme.keypos
          self.keyrot = self.engine.theme.keyrot

        if self.keyMesh:
          glPushMatrix()
          glDepthMask(1)
          glEnable(GL_LIGHTING)
          glEnable(GL_LIGHT0)
          glShadeModel(GL_SMOOTH)
          glRotatef(90, 0, 1, 0)
          glLightfv(GL_LIGHT0, GL_POSITION, np.array([5.0, 10.0, -10.0, 0.0], dtype=np.float32))
          glLightfv(GL_LIGHT0, GL_AMBIENT, np.array([0.2, 0.2, 0.2, 0.0], dtype=np.float32))
          glLightfv(GL_LIGHT0, GL_DIFFUSE, np.array([1.0, 1.0, 1.0, 0.0], dtype=np.float32))
          
          
          glRotatef(-90, 1, 0, 0)
          glRotatef(-90, 0, 0, 1)

          if n == 0: #green fret button
            glRotate(self.keyrot[0], 0, 1, 0), glTranslatef(0, 0, self.keypos[0])
          elif n == 1: #red fret button
            glRotate(self.keyrot[1], 0, 1, 0), glTranslatef(0, 0, self.keypos[1])
          elif n == 2: #yellow fret button
            glRotate(self.keyrot[2], 0, 1, 0), glTranslatef(0, 0, self.keypos[2])
          elif n == 3: #blue fret button
            glRotate(self.keyrot[3], 0, 1, 0), glTranslatef(0, 0, self.keypos[3])
          elif n == 4: #orange fret button
            glRotate(self.keyrot[4], 0, 1, 0), glTranslatef(0, 0, self.keypos[4])

          #Mesh - Main fret
          #Key_001 - Top of fret (key_color)
          #Key_002 - Bottom of fret (key2_color)
          #Glow_001 - Only rendered when a note is hit along with the glow.svg

          if self.keytex == True:
            glColor4f(1,1,1,visibility)
            if self.battleStatus[4]:
              glTranslatef(x, y + self.battleWhammyNow * .15, 0)
            else:
              glTranslatef(x, y, 0)
            glEnable(GL_TEXTURE_2D)
            if self.isDrum:
              if n == 0:
                self.keytexb.texture.bind()
              elif n == 1:
                self.keytexc.texture.bind()
              elif n == 2:
                self.keytexd.texture.bind()
              elif n == 3:
                self.keytexa.texture.bind()
              elif n == 4:
                self.keytexopen.texture.bind()
            else:
              getattr(self,"keytex"+chr(97+n)).texture.bind()
            glMatrixMode(GL_TEXTURE)
            glScalef(1, -1, 1)
            glMatrixMode(GL_MODELVIEW)
            glScalef(self.boardScaleX, self.boardScaleY, 1)
            if self.isDrum and n == 4:
                key = self.keyMeshOpen
            else:
              key = self.keyMesh
            if not self.hit[keyNumb] and (f or pressed):
              key.render("Mesh_001")
            elif self.hit[keyNumb]:
              key.render("Mesh_002")
            else:
              key.render("Mesh")
            glMatrixMode(GL_TEXTURE)
            glLoadIdentity()
            glMatrixMode(GL_MODELVIEW)
            glDisable(GL_TEXTURE_2D)
          else:
            glColor4f(.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, visibility)
            if self.battleStatus[4]:
              glTranslatef(x, y + self.battleWhammyNow * .15 + v * 6, 0)
            else:
              glTranslatef(x, y + v * 6, 0)
            key = self.keyMesh
        
            if(key.find("Glow_001")) == True:
              key.render("Mesh")
              if(key.find("Key_001")) == True:
                glColor3f(self.keyColor[0], self.keyColor[1], self.keyColor[2])
                key.render("Key_001")
              if(key.find("Key_002")) == True:
                glColor3f(self.key2Color[0], self.key2Color[1], self.key2Color[2])
                key.render("Key_002")
            else:
              key.render()
          
          glDisable(GL_LIGHTING)
          glDisable(GL_LIGHT0)
          glDepthMask(0)
          glPopMatrix()

    glDisable(GL_DEPTH_TEST)

  def noteBeingHeld(self):
    noteHeld = False
    if self.isDrum:
      return noteHeld
    for i in range(0,5):
      if self.hit[i] == True:
        noteHeld = True
    return noteHeld

  def isKillswitchPossible(self):
    possible = False
    if self.isDrum:
      return possible
    for i in range(0,5):
      if self.hit[i] == True:
        possible = True
    return possible

  def renderTail(self, length, sustain, kill, color, flat = False, tailOnly = False, isTappable = False, big = False, fret = 0, freestyleTail = 0, pos = 0):

    #volshebnyi - if freestyleTail == 0, act normally.
    #  if freestyleTail == 1, render an freestyle tail
    #  if freestyleTail == 2, render highlighted freestyle tail

    if not self.isDrum and not self.simpleTails:#Tail Colors
      tailcol = (1,1,1, color[3])
    else:
      if big == False and tailOnly == True:
        tailcol = (.6, .6, .6, color[3])
      else:
        tailcol = (color)

    if flat:
      tailscale = (1, .1, 1)
    else:
      tailscale = None

    if sustain:
      if not length == None:
        size = (.08, length)

        if size[1] > self.boardLength:
          s = self.boardLength
        else:
          s = length

        if freestyleTail == 0:    #normal tail rendering
          #myfingershurt: so any theme containing appropriate files can use new tails
          if not self.simpleTails:
            if big == True and tailOnly == True:
              if kill and self.killfx == 0:
                zsize = .25
                tex1 = self.kill1
                tex2 = self.kill2
                
                #volshebnyi - killswitch tail width and color change
                kEffect = ( math.sin( pos / 50 ) + 1 ) /2
                size = (0.02+kEffect*0.15, s - zsize)
                c = [self.killColor[0],self.killColor[1],self.killColor[2]]
                if c != [0,0,0]:
                  for i in range(0,3):
                    c[i]=c[i]*kEffect+color[i]*(1-kEffect)
                  tailcol = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1) 

              else:
                zsize = .25
                size = (.17, s - zsize)
                if self.starPowerActive and not color == (0,0,0,1):
                  tex1 = self.btail6
                  tex2 = self.btaile6
                else:
                  if fret == 0:
                    tex1 = self.btail1
                    tex2 = self.btaile1
                  elif fret == 1:
                    tex1 = self.btail2
                    tex2 = self.btaile2
                  elif fret == 2:
                    tex1 = self.btail3
                    tex2 = self.btaile3
                  elif fret == 3:
                    tex1 = self.btail4
                    tex2 = self.btaile4
                  elif fret == 4:
                    tex1 = self.btail5
                    tex2 = self.btaile5
            else:
              zsize = .15
              size = (.1, s - zsize)
              if tailOnly:#Note let go
                tex1 = self.tail0
                tex2 = self.taile0
              else:
                if self.starPowerActive and not color == (0,0,0,1):
                  tex1 = self.tail6
                  tex2 = self.taile6
                else:
                  if fret == 0:
                    tex1 = self.tail1
                    tex2 = self.taile1
                  elif fret == 1:
                    tex1 = self.tail2
                    tex2 = self.taile2
                  elif fret == 2:
                    tex1 = self.tail3
                    tex2 = self.taile3
                  elif fret == 3:
                    tex1 = self.tail4
                    tex2 = self.taile4
                  elif fret == 4:
                    tex1 = self.tail5
                    tex2 = self.taile5
          else:
            if big == True and tailOnly == True:
              if kill:
                zsize = .25
                tex1 = self.kill1
                if self.kill2:
                  tex2 = self.kill2
                if not self.kill2:
                  tex2 = None
                #volshebnyi - killswitch tail width and color change
                kEffect = ( math.sin( pos / 50 ) + 1 ) /2
                size = (0.02+kEffect*0.15, s - zsize)
                c = [self.killColor[0],self.killColor[1],self.killColor[2]]
                if c != [0,0,0]:
                  for i in range(0,3):
                    c[i]=c[i]*kEffect+color[i]*(1-kEffect)
                  tailcol = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1) 
              else:
                zsize = .25
                size = (.11, s - zsize)
                tex1 = self.bigTail1
                if self.bigTail2:
                  tex2 = self.bigTail2
                if not self.bigTail2:
                  tex2 = None
            else:
              zsize = .15
              size = (.08, s - zsize)
              tex1 = self.tail1
              if self.tail2:
                tex2 = self.tail2
              if not self.tail2:
                tex2 = None
        
        else:   #freestyleTail > 0
          # render an inactive freestyle tail  (self.freestyle1 & self.freestyle2)
          zsize = .25
  
          if self.freestyleActive:
            size = (.30, s - zsize)   #was .15
          else:
            size = (.15, s - zsize)

          if self.isDrum and self.drumFillsActive:
            if self.drumFillsHits >= 4:
              size = (.30, s - zsize)
            elif self.drumFillsHits >= 3:
              size = (.25, s - zsize)
            elif self.drumFillsHits >= 2:
              size = (.21, s - zsize)
            elif self.drumFillsHits >= 1:
              size = (.17, s - zsize)			
          
          tex1 = self.freestyle1
          if self.freestyle2:
            tex2 = self.freestyle2
          if not self.freestyle2:
            tex2 = None
          if freestyleTail == 1:
            c1, c2, c3, c4 = color
            tailGlow = 1 - (pos - self.freestyleLastFretHitTime[fret] ) / self.freestylePeriod
            if tailGlow < 0:
              tailGlow = 0
            color = (c1 + c1*2.0*tailGlow, c2 + c2*2.0*tailGlow, c3 + c3*2.0*tailGlow, c4*0.6 + c4*0.4*tailGlow)    #MFH - this fades inactive tails' color darker
          tailcol = (color)

        if freestyleTail == 0 and big and tailOnly and shaders.enable("tail"):
          color = (color[0]*1.5,color[1]*1.5,color[2]*1.5,1.0)
          shaders.setVar("color",color)
          if kill and self.killfx == 0:
            h = shaders.getVar("height")
            shaders.modVar("height",0.5,0.06/h-0.1)
          shaders.setVar("offset",(5.0-size[1],0.0))
          size=(size[0]*15,size[1])
          
          
        self.engine.draw3Dtex(tex1, vertex = (-size[0], 0, size[0], size[1]), texcoord = (0.0, 0.0, 1.0, 1.0),
                              scale = tailscale, color = tailcol)
        if tex2:
            self.engine.draw3Dtex(tex2, vertex = (-size[0], size[1], size[0], size[1] + (zsize)),
                                  scale = tailscale, texcoord = (0.0, 0.05, 1.0, 0.95), color = tailcol)

        shaders.disable()  

        #MFH - this block of code renders the tail "beginning" - before the note, for freestyle "lanes" only
        #volshebnyi
        if tex2:
          if freestyleTail > 0 and pos < self.freestyleStart + self.freestyleLength:
            self.engine.draw3Dtex(tex2, vertex = (-size[0], 0-(zsize), size[0], 0 + (.05)),
                                  scale = tailscale, texcoord = (0.0, 0.95, 1.0, 0.05), color = tailcol)

    if tailOnly:
      return

  def renderFreestyleLanes(self, visibility, song, pos, controls):
    if not song:
      return
    if not song.readyToGo:
      return

    #MFH - check for [section big_rock_ending] to set a flag to determine how to treat the last drum fill marker note:
    if song.breMarkerTime and pos > song.breMarkerTime:
      self.bigRockEndingMarkerSeen = True
    self.drumFillsReady = False

    boardWindowMax = pos + self.currentPeriod * self.beatsPerBoard
    track = song.midiEventTrack[self.player]
    beatsPerUnit = self.beatsPerBoard / self.boardLength
    breLaneOffset = (self.strings - 5) * .5

    if self.freestyleEnabled:
      freestyleActive = False
      if self.isDrum:
        self.drumFillsActive = False
        drumFillEvents = []
      for time, event in track.getEvents(pos - self.freestyleOffset, boardWindowMax + self.freestyleOffset):
        if isinstance(event, Song.MarkerNote):
          if event.number == Song.freestyleMarkingNote and (not event.happened or self.bigRockEndingMarkerSeen):		  #MFH - don't kill the BRE!
            if self.isDrum:
   	          drumFillEvents.append(event)
            length     = (event.length - 50) / self.currentPeriod / beatsPerUnit
            w = self.boardWidth / self.strings
            self.freestyleLength = event.length #volshebnyi
            self.freestyleStart = time # volshebnyi
            z  = ((time - pos) / self.currentPeriod) / beatsPerUnit
            z2 = ((time + event.length - pos) / self.currentPeriod) / beatsPerUnit

            if z > self.boardLength * .8:
              f = (self.boardLength - z) / (self.boardLength * .2)
            elif z < 0:
              f = min(1, max(0, 1 + z2))
            else:
              f = 1.0

            time -= self.freestyleOffset 
            #volshebnyi - allow tail to move under frets
            if self.isDrum:
              if time > pos:
                self.drumFillsHits = -1
              if self.starPower>=50 and not self.starPowerActive:
                self.drumFillsReady = True

              else:
                self.drumFillsReady = False
            if self.bigRockEndingMarkerSeen:
              self.freestyleReady = True
              if self.isDrum:
                self.drumFillsReady = False
            else:
              self.freestyleReady = False
            if time < pos:
              if self.bigRockEndingMarkerSeen:
                freestyleActive = True
              elif self.isDrum:
                if self.drumFillsReady:
                  self.drumFillsActive = True
                  self.drumFillWasJustActive = True
                if self.drumFillsHits<0:
                  self.drumFillsCount += 1
                  self.drumFillsHits = 0

              if z < -1.5:
                length += z +1.5
                z =  -1.5

            if self.isDrum:
              breRangeStart = 1
            else:
              breRangeStart = 0

            #volshebnyi - render freestyle tails
            if self.freestyleReady or self.drumFillsReady:
              for theFret in range(breRangeStart,5):
                x = (self.strings / 2 - breLaneOffset - theFret) * w
                if self.isDrum and theFret == 4:
                  c = self.fretColors[0]
                else:
                  c = self.fretColors[theFret]
                color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1.0 * visibility * f)
                glPushMatrix()
                glTranslatef(x, (1.0 - visibility) ** (theFret + 1), z)

                freestyleTailMode = 1

                self.renderTail(length = length, sustain = True, kill = False, color = color, flat = False, tailOnly = True, isTappable = False, big = True, fret = theFret, freestyleTail = freestyleTailMode, pos = pos)
                glPopMatrix()


            if self.isDrum and ( self.drumFillsActive and self.drumFillsHits >= 4 and z + length<self.boardLength ):
              glPushMatrix()
              color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1.0 * visibility * f)
              glTranslatef(x, 0.0, z + length)
              glScalef(1,1.7,1.3)
              self.renderNote(length, sustain = False, color = color, flat = False, tailOnly = False, isTappable = False, fret = 4, spNote = False, isOpen = False, spAct = True)
              glPopMatrix()

      self.freestyleActive = freestyleActive
      if self.isDrum:
        self.drumFillEvents = drumFillEvents

  def renderTails(self, visibility, song, pos, killswitch):
    if not song:
      return
    if not song.readyToGo:
      return

    # Update dynamic period
    self.currentPeriod = self.neckSpeed

    self.killPoints = False

    w = self.boardWidth / self.strings
    
    track = song.track[self.player]

    num = 0
    enable = True
    renderedNotes = self.getRequiredNotesForRender(song,pos)

    for time, event in renderedNotes:
      if isinstance(event, Tempo):
        self.tempoBpm = event.bpm
        continue
      
      if not isinstance(event, Note):
        continue

      if (event.noteBpm == 0.0):
        event.noteBpm = self.tempoBpm

      if self.coOpFailed:
        if self.coOpRestart:
          if time - self.coOpRescueTime < (self.currentPeriod * self.beatsPerBoard * 2):
            continue
          elif self.coOpRescueTime + (self.currentPeriod * self.beatsPerBoard * 2) < pos:
            self.coOpFailed = False
            self.coOpRestart = False
            Log.debug("Turning off coOpFailed. Rescue successful.")
        else:
          continue

      c = self.fretColors[event.number]

      x  = (self.strings / 2 - event.number) * w
      z  = ((time - pos) / self.currentPeriod) / self.beatsPerUnit
      z2 = ((time + event.length - pos) / self.currentPeriod) / self.beatsPerUnit


      if z > self.boardLength * .8:
        f = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        f = min(1, max(0, 1 + z2))
      else:
        f = 1.0

      color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1 * visibility * f)
      if event.length > 120:
        length     = (event.length - 50) / self.currentPeriod / self.beatsPerUnit
      else:
        length     = 0
      flat       = False
      tailOnly   = False

      spNote = False

      #myfingershurt: user setting for starpower refill / replenish notes

      if event.star and self.spEnabled:
        spNote = True
      if event.finalStar and self.spEnabled:
        spNote = True
        if event.played or event.hopod:
          if event.flameCount < 1 and not self.starPowerGained:
            if self.gameMode2p == 6:
              if self.battleSuddenDeath:
                self.battleObjects = [1] + self.battleObjects[:2]
              else:
                self.battleObjects = [self.battleObjectsEnabled[random.randint(0,len(self.battleObjectsEnabled)-1)]] + self.battleObjects[:2]
              self.battleGetTime = pos
              self.battleObjectGained = True
              Log.debug("Battle Object Gained, Objects %s" % str(self.battleObjects))
            else:
              if self.starPower < 100:
                self.starPower += 25
              if self.starPower > 100:
                self.starPower = 100
            self.neck.overdriveFlashCount = 0  #MFH - this triggers the oFlash strings & timer
            self.starPowerGained = True
            self.neck.ocount = 0

      if event.tappable < 2:
        isTappable = False
      else:
        isTappable = True
      
      # Clip the played notes to the origin
      #myfingershurt: this should be loaded once at init, not every render...
      if self.notedisappear == 0:#Notes keep on going when missed
        if event.played or event.hopod:#if the note isnt missed
          tailOnly = True
          length += z
          z = 0
          if length <= 0:
            continue
        if z < 0 and not (event.played or event.hopod):#if the note is missed 
          color = (.6, .6, .6, .5 * visibility * f)
          flat  = False 
      elif self.notedisappear == 1:#Notes disappear when missed
        if z < 0:#if note past frets
          if event.played or event.hopod:#if note was hit
            tailOnly = True
            length += z
            z = 0
            if length <= 0:
              continue
          else:#note missed
            color = (.6, .6, .6, .5 * visibility * f)
            flat  = False
      if self.notedisappear == 2:#turn red when missed
        if event.played or event.hopod:  #if the note isnt missed
          tailOnly = True
          length += z
          z = 0
          if length <= 0:
            continue
        if z < 0 and not (event.played or event.hopod): #if the note is missed 
          color = (1, 0, 0, 1)#turn note red
          flat  = False
          
      big = False
      self.bigMax = 0
      for i in range(0, self.strings):
        if self.hit[i]:
          big = True
          self.bigMax += 1

      if self.spEnabled and killswitch:
        if event.star or event.finalStar:
          if big == True and tailOnly == True:
            self.killPoints = True
            color = (1,1,1,1)

      if z + length < -1.0:
        continue
      if event.length <= 120:
        length = None

      sustain = False
      if event.length > (1.4 * (60000.0 / event.noteBpm) / 4):
        sustain = True
        
      glPushMatrix()
      glTranslatef(x, (1.0 - visibility) ** (event.number + 1), z)

      if self.battleStatus[8]:
        renderNote = random.randint(0,2)
      else:
        renderNote = 0
      if renderNote == 0:  
        if big == True and num < self.bigMax:
          num += 1
          self.renderTail(length, sustain = sustain, kill = killswitch, color = color, flat = flat, tailOnly = tailOnly, isTappable = isTappable, big = True, fret = event.number, pos = pos)
        else:
          self.renderTail(length, sustain = sustain, kill = killswitch, color = color, flat = flat, tailOnly = tailOnly, isTappable = isTappable, fret = event.number, pos = pos)

      glPopMatrix()
  

      if killswitch and self.killfx == 1:
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        for time, event in self.playedNotes:
          step  = self.currentPeriod / 16
          t     = time + event.length
          x     = (self.strings / 2 - event.number) * w
          c     = self.fretColors[event.number]
          s     = t
          proj  = 1.0 / self.currentPeriod / self.beatsPerUnit
          zStep = step * proj

          def waveForm(t):
            u = ((t - time) * -.1 + pos - time) / 64.0 + .0001
            return (math.sin(event.number + self.time * -.01 + t * .03) + math.cos(event.number + self.time * .01 + t * .02)) * .1 + .1 + math.sin(u) / (5 * u)

          glBegin(GL_TRIANGLE_STRIP)
          f1 = 0
          while t > time:
            
            if ((t-pos)*proj) < self.boardLength:
              z  = (t - pos) * proj
            else:
              z = self.boardLength            
            
            if z < 0:
              break
            f2 = min((s - t) / (6 * step), 1.0)
            a1 = waveForm(t) * f1
            a2 = waveForm(t - step) * f2
            if self.starPowerActive and self.theme != 2:#8bit
              glColor4f(self.spColor[0],self.spColor[1],self.spColor[2],1)  #(.3,.7,.9,1)
            else:
              glColor4f(c[0], c[1], c[2], .5)
            glVertex3f(x - a1, 0, z)
            glVertex3f(x - a2, 0, z - zStep)
            glColor4f(1, 1, 1, .75)
            glVertex3f(x, 0, z)
            glVertex3f(x, 0, z - zStep)
            if self.starPowerActive and self.theme != 2:#8bit
              glColor4f(self.spColor[0],self.spColor[1],self.spColor[2],1)  #(.3,.7,.9,1)
            else:
              glColor4f(c[0], c[1], c[2], .5)
            glVertex3f(x + a1, 0, z)
            glVertex3f(x + a2, 0, z - zStep)
            glVertex3f(x + a2, 0, z - zStep)
            glVertex3f(x - a2, 0, z - zStep)
            t -= step
            f1 = f2
          glEnd()
      
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

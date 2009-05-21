#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyostila                                  #
#               2008 Alarian                                        #
#               2008 myfingershurt                                  #
#               2008 Capo                                           #
#               2008 Glorandwarf                                    #
#               2008 QQStarS                                        #
#               2008 Blazingamer                                    #
#               2008 evilynux <evilynux@gmail.com>                  #
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

import Player
from Song import Note, Tempo, Bars
from Mesh import Mesh
import Theme
import random
from copy import deepcopy
from Shader import shaders

from OpenGL.GL import *
import math
from numpy import array, float32

#myfingershurt: needed for multi-OS file fetching
import os
import Log
import Song   #need the base song defines as well


class Guitar:
  def __init__(self, engine, playerObj, editorMode = False, player = 0):
    self.engine         = engine


    self.isDrum = False
    self.isBassGuitar = False
    self.isVocal = False

    self.starPowerDecreaseDivisor = 200.0/self.engine.audioSpeedFactor
    
    self.debugMode = False
    self.gameMode2p = self.engine.config.get("game","multiplayer_mode")
    self.matchingNotes = []
    
    self.sameNoteHopoString = False
    self.hopoProblemNoteNum = -1
    
    self.useMidiSoloMarkers = False
    self.currentGuitarSoloHitNotes = 0

    self.cappedScoreMult = 0
    self.starSpinFrameIndex = 0

    self.starSpinFrames = 16
    self.isStarPhrase = False
    self.finalStarSeen = False

    self.freestyleActive = False
    
    self.drumFillsActive = False
    
    self.bigRockEndingMarkerSeen = False

    #MFH - I do not understand fully how the handicap scorecard works at the moment, nor do I have the time to figure it out.
    #... so for now, I'm just writing some extra code here for the early hitwindow size handicap.
    self.earlyHitWindowSizeFactor = 0.5

    
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
    
    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("Guitar class init...")

    self.incomingNeckMode = self.engine.config.get("game", "incoming_neck_mode")
    

    
    self.bigRockEndings = self.engine.config.get("game", "big_rock_endings")
    
    self.boardWidth     = Theme.neckWidth
    self.boardLength    = Theme.neckLength
    #death_au: fixed neck size
    if Theme.twoDnote == False or Theme.twoDkeys == False:
      self.boardWidth     = 3.6
      self.boardLength    = 9.0  

    self.beatsPerBoard  = 5.0
    self.beatsPerUnit   = self.beatsPerBoard / self.boardLength
    self.strings        = 5
    self.fretWeight     = [0.0] * self.strings
    self.fretActivity   = [0.0] * self.strings
    self.fretColors     = Theme.fretColors
    self.spColor        = self.fretColors[5]
    self.playedNotes    = []

    self.freestyleHitFlameCounts = [0 for n in range(self.strings+1)]    #MFH

    
    self.lastPlayedNotes = []   #MFH - for reverting when game discovers it implied incorrectly
    
    self.missedNotes    = []
    self.missedNoteNums = []
    self.editorMode     = editorMode
    self.selectedString = 0
    self.time           = 0.0
    self.pickStartPos   = 0
    self.leftyMode      = False
    
    self.battleSuddenDeath  = False
    self.battleObjectsEnabled = []
    self.battleSDObjectsEnabled = []
    if self.engine.config.get("game", "battle_Whammy") == 1:
      self.battleObjectsEnabled.append(4)
    if self.engine.config.get("game", "battle_Diff_Up") == 1:
      if playerObj.getDifficultyInt() > 0:
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
    
    Log.debug(self.battleObjectsEnabled)
    self.battleNextObject   = 0
    self.battleObjects      = [0] * 3
    self.battleBeingUsed    = [0] * 2
    self.battleStatus       = [False] * 9
    self.battleStartTimes    = [0] * 9
    self.battleGetTime      = 0

    
    self.battleLeftyLength  = 8000 #
    self.battleDiffUpLength = 15000
    self.battleDiffUpValue  = playerObj.getDifficultyInt()
    self.battleDoubleLength = 8000
    self.battleAmpLength    = 8000
    self.battleWhammyLimit  = 6 #
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
    self.currentBpm     = 120.0
    self.currentPeriod  = 60000.0 / self.currentBpm
    self.targetBpm      = self.currentBpm
    self.targetPeriod   = 60000.0 / self.targetBpm
    self.lastBpmChange  = -1.0
    self.baseBeat       = 0.0


    self.indexFps       = self.engine.config.get("video", "fps") #QQstarS
    #########For Animations
    self.Animspeed      = 30#Lower value = Faster animations
    #For Animated Starnotes
    self.indexCount     = 0
    #Alarian, For animated hitglow
    self.HCount         = 0
    self.HCount2        = 0
    self.HCountAni      = False
    self.Hitanim        = True
    self.Hitanim2       = True
    
    #myfingershurt: to keep track of pause status here as well
    self.paused = False

    self.spEnabled = True
    self.starPower = 0
    self.starPowerGained = False

    self.killPoints = False

    self.starpowerMode = self.engine.config.get("game", "starpower_mode") #MFH
    
    #get difficulty
    self.difficulty = playerObj.getDifficultyInt()
    self.controlType = playerObj.controlType

    #myfingershurt:
    self.hopoStyle        = self.engine.config.get("game", "hopo_system")
    self.gh2sloppy        = self.engine.config.get("game", "gh2_sloppy")
    if self.gh2sloppy == 1:
      self.hopoStyle = 4
    self.LastStrumWasChord = False
    self.spRefillMode = self.engine.config.get("game","sp_notes_while_active")
    self.hitglow_color = self.engine.config.get("video", "hitglow_color") #this should be global, not retrieved every fret render.
    self.sfxVolume    = self.engine.config.get("audio", "SFX_volume")

    self.vbpmLogicType = self.engine.config.get("debug",   "use_new_vbpm_beta")

    
    #myfingershurt: this should be retrieved once at init, not repeatedly in-game whenever tails are rendered.
    self.notedisappear = self.engine.config.get("game", "notedisappear")
    self.fretsUnderNotes  = self.engine.config.get("game", "frets_under_notes")
    


    self.muteSustainReleases = self.engine.config.get("game", "sustain_muting") #MFH

    self.hitw = self.engine.config.get("game", "note_hit_window")  #this should be global, not retrieved every BPM change.
    if self.hitw == 0: 
      self.hitw = 1.2
    elif self.hitw == 1: 
      self.hitw = 1.9
    elif self.hitw == 2: 
      self.hitw = 2.3
    else:
      self.hitw = 1.2
    
    self.hitwcheat = self.engine.config.get("game", "hit_window_cheat")
    if self.hitwcheat == 1:   
      self.hitw = 0.70
    elif self.hitwcheat == 2: 
      self.hitw = 1.0
    
    self.twoChord       = 0
    self.twoChordApply  = False
    self.hopoActive     = 0
    
    #myfingershurt: need a separate variable to track whether or not hopos are actually active
    self.wasLastNoteHopod = False
    
    
    self.hopoLast       = -1
    self.hopoColor      = (0, .5, .5)
    self.player         = player

    self.hit = [False, False, False, False, False]
    
    self.freestyleHit = [False, False, False, False, False]
    
    self.fretboardHop = 0.00  #stump
    self.bgcount = 0

    self.playerObj = playerObj



    playerObj = None
    #Get theme
    themename = self.engine.data.themeLabel
    #now theme determination logic is only in data.py:
    self.theme = self.engine.data.theme
    
    #check if BRE enabled
    if self.bigRockEndings == 2 or (self.theme == 2 and self.bigRockEndings == 1):
      self.freestyleEnabled = True

    #blazingamer
    self.nstype = self.engine.config.get("game", "nstype")
    self.twoDnote = Theme.twoDnote
    self.twoDkeys = Theme.twoDkeys 
    self.threeDspin = Theme.threeDspin 
    self.killfx = self.engine.config.get("performance", "killfx")
    self.killCount         = 0
    self.noterotate = self.engine.config.get("coffee", "noterotate")
    
    #akedrou
    self.coOpRescueTime = 0.0
    
    #MFH- fixing neck speed
    if self.nstype < 3:   #not constant mode: 
      self.speed = self.engine.config.get("coffee", "neckSpeed")*0.01
    else:   #constant mode
      self.speed = 410 - self.engine.config.get("coffee", "neckSpeed")    #invert this value

    self.bigMax = 1
    
    self.keys = []
    self.actions = []
    self.soloKey = []

    
    self.setBPM(self.currentBpm)

    if self.starpowerMode == 1:
      self.starNotesSet = False
    else:
      self.starNotesSet = True

    self.maxStars = []
    self.starNotes = []
    self.totalNotes = 0


    engine.loadImgDrawing(self, "glowDrawing", "glow.png")
    
    self.oFlash = None

    #MFH - making hitflames optional
    self.hitFlamesPresent = False
    try:
      engine.loadImgDrawing(self, "hitflames1Drawing", os.path.join("themes",themename,"hitflames1.png"),  textureSize = (128, 128))
      engine.loadImgDrawing(self, "hitflames2Drawing", os.path.join("themes",themename,"hitflames2.png"),  textureSize = (128, 128))
      self.hitFlamesPresent = True
    except IOError:
      self.hitFlamesPresent = False
      self.hitflames1Drawing = None
      self.hitflames2Drawing = None

    try:
      engine.loadImgDrawing(self, "hitflamesAnim", os.path.join("themes",themename,"hitflamesanimation.png"),  textureSize = (128, 128))
    except IOError:
      #engine.loadImgDrawing(self, "hitflames1Drawing", os.path.join("themes",themename,"hitflames1.png"),  textureSize = (128, 128))
      #engine.loadImgDrawing(self, "hitflames2Drawing", os.path.join("themes",themename,"hitflames2.png"),  textureSize = (128, 128))
      self.Hitanim2 = False
      
    try:
      engine.loadImgDrawing(self, "hitglowAnim", os.path.join("themes",themename,"hitglowanimation.png"),  textureSize = (128, 128))
    except IOError:
      try:
        engine.loadImgDrawing(self, "hitglowDrawing", os.path.join("themes",themename,"hitglow.png"),  textureSize = (128, 128))
        engine.loadImgDrawing(self, "hitglow2Drawing", os.path.join("themes",themename,"hitglow2.png"),  textureSize = (128, 128))
      except IOError:
        self.hitglowDrawing = None
        self.hitglow2Drawing = None
        self.hitFlamesPresent = False   #MFH - shut down all flames if these are missing.
      self.Hitanim = False
      
    #racer: added RB beta frets option:
    self.rbnote = self.engine.config.get("game", "rbnote")
    
    #myfingershurt:
    self.bassGrooveNeckMode = self.engine.config.get("game", "bass_groove_neck")
    self.guitarSoloNeckMode = self.engine.config.get("game", "guitar_solo_neck")

    self.starspin = self.engine.config.get("performance", "starspin")
    if self.twoDnote == True:
      #Spinning starnotes or not?
      #myfingershurt: allowing any non-Rock Band theme to have spinning starnotes if the SpinNotes.png is available in that theme's folder
      if self.starspin == True and self.theme < 2:
        #myfingershurt: check for SpinNotes, if not there then no animation
        if self.gameMode2p == 6:
          try:  
            engine.loadImgDrawing(self, "noteButtons", os.path.join("themes",themename,"spinnotesbattle.png"))
            self.starSpinFrames = 8
          except IOError:
            try:
              self.starspin = False
              engine.loadImgDrawing(self, "noteButtons", os.path.join("themes",themename,"notesbattle.png"))
            except IOError:
              self.starspin = False
              engine.loadImgDrawing(self, "noteButtons", os.path.join("themes",themename,"notes.png"))
        else:    
          try:  
            engine.loadImgDrawing(self, "noteButtons", os.path.join("themes",themename,"spinnotes.png"))
          except IOError:
            self.starspin = False
            engine.loadImgDrawing(self, "noteButtons", os.path.join("themes",themename,"notes.png"))
      elif self.rbnote == 1 and self.theme == 2:
        try:
          engine.loadImgDrawing(self, "noteButtons", os.path.join("themes",themename,"notesbeta.png"))
        except IOError:
          engine.loadImgDrawing(self, "noteButtons", os.path.join("themes",themename,"notes.png"))
          self.rbnote = 0
      else:
        if self.gameMode2p == 6:
          try:
            engine.loadImgDrawing(self, "noteButtons", os.path.join("themes",themename,"notesbattle.png"))
          except IOError:
            engine.loadImgDrawing(self, "noteButtons", os.path.join("themes",themename,"notes.png"))
        else:
          engine.loadImgDrawing(self, "noteButtons", os.path.join("themes",themename,"notes.png"))
        #mfh - adding fallback for beta option
    else:
      #MFH - can't use IOError for fallback logic for a Mesh() call... 
      if self.engine.fileExists(os.path.join("themes", themename, "note.dae")):
        engine.resource.load(self,  "noteMesh",  lambda: Mesh(engine.resource.fileName("themes", themename, "note.dae")))
      else:
        engine.resource.load(self,  "noteMesh",  lambda: Mesh(engine.resource.fileName("note.dae")))
        
      try:
        engine.loadImgDrawing(self,  "notetexa",  os.path.join("themes", themename, "notetex_a.png"))
        engine.loadImgDrawing(self,  "notetexb",  os.path.join("themes", themename, "notetex_b.png"))
        engine.loadImgDrawing(self,  "notetexc",  os.path.join("themes", themename, "notetex_c.png"))
        engine.loadImgDrawing(self,  "notetexd",  os.path.join("themes", themename, "notetex_d.png"))
        engine.loadImgDrawing(self,  "notetexe",  os.path.join("themes", themename, "notetex_e.png"))
        self.notetex = True

      except IOError:
        self.notetexa = False
        self.notetexb = False
        self.notetexc = False
        self.notetexd = False
        self.notetexe = False
        self.notetex = False
        
      if self.engine.fileExists(os.path.join("themes", themename, "star.dae")):  
        engine.resource.load(self,  "starMesh",  lambda: Mesh(engine.resource.fileName("themes", themename, "star.dae")))
      else:  
        self.starMesh = None

      try:
        engine.loadImgDrawing(self,  "startexa",  os.path.join("themes", themename, "startex_a.png"))
        engine.loadImgDrawing(self,  "startexb",  os.path.join("themes", themename, "startex_b.png"))
        engine.loadImgDrawing(self,  "startexc",  os.path.join("themes", themename, "startex_c.png"))
        engine.loadImgDrawing(self,  "startexd",  os.path.join("themes", themename, "startex_d.png"))
        engine.loadImgDrawing(self,  "startexe",  os.path.join("themes", themename, "startex_e.png"))
        self.startex = True

      except IOError:
        self.startexa = False
        self.startexb = False
        self.startexc = False
        self.startexd = False
        self.startexe = False
        self.startex = False

    if self.gameMode2p == 6:
      try:
        engine.loadImgDrawing(self, "battleFrets", os.path.join("themes", themename,"battle_frets.png"))
      except IOError:
        self.battleFrets = None

    if self.twoDkeys == True:
      if self.theme == 2:  
        if self.rbnote == 1:
          #mfh - adding fallback for beta option
          try:
            engine.loadImgDrawing(self, "fretButtons", os.path.join("themes",themename,"fretbuttonsbeta.png"))
          except IOError:
            engine.loadImgDrawing(self, "fretButtons", os.path.join("themes",themename,"fretbuttons.png"))
            self.rbnote = 0
        else:
          engine.loadImgDrawing(self, "fretButtons", os.path.join("themes",themename,"fretbuttons.png"))
      else:   #not RB theme
        engine.loadImgDrawing(self, "fretButtons", os.path.join("themes",themename,"fretbuttons.png"))
    else:
      #MFH - can't use IOError for fallback logic for a Mesh() call... 
      if self.engine.fileExists(os.path.join("themes", themename, "key.dae")):
        engine.resource.load(self,  "keyMesh",  lambda: Mesh(engine.resource.fileName("themes", themename, "key.dae")))
      else:
        engine.resource.load(self,  "keyMesh",  lambda: Mesh(engine.resource.fileName("key.dae")))

      try:
        engine.loadImgDrawing(self,  "keytexa",  os.path.join("themes", themename, "keytex_a.png"))
        engine.loadImgDrawing(self,  "keytexb",  os.path.join("themes", themename, "keytex_b.png"))
        engine.loadImgDrawing(self,  "keytexc",  os.path.join("themes", themename, "keytex_c.png"))
        engine.loadImgDrawing(self,  "keytexd",  os.path.join("themes", themename, "keytex_d.png"))
        engine.loadImgDrawing(self,  "keytexe",  os.path.join("themes", themename, "keytex_e.png"))
        self.keytex = True

      except IOError:
        self.keytexa = False
        self.keytexb = False
        self.keytexc = False
        self.keytexd = False
        self.keytexe = False
        self.keytex = False
    


    if self.theme == 0 or self.theme == 1:
      engine.loadImgDrawing(self, "hitlightning", os.path.join("themes",themename,"lightning.png"),  textureSize = (128, 128))

                                                           
    #inkk: loading theme-dependant tail images
    #myfingershurt: must ensure the new tails don't affect the Rock Band mod...
    self.simpleTails = False

    try:
      for i in range(0,7):
        engine.loadImgDrawing(self, "tail"+str(i), os.path.join("themes",themename,"tails","tail"+str(i)+".png"),  textureSize = (128, 128))
        engine.loadImgDrawing(self, "taile"+str(i), os.path.join("themes",themename,"tails","taile"+str(i)+".png"),  textureSize = (128, 128))
        engine.loadImgDrawing(self, "btail"+str(i), os.path.join("themes",themename,"tails","btail"+str(i)+".png"),  textureSize = (128, 128))
        engine.loadImgDrawing(self, "btaile"+str(i), os.path.join("themes",themename,"tails","btaile"+str(i)+".png"),  textureSize = (128, 128))
        
    except IOError:
      self.simpleTails = True
      Log.debug("Simple tails used; complex tail loading error...")
      try:
        engine.loadImgDrawing(self, "tail1", os.path.join("themes",themename,"tail1.png"),  textureSize = (128, 128))
        engine.loadImgDrawing(self, "tail2", os.path.join("themes",themename,"tail2.png"),  textureSize = (128, 128))
        engine.loadImgDrawing(self, "bigTail1", os.path.join("themes",themename,"bigtail1.png"),  textureSize = (128, 128))
        engine.loadImgDrawing(self, "bigTail2", os.path.join("themes",themename,"bigtail2.png"),  textureSize = (128, 128))
      except IOError:
        engine.loadImgDrawing(self, "tail1", "tail1.png",  textureSize = (128, 128))
        engine.loadImgDrawing(self, "tail2", "tail2.png",  textureSize = (128, 128))
        engine.loadImgDrawing(self, "bigTail1", "bigtail1.png",  textureSize = (128, 128))
        engine.loadImgDrawing(self, "bigTail2", "bigtail2.png",  textureSize = (128, 128))

    try:
      engine.loadImgDrawing(self, "kill1", os.path.join("themes", themename, "kill1.png"),  textureSize = (128, 128))
      engine.loadImgDrawing(self, "kill2", os.path.join("themes", themename, "kill2.png"),  textureSize = (128, 128))
    except IOError:
      engine.loadImgDrawing(self, "kill1", "kill1.png",  textureSize = (128, 128))
      engine.loadImgDrawing(self, "kill2", "kill2.png",  textureSize = (128, 128))

    #MFH - freestyle tails (for drum fills & BREs)
    try:
      engine.loadImgDrawing(self, "freestyle1", os.path.join("themes", themename, "freestyletail1.png"),  textureSize = (128, 128))
      engine.loadImgDrawing(self, "freestyle2", os.path.join("themes", themename, "freestyletail2.png"),  textureSize = (128, 128))
    except IOError:
      engine.loadImgDrawing(self, "freestyle1", "freestyletail1.png",  textureSize = (128, 128))
      engine.loadImgDrawing(self, "freestyle2", "freestyletail2.png",  textureSize = (128, 128))



    self.meshColor  = Theme.meshColor
    self.hopoColor  = Theme.hopoColor
    self.spotColor = Theme.spotColor   
    self.keyColor = Theme.keyColor
    self.key2Color = Theme.key2Color
    self.tracksColor = Theme.tracksColor
    self.barsColor = Theme.barsColor
    self.flameColors = Theme.flameColors
    self.gh3flameColor = Theme.gh3flameColor
    self.flameSizes = Theme.flameSizes
    self.glowColor  = Theme.glowColor
    
    
    self.twoChordMax = False
    self.disableVBPM  = self.engine.config.get("game", "disable_vbpm")
    self.disableNoteSFX  = self.engine.config.get("video", "disable_notesfx")
    self.disableFretSFX  = self.engine.config.get("video", "disable_fretsfx")
    self.disableFlameSFX  = self.engine.config.get("video", "disable_flamesfx")

    self.overdriveFlashCounts = self.indexFps/4   #how many cycles to display the oFlash: self.indexFps/2 = 1/2 second

    #Blazingamer: These variables are updated through the guitarscene which then pass 
    #through to the neck because it is used in both the neck.py and the guitar.py
    self.isFailing = False
    self.rockLevel = 0.0
    self.canGuitarSolo = False
    self.guitarSolo = False
    self.fretboardHop = 0.00  #stump
    self.scoreMultiplier = 1
    self.coOpFailed = False #akedrou
    self.coOpRestart = False #akedrou
    self.starPowerActive = False
    self.overdriveFlashCount = self.overdriveFlashCounts
    
  def selectPreviousString(self):
    self.selectedString = (self.selectedString - 1) % self.strings

  def selectString(self, string):
    self.selectedString = string % self.strings

  def selectNextString(self):
    self.selectedString = (self.selectedString + 1) % self.strings

  def noteBeingHeld(self):
    noteHeld = False
    for i in range(0,5):
      if self.hit[i] == True:
        noteHeld = True
    return noteHeld

  def isKillswitchPossible(self):
    possible = False
    for i in range(0,5):
      if self.hit[i] == True:
        possible = True
    return possible

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


    
  def setMultiplier(self, multiplier):
    self.scoreMultiplier = multiplier


  def renderTail(self, length, sustain, kill, color, flat = False, tailOnly = False, isTappable = False, big = False, fret = 0, spNote = False, freestyleTail = 0, pos = 0):

    #volshebnyi - if freestyleTail == 0, act normally.
    #  if freestyleTail == 1, render an freestyle tail
    #  if freestyleTail == 2, render highlighted freestyle tail

    if not self.simpleTails:#Tail Colors
      tailcol = (1,1,1,1)
    else:
      if big == False and tailOnly == True:
        tailcol = (.2 + .4, .2 + .4, .2 + .4, 1)
      else:
        tailcol = (color)
        #volshebnyi - tail color when sp is active
        if self.starPowerActive and self.theme != 2 and not color == (0,0,0,1):#8bit
          c = self.fretColors[5]
          tailcol = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1) 

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

    #       if freestyleTail == 1, render freestyle tail

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
                c = [self.fretColors[6][0],self.fretColors[6][1],self.fretColors[6][2]]
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
                tex2 = self.kill2
                #volshebnyi - killswitch tail width and color change
                kEffect = ( math.sin( pos / 50 ) + 1 ) /2
                size = (0.02+kEffect*0.15, s - zsize)
                c = [self.fretColors[6][0],self.fretColors[6][1],self.fretColors[6][2]]
                if c != [0,0,0]:
                  for i in range(0,3):
                    c[i]=c[i]*kEffect+color[i]*(1-kEffect)
                  tailcol = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1) 
              else:
                zsize = .25
                size = (.11, s - zsize)
                tex1 = self.bigTail1
                tex2 = self.bigTail2
            else:
              zsize = .15
              size = (.08, s - zsize)
              tex1 = self.tail1
              tex2 = self.tail2
        
        else:   #freestyleTail > 0
          # render an inactive freestyle tail  (self.freestyle1 & self.freestyle2)
          zsize = .25  
          
          if self.freestyleActive:
            size = (.30, s - zsize)   #was .15
          else:
            size = (.15, s - zsize)   
          
          tex1 = self.freestyle1
          tex2 = self.freestyle2
          if freestyleTail == 1:
            #glColor4f(*color)
            c1, c2, c3, c4 = color
            tailGlow = 1 - (pos - self.freestyleLastFretHitTime[fret] ) / self.freestylePeriod
            if tailGlow < 0:
              tailGlow = 0
            color = (c1 + c1*2.0*tailGlow, c2 + c2*2.0*tailGlow, c3 + c3*2.0*tailGlow, c4*0.6 + c4*0.4*tailGlow)    #MFH - this fades inactive tails' color darker                    
            
          tailcol = (color)
        if self.theme == 2 and freestyleTail == 0 and big and tailOnly and shaders.enable("tail"):
          color = (color[0]*1.5,color[1]*1.5,color[2]*1.5,1.0)
          if kill and self.killfx == 0:
            if shaders.var["whammy"] == 0:
              color = (1.0,1.0,1.0,1.0)
              shaders.setVar("color",color)
              shaders.modVar("height",0.0,0.3)
            else:
              shaders.setVar("color",color)
              h = shaders.getVar("height")
              shaders.modVar("height",0.5,0.06/h-0.1)
          else:  
            shaders.setVar("color",color)
            shaders.modVar("height",0.2,0.3)
          shaders.setVar("scalexy",(5.0,1.0))
          shaders.setVar("offset",(5.0-size[1],0.0))
          size=(size[0]*15,size[1])
          
          
        self.engine.draw3Dtex(tex1, vertex = (-size[0], 0, size[0], size[1]), texcoord = (0.0, 0.0, 1.0, 1.0),
                              scale = tailscale, color = tailcol)
        self.engine.draw3Dtex(tex2, vertex = (-size[0], size[1], size[0], size[1] + (zsize)),
                              scale = tailscale, texcoord = (0.0, 0.05, 1.0, 0.95), color = tailcol)

        shaders.disable()  

        #MFH - this block of code renders the tail "beginning" - before the note, for freestyle "lanes" only
        #volshebnyi
        if freestyleTail > 0 and pos < self.freestyleStart + self.freestyleLength:
          self.engine.draw3Dtex(tex2, vertex = (-size[0], 0-(zsize), size[0], 0 + (.05)),
                                scale = tailscale, texcoord = (0.0, 0.95, 1.0, 0.05), color = tailcol)
          

    if tailOnly:
      return

  def renderNote(self, length, sustain, kill, color, flat = False, tailOnly = False, isTappable = False, big = False, fret = 0, spNote = False):

    if flat:
      glScalef(1, .1, 1)


    if tailOnly:
      return


    if self.twoDnote == True:
      #myfingershurt: this should be retrieved once at init, not repeatedly in-game whenever tails are rendered.
      if self.notedisappear == True:#Notes keep on going when missed
        notecol = (1,1,1)#capo
      else:
        if flat:#Notes disappear when missed
          notecol = (.1,.1,.1)
        else:
          notecol = (1,1,1)
      tailOnly == True
      
      if self.theme < 2:
        if self.starspin:
          size = (self.boardWidth/self.strings/2, self.boardWidth/self.strings/2)
          texSize = (fret/5.0,fret/5.0+0.2)
          if spNote == True:
            if isTappable:
              texY = (0.150+self.starSpinFrameIndex*0.05, 0.175+self.starSpinFrameIndex*0.05)
            else:
              texY = (0.125+self.starSpinFrameIndex*0.05, 0.150+self.starSpinFrameIndex*0.05)
          else:
            if isTappable:
              texY = (0.025,0.05)
            else:
              texY = (0,0.025)
          if self.starPowerActive:
            texY = (0.10,0.125) #QQstarS
            if isTappable:
              texSize = (0.2,0.4)
            else:
              texSize = (0,0.2)
        else:
          size = (self.boardWidth/self.strings/2, self.boardWidth/self.strings/2)
          texSize = (fret/5.0,fret/5.0+0.2)
          if spNote == True:
            if isTappable:
              texY = (0.6, 0.8)
            else:
              texY = (0.4,0.6)
          else:
            if isTappable:
              texY = (0.2,0.4)
            else:
              texY = (0,0.2)
          if self.starPowerActive:
            texY = (0.8,1)
            if isTappable:
              texSize = (0.2,0.4)
            else:
              texSize = (0,0.2)
          
      elif self.theme == 2:
        size = (self.boardWidth/self.strings/2, self.boardWidth/self.strings/2)
        texSize = (fret/5.0,fret/5.0+0.2)
        if spNote == True:
          if isTappable:
            texY = (3*0.166667, 4*0.166667)
          else:
            texY = (2*0.166667, 3*0.166667)
        else:
          if isTappable:
            texY = (1*0.166667, 2*0.166667)
          else:
            texY = (0, 1*0.166667)
        #myfingershurt: adding spNote==False conditional so that star notes can appear in overdrive
        if self.starPowerActive and spNote == False:
          if isTappable:
            texY = (5*0.166667, 1)
          else:
            texY = (4*0.166667, 5*0.166667)

      self.engine.draw3Dtex(self.noteButtons, vertex = (-size[0],size[1],size[0],-size[1]), texcoord = (texSize[0],texY[0],texSize[1],texY[1]),
                            scale = (1,1,1), multiples = True, color = (1,1,1), vertscale = .2)

    else:  

      #mesh = outer ring (black) 
      #mesh_001 = main note (key color) 
      #mesh_002 = top (spot or hopo if no mesh_003) 
      #mesh_003 = hopo bump (hopo color)
    
      if spNote == True and self.starMesh != None:
        note = self.starMesh
      else:
        note = self.noteMesh

      glPushMatrix()
      glEnable(GL_DEPTH_TEST)
      glDepthMask(1)
      glShadeModel(GL_SMOOTH)
      
      if self.noterotate:
        glRotatef(90, 0, 1, 0)
        glRotatef(-90, 1, 0, 0)
      
      if spNote == True and self.threeDspin == True:
        glRotate(90 + self.time/3, 0, 1, 0)
      #death_au: fixed 3D note colours
      #volshebnyi - note color when sp is active
      glColor4f(*color)
      if self.starPowerActive and self.theme != 2 and not color == (0,0,0,1):
        c = self.fretColors[5]
        glColor4f(.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1) 

      if fret == 0: 
        glRotate(Theme.noterotdegrees, 0, 0, Theme.noterot1)
      elif fret == 1:
        glRotate(Theme.noterotdegrees, 0, 0, Theme.noterot2)
      elif fret == 2:
        glRotate(Theme.noterotdegrees, 0, 0, Theme.noterot3)
      elif fret == 3:
        glRotate(Theme.noterotdegrees, 0, 0, Theme.noterot4)
      elif fret == 4:
        glRotate(Theme.noterotdegrees, 0, 0, Theme.noterot5)

      if self.notetex == True and spNote == False:
          
        glColor3f(1,1,1)
        glEnable(GL_TEXTURE_2D)
        if fret == 0: 
          self.notetexa.texture.bind()
        elif fret == 1:
          self.notetexb.texture.bind()
        elif fret == 2:
          self.notetexc.texture.bind()
        elif fret == 3:
          self.notetexd.texture.bind()
        elif fret == 4:
          self.notetexe.texture.bind()
        glMatrixMode(GL_TEXTURE)
        glScalef(1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        if isTappable:
          self.noteMesh.render("Mesh_001")
        else:
          self.noteMesh.render("Mesh")
        
        glMatrixMode(GL_TEXTURE)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_TEXTURE_2D)

      elif self.startex == True and spNote == True:
        glColor3f(1,1,1)
        glEnable(GL_TEXTURE_2D)
        if fret == 0: 
          self.startexa.texture.bind()
        elif fret == 1:
          self.startexb.texture.bind()
        elif fret == 2:
          self.startexc.texture.bind()
        elif fret == 3:
          self.startexd.texture.bind()
        elif fret == 4:
          self.startexe.texture.bind()
        glMatrixMode(GL_TEXTURE)
        glScalef(1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        if isTappable:
          self.starMesh.render("Mesh_001")
        else:
          self.starMesh.render("Mesh")
        glMatrixMode(GL_TEXTURE)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_TEXTURE_2D)          
        
      else:
        if shaders.enable("rbnotes"):
          shaders.setVar("Material",color)
        note.render("Mesh_001")
        shaders.disable()
        glColor3f(self.spotColor[0], self.spotColor[1], self.spotColor[2])
        if isTappable:
          if self.hopoColor[0] == -2:
            glColor4f(*color)
          else:
            glColor3f(self.hopoColor[0], self.hopoColor[1], self.hopoColor[2])
          if(note.find("Mesh_003")) == True:
            note.render("Mesh_003")
            glColor3f(self.spotColor[0], self.spotColor[1], self.spotColor[2])
        note.render("Mesh_002")
        glColor3f(self.meshColor[0], self.meshColor[1], self.meshColor[2])
        note.render("Mesh")
        



      glDepthMask(0)
      glPopMatrix()

  def renderFreestyleLanes(self, visibility, song, pos):
    if not song:
      return
    if not song.readyToGo:
      return


    #boardWindowMin = pos - self.currentPeriod * 2
    boardWindowMax = pos + self.currentPeriod * self.beatsPerBoard
    track = song.midiEventTrack[self.player]

    #MFH - render 5 freestyle tails when Song.freestyleMarkingNote comes up
    if self.freestyleEnabled:
      freestyleActive = False
      #for time, event in track.getEvents(boardWindowMin, boardWindowMax):
      for time, event in track.getEvents(pos - self.freestyleOffset , boardWindowMax + self.freestyleOffset):
        if isinstance(event, Song.MarkerNote):
          if event.number == Song.freestyleMarkingNote:
            length     = (event.length - 50) / self.currentPeriod / self.beatsPerUnit
            w = self.boardWidth / self.strings
            self.freestyleLength = event.length #volshebnyi
            self.freestyleStart = time # volshebnyi
            z  = ((time - pos) / self.currentPeriod) / self.beatsPerUnit
            z2 = ((time + event.length - pos) / self.currentPeriod) / self.beatsPerUnit
      
            if z > self.boardLength * .8:
              f = (self.boardLength - z) / (self.boardLength * .2)
            elif z < 0:
              f = min(1, max(0, 1 + z2))
            else:
              f = 1.0
  
            #MFH - must extend the tail past the first fretboard section dynamically so we don't have to render the entire length at once
            #volshebnyi - allow tail to move under frets 
            if time - self.freestyleOffset < pos:
              freestyleActive = True
              if z < -1.5:
                length += z +1.5
                z =  -1.5
  
            #MFH - render 5 freestyle tails
            for theFret in range(0,5):
              x  = (self.strings / 2 - theFret) * w
              c = self.fretColors[theFret]
              color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1 * visibility * f)
              glPushMatrix()
              glTranslatef(x, (1.0 - visibility) ** (theFret + 1), z)

              freestyleTailMode = 1
              
              self.renderTail(length, sustain = True, kill = False, color = color, flat = False, tailOnly = True, isTappable = False, big = True, fret = theFret, spNote = False, freestyleTail = freestyleTailMode, pos = pos)
              glPopMatrix()
              
      self.freestyleActive = freestyleActive



              


  def renderNotes(self, visibility, song, pos, killswitch):
    if not song:
      return
    if not song.readyToGo:
      return

    # Update dynamic period
    self.currentPeriod = self.neckSpeed
    #self.targetPeriod  = self.neckSpeed

    self.killPoints = False

    w = self.boardWidth / self.strings
    track = song.track[self.player]

    num = 0
    enable = True
    starEventsInView = False
    renderedNotes = self.getRequiredNotesForRender(song,pos)
    for time, event in renderedNotes:
    #for time, event in reversed(track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard)):    #MFH - reverse order of note rendering
      if isinstance(event, Tempo):
        self.tempoBpm = event.bpm
        if self.lastBpmChange > 0 and self.disableVBPM == True:
            continue
        if (pos - time > self.currentPeriod or self.lastBpmChange < 0) and time > self.lastBpmChange:
          self.baseBeat         += (time - self.lastBpmChange) / self.currentPeriod
          self.targetBpm         = event.bpm
          self.lastBpmChange     = time
        #  self.setBPM(self.targetBpm) # glorandwarf: was setDynamicBPM(self.targetBpm)
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
      
      #volshebnyi - hide notes in BRE zone if BRE enabled  
      if self.freestyleEnabled and self.freestyleStart > 0:
        if time >= self.freestyleStart-self.freestyleOffset and time < self.freestyleStart + self.freestyleLength+self.freestyleOffset:
          z = -2.0

      color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1 * visibility * f)
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
        #self.isStarPhrase = True
        starEventsInView = True
      if event.finalStar:
        self.finalStarSeen = True
        starEventsInView = True


      if event.star and self.spEnabled:
        spNote = True
      if event.finalStar and self.spEnabled:
        spNote = True
        if event.played or event.hopod:
          if event.flameCount < 1 and not self.starPowerGained:
            Log.debug("star power added")
            if self.gameMode2p == 6:
              if self.battleSuddenDeath:
                self.battleObjects[2] = self.battleObjects[1]
                self.battleObjects[1] = self.battleObjects[0]
                self.battleObjects[0] = 1
                self.battleGetTime = pos
              else:
                self.battleObjects[2] = self.battleObjects[1]
                self.battleObjects[1] = self.battleObjects[0]
                self.battleObjects[0] = self.battleObjectsEnabled[random.randint(0,len(self.battleObjectsEnabled)-1)]
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

      if event.tappable < 2:
        isTappable = False
      else:
        isTappable = True
      
      # Clip the played notes to the origin
      #myfingershurt: this should be loaded once at init, not every render...
      if self.notedisappear == True:#Notes keep on going when missed
        ###Capo###
        if event.played or event.hopod:
          tailOnly = True
          length += z
          z = 0
          if length <= 0:
            continue
        if z < 0 and not (event.played or event.hopod): 
          color = (.2 + .4, .2 + .4, .2 + .4, .5 * visibility * f)
          flat  = True
        ###endCapo###
      else:#Notes disappear when missed
        if z < 0:
          if event.played or event.hopod:
            tailOnly = True
            length += z
            z = 0
            if length <= 0:
              continue
          else:
            color = (.2 + .4, .2 + .4, .2 + .4, .5 * visibility * f)
            flat  = True
          
      big = False
      self.bigMax = 0
      for i in range(0,5):
        if self.hit[i]:
          big = True
          self.bigMax += 1

      #MFH - filter out this tail whitening when starpower notes have been disbled from a screwup
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
          self.renderNote(length, sustain = sustain, kill = killswitch, color = color, flat = flat, tailOnly = tailOnly, isTappable = isTappable, big = True, fret = event.number, spNote = spNote)
        else:
          self.renderNote(length, sustain = sustain, kill = killswitch, color = color, flat = flat, tailOnly = tailOnly, isTappable = isTappable, fret = event.number, spNote = spNote)
      glPopMatrix()

    if (not starEventsInView and self.finalStarSeen):
      self.spEnabled = True
      self.finalStarSeen = False
      self.isStarPhrase = False

  def renderTails(self, visibility, song, pos, killswitch):
    if not song:
      return
    if not song.readyToGo:
      return

    # Update dynamic period
    self.currentPeriod = self.neckSpeed
    #self.targetPeriod  = self.neckSpeed

    self.killPoints = False

    w = self.boardWidth / self.strings
    
    track = song.track[self.player]

    num = 0
    enable = True
    renderedNotes = self.getRequiredNotesForRender(song,pos)
    for time, event in renderedNotes:
    #for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard):
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
                self.battleObjects[2] = self.battleObjects[1]
                self.battleObjects[1] = self.battleObjects[0]
                self.battleObjects[0] = 1
                self.battleGetTime = pos
              else:
                self.battleObjects[2] = self.battleObjects[1]
                self.battleObjects[1] = self.battleObjects[0]
                self.battleObjects[0] = self.battleObjectsEnabled[random.randint(0,len(self.battleObjectsEnabled)-1)]
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
            if self.theme == 2 and self.oFlash != None:
              self.ocount = 0

      if event.tappable < 2:
        isTappable = False
      else:
        isTappable = True
      
      # Clip the played notes to the origin
      #myfingershurt: this should be loaded once at init, not every render...
      if self.notedisappear == True:#Notes keep on going when missed
        ###Capo###
        if event.played or event.hopod:
          tailOnly = True
          length += z
          z = 0
          if length <= 0:
            continue
        if z < 0 and not (event.played or event.hopod): 
          color = (.2 + .4, .2 + .4, .2 + .4, .5 * visibility * f)
          flat  = True
        ###endCapo###
      else:#Notes disappear when missed
        if z < 0:
          if event.played or event.hopod:
            tailOnly = True
            length += z
            z = 0
            if length <= 0:
              continue
          else:
            color = (.2 + .4, .2 + .4, .2 + .4, .5 * visibility * f)
            flat  = True
          
      big = False
      self.bigMax = 0
      for i in range(0,5):
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
          self.renderTail(length, sustain = sustain, kill = killswitch, color = color, flat = flat, tailOnly = tailOnly, isTappable = isTappable, big = True, fret = event.number, spNote = spNote, pos = pos)
        else:
          self.renderTail(length, sustain = sustain, kill = killswitch, color = color, flat = flat, tailOnly = tailOnly, isTappable = isTappable, fret = event.number, spNote = spNote, pos = pos)

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


  def renderFrets(self, visibility, song, controls):
    w = self.boardWidth / self.strings
    size = (.22, .22)
    v = 1.0 - visibility

    glEnable(GL_DEPTH_TEST)
    
    #Hitglow color option - myfingershurt sez this should be a Guitar class global, not retrieved ever fret render in-game...
    
    for n in range(self.strings):
      f = self.fretWeight[n]
      c = self.fretColors[n]
            
      if f and (controls.getState(self.actions[0]) or controls.getState(self.actions[1])):
        f += 0.25

      glColor4f(.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, visibility)
      y = v + f / 6
      x = (self.strings / 2 - n) * w

      if self.twoDkeys == True:

        if self.battleStatus[4]:
          fretWhamOffset = self.battleWhammyNow * .15
          fretColor = (1,1,1,.5)
        else:
          fretWhamOffset = 0
          fretColor = (1,1,1,1)

        size = (self.boardWidth/self.strings/2, self.boardWidth/self.strings/2.4)
        if self.battleStatus[3] and self.battleFrets != None and self.battleBreakString == n:
          texSize = (n/5.0+.042,n/5.0+0.158)
          size = (.30, .40)
          fretPos = 8 - round((self.battleBreakNow/self.battleBreakLimit) * 8)
          texY = (fretPos/8.0,(fretPos + 1.0)/8)
          self.engine.draw3Dtex(self.battleFrets, vertex = (size[0],size[1],-size[0],-size[1]), texcoord = (texSize[0], texY[0], texSize[1], texY[1]),
                                coord = (x,v + .08 + fretWhamOffset,0), multiples = True,color = fretColor, depth = True)
        else:
          texSize = (n/5.0,n/5.0+0.2)
          texY = (0.0,1.0/3.0)
          if controls.getState(self.keys[n]) or controls.getState(self.keys[n+5]):
            texY = (1.0/3.0,2.0/3.0)
          if self.hit[n] or (self.battleStatus[3] and self.battleBreakString == n):
            texY = (2.0/3.0,1.0)
  
          self.engine.draw3Dtex(self.fretButtons, vertex = (size[0],size[1],-size[0],-size[1]), texcoord = (texSize[0], texY[0], texSize[1], texY[1]),
                                coord = (x,v + fretWhamOffset,0), multiples = True,color = fretColor, depth = True)

      else:

        if self.keyMesh:
          glPushMatrix()
          glDepthMask(1)
          glEnable(GL_LIGHTING)
          glEnable(GL_LIGHT0)
          glShadeModel(GL_SMOOTH)
          glRotatef(90, 0, 1, 0)
          glLightfv(GL_LIGHT0, GL_POSITION, (5.0, 10.0, -10.0, 0.0))
          glLightfv(GL_LIGHT0, GL_AMBIENT,  (.2, .2, .2, 0.0))
          glLightfv(GL_LIGHT0, GL_DIFFUSE,  (1.0, 1.0, 1.0, 0.0))
          glRotatef(-90, 1, 0, 0)
          glRotatef(-90, 0, 0, 1)


          if n == 0: 
            glRotatef(Theme.noterotdegrees, 0, 0, -Theme.noterot1)
          elif n == 1:
            glRotatef(Theme.noterotdegrees, 0, 0, -Theme.noterot2)
          elif n == 2:
            glRotatef(Theme.noterotdegrees, 0, 0, -Theme.noterot3)
          elif n == 3:
            glRotatef(Theme.noterotdegrees, 0, 0, -Theme.noterot4)
          elif n == 4:
            glRotatef(Theme.noterotdegrees, 0, 0, -Theme.noterot5)


          #Mesh - Main fret
          #Key_001 - Top of fret (key_color)
          #Key_002 - Bottom of fret (key2_color)
          #Glow_001 - Only rendered when a note is hit along with the glow.svg

          #if self.complexkey == True:
          #  glColor4f(.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], visibility)
          #  if self.battleStatus[4]:
          #    glTranslatef(x, y + self.battleWhammyNow * .15, 0)
          #  else:
          #    glTranslatef(x, y, 0)
          if self.keytex == True:
            glColor4f(1,1,1,visibility)
            if self.battleStatus[4]:
              glTranslatef(x, y + self.battleWhammyNow * .15, 0)
            else:
              glTranslatef(x, y, 0)
            glEnable(GL_TEXTURE_2D)
            if n == 0: 
              self.keytexa.texture.bind()
            elif n == 1:
              self.keytexb.texture.bind()
            elif n == 2:
              self.keytexc.texture.bind()
            elif n == 3:
              self.keytexd.texture.bind()
            elif n == 4:
              self.keytexe.texture.bind()
            glMatrixMode(GL_TEXTURE)
            glScalef(1, -1, 1)
            glMatrixMode(GL_MODELVIEW)
            if f and not self.hit[n]:
              self.keyMesh.render("Mesh_001")
            elif self.hit[n]:
              self.keyMesh.render("Mesh_002")
            else:
              self.keyMesh.render("Mesh")
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


      ######################
      f = self.fretActivity[n]

      if f and self.disableFretSFX != True:

        if self.glowColor[0] == -1:
          s = 1.0
        else:
          s = 0.0
        
        while s < 1:
          ms = s * (math.sin(self.time) * .25 + 1)
          if self.glowColor[0] == -2:
            glColor3f(c[0] * (1 - ms), c[1] * (1 - ms), c[2] * (1 - ms))
          else:
            glColor3f(self.glowColor[0] * (1 - ms), self.glowColor[1] * (1 - ms), self.glowColor[2] * (1 - ms))
          
          glPushMatrix()
          if self.battleStatus[4]:
            glTranslatef(x, y + self.battleWhammyNow * .15, 0)
          else:
            glTranslatef(x, y, 0)
          glScalef(.1 + .02 * ms * f, .1 + .02 * ms * f, .1 + .02 * ms * f)
          glRotatef( 90, 0, 1, 0)
          glRotatef(-90, 1, 0, 0)
          glRotatef(-90, 0, 0, 1)
          if self.twoDkeys == False and self.keytex == False:
            if(self.keyMesh.find("Glow_001")) == True:
              key.render("Glow_001")
            else:
              key.render()
          glPopMatrix()
          s += 0.2
          
        #Hitglow color
        if self.hitglow_color == 0:
          glowcol = (c[0], c[1], c[2])#Same as fret
        elif self.hitglow_color == 1:
          glowcol = (1, 1, 1)#Actual color in .svg-file

        f += 2

        if self.battleStatus[4]:
          self.engine.draw3Dtex(self.glowDrawing, coord = (x, y + self.battleWhammyNow * .15, 0.01), rot = (f * 90 + self.time, 0, 1, 0),
                              texcoord = (0.0, 0.0, 1.0, 1.0), vertex = (-size[0] * f, -size[1] * f, size[0] * f, size[1] * f),
                              multiples = True, alpha = True, color = glowcol)
        else:
          self.engine.draw3Dtex(self.glowDrawing, coord = (x, y, 0.01), rot = (f * 90 + self.time, 0, 1, 0),
                              texcoord = (0.0, 0.0, 1.0, 1.0), vertex = (-size[0] * f, -size[1] * f, size[0] * f, size[1] * f),
                              multiples = True, alpha = True, color = glowcol)

      #self.hit[n] = False  #MFH -- why?  This prevents frets from being rendered under / before the notes...
    glDisable(GL_DEPTH_TEST)

  def renderFreestyleFlames(self, visibility, controls):
    if self.flameColors[0][0][0] == -1:
      return

    w = self.boardWidth / self.strings
    #track = song.track[self.player]

    size = (.22, .22)
    v = 1.0 - visibility

    #blazingamer- hitglow logic is not required for BRE since you can not perform holds during it, uncomment out if you disagree with this
    
##    if self.disableFlameSFX != True and self.HCountAni == True and self.HCount2 > 12:
##      for n in range(self.strings):
##        f = self.fretWeight[n]
##        c = self.fretColors[n]
##        if f and (controls.getState(self.actions[0]) or controls.getState(self.actions[1])):
##          f += 0.25      
##        y = v + f / 6
##        x = (self.strings / 2 - n) * w
##        f = self.fretActivity[n]
##
##        if f:
##          ms = math.sin(self.time) * .25 + 1
##          ff = f
##          ff += 1.2
##          
##          
##          #myfingershurt: need to cap flameSizes use of scoreMultiplier to 4x, the 5x and 6x bass groove mults cause crash:
##          if self.scoreMultiplier > 4:
##            #cappedScoreMult = 4
##            self.cappedScoreMult = 4
##          else:
##            self.cappedScoreMult = self.scoreMultiplier
##          
##          #flameSize = self.flameSizes[self.scoreMultiplier - 1][n]
##          flameSize = self.flameSizes[self.cappedScoreMult - 1][n]
##          if self.theme == 0 or self.theme == 1: #THIS SETS UP GH3 COLOR, ELSE ROCKBAND(which is DEFAULT in Theme.py)
##            flameColor = self.gh3flameColor
##          else:
##            #flameColor = self.flameColors[self.scoreMultiplier - 1][n]
##            flameColor = self.flameColors[self.cappedScoreMult - 1][n]
##          #Below was an if that set the "flame"-color to the same as the fret color if there was no specific flamecolor defined.
##
##          flameColorMod0 = 1.1973333333333333333333333333333
##          flameColorMod1 = 1.9710526315789473684210526315789
##          flameColorMod2 = 10.592592592592592592592592592593
##          
##          flamecol = (flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
##          if self.starPowerActive:
##            if self.theme == 0 or self.theme == 1: #GH3 starcolor
##              flamecol = (.3,.7,.9)
##            else: #Default starcolor (Rockband)
##              flamecol = (.9,.9,.9)
##              
##          if not self.Hitanim:   
##            self.engine.draw3Dtex(self.hitglowDrawing, coord = (x, y + .125, 0), rot = (90, 1, 0, 0),
##                                  scale = (0.5 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff),
##                                  vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
##                                  texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)
##            #Alarian: Animated hitflames
##          else:
##            self.HCount = self.HCount + 1
##            if self.HCount > self.Animspeed-1:
##              self.HCount = 0
##            HIndex = (self.HCount * 16 - (self.HCount * 16) % self.Animspeed) / self.Animspeed
##            if HIndex > 15:
##              HIndex = 0
##            texX = (HIndex*(1/16.0), HIndex*(1/16.0)+(1/16.0))
##
##            self.engine.draw3Dtex(self.hitglowAnim, coord = (x, y + .225, 0), rot = (90, 1, 0, 0), scale = (2.4, 1, 3.3),
##                                  vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
##                                  texcoord = (texX[0],0.0,texX[1],1.0), multiples = True, alpha = True, color = (1,1,1))
##
##
##          ff += .3
##
##          flameColorMod0 = 1.1973333333333333333333333333333
##          flameColorMod1 = 1.7842105263157894736842105263158
##          flameColorMod2 = 12.222222222222222222222222222222
##          
##          flamecol = (flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
##
##          if self.starPowerActive:
##            if self.theme == 0 or self.theme == 1: #GH3 starcolor
##              flamecol = (.3,.7,.9)
##            else: #Default starcolor (Rockband)
##              flamecol = (.8,.8,.8)
##
##          if not self.Hitanim: 
##            self.engine.draw3Dtex(self.hitglow2Drawing, coord = (x, y + .25, .05), rot = (90, 1, 0, 0),
##                                  scale = (.40 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff),
##                                  vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
##                                  texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)


    if self.disableFlameSFX != True:
      flameLimit = 10.0
      flameLimitHalf = round(flameLimit/2.0)
      for fretNum in range(self.strings):
        if controls.getState(self.keys[fretNum]) or controls.getState(self.keys[fretNum+5]):

          if self.freestyleHitFlameCounts[fretNum] < flameLimit:
            ms = math.sin(self.time) * .25 + 1
  
            x  = (self.strings / 2 - fretNum) * w
  
            ff = 1 + 0.25       
            y = v + ff / 6
  
            if self.theme == 2:
              y -= 0.5
            
            #flameSize = self.flameSizes[self.scoreMultiplier - 1][fretNum]
            flameSize = self.flameSizes[self.cappedScoreMult - 1][fretNum]
            if self.theme == 0 or self.theme == 1: #THIS SETS UP GH3 COLOR, ELSE ROCKBAND(which is DEFAULT in Theme.py)
              flameColor = self.gh3flameColor
            else: #MFH - fixing crash!
              #try:
              #  flameColor = self.flameColors[self.scoreMultiplier - 1][fretNum]
              #except IndexError:
              flameColor = self.fretColors[fretNum]
            if flameColor[0] == -2:
              flameColor = self.fretColors[fretNum]
            
            ff += 1.5 #ff first time is 2.75 after this
  
            if self.freestyleHitFlameCounts[fretNum] < flameLimitHalf:
              flamecol = (flameColor[0], flameColor[1], flameColor[2])
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = self.spColor #(.3,.7,.9)
                else: #Default starcolor (Rockband)
                  flamecol = (.1,.1,.1)
              self.engine.draw3Dtex(self.hitflames2Drawing, coord = (x, y + .20, 0), rot = (90, 1, 0, 0),
                                    scale = (.25 + .6 * ms * ff, self.freestyleHitFlameCounts[fretNum]/6.0 + .6 * ms * ff, self.freestyleHitFlameCounts[fretNum] / 6.0 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                    texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)
  
              flamecol = (flameColor[0], flameColor[1], flameColor[2])
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = self.spColor #(.3,.7,.9)
                else: #Default starcolor (Rockband)
                  flamecol = (.1,.1,.1)
              self.engine.draw3Dtex(self.hitflames2Drawing, coord = (x - .005, y + .25 + .005, 0), rot = (90, 1, 0, 0),
                                    scale = (.30 + .6 * ms * ff, (self.freestyleHitFlameCounts[fretNum] + 1) / 5.5 + .6 * ms * ff, (self.freestyleHitFlameCounts[fretNum] + 1) / 5.5 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                    texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)
  
              flamecol = (flameColor[0], flameColor[1], flameColor[2])
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = self.spColor #(.3,.7,.9)
                else: #Default starcolor (Rockband)
                  #flamecol = glColor3f(.2,.2,.2)
                  flamecol = (.2,.2,.2)
              self.engine.draw3Dtex(self.hitflames2Drawing, coord = (x+.005, y +.25 +.005, 0), rot = (90, 1, 0, 0),
                                    scale = (.35 + .6 * ms * ff, (self.freestyleHitFlameCounts[fretNum] + 1) / 5.0 + .6 * ms * ff, (self.freestyleHitFlameCounts[fretNum] + 1) / 5.0 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                    texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)
  
              flamecol = (flameColor[0], flameColor[1], flameColor[2])
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = self.spColor #(.3,.7,.9)
                else: #Default starcolor (Rockband)
                  flamecol = (.3,.3,.3)
              self.engine.draw3Dtex(self.hitflames2Drawing, coord = (x, y +.25 +.005, 0), rot = (90, 1, 0, 0),
                                    scale = (.40 + .6 * ms * ff, (self.freestyleHitFlameCounts[fretNum] + 1)/ 4.7 + .6 * ms * ff, (self.freestyleHitFlameCounts[fretNum] + 1) / 4.7 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                    texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)
            else:
              flameColorMod0 = 0.1 * (flameLimit - self.freestyleHitFlameCounts[fretNum])
              flameColorMod1 = 0.1 * (flameLimit - self.freestyleHitFlameCounts[fretNum])
              flameColorMod2 = 0.1 * (flameLimit - self.freestyleHitFlameCounts[fretNum])
              
              flamecol = (flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)

              #MFH - hit lightning logic is not needed for freestyle flames...

              self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x, y + .35, 0), rot = (90, 1, 0, 0),
                                    scale = (.25 + .6 * ms * ff, self.freestyleHitFlameCounts[fretNum] / 3.0 + .6 * ms * ff, self.freestyleHitFlameCounts[fretNum] / 3.0 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                    texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)

  
              flameColorMod0 = 0.1 * (flameLimit - self.freestyleHitFlameCounts[fretNum])
              flameColorMod1 = 0.1 * (flameLimit - self.freestyleHitFlameCounts[fretNum])
              flameColorMod2 = 0.1 * (flameLimit - self.freestyleHitFlameCounts[fretNum])
              
              flamecol = (flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)      
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = self.spColor #(.3,.7,.9)
                else: #Default starcolor (Rockband)
                  flamecol = (.5,.5,.5)
              self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x - .005, y + .40 + .005, 0), rot = (90, 1, 0, 0),
                                    scale = (.30 + .6 * ms * ff, (self.freestyleHitFlameCounts[fretNum] + 1)/ 2.5 + .6 * ms * ff, (self.freestyleHitFlameCounts[fretNum] + 1) / 2.5 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                    texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)
  
              flameColorMod0 = 0.1 * (flameLimit - self.freestyleHitFlameCounts[fretNum])
              flameColorMod1 = 0.1 * (flameLimit - self.freestyleHitFlameCounts[fretNum])
              flameColorMod2 = 0.1 * (flameLimit - self.freestyleHitFlameCounts[fretNum])
              
              flamecol = (flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = self.spColor #(.3,.7,.9)
                else: #Default starcolor (Rockband)
                  flamecol = (.6,.6,.6)
              self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x + .005, y + .35 + .005, 0), rot = (90, 1, 0, 0),
                                    scale = (.35 + .6 * ms * ff, (self.freestyleHitFlameCounts[fretNum] + 1) / 2.0 + .6 * ms * ff, (self.freestyleHitFlameCounts[fretNum] + 1) / 2.0 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                    texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)              
  
              flameColorMod0 = 0.1 * (flameLimit - self.freestyleHitFlameCounts[fretNum])
              flameColorMod1 = 0.1 * (flameLimit - self.freestyleHitFlameCounts[fretNum])
              flameColorMod2 = 0.1 * (flameLimit - self.freestyleHitFlameCounts[fretNum])
              
              flamecol = (flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = self.spColor #(.3,.7,.9)
                else: #Default starcolor (Rockband)
                  flamecol = (.7,.7,.7)
              self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x + .005, y + .35 + .005, 0), rot = (90, 1, 0, 0),
                                    scale = (.40 + .6 * ms * ff, (self.freestyleHitFlameCounts[fretNum] + 1) / 1.7 + .6 * ms * ff, (self.freestyleHitFlameCounts[fretNum] + 1) / 1.7 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                    texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)             

            self.freestyleHitFlameCounts[fretNum] += 1
        
          else:   #MFH - flame count is done - reset it!
            self.freestyleHitFlameCounts[fretNum] = 0    #MFH



  def renderFlames(self, visibility, song, pos, controls):
    if not song or self.flameColors[0][0][0] == -1:
      return

    w = self.boardWidth / self.strings
    track = song.track[self.player]

    size = (.22, .22)
    v = 1.0 - visibility

    if self.disableFlameSFX != True and self.HCountAni == True and self.HCount2 > 12:
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
          if self.scoreMultiplier > 4:
            #cappedScoreMult = 4
            self.cappedScoreMult = 4
          else:
            self.cappedScoreMult = self.scoreMultiplier
          
          #flameSize = self.flameSizes[self.scoreMultiplier - 1][n]
          flameSize = self.flameSizes[self.cappedScoreMult - 1][n]
          if self.theme == 0 or self.theme == 1: #THIS SETS UP GH3 COLOR, ELSE ROCKBAND(which is DEFAULT in Theme.py)
            flameColor = self.gh3flameColor
          else:
            #flameColor = self.flameColors[self.scoreMultiplier - 1][n]
            flameColor = self.flameColors[self.cappedScoreMult - 1][n]
          #Below was an if that set the "flame"-color to the same as the fret color if there was no specific flamecolor defined.

          flameColorMod0 = 1.1973333333333333333333333333333
          flameColorMod1 = 1.9710526315789473684210526315789
          flameColorMod2 = 10.592592592592592592592592592593
          
          flamecol = (flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
          if self.starPowerActive:
            if self.theme == 0 or self.theme == 1: #GH3 starcolor
              flamecol = self.spColor #(.3,.7,.9)
            else: #Default starcolor (Rockband)
              flamecol = (.9,.9,.9)
              
          if self.Hitanim != True:   
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

            self.engine.draw3Dtex(self.hitglowAnim, coord = (x, y + .225, 0), rot = (90, 1, 0, 0), scale = (2.4, 1, 3.3),
                                  vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                  texcoord = (texX[0],0.0,texX[1],1.0), multiples = True, alpha = True, color = (1,1,1))

          ff += .3

          flameColorMod0 = 1.1973333333333333333333333333333
          flameColorMod1 = 1.7842105263157894736842105263158
          flameColorMod2 = 12.222222222222222222222222222222
          
          flamecol = (flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
          if self.starPowerActive:
            if self.theme == 0 or self.theme == 1: #GH3 starcolor
              flamecol = self.spColor #(.3,.7,.9)
            else: #Default starcolor (Rockband)
              flamecol = (.8,.8,.8)

          if self.Hitanim != True: 

            self.engine.draw3Dtex(self.hitglow2Drawing, coord = (x, y + .25, .05), rot = (90, 1, 0, 0),
                                  scale = (.40 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff),
                                  vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                  texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)
          

          #self.hit[n] = True   #MFH - gonna move these determinations into the runtime function, this is ridiculous

    if self.disableFlameSFX != True:
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
            #flameColor = self.flameColors[self.scoreMultiplier - 1][event.number]
            flameColor = self.flameColors[self.cappedScoreMult - 1][event.number]
          if flameColor[0] == -2:
            flameColor = self.fretColors[event.number]
          
          ff += 1.5 #ff first time is 2.75 after this

          if self.Hitanim2 == True:
            self.HCount2 = self.HCount2 + 1
            self.HCountAni = False
            if self.HCount2 > 12:
              if event.length <= 130:
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
              flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
              flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
              flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
              
              flamecol = (flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
              spcolmod = (.7,.7,.7)
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: 
                  flamecol = (self.spColor[0]*spcolmod[0], self.spColor[1]*spcolmod[1], self.spColor[2]*spcolmod[2])
                  #flamecol = (.3,.6,.7)#GH3 starcolor
                else:
                  flamecol = (.4,.4,.4)#Default starcolor (Rockband)
              if self.theme != 2 and event.finalStar and self.spEnabled:
                wid, hei, = self.engine.view.geometry[2:4]
                self.engine.draw3Dtex(self.hitlightning, coord = (xlightning, y, 3.3), rot = (90, 1, 0, 0),
                                      scale = (.15 + .5 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, 2), vertex = (.4,-2,-.4,2),
                                      texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = (1,1,1))
              else:
                self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x, y + .35, 0), rot = (90, 1, 0, 0),
                                      scale = (.25 + .6 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff),
                                      vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                      multiples = True, alpha = True, color = flamecol)

              flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
              flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
              flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
              
              flamecol = (flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)      
              spcolmod = (.8,.8,.8)
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = (self.spColor[0]*spcolmod[0], self.spColor[1]*spcolmod[1], self.spColor[2]*spcolmod[2])
                  #flamecol = (.3,.6,.8)
                else: #Default starcolor (Rockband)
                  flamecol = (.5,.5,.5)
              self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x - .005, y + .40 + .005, 0), rot = (90, 1, 0, 0),
                                    scale = (.30 + .6 * ms * ff, (event.flameCount + 1)/ 2.5 + .6 * ms * ff, (event.flameCount + 1) / 2.5 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                    multiples = True, alpha = True, color = flamecol)

              flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
              flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
              flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
              
              flamecol = (flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
              spcolmod = (.9,.9,.9)
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = (self.spColor[0]*spcolmod[0], self.spColor[1]*spcolmod[1], self.spColor[2]*spcolmod[2])
                  #flamecol = (.3,.7,.8)
                else: #Default starcolor (Rockband)
                  flamecol = (.6,.6,.6)
              self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x + .005, y + .35 + .005, 0), rot = (90, 1, 0, 0),
                                    scale = (.35 + .6 * ms * ff, (event.flameCount + 1) / 2.0 + .6 * ms * ff, (event.flameCount + 1) / 2.0 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                    multiples = True, alpha = True, color = flamecol)


              flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
              flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
              flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
              
              flamecol = (flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
              spcolmod = (1,1,1)
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = (self.spColor[0]*spcolmod[0], self.spColor[1]*spcolmod[1], self.spColor[2]*spcolmod[2])
                  #flamecol = (.3,.7,.9)
                else: #Default starcolor (Rockband)
                  flamecol = (.7,.7,.7)
              self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x+.005, y +.35 +.005, 0), rot = (90, 1, 0, 0),
                                    scale = (.40 + .6 * ms * ff, (event.flameCount + 1) / 1.7 + .6 * ms * ff, (event.flameCount + 1) / 1.7 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                    multiples = True, alpha = True, color = flamecol)
          else:
            self.HCount2 = 13
            self.HCountAni = True
            if event.flameCount < flameLimitHalf:
              flamecol = (flameColor[0], flameColor[1], flameColor[2])
              spcolmod = (.3,.3,.3)
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = (self.spColor[0]*spcolmod[0], self.spColor[1]*spcolmod[1], self.spColor[2]*spcolmod[2])
                  #flamecol = (.0,.2,.4)
                else: #Default starcolor (Rockband)
                  flamecol = (.1,.1,.1)
              self.engine.draw3Dtex(self.hitflames2Drawing, coord = (x, y + .20, 0), rot = (90, 1, 0, 0),
                                      scale = (.25 + .6 * ms * ff, event.flameCount/6.0 + .6 * ms * ff, event.flameCount / 6.0 + .6 * ms * ff),
                                      vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                      multiples = True, alpha = True, color = flamecol)

              flamecol = (flameColor[0], flameColor[1], flameColor[2])
              spcolmod = (.4,.4,.4)
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = (self.spColor[0]*spcolmod[0], self.spColor[1]*spcolmod[1], self.spColor[2]*spcolmod[2])
                  #flamecol = (.1,.3,.5)
                else: #Default starcolor (Rockband)
                  flamecol = (.1,.1,.1)
              self.engine.draw3Dtex(self.hitflames2Drawing, coord = (x-.005, y + .255, 0), rot = (90, 1, 0, 0),
                                    scale = (.30 + .6 * ms * ff, event.flameCount/5.5 + .6 * ms * ff, event.flameCount / 5.5 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                    multiples = True, alpha = True, color = flamecol)

              flamecol = (flameColor[0], flameColor[1], flameColor[2])
              spcolmod = (.5,.5,.5)
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = (self.spColor[0]*spcolmod[0], self.spColor[1]*spcolmod[1], self.spColor[2]*spcolmod[2])
                  #flamecol = (.2,.4,.7)
                else: #Default starcolor (Rockband)
                  flamecol = (.2,.2,.2)
              self.engine.draw3Dtex(self.hitflames2Drawing, coord = (x+.005, y+.255, 0), rot = (90, 1, 0, 0),
                                    scale = (.35 + .6 * ms * ff, event.flameCount/5.0 + .6 * ms * ff, event.flameCount / 5.0 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                    multiples = True, alpha = True, color = flamecol)

              flamecol = (flameColor[0], flameColor[1], flameColor[2])
              spcolmod = (.6,.6,.6)
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = (self.spColor[0]*spcolmod[0], self.spColor[1]*spcolmod[1], self.spColor[2]*spcolmod[2])
                  #flamecol = (.2,.5,.7)
                else: #Default starcolor (Rockband)
                  flamecol = (.3,.3,.3)

              self.engine.draw3Dtex(self.hitflames2Drawing, coord = (x, y+.255, 0), rot = (90, 1, 0, 0),
                                    scale = (.40 + .6 * ms * ff, event.flameCount/4.7 + .6 * ms * ff, event.flameCount / 4.7 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                    multiples = True, alpha = True, color = flamecol)
            else:
              flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
              flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
              flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
              
              flamecol = (flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
              spcolmod = (.7,.7,.7)
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: 
                  flamecol = (self.spColor[0]*spcolmod[0], self.spColor[1]*spcolmod[1], self.spColor[2]*spcolmod[2])
                  #flamecol = (.3,.6,.7)#GH3 starcolor
                else:
                  flamecol = (.4,.4,.4)#Default starcolor (Rockband)
              if self.theme != 2 and event.finalStar and self.spEnabled:
                wid, hei, = self.engine.view.geometry[2:4]
                self.engine.draw3Dtex(self.hitlightning, coord = (xlightning, y, 3.3), rot = (90, 1, 0, 0),
                                      scale = (.15 + .5 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, 2), vertex = (.4,-2,-.4,2),
                                      texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = (1,1,1))
              else:
                self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x, y + .35, 0), rot = (90, 1, 0, 0),
                                      scale = (.25 + .6 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff),
                                      vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                      multiples = True, alpha = True, color = flamecol)

              flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
              flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
              flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
              
              flamecol = (flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)      
              spcolmod = (.8,.8,.8)
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = (self.spColor[0]*spcolmod[0], self.spColor[1]*spcolmod[1], self.spColor[2]*spcolmod[2])
                  #flamecol = (.3,.6,.8)
                else: #Default starcolor (Rockband)
                  flamecol = (.5,.5,.5)
              self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x - .005, y + .40 + .005, 0), rot = (90, 1, 0, 0),
                                    scale = (.30 + .6 * ms * ff, (event.flameCount + 1)/ 2.5 + .6 * ms * ff, (event.flameCount + 1) / 2.5 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                    multiples = True, alpha = True, color = flamecol)

              flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
              flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
              flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
              
              flamecol = (flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
              spcolmod = (.9,.9,.9)
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = (self.spColor[0]*spcolmod[0], self.spColor[1]*spcolmod[1], self.spColor[2]*spcolmod[2])
                  #flamecol = (.3,.7,.8)
                else: #Default starcolor (Rockband)
                  flamecol = (.6,.6,.6)
              self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x + .005, y + .35 + .005, 0), rot = (90, 1, 0, 0),
                                    scale = (.35 + .6 * ms * ff, (event.flameCount + 1) / 2.0 + .6 * ms * ff, (event.flameCount + 1) / 2.0 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                    multiples = True, alpha = True, color = flamecol)


              flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
              flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
              flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
              
              flamecol = (flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
              spcolmod = (1,1,1)
              if self.starPowerActive:
                if self.theme == 0 or self.theme == 1: #GH3 starcolor
                  flamecol = (self.spColor[0]*spcolmod[0], self.spColor[1]*spcolmod[1], self.spColor[2]*spcolmod[2])
                  #flamecol = (.3,.7,.9)
                else: #Default starcolor (Rockband)
                  flamecol = (.7,.7,.7)
              self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x+.005, y +.35 +.005, 0), rot = (90, 1, 0, 0),
                                    scale = (.40 + .6 * ms * ff, (event.flameCount + 1) / 1.7 + .6 * ms * ff, (event.flameCount + 1) / 1.7 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                    multiples = True, alpha = True, color = flamecol)
          event.flameCount += 1
        
  def render(self, visibility, song, pos, controls, killswitch):
  
    if shaders.turnon:
      shaders.globals["dfActive"] = self.drumFillsActive
      shaders.globals["breActive"] = self.freestyleActive
      shaders.globals["rockLevel"] = self.rockLevel
      

    if not self.starNotesSet == True:
      self.totalNotes = 0
      
      
      for time, event in song.track[self.player].getAllEvents():
        if not isinstance(event, Note):
          continue
        self.totalNotes += 1
        
        
      stars = []
      maxStars = []
      maxPhrase = self.totalNotes/120
      for q in range(0,maxPhrase):
        for n in range(0,10):
          stars.append(self.totalNotes/maxPhrase*(q)+n+maxPhrase/4)
        maxStars.append(self.totalNotes/maxPhrase*(q)+10+maxPhrase/4)
      i = 0
      for time, event in song.track[self.player].getAllEvents():
        if not isinstance(event, Note):
          continue
        for a in stars:
          if i == a:
            self.starNotes.append(time)
            event.star = True
        for a in maxStars:
          if i == a:
            self.maxStars.append(time)
            event.finalStar = True
        i += 1
      for time, event in song.track[self.player].getAllEvents():
        if not isinstance(event, Note):
          continue
        for q in self.starNotes:
          if time == q:
            event.star = True
        for q in self.maxStars:
          #if time == q and not event.finalStar:
          #  event.star = True
          if time == q:   #MFH - no need to mark only the final SP phrase note as the finalStar as in drums, they will be hit simultaneously here.
            event.finalStar = True
      self.starNotesSet = True

    if not (self.coOpFailed and not self.coOpRestart):
      glEnable(GL_BLEND)
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
      glEnable(GL_COLOR_MATERIAL)
      if self.leftyMode:
        if not self.battleStatus[6]:
          glScalef(-1, 1, 1)
      elif self.battleStatus[6]:
        glScalef(-1, 1, 1)



      if self.scoreMultiplier > 4 and self.bgcount < 1:
        self.bgcount += .1
      if self.scoreMultiplier < 4 and self.bgcount > 0:
        self.bgcount -= .1

      if self.freestyleActive:
        self.renderTails(visibility, song, pos, killswitch)
        self.renderNotes(visibility, song, pos, killswitch)
        self.renderFreestyleLanes(visibility, song, pos) #MFH - render the lanes on top of the notes.
        self.renderFrets(visibility, song, controls)

        if self.hitFlamesPresent:   #MFH - only if present!
          self.renderFreestyleFlames(visibility, controls)    #MFH - freestyle hit flames

      else:    
        if self.fretsUnderNotes:  #MFH
          if self.twoDnote == True:
            self.renderTails(visibility, song, pos, killswitch)
            self.renderFrets(visibility, song, controls)
            self.renderNotes(visibility, song, pos, killswitch)
          else:
            self.renderTails(visibility, song, pos, killswitch)
            self.renderNotes(visibility, song, pos, killswitch)
            self.renderFrets(visibility, song, controls)
        else:
          self.renderTails(visibility, song, pos, killswitch)
          self.renderNotes(visibility, song, pos, killswitch)
          self.renderFrets(visibility, song, controls)

        self.renderFreestyleLanes(visibility, song, pos) #MFH - render the lanes on top of the notes.

        
        if self.hitFlamesPresent:   #MFH - only if present!
          self.renderFlames(visibility, song, pos, controls)    #MFH - only when freestyle inactive!
        
      if self.leftyMode:
        if not self.battleStatus[6]:
          glScalef(-1, 1, 1)
      elif self.battleStatus[6]:
        glScalef(-1, 1, 1)

  def getMissedNotes(self, song, pos, catchup = False):
    if not song:
      return
    if not song.readyToGo:
      return

    m1      = self.lateMargin
    m2      = self.lateMargin * 2

    #if catchup == True:
    #  m2 = 0
      
    track   = song.track[self.player]
    notes   = [(time, event) for time, event in track.getEvents(pos - m1, pos - m2) if isinstance(event, Note)]
    notes   = [(time, event) for time, event in notes if (time >= (pos - m2)) and (time <= (pos - m1))]
    notes   = [(time, event) for time, event in notes if not event.played and not event.hopod and not event.skipped]

    if catchup == True:
      for time, event in notes:
        event.skipped = True

    return sorted(notes, key=lambda x: x[1].number)        
    #return notes

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



  def getRequiredNotes(self, song, pos):
    if self.battleStatus[2] and self.difficulty != 0:
      if pos < self.battleStartTimes[2] + self.currentPeriod * self.beatsPerBoard or pos > self.battleStartTimes[2] - self.currentPeriod * self.beatsPerBoard + self.battleDiffUpLength:
        song.difficulty[self.player] = Song.difficulties[self.battleDiffUpValue]
      else:
        song.difficulty[self.player] = Song.difficulties[self.battleDiffUpValue - 1]
        
    track   = song.track[self.player]
    notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + self.earlyMargin) if isinstance(event, Note)]
    notes = [(time, event) for time, event in notes if not event.played]
    notes = [(time, event) for time, event in notes if (time >= (pos - self.lateMargin)) and (time <= (pos + self.earlyMargin))]
    if notes:
      t     = min([time for time, event in notes])
      notes = [(time, event) for time, event in notes if time - t < 1e-3]
    #Log.debug(notes)
    if self.battleStatus[7]:
      notes = self.getDoubleNotes(notes)
    return sorted(notes, key=lambda x: x[1].number)

  def getRequiredNotes2(self, song, pos, hopo = False):
    if self.battleStatus[2] and self.difficulty != 0:
      if pos < self.battleStartTimes[2] + self.currentPeriod * self.beatsPerBoard or pos > self.battleStartTimes[2] - self.currentPeriod * self.beatsPerBoard + self.battleDiffUpLength:
        song.difficulty[self.player] = Song.difficulties[self.battleDiffUpValue]
      else:
        song.difficulty[self.player] = Song.difficulties[self.battleDiffUpValue - 1]
        
    track   = song.track[self.player]
    notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + self.earlyMargin) if isinstance(event, Note)]
    notes = [(time, event) for time, event in notes if not (event.hopod or event.played)]
    notes = [(time, event) for time, event in notes if (time >= (pos - self.lateMargin)) and (time <= (pos + self.earlyMargin))]
    if notes:
      t     = min([time for time, event in notes])
      notes = [(time, event) for time, event in notes if time - t < 1e-3]
    #Log.debug(notes)
    if self.battleStatus[7]:
      notes = self.getDoubleNotes(notes)
    return sorted(notes, key=lambda x: x[1].number)
    
  def getRequiredNotes3(self, song, pos, hopo = False):
    if self.battleStatus[2] and self.difficulty != 0:
      if pos < self.battleStartTimes[2] + self.currentPeriod * self.beatsPerBoard or pos > self.battleStartTimes[2] - self.currentPeriod * self.beatsPerBoard + self.battleDiffUpLength:
        song.difficulty[self.player] = Song.difficulties[self.battleDiffUpValue]
      else:
        song.difficulty[self.player] = Song.difficulties[self.battleDiffUpValue - 1]
        
    track   = song.track[self.player]
    notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + self.earlyMargin) if isinstance(event, Note)]
    notes = [(time, event) for time, event in notes if not (event.hopod or event.played or event.skipped)]
    notes = [(time, event) for time, event in notes if (time >= (pos - self.lateMargin)) and (time <= (pos + self.earlyMargin))]
    #Log.debug(notes)
    if self.battleStatus[7]:
      notes = self.getDoubleNotes(notes)
    return sorted(notes, key=lambda x: x[1].number)

  #MFH - corrected and optimized:
  #def getRequiredNotesMFH(self, song, pos):
  def getRequiredNotesMFH(self, song, pos, hopoTroubleCheck = False):
    if self.battleStatus[2] and self.difficulty != 0:
      if pos < self.battleStartTimes[2] + self.currentPeriod * self.beatsPerBoard or pos > self.battleStartTimes[2] - self.currentPeriod * self.beatsPerBoard + self.battleDiffUpLength:
        song.difficulty[self.player] = Song.difficulties[self.battleDiffUpValue]
      else:
        song.difficulty[self.player] = Song.difficulties[self.battleDiffUpValue - 1]
    
    track   = song.track[self.player]
    if hopoTroubleCheck:
      #notes = [(time, event) for time, event in track.getEvents(pos, pos + (self.earlyMargin*2)) if isinstance(event, Note)]
      #notes = [(time, event) for time, event in notes if not (event.hopod or event.played or event.skipped)]
      notes = [(time, event) for time, event in track.getEvents(pos, pos + (self.earlyMargin*2)) if isinstance(event, Note)]
      notes = [(time, event) for time, event in notes if not time==pos] #MFH - filter out the problem note that caused this check!
    else:
      notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + self.earlyMargin) if isinstance(event, Note)]
      notes = [(time, event) for time, event in notes if not (event.hopod or event.played or event.skipped)]
      #MFH - this additional filtration step removes sustains whose Note On event time is now outside the hitwindow.
      notes = [(time, event) for time, event in notes if (time >= (pos - self.lateMargin)) and (time <= (pos + self.earlyMargin))]

    sorted(notes, key=lambda x: x[0])
    if self.battleStatus[7]:
      notes = self.getDoubleNotes(notes)
    return sorted(notes, key=lambda x: x[0])    #MFH - what the hell, this should be sorted by TIME not note number....

  def getDoubleNotes(self, notes):
    if self.battleStatus[7] and notes != []:
      notes = sorted(notes, key=lambda x: x[0])
      curTime = 0
      tempnotes = []
      tempnumbers = []
      tempnote = None
      curNumbers = []
      noteCount = 0
      for time, note in notes:
        noteCount += 1
        if not isinstance(note, Note):
          if noteCount == len(notes) and len(curNumbers) < 3 and len(curNumbers) > 0:
            maxNote = curNumbers[0]
            minNote = curNumbers[0]
            for i in range(0, len(curNumbers)):
              if curNumbers[i] > maxNote:
                maxNote = curNumbers[i]
              if curNumbers[i] < minNote:
                minNote = curNumbers[i]
            curNumbers = []
            if maxNote < 4:
              tempnumbers.append(maxNote + 1)
            elif minNote > 0:
              tempnumbers.append(minNote - 1)
            else:
              tempnumbers.append(2)
          elif noteCount == len(notes) and len(curNumbers) > 2:
            tempnumbers.append(-1)
            curNumbers = []
          continue
        if time != curTime:
          if curTime != 0 and len(curNumbers) < 3:
            maxNote = curNumbers[0]
            minNote = curNumbers[0]
            for i in range(0, len(curNumbers)):
              if curNumbers[i] > maxNote:
                maxNote = curNumbers[i]
              if curNumbers[i] < minNote:
                minNote = curNumbers[i]
            curNumbers = []
            if maxNote < 4:
              tempnumbers.append(maxNote + 1)
            elif minNote > 0:
              tempnumbers.append(minNote - 1)
            else:
              tempnumbers.append(2)
          elif (curTime != 0 or noteCount == len(notes)) and len(curNumbers) > 2:
            tempnumbers.append(-1)
            curNumbers = []
          tempnotes.append((time,deepcopy(note)))
          curTime = time
          curNumbers.append(note.number)
          if noteCount == len(notes) and len(curNumbers) < 3:
            maxNote = curNumbers[0]
            minNote = curNumbers[0]
            for i in range(0, len(curNumbers)):
              if curNumbers[i] > maxNote:
                maxNote = curNumbers[i]
              if curNumbers[i] < minNote:
                minNote = curNumbers[i]
            curNumbers = []
            if maxNote < 4:
              tempnumbers.append(maxNote + 1)
            elif minNote > 0:
              tempnumbers.append(minNote - 1)
            else:
              tempnumbers.append(2)
          elif noteCount == len(notes) and len(curNumbers) > 2:
            tempnumbers.append(-1)
            curNumbers = []
        else:
          curNumbers.append(note.number)
          if noteCount == len(notes) and len(curNumbers) < 3:
            maxNote = curNumbers[0]
            minNote = curNumbers[0]
            for i in range(0, len(curNumbers)):
              if curNumbers[i] > maxNote:
                maxNote = curNumbers[i]
              if curNumbers[i] < minNote:
                minNote = curNumbers[i]
            curNumbers = []
            if maxNote < 4:
              tempnumbers.append(maxNote + 1)
            elif minNote > 0:
              tempnumbers.append(minNote - 1)
            else:
              tempnumbers.append(2)
          elif noteCount == len(notes) and len(curNumbers) > 2:
            tempnumbers.append(-1)
            curNumbers = []
      noteCount = 0
      for time, note in tempnotes:
        if tempnumbers[noteCount] != -1:
          note.number = tempnumbers[noteCount]
          noteCount += 1
          if time > self.battleStartTimes[7] + self.currentPeriod * self.beatsPerBoard and time < self.battleStartTimes[7] - self.currentPeriod * self.beatsPerBoard + self.battleDoubleLength:
            notes.append((time,note))
        else:
          noteCount += 1
    return sorted(notes, key=lambda x: x[0])

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
      #Log.debug(notes)
    else:
      track   = song.track[self.player]
      notes = [(time, event) for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard)]
    
    if self.battleStatus[7]:
      notes = self.getDoubleNotes(notes)
    return notes
 
  #MFH - corrected and optimized:
  def getRequiredNotesForJurgenOnTime(self, song, pos):
    track   = song.track[self.player]
    notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + 30) if isinstance(event, Note)]
    notes = [(time, event) for time, event in notes if not (event.hopod or event.played or event.skipped)]

    if self.battleStatus[7]:
      notes = self.getDoubleNotes(notes)
    return sorted(notes, key=lambda x: x[0])    #MFH - what the hell, this should be sorted by TIME not note number....



  def controlsMatchNotes(self, controls, notes):
    # no notes?
    if not notes:
      return False
  
    # check each valid chord
    chords = {}
    for time, note in notes:
      if not time in chords:
        chords[time] = []
      chords[time].append((time, note))

    #Make sure the notes are in the right time order
    chordlist = chords.values()
    chordlist.sort(lambda a, b: cmp(a[0][0], b[0][0]))

    twochord = 0
    for chord in chordlist:
      # matching keys?
      requiredKeys = [note.number for time, note in chord]
      requiredKeys = self.uniqify(requiredKeys)
      
      if len(requiredKeys) > 2 and self.twoChordMax == True:
        twochord = 0
        for k in self.keys:
          if controls.getState(k):
            twochord += 1
        if twochord == 2:
          skipped = len(requiredKeys) - 2
          requiredKeys = [min(requiredKeys), max(requiredKeys)]
        else:
          twochord = 0

      for n in range(self.strings):
        if n in requiredKeys and not (controls.getState(self.keys[n]) or controls.getState(self.keys[n+5])):
          return False
        if not n in requiredKeys and (controls.getState(self.keys[n]) or controls.getState(self.keys[n+5])):
          # The lower frets can be held down
          if n > max(requiredKeys):
            return False
      if twochord != 0:
        if twochord != 2:
          for time, note in chord:
            note.played = True
        else:
          self.twoChordApply = True
          for time, note in chord:
            note.skipped = True
          chord[0][1].skipped = False
          chord[-1][1].skipped = False
          chord[0][1].played = True
          chord[-1][1].played = True
    if twochord == 2:
      self.twoChord += skipped

    return True

  def controlsMatchNotes2(self, controls, notes, hopo = False):
    # no notes?
    if not notes:
      return False

    # check each valid chord
    chords = {}
    for time, note in notes:
      if note.hopod == True and (controls.getState(self.keys[note.number]) or controls.getState(self.keys[note.number + 5])):
      #if hopo == True and controls.getState(self.keys[note.number]):
        self.playedNotes = []
        return True
      if not time in chords:
        chords[time] = []
      chords[time].append((time, note))

    #Make sure the notes are in the right time order
    chordlist = chords.values()
    chordlist.sort(lambda a, b: cmp(a[0][0], b[0][0]))

    twochord = 0
    for chord in chordlist:
      # matching keys?
      requiredKeys = [note.number for time, note in chord]
      requiredKeys = self.uniqify(requiredKeys)

      if len(requiredKeys) > 2 and self.twoChordMax == True:
        twochord = 0
        for n, k in enumerate(self.keys):
          if controls.getState(k):
            twochord += 1
        if twochord == 2:
          skipped = len(requiredKeys) - 2
          requiredKeys = [min(requiredKeys), max(requiredKeys)]
        else:
          twochord = 0
        
      for n in range(self.strings):
        if n in requiredKeys and not (controls.getState(self.keys[n]) or controls.getState(self.keys[n+5])):
          return False
        if not n in requiredKeys and (controls.getState(self.keys[n]) or controls.getState(self.keys[n+5])):
          # The lower frets can be held down
          if hopo == False and n >= min(requiredKeys):
            return False
      if twochord != 0:
        if twochord != 2:
          for time, note in chord:
            note.played = True
        else:
          self.twoChordApply = True
          for time, note in chord:
            note.skipped = True
          chord[0][1].skipped = False
          chord[-1][1].skipped = False
          chord[0][1].played = True
          chord[-1][1].played = True
        
    if twochord == 2:
      self.twoChord += skipped
      
    return True

  def controlsMatchNotes3(self, controls, notes, hopo = False):
    # no notes?
    if not notes:
      return False

    # check each valid chord
    chords = {}
    for time, note in notes:
      if note.hopod == True and (controls.getState(self.keys[note.number]) or controls.getState(self.keys[note.number + 5])):
      #if hopo == True and controls.getState(self.keys[note.number]):
        self.playedNotes = []
        return True
      if not time in chords:
        chords[time] = []
      chords[time].append((time, note))

    #Make sure the notes are in the right time order
    chordlist = chords.values()
    #chordlist.sort(lambda a, b: cmp(a[0][0], b[0][0]))
    chordlist.sort(key=lambda a: a[0][0])

    self.missedNotes = []
    self.missedNoteNums = []
    twochord = 0
    for chord in chordlist:
      # matching keys?
      requiredKeys = [note.number for time, note in chord]
      requiredKeys = self.uniqify(requiredKeys)

      if len(requiredKeys) > 2 and self.twoChordMax == True:
        twochord = 0
        for n, k in enumerate(self.keys):
          if controls.getState(k):
            twochord += 1
        if twochord == 2:
          skipped = len(requiredKeys) - 2
          requiredKeys = [min(requiredKeys), max(requiredKeys)]
        else:
          twochord = 0
          
      if (self.controlsMatchNote3(controls, chord, requiredKeys, hopo)):
        if twochord != 2:
          for time, note in chord:
            note.played = True
        else:
          self.twoChordApply = True
          for time, note in chord:
            note.skipped = True
          chord[0][1].skipped = False
          chord[-1][1].skipped = False
          chord[0][1].played = True
          chord[-1][1].played = True
        break
      if hopo == True:
        break
      self.missedNotes.append(chord)
    else:
      self.missedNotes = []
      self.missedNoteNums = []
    
    for chord in self.missedNotes:
      for time, note in chord:
        if self.debugMode:
          self.missedNoteNums.append(note.number)
        note.skipped = True
        note.played = False
    if twochord == 2:
      self.twoChord += skipped
      
    return True

  #MFH - special function for HOPO intentions checking
  def controlsMatchNextChord(self, controls, notes):
    # no notes?
    if not notes:
      return False

    # check each valid chord
    chords = {}
    for time, note in notes:
      if not time in chords:
        chords[time] = []
      chords[time].append((time, note))

    #Make sure the notes are in the right time order
    chordlist = chords.values()
    chordlist.sort(key=lambda a: a[0][0])

    twochord = 0
    for chord in chordlist:
      # matching keys?
      self.requiredKeys = [note.number for time, note in chord]
      self.requiredKeys = self.uniqify(self.requiredKeys)

      if len(self.requiredKeys) > 2 and self.twoChordMax == True:
        twochord = 0
        self.twoChordApply = True
        for n, k in enumerate(self.keys):
          if controls.getState(k):
            twochord += 1
        if twochord == 2:
          skipped = len(self.requiredKeys) - 2
          self.requiredKeys = [min(self.requiredKeys), max(self.requiredKeys)]
        else:
          twochord = 0
          
      if (self.controlsMatchNote3(controls, chord, self.requiredKeys, False)):
        return True
      else:
        return False




  def uniqify(self, seq, idfun=None): 
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result
  
  def controlsMatchNote3(self, controls, chordTuple, requiredKeys, hopo):
    if len(chordTuple) > 1:
    #Chords must match exactly
      for n in range(self.strings):
        if (n in requiredKeys and not (controls.getState(self.keys[n]) or controls.getState(self.keys[n+5]))) or (n not in requiredKeys and (controls.getState(self.keys[n]) or controls.getState(self.keys[n+5]))):
          return False
    else:
    #Single Note must match that note
      requiredKey = requiredKeys[0]
      if not controls.getState(self.keys[requiredKey]) and not controls.getState(self.keys[requiredKey+5]):
        return False


      #myfingershurt: this is where to filter out higher frets held when HOPOing:
      if hopo == False or self.hopoStyle == 2 or self.hopoStyle == 3:
      #Check for higher numbered frets if not a HOPO or if GH2 strict mode
        for n, k in enumerate(self.keys):
          if (n > requiredKey and n < 5) or (n > 4 and n > requiredKey + 5):
          #higher numbered frets cannot be held
            if controls.getState(k):
              return False

    return True

  def areNotesTappable(self, notes):
    if not notes:
      return
    for time, note in notes:
      if note.tappable > 1:
        return True
    return False
  
  def startPick(self, song, pos, controls, hopo = False):
    if hopo == True:
      res = startPick2(song, pos, controls, hopo)
      return res
    if not song:
      return False
    if not song.readyToGo:
      return False
    
    self.playedNotes = []
    
    self.matchingNotes = self.getRequiredNotes(song, pos)

    if self.controlsMatchNotes(controls, self.matchingNotes):
      self.pickStartPos = pos
      for time, note in self.matchingNotes:
        if note.skipped == True:
          continue
        self.pickStartPos = max(self.pickStartPos, time)
        note.played       = True
        self.playedNotes.append([time, note])
        if self.guitarSolo:
          self.currentGuitarSoloHitNotes += 1
      return True
    return False

  def startPick2(self, song, pos, controls, hopo = False):
    if not song:
      return False
    if not song.readyToGo:
      return False
    
    self.playedNotes = []
    
    self.matchingNotes = self.getRequiredNotes2(song, pos, hopo)

    if self.controlsMatchNotes2(controls, self.matchingNotes, hopo):
      self.pickStartPos = pos
      for time, note in self.matchingNotes:
        if note.skipped == True:
          continue
        self.pickStartPos = max(self.pickStartPos, time)
        if hopo:
          note.hopod        = True
        else:
          note.played       = True
        if note.tappable == 1 or note.tappable == 2:
          self.hopoActive = time
          self.wasLastNoteHopod = True
        elif note.tappable == 3:
          self.hopoActive = -time
          self.wasLastNoteHopod = True
        else:
          self.hopoActive = 0
          self.wasLastNoteHopod = False
        self.playedNotes.append([time, note])
        if self.guitarSolo:
          self.currentGuitarSoloHitNotes += 1
        
      self.hopoLast     = note.number
      return True
    return False

  def startPick3(self, song, pos, controls, hopo = False):
    if not song:
      return False
    if not song.readyToGo:
      return False
    
    self.lastPlayedNotes = self.playedNotes
    self.playedNotes = []
    
    self.matchingNotes = self.getRequiredNotesMFH(song, pos)

    self.controlsMatchNotes3(controls, self.matchingNotes, hopo)
    
    #myfingershurt
    
    for time, note in self.matchingNotes:
      if note.played != True:
        continue
      
      if shaders.turnon:
        shaders.var["fret"][self.player][note.number]=shaders.time()
        shaders.var["fretpos"][self.player][note.number]=pos
        
      
      self.pickStartPos = pos
      self.pickStartPos = max(self.pickStartPos, time)
      if hopo:
        note.hopod        = True
      else:
        note.played       = True
        #self.wasLastNoteHopod = False
      if note.tappable == 1 or note.tappable == 2:
        self.hopoActive = time
        self.wasLastNoteHopod = True
      elif note.tappable == 3:
        self.hopoActive = -time
        self.wasLastNoteHopod = True
        if hopo:  #MFH - you just tapped a 3 - make a note of it. (har har)
          self.hopoProblemNoteNum = note.number
          self.sameNoteHopoString = True
      else:
        self.hopoActive = 0
        self.wasLastNoteHopod = False
      self.hopoLast     = note.number
      self.playedNotes.append([time, note])
      if self.guitarSolo:
        self.currentGuitarSoloHitNotes += 1
        

     
    #myfingershurt: be sure to catch when a chord is played
    if len(self.playedNotes) > 1:
      lastPlayedNote = None
      for time, note in self.playedNotes:
        if isinstance(lastPlayedNote, Note):
          if note.tappable == 1 and lastPlayedNote.tappable == 1:
            self.LastStrumWasChord = True
            #self.sameNoteHopoString = False
          else:
            self.LastStrumWasChord = False
        lastPlayedNote = note
    
    elif len(self.playedNotes) > 0: #ensure at least that a note was played here
      self.LastStrumWasChord = False

    if len(self.playedNotes) != 0:
      return True
    return False

  def soloFreestylePick(self, song, pos, controls):
    numHits = 0
    for theFret in range(5):
      self.freestyleHit[theFret] = controls.getState(self.keys[theFret+5])
      if self.freestyleHit[theFret]:
        if shaders.turnon:
          shaders.var["fret"][self.player][theFret]=shaders.time()
          shaders.var["fretpos"][self.player][theFret]=pos
        numHits += 1
    return numHits

  #MFH - TODO - handle freestyle picks here
  def freestylePick(self, song, pos, controls):
    numHits = 0
    #if not song:
    #  return numHits
    
    if not controls.getState(self.actions[0]) and not controls.getState(self.actions[1]):
      return 0

    for theFret in range(5):
      self.freestyleHit[theFret] = controls.getState(self.keys[theFret])
      if self.freestyleHit[theFret]:
        if shaders.turnon:
          shaders.var["fret"][self.player][theFret]=shaders.time()
          shaders.var["fretpos"][self.player][theFret]=pos
        numHits += 1
    return numHits




  def endPick(self, pos):
    for time, note in self.playedNotes:
      if time + note.length > pos + self.noteReleaseMargin:
        self.playedNotes = []
        return False
      
    self.playedNotes = []
    return True
    
  def getPickLength(self, pos):
    if not self.playedNotes:
      return 0.0
    
    # The pick length is limited by the played notes
    pickLength = pos - self.pickStartPos
    for time, note in self.playedNotes:
      pickLength = min(pickLength, note.length)
    return pickLength


  def coOpRescue(self, pos):
    self.coOpRestart = True #initializes Restart Timer
    self.coOpRescueTime  = pos
    self.starPower  = 0
    Log.debug("Rescued at " + str(pos))
  
  def run(self, ticks, pos, controls):
  
    if not self.paused:
      self.time += ticks
    
    #MFH - Determine which frame to display for starpower notes
    if self.starspin:
      self.indexCount = self.indexCount + 1
      if self.indexCount > self.Animspeed-1:
        self.indexCount = 0
      self.starSpinFrameIndex = (self.indexCount * self.starSpinFrames - (self.indexCount * self.starSpinFrames) % self.Animspeed) / self.Animspeed
      if self.starSpinFrameIndex > self.starSpinFrames - 1:
        self.starSpinFrameIndex = 0
        
    
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

    
    # update frets
    if self.editorMode:
      if (controls.getState(self.actions[0]) or controls.getState(self.actions[1])):
        for i in range(self.strings):
          if controls.getState(self.keys[i]) or controls.getState(self.keys[i+5]):
            activeFrets.append(i)
        activeFrets = activeFrets or [self.selectedString]
      else:
        activeFrets = []
    else:
      activeFrets = [note.number for time, note in self.playedNotes]
    
    for n in range(self.strings):
      if controls.getState(self.keys[n]) or controls.getState(self.keys[n+5]) or (self.editorMode and self.selectedString == n):
        self.fretWeight[n] = 0.5
      else:
        self.fretWeight[n] = max(self.fretWeight[n] - ticks / 64.0, 0.0)
      if n in activeFrets:
        self.fretActivity[n] = min(self.fretActivity[n] + ticks / 32.0, 1.0)
      else:
        self.fretActivity[n] = max(self.fretActivity[n] - ticks / 64.0, 0.0)
      
      #MFH - THIS is where note sustains should be determined... NOT in renderNotes / renderFrets / renderFlames  -.-
      if self.fretActivity[n]:
        self.hit[n] = True
      else:
        self.hit[n] = False

    
    if self.vbpmLogicType == 0:   #MFH - VBPM (old)
      if self.currentBpm != self.targetBpm:
        diff = self.targetBpm - self.currentBpm
        if (round((diff * .03), 4) != 0):
          self.currentBpm = round(self.currentBpm + (diff * .03), 4)
        else:
          self.currentBpm = self.targetBpm
        self.setBPM(self.currentBpm) # glorandwarf: was setDynamicBPM(self.currentBpm)

    for time, note in self.playedNotes:
      if pos > time + note.length:
        return False

    return True


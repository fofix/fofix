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

from OpenGL.GL import *
import math

#myfingershurt: needed for multi-OS file fetching
import os

import Log

import Song   #need the base song defines as well

#KEYS = [Player.KEY1, Player.KEY2, Player.KEY3, Player.KEY4, Player.KEY5]
PLAYER1KEYS    = [Player.KEY1, Player.KEY2, Player.KEY3, Player.KEY4, Player.KEY5]
PLAYER1ACTIONS = [Player.ACTION1, Player.ACTION2]
PLAYER2KEYS    = [Player.PLAYER_2_KEY1, Player.PLAYER_2_KEY2, Player.PLAYER_2_KEY3, Player.PLAYER_2_KEY4, Player.PLAYER_2_KEY5]
PLAYER2ACTIONS = [Player.PLAYER_2_ACTION1, Player.PLAYER_2_ACTION2]


class Guitar:
  def __init__(self, engine, editorMode = False, player = 0):
    self.engine         = engine
    self.isDrum = False
    self.isBassGuitar = False
    
    self.debugMode = False

    self.matchingNotes = []
    
    self.sameNoteHopoString = False
    self.hopoProblemNoteNum = -1
    
    self.useMidiSoloMarkers = False
    self.canGuitarSolo = False
    self.guitarSolo = False
    self.currentGuitarSoloHitNotes = 0

    self.cappedScoreMult = 0
    self.starSpinFrameIndex = 0

    self.isStarPhrase = False
    self.finalStarSeen = False

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
    
    self.boardWidth     = 3.0
    self.boardLength    = 9.0
    self.beatsPerBoard  = 5.0
    self.strings        = 5
    self.fretWeight     = [0.0] * self.strings
    self.fretActivity   = [0.0] * self.strings
    self.fretColors     = Theme.fretColors
    self.playedNotes    = []
    
    self.lastPlayedNotes = []   #MFH - for reverting when game discovers it implied incorrectly
    
    self.missedNotes    = []
    self.missedNoteNums = []
    self.editorMode     = editorMode
    self.selectedString = 0
    self.time           = 0.0
    self.pickStartPos   = 0
    self.leftyMode      = False


    self.actualBpm = 0.0

    self.currentBpm     = 50.0   
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
    self.Hitanim        = True
    
    #myfingershurt: to keep track of pause status here as well
    self.paused = False

    self.spEnabled = True
    self.starPower = 0
    self.starPowerActive = False
    self.starPowerGained = False

    self.killPoints = False

    self.starpowerMode = self.engine.config.get("game", "starpower_mode") #MFH

    #get difficulty
    self.difficulty = self.engine.config.get("player%d" %(player), "difficulty")

    #myfingershurt:
    self.hopoStyle        = self.engine.config.get("game", "hopo_style")
    self.LastStrumWasChord = False
    self.spRefillMode = self.engine.config.get("game","sp_notes_while_active")
    self.hitglow_color = self.engine.config.get("video", "hitglow_color") #this should be global, not retrieved every fret render.
    self.sfxVolume    = self.engine.config.get("audio", "SFX_volume")
    
    #myfingershurt: this should be retrieved once at init, not repeatedly in-game whenever tails are rendered.
    self.notedisappear = self.engine.config.get("game", "notedisappear")
    self.fretsUnderNotes  = self.engine.config.get("game", "frets_under_notes")
    self.staticStrings  = self.engine.config.get("performance", "static_strings")
    


    self.muteSustainReleases = self.engine.config.get("game", "sustain_muting") #MFH

    self.hitw = self.engine.config.get("game", "hit_window")  #this should be global, not retrieved every BPM change.
    if self.hitw == 0:   #wide
      self.hitw = 0.70
    elif self.hitw == 1: #normal
      self.hitw = 1.0
    elif self.hitw == 2: #tight
      self.hitw = 1.2
    elif self.hitw == 3: #blazingamer new tighter hit window
      self.hitw = 1.9
    elif self.hitw == 4: #racer: new super tight hit window
      self.hitw = 2.3
    else:
      self.hitw = 1

    
    self.twoChord       = 0
    self.hopoActive     = 0
    
    #myfingershurt: need a separate variable to track whether or not hopos are actually active
    self.wasLastNoteHopod = False
    
    
    self.hopoLast       = -1
    self.hopoColor      = (0, .5, .5)
    self.player         = player
    self.scoreMultiplier = 1

    self.hit = [False, False, False, False, False]

    neckSettingName = "neck_choose_p%d" % (self.player)
    self.neck = self.engine.config.get("coffee", neckSettingName)

    #Get theme
    themename = self.engine.data.themeLabel
    #now theme determination logic is only in data.py:
    self.theme = self.engine.data.theme

    #blazingamer
    self.nstype = self.engine.config.get("game", "nstype")
    self.twoDnote = Theme.twoDnote
    self.twoDkeys = Theme.twoDkeys 
    self.threeDspin = Theme.threeDspin 
    self.killfx = self.engine.config.get("performance", "killfx")
    self.killCount         = 0
    self.ocount = 0
    self.noterotate = self.engine.config.get("coffee", "noterotate")
    self.isFailing = False
    self.failcount = 0
    self.failcount2 = False
    self.spcount = 0
    self.spcount2 = 0
    
    #MFH- fixing neck speed
    if self.nstype < 3:   #not constant mode: 
      self.speed = self.engine.config.get("coffee", "neckSpeed")*0.01
    else:   #constant mode
      self.speed = 410 - self.engine.config.get("coffee", "neckSpeed")    #invert this value

  
    #death_au: fixed neck size
    if self.twoDnote == False or self.twoDkeys == False:
      self.boardWidth     = 3.6
      self.boardLength    = 9.0  

    self.bigMax = 1
    
    if player == 0:
      self.keys = PLAYER1KEYS
      self.actions = PLAYER1ACTIONS
    else:
      self.keys = PLAYER2KEYS
      self.actions = PLAYER2ACTIONS

    
    self.setBPM(self.currentBpm)

    if self.starpowerMode == 1:
      self.starNotesSet = False
    else:
      self.starNotesSet = True

    self.maxStars = []
    self.starNotes = []
    self.totalNotes = 0


    engine.loadImgDrawing(self, "glowDrawing", "glow.png")

    # evilynux - Fixed random neck -- MFH: further fixing random neck
    if self.neck == "0" or self.neck == "Neck_0" or self.neck == "randomneck":
      self.max = self.engine.config.get("coffee", "max_neck")
      self.neck = []
      # evilynux - improved loading logic to support arbitrary filenames
      for i in os.listdir(self.engine.resource.fileName("necks")):
        # evilynux - Special cases, ignore these...
        if( str(i) == "overdriveneck.png" or str(i) == "randomneck.png"  or str(i) == "Neck_0.png" or str(i)[-4:] != ".png" ):
          continue
        else:
          self.neck.append(str(i)[:-4]) # evilynux - filename w/o extension
      i = random.randint(1,self.max)
      engine.loadImgDrawing(self, "neckDrawing", os.path.join("necks",self.neck[i]+".png"),  textureSize = (256, 256))
      Log.debug("Random neck chosen: " + self.neck[i])
    else:
      try:
        # evilynux - first assume the self.neck contains the full filename
        engine.loadImgDrawing(self, "neckDrawing", os.path.join("necks",self.neck+".png"),  textureSize = (256, 256))
      except IOError:
        engine.loadImgDrawing(self, "neckDrawing", os.path.join("necks","Neck_"+self.neck+".png"),  textureSize = (256, 256))





    engine.loadImgDrawing(self, "hitflames1Drawing", os.path.join("themes",themename,"hitflames1.png"),  textureSize = (128, 128))
    engine.loadImgDrawing(self, "hitflames2Drawing", os.path.join("themes",themename,"hitflames2.png"),  textureSize = (128, 128))

    try:
      engine.loadImgDrawing(self, "hitglowAnim", os.path.join("themes",themename,"hitglowanimation.png"),  textureSize = (128, 128))
    except IOError:
      engine.loadImgDrawing(self, "hitglowDrawing", os.path.join("themes",themename,"hitglow.png"),  textureSize = (128, 128))
      engine.loadImgDrawing(self, "hitglow2Drawing", os.path.join("themes",themename,"hitglow2.png"),  textureSize = (128, 128))
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
        engine.loadImgDrawing(self, "noteButtons", os.path.join("themes",themename,"notes.png"))
        #mfh - adding fallback for beta option
    else:
      #MFH - can't use IOError for fallback logic for a Mesh() call... 
      if self.engine.fileExists(os.path.join("themes", themename, "note.dae")):
        engine.resource.load(self,  "noteMesh",  lambda: Mesh(engine.resource.fileName("themes", themename, "note.dae")))
      else:
        engine.resource.load(self,  "noteMesh",  lambda: Mesh(engine.resource.fileName("note.dae")))
      if self.engine.fileExists(os.path.join("themes", themename, "star.dae")):  
        engine.resource.load(self,  "starMesh",  lambda: Mesh(engine.resource.fileName("themes", themename, "star.dae")))
      else:  
        self.starMesh = None






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
        if self.engine.fileExists(os.path.join("themes", themename, "key_hold.dae")) and self.engine.fileExists(os.path.join("themes", themename, "key_hit.dae")) :
          engine.resource.load(self,  "keyMesh2",  lambda: Mesh(engine.resource.fileName("themes", themename, "key_hold.dae")))
          engine.resource.load(self,  "keyMesh3",  lambda: Mesh(engine.resource.fileName("themes", themename, "key_hit.dae")))
          self.complexkey = True
        else:
          self.complexkey = False
      else:
        engine.resource.load(self,  "keyMesh",  lambda: Mesh(engine.resource.fileName("key.dae")))

    


    if self.theme == 2:
      if self.rbnote == 1:
        #mfh - adding fallback for beta option
        try:
          engine.loadImgDrawing(self, "oSideBars", os.path.join("themes",themename,"overdrive side_barsbeta.png"),  textureSize = (256, 256))
          engine.loadImgDrawing(self, "oCenterLines", os.path.join("themes",themename,"overdrive center_linesbeta.png"),  textureSize = (256, 256))
          engine.loadImgDrawing(self, "oNeck", os.path.join("themes",themename,"overdriveneckbeta.png"),  textureSize = (256, 256))
        except IOError:
          try:
            engine.loadImgDrawing(self, "oSideBars", os.path.join("themes",themename,"overdrive side_bars.png"),  textureSize = (256, 256))
          except IOError:
            self.oSideBars = None
          try:
            engine.loadImgDrawing(self, "oCenterLines", os.path.join("themes",themename,"overdrive center_lines.png"),  textureSize = (256, 256))
          except IOError:
            self.oCenterLines = None
          try:
            engine.loadImgDrawing(self, "oNeck", os.path.join("themes",themename,"overdriveneck.png"),  textureSize = (256, 256))
          except IOError:
            self.oNeck = None
          self.rbnote = 0
      else:
        try:
          engine.loadImgDrawing(self, "oSideBars", os.path.join("themes",themename,"overdrive side_bars.png"),  textureSize = (256, 256))
        except IOError:
          self.oSideBars = None
        try:
          engine.loadImgDrawing(self, "oCenterLines", os.path.join("themes",themename,"overdrive center_lines.png"),  textureSize = (256, 256))
        except IOError:
          self.oCenterLines = None
        try:
          engine.loadImgDrawing(self, "oNeck", os.path.join("themes",themename,"overdriveneck.png"),  textureSize = (256, 256))
        except IOError:
          self.oNeck = None

      #MFH: support for optional overdrive_string_flash.png
      self.overdriveFlashCounts = self.indexFps/4   #how many cycles to display the oFlash: self.indexFps/2 = 1/2 second
      self.overdriveFlashCount = self.overdriveFlashCounts
      try:
        engine.loadImgDrawing(self, "oFlash", os.path.join("themes",themename,"overdrive_string_flash.png"),  textureSize = (256, 256))
      except IOError:
        self.oFlash = None


    engine.loadImgDrawing(self, "centerLines", os.path.join("themes",themename,"center_lines.png"))
    engine.loadImgDrawing(self, "sideBars", os.path.join("themes",themename,"side_bars.png"))
    engine.loadImgDrawing(self, "bpm_halfbeat", os.path.join("themes",themename,"bpm_halfbeat.png"))
    engine.loadImgDrawing(self, "bpm_beat", os.path.join("themes",themename,"bpm_beat.png"))
    engine.loadImgDrawing(self, "bpm_measure", os.path.join("themes",themename,"bpm_measure.png"))

    if self.theme == 0 or self.theme == 1:
      engine.loadImgDrawing(self, "hitlightning", os.path.join("themes",themename,"lightning.png"),  textureSize = (128, 128))

      #myfingershurt: the starpower neck file should be in the theme folder... and also not required:
      try:
        engine.loadImgDrawing(self, "oNeck", os.path.join("themes",themename,"starpowerneck.png"),  textureSize = (256, 256))
      except IOError:
        self.oNeck = None

    #myfingershurt: Bass Groove neck:
    if self.bassGrooveNeckMode > 0:
      if self.bassGrooveNeckMode == 1:  #replace neck
        try:
          engine.loadImgDrawing(self, "bassGrooveNeck", os.path.join("themes",themename,"bassgrooveneck.png"),  textureSize = (256, 256))
        except IOError:
          self.bassGrooveNeck = None
      elif self.bassGrooveNeckMode == 2:  #overlay neck
        try:
          engine.loadImgDrawing(self, "bassGrooveNeck", os.path.join("themes",themename,"bassgrooveneckovr.png"),  textureSize = (256, 256))
        except IOError:
          self.bassGrooveNeck = None
    else:
      self.bassGrooveNeck = None



    #myfingershurt: Guitar Solo neck:
    if self.guitarSoloNeckMode > 0:
      if self.guitarSoloNeckMode == 1:  #replace neck
        try:
          engine.loadImgDrawing(self, "guitarSoloNeck", os.path.join("themes",themename,"guitarsoloneck.png"),  textureSize = (256, 256))
        except IOError:
          self.guitarSoloNeck = None
      elif self.guitarSoloNeckMode == 2:  #overlay neck
        try:
          engine.loadImgDrawing(self, "guitarSoloNeck", os.path.join("themes",themename,"guitarsoloneckovr.png"),  textureSize = (256, 256))
        except IOError:
          self.guitarSoloNeck = None
    else:
      self.guitarSoloNeck = None

    try:
      engine.loadImgDrawing(self, "failNeck", os.path.join("themes",themename,"failneck.png"))
    except IOError:
      engine.loadImgDrawing(self, "failNeck", os.path.join("failneck.png"))
                                                           
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
    
    
    self.twoChordMax = self.engine.config.get("player%d" % (player), "two_chord_max")
    self.disableVBPM  = self.engine.config.get("game", "disable_vbpm")
    self.disableNoteSFX  = self.engine.config.get("video", "disable_notesfx")
    self.disableFretSFX  = self.engine.config.get("video", "disable_fretsfx")
    self.disableFlameSFX  = self.engine.config.get("video", "disable_flamesfx")
  
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
    if self.actualBpm != bpm:
      self.actualBpm = bpm
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
  
      # Alarian: Hitwindows/-margins
      self.earlyMargin       = 250 - bpm/5 - 70*self.hitw
      self.lateMargin        = 250 - bpm/5 - 70*self.hitw

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

  def renderIncomingNeck(self, visibility, song, pos, time, neckTexture):   #MFH - attempt to "scroll" an incoming guitar solo neck towards the player
    if not song:
      return
    
    def project(beat):
      return 0.125 * beat / beatsPerUnit    # glorandwarf: was 0.12

    v            = visibility
    w            = self.boardWidth
    l            = self.boardLength

    beatsPerUnit = self.beatsPerBoard / self.boardLength

    #offset       = (pos - self.lastBpmChange) / self.currentPeriod + self.baseBeat 
    offset = 0

    z  = ((time - pos) / self.currentPeriod) / beatsPerUnit

    color = (1,1,1)

    glEnable(GL_TEXTURE_2D)
    if neckTexture:
      neckTexture.texture.bind()


    glBegin(GL_TRIANGLE_STRIP)
    glColor4f(color[0],color[1],color[2], 0)
    glTexCoord2f(0.0, project(offset - 2 * beatsPerUnit))
    #glVertex3f(-w / 2, 0, -2)
    glVertex3f(-w / 2, 0, z)   #point A
    glTexCoord2f(1.0, project(offset - 2 * beatsPerUnit))
    #glVertex3f( w / 2, 0, -2)
    glVertex3f( w / 2, 0, z)   #point B

    
    glColor4f(color[0],color[1],color[2], v)
    glTexCoord2f(0.0, project(offset - 1 * beatsPerUnit))
    #glVertex3f(-w / 2, 0, -1)
    glVertex3f(-w / 2, 0, z+1)   #point C
    glTexCoord2f(1.0, project(offset - 1 * beatsPerUnit))
    #glVertex3f( w / 2, 0, -1)
    glVertex3f( w / 2, 0, z+1)   #point D
    
    glTexCoord2f(0.0, project(offset + l * beatsPerUnit * .7))
    #glVertex3f(-w / 2, 0, l * .7)
    glVertex3f(-w / 2, 0, z+2+l * .7) #point E
    glTexCoord2f(1.0, project(offset + l * beatsPerUnit * .7))
    #glVertex3f( w / 2, 0, l * .7)
    glVertex3f( w / 2, 0, z+2+l * .7) #point F
    
    glColor4f(color[0],color[1],color[2], 0)
    glTexCoord2f(0.0, project(offset + l * beatsPerUnit))
    #glVertex3f(-w / 2, 0, l)
    glVertex3f(-w / 2, 0, z+2+l)    #point G
    glTexCoord2f(1.0, project(offset + l * beatsPerUnit))
    #glVertex3f( w / 2, 0, l)
    glVertex3f( w / 2, 0, z+2+l)    #point H
    glEnd()
    
    glDisable(GL_TEXTURE_2D)

    
  def renderNeck(self, visibility, song, pos):
    if not song:
      return
    
    def project(beat):
      return 0.125 * beat / beatsPerUnit    # glorandwarf: was 0.12

    v            = visibility
    w            = self.boardWidth
    l            = self.boardLength

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    offset       = (pos - self.lastBpmChange) / self.currentPeriod + self.baseBeat 

    if self.starPowerActive and self.theme == 0:#8bit
      color = (.3,.7,.9)
    elif self.starPowerActive and self.theme == 1:
      color = (.3,.7,.9)
    else:
      color = (1,1,1)   

    glEnable(GL_TEXTURE_2D)
    #myfingershurt: every theme can have oNeck:
    if self.starPowerActive and self.oNeck and self.spcount == 1.2:
      self.oNeck.texture.bind()
    elif self.guitarSolo and self.guitarSoloNeck != None and self.guitarSoloNeckMode == 1:
      self.guitarSoloNeck.texture.bind()
    elif self.scoreMultiplier > 4 and self.bassGrooveNeck != None and self.bassGrooveNeckMode == 1:
      self.bassGrooveNeck.texture.bind()
    else:
      self.neckDrawing.texture.bind()

    glBegin(GL_TRIANGLE_STRIP)
    glColor4f(color[0],color[1],color[2], 0)
    glTexCoord2f(0.0, project(offset - 2 * beatsPerUnit))
    glVertex3f(-w / 2, 0, -2)
    glTexCoord2f(1.0, project(offset - 2 * beatsPerUnit))
    glVertex3f( w / 2, 0, -2)
    
    glColor4f(color[0],color[1],color[2], v)
    glTexCoord2f(0.0, project(offset - 1 * beatsPerUnit))
    glVertex3f(-w / 2, 0, -1)
    glTexCoord2f(1.0, project(offset - 1 * beatsPerUnit))
    glVertex3f( w / 2, 0, -1)
    
    glTexCoord2f(0.0, project(offset + l * beatsPerUnit * .7))
    glVertex3f(-w / 2, 0, l * .7)
    glTexCoord2f(1.0, project(offset + l * beatsPerUnit * .7))
    glVertex3f( w / 2, 0, l * .7)
    
    glColor4f(color[0],color[1],color[2], 0)
    glTexCoord2f(0.0, project(offset + l * beatsPerUnit))
    glVertex3f(-w / 2, 0, l)
    glTexCoord2f(1.0, project(offset + l * beatsPerUnit))
    glVertex3f( w / 2, 0, l)
    glEnd()

    if self.scoreMultiplier > 4 and self.bassGrooveNeck != None and self.bassGrooveNeckMode == 2:   #static bass groove overlay
      self.bassGrooveNeck.texture.bind()
     
      glBegin(GL_TRIANGLE_STRIP)
      glColor4f(color[0],color[1],color[2], 0)
      glTexCoord2f(0.0, project(-2 * beatsPerUnit))
      glVertex3f(-w / 2, 0, -2)
      glTexCoord2f(1.0, project(-2 * beatsPerUnit))
      glVertex3f( w / 2, 0, -2)
      
      glColor4f(color[0],color[1],color[2], v)
      glTexCoord2f(0.0, project(-1 * beatsPerUnit))
      glVertex3f(-w / 2, 0, -1)
      glTexCoord2f(1.0, project(-1 * beatsPerUnit))
      glVertex3f( w / 2, 0, -1)
      
      glTexCoord2f(0.0, 0)
      glVertex3f(-w / 2, 0, 0)
      glTexCoord2f(1.0, 0)
      glVertex3f( w / 2, 0, 0)
      
      glColor4f(color[0],color[1],color[2], 0)
      glTexCoord2f(0.0, project(l * beatsPerUnit))
      glVertex3f(-w / 2, 0, l)
      glTexCoord2f(1.0, project(l * beatsPerUnit))
      glVertex3f( w / 2, 0, l)
      glEnd()

    elif self.guitarSolo and self.guitarSoloNeck != None and self.guitarSoloNeckMode == 2:   #static overlay
      self.guitarSoloNeck.texture.bind()

      glBegin(GL_TRIANGLE_STRIP)
      glColor4f(color[0],color[1],color[2], 0)
      glTexCoord2f(0.0, project(-2 * beatsPerUnit))
      glVertex3f(-w / 2, 0, -2)
      glTexCoord2f(1.0, project(-2 * beatsPerUnit))
      glVertex3f( w / 2, 0, -2)
      
      glColor4f(color[0],color[1],color[2], v)
      glTexCoord2f(0.0, project(-1 * beatsPerUnit))
      glVertex3f(-w / 2, 0, -1)
      glTexCoord2f(1.0, project(-1 * beatsPerUnit))
      glVertex3f( w / 2, 0, -1)
      
      glTexCoord2f(0.0, 0)
      glVertex3f(-w / 2, 0, 0)
      glTexCoord2f(1.0, 0)
      glVertex3f( w / 2, 0, 0)
      
      glColor4f(color[0],color[1],color[2], 0)
      glTexCoord2f(0.0, project(l * beatsPerUnit))
      glVertex3f(-w / 2, 0, l)
      glTexCoord2f(1.0, project(l * beatsPerUnit))
      glVertex3f( w / 2, 0, l)
      glEnd()


    if self.spcount2 != 0 and self.spcount < 1.2:   #static overlay
      self.oNeck.texture.bind()
      
      glBegin(GL_TRIANGLE_STRIP)
      glColor4f(color[0],color[1],color[2], 0)
      glTexCoord2f(0.0, project(offset - 2 * beatsPerUnit))
      glVertex3f(-w / 2, 0, -2)
      glTexCoord2f(1.0, project(offset - 2 * beatsPerUnit))
      glVertex3f( w / 2, 0, -2)
      
      glColor4f(color[0],color[1],color[2], self.spcount)
      glTexCoord2f(0.0, project(offset - 1 * beatsPerUnit))
      glVertex3f(-w / 2, 0, -1)
      glTexCoord2f(1.0, project(offset - 1 * beatsPerUnit))
      glVertex3f( w / 2, 0, -1)
      
      glTexCoord2f(0.0, project(offset + l * beatsPerUnit * .7))
      glVertex3f(-w / 2, 0, l * .7)
      glTexCoord2f(1.0, project(offset + l * beatsPerUnit * .7))
      glVertex3f( w / 2, 0, l * .7)
      
      glColor4f(color[0],color[1],color[2], 0)
      glTexCoord2f(0.0, project(offset + l * beatsPerUnit))
      glVertex3f(-w / 2, 0, l)
      glTexCoord2f(1.0, project(offset + l * beatsPerUnit))
      glVertex3f( w / 2, 0, l)
      glEnd()

    if self.isFailing:   #static overlay
      self.failNeck.texture.bind()
      
      color = (1,1,1) 
      glBegin(GL_TRIANGLE_STRIP)
      glColor4f(color[0],color[1],color[2], 0)
      glTexCoord2f(0.0, project(-2 * beatsPerUnit))
      glVertex3f(-w / 2, 0, -2)
      glTexCoord2f(1.0, project(-2 * beatsPerUnit))
      glVertex3f( w / 2, 0, -2)
      
      glColor4f(color[0],color[1],color[2], self.failcount)
      glTexCoord2f(0.0, project(-1 * beatsPerUnit))
      glVertex3f(-w / 2, 0, -1)
      glTexCoord2f(1.0, project(-1 * beatsPerUnit))
      glVertex3f( w / 2, 0, -1)
      
      glTexCoord2f(0.0, 0)
      glVertex3f(-w / 2, 0, 0)
      glTexCoord2f(1.0, 0)
      glVertex3f( w / 2, 0, 0)
      
      glColor4f(color[0],color[1],color[2], 0)
      glTexCoord2f(0.0, project(l * beatsPerUnit))
      glVertex3f(-w / 2, 0, l)
      glTexCoord2f(1.0, project(l * beatsPerUnit))
      glVertex3f( w / 2, 0, l)
      glEnd()
      
    glDisable(GL_TEXTURE_2D)

  def drawTrack(self, visibility, song, pos):
    if not song:
      return

    def project(beat):
      return 0.125 * beat / beatsPerUnit    # glorandwarf: was 0.12

    if self.theme == 0 or self.theme == 1:
      size = 2
    else:
      size = 0

    v            = visibility
    w            = self.boardWidth
    l            = self.boardLength

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    offset       = (pos - self.lastBpmChange) / self.currentPeriod + self.baseBeat 

    glEnable(GL_TEXTURE_2D)
    
    #MFH - logic to briefly display oFlash
    if self.theme == 2 and self.overdriveFlashCount < self.overdriveFlashCounts and self.oFlash:
      self.overdriveFlashCount = self.overdriveFlashCount + 1
      self.oFlash.texture.bind()
    elif self.theme == 2 and self.starPowerActive and self.oCenterLines:
      self.oCenterLines.texture.bind()
    else:
      self.centerLines.texture.bind()

    if self.staticStrings:    #MFH
    
      glBegin(GL_TRIANGLE_STRIP)
      glColor4f(1, 1, 1, v)
      glTexCoord2f(0.0, project(-2 * beatsPerUnit))
      glVertex3f(-w / 2, 0, -2+size)
      glTexCoord2f(1.0, project(-2 * beatsPerUnit))
      glVertex3f( w / 2, 0, -2+size)
      
      glColor4f(1, 1, 1, v)
      glTexCoord2f(0.0, project(-1 * beatsPerUnit))
      glVertex3f(-w / 2, 0, -1+size)
      glTexCoord2f(1.0, project(-1 * beatsPerUnit))
      glVertex3f( w / 2, 0, -1+size)
      
      glTexCoord2f(0.0, project(l * beatsPerUnit * .7))
      glVertex3f(-w / 2, 0, l * .7)
      glTexCoord2f(1.0, project(1 * beatsPerUnit * .7))
      glVertex3f( w / 2, 0, l * .7)
      
      glColor4f(1, 1, 1, 0)
      glTexCoord2f(0.0, project(l * beatsPerUnit))
      glVertex3f(-w / 2, 0, l)
      glTexCoord2f(1.0, project(1 * beatsPerUnit))
      glVertex3f( w / 2, 0, l)

    else:   #MFH: original moving strings

      glBegin(GL_TRIANGLE_STRIP)
      glColor4f(1, 1, 1, v)
      glTexCoord2f(0.0, project(offset - 2 * beatsPerUnit))
      glVertex3f(-w / 2, 0, -2+size)
      glTexCoord2f(1.0, project(offset - 2 * beatsPerUnit))
      glVertex3f( w / 2, 0, -2+size)
      
      glColor4f(1, 1, 1, v)
      glTexCoord2f(0.0, project(offset - 1 * beatsPerUnit))
      glVertex3f(-w / 2, 0, -1+size)
      glTexCoord2f(1.0, project(offset - 1 * beatsPerUnit))
      glVertex3f( w / 2, 0, -1+size)
      
      glTexCoord2f(0.0, project(offset + l * beatsPerUnit * .7))
      glVertex3f(-w / 2, 0, l * .7)
      glTexCoord2f(1.0, project(offset + l * beatsPerUnit * .7))
      glVertex3f( w / 2, 0, l * .7)
      
      glColor4f(1, 1, 1, 0)
      glTexCoord2f(0.0, project(offset + l * beatsPerUnit))
      glVertex3f(-w / 2, 0, l)
      glTexCoord2f(1.0, project(offset + l * beatsPerUnit))
      glVertex3f( w / 2, 0, l)

    glEnd()

    glDisable(GL_TEXTURE_2D)

  def drawSideBars(self, visibility, song, pos):
    if not song:
      return

    def project(beat):
      return 0.125 * beat / beatsPerUnit  # glorandwarf: was 0.12

    v            = visibility
    w            = self.boardWidth + 0.15
    l            = self.boardLength

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    offset       = (pos - self.lastBpmChange) / self.currentPeriod + self.baseBeat 

    c = (1,1,1)

    glEnable(GL_TEXTURE_2D)
    if self.theme == 2 and self.starPowerActive and self.oSideBars:
      self.oSideBars.texture.bind()
    else:
      self.sideBars.texture.bind()
    
    glBegin(GL_TRIANGLE_STRIP)
    glColor4f(c[0], c[1], c[2], 0)
    glTexCoord2f(0.0, project(offset - 2 * beatsPerUnit))
    glVertex3f(-w / 2, 0, -2)
    glTexCoord2f(1.0, project(offset - 2 * beatsPerUnit))
    glVertex3f( w / 2, 0, -2)
    
    glColor4f(c[0], c[1], c[2], v)
    glTexCoord2f(0.0, project(offset - 1 * beatsPerUnit))
    glVertex3f(-w / 2, 0, -1)
    glTexCoord2f(1.0, project(offset - 1 * beatsPerUnit))
    glVertex3f( w / 2, 0, -1)
    
    glTexCoord2f(0.0, project(offset + l * beatsPerUnit * .7))
    glVertex3f(-w / 2, 0, l * .7)
    glTexCoord2f(1.0, project(offset + l * beatsPerUnit * .7))
    glVertex3f( w / 2, 0, l * .7)
    
    glColor4f(c[0], c[1], c[2], 0)
    glTexCoord2f(0.0, project(offset + l * beatsPerUnit))
    glVertex3f(-w / 2, 0, l)
    glTexCoord2f(1.0, project(offset + l * beatsPerUnit))
    glVertex3f( w / 2, 0, l)
    glEnd()

    glDisable(GL_TEXTURE_2D)

  def drawBPM(self, visibility, song, pos):
    if not song:
      return

    v            = visibility
    w            = self.boardWidth

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    track = song.track[self.player]

    glEnable(GL_TEXTURE_2D)

    for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard):
      if not isinstance(event, Bars):
        continue   

      glPushMatrix()

      z  = ((time - pos) / self.currentPeriod) / beatsPerUnit
      z2 = ((time + event.length - pos) / self.currentPeriod) / beatsPerUnit

      if z > self.boardLength:
        f = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        f = min(1, max(0, 1 + z2))
      else:
        f = 1.0
        
      if event.barType == 0: #half-beat
        sw  = 0.1 #width
        self.bpm_halfbeat.texture.bind()
      elif event.barType == 1: #beat
        sw  = 0.1 #width
        self.bpm_beat.texture.bind()
      elif event.barType == 2: #measure
        sw  = 0.1 #width
        self.bpm_measure.texture.bind()

      glColor4f(1, 1, 1, v)
      glBegin(GL_TRIANGLE_STRIP)
      glTexCoord2f(0.0, 1.0)
      glVertex3f(-(w / 2), 0, z + sw)
      glTexCoord2f(0.0, 0.0)
      glVertex3f(-(w / 2), 0, z - sw)
      glTexCoord2f(1.0, 1.0)
      glVertex3f(w / 2,    0, z + sw)
      glTexCoord2f(1.0, 0.0)
      glVertex3f(w / 2,    0, z - sw)
      glEnd()
      glPopMatrix()

    glDisable(GL_TEXTURE_2D)
    
  def renderTracks(self, visibility):
    if self.tracksColor[0] == -1:
      return
    w = self.boardWidth / self.strings
    v = 1.0 - visibility

    if self.editorMode:
      x = (self.strings / 2 - self.selectedString) * w
      s = 2 * w / self.strings
      z1 = -0.5 * visibility ** 2
      z2 = (self.boardLength - 0.5) * visibility ** 2
      
      glColor4f(1, 1, 1, .15)
      
      glBegin(GL_TRIANGLE_STRIP)
      glVertex3f(x - s, 0, z1)
      glVertex3f(x + s, 0, z1)
      glVertex3f(x - s, 0, z2)
      glVertex3f(x + s, 0, z2)
      glEnd()

    sw = 0.025
    for n in range(self.strings - 1, -1, -1):
      glBegin(GL_TRIANGLE_STRIP)
      glColor4f(self.tracksColor[0], self.tracksColor[1], self.tracksColor[2], 0)
      glVertex3f((n - self.strings / 2) * w - sw, -v, -2)
      glVertex3f((n - self.strings / 2) * w + sw, -v, -2)
      glColor4f(self.tracksColor[0], self.tracksColor[1], self.tracksColor[2], (1.0 - v) * .75)
      glVertex3f((n - self.strings / 2) * w - sw, -v, -1)
      glVertex3f((n - self.strings / 2) * w + sw, -v, -1)
      glColor4f(self.tracksColor[0], self.tracksColor[1], self.tracksColor[2], (1.0 - v) * .75)
      glVertex3f((n - self.strings / 2) * w - sw, -v, self.boardLength * .7)
      glVertex3f((n - self.strings / 2) * w + sw, -v, self.boardLength * .7)
      glColor4f(self.tracksColor[0], self.tracksColor[1], self.tracksColor[2], 0)
      glVertex3f((n - self.strings / 2) * w - sw, -v, self.boardLength)
      glVertex3f((n - self.strings / 2) * w + sw, -v, self.boardLength)
      glEnd()
      v *= 2
      
  def renderBars(self, visibility, song, pos):
    if not song or self.tracksColor[0] == -1:
      return
    
    w            = self.boardWidth
    v            = 1.0 - visibility
    sw           = 0.02
    beatsPerUnit = self.beatsPerBoard / self.boardLength
    pos         -= self.lastBpmChange
    offset       = pos / self.currentPeriod * beatsPerUnit
    currentBeat  = pos / self.currentPeriod
    beat         = int(currentBeat)

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    glPushMatrix()
    while beat < currentBeat + self.beatsPerBoard:
      z = (beat - currentBeat) / beatsPerUnit

      if z > self.boardLength * .8:
        c = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        c = max(0, 1 + z)
      else:
        c = 1.0
        
      glRotate(v * 90, 0, 0, 1)

      if (beat % 1.0) < 0.001:
        glColor4f(self.barsColor[0], self.barsColor[1], self.barsColor[2], visibility * c * .75)
      else:
        glColor4f(self.barsColor[0], self.barsColor[1], self.barsColor[2], visibility * c * .5)

      glBegin(GL_TRIANGLE_STRIP)
      glVertex3f(-(w / 2), -v, z + sw)
      glVertex3f(-(w / 2), -v, z - sw)
      glVertex3f(w / 2,    -v, z + sw)
      glVertex3f(w / 2,    -v, z - sw)
      glEnd()
      
      if self.editorMode:
        beat += 1.0 / 4.0
      else:
        beat += 1
    glPopMatrix()

    Theme.setSelectedColor(visibility * .5)
    glBegin(GL_TRIANGLE_STRIP)
    glVertex3f(-w / 2, 0,  sw)
    glVertex3f(-w / 2, 0, -sw)
    glVertex3f(w / 2,  0,  sw)
    glVertex3f(w / 2,  0, -sw)
    glEnd()

  def renderTail(self, length, sustain, kill, color, flat = False, tailOnly = False, isTappable = False, big = False, fret = 0, spNote = False):

    if not self.simpleTails:#Tail Colors
      glColor4f(1,1,1,1)
    else:
      if big == False and tailOnly == True:
        glColor4f(.2 + .4, .2 + .4, .2 + .4, 1)
      else:
        glColor4f(*color)
        if self.starPowerActive and self.theme != 2 and not color == (0,0,0,1):#8bit
          glColor4f(.3,.7,.9,1)

    if flat:
      glScalef(1, .1, 1)

    beatsPerUnit = self.beatsPerBoard / self.boardLength

    if sustain:
      if not length == None:
        size = (.08, length + 0.00001)

        if size[1] > self.boardLength:
          s = self.boardLength
        else:
          s = (length + 0.00001)

        #myfingershurt: so any theme containing appropriate files can use new tails
        if not self.simpleTails:
            
          if big == True and tailOnly == True:
            if kill and self.killfx == 0:
              zsize = .25
              size = (.15, s - zsize)
              tex1 = self.kill1
              tex2 = self.kill2
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
            if kill and self.killfx == 0:
              zsize = .25
              size = (.15, s - zsize)
              tex1 = self.kill1
              tex2 = self.kill2
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
        
        glEnable(GL_TEXTURE_2D)
        tex1.texture.bind()


        glBegin(GL_TRIANGLE_STRIP)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-size[0], 0, 0)
        glTexCoord2f(1.0, 0.0)
        glVertex3f( size[0], 0, 0)
        glTexCoord2f(0.0,1.0)
        glVertex3f(-size[0], 0, size[1])
        glTexCoord2f(1.0,1.0)
        glVertex3f( size[0], 0, size[1])

        glEnd()

        glDisable(GL_TEXTURE_2D)

        glEnable(GL_TEXTURE_2D)
        tex2.texture.bind()

        glBegin(GL_TRIANGLE_STRIP)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-size[0], 0, size[1] - (.01))
        glTexCoord2f(1.0, 0.0)
        glVertex3f( size[0], 0, size[1] - (.01))
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-size[0], 0, size[1] + (zsize))
        glTexCoord2f(1.0, 1.0)
        glVertex3f( size[0], 0, size[1] + (zsize))
        glEnd()

        glDisable(GL_TEXTURE_2D)

    if tailOnly:
      return

  def renderNote(self, length, sustain, kill, color, flat = False, tailOnly = False, isTappable = False, big = False, fret = 0, spNote = False):

    if flat:
      glScalef(1, .1, 1)

    beatsPerUnit = self.beatsPerBoard / self.boardLength


    if tailOnly:
      return


    if self.twoDnote == True:
      #myfingershurt: this should be retrieved once at init, not repeatedly in-game whenever tails are rendered.
      glPushMatrix()
      if self.notedisappear == True:#Notes keep on going when missed
        glColor4f(1,1,1,1)#capo
        glScalef(1, 1, 1)#capo
      else:
        if flat:#Notes disappear when missed
          glColor4f(.1,.1,.1,1)
        else:
          glColor4f(1,1,1,1)
      tailOnly == True
      
      if self.theme < 2:
        if self.starspin:
          size = (self.boardWidth/self.strings/2, self.boardWidth/self.strings/2)
          texSize = (fret/5.0,fret/5.0+0.2)
          if spNote == True:
            if isTappable:
              texY = (0.9-self.starSpinFrameIndex*0.05, 0.925-self.starSpinFrameIndex*0.05)
            else:
              texY = (0.875-self.starSpinFrameIndex*0.05, 0.9-self.starSpinFrameIndex*0.05)
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
          
      glEnable(GL_TEXTURE_2D)
      self.noteButtons.texture.bind()


      glBegin(GL_TRIANGLE_STRIP)

      glTexCoord2f(texSize[0],texY[0])
      glVertex3f(-size[0], 0.2, size[1])
      glTexCoord2f(texSize[1],texY[0])
      glVertex3f( size[0], 0.2, size[1])
      glTexCoord2f(texSize[0],texY[1])
      glVertex3f(-size[0], -0.2, -size[1])
      glTexCoord2f(texSize[1],texY[1])
      glVertex3f( size[0], -0.2, -size[1])

      glEnd()

      glDisable(GL_TEXTURE_2D)

      glPopMatrix()

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
      glColor4f(*color)
      if self.starPowerActive and self.theme != 2 and not color == (0,0,0,1):
        glColor4f(.3,.7,.9, 1)

      note.render("Mesh_001")
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

  def renderIncomingNecks(self, visibility, song, pos):
    if not song:
      return

    if self.incomingNeckMode > 0:   #if enabled
      boardWindowMin = pos - self.currentPeriod * 2
      boardWindowMax = pos + self.currentPeriod * self.beatsPerBoard


      #if self.song.hasStarpowerPaths and self.song.midiStyle == Song.MIDI_TYPE_RB:  
      if self.useMidiSoloMarkers:
        track = song.midiEventTrack[self.player]
        for time, event in track.getEvents(boardWindowMin, boardWindowMax):
          if isinstance(event, Song.MarkerNote):
            if event.number == Song.starPowerMarkingNote:
              if self.guitarSoloNeck:
                if event.endMarker:   #solo end
                  if self.incomingNeckMode == 2:    #render both start and end incoming necks
                    if self.guitarSolo:   #only until the end of the guitar solo!
                      if self.starPowerActive and self.oNeck:
                        neckImg = self.oNeck
                      elif self.scoreMultiplier > 4 and self.bassGrooveNeck != None and self.bassGrooveNeckMode == 1:
                        neckImg = self.bassGrooveNeck
                      else:
                        neckImg = self.neckDrawing
                      self.renderIncomingNeck(visibility, song, pos, time, neckImg)
                else:   #solo start
                  if not self.guitarSolo:   #only until guitar solo starts!
                    neckImg = self.guitarSoloNeck
                    self.renderIncomingNeck(visibility, song, pos, time, neckImg)
              

      else:   #fall back on text-based guitar solo marking track
        for time, event in song.eventTracks[Song.TK_GUITAR_SOLOS].getEvents(boardWindowMin, boardWindowMax):
          if self.canGuitarSolo and self.guitarSoloNeck:
            if event.text.find("ON") >= 0:
              if not self.guitarSolo:   #only until guitar solo starts!
                neckImg = self.guitarSoloNeck
                self.renderIncomingNeck(visibility, song, pos, time, neckImg)
            #else: #event.text.find("OFF"):
            elif self.incomingNeckMode == 2:    #render both start and end incoming necks
              if self.guitarSolo:   #only until the end of the guitar solo!
                if self.starPowerActive and self.oNeck:
                  neckImg = self.oNeck
                elif self.scoreMultiplier > 4 and self.bassGrooveNeck != None and self.bassGrooveNeckMode == 1:
                  neckImg = self.bassGrooveNeck
                else:
                  neckImg = self.neckDrawing
                self.renderIncomingNeck(visibility, song, pos, time, neckImg)
              


  def renderNotes(self, visibility, song, pos, killswitch):
    if not song:
      return

    # Update dynamic period
    self.currentPeriod = self.neckSpeed
    self.targetPeriod  = self.neckSpeed

    self.killPoints = False

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    w = self.boardWidth / self.strings
    track = song.track[self.player]

    num = 0
    enable = True
    starEventsInView = False

    for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard):
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

      #for q in self.starNotes:
      #  if time == q:
      #    event.star = True
      #    enable = False
      #for q in self.maxStars:
      #  if time == q:
      #    event.finalStar = True
      #    enable = False
      
      c = self.fretColors[event.number]

      x  = (self.strings / 2 - event.number) * w
      z  = ((time - pos) / self.currentPeriod) / beatsPerUnit
      z2 = ((time + event.length - pos) / self.currentPeriod) / beatsPerUnit


      if z > self.boardLength * .8:
        f = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        f = min(1, max(0, 1 + z2))
      else:
        f = 1.0

      color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1 * visibility * f)
      if event.length > 120:
        length     = (event.length - 50) / self.currentPeriod / beatsPerUnit
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
            if self.starPower < 100:
              self.starPower += 25
            if self.starPower > 100:
              self.starPower = 100
            self.overdriveFlashCount = 0  #MFH - this triggers the oFlash strings & timer
            self.starPowerGained = True

      #if enable:
      #  self.spEnabled = True

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

      #if event.star or event.finalStar:
      #  if big == True and tailOnly == True:
      #    self.killPoints = True

      #MFH - filter out this tail whitening when starpower notes have been disbled from a screwup
      if self.spEnabled and killswitch:
      #if not killswitch == False:
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

    # Update dynamic period
    self.currentPeriod = self.neckSpeed
    self.targetPeriod  = self.neckSpeed

    self.killPoints = False

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    w = self.boardWidth / self.strings
    track = song.track[self.player]

    num = 0
    enable = True
    for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard):
    #for time, event in reversed(track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard)):    #MFH - reverse order of note rendering
      if isinstance(event, Tempo):
        self.tempoBpm = event.bpm
        #if self.lastBpmChange > 0 and self.disableVBPM == True:
        #    continue
        #if (pos - time > self.currentPeriod or self.lastBpmChange < 0) and time > self.lastBpmChange:
        #  self.baseBeat         += (time - self.lastBpmChange) / self.currentPeriod
        #  self.targetBpm         = event.bpm
        #  self.lastBpmChange     = time
        #  self.setBPM(self.targetBpm) # glorandwarf: was setDynamicBPM(self.targetBpm)
        continue
      
      if not isinstance(event, Note):
        continue

      if (event.noteBpm == 0.0):
        event.noteBpm = self.tempoBpm

      #for q in self.starNotes:
      #  if time == q:
      #    event.star = True
      #    enable = False
      #for q in self.maxStars:
      #  if time == q:
      #    event.finalStar = True
      #    enable = False
      
      c = self.fretColors[event.number]

      x  = (self.strings / 2 - event.number) * w
      z  = ((time - pos) / self.currentPeriod) / beatsPerUnit
      z2 = ((time + event.length - pos) / self.currentPeriod) / beatsPerUnit


      if z > self.boardLength * .8:
        f = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        f = min(1, max(0, 1 + z2))
      else:
        f = 1.0

      color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1 * visibility * f)
      if event.length > 120:
        length     = (event.length - 50) / self.currentPeriod / beatsPerUnit
      else:
        length     = 0
      flat       = False
      tailOnly   = False

      spNote = False

      #myfingershurt: user setting for starpower refill / replenish notes
      #if self.starPowerActive:
      #  if self.spRefillMode == 0:    #mode 0 = no starpower / overdrive refill notes
      #    self.spEnabled = False
      #  elif self.spRefillMode == 1 and self.theme != 2:  #mode 1 = overdrive refill notes in RB themes only
      #    self.spEnabled = False


      if event.star and self.spEnabled:
        spNote = True
      if event.finalStar and self.spEnabled:
        spNote = True
        if event.played or event.hopod:
          if event.flameCount < 1 and not self.starPowerGained:
            if self.starPower < 100:
              self.starPower += 25
            if self.starPower > 100:
              self.starPower = 100
            self.overdriveFlashCount = 0  #MFH - this triggers the oFlash strings & timer
            self.starPowerGained = True
            if self.theme == 2 and self.oFlash != None:
              self.ocount = 0

      #if enable:
      #  self.spEnabled = True

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

      #if event.star or event.finalStar:
      #  if big == True and tailOnly == True:
      #    self.killPoints = True

      #if not killswitch == False:
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
      if big == True and num < self.bigMax:
        num += 1
        self.renderTail(length, sustain = sustain, kill = killswitch, color = color, flat = flat, tailOnly = tailOnly, isTappable = isTappable, big = True, fret = event.number, spNote = spNote)
      else:
        self.renderTail(length, sustain = sustain, kill = killswitch, color = color, flat = flat, tailOnly = tailOnly, isTappable = isTappable, fret = event.number, spNote = spNote)
      glPopMatrix()
  

      if killswitch and self.killfx == 1:
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        for time, event in self.playedNotes:
          step  = self.currentPeriod / 16
          t     = time + event.length
          x     = (self.strings / 2 - event.number) * w
          c     = self.fretColors[event.number]
          s     = t
          proj  = 1.0 / self.currentPeriod / beatsPerUnit
          zStep = step * proj

          def waveForm(t):
            u = ((t - time) * -.1 + pos - time) / 64.0 + .0001
            return (math.sin(event.number + self.time * -.01 + t * .03) + math.cos(event.number + self.time * .01 + t * .02)) * .1 + .1 + math.sin(u) / (5 * u)

          glBegin(GL_TRIANGLE_STRIP)
          f1 = 0
          while t > time:
            
            #z  = (t - pos) * proj    #MFH - this method rendered past the end of the board for long notes and caused massive lag
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
              glColor4f(.3,.7,.9,1)
            else:
              glColor4f(c[0], c[1], c[2], .5)
            glVertex3f(x - a1, 0, z)
            glVertex3f(x - a2, 0, z - zStep)
            glColor4f(1, 1, 1, .75)
            glVertex3f(x, 0, z)
            glVertex3f(x, 0, z - zStep)
            if self.starPowerActive and self.theme != 2:#8bit
              glColor4f(.3,.7,.9,1)
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
    #self.hitglow_color = self.engine.config.get("video", "hitglow_color")
    
    for n in range(self.strings):
      f = self.fretWeight[n]
      c = self.fretColors[n]
            
      if f and (controls.getState(self.actions[0]) or controls.getState(self.actions[1])):
        f += 0.25

      glColor4f(.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, visibility)
      y = v + f / 6
      x = (self.strings / 2 - n) * w

      if self.twoDkeys == True:
        
        glPushMatrix()
        glTranslatef(x, v, 0)
        glDepthMask(1)
        glShadeModel(GL_SMOOTH)

        glColor4f(1,1,1,1)
  
        size = (self.boardWidth/self.strings/2, self.boardWidth/self.strings/2.4)
        texSize = (n/5.0,n/5.0+0.2)

        texY = (0.0,1.0/3.0)
        if controls.getState(self.keys[n]):
          texY = (1.0/3.0,2.0/3.0)
        if self.hit[n]:
          texY = (2.0/3.0,1.0)

        glEnable(GL_TEXTURE_2D)
        self.fretButtons.texture.bind()

        glBegin(GL_TRIANGLE_STRIP)

        glTexCoord2f(texSize[0],texY[0])
        glVertex3f( size[0], 0, size[1])
        glTexCoord2f(texSize[1],texY[0])
        glVertex3f(-size[0], 0, size[1])
        glTexCoord2f(texSize[0],texY[1])
        glVertex3f( size[0], 0, -size[1])
        glTexCoord2f(texSize[1],texY[1])
        glVertex3f(-size[0], 0, -size[1])

        glEnd()

        glDisable(GL_TEXTURE_2D)

        glDepthMask(0)
        glPopMatrix()

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

          #Mesh - Main fret
          #Key_001 - Top of fret (key_color)
          #Key_002 - Bottom of fret (key2_color)
          #Glow_001 - Only rendered when a note is hit along with the glow.svg

          if self.complexkey == True:
            glColor4f(.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], visibility)
            glTranslatef(x, y, 0)
            if f and not self.hit[n]:
              key = self.keyMesh2
            elif self.hit[n]:
              key = self.keyMesh3
            else:
              key = self.keyMesh
          else:
            glColor4f(.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, visibility)
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
        glBlendFunc(GL_ONE, GL_ONE)

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
          glTranslate(x, y, 0)
          glScalef(.1 + .02 * ms * f, .1 + .02 * ms * f, .1 + .02 * ms * f)
          glRotatef( 90, 0, 1, 0)
          glRotatef(-90, 1, 0, 0)
          glRotatef(-90, 0, 0, 1)
          if self.twoDkeys == False:
            if(self.keyMesh.find("Glow_001")) == True:
              key.render("Glow_001")
            else:
              key.render()
          glPopMatrix()
          s += 0.2
        #Hitglow color
        if self.hitglow_color == 0:
          glColor3f(c[0], c[1], c[2])#Same as fret
        elif self.hitglow_color == 1:
          glColor3f(1, 1, 1)#Actual color in .svg-file
        glEnable(GL_TEXTURE_2D)
        self.glowDrawing.texture.bind()
        f += 2

        glPushMatrix()
        glTranslate(x, y, 0)
        glRotate(f * 90 + self.time, 0, 1, 0)
        glBegin(GL_TRIANGLE_STRIP)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-size[0] * f, 0, -size[1] * f)
        glTexCoord2f(1.0, 0.0)
        glVertex3f( size[0] * f, 0, -size[1] * f)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-size[0] * f, 0,  size[1] * f)
        glTexCoord2f(1.0, 1.0)
        glVertex3f( size[0] * f, 0,  size[1] * f)
        glEnd()
        glPopMatrix()
      
        glDisable(GL_TEXTURE_2D)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

      #self.hit[n] = False  #MFH -- why?  This prevents frets from being rendered under / before the notes...
    glDisable(GL_DEPTH_TEST)

  def renderFlames(self, visibility, song, pos, controls):
    if not song or self.flameColors[0][0][0] == -1:
      return

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    w = self.boardWidth / self.strings
    track = song.track[self.player]

    size = (.22, .22)
    v = 1.0 - visibility

    if self.disableFlameSFX != True:
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
          
          glBlendFunc(GL_SRC_ALPHA, GL_ONE)
          
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
          
          glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
          if self.starPowerActive:
            if self.theme == 0 or self.theme == 1: #GH3 starcolor
              glColor3f(.3,.7,.9)
            else: #Default starcolor (Rockband)
              glColor3f(.9,.9,.9)
              
          if not self.Hitanim:   
            glEnable(GL_TEXTURE_2D)
            self.hitglowDrawing.texture.bind()    
            glPushMatrix()
            glTranslate(x, y + .125, 0)
            glRotate(90, 1, 0, 0)
            glScalef(0.5 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()
            glDisable(GL_TEXTURE_2D)
            #Alarian: Animated hitflames
          else:
            self.HCount = self.HCount + 1
            if self.HCount > self.Animspeed-1:
              self.HCount = 0
            HIndex = (self.HCount * 16 - (self.HCount * 16) % self.Animspeed) / self.Animspeed
            if HIndex > 15:
              HIndex = 0
            texX = (HIndex*(1/16.0), HIndex*(1/16.0)+(1/16.0))

            glColor3f(1,1,1)
            glEnable(GL_TEXTURE_2D)
            self.hitglowAnim.texture.bind()    
            glPushMatrix()
            glTranslate(x, y + .225, 0)
            glRotate(90, 1, 0, 0)
            #glScalef(1.7, 1, 2.6)
            glScalef(2, 1, 2.9)   #worldrave correct flame size
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(texX[0], 0.0)#upper left corner of frame square in .png
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)#"upper left" corner of surface that texture is rendered on
            glTexCoord2f(texX[1], 0.0)#upper right
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(texX[0], 1.0)#lower left
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(texX[1], 1.0)#lower right
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()
            glDisable(GL_TEXTURE_2D)

          ff += .3

          flameColorMod0 = 1.1973333333333333333333333333333
          flameColorMod1 = 1.7842105263157894736842105263158
          flameColorMod2 = 12.222222222222222222222222222222
          
          glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
          if self.starPowerActive:
            if self.theme == 0 or self.theme == 1: #GH3 starcolor
              glColor3f(.3,.7,.9)
            else: #Default starcolor (Rockband)
              glColor3f(.8,.8,.8)

          if not self.Hitanim: 
            glEnable(GL_TEXTURE_2D)
            self.hitglow2Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x, y + .25, .05)
            glRotate(90, 1, 0, 0)
            glScalef(.40 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()
            glDisable(GL_TEXTURE_2D)
          
          glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

          #self.hit[n] = True   #MFH - gonna move these determinations into the runtime function, this is ridiculous

    if self.disableFlameSFX != True:
      flameLimit = 10.0
      flameLimitHalf = round(flameLimit/2.0)
      for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard):
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
          glBlendFunc(GL_ONE, GL_ONE)

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

          if event.flameCount < flameLimitHalf:
            glColor3f(flameColor[0], flameColor[1], flameColor[2])
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                glColor3f(.0,.2,.4)
              else: #Default starcolor (Rockband)
                glColor3f(.1,.1,.1)
            glEnable(GL_TEXTURE_2D)
            self.hitflames2Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x, y + .20, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.25 + .6 * ms * ff, event.flameCount/6.0 + .6 * ms * ff, event.flameCount / 6.0 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()
            glDisable(GL_TEXTURE_2D) 

            glColor3f(flameColor[0], flameColor[1], flameColor[2])
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                glColor3f(.1,.3,.5)
              else: #Default starcolor (Rockband)
                glColor3f(.1,.1,.1)
            glEnable(GL_TEXTURE_2D)
            self.hitflames2Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x - .005, y + .25 + .005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.30 + .6 * ms * ff, (event.flameCount + 1) / 5.5 + .6 * ms * ff, (event.flameCount + 1) / 5.5 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()	  
            glDisable(GL_TEXTURE_2D)

            glColor3f(flameColor[0], flameColor[1], flameColor[2])
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                glColor3f(.2,.4,.7)
              else: #Default starcolor (Rockband)
                glColor3f(.2,.2,.2)
            glEnable(GL_TEXTURE_2D)
            self.hitflames2Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x+.005, y +.25 +.005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.35 + .6 * ms * ff, (event.flameCount + 1) / 5.0 + .6 * ms * ff, (event.flameCount + 1) / 5.0 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()	  
            glDisable(GL_TEXTURE_2D)

            glColor3f(flameColor[0], flameColor[1], flameColor[2])
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                glColor3f(.2,.5,.7)
              else: #Default starcolor (Rockband)
                glColor3f(.3,.3,.3)
            glEnable(GL_TEXTURE_2D)
            self.hitflames2Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x, y +.25 +.005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.40 + .6 * ms * ff, (event.flameCount + 1)/ 4.7 + .6 * ms * ff, (event.flameCount + 1) / 4.7 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()	  
            glDisable(GL_TEXTURE_2D)
          else:
            flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
            
            glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
            if self.theme == 0 and event.finalStar and self.spEnabled:
              glColor3f(1,1,1)#lightning color
            elif self.theme == 1 and event.finalStar and self.spEnabled:
              glColor3f(1,1,1)#lightning color
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: 
                glColor3f(.3,.6,.7)#GH3 starcolor
              else:
                glColor3f(.4,.4,.4)#Default starcolor (Rockband)
            glEnable(GL_TEXTURE_2D)
            if self.theme == 0 and event.finalStar and self.spEnabled:
              self.hitlightning.texture.bind()
              wid, hei, = self.engine.view.geometry[2:4]
              glPushMatrix()
              glTranslate(xlightning, y, 3.3)
              glRotate(90, 1, 0, 0)
              glScalef(.15 + .5 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, 2)
              glBegin(GL_TRIANGLE_STRIP)
              glTexCoord2f(0.0, 0.0)
              glVertex3f( .4, 0, -2)
              glTexCoord2f(1.0, 0.0)
              glVertex3f(-.4, 0, -2)
              glTexCoord2f(0.0, 1.0)
              glVertex3f( .4, 0,  2)
              glTexCoord2f(1.0, 1.0)
              glVertex3f(-.4, 0,  2)
            elif self.theme == 1 and event.finalStar and self.spEnabled:
              self.hitlightning.texture.bind()
              wid, hei, = self.engine.view.geometry[2:4]
              glPushMatrix()
              glTranslate(xlightning, y, 3.3)
              glRotate(90, 1, 0, 0)
              glScalef(.15 + .5 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, 2)
              glBegin(GL_TRIANGLE_STRIP)
              glTexCoord2f(0.0, 0.0)
              glVertex3f( .4, 0, -2)
              glTexCoord2f(1.0, 0.0)
              glVertex3f(-.4, 0, -2)
              glTexCoord2f(0.0, 1.0)
              glVertex3f( .4, 0,  2)
              glTexCoord2f(1.0, 1.0)
              glVertex3f(-.4, 0,  2)
            else:
              self.hitflames1Drawing.texture.bind()
              glPushMatrix()
              glTranslate(x, y + .35, 0)
              glRotate(90, 1, 0, 0)
              glScalef(.25 + .6 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff)
              glBegin(GL_TRIANGLE_STRIP)
              glTexCoord2f(0.0, 0.0)
              glVertex3f(-flameSize * ff, 0, -flameSize * ff)
              glTexCoord2f(1.0, 0.0)
              glVertex3f( flameSize * ff, 0, -flameSize * ff)
              glTexCoord2f(0.0, 1.0)
              glVertex3f(-flameSize * ff, 0,  flameSize * ff)
              glTexCoord2f(1.0, 1.0)
              glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()
            glDisable(GL_TEXTURE_2D)

            flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
            
            glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)      
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                glColor3f(.3,.6,.8)
              else: #Default starcolor (Rockband)
                glColor3f(.5,.5,.5)
            glEnable(GL_TEXTURE_2D)
            self.hitflames1Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x - .005, y + .40 + .005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.30 + .6 * ms * ff, (event.flameCount + 1)/ 2.5 + .6 * ms * ff, (event.flameCount + 1) / 2.5 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()  
            glDisable(GL_TEXTURE_2D)

            flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
            
            glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                glColor3f(.3,.7,.8)
              else: #Default starcolor (Rockband)
                glColor3f(.6,.6,.6)
            glEnable(GL_TEXTURE_2D)
            self.hitflames1Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x + .005, y + .35 + .005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.35 + .6 * ms * ff, (event.flameCount + 1) / 2.0 + .6 * ms * ff, (event.flameCount + 1) / 2.0 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()  
            glDisable(GL_TEXTURE_2D)

            flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
            
            glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                glColor3f(.3,.7,.9)
              else: #Default starcolor (Rockband)
                glColor3f(.7,.7,.7)
            glEnable(GL_TEXTURE_2D)
            self.hitflames1Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x+.005, y +.35 +.005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.40 + .6 * ms * ff, (event.flameCount + 1) / 1.7 + .6 * ms * ff, (event.flameCount + 1) / 1.7 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()  
            glDisable(GL_TEXTURE_2D)
         

          glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
          event.flameCount += 1
        
  def render(self, visibility, song, pos, controls, killswitch):

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

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_COLOR_MATERIAL)
    if self.leftyMode:
      glScalef(-1, 1, 1)

    if self.ocount <= 1:
      self.ocount = self.ocount + .1
    else:
      self.ocount = 1

    if self.isFailing == True:
      if self.failcount <= 1 and self.failcount2 == False:
        self.failcount += .05
      elif self.failcount >= 1 and self.failcount2 == False:
        self.failcount = 1
        self.failcount2 = True
        
      if self.failcount >= 0 and self.failcount2 == True:
        self.failcount -= .05
      elif self.failcount <= 0 and self.failcount2 == True:
        self.failcount = 0
        self.failcount2 = False

    if self.isFailing == False and self.failcount > 0:
      self.failcount -= .05
      sefl.failcount2 = False

    if self.starPowerActive:

      if self.spcount < 1.2:
        self.spcount += .05
        self.spcount2 = 1
      elif self.spcount >=1.2:
        self.spcount = 1.2
        self.spcount2 = 0
    else:
      if self.spcount > 0:
        self.spcount -= .05
        self.spcount2 = 2
      elif self.spcount <=0:
        self.spcount = 0
        self.spcount2 = 0
      
    self.renderNeck(visibility, song, pos)
    self.renderIncomingNecks(visibility, song, pos) #MFH
    if self.theme == 0 or self.theme == 1 or self.theme == 2:
      self.drawTrack(self.ocount, song, pos)
      self.drawBPM(visibility, song, pos)
      self.drawSideBars(visibility, song, pos)
    else:
      self.renderTracks(visibility)
      self.renderBars(visibility, song, pos)
    

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

    self.renderFlames(visibility, song, pos, controls)
    
    if self.leftyMode:
      glScalef(-1, 1, 1)

  def getMissedNotes(self, song, pos, catchup = False):
    if not song:
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

    m1      = self.lateMargin
    m2      = self.lateMargin * 2
      
    track   = song.track[self.player]
    notes   = [(time, event) for time, event in track.getEvents(pos - m2, pos - m1) if isinstance(event, Note)]   #was out of order
    
    #MFH - this additional filtration step removes sustains whose Note On event time is now outside the hitwindow.
    notes   = [(time, event) for time, event in notes if (time >= (pos - m2)) and (time <= (pos - m1))] 
    
    notes   = [(time, event) for time, event in notes if not event.played and not event.hopod and not event.skipped]

    if catchup == True:
      for time, event in notes:
        event.skipped = True
      
    return sorted(notes, key=lambda x: x[0])    #MFH - what the hell, this should be sorted by TIME not note number....



  def getRequiredNotes(self, song, pos):
    track   = song.track[self.player]
    notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + self.earlyMargin) if isinstance(event, Note)]
    notes = [(time, event) for time, event in notes if not event.played]
    notes = [(time, event) for time, event in notes if (time >= (pos - self.lateMargin)) and (time <= (pos + self.earlyMargin))]
    if notes:
      t     = min([time for time, event in notes])
      notes = [(time, event) for time, event in notes if time - t < 1e-3]
    return sorted(notes, key=lambda x: x[1].number)

  def getRequiredNotes2(self, song, pos, hopo = False):

    track   = song.track[self.player]
    notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + self.earlyMargin) if isinstance(event, Note)]
    notes = [(time, event) for time, event in notes if not (event.hopod or event.played)]
    notes = [(time, event) for time, event in notes if (time >= (pos - self.lateMargin)) and (time <= (pos + self.earlyMargin))]
    if notes:
      t     = min([time for time, event in notes])
      notes = [(time, event) for time, event in notes if time - t < 1e-3]
      
    return sorted(notes, key=lambda x: x[1].number)
    
  def getRequiredNotes3(self, song, pos, hopo = False):

    track   = song.track[self.player]
    notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + self.earlyMargin) if isinstance(event, Note)]
    notes = [(time, event) for time, event in notes if not (event.hopod or event.played or event.skipped)]
    notes = [(time, event) for time, event in notes if (time >= (pos - self.lateMargin)) and (time <= (pos + self.earlyMargin))]

    return sorted(notes, key=lambda x: x[1].number)

  #MFH - corrected and optimized:
  #def getRequiredNotesMFH(self, song, pos):
  def getRequiredNotesMFH(self, song, pos, hopoTroubleCheck = False):
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


    return sorted(notes, key=lambda x: x[0])    #MFH - what the hell, this should be sorted by TIME not note number....


  #MFH - corrected and optimized:
  def getRequiredNotesForJurgenOnTime(self, song, pos):
    track   = song.track[self.player]
    notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + 30) if isinstance(event, Note)]
    notes = [(time, event) for time, event in notes if not (event.hopod or event.played or event.skipped)]

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
        for n, k in enumerate(self.keys):
          if controls.getState(k):
            twochord += 1
        if twochord == 2:
          skipped = len(requiredKeys) - 2
          requiredKeys = [min(requiredKeys), max(requiredKeys)]
        else:
          twochord = 0

      for n, k in enumerate(self.keys):
        if n in requiredKeys and not controls.getState(k):
          return False
        if not n in requiredKeys and controls.getState(k):
          # The lower frets can be held down
          if n > max(requiredKeys):
            return False
      if twochord != 0:
        if twochord != 2:
          for time, note in chord:
            note.played = True
        else:
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
      if note.hopod == True and controls.getState(self.keys[note.number]):
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
        
      for n, k in enumerate(self.keys):
        if n in requiredKeys and not controls.getState(k):
          return False
        if not n in requiredKeys and controls.getState(k):
          # The lower frets can be held down
          if hopo == False and n >= min(requiredKeys):
            return False
      if twochord != 0:
        if twochord != 2:
          for time, note in chord:
            note.played = True
        else:
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
      if note.hopod == True and controls.getState(self.keys[note.number]):
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
      for n, k in enumerate(self.keys):
        if (n in requiredKeys and not controls.getState(k)) or (n not in requiredKeys and controls.getState(k)):
          return False
    else:
    #Single Note must match that note
      requiredKey = requiredKeys[0]
      if not controls.getState(self.keys[requiredKey]):
        return False


      #myfingershurt: this is where to filter out higher frets held when HOPOing:
      if hopo == False or self.hopoStyle == 2 or self.hopoStyle == 4:
      #Check for higher numbered frets if not a HOPO or if GH2 strict mode
        for n, k in enumerate(self.keys):
          if n > requiredKey:
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
    
    
    self.lastPlayedNotes = self.playedNotes
    self.playedNotes = []
    
    self.matchingNotes = self.getRequiredNotesMFH(song, pos)

    self.controlsMatchNotes3(controls, self.matchingNotes, hopo)
    
    #myfingershurt
    
    for time, note in self.matchingNotes:
      if note.played != True:
        continue
      
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

  def run(self, ticks, pos, controls):
    self.time += ticks
    
    #MFH - Determine which frame to display for starpower notes
    if self.starspin:
      self.indexCount = self.indexCount + 1
      if self.indexCount > self.Animspeed-1:
        self.indexCount = 0
      self.starSpinFrameIndex = (self.indexCount * 16 - (self.indexCount * 16) % self.Animspeed) / self.Animspeed
      if self.starSpinFrameIndex > 15:
        self.starSpinFrameIndex = 0
    
    #myfingershurt: must not decrease SP if paused.
    if self.starPowerActive == True and self.paused == False:
      self.starPower -= ticks/200.0
      if self.starPower <= 0:
        self.starPower = 0
        self.starPowerActive = False
        #MFH - TODO - add call to play star power deactivation sound, if it exists (if not play nothing)
        if self.engine.data.starDeActivateSoundFound:
          #self.engine.data.starDeActivateSound.setVolume(self.sfxVolume)
          self.engine.data.starDeActivateSound.play()

    
    # update frets
    if self.editorMode:
      if (controls.getState(self.actions[0]) or controls.getState(self.actions[1])):
        activeFrets = [i for i, k in enumerate(self.keys) if controls.getState(k)] or [self.selectedString]
      else:
        activeFrets = []
    else:
      activeFrets = [note.number for time, note in self.playedNotes]
    
    for n in range(self.strings):
      if controls.getState(self.keys[n]) or (self.editorMode and self.selectedString == n):
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

    # glorandwarf: moved the update bpm code - was after the for statement below
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

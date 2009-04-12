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
import Shader

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

    self.starPowerDecreaseDivisor = 200.0/self.engine.audioSpeedFactor

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
    
    self.neckAlpha=[] # necks transparency
    self.neckAlpha.append( self.engine.config.get("game", "necks_alpha") ) # all necks
    self.neckAlpha.append( self.neckAlpha[0] * self.engine.config.get("game", "neck_alpha") ) # solo neck
    self.neckAlpha.append( self.neckAlpha[0] * self.engine.config.get("game", "solo_neck_alpha") ) # solo neck
    self.neckAlpha.append( self.neckAlpha[0] * self.engine.config.get("game", "bg_neck_alpha") ) # bass groove neck
    self.neckAlpha.append( self.neckAlpha[0] * self.engine.config.get("game", "overlay_neck_alpha") ) # overlay neck
    self.neckAlpha.append( self.neckAlpha[0] * self.engine.config.get("game", "fail_neck_alpha") ) # fail neck
    
    self.bigRockEndings = self.engine.config.get("game", "big_rock_endings")
    
    self.boardWidth     = 3.0
    self.boardLength    = 9.0
    self.beatsPerBoard  = 5.0
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


    self.actualBpm = 0.0

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
    self.starPowerActive = False
    self.starPowerGained = False

    self.killPoints = False

    self.starpowerMode = self.engine.config.get("game", "starpower_mode") #MFH
    
    #get difficulty
    self.difficulty = playerObj.getDifficultyInt()

    #myfingershurt:
    self.hopoStyle        = self.engine.config.get("game", "hopo_system")
    self.gh2sloppy        = self.engine.config.get("game", "gh2_sloppy")
    if self.gh2sloppy == 1:
      self.hopoStyle = 4
    self.LastStrumWasChord = False
    self.spRefillMode = self.engine.config.get("game","sp_notes_while_active")
    self.hitglow_color = self.engine.config.get("video", "hitglow_color") #this should be global, not retrieved every fret render.
    self.sfxVolume    = self.engine.config.get("audio", "SFX_volume")
    
    #myfingershurt: this should be retrieved once at init, not repeatedly in-game whenever tails are rendered.
    self.notedisappear = self.engine.config.get("game", "notedisappear")
    self.fretsUnderNotes  = self.engine.config.get("game", "frets_under_notes")
    self.staticStrings  = self.engine.config.get("performance", "static_strings")
    


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
    self.scoreMultiplier = 1

    self.hit = [False, False, False, False, False]
    
    self.freestyleHit = [False, False, False, False, False]
    

    self.neck = str(playerObj.neck)
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
    self.ocount = 0
    self.noterotate = self.engine.config.get("coffee", "noterotate")
    self.isFailing = False
    self.failcount = 0
    self.failcount2 = False
    self.spcount = 0
    self.spcount2 = 0
    self.bgcount = 0
    self.ovroverlay = self.engine.config.get("fretboard", "ovroverlay")
    
    #akedrou
    self.coOpFailed = False
    self.coOpRestart = False
    self.coOpRescueTime = 0.0
    
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
    
    self.keys = []
    self.actions = []

    
    self.setBPM(self.currentBpm)

    if self.starpowerMode == 1:
      self.starNotesSet = False
    else:
      self.starNotesSet = True

    self.maxStars = []
    self.starNotes = []
    self.totalNotes = 0


    engine.loadImgDrawing(self, "glowDrawing", "glow.png")
    
    if not engine.data.fileExists(os.path.join("necks", self.neck + ".png")) and not engine.data.fileExists(os.path.join("necks", "Neck_" + self.neck + ".png")):
      self.neck = str(engine.mainMenu.chosenNeck) #this neck is safe!

    # evilynux - Fixed random neck -- MFH: further fixing random neck
    if self.neck == "0" or self.neck == "Neck_0" or self.neck == "randomneck":
      self.neck = []
      # evilynux - improved loading logic to support arbitrary filenames
      for i in os.listdir(self.engine.resource.fileName("necks")):
        # evilynux - Special cases, ignore these...
        if( str(i) == "overdriveneck.png" or str(i) == "randomneck.png"  or str(i) == "Neck_0.png" or str(i)[-4:] != ".png" ):
          continue
        else:
          self.neck.append(str(i)[:-4]) # evilynux - filename w/o extension
      i = random.randint(1,len(self.neck))
      engine.loadImgDrawing(self, "neckDrawing", os.path.join("necks",self.neck[i]+".png"),  textureSize = (256, 256))
      Log.debug("Random neck chosen: " + self.neck[i])
    else:
      try:
        # evilynux - first assume the self.neck contains the full filename
        engine.loadImgDrawing(self, "neckDrawing", os.path.join("necks",self.neck+".png"),  textureSize = (256, 256))
      except IOError:
        engine.loadImgDrawing(self, "neckDrawing", os.path.join("necks","Neck_"+self.neck+".png"),  textureSize = (256, 256))




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
          try:
            engine.loadImgDrawing(self, "oNeckBass", os.path.join("themes",themename,"overdriveneck_bass.png"),  textureSize = (256, 256))
          except IOError:
            try:
              engine.loadImgDrawing(self, "oNeckBass", os.path.join("themes",themename,"overdriveneck.png"),  textureSize = (256, 256))
            except IOError:
              self.oNeckBass = None
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
          engine.loadImgDrawing(self, "oNeckBass", os.path.join("themes",themename,"overdriveneck_bass.png"),  textureSize = (256, 256))
        except IOError:
          try:
            engine.loadImgDrawing(self, "oNeckBass", os.path.join("themes",themename,"overdriveneck.png"),  textureSize = (256, 256))
          except IOError:
            self.oNeckBass = None
        try:
          engine.loadImgDrawing(self, "oNeck", os.path.join("themes",themename,"overdriveneck.png"),  textureSize = (256, 256))
        except IOError:
          self.oNeck = None
          
      try:
        engine.loadImgDrawing(self, "oNeckovr", os.path.join("themes",themename,"overdriveneckovr.png"),  textureSize = (256, 256))
      except IOError:
        self.oNeckovr = None

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

      self.oNeckovr = None #fixes GH theme crash
      #myfingershurt: the starpower neck file should be in the theme folder... and also not required:
      try:
        engine.loadImgDrawing(self, "oNeck", os.path.join("themes",themename,"starpowerneck.png"),  textureSize = (256, 256))
      except IOError:
        self.oNeck = None
      try:
        engine.loadImgDrawing(self, "oNeckBass", os.path.join("themes",themename,"starpowerneck_bass.png"),  textureSize = (256, 256))
      except IOError:
        try:
          engine.loadImgDrawing(self, "oNeckBass", os.path.join("themes",themename,"starpowerneck.png"),  textureSize = (256, 256))
        except IOError:
          self.oNeckBass = None

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
    if not song.readyToGo:
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

  def renderNeckMethod(self, visibility, offset, beatsPerUnit, neck, alpha = False): #blazingamer: New neck rendering method

    def project(beat):
      return 0.125 * beat / beatsPerUnit    # glorandwarf: was 0.12
      
    
    if self.starPowerActive and self.theme == 0:#8bit
      color = self.spColor #(.3,.7,.9)
    elif self.starPowerActive and self.theme == 1:
      color = self.spColor #(.3,.7,.9)
    else:
      color = (1,1,1)

    v            = visibility
    w            = self.boardWidth
    l            = self.boardLength

    beatsPerUnit = beatsPerUnit
    offset       = offset
    
    glEnable(GL_TEXTURE_2D)

    if alpha == True:
      glBlendFunc(GL_ONE, GL_ONE)
    neck.texture.bind()
    neck_col  = array([[color[0],color[1],color[2], 0],
                       [color[0],color[1],color[2], 0],
                       [color[0],color[1],color[2], v],
                       [color[0],color[1],color[2], v],
                       [color[0],color[1],color[2], v],
                       [color[0],color[1],color[2], v],
                       [color[0],color[1],color[2], 0],
                       [color[0],color[1],color[2], 0]], dtype=float32)
    neck_vtx = array([[-w / 2, 0, -2],
                      [w / 2, 0, -2],
                      [-w / 2, 0, -1],
                      [w / 2, 0, -1],
                      [-w / 2, 0, l * .7],
                      [w / 2, 0, l * .7],
                      [-w / 2, 0, l],
                      [w / 2, 0, l]], dtype=float32)
    neck_tex  = array([[0.0, project(offset - 2 * beatsPerUnit)],
                       [1.0, project(offset - 2 * beatsPerUnit)],
                       [0.0, project(offset - 1 * beatsPerUnit)],
                       [1.0, project(offset - 1 * beatsPerUnit)],
                       [0.0, project(offset + l * beatsPerUnit * .7)],
                       [1.0, project(offset + l * beatsPerUnit * .7)],
                       [0.0, project(offset + l * beatsPerUnit)],
                       [1.0, project(offset + l * beatsPerUnit)]], dtype=float32)
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_COLOR_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY);
    glVertexPointerf(neck_vtx)
    glColorPointerf(neck_col)
    glTexCoordPointerf(neck_tex)
    glDrawArrays(GL_TRIANGLE_STRIP, 0, neck_vtx.shape[0])
    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_COLOR_ARRAY)
    glDisableClientState(GL_TEXTURE_COORD_ARRAY);

    if alpha == True:
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
      
    glDisable(GL_TEXTURE_2D)
    
  def renderNeck(self, visibility, song, pos):     
    if not song:
      return
    if not song.readyToGo:
      return
    
    def project(beat):
      print 0.125 * beat / beatsPerUnit
      return 0.125 * beat / beatsPerUnit    # glorandwarf: was 0.12

    v            = visibility
    w            = self.boardWidth
    l            = self.boardLength

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    offset       = (pos - self.lastBpmChange) / self.currentPeriod + self.baseBeat 

    #myfingershurt: every theme can have oNeck:

    if self.guitarSolo and self.guitarSoloNeck != None and self.guitarSoloNeckMode == 1:
      neck = self.guitarSoloNeck
    elif self.scoreMultiplier > 4 and self.bassGrooveNeck != None and self.bassGrooveNeckMode == 1:
      neck = self.bassGrooveNeck
    elif self.starPowerActive and not (self.spcount2 != 0 and self.spcount < 1.2) and self.oNeck and self.scoreMultiplier <= 4:
      if self.isBassGuitar and self.oNeckBass:
        neck = self.oNeckBass
      else:
        neck = self.oNeck
    else:
      neck = self.neckDrawing

    
    
    if not (self.guitarSolo and self.guitarSoloNeck != None and self.guitarSoloNeckMode == 2):
      self.renderNeckMethod(v*self.neckAlpha[1], offset, beatsPerUnit, neck)

    if self.bgcount > 0 and self.bassGrooveNeck != None and self.bassGrooveNeckMode == 2:   #static bass groove overlay
      self.renderNeckMethod(v*self.bgcount*self.neckAlpha[3], 0, beatsPerUnit, self.bassGrooveNeck)
      
    elif self.guitarSolo and self.guitarSoloNeck != None and self.guitarSoloNeckMode == 2:   #static overlay
      self.renderNeckMethod(v*self.neckAlpha[2], 0, beatsPerUnit, self.guitarSoloNeck)
      
    if self.spcount2 != 0 and self.spcount < 1.2 and self.oNeck:   #static overlay
      if self.oNeckovr != None and (self.scoreMultiplier > 4 or self.guitarSolo):
        neck = self.oNeckovr
      else:
        if self.isBassGuitar and self.oNeckBass:
          neck = self.oNeckBass
        else:
          neck = self.oNeck
          
      self.renderNeckMethod(self.spcount*self.neckAlpha[4], offset, beatsPerUnit, neck)
      
    
      
    if self.starPowerActive and not (self.spcount2 != 0 and self.spcount < 1.2) and self.oNeck and (self.scoreMultiplier > 4 or self.guitarSolo):   #static overlay

      if self.oNeckovr != None:
        neck = self.oNeckovr
      else:
        if self.isBassGuitar and self.oNeckBass:
          neck = self.oNeckBass
        else:
          neck = self.oNeck
        alpha = True

      self.renderNeckMethod(v*self.neckAlpha[4], offset, beatsPerUnit, neck, alpha)

    if Shader.list.enabled:
      posx = Shader.list.time()
      fret = []
      for i in range(5):
        fret.append(max(posx - Shader.list.var["fret"][i] + 0.7,0.01))
      r = 1.2 / fret[1] + 0.6 / fret[2] + 0.8 / fret[4]
      g = 1.2 / fret[0] + 0.6 / fret[2] + 0.4 / fret[4]
      b = 1.2 / fret[3]
      a = (r+g+b)/70.0
      Shader.list.var["color"]=(r,g,b,a*2.0)
      
    if Shader.list.enable("neck"):
      Shader.list.setVar("fretcol","color")
      Shader.list.setVar("fail",self.isFailing)
      Shader.list.update()
      glBegin(GL_TRIANGLE_STRIP)
      glVertex3f(-w / 2, 0.1, -2)
      glVertex3f(w / 2, 0.1, -2)
      glVertex3f(-w / 2, 0.1, l)
      glVertex3f(w / 2, 0.1, l)
      glEnd()
      Shader.list.disable()
    else:
      if self.isFailing:
        self.renderNeckMethod(self.failcount*self.neckAlpha[5], 0, beatsPerUnit, self.failNeck)
        
    if (self.guitarSolo or self.starPowerActive) and self.theme == 1:
      Shader.list.var["solocolor"]=(0.3,0.7,0.9,0.6)
    else:
      Shader.list.var["solocolor"]=(0.0,)*4


  def drawTrack(self, visibility, song, pos):
    if not song:
      return
    if not song.readyToGo:
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
    if not song.readyToGo:
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
    
    if self.theme == 1:   
      if Shader.list.enable("sololight"):
        Shader.list.modVar("color",Shader.list.var["solocolor"])
        Shader.list.setVar("offset",(-3.5,-w/2))
        glBegin(GL_TRIANGLE_STRIP)
        glVertex3f(w / 2-1.0, 0.4, -2)
        glVertex3f(w / 2+1.0, 0.4, -2)
        glVertex3f(w / 2-1.0, 0.4, l)
        glVertex3f(w / 2+1.0, 0.4, l)
        glEnd()   
        Shader.list.setVar("offset",(-3.5,w/2))
        Shader.list.setVar("time",Shader.list.time()+0.5)
        glBegin(GL_TRIANGLE_STRIP)
        glVertex3f(-w / 2+1.0, 0.4, -2)
        glVertex3f(-w / 2-1.0, 0.4, -2)
        glVertex3f(-w / 2+1.0, 0.4, l)
        glVertex3f(-w / 2-1.0, 0.4, l)
        glEnd()  
        Shader.list.disable()

  def drawBPM(self, visibility, song, pos):
    if not song:
      return
    if not song.readyToGo:
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

    beatsPerUnit = self.beatsPerBoard / self.boardLength

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
          
        if self.theme == 2 and big and tailOnly and Shader.list.enable("tail"):
          if kill and self.killfx == 0:
            Shader.list.setVar("color",(1.0,1.0,1.0,1.0))
            Shader.list.setVar("height",0.05)
          else:  
            
            Shader.list.setVar("color",color[:3]+(0.3,))
            Shader.list.setVar("height",0.3)
          Shader.list.setVar("scalexy",(5.0,1.0))
          Shader.list.setVar("offset",(5.0-s,0.0))
          size=(size[0]*4,size[1])
          
          
        self.engine.draw3Dtex(tex1, vertex = (-size[0], 0, size[0], size[1]), texcoord = (0.0, 0.0, 1.0, 1.0),
                              scale = tailscale, color = tailcol)
        self.engine.draw3Dtex(tex2, vertex = (-size[0], size[1], size[0], size[1] + (zsize)),
                              scale = tailscale, texcoord = (0.0, 0.05, 1.0, 0.95), color = tailcol)

        Shader.list.disable()  

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

    beatsPerUnit = self.beatsPerBoard / self.boardLength


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

  def renderFreestyleLanes(self, visibility, song, pos):
    if not song:
      return
    if not song.readyToGo:
      return


    #boardWindowMin = pos - self.currentPeriod * 2
    boardWindowMax = pos + self.currentPeriod * self.beatsPerBoard
    track = song.midiEventTrack[self.player]
    #self.currentPeriod = self.neckSpeed
    beatsPerUnit = self.beatsPerBoard / self.boardLength

    #MFH - render 5 freestyle tails when Song.freestyleMarkingNote comes up
    if self.freestyleEnabled:
      freestyleActive = False
      #for time, event in track.getEvents(boardWindowMin, boardWindowMax):
      for time, event in track.getEvents(pos - self.freestyleOffset , boardWindowMax + self.freestyleOffset):
        if isinstance(event, Song.MarkerNote):
          if event.number == Song.freestyleMarkingNote:
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



  def renderIncomingNecks(self, visibility, song, pos):
    if not song:
      return
    if not song.readyToGo:
      return

    boardWindowMin = pos - self.currentPeriod * 2
    boardWindowMax = pos + self.currentPeriod * self.beatsPerBoard
    track = song.midiEventTrack[self.player]
    #self.currentPeriod = self.neckSpeed
    beatsPerUnit = self.beatsPerBoard / self.boardLength
    



    if self.incomingNeckMode > 0:   #if enabled


      #if self.song.hasStarpowerPaths and self.song.midiStyle == Song.MIDI_TYPE_RB:  
      if self.useMidiSoloMarkers:
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
    if not song.readyToGo:
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
      z  = ((time - pos) / self.currentPeriod) / beatsPerUnit
      z2 = ((time + event.length - pos) / self.currentPeriod) / beatsPerUnit


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
    self.targetPeriod  = self.neckSpeed

    self.killPoints = False

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    
    w = self.boardWidth / self.strings
    
    track = song.track[self.player]

    num = 0
    enable = True
    for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard):
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
          proj  = 1.0 / self.currentPeriod / beatsPerUnit
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

        size = (self.boardWidth/self.strings/2, self.boardWidth/self.strings/2.4)
        texSize = (n/5.0,n/5.0+0.2)

        texY = (0.0,1.0/3.0)
        if controls.getState(self.keys[n]) or controls.getState(self.keys[n+5]):
          texY = (1.0/3.0,2.0/3.0)
        if self.hit[n]:
          texY = (2.0/3.0,1.0)

        self.engine.draw3Dtex(self.fretButtons, vertex = (size[0],size[1],-size[0],-size[1]), texcoord = (texSize[0], texY[0], texSize[1], texY[1]),
                              coord = (x,v,0), multiples = True,color = (1,1,1), depth = True)

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
          glowcol = (c[0], c[1], c[2])#Same as fret
        elif self.hitglow_color == 1:
          glowcol = (1, 1, 1)#Actual color in .svg-file

        f += 2

        self.engine.draw3Dtex(self.glowDrawing, coord = (x, y, 0.01), rot = (f * 90 + self.time, 0, 1, 0),
                              texcoord = (0.0, 0.0, 1.0, 1.0), vertex = (-size[0] * f, -size[1] * f, size[0] * f, size[1] * f),
                              multiples = True, alpha = True, color = glowcol)

      #self.hit[n] = False  #MFH -- why?  This prevents frets from being rendered under / before the notes...
    glDisable(GL_DEPTH_TEST)

  def renderFreestyleFlames(self, visibility, controls):
    if self.flameColors[0][0][0] == -1:
      return

    beatsPerUnit = self.beatsPerBoard / self.boardLength
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

    beatsPerUnit = self.beatsPerBoard / self.boardLength
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
        self.failcount2 = False

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

      if self.scoreMultiplier > 4 and self.bgcount < 1:
        self.bgcount += .1
      if self.scoreMultiplier < 4 and self.bgcount > 0:
        self.bgcount -= .1
      
      
      self.renderNeck(visibility, song, pos)
      self.renderIncomingNecks(visibility, song, pos) #MFH
      if self.theme == 0 or self.theme == 1 or self.theme == 2:
        self.drawTrack(self.ocount, song, pos)
        self.drawBPM(visibility, song, pos)
        self.drawSideBars(visibility, song, pos)
      else:
        self.renderTracks(visibility)
        self.renderBars(visibility, song, pos)
    

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

      Shader.list.var["fret"][note.number]=Shader.list.time()
      
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
        Shader.list.var["fret"][theFret]=Shader.list.time()
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
        Shader.list.var["fret"][theFret]=Shader.list.time()
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
      self.starSpinFrameIndex = (self.indexCount * 16 - (self.indexCount * 16) % self.Animspeed) / self.Animspeed
      if self.starSpinFrameIndex > 15:
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

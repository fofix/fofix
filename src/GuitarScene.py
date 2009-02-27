#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstil?                                  #
#               2008 Alarian                                        #
#               2008 myfingershurt                                  #
#               2008 Capo                                           #
#               2008 Spikehead777                                   #
#               2008 Glorandwarf                                    #
#               2008 ShiekOdaSandz                                  #
#               2008 QQStarS                                        #
#               2008 .liquid.                                       #
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

from Scene import SceneServer, SceneClient
from Song import Note, Tempo, TextEvent, PictureEvent, loadSong, Bars
from Menu import Menu
from Guitar import Guitar, PLAYER1KEYS, PLAYER2KEYS, PLAYER1ACTIONS, PLAYER2ACTIONS

#myfingershurt: drums :)
from Drum import Drum, PLAYER1DRUMS, PLAYER2DRUMS

from Language import _
import Player
import Dialogs
import Data
import Theme
import View
import Audio
import Stage
import Settings
import Song
import Scorekeeper

import math
import pygame
import random
import os

#myfingershurt: decimal class allows for better handling of fixed-point numbers
import decimal
import Log
import locale

from OpenGL.GL import *

#MFH: experimental 2D font rendering module
import lamina

#stump: needed for continuous star fillup
import Image
import ImageDraw
from Svg import ImgDrawing


class GuitarScene:
  pass

class GuitarSceneServer(GuitarScene, SceneServer):
  pass

class GuitarSceneClient(GuitarScene, SceneClient):
  def createClient(self, libraryName, songName, Players):
  
    if self.engine.createdGuitarScene:  #MFH - dual / triple loading cycle fix
      Log.warn("Extra GuitarSceneClient was instantiated, but detected and shut down.  Cause unknown.")
      return
    else:
      self.engine.createdGuitarScene = True

    self.playerList   = [self.player]

    self.partyMode = False
    self.battle = False #QQstarS:new2 Bettle
    self.coOp = False
    self.coOpRB = False #akedrou
    self.coOpGH = False
    self.coOpType = False
    self.practiceMode = False
    Log.debug("GuitarSceneClient init...")

    self.coOpPlayerMeter = 1

    #MFH - testing new traceback logging:
    #raise TypeError
    
    splash = Dialogs.showLoadingSplashScreen(self.engine, _("Preparing...")) 


    self.countdownSeconds = 5   #MFH - don't change this initialization value unless you alter the other related variables to match
    self.countdown = 10   #MFH - arbitrary value to prevent song from starting right away
    
    #MFH - retrieve game parameters:
    self.gamePlayers = self.engine.config.get("game", "players")
    self.gameMode1p = self.engine.config.get("player0","mode_1p")
    self.gameMode2p = self.engine.config.get("player1","mode_2p")
    self.fxEnabled = self.engine.config.get("video","special_fx")

    Players = self.gamePlayers    #ensure this gets passed correctly

    if self.gameMode1p == 2:
      self.careerMode = True
    else:
      self.careerMode = False


    
    #MFH - check for party mode
    if self.gameMode2p == 2:
      self.partyMode  = True
      Players         = 1
      self.partySwitch      = 0
      self.partyTime        = self.engine.config.get("game", "party_time")
      self.partyPlayer      = 0
    elif Players == 2:
      self.playerList = self.playerList + [self.player2]
      
      #MFH - check for battle mode
      if self.gameMode2p == 1:
        self.battle   = True
        self.coOp     = False
        self.coOpRB   = False
        self.coOpGH   = False
        self.coOpType = False
      elif self.gameMode2p == 3:
        self.battle   = False
        self.coOp     = True
        self.coOpRB   = False
        self.coOpGH   = False
        self.coOpType = True
      elif self.gameMode2p == 4:
        self.battle   = False
        self.coOp     = False
        self.coOpRB   = True
        self.coOpGH   = False
        self.coOpType = True
      elif self.gameMode2p == 5:
        self.battle   = False
        self.coOp     = False
        self.coOpRB   = False
        self.coOpGH   = True
        self.coOpType = True
      else:
        self.battle   = False
        self.coOp     = False
        self.coOpRB   = False
        self.coOpGH   = False
        self.coOpType = False

    self.splayers = Players #Spikehead777

    #myfingershurt: drums :)
    self.guitars = []
    self.keysList = []
    for i,player in enumerate(self.playerList):
      if player.part.id == Song.DRUM_PART:
        self.guitars.append(Drum(self.engine,False,i))
      else:
        self.guitars.append(Guitar(self.engine,False,i))
        if player.part.id == Song.LEAD_PART or player.part.id == Song.GUITAR_PART:    #both these selections should get guitar solos
          self.guitars[i].canGuitarSolo = True
        elif player.part.id == Song.BASS_PART:
          self.guitars[i].isBassGuitar = True
      if player.practiceMode:
        self.practiceMode = True
    if self.guitars[0].isDrum: 
      self.keysList = [PLAYER1DRUMS]
    else:
      self.keysList = [PLAYER1KEYS]
    if Players == 2:
      if self.guitars[1].isDrum: 
        self.keysList = self.keysList + [PLAYER2DRUMS]
      else:
        self.keysList = self.keysList + [PLAYER2KEYS]
    
    #Log.debug("GuitarScene keysList: " + str(self.keysList))
    Log.debug("GuitarScene keysList: %s" % str(self.keysList))

    #for number formatting with commas for Rock Band:
    locale.setlocale(locale.LC_ALL, '')   #more compatible
    
    self.visibility       = 1.0
    self.libraryName      = libraryName
    self.songName         = songName
    self.done             = False
    
    #try:
    #  self.sfxChannel = self.engine.audio.getChannel(5)
    #except Exception, e:
    #  Log.warn("GuitarScene.py: Unable to procure sound effect track: %s" % e)
    #  self.sfxChannel = None
    
    self.lastMultTime     = [None for i in self.playerList]
    self.cheatCodes       = [
      #([117, 112, 116, 111, 109, 121, 116, 101, 109, 112, 111], self.toggleAutoPlay), #Jurgen is enabled in the menu -- Spikehead777
      ([102, 97, 115, 116, 102, 111, 114, 119, 97, 114, 100],   self.goToResults)
    ]
    self.enteredCode      = []
    self.song             = None

    #self.finishedProcessingSong = False

    #Spikehead777
    self.jurg             = self.engine.config.get("game", "jurgtype")
    
    #MFH
    self.jurgenLogic = self.engine.config.get("game", "jurglogic")    #logic 0 = original, logic 1 = MFH-1
    #self.jurgenText = self.engine.config.get("game", "jurgtext")
    self.jurgenText = Theme.jurgTextPos
    if float(self.jurgenText[2]) < 0.00035:
      self.jurgenText[2] = 0.00035
    if float(self.jurgenText[0]) < 0:
      self.jurgenText[0] = 0
    if float(self.jurgenText[1]) < 0:
      self.jurgenText[1] = 0

    self.whammySavesSP = self.engine.config.get("game", "whammy_saves_starpower") #MFH
    self.failingEnabled = self.engine.config.get("coffee", "failingEnabled")

    self.timeLeft = None
    self.processedFirstNoteYet = False
    
    self.numOfPlayers = len(self.playerList)        #MFH - MUST be in front of loadSettings call!
    
    self.autoPlay         = self.engine.config.get("game", "jurgmode")
    if self.autoPlay == 0:
      self.autoPlay = True
    else:
      self.autoPlay = False
    self.playerAssist = [None for i in self.playerList]
    self.playerAssist[0] = self.engine.config.get("game", "p1_assist")
    if self.numOfPlayers > 1:
      self.playerAssist[1] = self.engine.config.get("game", "p2_assist")
    for i, player in enumerate(self.playerList):
      if self.playerAssist[i] == 3 and not self.guitars[i].isDrum:
        self.playerAssist[i] = 0
      elif self.playerAssist[i] == 2 and player.getDifficultyInt() > 1:
        self.playerAssist[i] = 0
      elif self.playerAssist[i] == 1 and player.getDifficultyInt() > 2:
        self.playerAssist[i] = 0
    for assistMode in self.playerAssist:
      if assistMode > 0:
        self.assisting = True
        break
    else:
      self.assisting = False
    
    self.jurgPlayer       = [False for i in self.playerList]

    self.lastPickPos      = [None for i in self.playerList]
    self.lastSongPos      = 0.0
    self.keyBurstTimeout  = [None for i in self.playerList]
    self.keyBurstPeriod   = 30
    self.camera.target    = (0.0, 0.0, 4.0)
    self.camera.origin    = (0.0, 3.0, -3.0)
    self.camera.target    = (0.0, 1.0, 8.0)
    self.camera.origin    = (0.0, 2.0, -3.4)

    self.targetX          = Theme.povTargetX
    self.targetY          = Theme.povTargetY
    self.targetZ          = Theme.povTargetZ
    self.originX          = Theme.povOriginX
    self.originY          = Theme.povOriginY
    self.originZ          = Theme.povOriginZ
    self.ending           = False
    

    self.pause = False
    self.failed = False
    self.finalFailed = False
    self.failEnd = False
    self.crowdsCheering = False #akedrou
    self.inUnison = [False for i in self.playerList]
    self.haveUnison = [False for i in self.playerList]
    self.firstUnison = False
    self.firstUnisonDone = False
    self.unisonActive = False
    self.unisonNum = 0
    self.unisonEarn = [False for i in self.playerList]
    self.starPowersActive = 0
    self.playersInGreen = 0
    self.crowdFaderVolume = 0.0
    self.coOpStarPower = 0
    self.coOpStarPowerTimer = 0
    self.coOpStarPowerActive = [0 for i in self.playerList]
    self.failTimer = 0
    self.rockTimer = 0  #myfingershurt
    self.youRock = False    #myfingershurt
    self.rockCountdown = 100
    self.soloReviewDispDelay = 300
    self.baseScore = 50
    self.baseSustainScore = .1
    self.rockFinished = False
    self.spTimes = [[] for i in self.playerList]
    self.midiSP = False
    self.oBarScale = 0.0 #volshebnyi - overdrive bar scale factor


    ###Capo###
    self.firstClap = True
    ###endCapo###
    
    
    self.multi = [1 for i in self.playerList]
    self.x1 = [0 for i in self.playerList]
    self.y1 = [0 for i in self.playerList]
    self.x2 = [0 for i in self.playerList]
    self.y2 = [0 for i in self.playerList]
    self.x3 = [0 for i in self.playerList]
    self.y3 = [0 for i in self.playerList]
    if self.coOpType:
      self.x1.append(0)
      self.y1.append(0)
      self.x2.append(0)
      self.y2.append(0)
      self.x3.append(0)
      self.y3.append(0)
    

    #MFH - precalculation variable definition


    #Get theme
    themename = self.engine.data.themeLabel
    self.theme = self.engine.data.theme

    if Theme.rmtype != None:
      self.rmtype = Theme.rmtype
    else:
      self.rmtype = self.theme

    if Theme.hopoIndicatorX != None:
      self.hopoIndicatorX   = Theme.hopoIndicatorX
    else:
      self.hopoIndicatorX = .950
      
    if Theme.hopoIndicatorY != None:
      self.hopoIndicatorY   = Theme.hopoIndicatorY
    else:
      self.hopoIndicatorY = .710
     
    self.hopoIndicatorActiveColor   = Theme.hopoIndicatorActiveColor
    self.hopoIndicatorInactiveColor   = Theme.hopoIndicatorInactiveColor
    
    if self.coOpGH:
      for i, guitar in enumerate(self.guitars):
        guitar.starPowerDecreaseDivisor /= self.numOfPlayers




    stage = os.path.join("themes",themename,"stage.ini")
    self.stage = Stage.Stage(self, self.engine.resource.fileName(stage))

    self.loadSettings()

    #MFH pre-translate text strings:
    self.tsNoteStreak = _("Note Streak!!!")
    if self.theme == 2:
      self.tsStarPowerReady = _("Overdrive Ready")
      self.tsCoOpStarPower  = _("Activate Overdrive!")
    else:
      self.tsStarPowerReady = _("Star Power Ready")
      self.tsCoOpStarPower  = _("Activate Star Power!") #The proper is "Tilt guitar to activate Star Power", but drums and all...
    self.tsYouFailedBattle = _("You Failed!!!!")
    self.tsJurgenIsHere = _("Jurgen is here")
    self.tsJurgenWasHere = _("Jurgen was here")
    self.tsPercentComplete = _("% Complete")
    self.tsHopoIndicator = _("HOPO")
    self.tsCompleted = _("COMPLETED")
    self.tsPercentOn = _(" % ON ")
    self.tsBassGroove = _("BASS GROOVE")
    self.tsBassGrooveLabel = _("Bass Groove:")
    self.tsHandicapLabel = _("Handicap")
    self.tsAvgLabel = _("Avg")
    self.tsAccVeryLate = _("Very Late")
    self.tsAccLate = _("Late")
    self.tsAccSlightlyLate = _("Slightly Late")
    self.tsAccExcellentLate = _("-Excellent!")
    self.tsAccPerfect = _("Perfect!!")
    self.tsAccExcellentEarly = _("+Excellent!")
    self.tsAccSlightlyEarly = _("Slightly Early")
    self.tsAccEarly = _("Early")
    self.tsAccVeryEarly = _("Very Early")
    self.msLabel = _("ms")
    #self.tsSolo = _("Guitar Solo!")
    self.tsSolo = _("Solo!")
    self.tsPerfectSolo = _("Perfect")
    self.tsAwesomeSolo = _("Awesome")
    self.tsGreatSolo = _("Great")
    self.tsGoodSolo = _("Good")
    self.tsSolidSolo = _("Solid")
    self.tsOkaySolo = _("Okay")
    self.tsMessySolo = _("Messy")
    self.tsPtsLabel = _("pts")
    self.tsGetReady = _("Get Ready to Rock")
    self.tsAsMadeFamousBy = _("as made famous by")
    self.tsBy = _("by ")
    self.tsFrettedBy = _(" fretted by ")


    self.playerList[0].currentTheme = self.theme
    if self.numOfPlayers > 1:
      self.playerList[1].currentTheme = self.theme

    #MFH - precalculate full and player viewports
    self.engine.view.setViewport(1,0)
    self.wFull, self.hFull = self.engine.view.geometry[2:4]
    #Log.debug("GuitarScene wFull = %d, hFull = %d" % (self.wFull, self.hFull) )
    self.wPlayer = []
    self.hPlayer = []
    self.hOffset = []
    self.hFontOffset = []
    self.stage.wFull = self.wFull   #MFH - needed for new stage background handling
    self.stage.hFull = self.hFull
    #self.fontScreenBottom = 0.75      #from our current viewport's constant 3:4 aspect ratio (which is always stretched to fill the video resolution)
    self.fontScreenBottom = self.engine.data.fontScreenBottom
    self.oBarScaleCoef = (0.6 + 0.4 * self.numOfPlayers) * 1.256 * self.hFull / self.wFull #volshebnyi - depends on resolution and number of players 
    
    for i, thePlayer in enumerate(self.playerList):
      self.engine.view.setViewportHalf(self.numOfPlayers,i)
      w, h = self.engine.view.geometry[2:4]
      self.wPlayer.append( w )
      self.hPlayer.append( h )
      self.hOffset.append( h )
      self.hFontOffset.append( h )
      self.wPlayer[i] = self.wPlayer[i]*self.numOfPlayers #QQstarS: set the width to right one
      if self.numOfPlayers>1:
        self.hPlayer[i] = self.hPlayer[i]*self.numOfPlayers/1.5 #QQstarS: Set the hight to right one
      else:
        self.hPlayer[i] = self.hPlayer[i]*self.numOfPlayers #QQstarS: Set the hight to right one
      self.hOffset[i] = self.hPlayer[i]*.4*(self.numOfPlayers-1) #QQstarS: Hight Offset when there are 2 players
      self.hFontOffset[i] = -self.hOffset[i]/self.hPlayer[i]*0.752 #QQstarS: font Hight Offset when there are 2 players

    self.engine.view.setViewport(1,0)

    

    self.drumMisses = self.engine.config.get("game", "T_sound") #Faaa Drum sound
    if not self.engine.data.bassDrumSoundFound:
      self.bassKickSoundEnabled = False
    if not self.engine.data.T1DrumSoundFound:
      self.drumMisses == 0
    if not self.engine.data.T2DrumSoundFound:
      self.drumMisses == 0
    if not self.engine.data.T3DrumSoundFound:
      self.drumMisses == 0
    if not self.engine.data.CDrumSoundFound:
      self.drumMisses == 0


    #MFH - constant definitions, ini value retrievals
    self.pitchBendLowestFactor = .90 #stump: perhaps read this from song.ini and fall back on a specific value?
    self.lineByLineLyricMaxLineWidth = 0.5
    self.lineByLineStartSlopMs = 750
    self.digitalKillswitchStarpowerChunkSize = 0.05 * self.engine.audioSpeedFactor
    self.digitalKillswitchActiveStarpowerChunkSize = self.digitalKillswitchStarpowerChunkSize / 3.0
    # evilynux: was 0.10, now much closer to actual GH3
    self.analogKillswitchStarpowerChunkSize = 0.15 * self.engine.audioSpeedFactor
    self.analogKillswitchActiveStarpowerChunkSize = self.analogKillswitchStarpowerChunkSize / 3.0
    self.rbOverdriveBarGlowFadeInChunk = .07     #this amount added to visibility every run() cycle when fading in - original .2
    self.rbOverdriveBarGlowFadeOutChunk = .03   #this amount subtracted from visibility every run() cycle when fading out - original .07
    self.crowdCheerFadeInChunk =  .02           #added to crowdVolume every run() when fading in
    self.crowdCheerFadeOutChunk = .03           #subtracted from crowdVolume every run() on fade out.
    self.maxDisplayTextScale = 0.0024       #orig 0.0024
    self.displayTextScaleStep2 = 0.00008    #orig 0.00008
    self.displayTextScaleStep1 = 0.0001     #orig 0.0001
    self.textTimeToDisplay = 100
    self.songInfoDisplayScale = Theme.songInfoDisplayScale
    self.songInfoDisplayX = Theme.songInfoDisplayX             #Worldrave - This controls the X position of song info display during countdown
    self.songInfoDisplayY = Theme.songInfoDisplayY             #Worldrave - This controls the Y position of song info display during countdown
    self.lyricMode = self.engine.config.get("game", "lyric_mode")
    self.scriptLyricPos = self.engine.config.get("game", "script_lyric_pos")
    self.starClaps = self.engine.config.get("game", "star_claps")
    self.rb_sp_neck_glow = self.engine.config.get("game", "rb_sp_neck_glow")
    self.accuracy = [0 for i in self.playerList]
    self.resumeCountdownEnabled = self.engine.config.get("game", "resume_countdown")
    self.resumeCountdown = 0
    self.resumeCountdownSeconds = 0
    self.pausePos = 0
    self.dispAccuracy = [False for i in self.playerList]
    self.showAccuracy = self.engine.config.get("game", "accuracy_mode")
    self.hitAccuracyPos = self.engine.config.get("game", "accuracy_pos")
    self.showUnusedTextEvents = self.engine.config.get("game", "show_unused_text_events")
    self.bassKickSoundEnabled = self.engine.config.get("game", "bass_kick_sound")
    self.gameTimeMode = self.engine.config.get("game", "game_time")
    self.midiLyricsEnabled = self.engine.config.get("game", "rb_midi_lyrics")
    self.midiSectionsEnabled = self.engine.config.get("game", "rb_midi_sections") #MFH
    if self.numOfPlayers > 1 and self.midiLyricsEnabled == 1:
      self.midiLyricsEnabled = 0
    if self.numOfPlayers > 1 and self.midiSectionsEnabled == 1:
      self.midiSectionsEnabled = 0
    self.readTextAndLyricEvents = self.engine.config.get("game","rock_band_events")
    self.hopoDebugDisp = self.engine.config.get("game","hopo_debug_disp")
    if self.hopoDebugDisp == 1:
      for g, guitar in enumerate(self.guitars):
        if not guitar.isDrum:
          guitar.debugMode = True
    self.numDecimalPlaces = self.engine.config.get("game","decimal_places")
    self.decimal = decimal.Decimal
    self.decPlaceOffset = self.decimal(10) ** -(self.numDecimalPlaces)       # same as Decimal('0.01')
    #self.decOnePlace = self.decimal('0.01')
    self.starScoring = self.engine.config.get("game", "star_scoring")#MFH
    self.ignoreOpenStrums = self.engine.config.get("game", "ignore_open_strums") #MFH
    self.muteSustainReleases = self.engine.config.get("game", "sustain_muting") #MFH
    self.hopoIndicatorEnabled = self.engine.config.get("game", "hopo_indicator") #MFH
    self.fontShadowing = self.engine.config.get("game", "in_game_font_shadowing") #MFH
    self.muteLastSecond = self.engine.config.get("audio", "mute_last_second") #MFH
    self.mutedLastSecondYet = False
    self.starScoreUpdates = self.engine.config.get("performance", "star_score_updates") #MFH
    self.currentlyAnimating = True
    self.missPausesAnim = self.engine.config.get("game", "miss_pauses_anim") #MFH
    self.displayAllGreyStars = Theme.displayAllGreyStars
    self.starpowerMode = self.engine.config.get("game", "starpower_mode") #MFH
    self.logMarkerNotes = self.engine.config.get("game", "log_marker_notes")
    self.logStarpowerMisses = self.engine.config.get("game", "log_starpower_misses")
    self.soloFrameMode = self.engine.config.get("game", "solo_frame")
    self.whammyEffect = self.engine.config.get("audio",  "whammy_effect")
    if self.whammyEffect == 1 and not Audio.pitchBendSupported:    #pitchbend
      Dialogs.showMessage(self.engine, "Pitchbend module not found!  Forcing Killswitch effect.")
      self.whammyEffect = 0
    self.bigRockEndings = self.engine.config.get("game", "big_rock_endings")
    self.showFreestyleActive = self.engine.config.get("debug",   "show_freestyle_active")
    #stump: continuous star fillup
    self.starFillupCenterX = Theme.starFillupCenterX
    self.starFillupCenterY = Theme.starFillupCenterY
    self.starFillupInRadius = Theme.starFillupInRadius
    self.starFillupOutRadius = Theme.starFillupOutRadius
    self.starFillupColor = Theme.starFillupColor
    self.starContinuousAvailable = self.engine.config.get("performance", "star_continuous_fillup") and \
      None not in (self.starFillupCenterX, self.starFillupCenterY, self.starFillupInRadius, self.starFillupOutRadius, self.starFillupColor)
    




    #MFH - switch to midi lyric mode option
    self.midiLyricMode = self.engine.config.get("game", "midi_lyric_mode")
    #self.midiLyricMode = 0
    self.currentSimpleMidiLyricLine = ""
    self.noMoreMidiLineLyrics = False

    
    self.fontMode = self.engine.config.get("game", "font_rendering_mode")   #0 = oGL Hack, 1=LaminaScreen, 2=LaminaFrames
    self.laminaScreen = None
    if self.fontMode == 1:    #0 = oGL Hack, 1=LaminaScreen, 2=LaminaFrames
      #self.laminaScreen = lamina.LaminaScreenSurface(0.985)
      self.laminaScreen = lamina.LaminaScreenSurface(1.0)
      self.laminaScreen.clear()
      self.laminaScreen.refresh()
      self.laminaScreen.refreshPosition()
    elif self.fontMode == 2:    #0 = oGL Hack, 1=LaminaScreen, 2=LaminaFrames
      #self.laminaScreen = lamina.LaminaScreenSurface(0.985)
      self.laminaFrame_soloAcc = lamina.LaminaPanelSurface(quadDims=(-1,-1,500,500))
      self.laminaFrame_soloAcc.surf.fill( (0,0,255) )
      self.laminaFrame_soloAcc.refresh()


    self.screenCenterX = self.engine.video.screen.get_rect().centerx
    self.screenCenterY = self.engine.video.screen.get_rect().centery
  

    #racer: practice beat claps:
    self.beatClaps = self.engine.config.get("game", "beat_claps")
    

    self.killDebugEnabled = self.engine.config.get("game", "kill_debug")

    #myfingershurt: for checking if killswitch key is analog for whammy
    self.whammyVolAdjStep = 0.1
    self.analogKillMode = [self.engine.config.get("game", "analog_killsw_mode"),self.engine.config.get("game", "analog_killsw_mode_p2")]
    self.isKillAnalog = [False for i in self.playerList]
    self.whichJoy = [0 for i in self.playerList]
    self.whichAxis = [0 for i in self.playerList]
    self.whammyVol = [0.0 for i in self.playerList]
    self.targetWhammyVol = [0.0 for i in self.playerList]
    
    self.defaultWhammyVol = [self.analogKillMode[i]-1.0 for i, thePlayer in enumerate(self.playerList)]   #makes xbox defaults 1.0, PS2 defaults 0.0
    for i, thePlayer in enumerate(self.playerList):
      if self.analogKillMode[i] == 3:   #XBOX inverted mode
        self.defaultWhammyVol[i] = -1.0

    self.actualWhammyVol = [self.defaultWhammyVol[i] for i, thePlayer in enumerate(self.playerList)]
    
    self.lastWhammyVol = [self.defaultWhammyVol[i] for i, thePlayer in enumerate(self.playerList)]
    
    KillKeyCode = [0 for i in self.playerList]
    self.lastTapText = "tapp: -"

    #myfingershurt: auto drum starpower activation option
    #self.autoDrumStarpowerActivate = self.engine.config.get("game", "auto_drum_sp")
    self.autoDrumStarpowerActivate = self.engine.config.get("game", "drum_sp_mode")

    self.numDrumFills = 0   #MFH - count drum fills to see whether or not we should use auto SP

    #MFH - TODO - rewrite in an expandable fashion; requires creation of some new Player object constants that will link to the appropriate player's control based on which player the object is set to
    if self.analogKillMode[0] > 0:
      KillKeyCode[0] = self.controls.getReverseMapping(Player.KILL)
      self.isKillAnalog[0], self.whichJoy[0], self.whichAxis[0] = self.engine.input.getWhammyAxis(KillKeyCode[0])
    if self.numOfPlayers > 1 and self.analogKillMode[1] > 0:
      KillKeyCode[1] = self.controls.getReverseMapping(Player.PLAYER_2_KILL)
      self.isKillAnalog[1], self.whichJoy[1], self.whichAxis[1] = self.engine.input.getWhammyAxis(KillKeyCode[1])


    self.inGameStats = self.engine.config.get("performance","in_game_stats")
    self.inGameStars = self.engine.config.get("game","in_game_stars")
    self.partialStars = self.engine.config.get("game","partial_stars")

    
    self.guitarSoloAccuracyDisplayMode = self.engine.config.get("game", "gsolo_accuracy_disp")
    self.guitarSoloAccuracyDisplayPos = self.engine.config.get("game", "gsolo_acc_pos")
    
    #need a new flag for each player, showing whether or not they've missed a note during a solo section.
    #this way we have a backup detection of Perfect Solo in case a note got left out, picks up the other side of the solo slop
    self.guitarSoloBroken = [False for i in self.playerList]


    self.deadPlayerList = [] #akedrou - keep the order failed.
    self.numDeadPlayers = 0
    coOpInstruments = []
    self.scoring = [None for i in self.playerList]
    #self.stars = [0,0]
    for i, thePlayer in enumerate(self.playerList):   
      if self.guitars[i].isDrum:
        instrument = Song.DRUM_PART
        coOpInstruments.append(instrument)
      elif self.guitars[i].isBassGuitar:
        instrument = Song.BASS_PART
        coOpInstruments.append(instrument)
      else:
        instrument = Song.GUITAR_PART #while different guitars exist, they don't affect scoring.
        coOpInstruments.append(instrument)
      self.scoring[i] = Scorekeeper.ScoreCard([instrument])
    if self.coOpType:
      self.coOpScoreCard = Scorekeeper.ScoreCard(coOpInstruments, coOpType = True)
    else:
      self.coOpScoreCard = None
    
    self.partialStar = [0 for i in self.playerList]
    self.starRatio = [0.0 for i in self.playerList]
    self.dispSoloReview = [False for i in self.playerList]
    self.soloReviewText = [[] for i in self.playerList]
    self.soloReviewCountdown = [0 for i in self.playerList]
    self.guitarSoloAccuracy = [0.0 for i in self.playerList]
    self.guitarSoloActive = [False for i in self.playerList]
    self.currentGuitarSolo = [0 for i in self.playerList]

    #guitar solo display initializations
    if self.theme == 2:
      self.solo_soloFont = self.engine.data.scoreFont
    else:
      self.solo_soloFont = self.engine.data.font

    self.guitarSoloShown = [False for i in self.playerList]
    self.currentGuitarSoloLastHitNotes = [1 for i in self.playerList]
    self.solo_xOffset = [0.0 for i in self.playerList]
    self.solo_yOffset = [0.0 for i in self.playerList]
    self.solo_boxXOffset = [0.0 for i in self.playerList]
    self.solo_boxYOffset = [0.0 for i in self.playerList]
    self.solo_Tw = [0.0 for i in self.playerList]
    self.solo_Th = [0.0 for i in self.playerList]
    self.solo_soloText = ["solo" for i in self.playerList]
    self.soloAcc_Rect = [None for i in self.playerList]
    self.solo_txtSize = 0.00250
    for i, playa in enumerate(self.playerList):
      if self.guitarSoloAccuracyDisplayPos == 0:    #right
        if self.guitarSoloAccuracyDisplayMode == 1:   #percentage only
          self.solo_xOffset[i] = 0.890
        else:
          self.solo_xOffset[i] = 0.950
      else:
        self.solo_xOffset[i] = 0.150
      self.solo_yOffset[i] = 0.320   #last change -.040


    #self.totalNotes = [0,0]
    #self.totalSingleNotes = [0,0]
    self.currentGuitarSoloTotalNotes = [0 for i in self.playerList]
    #self.currentGuitarSoloHitNotes = [0,0]
    self.guitarSolos = [ [] for i in self.playerList]
    guitarSoloStartTime = 0
    isGuitarSoloNow = False
    guitarSoloNoteCount = 0
    lastSoloNoteTime = 0
    self.drumStart = False
    soloSlop = 100.0
    unisonCheck = []

    if self.careerMode:
      self.failingEnabled = True


    self.tut = self.engine.config.get("game", "tut")
    

    #MFH - no Jurgen in Career mode or tutorial mode or practice mode:
    if self.careerMode or self.tut or self.playerList[0].practiceMode:
      self.autoPlay = False

    
    self.rockFailUp  = True #akedrou - fading mech
    self.rockFailViz = 0.0
    self.failViz = [0.0 for i in self.playerList]
    
    self.phrases = self.engine.config.get("coffee", "game_phrases")#blazingamer
    self.starfx = self.engine.config.get("game", "starfx")#blazingamer
    smallMult = self.engine.config.get("game","small_rb_mult")
    self.rbmfx = False
    if smallMult == 2 or (smallMult == 1 and Theme.smallMult):
      self.rbmfx = True
    self.boardY = 2
    self.rbOverdriveBarGlowVisibility = 0
    self.rbOverdriveBarGlowFadeOut = False
    self.counting = self.engine.config.get("video", "counting")





    #MFH - this is where song loading originally took place, and the loading screen was spawned.
    self.engine.resource.load(self, "song", lambda: loadSong(self.engine, songName, library = libraryName, part = [player.part for player in self.playerList], practiceMode = self.playerList[0].practiceMode), synch = True, onLoad = self.songLoaded)

    #myfingershurt: new loading place for "loading" screen for song preparation:
    #blazingamer new loading phrases
    phrase = self.song.info.loading
    if phrase == "":
      phrase = random.choice(Theme.loadingPhrase.split("_"))
      if phrase == "None":
        i = random.randint(0,4)
        if i == 0:
          phrase = "Let's get this show on the Road"
        elif i == 1:
          phrase = "Impress the Crowd"
        elif i == 2:
          phrase = "Don't forget to strum!"
        elif i == 3:
          phrase = "Rock the house!"
        else:
          phrase = "Jurgen is watching"
    # glorandwarf: show the loading splash screen and load the song synchronously
    Dialogs.hideLoadingSplashScreen(self.engine, splash)
    splash = None
    splash = Dialogs.showLoadingSplashScreen(self.engine, phrase)



    if self.playerList[0].practiceMode or self.song.info.tutorial or self.tut:
      self.failingEnabled = False



    self.playerList[0].hopoFreq = self.song.info.hopofreq
    
    bassGrooveEnableSet = self.engine.config.get("game", "bass_groove_enable")
    if bassGrooveEnableSet == 1 and self.theme == 2:
      self.bassGrooveEnabled = True
    elif bassGrooveEnableSet == 2 and self.song.midiStyle == Song.MIDI_TYPE_RB:
      self.bassGrooveEnabled = True
    elif bassGrooveEnableSet == 3:
      self.bassGrooveEnabled = True
    else:
      self.bassGrooveEnabled = False
      
    for scoreCard in self.scoring:
      scoreCard.bassGrooveEnabled = self.bassGrooveEnabled

    #MFH - single audio track song detection
    self.isSingleAudioTrack = self.song.isSingleAudioTrack


    #myfingershurt: also want to go through song and search for guitar solo parts, and count notes in them in each diff.


    #MFH - now, handle MIDI starpower / overdrive / other special marker notes:
    
    #MFH - first, count the markers for each instrument.  If a particular instrument does not have at least two starpower phrases 
    #  marked, ignore them and force auto-generation of SP paths.
    
    for i, guitar in enumerate(self.guitars):   #MFH - count number of drum fills
      if guitar.isDrum:   #MFH - count number of drum fill markers
        self.numDrumFills = len([1 for time, event in self.song.midiEventTrack[i].getAllEvents() if (isinstance(event, Song.MarkerNote) and (event.number == Song.freestyleMarkingNote) ) ])
        Log.debug("Drum part found, scanning for drum fills.... %d freestyle markings found (the last one may be a Big Rock Ending)." % self.numDrumFills)
    

    #MFH - handle early hit window automatic type determination, and how it compares to the forced handicap if not auto
    self.effectiveEarlyHitWindow = Song.EARLY_HIT_WINDOW_HALF
    self.automaticEarlyHitWindow = Song.EARLY_HIT_WINDOW_HALF
    self.forceEarlyHitWindowSetting = self.engine.config.get("handicap",   "early_hit_window")
    if self.song.info.early_hit_window_size:
      Log.debug("song.ini setting found speficying early_hit_window_size - %s" % self.song.info.early_hit_window_size)
      if self.song.info.early_hit_window_size.lower() == "none":
        self.automaticEarlyHitWindow = Song.EARLY_HIT_WINDOW_NONE
      elif self.song.info.early_hit_window_size.lower() == "half":
        self.automaticEarlyHitWindow = Song.EARLY_HIT_WINDOW_HALF
      #elif self.song.info.early_hit_window_size.lower() == "full":
      else:  #all other unrecognized cases, default to "full"
        self.automaticEarlyHitWindow = Song.EARLY_HIT_WINDOW_FULL

    else:
      Log.debug("No song.ini setting found speficying early_hit_window_size - using automatic detection...")

      if self.song.midiStyle == Song.MIDI_TYPE_RB:
        Log.debug("Basic RB1/RB2 type MIDI found - early hitwindow of NONE is set as handicap base.")
        self.automaticEarlyHitWindow = Song.EARLY_HIT_WINDOW_NONE

    if self.forceEarlyHitWindowSetting > 0:   #MFH - if user is specifying a specific early hitwindow, then calculate handicap...
      self.effectiveEarlyHitWindow = self.forceEarlyHitWindowSetting
      tempHandicap = 1.00
      if self.automaticEarlyHitWindow > self.effectiveEarlyHitWindow:   #MFH - positive handicap
        tempHandicap += ( (self.automaticEarlyHitWindow - self.effectiveEarlyHitWindow) * 0.05 )
      elif self.automaticEarlyHitWindow < self.effectiveEarlyHitWindow:   #MFH - negative handicap
        tempHandicap -= ( (self.effectiveEarlyHitWindow - self.automaticEarlyHitWindow) * 0.05 )
      for scoreCard in self.scoring:
        scoreCard.earlyHitWindowSizeHandicap = tempHandicap
      if self.coOpType:
        self.coOpScoreCard.earlyHitWindowSizeHandicap = tempHandicap
      Log.debug("User-forced early hit window setting %d, effective handicap determined: %f" % (self.forceEarlyHitWindowSetting,tempHandicap) )

    else:
      Log.debug("Automatic early hit window mode - automatically-detected setting used: %d" % self.automaticEarlyHitWindow)
      self.effectiveEarlyHitWindow = self.automaticEarlyHitWindow

    tempEarlyHitWindowSizeFactor = 0.5
    if self.effectiveEarlyHitWindow == 1:     #none
      tempEarlyHitWindowSizeFactor = 0.10     #really, none = about 10%
    elif self.effectiveEarlyHitWindow == 2:   #half
      tempEarlyHitWindowSizeFactor = 0.5
    else:                                     #any other value will be full
      tempEarlyHitWindowSizeFactor = 1.0
    
    for theGuitar in self.guitars:    #MFH - force update of early hit window
      theGuitar.earlyHitWindowSizeFactor = tempEarlyHitWindowSizeFactor
      theGuitar.actualBpm = 0.0
      theGuitar.currentBpm = 120.0
      theGuitar.setBPM(theGuitar.currentBpm)

    #if self.starpowerMode == 2:     #auto-MIDI mode only
    if self.song.hasStarpowerPaths:
      for i,guitar in enumerate(self.guitars):

        #MFH - first, count the SP marker notes!
        numOfSpMarkerNotes = len([1 for time, event in self.song.midiEventTrack[i].getAllEvents() if (isinstance(event, Song.MarkerNote) and not event.endMarker and (event.number == Song.overDriveMarkingNote or (event.number == Song.starPowerMarkingNote and self.song.midiStyle == Song.MIDI_TYPE_GH) ) ) ])

        
        #also want to count RB solo sections in this track, if the MIDI type is RB.  Then we'll know to activate MIDI guitar solo markers or not 
        # for this instrument
        if self.song.midiStyle == Song.MIDI_TYPE_RB:
          numMidiSoloMarkerNotes = len([1 for time, event in self.song.midiEventTrack[i].getAllEvents() if (isinstance(event, Song.MarkerNote) and not event.endMarker and event.number == Song.starPowerMarkingNote ) ])          
          if numMidiSoloMarkerNotes > 0:  #if at least 1 solo marked in this fashion, tell that guitar to ignore text solo events
            guitar.useMidiSoloMarkers = True
            
        if numOfSpMarkerNotes > 1:
        
          for time, event in self.song.midiEventTrack[i].getAllEvents():
            if isinstance(event, Song.MarkerNote) and not event.endMarker:
              markStarpower = False
              if event.number == Song.overDriveMarkingNote:
                markStarpower = True
              if event.number == Song.starPowerMarkingNote:
                if self.song.midiStyle == Song.MIDI_TYPE_GH:
                  markStarpower = True
                #else:  #RB solo marking!
              
              if markStarpower and self.starpowerMode == 2:     #auto-MIDI mode only:
                tempStarpowerNoteList = self.song.track[i].getEvents(time, time+event.length) 
                self.spTimes[i].append((time,time+event.length))
                lastSpNoteTime = 0
                for spTime, spEvent in tempStarpowerNoteList:
                  if isinstance(spEvent, Note):
                    if spTime > lastSpNoteTime:
                      lastSpNoteTime = spTime
                    spEvent.star = True
                #now, go back and mark all of the last chord as finalStar
                #   BUT only if not drums!  If drums, mark only ONE of the last notes!
                #lastChordTime = spTime
                oneLastSpNoteMarked = False
                for spTime, spEvent in tempStarpowerNoteList:
                  if isinstance(spEvent, Note):
                    if spTime == lastSpNoteTime:
                      if (guitar.isDrum and not oneLastSpNoteMarked) or (not guitar.isDrum):
                        spEvent.finalStar = True
                        oneLastSpNoteMarked = True
                if self.logMarkerNotes == 1:
                  Log.debug("GuitarScene: P%d overdrive / starpower phrase marked between %f and %f" % ( i+1, time, time+event.length ) )
                  if lastSpNoteTime == 0:
                    Log.warn("This starpower phrase doesn't appear to have any finalStar notes marked... probably will not reward starpower!")
          self.midiSP = True
          unisonCheck.extend(self.spTimes[i])
        
        elif self.starpowerMode == 2: #this particular instrument only has one starpower path marked!  Force auto-generation of SP paths.            
          Log.warn("Instrument %s only has one starpower path marked!  ...falling back on auto-generated paths for this instrument." % self.playerList[i].part.text)
          guitar.starNotesSet = False     #fallback on auto generation.
    
    elif self.starpowerMode == 2:
      Log.warn("This song does not appear to have any starpower or overdrive paths marked, falling back on auto-generated paths.")
      for guitar in self.guitars:
        guitar.starNotesSet = False     #fallback on auto generation.

    
    
    
    
    self.lastDrumNoteTime = 0.0
    self.lastNoteTimes = [0.0 for i in self.playerList]
    #self.lastDrumNoteEvent = None
    self.drumScoringEnabled = True
    
    
    #count / init solos
    for i,guitar in enumerate(self.guitars):
      #MFH - go through, locate, and mark the last drum note.  When this is encountered, drum scoring should be turned off.
      lastDrumNoteTime = 0.0
      lastDrumNoteEvent = None
      for time, event in self.song.track[i].getAllEvents():
        if isinstance(event, Note):
          if time >= lastDrumNoteTime:
            lastDrumNoteTime = time
            lastDrumNoteEvent = event
      if guitar.isDrum:
        self.lastDrumNoteTime = lastDrumNoteTime
        Log.debug("Last drum note located at time = " + str(self.lastDrumNoteTime) )
        #self.lastDrumNoteEvent = lastDrumNoteEvent

        self.scoring[i].totalStreakNotes = len([1 for time, event in self.song.track[i].getAllEvents() if isinstance(event, Note)])
      else:
        self.scoring[i].totalStreakNotes = len(set(time for time, event in self.song.track[i].getAllEvents() if isinstance(event, Note)))
      self.scoring[i].lastNoteEvent = lastDrumNoteEvent
      self.scoring[i].lastNoteTime  = lastDrumNoteTime
      self.lastNoteTimes[i] = lastDrumNoteTime
      if lastDrumNoteEvent:
        Log.debug("Last note (number %d) found for player %d at time %f" % (lastDrumNoteEvent.number, i, lastDrumNoteTime) )
      else:
        Log.debug("Last note event not found and is None!")


#-      #volshebnyi - don't count notes in BRE zones if BRE active
#-      if guitar.freestyleEnabled:
#-        self.playerList[i].freestyleSkippedNotes = 0
#-        for time, event in self.song.midiEventTrack[i].getAllEvents():
#-          if isinstance(event, Song.MarkerNote) and not event.endMarker:
#-              if (event.number == Song.freestyleMarkingNote):
#-                if guitar.isDrum:
#-                    guitar.drumFillsTotal += 1
#-                else:
#-                  for freestyleTime, event1 in self.song.track[i].getEvents(time, time + event.length):
#-                    if isinstance(event1, Note):
#-                      self.playerList[i].freestyleSkippedNotes += 1
#-
#-      self.playerList[i].totalStreakNotes -= self.playerList[i].freestyleSkippedNotes


      self.scoring[i].totalNotes = len([1 for Ntime, event in self.song.track[i].getAllEvents() if isinstance(event, Note)])
      
      if guitar.useMidiSoloMarkers:   #mark using the new MIDI solo marking system
        for time, event in self.song.midiEventTrack[i].getAllEvents():
          if isinstance(event, Song.MarkerNote) and not event.endMarker:
            if (event.number == Song.starPowerMarkingNote) and (self.song.midiStyle == Song.MIDI_TYPE_RB):    #solo marker note.
              startTime = time
              endTime = time + event.length
              guitarSoloNoteCount = len([1 for Gtime, Gevent in self.song.track[i].getEvents(startTime, endTime) if isinstance(Gevent, Note)])
              self.guitarSolos[i].append(guitarSoloNoteCount - 1)
              Log.debug("P" + str(i+1) + " MIDI " + self.playerList[i].part.text + " Solo found from: " + str(startTime) + " to: " + str(endTime) + ", containing " + str(guitarSoloNoteCount) + " notes." )
        
      else:   #mark using the old text-based system
      
        #Ntime now should contain the last note time - this can be used for guitar solo finishing
        #MFH - use new self.song.eventTracks[Song.TK_GUITAR_SOLOS] -- retrieve a gsolo on / off combo, then use it to count notes
        # just like before, detect if end reached with an open solo - and add a GSOLO OFF event just before the end of the song.
        for time, event in self.song.eventTracks[Song.TK_GUITAR_SOLOS].getAllEvents():
          if event.text.find("GSOLO") >= 0:
            if event.text.find("ON") >= 0:
              isGuitarSoloNow = True
              guitarSoloStartTime = time
            else:
              isGuitarSoloNow = False
              guitarSoloNoteCount = len([1 for Gtime, Gevent in self.song.track[i].getEvents(guitarSoloStartTime, time) if isinstance(Gevent, Note)])
              self.guitarSolos[i].append(guitarSoloNoteCount - 1)
              Log.debug("GuitarScene: Guitar Solo found: " + str(guitarSoloStartTime) + "-" + str(time) + " = " + str(guitarSoloNoteCount) )
        if isGuitarSoloNow:   #open solo until end - needs end event!
          isGuitarSoloNow = False
          #guitarSoloNoteCount = len([1 for Gtime, Gevent in self.song.track[i].getEvents(guitarSoloStartTime, time) if isinstance(Gevent, Note)])
          #MFH - must find the real "last note" time, requires another iteration...
          for lnTime, lnEvent in self.song.track[i].getAllEvents():
            if isinstance(lnEvent, Note):
              if lnTime > Ntime:
                Ntime = lnTime
          #Ntime = Ntime + soloSlop
          guitarSoloNoteCount = len([1 for Gtime, Gevent in self.song.track[i].getEvents(guitarSoloStartTime, Ntime) if isinstance(Gevent, Note)])
          self.guitarSolos[i].append(guitarSoloNoteCount - 1)
          newEvent = TextEvent("GSOLO OFF", 100.0)
          #self.song.eventTracks[Song.TK_GUITAR_SOLOS].addEvent(time - soloSlop,newEvent) #adding the missing GSOLO OFF event
          self.song.eventTracks[Song.TK_GUITAR_SOLOS].addEvent(Ntime, newEvent) #adding the missing GSOLO OFF event
          Log.debug("GuitarScene: Guitar Solo until end of song found - (guitarSoloStartTime - Ntime = guitarSoloNoteCount): " + str(guitarSoloStartTime) + "-" + str(Ntime) + " = " + str(guitarSoloNoteCount) )
    


    self.unisonConfirm = [] #akedrou
    self.unisonPlayers = []
    self.unisonIndex = 0
    if self.coOpRB:
      for spNoted in unisonCheck:
        if unisonCheck.count(spNoted) > 1:
          if not spNoted in self.unisonConfirm:
            self.unisonConfirm.append(spNoted)
      if len(self.unisonConfirm) > 0:
        self.unisonPlayers = [[] for i in self.unisonConfirm]
        for i in range(len(self.unisonConfirm)):
          for j in range(len(self.spTimes)):
            if self.unisonConfirm[i] in self.spTimes[j]:
              self.unisonPlayers[i].append(j)
        Log.debug("Unisons confirmed: " + str(self.unisonConfirm))
        Log.debug("Unisons between: " + str(self.unisonPlayers))
        
        
    #MFH - handle gathering / sizing / grouping line-by-line lyric display here, during initialization:
    self.midiLyricLineEvents = []    #MFH - this is a list of sublists of tuples.
                                # The tuples will contain (time, event)  
                                # The sublists will contain:
                                #   references to Lyric text events that will be treated as lines
                                #    such that the game can still use song position to determine each text event's color 
    self.midiLyricLines = []        #MFH - this is a list of text strings
                                    #  it will contain a list of the concactenated midi lines for a simpler lyric display mode
    self.nextMidiLyricLine = ""
    self.lyricHeight = 0

    if self.midiLyricsEnabled > 0 and (self.midiLyricMode == 1 or self.midiLyricMode == 2):   #line-by-line lyrics mode is selected and enabled:
      lyricFont = self.engine.data.font
      if self.theme == 2:
        txtSize = 0.00170
      else:
        txtSize = 0.00175
      self.lyricHeight = lyricFont.getStringSize("A", scale = txtSize)[1]

      #MFH - now we need an appropriate array to store and organize the lyric events into "lines"
      #  -- the first attempt at coding this will probably butcher the measures and timing horribly, but at least
      #     those of us with older systems can read the lyrics without them jumping all over the place.
      tempLyricLine = ""
      tempLyricLineEvents = []
      firstTime = None
      for time, event in self.song.eventTracks[Song.TK_LYRICS].getAllEvents():
        if not firstTime:
          firstTime = time
        lastLyricLineContents = tempLyricLine
        tempLyricLine = tempLyricLine + " " + event.text
        if lyricFont.getStringSize(tempLyricLine, scale = txtSize)[0] > self.lineByLineLyricMaxLineWidth: 
          self.midiLyricLineEvents.append(tempLyricLineEvents)
          self.midiLyricLines.append( (firstTime, lastLyricLineContents) )
          firstTime = None
          tempLyricLine = event.text
          tempLyricLineEvents = []
        tempLyricLineEvents.append( (time, event) )
      else:   #after last line is accumulated
        if len(self.midiLyricLines) > 0:
          self.midiLyricLineEvents.append(tempLyricLineEvents)
          self.midiLyricLines.append( (firstTime, tempLyricLine) )
      



      
      #MFH - test unpacking / decoding the lyrical lines:
      for midiLyricSubList in self.midiLyricLineEvents:
        Log.debug("...New MIDI lyric line:")
        for lyricTuple in midiLyricSubList:
          time, event = lyricTuple
          Log.debug("MIDI Line-by-line lyric unpack test - time, event = " + str(time) + ", " + event.text )
              
      for lineStartTime, midiLyricSimpleLineText in self.midiLyricLines:
        Log.debug("MIDI Line-by-line simple lyric line starting at time: " + str(lineStartTime) + ", " + midiLyricSimpleLineText)

    self.numMidiLyricLines = len(self.midiLyricLines)


    #self.initializeStarScoringThresholds()    #MFH
    self.coOpTotalStreakNotes = 0
    self.coOpTotalNotes = 0
    coOpTotalStreakNotes = 0
    coOpTotalNotes = 0
    self.star = [{} for i in self.playerList]
    if self.coOpScoreCard:
      self.coOpScoreCard.lastNoteTime  = max(self.lastNoteTimes)
      Log.debug("Last note for co-op mode found at %.2f" % self.coOpScoreCard.lastNoteTime)
    for i, scoreCard in enumerate(self.scoring):   #accumulate base scoring values for co-op
      if self.coOpScoreCard:
        self.coOpScoreCard.totalStreakNotes += scoreCard.totalStreakNotes
        self.coOpScoreCard.totalNotes += scoreCard.totalNotes
    self.coOpPlayerIndex = len(self.playerList)

    #glorandwarf: need to store the song's beats per second (bps) for later
    self.songBPS = self.song.bpm / 60.0

    # evilynux - Load stage background(s)
    self.stage.load(self.libraryName, self.songName, self.playerList[0].practiceMode)

    #MFH - this determination logic should happen once, globally -- not repeatedly.
    self.showScriptLyrics = False
    if self.song.hasMidiLyrics and self.lyricMode == 3: #racer: new option for double lyrics
      self.showScriptLyrics = False
    elif not self.song.hasMidiLyrics and self.lyricMode == 3: #racer
      self.showScriptLyrics = True
    elif self.song.info.tutorial:
      self.showScriptLyrics = True
    elif self.lyricMode == 1 and self.song.info.lyrics:   #lyrics: song.ini
      self.showScriptLyrics = True
    elif self.lyricMode == 2:   #lyrics: Auto
      self.showScriptLyrics = True
    
    



    #lyric sheet!
    if self.readTextAndLyricEvents == 2 or (self.readTextAndLyricEvents == 1 and self.theme == 2):
      if self.song.hasMidiLyrics and self.midiLyricsEnabled > 0:
        if self.midiLyricMode == 0:
          try:
            self.engine.loadImgDrawing(self, "lyricSheet", os.path.join("themes",themename,"lyricsheet.png"))
          except IOError:
            self.lyricSheet = None
        else:
          try:
            self.engine.loadImgDrawing(self, "lyricSheet", os.path.join("themes",themename,"lyricsheet2.png"))
          except IOError:
            try:
              self.engine.loadImgDrawing(self, "lyricSheet", os.path.join("themes",themename,"lyricsheet.png"))
            except IOError:
              self.lyricSheet = None
      else:
        self.lyricSheet = None
    else:
      self.lyricSheet = None


    if self.lyricSheet:
      imgwidth = self.lyricSheet.width1()
      self.lyricSheetScaleFactor = 640.000/imgwidth
      

    #brescorebackground.png
    try:
      self.engine.loadImgDrawing(self, "breScoreBackground", os.path.join("themes",themename,"brescorebackground.png"))
      breScoreBackgroundImgwidth = self.breScoreBackground.width1()
      self.breScoreBackgroundWFactor = 640.000/breScoreBackgroundImgwidth
    except IOError:
      Log.debug("BRE score background image loading problem!")
      self.breScoreBackground = None
      self.breScoreBackgroundWFactor = None

    #brescoreframe.png
    try:
      self.engine.loadImgDrawing(self, "breScoreFrame", os.path.join("themes",themename,"brescoreframe.png"))
      breScoreFrameImgwidth = self.breScoreFrame.width1()
      self.breScoreFrameWFactor = 640.000/breScoreFrameImgwidth
    except IOError:

      try:    #MFH - fallback on using soloframe.png if no brescoreframe.png is found
        self.engine.loadImgDrawing(self, "breScoreFrame", os.path.join("themes",themename,"soloframe.png"))
        breScoreFrameImgwidth = self.breScoreFrame.width1()
        self.breScoreFrameWFactor = 640.000/breScoreFrameImgwidth
      except IOError:
        self.breScoreFrame = None
        self.breScoreFrameWFactor = None


    
    try:
      self.engine.loadImgDrawing(self, "soloFrame", os.path.join("themes",themename,"soloframe.png"))
      soloImgwidth = self.soloFrame.width1()
      self.soloFrameWFactor = 640.000/soloImgwidth
      #soloImgheight = self.soloFrame.height1()
      #soloHeightYFactor = (640.000*self.hFull)/self.wFull
      #self.soloFrameHFactor = soloHeightYFactor/soloImgheight
    except IOError:
      self.soloFrame = None
      self.soloFrameWFactor = None
      #self.soloFrameHFactor = None


    self.partImage = True
    self.part = [None for i in self.playerList]
    self.partLoad = None
    if self.counting or self.coOpType:
      for i, thePlayer in enumerate(self.playerList):
        if not self.partImage:
          break
        try:
          if self.guitars[i].isDrum:
            self.engine.loadImgDrawing(self, "partLoad", os.path.join("themes",themename,"drum.png"))
          elif self.guitars[i].isBassGuitar:
            self.engine.loadImgDrawing(self, "partLoad", os.path.join("themes",themename,"bass.png"))
          else:
            self.engine.loadImgDrawing(self, "partLoad", os.path.join("themes",themename,"guitar.png"))
        except IOError:
          try:
            if self.guitars[i].isDrum:
              self.engine.loadImgDrawing(self, "partLoad", os.path.join("drum.png"))
            elif self.guitars[i].isBassGuitar:
              self.engine.loadImgDrawing(self, "partLoad", os.path.join("bass.png"))
            else:
              self.engine.loadImgDrawing(self, "partLoad", os.path.join("guitar.png"))
          except IOError:
            self.counting = False
            self.partImage = False
        if self.partLoad:
          self.part[i] = self.partLoad

    self.partLoad = None

    if self.soloFrameMode == 0:
      self.soloFrame = None
      #self.soloFrameHFactor = None
      self.soloFrameWFactor = None
      

    if self.rmtype == 0:

      #starpower
      self.engine.loadImgDrawing(self, "oTop", os.path.join("themes",themename,"sptop.png"))
      self.engine.loadImgDrawing(self, "oBottom", os.path.join("themes",themename,"spbottom.png"))
      self.engine.loadImgDrawing(self, "oFill", os.path.join("themes",themename,"spfill.png"))
      self.engine.loadImgDrawing(self, "oFull", os.path.join("themes",themename,"spfull.png"))
      
      #Pause Screen
      self.engine.loadImgDrawing(self, "pauseScreen", os.path.join("themes",themename,"pause.png"))
      self.engine.loadImgDrawing(self, "failScreen", os.path.join("themes",themename,"fail.png"))
      #Rockmeter
      self.engine.loadImgDrawing(self, "rockmeter", os.path.join("themes",themename,"rockmeter.png"))
      self.engine.loadImgDrawing(self, "counter", os.path.join("themes",themename,"counter.png"))
      #Multiplier
      #if self.playerList[0].part.text == "Bass Guitar": #kk69: uses multb.png for mult.png specifically for bass

      #MFH - TODO - rewrite all this bass guitar multiplier code to be more expandable, and create a "mult" object for each player instead of sharing one (so 2 player will show up one bass mult correctly)
      if self.guitars[0].isBassGuitar: #kk69: uses multb.png for mult.png specifically for bass
        try:
          self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"multb.png"))
        except IOError:
          self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"mult.png"))
      else:
        self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"mult.png"))

      if self.numOfPlayers > 1:
        #if self.playerList[1].part.text == "Bass Guitar":
        if self.guitars[1].isBassGuitar:
          try:
            self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"multb.png"))
          except IOError:
            self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"mult.png"))
        else:
          self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"mult.png"))#end kk69
      #death_au: Bass groove multiplier (with fall-back logic)
      try:
        self.engine.loadImgDrawing(self, "bassgroovemult", os.path.join("themes",themename,"bassgroovemult.png"))
      except IOError:
        self.bassgroovemult = None
      
      self.engine.loadImgDrawing(self, "basedots", os.path.join("themes",themename,"dots","basedots.png"))
      self.engine.loadImgDrawing(self, "dt1", os.path.join("themes",themename,"dots","dt1.png"))
      self.engine.loadImgDrawing(self, "dt2", os.path.join("themes",themename,"dots","dt2.png"))
      self.engine.loadImgDrawing(self, "dt3", os.path.join("themes",themename,"dots","dt3.png"))
      self.engine.loadImgDrawing(self, "dt4", os.path.join("themes",themename,"dots","dt4.png"))
      self.engine.loadImgDrawing(self, "dt5", os.path.join("themes",themename,"dots","dt5.png"))
      self.engine.loadImgDrawing(self, "dt6", os.path.join("themes",themename,"dots","dt6.png"))
      self.engine.loadImgDrawing(self, "dt7", os.path.join("themes",themename,"dots","dt7.png"))
      self.engine.loadImgDrawing(self, "dt8", os.path.join("themes",themename,"dots","dt8.png"))
      self.engine.loadImgDrawing(self, "dt9", os.path.join("themes",themename,"dots","dt9.png"))
      self.engine.loadImgDrawing(self, "dt10", os.path.join("themes",themename,"dots","dtfull.png"))
      
      #rockmeter
      self.engine.loadImgDrawing(self, "rockHi", os.path.join("themes",themename,"rock_hi.png"))
      self.engine.loadImgDrawing(self, "rockLo", os.path.join("themes",themename,"rock_low.png"))
      self.engine.loadImgDrawing(self, "rockMed", os.path.join("themes",themename,"rock_med.png"))
      self.engine.loadImgDrawing(self, "arrow", os.path.join("themes",themename,"rock_arr.png"))
      self.engine.loadImgDrawing(self, "rockTop", os.path.join("themes",themename,"rock_top.png"))
      #failMessage
      self.engine.loadImgDrawing(self, "failMsg", os.path.join("themes",themename,"youfailed.png"))
      #myfingershurt: youRockMessage
      self.engine.loadImgDrawing(self, "rockMsg", os.path.join("themes",themename,"yourock.png"))


    elif self.rmtype == 1 or self.rmtype == 3:
      #Pause Screen
      self.engine.loadImgDrawing(self, "pauseScreen", os.path.join("themes",themename,"pause.png"))
      self.engine.loadImgDrawing(self, "failScreen", os.path.join("themes",themename,"fail.png"))
      #Rockmeter
      if self.coOpType:
        try:
          self.engine.loadImgDrawing(self, "coopRockmeter", os.path.join("themes",themename,"coop_rockmeter.png"))
        except IOError:
          self.coopRockmeter = None
          Log.warn("No valid co-op rockmeter found. Weirdness ensuing.")
        try:
          self.engine.loadImgDrawing(self, "rockTop", os.path.join("themes",themename,"coop_rock_top.png"))
        except IOError:
          self.rockTop   = None
          Log.warn("No valid co-op rock top found. Continuing without display!")
        try:
          self.engine.loadImgDrawing(self, "counter", os.path.join("themes",themename,"coop_counter.png"))
        except IOError:
          self.engine.loadImgDrawing(self, "counter", os.path.join("themes",themename,"counter.png"))
      else:
        self.engine.loadImgDrawing(self, "rockTop", os.path.join("themes",themename,"rock_top.png"))
        self.engine.loadImgDrawing(self, "counter", os.path.join("themes",themename,"counter.png"))
      
      self.engine.loadImgDrawing(self, "rockmeter", os.path.join("themes",themename,"rockmeter.png"))

      #Multiplier
      #if self.playerList[0].part.text == "Bass Guitar": #kk69: uses multb.png for mult.png specifically for bass
      if self.guitars[0].isBassGuitar: #kk69: uses multb.png for mult.png specifically for bass
        try:
          self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"multb.png"))
        except IOError:
          self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"mult.png"))
      else:
        self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"mult.png"))

      if self.numOfPlayers > 1:
        #if self.playerList[1].part.text == "Bass Guitar":
        if self.guitars[1].isBassGuitar:
          try:
            self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"multb.png"))
          except IOError:
            self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"mult.png"))
        else:
          self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"mult.png"))#end kk69
      #death_au: Bass groove multiplier (with fall-back logic)
      try:
        self.engine.loadImgDrawing(self, "bassgroovemult", os.path.join("themes",themename,"bassgroovemult.png"))
      except IOError:
        self.bassgroovemult = None
      
      
      #dots
      #myfingershurt: determine which type of dots are included with this theme - dots.png = 10 small dots, dotshalf.png = 5 larger dots with half-dot increments
      self.halfDots = True
      if self.coOpType:
        try:
          try:
            self.engine.loadImgDrawing(self, "dots", os.path.join("themes",themename,"coop_dotshalf.png"))
          except IOError:
            self.engine.loadImgDrawing(self, "dots", os.path.join("themes",themename,"coop_dots.png"))
            self.halfDots = False
        except IOError:
          try:
            self.engine.loadImgDrawing(self, "dots", os.path.join("themes",themename,"dotshalf.png"))
          except IOError:
            self.engine.loadImgDrawing(self, "dots", os.path.join("themes",themename,"dots.png"))
            self.halfDots = False
      else:
        try:
          self.engine.loadImgDrawing(self, "dots", os.path.join("themes",themename,"dotshalf.png"))
        except IOError:
          self.engine.loadImgDrawing(self, "dots", os.path.join("themes",themename,"dots.png"))
          self.halfDots = False
      
      
      #rockmeter
      if self.coOpType:
        try:
          self.engine.loadImgDrawing(self, "rockHi", os.path.join("themes",themename,"coop_rock_hi.png"))
          self.engine.loadImgDrawing(self, "rockLo", os.path.join("themes",themename,"coop_rock_low.png"))
          self.engine.loadImgDrawing(self, "rockMed", os.path.join("themes",themename,"coop_rock_med.png"))
          self.engine.loadImgDrawing(self, "arrow", os.path.join("themes",themename,"coop_arr.png"))
          self.engine.loadImgDrawing(self, "rockTop", os.path.join("themes",themename,"coop_rock_top.png"))
        except IOError:
          self.engine.loadImgDrawing(self, "arrow", os.path.join("themes",themename,"rock_arr.png"))
          self.rockTop = None
          self.rockHi  = None
          self.rockMed = None
          self.rockLo  = None
        try:
          self.engine.loadImgDrawing(self, "scorePicBand", os.path.join("themes",themename,"coop_score.png"))
        except IOError:
          self.scorePicBand = None
      else:
          self.engine.loadImgDrawing(self, "rockHi", os.path.join("themes",themename,"rock_hi.png"))
          self.engine.loadImgDrawing(self, "rockLo", os.path.join("themes",themename,"rock_low.png"))
          self.engine.loadImgDrawing(self, "rockMed", os.path.join("themes",themename,"rock_med.png"))
          self.engine.loadImgDrawing(self, "arrow", os.path.join("themes",themename,"rock_arr.png"))
        
      #starPower
      if self.starfx:
        self.engine.loadImgDrawing(self, "SP", os.path.join("themes",themename,"splight.png"))
      #failMessage
      self.engine.loadImgDrawing(self, "failMsg", os.path.join("themes",themename,"youfailed.png"))
      #myfingershurt: youRockMessage
      self.engine.loadImgDrawing(self, "rockMsg", os.path.join("themes",themename,"yourock.png"))


    elif self.rmtype == 2:

      
      #Pause Screen
      self.engine.loadImgDrawing(self, "pauseScreen", os.path.join("themes",themename,"pause.png"))
      try:
        self.engine.loadImgDrawing(self, "failScreen", os.path.join("themes",themename,"fail.png"))
      except IOError:
        self.engine.loadImgDrawing(self, "failScreen", os.path.join("themes",themename,"pause.png"))
      #Rockmeter
      self.engine.loadImgDrawing(self, "counter", os.path.join("themes",themename,"counter.png"))


      self.rockArr  = [None for i in self.playerList]
      self.scorePic = [None for i in self.playerList]
      for i,thePlayer in enumerate(self.playerList):
        try:
          if self.guitars[i].isDrum:
            self.engine.loadImgDrawing(self, "scorePicLoad", os.path.join("themes",themename,"score_drums.png"))
          elif self.guitars[i].isBassGuitar:
            self.engine.loadImgDrawing(self, "scorePicLoad", os.path.join("themes",themename,"score_bass.png"))
          else:
            self.engine.loadImgDrawing(self, "scorePicLoad", os.path.join("themes",themename,"score_guitar.png"))
        except IOError:
          self.engine.loadImgDrawing(self, "scorePicLoad", os.path.join("themes",themename,"score.png"))
        self.scorePic[i] = self.scorePicLoad
        try:
          if self.guitars[i].isDrum:
            self.engine.loadImgDrawing(self, "rockArrLoad", os.path.join("themes",themename,"rockarr_drums.png"))
          elif self.guitars[i].isBassGuitar:
            self.engine.loadImgDrawing(self, "rockArrLoad", os.path.join("themes",themename,"rockarr_bass.png"))
          else:
            self.engine.loadImgDrawing(self, "rockArrLoad", os.path.join("themes",themename,"rockarr_guitar.png"))
        except IOError:
          self.engine.loadImgDrawing(self, "rockArrLoad", os.path.join("themes",themename,"rock_arr.png"))
        self.rockArr[i] = self.rockArrLoad
      try:
        self.engine.loadImgDrawing(self, "rockArrGlow", os.path.join("themes",themename,"rock_arr_glow.png"))
      except IOError:
        self.rockArrGlow = None
      
      self.scorePicLoad = None
      self.rockArrLoad = None
      self.engine.loadImgDrawing(self, "scorePicBand", os.path.join("themes",themename,"score.png"))




      #Multiplier
      #if self.playerList[0].part.text == "Bass Guitar": #kk69: uses multb.png for mult.png specifically for bass
      if self.guitars[0].isBassGuitar: #kk69: uses multb.png for mult.png specifically for bass
        try:
          self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"multb.png"))
        except IOError:
          self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"mult.png"))
      else:
        self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"mult.png"))

      if self.numOfPlayers > 1:
        #if self.playerList[1].part.text == "Bass Guitar":
        if self.guitars[1].isBassGuitar:
          try:
            self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"multb.png"))
          except IOError:
            self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"mult.png"))
        else:
          self.engine.loadImgDrawing(self, "mult", os.path.join("themes",themename,"mult.png"))#end kk69
      #death_au: Bass groove multiplier (with fall-back logic)
      try:
        self.engine.loadImgDrawing(self, "bassgroovemult", os.path.join("themes",themename,"bassgroovemult.png"))
      except IOError:
        self.bassgroovemult = None
      
      #UC's new multiplier - check if mult2 is present, if so use new mult code:
      try:
        self.engine.loadImgDrawing(self, "mult2",os.path.join("themes",themename,"mult2.png"))
        self.multRbFill = True
      except IOError:
        self.multRbFill = False
      
      
      #rockmeter
      self.engine.loadImgDrawing(self, "rockTop", os.path.join("themes",themename,"rock_top.png"))
      self.engine.loadImgDrawing(self, "rockBottom", os.path.join("themes",themename,"rock_bottom.png"))
      if self.coOpRB:
        try:
          self.engine.loadImgDrawing(self, "rockTopFail", os.path.join("themes",themename,"rock_top_fail.png"))
          self.rockFailFound = True
        except IOError:
          self.rockFailFound = False
        try:
          self.engine.loadImgDrawing(self, "rescueBox", os.path.join("themes",themename,"rescuebox.png"))
          self.engine.loadImgDrawing(self, "rescueCheck", os.path.join("themes",themename,"rescuecheck.png"))
        except IOError:
          self.engine.loadImgDrawing(self, "rescueBox", os.path.join("themes",themename,"starwhite.png"))
          self.engine.loadImgDrawing(self, "rescueCheck", os.path.join("themes",themename,"stargrey.png"))
        try:
          self.engine.loadImgDrawing(self, "bandStarMult", os.path.join("themes",themename,"bandstarmult.png"))
          self.bandMultFound = True
        except IOError:
          self.bandMultFound = False
        try:
          self.engine.loadImgDrawing(self, "coOpFailImg", os.path.join("themes",themename,"coop_fail.png"))
        except IOError:
          self.engine.loadImgDrawing(self, "coOpFailImg", os.path.join("themes",themename,"youfailed.png"))
        try:
          self.engine.loadImgDrawing(self, "unisonPic", os.path.join("themes",themename,"unison.png"))
        except IOError:
          self.unisonPic = None
         
      #myfingershurt: Rock Band theme gets instrument-dependant rock meter arrows:




      self.engine.loadImgDrawing(self, "rockFull", os.path.join("themes",themename,"rock_max.png"))
      self.engine.loadImgDrawing(self, "rockFill", os.path.join("themes",themename,"rock_fill.png"))
      #Overdrive
      self.engine.loadImgDrawing(self, "oTop", os.path.join("themes",themename,"overdrive top.png"))
      self.engine.loadImgDrawing(self, "oBottom", os.path.join("themes",themename,"overdrive bottom.png"))
      self.engine.loadImgDrawing(self, "oFill", os.path.join("themes",themename,"overdrive fill.png"))
      self.engine.loadImgDrawing(self, "oFull", os.path.join("themes",themename,"overdrive full.png"))
      #failMessage
      self.engine.loadImgDrawing(self, "failMsg", os.path.join("themes",themename,"youfailed.png"))
      #myfingershurt: youRockMessage
      self.engine.loadImgDrawing(self, "rockMsg", os.path.join("themes",themename,"yourock.png"))

    
    #MFH - in-game star display:
    try:
      self.engine.loadImgDrawing(self, "starWhite", os.path.join("themes",themename,"starwhite.png"))
      self.engine.loadImgDrawing(self, "starGrey", os.path.join("themes",themename,"stargrey.png"))
      self.engine.loadImgDrawing(self, "starPerfect", os.path.join("themes",themename,"starperfect.png"))
    except IOError:
      self.starWhite = None
      self.starGrey = None
      self.starPerfect = None
    try:
      self.engine.loadImgDrawing(self, "starFC", os.path.join("themes",themename,"starfc.png"))
    except IOError:
      try:
        self.engine.loadImgDrawing(self, "starFC", os.path.join("themes",themename,"starperfect.png"))
      except IOError:
        self.starFC = None

    #stump: continuous partial stars
    # This is (compared to the other stuff) SLOOOOW!  Thus we generate the images now so we don't have to during gameplay...
    if self.starContinuousAvailable:
      try:
        self.drawnOverlays = {}
        baseStarGreyImageSize = Image.open(self.starGrey.texture.name).size
        for degrees in range(0, 360, 5):
          overlay = Image.new('RGBA', baseStarGreyImageSize)
          draw = ImageDraw.Draw(overlay)
          draw.pieslice((self.starFillupCenterX-self.starFillupOutRadius, self.starFillupCenterY-self.starFillupOutRadius,
                         self.starFillupCenterX+self.starFillupOutRadius, self.starFillupCenterY+self.starFillupOutRadius),
                        -90, degrees-90, outline=self.starFillupColor, fill=self.starFillupColor)
          draw.ellipse((self.starFillupCenterX-self.starFillupInRadius, self.starFillupCenterY-self.starFillupInRadius,
                        self.starFillupCenterX+self.starFillupInRadius, self.starFillupCenterY+self.starFillupInRadius),
                       outline=(0, 0, 0, 0), fill=(0, 0, 0, 0))
          dispOverlay = ImgDrawing(self.engine.data.svg, overlay)
          self.drawnOverlays[degrees] = dispOverlay
      except:
        Log.error('Could not prebuild star overlay textures: ')
        self.starContinuousAvailable = False

    self.starGrey1 = None
    if self.starWhite and self.starGrey and self.starPerfect and self.partialStars == 1 and not self.starContinuousAvailable:   #MFH - even better in-game star display, stargrey1.png - stargrey7.png (stargrey8.png is useless - that's a white star.)
      try:
        self.engine.loadImgDrawing(self, "starGrey1", os.path.join("themes",themename,"stargrey1.png"))
        self.engine.loadImgDrawing(self, "starGrey2", os.path.join("themes",themename,"stargrey2.png"))
        self.engine.loadImgDrawing(self, "starGrey3", os.path.join("themes",themename,"stargrey3.png"))
        self.engine.loadImgDrawing(self, "starGrey4", os.path.join("themes",themename,"stargrey4.png"))
        self.engine.loadImgDrawing(self, "starGrey5", os.path.join("themes",themename,"stargrey5.png"))
        self.engine.loadImgDrawing(self, "starGrey6", os.path.join("themes",themename,"stargrey6.png"))
        self.engine.loadImgDrawing(self, "starGrey7", os.path.join("themes",themename,"stargrey7.png"))
      except IOError:
        self.starGrey1 = None
        self.starGrey2 = None
        self.starGrey3 = None
        self.starGrey4 = None
        self.starGrey5 = None
        self.starGrey6 = None
        self.starGrey7 = None
   
    try:
      self.engine.loadImgDrawing(self, "rockOff", os.path.join("themes",themename,"rock_off.png"))
    except IOError:
      if self.rmtype == 2:
        self.engine.loadImgDrawing(self, "rockOff", os.path.join("themes",themename,"rock_fill.png"))
      else:
        self.engine.loadImgDrawing(self, "rockOff", os.path.join("themes",themename,"rock_med.png"))
    
    
    self.rockMax = 30000.0
    self.rockMedThreshold = self.rockMax/3.0    #MFH
    self.rockHiThreshold = self.rockMax/3.0*2   #MFH
    self.rock = [self.rockMax/2 for i in self.playerList]
    self.arrowRotation    = [.5 for i in self.playerList]
    self.starNotesMissed = [False for i in self.playerList]  #MFH
    self.notesMissed = [False for i in self.playerList]
    self.lessMissed = [False for i in self.playerList]
    self.notesHit = [False for i in self.playerList]
    self.lessHit = False
    self.minBase = 400
    self.pluBase = 15
    self.minGain = 2
    self.pluGain = 7
    self.battleMax = 300 #QQstarS:new2  the max adding when battle
    self.minusRock = [self.minBase for i in self.playerList]
    self.plusRock = [self.pluBase for i in self.playerList]
    self.coOpMulti = 1
    self.coOpFailDone = [False for i in self.playerList]
    if self.coOpRB: #akedrou
      self.coOpPlayerMeter = len(self.rock)
      self.rock.append(self.rockMax/2)
      self.minusRock.append(0.0)
      self.plusRock.append(0.0)
      self.timesFailed  = [0 for i in self.playerList]
    if self.coOp or self.coOpGH:
      self.coOpPlayerMeter = len(self.rock)-1 #make sure it's the last one

    self.counterY = -0.1
    self.coOpPhrase = 0

    self.scaleText = [0.0 for i in self.playerList]
    self.displayText = [None for i in self.playerList]
    self.displayTextScale = [0.0 for i in self.playerList]
    #self.streakFlag = None #QQstarS:Set the flag,to show which one has reach the 50 note
    self.textTimer = [0.0 for i in self.playerList]
    #self.textChanged = False
    self.textY = [.3 for i in self.playerList]
    self.scaleText2 = [0.0 for i in self.playerList]
    self.goingUP = [False for i in self.playerList]
    self.lastStreak = [0 for i in self.playerList]
    if self.coOpType:
      self.coOpPhrase = len(self.scaleText)
      self.scaleText.append(0.0)
      self.displayText.append(None)
      self.displayTextScale.append(0.0)
      self.textTimer.append(0.0)
      self.textY.append(.3)
      self.scaleText2.append(0.0)
      self.goingUP.append(False)
      self.lastStreak.append(0)

    self.killswitchEngaged = [None for i in self.playerList]


    #MFH - retrieve theme.ini pause background & text positions 
    self.pause_bkg = [float(i) for i in Theme.pause_bkg_pos]
    self.pause_bkg
    self.pause_text_x = Theme.pause_text_xPos
    self.pause_text_y = Theme.pause_text_yPos

    if self.pause_text_x == None:
      self.pause_text_x = .3

    if self.pause_text_y == None:
      self.pause_text_y = .31


    #MFH - new theme.ini color options:

    self.pause_text_color = Theme.hexToColor(Theme.pause_text_colorVar)
    self.pause_selected_color = Theme.hexToColor(Theme.pause_selected_colorVar)
    self.fail_text_color = Theme.hexToColor(Theme.fail_text_colorVar)
    self.fail_selected_color = Theme.hexToColor(Theme.fail_selected_colorVar)
    self.fail_completed_color = Theme.hexToColor(Theme.fail_completed_colorVar)

    settingsMenu = Settings.GameSettingsMenu(self.engine, self.pause_text_color, self.pause_selected_color)
    settingsMenu.fadeScreen = False

    
    # evilynux - More themeable options
    self.rockmeter_score_color = Theme.hexToColor(Theme.rockmeter_score_colorVar)
    
    #self.fail_completed_color = Theme.hexToColor(Theme.song_name_selected_colorVar) # text same color as selected song
    #self.fail_completed_color = Theme.hexToColor(Theme.fail_text_colorVar)  #No, now same as fail_text color.
    
    self.ingame_stats_color = Theme.hexToColor(Theme.ingame_stats_colorVar)

    Log.debug("Pause text / selected hex colors: " + Theme.pause_text_colorVar + " / " + Theme.pause_selected_colorVar)

    if self.pause_text_color == None:
      self.pause_text_color = (1,1,1)
    if self.pause_selected_color == None:
      self.pause_selected_color = (1,0.75,0)

    if self.fail_text_color == None:
      self.fail_text_color = (1,1,1)
    if self.fail_selected_color == None:
      self.fail_selected_color = (1,0.75,0)
    if self.fail_completed_color == None:
      self.fail_completed_color = self.fail_text_color

    Log.debug("Pause text / selected colors: " + str(self.pause_text_color) + " / " + str(self.pause_selected_color))



#racer: theme.ini fail positions
    size = self.engine.data.pauseFont.getStringSize("Quit to Main")
    self.fail_bkg = [float(i) for i in Theme.fail_bkg_pos]
    self.fail_text_x = Theme.fail_text_xPos
    self.fail_text_y = Theme.fail_text_yPos

    if self.fail_text_x == None:
      self.fail_text_x = .5-size[0]/2.0

    if self.fail_text_y == None:
      self.fail_text_y = .47

    if self.theme == 1: #GH3-like theme
      if self.careerMode:
        self.menu = Menu(self.engine, [
          (_("         RESUME"), self.resumeSong), #Worldrave adjusted proper spacing.
          (_("        RESTART"), self.restartSong),
          #(_("        GIVE UP"), self.changeSong), *Worldrave-commented out just to match GH3. Since this is a GH3 specific instruction.
          (_("       PRACTICE"), self.practiceSong), #evilynux
          (_("        OPTIONS"), settingsMenu),
          (_("           QUIT"), self.quit), #Worldrave - added graphic menu support "careerpause" for Career Pause menu in below line.
        ], name = "careerpause", fadeScreen = False, onClose = self.resumeGame, font = self.engine.data.pauseFont, pos = (self.pause_text_x, self.pause_text_y), textColor = self.pause_text_color, selectedColor = self.pause_selected_color, append_submenu_char = False)
      else:
        self.menu = Menu(self.engine, [
          (_("        RESUME"), self.resumeSong),
          (_("       RESTART"), self.restartSong),
 #         (_("        GIVE UP"), self.changeSong),
          (_("      END SONG"), self.endSong),
          (_("       OPTIONS"), settingsMenu),
          (_("           QUIT"), self.quit),  #Worldrave - added graphic menu support "pause" for Pause menu in below line.
        ], name = "pause", fadeScreen = False, onClose = self.resumeGame, font = self.engine.data.pauseFont, pos = (self.pause_text_x, self.pause_text_y), textColor = self.pause_text_color, selectedColor = self.pause_selected_color, append_submenu_char = False)
      size = self.engine.data.pauseFont.getStringSize("Quit to Main")
      if self.careerMode:
        self.failMenu = Menu(self.engine, [
          (_("RETRY SONG"), self.restartAfterFail),
          (_("  PRACTICE"), self.practiceSong), #evilynux
          (_(" NEW SONG"), self.changeAfterFail),
          (_("     QUIT"), self.quit),   #Worldrave - added graphic menu support "careerfail" for Career Failed menu in below line.
        ], name = "careerfail", fadeScreen = False, onCancel = self.changeAfterFail, font = self.engine.data.pauseFont, pos = (self.fail_text_x, self.fail_text_y), textColor = self.fail_text_color, selectedColor = self.fail_selected_color)
      else:
        self.failMenu = Menu(self.engine, [
          (_("RETRY SONG"), self.restartAfterFail),
          (_(" NEW SONG"), self.changeAfterFail),
          (_("     QUIT"), self.quit),  #Worldrave - added graphic menu support "fail" for Fail menu in below line.
        ], name = "fail", fadeScreen = False, onCancel = self.changeAfterFail, font = self.engine.data.pauseFont, pos = (self.fail_text_x, self.fail_text_y), textColor = self.fail_text_color, selectedColor = self.fail_selected_color)
      #FirstTime = True
      #self.restartSong(FirstTime)
    elif self.theme == 0:   #GH2-like theme
      if self.careerMode:
        self.menu = Menu(self.engine, [
          (_("  Resume"),       self.resumeSong),
          (_("  Start Over"),      self.restartSong),
          (_("  Change Song"),       self.changeSong),
          (_("  Practice"),       self.practiceSong), #evilynux
          (_("  Settings"),          settingsMenu),
          (_("  Quit to Main Menu"), self.quit),  #Worldrave - added graphic menu support "careerpause" for Career Pause menu in below line.
        ], name = "careerpause", fadeScreen = False, onClose = self.resumeGame, font = self.engine.data.pauseFont, pos = (self.pause_text_x, self.pause_text_y), textColor = self.pause_text_color, selectedColor = self.pause_selected_color)
      else:
        self.menu = Menu(self.engine, [
          (_("  Resume"),       self.resumeSong),
          (_("  Start Over"),      self.restartSong),
          (_("  Change Song"),       self.changeSong),
          (_("  End Song"),          self.endSong),
          (_("  Settings"),          settingsMenu),
          (_("  Quit to Main Menu"), self.quit),  #Worldrave - added graphic menu support "pause" for Pause menu in below line.
        ], name = "pause", fadeScreen = False, onClose = self.resumeGame, font = self.engine.data.pauseFont, pos = (self.pause_text_x, self.pause_text_y), textColor = self.pause_text_color, selectedColor = self.pause_selected_color)
      size = self.engine.data.pauseFont.getStringSize("Quit to Main")
      if self.careerMode:
        self.failMenu = Menu(self.engine, [
          (_(" Try Again?"), self.restartAfterFail),
          (_("  Give Up?"), self.changeAfterFail),
          (_("  Practice?"), self.practiceSong), #evilynux
          (_("Quit to Main"), self.quit),  #Worldrave - added graphic menu support "careerfail" for Career Fail menu in below line.
        ], name = "careerfail", fadeScreen = False, onCancel = self.changeAfterFail, font = self.engine.data.pauseFont, pos = (self.fail_text_x, self.fail_text_y), textColor = self.fail_text_color, selectedColor = self.fail_selected_color)
      else:
        self.failMenu = Menu(self.engine, [
          (_(" Try Again?"), self.restartAfterFail),
          (_("  Give Up?"), self.changeAfterFail),
          (_("Quit to Main"), self.quit),  #Worldrave - added graphic menu support "fail" for Fail menu in below line.
        ], name = "fail", fadeScreen = False, onCancel = self.changeAfterFail, font = self.engine.data.pauseFont, pos = (self.fail_text_x, self.fail_text_y), textColor = self.fail_text_color, selectedColor = self.fail_selected_color)
      #FirstTime = True
      #self.restartSong(FirstTime)
    elif self.theme == 2:   #RB-like theme
      size = self.engine.data.pauseFont.getStringSize("Quit to Main Menu")
      if self.careerMode:
        self.menu = Menu(self.engine, [
          (_("   RESUME"),       self.resumeSong),
          (_("   RESTART"),      self.restartSong),
          (_("   CHANGE SONG"),       self.changeSong),
          (_("   PRACTICE"),       self.practiceSong), #evilynux
          (_("   SETTINGS"),          settingsMenu),
          (_("   QUIT"), self.quit),  #Worldrave - added graphic menu support "careerpause" for Career Pause menu in below line.
        ], name = "careerpause", fadeScreen = False, onClose = self.resumeGame, font = self.engine.data.pauseFont, pos = (self.pause_text_x, self.pause_text_y), textColor = self.pause_text_color, selectedColor = self.pause_selected_color)
      else:      
        self.menu = Menu(self.engine, [
          (_("   RESUME"),       self.resumeSong),
          (_("   RESTART"),      self.restartSong),
          (_("   CHANGE SONG"),       self.changeSong),
          (_("   END SONG"),          self.endSong),
          (_("   SETTINGS"),          settingsMenu),
          (_("   QUIT"), self.quit),   #Worldrave - added graphic menu support "pause" for Pause menu in below line.
        ], name = "pause", fadeScreen = False, onClose = self.resumeGame, font = self.engine.data.pauseFont, pos = (self.pause_text_x, self.pause_text_y), textColor = self.pause_text_color, selectedColor = self.pause_selected_color)
      size = self.engine.data.pauseFont.getStringSize("Quit to Main")
      if self.careerMode:
        self.failMenu = Menu(self.engine, [
          (_(" RETRY"), self.restartAfterFail),
          (_(" NEW SONG"), self.changeAfterFail),
          (_(" PRACTICE"), self.practiceSong), #evilynux
          (_(" QUIT"), self.quit),  #Worldrave - added graphic menu support "careerfail" for Career Fail menu in below line.
        ], name = "careerfail", fadeScreen = False, onCancel = self.changeAfterFail, font = self.engine.data.pauseFont, pos = (self.fail_text_x, self.fail_text_y), textColor = self.fail_text_color, selectedColor = self.fail_selected_color)
      else:
        self.failMenu = Menu(self.engine, [
          (_(" RETRY"), self.restartAfterFail),
          (_(" NEW SONG"), self.changeAfterFail),
          (_(" QUIT"), self.quit),  #Worldrave - added graphic menu support "fail" for Fail menu in below line.
        ], name = "fail", fadeScreen = False, onCancel = self.changeAfterFail, font = self.engine.data.pauseFont, pos = (self.fail_text_x, self.fail_text_y), textColor = self.fail_text_color, selectedColor = self.fail_selected_color)

    FirstTime = True
    self.restartSong(FirstTime)

    # hide the splash screen
    Dialogs.hideLoadingSplashScreen(self.engine, splash)
    splash = None
    
    self.engine.createdGuitarScene = False
    #MFH - end of GuitarScene cleint initialization routine


  def pauseGame(self):
    if self.song and self.song.readyToGo:
      self.song.pause()
      self.pausePos = self.getSongPosition()
      self.pause = True
      for guitar in self.guitars:
        guitar.paused = True

  def failGame(self):
    self.engine.view.pushLayer(self.failMenu)
    if self.song and self.song.readyToGo and self.pause: #akedrou - don't let the pause menu overlap the fail menu.
      self.engine.view.popLayer(self.menu)
      self.pause = False
      for guitar in self.guitars:
        guitar.paused = False
    self.failEnd = True

  def resumeGame(self):
    self.loadSettings()
    self.setCamera()
    if self.resumeCountdownEnabled and not self.failed and not self.countdown:
      self.resumeCountdownSeconds = 3
      self.resumeCountdown = float(self.resumeCountdownSeconds) * self.songBPS
      self.pause = False
    else:
      if self.song and self.song.readyToGo:
        if not self.failed: #akedrou - don't resume the song if you have already failed.
          self.song.unpause()
        self.pause = False
        for guitar in self.guitars:
          guitar.paused = False

  def resumeSong(self):
    self.engine.view.popLayer(self.menu)
    self.resumeGame()

  def lostFocus(self): #akedrou - catch to pause on lostFocus
    if self.song and self.song.readyToGo:
      if not self.failed and not self.pause:
        self.engine.view.pushLayer(self.menu)
        self.pauseGame()
  
  def setCamera(self):
    #x=0 middle
    #x=1 rotate left
    #x=-1 rotate right
    #y=3 middle
    #y=4 rotate back
    #y=2 rotate front
    #z=-3

    if self.pov == 1:
      self.camera.target    = (0.0, 0.6, 4.4) #kk69:More like GH3
      self.camera.origin    = (0.0, 3.5*self.boardY, -3.8)
    elif self.pov == 2: #Racer
      self.camera.target    = (0.0, 0.0, 3.7)
      self.camera.origin    = (0.0, 2.9*self.boardY, -2.9)
    elif self.pov == 3: #Racer
      self.camera.target    = (0.0, 1.6, 2.0)
      self.camera.origin    = (0.0, 2.6*self.boardY, -3.6)
    elif self.pov == 4: #blazingamer
      self.camera.target    = (0.0, -6.0, 2.6666666666)
      self.camera.origin    = (0.0, 6.0, 2.6666666665) 
    elif self.pov == 5: #Blazingamer theme-dependant
      if self.rmtype == 0:
        self.camera.target    = (0.0, 1.6, 2.0)
        self.camera.origin    = (0.0, 2.6*self.boardY, -3.6)
      elif self.rmtype == 1:
        self.camera.target    = (0.0, 0.6, 4.4) #Worldrave - Perfected the proper GH3 POV
        self.camera.origin    = (0.0, 3.5*self.boardY, -3.8)
      elif self.rmtype == 2:
        self.camera.target    = (0.0, 0.0, 3.7)
        self.camera.origin    = (0.0, 2.9*self.boardY, -2.9)
    else:
      self.camera.target    = (0.0, 0.0, 4.0)
      self.camera.origin    = (0.0, 3.0*self.boardY, -3.0)

    if self.rmtype == 3:
      self.camera.target    = (0.0, 1.4, 1.8) #kk69:More like GH3
      self.camera.origin    = (0.0, 2.8, -3.6)

    if (self.targetX and self.targetY and self.targetZ and self.originX and self.originY and self.originZ != None) and self.rmtype != 3:
      self.camera.target    = (self.targetX, self.targetY, self.targetZ)
      self.camera.origin    = (self.originX, self.originY*self.boardY, self.originZ)

    #if self.fontMode == 1:    #0 = oGL Hack, 1=LaminaScreen, 2=LaminaFrames
    #  self.laminaScreen.refreshPosition()   #needs to be called whenever camera position changes
    #above does not work......

           
  def freeResources(self):
    self.engine.view.setViewport(1,0)
    self.counter = None
    self.failScreen = None
    self.failMsg = None
    self.menu = None
    self.mult = None
    self.pauseScreen = None
    self.rockTop = None
    self.rockMsg = None

    #MFH - Ensure all event tracks are destroyed before removing Song object!
    if self.song:
      self.song.tracks = None
      self.song.eventTracks = None
      self.song.midiEventTracks = None
    self.song = None

    self.rockOff = None
    if self.rmtype == 0:
      self.arrow = None
      self.rockmeter = None
      self.basedots = None
      self.dt1 = None
      self.dt2 = None
      self.dt3 = None
      self.dt4 = None
      self.dt5 = None
      self.dt6 = None
      self.dt7 = None
      self.dt8 = None
      self.dt9 = None
      self.dt10 = None
      self.rockHi = None
      self.rockLo = None
      self.rockMed = None      
      self.oTop = None
      self.oBottom = None
      self.oFill = None
      self.oFull = None
    elif self.rmtype == 1 or self.rmtype == 3:
      self.arrow = None
      self.rockmeter = None
      if self.coOpType:
        self.coopRockmeter = None
        self.scorePicBand  = None
      self.dots = None
      self.basedots = None
      self.rockHi = None
      self.rockLo = None
      self.rockMed = None
      self.SP = None
    elif self.rmtype == 2:
      self.oTop = None
      self.oBottom = None
      self.oFill = None
      self.oFull = None
      self.rockBottom = None
      self.rockFull = None
      self.rockFill = None
      self.scorePic = [None for i in self.playerList]
      self.scorePicBand = None
      self.rockArr = [None for i in self.playerList]
      self.rockArrGlow = None
      self.mult2 = None
    if self.coOpRB:
      self.coOpFailImg = None
      self.rescueBox = None
      self.rescueCheck = None
      self.rockTopFail = None
      self.bandStarMult = None
      self.unisonPic = None
    #MFH - additional cleanup!
    self.lyricSheet = None
    self.starWhite = None
    self.starGrey = None
    self.starPerfect = None
    self.starGrey1 = None
    self.starGrey2 = None
    self.starGrey3 = None
    self.starGrey4 = None
    self.starGrey5 = None
    self.starGrey6 = None
    self.starGrey7 = None
    self.part = [None for i in self.playerList]
    for scoreCard in self.scoring:
      scoreCard.lastNoteEvent = None
    if self.coOpType:
      self.coOpScoreCard.lastNoteEvent = None
    

  def getHandicap(self):
    hopoFreq = self.engine.config.get("coffee", "hopo_frequency")
    hopoCheat = self.engine.config.get("coffee", "hopo_freq_cheat")
    try:
      songHopo = int(self.song.info.hopofreq)
    except Exception, e:
      songHopo = 1
    for i, scoreCard in enumerate(self.scoring):
      if self.gh2sloppy == 1: # or self.rb2sloppy == 1:
        if (scoreCard.handicap)&1 != 1:
          scoreCard.handicap += 1
        if self.coOpType:
          if self.coOpScoreCard.handicap&1 != 1:
            self.coOpScoreCard.handicap += 1
      if self.engine.audioSpeedFactor != 1 or scoreCard.earlyHitWindowSizeHandicap != 1.0: #scalable handicaps
        if (scoreCard.handicap>>1)&1 != 1:
          scoreCard.handicap += 0x2
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>1)&1 != 1:
            self.coOpScoreCard.handicap += 0x2
      if not self.failingEnabled:
        if (scoreCard.handicap>>2)&1 != 1:
          scoreCard.handicap += 0x4
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>2)&1 != 1:
            self.coOpScoreCard.handicap += 0x4
      if self.guitars[i].twoChordApply:
        if (scoreCard.handicap>>3)&1 != 1:
          scoreCard.handicap += 0x8
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>3)&1 != 1:
            self.coOpScoreCard.handicap += 0x8
      if self.guitars[i].hitw == 0.70:
        if (scoreCard.handicap>>4)&1 != 1:
          scoreCard.handicap += 0x10
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>4)&1 != 1:
            self.coOpScoreCard.handicap += 0x10
      elif self.guitars[i].hitw == 1.0:
        if (scoreCard.handicap>>5)&1 != 1:
          scoreCard.handicap += 0x20
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>5)&1 != 1:
            self.coOpScoreCard.handicap += 0x20
      elif self.guitars[i].hitw == 1.9:
        if (scoreCard.handicap>>6)&1 != 1:
          scoreCard.handicap += 0x40
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>6)&1 != 1:
            self.coOpScoreCard.handicap += 0x40
      elif self.guitars[i].hitw == 2.3:
        if (scoreCard.handicap>>7)&1 != 1:
          scoreCard.handicap += 0x80
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>7)&1 != 1:
            self.coOpScoreCard.handicap += 0x80
      if self.hopoStyle == 0: #no taps
        if (scoreCard.handicap>>8)&1 != 1:
          scoreCard.handicap += 0x100
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>8)&1 != 1:
            self.coOpScoreCard.handicap += 0x100
      elif hopoFreq == 0 and songHopo != 1:
        if (scoreCard.handicap>>9)&1 != 1:
          scoreCard.handicap += 0x200
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>9)&1 != 1:
            self.coOpScoreCard.handicap += 0x200
      elif hopoFreq == 1 and songHopo != 1:
        if (scoreCard.handicap>>10)&1 != 1:
          scoreCard.handicap += 0x400
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>10)&1 != 1:
            self.coOpScoreCard.handicap += 0x400
      elif hopoCheat == 1 and songHopo != 1:
        if (scoreCard.handicap>>11)&1 != 1:
          scoreCard.handicap += 0x800
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>11)&1 != 1:
            self.coOpScoreCard.handicap += 0x800
      elif hopoCheat == 2 and songHopo != 1:
        if (scoreCard.handicap>>12)&1 != 1:
          scoreCard.handicap += 0x1000
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>12)&1 != 1:
            self.coOpScoreCard.handicap += 0x1000
      elif hopoFreq == 3 and songHopo != 1:
        if (scoreCard.handicap>>13)&1 != 1:
          scoreCard.handicap += 0x2000
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>13)&1 != 1:
            self.coOpScoreCard.handicap += 0x2000
      elif self.allTaps == 1:
        if (scoreCard.handicap>>14)&1 != 1:
          scoreCard.handicap += 0x4000
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>14)&1 != 1:
            self.coOpScoreCard.handicap += 0x4000
      if self.whammySavesSP:
        if (scoreCard.handicap>>15)&1 != 1:
          scoreCard.handicap += 0x8000
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>15)&1 != 1:
            self.coOpScoreCard.handicap += 0x8000
      if self.autoPlay and (self.jurg == i or self.jurg == 2): #2 as both
        if (scoreCard.handicap>>16)&1 != 1:
          scoreCard.handicap += 0x10000
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>16)&1 != 1:
            self.coOpScoreCard.handicap += 0x10000
      if self.playerAssist[i] == 1:
        if (scoreCard.handicap>>17)&1 != 1:
          scoreCard.handicap += 0x20000
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>17)&1 != 1:
            self.coOpScoreCard.handicap += 0x20000
      if self.playerAssist[i] == 2:
        if (scoreCard.handicap>>18)&1 != 1:
          scoreCard.handicap += 0x40000
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>18)&1 != 1:
            self.coOpScoreCard.handicap += 0x40000
      if self.playerAssist[i] == 3:
        if (scoreCard.handicap>>19)&1 != 1:
          scoreCard.handicap += 0x80000
        if self.coOpType:
          if (self.coOpScoreCard.handicap>>19)&1 != 1:
            self.coOpScoreCard.handicap += 0x80000
      scoreCard.updateHandicapValue()
    if self.coOpType:
      self.coOpScoreCard.updateHandicapValue()
    
  def loadSettings(self):
    self.stage.updateDelays()

    self.guitarVolume     = self.engine.config.get("audio", "guitarvol")
    self.songVolume       = self.engine.config.get("audio", "songvol")
    self.rhythmVolume     = self.engine.config.get("audio", "rhythmvol")
    self.screwUpVolume    = self.engine.config.get("audio", "screwupvol")
    self.killVolume       = self.engine.config.get("audio", "kill_volume")
    self.sfxVolume        = self.engine.config.get("audio", "SFX_volume")
    self.crowdVolume      = self.engine.config.get("audio", "crowd_volume") #akedrou
    self.crowdsEnabled    = self.engine.config.get("audio", "enable_crowd_tracks")
    self.engine.data.sfxVolume = self.sfxVolume   #MFH - keep Data updated
    self.engine.data.crowdVolume = self.crowdVolume

    #MFH - now update volume of all screwup sounds and other SFX:
    self.engine.data.SetAllScrewUpSoundFxObjectVolumes(self.screwUpVolume)
    self.engine.data.SetAllSoundFxObjectVolumes(self.sfxVolume)
    
    #Re-apply Jurgen Settings -- Spikehead777
    self.jurg             = self.engine.config.get("game", "jurgtype")
    
    #MFH
    self.jurgenLogic = self.engine.config.get("game", "jurglogic")    #logic 0 = original, logic 1 = MFH-1

    
    #MFH - no Jurgen in Career mode.
    if self.careerMode:
      self.autoPlay = False
    else:
      self.autoPlay         = self.engine.config.get("game", "jurgmode")
      if self.autoPlay == 0:
        self.autoPlay = True
      else:
        self.autoPlay = False

    self.hopoStyle        = self.engine.config.get("game", "hopo_system")
    self.gh2sloppy        = self.engine.config.get("game", "gh2_sloppy")
    self.allTaps          = 0
    self.autoKickBass     = [0 for i in self.playerList]
    if self.gh2sloppy == 1:
      self.hopoStyle = 4
    self.hopoAfterChord = self.engine.config.get("game", "hopo_after_chord")

    self.pov              = self.engine.config.get("fretboard", "point_of_view")
    #CoffeeMod

    if self.numOfPlayers == 1:
      #De-emphasize non played part
      self.rhythmVolume *= 0.6
    
    for i,guitar in enumerate(self.guitars):
      guitar.leftyMode = self.engine.config.get("player%d" % (i), "leftymode")
      guitar.twoChordMax  = self.engine.config.get("player%d" % (i), "two_chord_max")
    
    if self.song and self.song.readyToGo:
      self.getHandicap() #akedrou - to be sure scoring objects are created.
      #myfingershurt: ensure that after a pause or restart, the a/v sync delay is refreshed:
      self.song.refreshAudioDelay()
      #myfingershurt: ensuring the miss volume gets refreshed:
      self.song.refreshMissVolume()
      if self.crowdsCheering == True:
        self.song.setCrowdVolume(self.crowdVolume)
      else:
        self.song.setCrowdVolume(0.0)
      self.song.setBackgroundVolume(self.songVolume)
      self.song.setRhythmVolume(self.rhythmVolume)
      self.song.setDrumVolume(self.rhythmVolume)
  
  def songLoaded(self, song):
    for i, player in enumerate(self.playerList):
      song.difficulty[i] = player.difficulty
    
    self.song.readyToGo = False
  
  def endSong(self):
    self.engine.view.popLayer(self.menu)
    validScoreFound = False
    for scoreCard in self.scoring:  #MFH - what if 2p (human) battles 1p (Jurgen / CPU)?  He needs a valid score too!
      if scoreCard.score > 0:
        validScoreFound = True
    if self.coOpType:
      if self.coOpScoreCard.score > 0:
        validScoreFound = True
    if validScoreFound:
    #if self.player.score > 0:
      self.goToResults()
    else:
      self.changeSong()
  
  def quit(self):
    if self.song:
      self.song.stop()
    self.resetVariablesToDefaults()
    self.done = True
    self.engine.view.setViewport(1,0)
    self.engine.view.popLayer(self.menu)
    self.engine.view.popLayer(self.failMenu)
    self.freeResources()
    self.session.world.finishGame()

  # evilynux - Switch to Practice
  def practiceSong(self):
    if self.song:
      self.song.stop()
      self.song  = None
    self.resetVariablesToDefaults()
    self.engine.view.setViewport(1,0)
    self.engine.view.popLayer(self.menu)
    self.engine.view.popLayer(self.failMenu)
    self.freeResources()
    self.engine.config.set("player0","mode_1p", 1)
    self.engine.config.set("player0","mode_2p", 1)
    self.session.world.deleteScene(self)
    self.session.world.createScene("SongChoosingScene")

  def changeSong(self):
    if self.song:
      self.song.stop()
      self.song  = None
    self.resetVariablesToDefaults()
    self.engine.view.setViewport(1,0)
    self.engine.view.popLayer(self.menu)
    self.engine.view.popLayer(self.failMenu)
    self.freeResources()
    self.session.world.deleteScene(self)
    self.session.world.createScene("SongChoosingScene")

  def changeAfterFail(self):
    if self.song:
      self.song.stop()
      self.song  = None
    self.resetVariablesToDefaults()
    self.engine.view.setViewport(1,0)
    self.engine.view.popLayer(self.failMenu)
    self.freeResources()
    self.session.world.deleteScene(self)
    self.session.world.createScene("SongChoosingScene")

  def initBeatAndSpClaps(self):
    ###Capo###
    if self.song:
      self.beatTime = []
      if (self.starClaps or self.beatClaps):
        for time, event in self.song.track[0].getAllEvents():
          if isinstance(event, Bars):
            if (event.barType == 1 or event.barType == 2):
              self.beatTime.append(time)
    ###endCapo###


  def resetVariablesToDefaults(self):
    if self.song:
      self.song.readyToGo = False
    #self.countdown = 4.0 * self.songBPS
    self.countdownSeconds = 5   #MFH - This needs to be reset for song restarts, too!
    self.countdown = float(self.countdownSeconds) * self.songBPS
    self.scaleText = [0.0 for i in self.playerList]
    self.displayText = [None for i in self.playerList]
    self.displayTextScale = [0.0 for i in self.playerList]
    self.textTimer = [0.0 for i in self.playerList]
    self.textY = [.3 for i in self.playerList]
    self.scaleText2 = [0.0 for i in self.playerList]
    self.goingUP = [False for i in self.playerList]
    self.lastStreak = [0 for i in self.playerList]
    if self.coOpType:
      self.coOpPhrase = len(self.scaleText)
      self.scaleText.append(0.0)
      self.displayText.append(None)
      self.displayTextScale.append(0.0)
      self.textTimer.append(0.0)
      self.textY.append(.3)
      self.scaleText2.append(0.0)
      self.goingUP.append(False)
      self.lastStreak.append(0)
    self.midiLyricLineIndex = 0
    self.drumStart = False  #faaa's drum sound mod restart
    self.dispAccuracy = [False for i in self.playerList]
    for playaNum, thePlayer in enumerate(self.playerList): 
      #thePlayer.stars = 0
      self.guitars[playaNum].spEnabled = True
      self.guitars[playaNum].bigRockEndingMarkerSeen = False
    #self.partialStar = [0 for i in self.playerList]
    #self.starRatio = [0.0 for i in self.playerList]
    for scoreCard in self.scoring:
      scoreCard.reset()
    self.crowdsCheering = False #akedrou
    if self.coOpType:
      self.coOpScoreCard.reset()
      self.coOpStarPower = 0
      self.coOpStarPowerTimer = 0
      self.coOpStarPowerActive = [0 for i in self.playerList]
    self.mutedLastSecondYet = False
    self.dispSoloReview = [False for i in self.playerList]
    self.soloReviewCountdown = [0 for i in self.playerList]
    self.guitarSoloAccuracy = [0.0 for i in self.playerList]
    self.guitarSoloActive = [False for i in self.playerList]
    self.currentGuitarSolo = [0 for i in self.playerList]
    self.guitarSoloBroken = [False for i in self.playerList]
    self.inUnison = [False for i in self.playerList]
    self.haveUnison = [False for i in self.playerList]
    self.firstUnison = False
    self.firstUnisonDone = False
    self.unisonNum = 0
    self.unisonIndex = 0
    self.unisonActive = False
    self.unisonEarn   = [False for i in self.playerList]
    self.resumeCountdown = 0
    self.resumeCountdownSeconds = 0
    self.pausePos = 0
    self.failTimer = 0  #myfingershurt
    self.rockTimer = 0  #myfingershurt
    self.youRock = False    #myfingershurt
    self.rockFinished = False    #myfingershurt
    self.rock = [self.rockMax/2 for i in self.playerList]
    self.minusRock = [0.0 for i in self.playerList]
    self.plusRock = [0.0 for i in self.playerList]
    self.coOpMulti = 1
    self.deadPlayerList = []
    self.numDeadPlayers  = 0
    self.coOpFailDone = [False for i in self.playerList]
    self.rockFailUp = True
    self.rockFailViz  = 0.0
    self.failViz = [0.0 for i in self.playerList]
    if self.coOpRB:
      self.rock.append(self.rockMax/2)
      self.minusRock.append(0.0)
      self.plusRock.append(0.0)
      self.timesFailed = [0 for i in self.playerList]
    for i, thePlayer in enumerate(self.playerList):
      self.guitars[i].starPower = 0   
      self.guitars[i].coOpFailed = False
      #volshebnyi - BRE variables reset
      self.guitars[i].freestyleStart = 0 
      self.guitars[i].freestyleFirstHit = 0 
      self.guitars[i].freestyleLength = 0
      self.guitars[i].freestyleBonusFret = 0
      if self.guitars[i].isDrum:
        self.guitars[i].drumFillsCount = 0
        self.guitars[i].drumFillsHits = 0
      for i1 in range(0, 5):
        self.guitars[i].freestyleLastFretHitTime[i1] = 0
    self.failed = False
    self.finalFailed = False
    self.failEnd = False
    self.failTimer = 0
    self.rockTimer = 0  #myfingershurt
    self.youRock = False    #myfingershurt
    self.rockFinished = False    #myfingershurt
    self.drumScoringEnabled = True  #MFH
    self.initBeatAndSpClaps()

    #MFH - init vars for the next time & lyric line to display
    self.midiLyricLineIndex = 0
    self.nextMidiLyricStartTime = 0
    if ( self.numMidiLyricLines > 0 ):
      self.nextMidiLyricStartTime, self.nextMidiLyricLine = self.midiLyricLines[self.midiLyricLineIndex]

    #MFH - initialize word-by-word 2-line MIDI lyric display / highlighting system:
    self.activeMidiLyricLine_GreyWords = ""
    self.activeMidiLyricLine_GreenWords = ""
    self.activeMidiLyricLine_WhiteWords = ""
    self.activeMidiLyricLineIndex = 0
    self.activeMidiLyricWordSubIndex = 0
    self.numWordsInCurrentMidiLyricLine = 0
    self.currentSimpleMidiLyricLine = ""
    self.nextLyricWordTime = 0
    self.nextLyricEvent = None
    self.nextLyricIsOnNewLine = False
    
    if self.midiLyricMode == 2:
      
      if self.numMidiLyricLines > self.activeMidiLyricLineIndex:
        self.numWordsInCurrentMidiLyricLine = 0
        for nextLyricTime, nextLyricEvent in self.midiLyricLineEvents[self.activeMidiLyricLineIndex]:   #populate the first active line
          self.numWordsInCurrentMidiLyricLine += 1
      
        if self.numWordsInCurrentMidiLyricLine > self.activeMidiLyricWordSubIndex+1:  #there is another word in this line
          self.nextLyricWordTime, self.nextLyricEvent = self.midiLyricLineEvents[self.activeMidiLyricLineIndex][self.activeMidiLyricWordSubIndex]
        else:
          self.noMoreMidiLineLyrics = True    #t'aint no lyrics t'start wit!
        #self.activeMidiLyricWordSubIndex += 1
        for nextLyricTime, nextLyricEvent in self.midiLyricLineEvents[self.activeMidiLyricLineIndex]:   #populate the first active line
          self.activeMidiLyricLine_WhiteWords = "%s %s" % (self.activeMidiLyricLine_WhiteWords, nextLyricEvent.text)
        if self.numMidiLyricLines > self.activeMidiLyricLineIndex+2:  #is there a second line of lyrics?
          tempTime, self.currentSimpleMidiLyricLine = self.midiLyricLines[self.activeMidiLyricLineIndex+1]

    for player in self.playerList:
      player.reset()
    self.stage.reset()
    self.enteredCode     = []
    self.jurgPlayer       = [False for i in self.playerList] #Jurgen hasn't played the restarted song =P
    
    for guitar in self.guitars:
      guitar.twoChord = 0
      guitar.hopoActive = 0
      guitar.wasLastNoteHopod = False
      guitar.sameNoteHopoString = False
      guitar.hopoLast = -1
      guitar.guitarSolo = False
      guitar.currentGuitarSoloHitNotes = 0
      guitar.scoreMultiplier = 1
      
    if self.partyMode == True:
      self.guitars[0].keys = PLAYER1KEYS
      self.guitars[0].actions = PLAYER1ACTIONS
      self.keysList   = [PLAYER1KEYS]
    if self.battle == True and self.numOfPlayers>1:
      self.guitars[0].actions = PLAYER1ACTIONS
      self.guitars[1].actions = PLAYER2ACTIONS

    self.engine.collectGarbage()

    self.boardY = 2
    self.setCamera()


    if self.song:
      self.song.readyToGo = True

    
  def restartSong(self, firstTime = False):  #QQstarS: Fix this function
    self.resetVariablesToDefaults()
    self.engine.data.startSound.play()
    self.engine.view.popLayer(self.menu)

    if not self.song:
      return
    
    # glorandwarf: the countdown is now the number of beats to run
    # before the song begins
    
    
    self.partySwitch = 0
    for i,guitar in enumerate(self.guitars):
      guitar.endPick(i)
    self.song.stop()

    for i, guitar in enumerate(self.guitars):
      #myfingershurt: preventing ever-thickening BPM lines after restarts
      if firstTime:
        self.song.track[i].markBars()

        #MFH - should only be done the first time.
        if self.hopoStyle > 0 or self.song.info.hopo == "on":
          if not guitar.isDrum:
            if self.hopoStyle == 2 or self.hopoStyle == 3 or self.hopoStyle == 4:  #GH2 style HOPO system
              self.song.track[i].markHopoGH2(self.song.info.EighthNoteHopo, self.hopoAfterChord, self.song.info.hopofreq)
            elif self.hopoStyle == 1:   #RF-Mod style HOPO system
              self.song.track[i].markHopoRF(self.song.info.EighthNoteHopo, self.song.info.hopofreq)
    
    #myfingershurt: removing buggy disable stats option
    lastTime = 0
    for i,guitar in enumerate(self.guitars):      
      for time, event in self.song.track[i].getAllEvents():
        if not isinstance(event, Note):
          continue
        if time + event.length > lastTime:
          lastTime = time + event.length

    self.initBeatAndSpClaps()


    
    self.lastEvent = lastTime + 1000
    self.lastEvent = round(self.lastEvent / 1000) * 1000
    #self.notesCum = 0
    self.noteLastTime = 0
            
  def restartAfterFail(self):  #QQstarS: Fix this function
    self.resetVariablesToDefaults()
    self.engine.data.startSound.play()
    self.engine.view.popLayer(self.failMenu)

    if not self.song:
      return
      
    self.partySwitch = 0
    for i,guitar in enumerate(self.guitars):
      guitar.endPick(i)
    self.song.stop()

    for i, guitar in enumerate(self.guitars):
      #myfingershurt: next line commented to prevent everthickening BPM lines
      if self.hopoStyle > 0 or self.song.info.hopo == "on":
        if self.hopoStyle == 2 or self.hopoStyle == 3 or self.hopoStyle == 4:  #GH2 style HOPO system
          self.song.track[i].markHopoGH2(self.song.info.EighthNoteHopo, self.hopoAfterChord, self.song.info.hopofreq)
        elif self.hopoStyle == 1:   #RF-Mod style HOPO system
          self.song.track[i].markHopoRF(self.song.info.EighthNoteHopo, self.song.info.hopofreq)
    
    lastTime = 0
    for i,guitar in enumerate(self.guitars):      
      for time, event in self.song.track[i].getAllEvents():
        if not isinstance(event, Note):
          continue
        if time + event.length > lastTime:
          lastTime = time + event.length

    self.lastEvent = lastTime + 1000
    self.lastEvent = round(self.lastEvent / 1000) * 1000
    #self.notesCum = 0
    self.noteLastTime = 0

  def startSolo(self, playerNum):   #MFH - more modular and general handling of solos
    i = playerNum
     #Guitar Solo Start
    self.currentGuitarSoloTotalNotes[i] = self.guitarSolos[i][self.currentGuitarSolo[i]]
    self.guitarSoloBroken[i] = False
    self.guitars[i].guitarSolo = True
    #self.displayText[i] = _("Guitar Solo!")
    instrumentSoloString = "%s %s" % (self.playerList[i].part.text, self.tsSolo)
    if self.phrases > 1:
      self.newScalingText(i, instrumentSoloString )
    #self.sfxChannel.setVolume(self.sfxVolume)
    self.engine.data.crowdSound.play()
  
  def endSolo(self, playerNum):     #MFH - more modular and general handling of solos
    i = playerNum
    #Guitar Solo End
    self.guitars[i].guitarSolo = False
    #self.sfxChannel.setVolume(self.sfxVolume)    #liquid
    self.guitarSoloAccuracy[i] = (float(self.guitars[i].currentGuitarSoloHitNotes) / float(self.currentGuitarSoloTotalNotes[i]) ) * 100.0
    if not self.guitarSoloBroken[i]:    #backup perfect solo detection
      if self.guitars[i].currentGuitarSoloHitNotes > 0: #MFH - need to make sure someone didn't just not play a guitar solo at all - and still wind up with 100%
        self.guitarSoloAccuracy[i] = 100.0
    if self.guitarSoloAccuracy[i] > 100.0:
      self.guitarSoloAccuracy[i] = 100.0
    if self.guitarSoloBroken[i] and self.guitarSoloAccuracy[i] == 100.0:   #streak was broken, not perfect solo, force 99%
      self.guitarSoloAccuracy[i] = 99.0

    if self.guitarSoloAccuracy[i] == 100.0: #fablaculp: soloDescs changed
      soloDesc = "%s %s" % (self.tsPerfectSolo, self.tsSolo)
      soloScoreMult = 100
      self.engine.data.crowdSound.play()    #liquid
    elif self.guitarSoloAccuracy[i] >= 95.0:
      soloDesc = "%s %s" % (self.tsAwesomeSolo, self.tsSolo)
      soloScoreMult = 50
      self.engine.data.crowdSound.play()    #liquid
    elif self.guitarSoloAccuracy[i] >= 90.0:
      soloDesc = "%s %s" % (self.tsGreatSolo, self.tsSolo)
      soloScoreMult = 30
      self.engine.data.crowdSound.play()    #liquid
    elif self.guitarSoloAccuracy[i] >= 80.0:
      soloDesc = "%s %s" % (self.tsGoodSolo, self.tsSolo)
      soloScoreMult = 20
    elif self.guitarSoloAccuracy[i] >= 70.0:
      soloDesc = "%s %s" % (self.tsSolidSolo, self.tsSolo)
      soloScoreMult = 10
    elif self.guitarSoloAccuracy[i] >= 60.0:
      soloDesc = "%s %s" % (self.tsOkaySolo, self.tsSolo)
      soloScoreMult = 5
    else:   #0% - 59.9%
      soloDesc = "%s %s" % (self.tsMessySolo, self.tsSolo)
      soloScoreMult = 0
      self.engine.data.failSound.play()    #liquid
    soloBonusScore = soloScoreMult * self.guitars[i].currentGuitarSoloHitNotes
    self.scoring[i].score += soloBonusScore
    if self.coOpType:
      self.coOpScoreCard.score += soloBonusScore
    trimmedSoloNoteAcc = self.decimal(str(self.guitarSoloAccuracy[i])).quantize(self.decPlaceOffset)
    #self.soloReviewText[i] = [soloDesc,str(trimmedSoloNoteAcc) + "% = " + str(soloBonusScore) + _(" pts")]
    #ptsText = _("pts")
    self.soloReviewText[i] = [soloDesc, 
      "%(soloNoteAcc)s%% = %(soloBonus)d %(pts)s" % \
      {'soloNoteAcc': str(trimmedSoloNoteAcc), 'soloBonus': soloBonusScore, 'pts': self.tsPtsLabel} ]
    self.dispSoloReview[i] = True
    self.soloReviewCountdown[i] = 0
    #reset for next solo
    self.guitars[i].currentGuitarSoloHitNotes = 0
    self.currentGuitarSolo[i] += 1


  def updateGuitarSolo(self, playerNum):
    i = playerNum
    #if self.guitars[i].canGuitarSolo:
    if self.guitars[i].guitarSolo:

      #update guitar solo for player i

      #if we hit more notes in the solo than were counted, update the solo count (for the slop)
      if self.guitars[i].currentGuitarSoloHitNotes > self.currentGuitarSoloTotalNotes[i]:
        self.currentGuitarSoloTotalNotes[i] = self.guitars[i].currentGuitarSoloHitNotes

      if self.guitars[i].currentGuitarSoloHitNotes != self.currentGuitarSoloLastHitNotes[i]:    #changed!
        self.currentGuitarSoloLastHitNotes[i] = self.guitars[i].currentGuitarSoloHitNotes   #update.
        if self.guitarSoloAccuracyDisplayMode > 0:    #if not off:
          tempSoloAccuracy = (float(self.guitars[i].currentGuitarSoloHitNotes)/float(self.currentGuitarSoloTotalNotes[i]) * 100.0)
          trimmedIntSoloNoteAcc = self.decimal(str(tempSoloAccuracy)).quantize(self.decPlaceOffset)
          if self.guitarSoloAccuracyDisplayMode == 1:   #percentage only
            #soloText = str(trimmedIntSoloNoteAcc) + "%"
            self.solo_soloText[i] = "%s%%" % str(trimmedIntSoloNoteAcc)
          elif self.guitarSoloAccuracyDisplayMode == 2:   #detailed
            #soloText = str(self.guitars[i].currentGuitarSoloHitNotes) + "/" + str(self.currentGuitarSoloTotalNotes[i]) + ": " + str(trimmedIntSoloNoteAcc) + "%"
            self.solo_soloText[i] = "%(hitSoloNotes)d/ %(totalSoloNotes)d: %(soloAcc)s%%" % \
              {'hitSoloNotes': self.guitars[i].currentGuitarSoloHitNotes, 'totalSoloNotes': self.currentGuitarSoloTotalNotes[i], 'soloAcc': str(trimmedIntSoloNoteAcc)}
          self.solo_soloText[i] = self.solo_soloText[i].replace("0","O")
  

          if self.fontMode==0:      #0 = oGL Hack, 1=LaminaScreen, 2=LaminaFrames
            self.solo_Tw[i], self.solo_Th[i] = self.solo_soloFont.getStringSize(self.solo_soloText[i],self.solo_txtSize)
            self.solo_boxXOffset[i] = self.solo_xOffset[i]
            
            if self.guitarSoloAccuracyDisplayPos == 0:  #right
              self.solo_xOffset[i] -= self.solo_Tw[i]
              self.solo_boxXOffset[i] -= self.solo_Tw[i]/2
              #soloFont.render(soloText, (xOffset - Tw, yOffset),(1, 0, 0),txtSize)   #right-justified
            elif self.guitarSoloAccuracyDisplayPos == 1:  #centered
              self.solo_xOffset[i] = 0.5 - self.solo_Tw[i]/2
              self.solo_boxXOffset[i] = 0.5
              #soloFont.render(soloText, (0.5 - Tw/2, yOffset),(1, 0, 0),txtSize)   #centered
            elif self.guitarSoloAccuracyDisplayPos == 3:  #racer: rock band 
              if self.hitAccuracyPos == 0: #Center - need to move solo text above this!
                self.solo_yOffset[i] = 0.100    #above Jurgen Is Here
              elif self.jurgPlayer[i] and self.autoPlay:
                self.solo_yOffset[i] = 0.140    #above Jurgen Is Here
              else:   #no jurgens here:
                self.solo_yOffset[i] = 0.175    #was 0.210, occluded notes
              self.solo_xOffset[i] = 0.5 - self.solo_Tw[i]/2
              self.solo_boxXOffset[i] = 0.5
              #soloFont.render(soloText, (0.5 - Tw/2, yOffset),(1, 0, 0),txtSize)   #rock band
            else:   #left
              self.solo_boxXOffset[i] += self.solo_Tw[i]/2
              #soloFont.render(soloText, (xOffset, yOffset),(1, 0, 0),txtSize)   #left-justified

          elif self.fontMode==1:      #0 = oGL Hack, 1=LaminaScreen, 2=LaminaFrames
            #only update if the text will have changed!
            #trying new rendering method...
            tempSurface = self.solo_soloFont.pygameFontRender(self.solo_soloText[i], antialias=False, color=(0,0,255), background=(0,0,0)  )
            # Create a rectangle
            self.soloAcc_Rect[i] = tempSurface.get_rect()
            # Center the rectangle
            self.soloAcc_Rect[i].centerx = self.screenCenterX
            self.soloAcc_Rect[i].centery = self.screenCenterY
            # Blit the text
            #self.engine.video.screen.blit(tempSurface, tempRect)
            self.laminaScreen.surf.blit(tempSurface, self.soloAcc_Rect[i])
            #self.laminaScreen.refresh()         #needs to be called whenever text contents change
            self.laminaScreen.refresh([self.soloAcc_Rect[i]])         #needs to be called whenever text contents change
            #self.laminaScreen.refreshPosition()   #needs to be called whenever camera position changes                        
            #self.laminaScreen.display()

          elif self.fontMode==2:  #0 = oGL Hack, 1=LaminaScreen, 2=LaminaFrames
            #trying new rendering method...
            tempSurface = self.solo_soloFont.pygameFontRender(self.solo_soloText[i], antialias=False, color=(0,0,255), background=(0,0,0)  )
            # Create a rectangle
            tempRect = tempSurface.get_rect()
            # Center the rectangle
            #tempRect.centerx = self.screenCenterX
            #tempRect.centery = self.screenCenterY
            # Blit the text
            #self.engine.video.screen.blit(tempSurface, tempRect)
            self.laminaFrame_soloAcc.surf.blit(tempSurface, tempRect)
            self.laminaFrame_soloAcc.refresh()

          self.guitarSoloShown[i] = True

    else:   #not currently a guitar solo - clear Lamina solo accuracy surface (but only once!)
      if self.guitarSoloShown[i]:
        self.guitarSoloShown[i] = False
        self.currentGuitarSoloLastHitNotes[i] = 1
        if self.fontMode==1 and self.soloAcc_Rect[i]:
          self.laminaScreen.clear()
          self.laminaScreen.refresh(self.soloAcc_Rect[i])
        
        

  def handleWhammy(self, playerNum):
    i = playerNum
    if self.resumeCountdown > 0:    #MFH - conditions to completely ignore whammy
      return

    try:    #since analog axis might be set but joystick not present = crash
      #MFH - adding another nest of logic filtration; don't even want to run these checks unless there are playedNotes present!
      if self.guitars[i].playedNotes:
        #Player i kill / whammy check:
        if self.isKillAnalog[i]:
          if self.CheckForValidKillswitchNote(i):    #if a note has length and is being held enough to get score
          
            #rounding to integers, setting volumes 0-10 and only when changed from last time:
            #want a whammy reading of 0.0 to = full volume, as that's what it reads at idle
            if self.analogKillMode[i] == 2:  #XBOX mode: (1.0 at rest, -1.0 fully depressed)
              self.whammyVol[i] = 1.0 - (round(10* ((self.engine.input.joysticks[self.whichJoy[i]].get_axis(self.whichAxis[i])+1.0) / 2.0 ))/10.0)
            elif self.analogKillMode[i] == 3:  #XBOX Inverted mode: (-1.0 at rest, 1.0 fully depressed)
              self.whammyVol[i] = (round(10* ((self.engine.input.joysticks[self.whichJoy[i]].get_axis(self.whichAxis[i])+1.0) / 2.0 ))/10.0)
            else: #PS2 mode: (0.0 at rest, fluctuates between 1.0 and -1.0 when pressed)
              self.whammyVol[i] = (round(10*(abs(self.engine.input.joysticks[self.whichJoy[i]].get_axis(self.whichAxis[i]))))/10.0)
            if self.whammyVol[i] > 0.0 and self.whammyVol[i] < 0.1:
              self.whammyVol[i] = 0.1
            
            #MFH - simple whammy tail determination:
            if self.whammyVol[i] > 0.1:
              self.killswitchEngaged[i] = True
            else:
              self.killswitchEngaged[i] = False
            
            if self.whammyVol[i] != self.lastWhammyVol[i] and self.whammyVol[i] > 0.1:
              if self.guitars[i].killPoints:
                self.guitars[i].starPower += self.analogKillswitchStarpowerChunkSize
                if self.guitars[i].starPower > 100:
                  self.guitars[i].starPower = 100
              elif (self.guitars[i].starPowerActive and self.whammySavesSP):
                self.guitars[i].starPower += self.analogKillswitchActiveStarpowerChunkSize
                if self.guitars[i].starPower > 100:
                  self.guitars[i].starPower = 100


            self.lastWhammyVol[i] = self.whammyVol[i]
            
            #here, scale whammyVol to match kill volume setting:
            self.targetWhammyVol[i] = self.whammyVol[i] * (1.0 - self.killVolume)
  
            if self.actualWhammyVol[i] < self.targetWhammyVol[i]:
              self.actualWhammyVol[i] += self.whammyVolAdjStep
              whammyVolSet = 1.0 - self.actualWhammyVol[i]
              if self.whammyEffect == 0:    #killswitch
                self.song.setInstrumentVolume(whammyVolSet, self.players[i].part)
              elif self.whammyEffect == 1:    #pitchbend
                self.song.setInstrumentPitch(self.pitchBendLowestFactor+((1.0-self.pitchBendLowestFactor)*self.whammyVol[i]), self.players[i].part)


            elif self.actualWhammyVol[i] > self.targetWhammyVol[i]:
              self.actualWhammyVol[i] -= self.whammyVolAdjStep
              whammyVolSet = 1.0 - self.actualWhammyVol[i]
              if self.whammyEffect == 0:    #killswitch
                self.song.setInstrumentVolume(whammyVolSet, self.players[i].part)
              elif self.whammyEffect == 1:    #pitchbend
                self.song.setInstrumentPitch(self.pitchBendLowestFactor+((1.0-self.pitchBendLowestFactor)*self.whammyVol[i]), self.players[i].part)
            
          elif self.scoring[i].streak > 0:
            self.song.setInstrumentVolume(1.0, self.players[i].part)
            if self.whammyEffect == 1:    #pitchbend
              self.song.resetInstrumentPitch(self.players[i].part)
            self.actualWhammyVol[i] = self.defaultWhammyVol[i]
  
        else:   #digital killswitch:
          if self.CheckForValidKillswitchNote(i):    #if a note has length and is being held enough to get score
            if self.killswitchEngaged[i] == True: #QQstarS:new Fix the killswitch
              if self.guitars[i].isKillswitchPossible() == True:
                self.killswitchEngaged[i] = True
                if self.whammyEffect == 0:    #killswitch
                  self.song.setInstrumentVolume(self.killVolume, self.players[i].part)  #MFH
                elif self.whammyEffect == 1:    #pitchbend
                  self.song.setInstrumentPitch(self.pitchBendLowestFactor+((1.0-self.pitchBendLowestFactor)*self.whammyVol[i]), self.players[i].part)
                if self.guitars[i].killPoints:
                  self.guitars[i].starPower += self.digitalKillswitchStarpowerChunkSize
                  if self.guitars[i].starPower > 100:
                    self.guitars[i].starPower = 100
                elif (self.guitars[i].starPowerActive and self.whammySavesSP):
                  self.guitars[i].starPower += self.digitalKillswitchActiveStarpowerChunkSize
                  if self.guitars[i].starPower > 100:
                    self.guitars[i].starPower = 100

              else:
                self.killswitchEngaged[i] = None
            elif self.scoring[i].streak > 0:
              self.song.setInstrumentVolume(1.0, self.players[i].part)
              if self.whammyEffect == 1:    #pitchbend
                self.song.resetInstrumentPitch(self.players[i].part)
              self.killswitchEngaged[i] = False
          elif self.scoring[i].streak > 0:
            self.song.setInstrumentVolume(1.0, self.players[i].part)
            if self.whammyEffect == 1:    #pitchbend
              self.song.resetInstrumentPitch(self.players[i].part)
            self.killswitchEngaged[i] = False
          else:
            self.killswitchEngaged[i] = False
          
    except Exception, e:
      self.whammyVol[i] = self.defaultWhammyVol[i] 



  def handlePhrases(self, playerNum, playerStreak):
    if self.phrases > 0:
  
      i = playerNum
      
      if (self.coOpType and i == self.coOpPhrase) or not self.coOpType:
        if self.lastStreak[i] < playerStreak:
          textChanged = True
        else:
          textChanged = False
        self.lastStreak[i] = playerStreak
  
        if (playerStreak == 50 or (self.lastStreak[i] < 50 and playerStreak > 50) ) and textChanged:
          #self.displayText[i] = _("50 Note Streak!!!") #kk69: more GH3-like
          #self.newScalingText(i, _("50 Note Streak!!!") )
          self.newScalingText(i, "50 %s" % self.tsNoteStreak)
          #self.streakFlag = "%d" % (i)   #QQstarS:Set [0] to [i] #if player0 streak50, set the flag to 1. 
        #MFH - I think a simple integer modulo would be more efficient here: 
        else:
          streakModulo = playerStreak % 100
          if ( (streakModulo == 0) or (self.lastStreak[i] % 100 > streakModulo) ) and playerStreak > 50 and textChanged:
            #self.displayText[i] = _("%d Note Streak!!!") % playerStreak #kk69: more GH3-like
            #self.newScalingText(i, _("%d Note Streak!!!") % playerStreak )
            #self.newScalingText(i, _("%d Note Streak!!!") % (playerStreak - streakModulo) )
            self.newScalingText(i, "%d %s" % (playerStreak - streakModulo, self.tsNoteStreak) )
            #self.streakFlag = "%d" % (i)  #QQstarS:Set [0] to [i] #if player0 streak50, set the flag to 1.
  
      if self.scaleText[i] >= self.maxDisplayTextScale:
        self.displayTextScale[i] = self.scaleText[i] + self.scaleText2[i]
        if self.scaleText2[i] <= -0.0005:
          self.goingUP[i] = True
        elif self.scaleText2[i] >= 0.0005:
          self.goingUP[i] = False
        if self.goingUP[i]:
          self.scaleText2[i] += self.displayTextScaleStep2
        else:
          self.scaleText2[i] -= self.displayTextScaleStep2
      else:
        self.displayTextScale[i] = self.scaleText[i]
  
      if not self.displayText[i] == None and not self.scaleText[i] >= self.maxDisplayTextScale:
        self.scaleText[i] += self.displayTextScaleStep1
      if self.scaleText[i] > self.maxDisplayTextScale:
        self.scaleText[i] = self.maxDisplayTextScale
      if not self.displayText[i] == None:
        self.textTimer[i] += 1
      if self.textTimer[i] > self.textTimeToDisplay:
        self.textY[i] -= 0.02
      if self.textY[i] < 0:
        self.scaleText[i] = 0
        self.textTimer[i] = 0
        self.displayText[i] = None
        #textChanged = False
        self.textY[i] = .3
        self.scaleText2[i] = 0.0
        self.goingUP[i] = False


  def newScalingText(self, playerNum, text):
      i = playerNum
      self.scaleText[i] = 0
      self.textTimer[i] = 0
      self.textY[i] = .3
      self.scaleText2[i] = 0.0
      self.goingUP[i] = False
      self.displayText[i] = text


  def handlePick(self, playerNum, hopo = False, pullOff = False):
    i = playerNum
    num = playerNum
    guitar = self.guitars[num]

    if self.resumeCountdown > 0:    #MFH - conditions to completely ignore picks
      return



    #MFH - only actually pick if the player has not failed already!
    if self.rock[i] > 0:

      # Volshebnyi - new BRE and drum fills scoring
      if guitar.freestyleActive or (guitar.isDrum and guitar.drumFillsActive):
        if guitar.freestyleActive:  #MFH - only for BREs, not drum fills.  Will depend on BRE sound option when implemented.
          self.song.setInstrumentVolume(1.0, self.players[i].part)  #MFH - ensure that every freestyle pick, the volume for that track is set to 1.0
        pos = self.getSongPosition()
        score = 0
        numFreestyleHits = guitar.freestylePick(self.song, pos, self.controls)
        if numFreestyleHits>0 or guitar.isDrum:
          if guitar.freestyleFirstHit + guitar.freestyleLength < pos :
            guitar.freestyleFirstHit = pos
            if guitar.bigRockLogic == 1 :
                self.guitars[num].freestylePeriod = 1500
                score = 450
                guitar.freestyleBaseScore = 300
                guitar.freestyleBonusFret = random.randint(0,4)
            if guitar.bigRockLogic == 2 :
                guitar.freestylePeriod = 1500
                guitar.freestyleBaseScore = 150
                score = 600 * numFreestyleHits
            if guitar.isDrum:
                guitar.drumFillsHits = 0
            guitar.freestyleLastHit = pos - guitar.freestylePeriod
            for fret in range (0,5):
                guitar.freestyleLastFretHitTime[fret] = pos - guitar.freestylePeriod
                
          if guitar.isDrum:
            guitar.drumFillsHits += 1
            #if guitar.freestyleSP:   #MFH - this logic should be in the run() function, not conditional here...
            #  self.activateSP(num)
            #  guitar.freestyleSP = False
  
          if guitar.bigRockLogic == 0 or guitar.bigRockLogic == 1:
            brzoneremain = ( guitar.freestyleLength - pos + guitar.freestyleFirstHit ) / guitar.freestyleLength
            hitspeed = min(( pos - guitar.freestyleLastHit ) / guitar.freestylePeriod, 1.0)
            if guitar.bigRockLogic == 1 and numFreestyleHits == 1:
              if self.controls.getState(guitar.keys[guitar.freestyleBonusFret]) or ( guitar.isDrum and guitar.freestyleBonusFret>0 and self.controls.getState(guitar.keys[guitar.freestyleBonusFret+4]) ):
                hitspeed = 1.0
                guitar.freestyleBonusFret = random.randint(0,4)
            score = int( score +  guitar.freestyleBaseScore * hitspeed * ( guitar.freestylePercent + ( 100 - guitar.freestylePercent )  * brzoneremain ) / 100 )
            guitar.freestyleLastHit = pos
                
          if guitar.bigRockLogic == 2:
            if self.controls.getState(guitar.keys[0]):
              hitspeed = min((pos - guitar.freestyleLastFretHitTime[0]) / guitar.freestylePeriod, 1.0)
              score += guitar.freestyleBaseScore * hitspeed
            for fret in range (1,5):
              if self.controls.getState(guitar.keys[fret]) or ( guitar.isDrum and self.controls.getState(guitar.keys[fret+4])):
                hitspeed = min((pos - guitar.freestyleLastFretHitTime[fret]) / guitar.freestylePeriod, 1.0)
                score += guitar.freestyleBaseScore * hitspeed
            if numFreestyleHits > 0:    #MFH - to prevent a float division!
              score = int ( score / numFreestyleHits )
          if self.controls.getState(guitar.keys[0]):
            guitar.freestyleLastFretHitTime[0] = pos
          for fret in range (1,5):
            if self.controls.getState(guitar.keys[fret]) or ( guitar.isDrum and self.controls.getState(guitar.keys[fret+4])):
              guitar.freestyleLastFretHitTime[fret] = pos
          
          #MFH - Add all BRE score to a temporary score accumulator with a separate display box
          #   and only reward if all notes after the BRE are hit without breaking streak!
          if guitar.freestyleActive:   #MFH - only want to add the score if this is a BRE - drum fills get no scoring...
            if self.coOpType:
              self.scoring[num].endingScore += score
              self.scoring[num].endingStreakBroken = False
              self.scoring[num].freestyleWasJustActive = True
              self.coOpScoreCard.endingScore += score
              self.coOpScoreCard.endingStreakBroken = False
              self.coOpScoreCard.freestyleWasJustActive = True
            else:
              #self.playerList[num].addScore( score )
              self.scoring[num].endingScore += score
              #also, when this happens, want to set a flag indicating that all of the remaining notes in the song must be hit without
              # breaking streak, or this score will not be kept!
              self.scoring[num].endingStreakBroken = False
              self.scoring[num].freestyleWasJustActive = True
  
        #MFH - also must ensure notes that pass during this time are marked as skipped without resetting the streak
        #missedNotes = self.guitars[num].getMissedNotesMFH(self.song, pos, catchup = True)
        missedNotes = guitar.getMissedNotesMFH(self.song, pos + guitar.earlyMargin, catchup = True)  #MFh - check slightly ahead here.
        for tym, theNote in missedNotes:   #MFH - also want to mark these notes as Played so they don't count against the note total!
          #theNote.played = True
          theNote.skipped = True
          if self.coOpType:
            self.coOpScoreCard.totalStreakNotes -= 1
          else:
            self.scoring[num].totalStreakNotes -= 1
        
      else:
        if guitar.isDrum:
          self.doPick(i)
        else:
          if self.hopoStyle ==  1:   #1 = rf-mod
            self.doPick3RF(i, hopo)
          elif self.hopoStyle == 2 or self.hopoStyle == 3 or self.hopoStyle == 4:  #GH2 style HOPO 
            self.doPick3GH2(i, hopo, pullOff)
          else:   #2 = no HOPOs
            self.doPick(i)

  def handleJurgen(self, pos):
    #chordFudge = 1   #MFH - was 10 - #myfingershurt - needed to detect chords
    chordFudge = self.song.track[0].chordFudge
    if self.autoPlay or self.assisting:
      for i,guitar in enumerate(self.guitars):
  
        #Allow Jurgen per player...Spikehead777
        if self.jurg == 2: #All players
          self.jurgPlayer[i] = True
        else:
          if self.jurg == i: #if it is this player
            self.jurgPlayer[i] = True
          else: #and if not
            if self.playerAssist[i] == 0: #and no assist
              continue
        
        if self.jurgenLogic == 0:   #original FoF / RF-Mod style Jurgen Logic (cannot handle fast notes / can only handle 1 strum per notewindow)
          notes = guitar.getRequiredNotesMFH(self.song, pos)  #mfh - needed updatin' 
          notes = [note.number for time, note in notes]
          changed = False
          held = 0
          for n, k in enumerate(self.keysList[i]):
            if (self.autoPlay and self.jurgPlayer[i]) or (k == self.guitars[i].keys[4] and self.playerAssist[i] == 2) or ((k == self.guitars[i].keys[4] or k == self.guitars[i].keys[3]) and self.playerAssist[i] == 1) or (self.playerAssist[i] == 3 and k == self.guitars[i].keys[0]):
              if n in notes and not self.controls.getState(k):
                changed = True
                self.controls.toggle(k, True)
                self.keyPressed3(None, 0, k)  #mfh
              elif not n in notes and self.controls.getState(k):
                changed = True
                self.controls.toggle(k, False)
                self.keyReleased3(k)    #mfh
              if self.controls.getState(k):
                held += 1
            
          #if changed and held and not self.playerList[i].part.text == "Drums":  #dont need the extra pick for drums
          if changed and held and not guitar.isDrum:  #dont need the extra pick for drums
            #myfingershurt:
            self.handlePick(i)
        
        elif self.jurgenLogic == 1:   #Jurgen logic style MFH-Early -- will separate notes out by time index, with chord slop detection, and strum every note
          #MFH - Jurgen needs some logic that can handle notes that may be coming too fast to retrieve one set at a time
          notes = guitar.getRequiredNotesMFH(self.song, pos)  #mfh - needed updatin' 
          
          #now, want to isolate the first note or set of notes to strum - then do it, and then release the controls
          if notes:
            jurgStrumTime = notes[0][0]
            jurgStrumNotes = [note.number for time, note in notes if abs(time-jurgStrumTime) <= chordFudge]
          else:
            jurgStrumNotes = []
          
          changed = False
          held = 0
  
          for n, k in enumerate(self.keysList[i]):
            
            if (self.autoPlay and self.jurgPlayer[i]) or (k == self.guitars[i].keys[4] and self.playerAssist[i] == 2) or ((k == self.guitars[i].keys[4] or k == self.guitars[i].keys[3]) and self.playerAssist[i] == 1) or (self.guitars[i].isDrum and self.playerAssist[i] == 3 and k == self.guitars[i].keys[0]):
              if n in jurgStrumNotes and not self.controls.getState(k):
                changed = True
                self.controls.toggle(k, True)
                self.keyPressed(None, 0, k)  #mfh
              elif not n in jurgStrumNotes and self.controls.getState(k):
                changed = True
                self.controls.toggle(k, False)
                self.keyReleased(k)    #mfh
              if self.controls.getState(k):
                held += 1
          #if changed and held and not self.playerList[i].part.text == "Drums":  #dont need the extra pick for drums
          if changed and held and not guitar.isDrum:  #dont need the extra pick for drums
            #myfingershurt:
            self.handlePick(i)
  
        elif self.jurgenLogic == 2:   #Jurgen logic style MFH-OnTime1 -- Have Jurgen attempt to strum on time instead of as early as possible
          #This method simply shrinks the note retrieval window to only notes that are on time and late.  No early notes are even considered.
          #MFH - Jurgen needs some logic that can handle notes that may be coming too fast to retrieve one set at a time
          notes = guitar.getRequiredNotesForJurgenOnTime(self.song, pos)  #mfh - needed updatin' 
          
          #now, want to isolate the first note or set of notes to strum - then do it, and then release the controls
          if notes:
            jurgStrumTime = notes[0][0]
            jurgStrumNotes = [note.number for time, note in notes if abs(time-jurgStrumTime) <= chordFudge]
          else:
            jurgStrumNotes = []
          
          changed = False
          held = 0
  
          for n, k in enumerate(self.keysList[i]):
            if (self.autoPlay and self.jurgPlayer[i]) or (k == self.guitars[i].keys[4] and self.playerAssist[i] == 2) or ((k == self.guitars[i].keys[4] or k == self.guitars[i].keys[3]) and self.playerAssist[i] == 1) or (self.guitars[i].isDrum and self.playerAssist[i] == 3 and k == self.guitars[i].keys[0]):
              if n in jurgStrumNotes and not self.controls.getState(k):
                changed = True
                self.controls.toggle(k, True)
                self.keyPressed(None, 0, k)  #mfh
              elif not n in jurgStrumNotes and self.controls.getState(k):
                changed = True
                self.controls.toggle(k, False)
                self.keyReleased(k)    #mfh
              if self.controls.getState(k):
                held += 1
          #if changed and held and not self.playerList[i].part.text == "Drums":  #dont need the extra pick for drums
          if changed and held and not guitar.isDrum:  #dont need the extra pick for drums
            #myfingershurt:
            self.handlePick(i)
  
        elif self.jurgenLogic == 3:   #Jurgen logic style MFH-OnTime2 -- Have Jurgen attempt to strum on time instead of as early as possible
          #This method retrieves all notes in the window and only attempts to play them as they pass the current position, like a real player
          notes = guitar.getRequiredNotesMFH(self.song, pos)  #mfh - needed updatin' 
          
          
          
          #now, want to isolate the first note or set of notes to strum - then do it, and then release the controls
          if notes:
            jurgStrumTime = notes[0][0]
            jurgStrumNotes = [note.number for time, note in notes if abs(time-jurgStrumTime) <= chordFudge]
          else:
            jurgStrumTime = 0
            jurgStrumNotes = []
          
          changed = False
          held = 0
  
          #MFH - check if jurgStrumTime is close enough to the current position (or behind it) before actually playing the notes:
          if not notes or jurgStrumTime <= (pos + 30):
            
            for n, k in enumerate(self.keysList[i]):
              if (self.autoPlay and self.jurgPlayer[i]) or (k == self.guitars[i].keys[4] and self.playerAssist[i] == 2) or ((k == self.guitars[i].keys[4] or k == self.guitars[i].keys[3]) and self.playerAssist[i] == 1) or (self.guitars[i].isDrum and self.playerAssist[i] == 3 and k == self.guitars[i].keys[0]):
                if n in jurgStrumNotes and not self.controls.getState(k):
                  changed = True
                  self.controls.toggle(k, True)
                  self.keyPressed(None, 0, k)  #mfh
                elif not n in jurgStrumNotes and self.controls.getState(k):
                  changed = True
                  self.controls.toggle(k, False)
                  self.keyReleased(k)    #mfh
                if self.controls.getState(k):
                  held += 1
            #if changed and held and not self.playerList[i].part.text == "Drums":  #dont need the extra pick for drums
            if changed and held and not guitar.isDrum:  #dont need the extra pick for drums
              #myfingershurt:
              self.handlePick(i)
            #MFH - release all frets - who cares about held notes, I want a test player (actually if no keyReleased call, will hold notes fine)
            for n, k in enumerate(self.keysList[i]):
              if (self.autoPlay and self.jurgPlayer[i]) or (k == self.guitars[i].keys[4] and self.playerAssist[i] == 2) or ((k == self.guitars[i].keys[4] or k == self.guitars[i].keys[3]) and self.playerAssist[i] == 1) or (self.guitars[i].isDrum and self.playerAssist[i] == 3 and k == self.guitars[i].keys[0]):
                if self.controls.getState(k):
                  self.controls.toggle(k, False)
  

  def rockmeterDecrease(self, playerNum):
    i = playerNum
    rockMinusAmount = 0 #akedrou - simplify the various incarnations of minusRock.
    if self.guitars[i].isDrum: 
      self.drumStart = True
      if not self.drumScoringEnabled:   #MFH - ignore when drum scoring is disabled
        return

    if self.starNotesMissed[i] or self.guitars[i].isStarPhrase:
      self.guitars[i].isStarPhrase = True
      self.guitars[i].spEnabled = False
      #self.guitars[i].spNote = False 

    if not self.failingEnabled or self.practiceMode:
      return

    if self.battle and self.numOfPlayers > 1: #battle mode
      if self.notesMissed[i]: #QQstarS:Set [i] to [i]
        self.minusRock[i] += self.minGain/self.multi[i]
        #self.rock[i] -= self.minusRock[i]/self.multi[i]
        if self.plusRock[i] > self.pluBase:
          self.plusRock[i] -= self.pluGain*2.0/self.multi[i]
        if self.plusRock[i] <= self.pluBase:
          self.plusRock[i] = self.pluBase/self.multi[i]
      if self.lessMissed[i]: #QQstarS:Set [i] to [i]
        self.minusRock[i] += self.minGain/5.0/self.multi[i]
        #self.rock[i] -= self.minusRock[i]/5.0/self.multi[i]
        if self.plusRock[i] > self.pluBase:
          self.plusRock[i] -= self.pluGain/2.5/self.multi[i]
    
    elif (self.coOp or self.coOpGH) and self.numOfPlayers > 1: #co-op mode
      if self.notesMissed[i]:
        self.minusRock[self.coOpPlayerMeter] += self.minGain/self.multi[i]
        rockMinusAmount = self.minusRock[self.coOpPlayerMeter]/self.multi[i]
        self.rock[self.coOpPlayerMeter] -= rockMinusAmount
        if self.plusRock[self.coOpPlayerMeter] > self.pluBase:
          self.plusRock[self.coOpPlayerMeter] -= self.pluGain*2.0/self.multi[i]
        if self.plusRock[self.coOpPlayerMeter] <= self.pluBase:
          self.plusRock[self.coOpPlayerMeter] = self.pluBase/self.multi[i]
      if self.lessMissed[i]:
        self.minusRock[self.coOpPlayerMeter] += self.minGain/5.0/self.multi[i]
        rockMinusAmount = self.minusRock[0]/5.0/self.multi[i]
        self.rock[self.coOpPlayerMeter] -= rockMinusAmount
        if self.plusRock[self.coOpPlayerMeter] > self.pluBase:
          self.plusRock[self.coOpPlayerMeter] -= self.pluGain/2.5/self.multi[i]
      if (self.rock[self.coOpPlayerMeter]/self.rockMax <= 0.667) and ((self.rock[self.coOpPlayerMeter]+rockMinusAmount)/self.rockMax > 0.667): #akedrou
        self.playersInGreen -= 1
        
    elif self.coOpRB and self.numOfPlayers > 1: #RB co-op mode
      if self.notesMissed[i]:
        self.minusRock[i] += self.minGain/self.coOpMulti
        if self.numDeadPlayers > 0:
          self.minusRock[self.coOpPlayerMeter] += self.minGain/self.coOpMulti
          rockMinusAmount = self.minusRock[self.coOpPlayerMeter]/self.coOpMulti
          self.rock[self.coOpPlayerMeter] -= rockMinusAmount/self.numOfPlayers
        self.rock[i] -= self.minusRock[i]/self.coOpMulti
        if self.plusRock[i] > self.pluBase:
          self.plusRock[i] -= self.pluGain*2.0/self.coOpMulti
        if self.plusRock[i] <= self.pluBase:
          self.plusRock[i] = self.pluBase/self.coOpMulti
      if self.lessMissed[i]:
        self.minusRock[i] += self.minGain/5.0/self.coOpMulti
        if self.numDeadPlayers > 0:
          self.minusRock[self.coOpPlayerMeter] += self.minGain/5.0/self.coOpMulti
          rockMinusAmount = self.minusRock[i]/5.0/self.coOpMulti
          self.rock[self.coOpPlayerMeter] -= rockMinusAmount/(self.numOfPlayers - self.numDeadPlayers)
        self.rock[i] -= self.minusRock[i]/5.0/self.coOpMulti
        if self.plusRock[i] > self.pluBase:
          self.plusRock[i] -= self.pluGain/2.5/self.coOpMulti
        
    else:   #normal mode
      if self.notesMissed[i]:
        self.minusRock[i] += self.minGain/self.multi[i]
        rockMinusAmount = self.minusRock[i]/self.multi[i]
        self.rock[i] -= rockMinusAmount
        if self.plusRock[i] > self.pluBase:
          self.plusRock[i] -= self.pluGain*2.0/self.multi[i]
        if self.plusRock[i] <= self.pluBase:
          self.plusRock[i] = self.pluBase/self.multi[i]
      if self.lessMissed[i]:
        self.minusRock[i] += self.minGain/5.0/self.multi[i]
        rockMinusAmount = self.minusRock[i]/5.0/self.multi[i]
        self.rock[i] -= rockMinusAmount
        if self.plusRock[i] > self.pluBase:
          self.plusRock[i] -= self.pluGain/2.5/self.multi[i]
      if (self.rock[i]/self.rockMax <= 0.667) and ((self.rock[i]+rockMinusAmount)/self.rockMax > 0.667): #akedrou
        self.playersInGreen -= 1

    if self.minusRock[i] <= self.minBase:
      self.minusRock[i] = self.minBase
    if self.plusRock[i] <= self.pluBase:
      self.plusRock[i] = self.pluBase



  def rockmeterIncrease(self, playerNum):
    i = playerNum
    if self.guitars[i].isDrum: 
      self.drumStart = True
    if not self.failingEnabled or self.practiceMode:
      return
    if self.battle and self.numOfPlayers > 1: #battle mode
      if i == 0:
        otherPlayer = 1
      elif i == 1:
        otherPlayer = 0
      if self.notesHit[i]:
        if self.rock[i] < self.rockMax:
          self.plusRock[i] += self.pluGain*self.multi[i]
          if self.plusRock[i] > self.battleMax:
            self.plusRock[i] = self.battleMax
          self.rock[i] += self.plusRock[i]*self.multi[i]
          self.rock[otherPlayer] -= self.plusRock[i]*self.multi[i]
        if self.rock[otherPlayer] < 0:
          self.rock[otherPlayer] = 0
        if self.rock[i] >= self.rockMax:
          self.rock[i] = self.rockMax
        if self.minusRock[i] > self.minBase:
          self.minusRock[i] -= self.minGain/2.0*self.multi[i]
    
    #MFH TODO maintain separate rock status for each player
    elif (self.coOp or self.coOpGH) and self.numOfPlayers > 1: 
      if self.rock[self.coOpPlayerMeter] < self.rockMax:
        self.plusRock[self.coOpPlayerMeter] += self.pluGain*self.multi[i]
        self.rock[self.coOpPlayerMeter] += self.plusRock[self.coOpPlayerMeter]*self.multi[i]
      if self.rock[self.coOpPlayerMeter] >= self.rockMax:
        self.rock[self.coOpPlayerMeter] = self.rockMax
      if self.minusRock[self.coOpPlayerMeter] > self.minBase:
        self.minusRock[self.coOpPlayerMeter] -= self.minGain/2.0*self.multi[i]
      if (self.rock[self.coOpPlayerMeter]/self.rockMax > 0.667) and ((self.rock[self.coOpPlayerMeter]-(self.plusRock[self.coOpPlayerMeter]*self.multi[i]))/self.rockMax <= 0.667):
          self.playersInGreen += 1
          if self.engine.data.cheerSoundFound > 0: #haven't decided whether or not to cut crowdSound with crowdsEnabled = 0, but would have to do it at solos too...
            self.engine.data.crowdSound.play()
          
    elif self.coOpRB and self.numOfPlayers > 1: 
      if self.rock[i] < self.rockMax:
        self.plusRock[i] += self.pluGain*self.coOpMulti
        self.rock[i] += (self.plusRock[i]*self.coOpMulti)
      if self.rock[i] >= self.rockMax:
        self.rock[i] = self.rockMax
      if self.minusRock[i] > self.minBase:
        self.minusRock[i] -= self.minGain/2.0*self.coOpMulti

    
    else:   #normal mode
  
      if self.rock[i] < self.rockMax:
        self.plusRock[i] += self.pluGain*self.multi[i]
        self.rock[i] += self.plusRock[i]*self.multi[i]
      if self.rock[i] >= self.rockMax:
        self.rock[i] = self.rockMax
      if self.minusRock[i] > self.minBase:
        self.minusRock[i] -= self.minGain/2.0*self.multi[i]
      #Log.debug(str((self.rock[i]-(self.plusRock[i]*self.multi[i]))/self.rockMax) % "AND" % str(self.rock[i]/self.rockMax))
      if (self.rock[i]/self.rockMax > 0.667) and ((self.rock[i]-(self.plusRock[i]*self.multi[i]))/self.rockMax <= 0.667):
        self.playersInGreen += 1
        if self.engine.data.cheerSoundFound > 0: #haven't decided whether or not to cut crowdSound with crowdsEnabled = 0, but would have to do it at solos too...
          self.engine.data.crowdSound.play()
          
    if self.minusRock[i] <= self.minBase:
      self.minusRock[i] = self.minBase
    if self.plusRock[i] <= self.pluBase:
      self.plusRock[i] = self.pluBase


  def rockmeterDrain(self):
    self.rock[self.coOpPlayerMeter] -= 15.0
    self.minusRock[self.coOpPlayerMeter] += self.minGain/10/self.coOpMulti


  def run(self, ticks): #QQstarS: Fix this funcion

    if self.song and self.song.readyToGo and not self.pause and not self.failed:
      SceneClient.run(self, ticks)
      if not self.resumeCountdown and not self.pause:
        pos = self.getSongPosition()

        self.song.update(ticks)
        # update stage
      else:
        pos = self.pausePos

      #MFH - new failing detection logic
      if self.failingEnabled:
        #if self.numOfPlayers > 1:
        if self.numOfPlayers > 1 and self.coOpType:
          if self.rock[self.coOpPlayerMeter] <= 0:
            self.failed = True
          else:
            if self.coOpRB:
              for i, player in enumerate(self.playerList):
                if self.rock[i] <= 0 and not self.coOpFailDone[i]:
                  self.guitars[i].coOpFailed = True
                  self.guitars[i].starPower  = 0.0
                  self.engine.data.coOpFailSound.play()
                  self.deadPlayerList.append(i)
                  self.numDeadPlayers += 1
                  self.timesFailed[i] += 1
                  self.crowdsCheering = False
                  self.song.setInstrumentVolume(0.0, self.players[i].part)
                  if self.whammyEffect == 1:    #pitchbend
                    self.song.resetInstrumentPitch(self.players[i].part)
                  self.coOpFailDone[i] = True
        else:
          somebodyStillAlive = False
          for i, player in enumerate(self.playerList):
            if self.rock[i] > 0:
              somebodyStillAlive = True
          if not somebodyStillAlive:    #only if everybody has failed
            self.failed = True
      
      if pos > self.lastDrumNoteTime:   #MFH - disable drum scoring so that the drummer can get down with his bad self at the end of the song without penalty.
        self.drumScoringEnabled = False # ...is that what drummers do?

      
      for i,guitar in enumerate(self.guitars):  
        self.stage.run(pos, guitar.currentPeriod)

      
        if guitar.isDrum and guitar.freestyleSP:    #MFH - this drum fill starpower activation logic should always be checked.
          self.activateSP(i)
          guitar.freestyleSP = False


        #MFH - check for any unplayed notes and for an unbroken streak since the BRE, then award bonus scores
        #akedrou - does not work for co-op.
        if self.coOpType:
          scoreCard = self.coOpScoreCard
          if scoreCard.freestyleWasJustActive and not scoreCard.endingAwarded:
            if scoreCard.lastNoteTime < pos and not scoreCard.endingStreakBroken:
              Log.debug("Big Rock Ending bonus awarded for co-op players! %d points." % scoreCard.endingScore)
              if scoreCard.endingScore > 0:
                scoreCard.addEndingScore()
                self.engine.data.starActivateSound.play()
              scoreCard.endingAwarded = True
        else:
          scoreCard = self.scoring[i]
          if scoreCard.freestyleWasJustActive and not scoreCard.endingAwarded:   
            if scoreCard.lastNoteEvent and not scoreCard.endingStreakBroken:
              if scoreCard.lastNoteEvent.played or scoreCard.lastNoteEvent.hopod:
                Log.debug("Big Rock Ending bonus awarded for player %d: %d points" % (i, scoreCard.endingScore) )
                if scoreCard.endingScore > 0:
                  #thePlayer.score += thePlayer.endingScore
                  scoreCard.addEndingScore()
                  #thePlayer.endingScore = 0
                  self.engine.data.starActivateSound.play()
                scoreCard.endingAwarded = True
                #thePlayer.freestyleWasJustActive = False




        if guitar.starPowerGained == True:
          if self.unisonActive and self.inUnison[i]:
            self.unisonEarn[i] = True
          if self.coOpGH:
            self.coOpStarPower += (25 * self.numOfPlayers) #lets 2 SP phrases give SP
            if self.coOpStarPower > (100 * self.numOfPlayers):
              self.coOpStarPower = (100 * self.numOfPlayers)
            if self.coOpStarPower >= (50 * self.numOfPlayers) and not guitar.starPowerActive:
              self.engine.data.starReadySound.play()
            else:
              self.engine.data.starSound.play()
            if guitar.isDrum and self.autoDrumStarpowerActivate == 0 and self.numDrumFills < 2:
              self.activateSP(i)
          else:
            #myfingershurt: auto drum starpower activation option:
            if guitar.isDrum and self.autoDrumStarpowerActivate == 0 and self.numDrumFills < 2:
              self.activateSP(i)
            if guitar.starPower >= 50 and not guitar.starPowerActive:
              self.engine.data.starReadySound.play()
            else:
              self.engine.data.starSound.play()
            


          if self.phrases > 1:
            if self.coOpGH:
              if guitar.starPowerGained and self.coOpStarPower >= (50 * self.numOfPlayers) and not guitar.starPowerActive:
                self.newScalingText(self.coOpPhrase, self.tsStarPowerReady )
            else:
              if guitar.starPower >= 50 and not guitar.starPowerActive:  #QQstarS:Set [0] to [i]
                self.newScalingText(i, self.tsStarPowerReady )
                
          guitar.starPowerGained = False  #QQstarS:Set [0] to [i]

      # update board
      #for i,guitar in enumerate(self.guitars):
        if self.coOpGH:
          for k, theGuitar in enumerate(self.guitars):
            theGuitar.starPower = self.coOpStarPower/self.numOfPlayers
        
        if not guitar.run(ticks, pos, self.controls):
          # done playing the current notes
          self.endPick(i)

        #MFH - ensure this missed notes check doesn't fail you during a freestyle section
        if guitar.freestyleActive or guitar.drumFillsActive:  
          missedNotes = guitar.getMissedNotesMFH(self.song, pos + guitar.lateMargin*2, catchup = True)  #MFH - get all notes in the freestyle section.
          for tym, theNote in missedNotes:   #MFH - also want to mark these notes as Played so they don't count against the note total!
            #theNote.played = True
            theNote.skipped = True
            if self.coOpType:
              self.coOpScoreCard.totalStreakNotes -= 1
            else:
              self.scoring[i].totalStreakNotes -= 1
        else:
          missedNotes = guitar.getMissedNotesMFH(self.song, pos)
          if guitar.paused:
            missedNotes = []
          if missedNotes:
            if guitar.isDrum:
              self.drumStart = True
            self.lessMissed[i] = True  #QQstarS:Set [0] to [i]
            for tym, theNote in missedNotes:  #MFH
              self.scoring[i].notesMissed += 1
              if self.coOpType:
                self.coOpScoreCard.notesMissed += 1
              if theNote.star or theNote.finalStar:
                if self.logStarpowerMisses == 1:
                  Log.debug("SP Miss: run(), note: %d, gameTime: %s" % (theNote.number, self.timeLeft) )
                self.starNotesMissed[i] = True
                if self.unisonActive:
                  self.inUnison[i] = False

          if (self.scoring[i].streak != 0 or not self.processedFirstNoteYet) and not guitar.playedNotes and len(missedNotes) > 0:
            if not self.processedFirstNoteYet:
              self.stage.triggerMiss(pos)
              self.notesMissed[i] = True
            self.processedFirstNoteYet = True
            self.currentlyAnimating = False
            guitar.setMultiplier(1)
            guitar.hopoLast = -1
            self.song.setInstrumentVolume(0.0, self.players[i].part)
            if self.whammyEffect == 1:    #pitchbend
              self.song.resetInstrumentPitch(self.players[i].part)
            self.guitarSoloBroken[i] = True
            if self.coOpType:
              self.coOpScoreCard.streak = 0
              self.coOpScoreCard.endingStreakBroken = True
            self.scoring[i].streak = 0
            self.scoring[i].endingStreakBroken = True   #MFH
            if self.hopoDebugDisp == 1:
              missedNoteNums = [noat.number for time, noat in missedNotes]
              #Log.debug("Miss: run(), found missed note(s)... %s" % str(missedNoteNums) + ", Time left=" + str(self.timeLeft))
              Log.debug("Miss: run(), found missed note(s)... %(missedNotes)s, Song time=%(songTime)s" % \
                {'missedNotes': str(missedNoteNums), 'songTime': str(self.timeLeft)})
  
            guitar.hopoActive = 0
            guitar.wasLastNoteHopod = False
            guitar.sameNoteHopoString = False
            guitar.hopoProblemNoteNum = -1
            #self.problemNotesP1 = []
            #self.problemNotesP2 = []
          #notes = self.guitars[i].getRequiredNotesMFH(self.song, pos)    #MFH - wtf was this doing here?  I must have left it by accident o.o


      #if not self.pause and not self.failed:
      #myfingershurt: Capo's starpower claps on a user setting:
      #if self.starClaps and self.song and len(self.beatTime) > 0 or (self.beatClaps and self.song and len(self.beatTime) > 0):
      if (self.starClaps or self.beatClaps) and len(self.beatTime) > 0:
        ###Capo###
        #Play a sound on each beat on starpower
        clap = False
        if self.playerList[0].practiceMode and self.beatClaps:
          clap = True
        else:
          for i,player in enumerate(self.playerList):
            if self.guitars[i].starPowerActive == True:
              clap = True
              break
        #pos = self.getSongPosition()
        if pos >= (self.beatTime[0] - 100):
          self.beatTime.pop(0)
          if clap == True:
            if self.firstClap == False:
              #self.sfxChannel.setVolume(self.sfxVolume)
              #self.sfxChannel.play(self.engine.data.clapSound)
              self.engine.data.clapSound.play()
            else:
              self.firstClap = False
          else:
            self.firstClap = True
        ###endCapo###
        
      #MFH - new refugees from the render() function:
      if self.theme == 2:
        if self.rbOverdriveBarGlowFadeOut == False:
          self.rbOverdriveBarGlowVisibility = self.rbOverdriveBarGlowVisibility + self.rbOverdriveBarGlowFadeInChunk
        elif self.rbOverdriveBarGlowFadeOut == True:
          self.rbOverdriveBarGlowVisibility = self.rbOverdriveBarGlowVisibility - self.rbOverdriveBarGlowFadeOutChunk

        if self.rbOverdriveBarGlowVisibility >= 1 and self.rbOverdriveBarGlowFadeOut == False:
          self.rbOverdriveBarGlowFadeOut = True
        elif self.rbOverdriveBarGlowVisibility <= 0 and self.rbOverdriveBarGlowFadeOut == True:
          self.rbOverdriveBarGlowFadeOut = False
      
      for playerNum, thePlayer in enumerate(self.playerList):
        self.handleWhammy(playerNum)
        self.handlePhrases(playerNum, self.scoring[i].streak)
        self.updateGuitarSolo(playerNum)
      if self.coOpType:
        self.handlePhrases(self.coOpPhrase, self.coOpScoreCard.streak)
      self.handleJurgen(pos)

      #stage rotation
      #MFH - logic to prevent advancing rotation frames if you have screwed up, until you resume a streak
      if (self.currentlyAnimating and self.missPausesAnim == 1) or self.missPausesAnim == 0:
        self.stage.rotate()
      self.starPowersActive = 0
      self.coOpStarPower = 0
      #MFH - new logic to update the starpower pre-multiplier
      #akedrou - broken up to support RB Co-op properly.
      for i, guitar in enumerate(self.guitars):
        if guitar.starPowerActive: 
          self.multi[i] = 2
          self.starPowersActive += 1
        else:
          self.multi[i] = 1
        if self.coOpGH:
          self.coOpStarPower += guitar.starPower
      if self.coOpRB:
        if self.unisonIndex < len(self.unisonConfirm) and not self.unisonActive: #akedrou - unison bonuses
          while self.unisonConfirm[self.unisonIndex][0] < pos:
            self.unisonIndex += 1
            if len(self.unisonConfirm) == self.unisonIndex:
              break
          if len(self.unisonConfirm) > self.unisonIndex:
            if self.unisonConfirm[self.unisonIndex][0] - pos < self.song.period * 2:
              self.unisonActive = True
              self.firstUnison = True
              self.unisonNum = len(self.unisonPlayers[self.unisonIndex])
        if self.starPowersActive > 0:
          self.coOpMulti = 2 * self.starPowersActive
        else:
          self.coOpMulti = 1
        #MFH - rewritten rockmeter / starpower miss logic, and Faaa's drum sounds:
        #the old logic was ridiculously complicated  
      # For each existing player
      if self.coOpRB:
        oldCoOpRock = self.rock[self.coOpPlayerMeter]
        coOpRock = 0.0
      for i, guitar in enumerate(self.guitars):
        if (self.coOpRB and not guitar.coOpFailed) or not self.coOpRB:
          if self.notesMissed[i] or self.lessMissed[i]:   #(detects missed note or overstrum)
            if guitar.isDrum:
              if self.drumMisses == 0:    #mode: always
                self.rockmeterDecrease(i)
              #elif self.drumMisses == 1 and self.countdownSeconds < 1:    #mode: song start
              elif self.drumMisses == 1 and self.countdown < 1:    #mode: song start
                self.rockmeterDecrease(i)
              elif self.drumMisses == 2 and self.drumStart:    #mode: song start
                self.rockmeterDecrease(i)
            else:   #not drums
              self.rockmeterDecrease(i)
          if self.notesHit[i]:
            self.rockmeterIncrease(i)
          if self.coOpRB:
            coOpRock += self.rock[i]
        else:
          if not guitar.coOpRestart:
            self.rockmeterDrain()
          else:
            oldCoOpRock = 0.0
            coOpRock += self.rock[i]
        self.notesMissed[i] = False 
        self.starNotesMissed[i] = False
        self.notesHit[i] = False 
        self.lessMissed[i] = False 
        if self.unisonActive:
          if self.firstUnison and i in self.unisonPlayers[self.unisonIndex]:
            self.inUnison[i] = True
            self.haveUnison[i] = True
          
          
        #battle failing
        if self.battle and self.numOfPlayers>1:
          if self.rock[i] <= 0:
            #self.displayText[i] = "You Failed!!!!"
            #self.newScalingText(i, _("You Failed!!!!") )
            self.newScalingText(i, self.tsYouFailedBattle )
            #self.streakFlag = str(i)   #QQstarS:Set [0] to [i] #if player0 streak50, set the flag to 1. 
            guitar.actions = [0,0,0]

      if self.coOpRB: #RB co-op meter is just an average until someone dies.
        if self.numDeadPlayers == 0:
          self.rock[self.coOpPlayerMeter] = coOpRock/self.numOfPlayers
          if (self.rock[self.coOpPlayerMeter]/self.rockMax > 0.667) and (oldCoOpRock/self.rockMax <= 0.667):
            self.playersInGreen = 1
            if self.engine.data.cheerSoundFound > 0: #haven't decided whether or not to cut crowdSound with crowdsEnabled = 0, but would have to do it at solos too...
              self.engine.data.crowdSound.play()
        if (self.rock[self.coOpPlayerMeter]/self.rockMax <= 0.667) and (oldCoOpRock/self.rockMax > 0.667):
          self.playersInGreen = 0

      if self.unisonActive: #akedrou unison bonuses
        if self.firstUnison:
          self.firstUnison = False
          self.firstUnisonDone = True
        if pos - self.unisonConfirm[self.unisonIndex][1] > 0 and self.firstUnisonDone:
          for i in range(len(self.inUnison)):
            if self.inUnison[i] != self.haveUnison[i]:
              break
          else:
            if self.engine.data.cheerSoundFound > 0:
              self.engine.data.crowdSound.play()
            for i,guitar in enumerate(self.guitars):
              if self.inUnison[i]:
                guitar.starPower += 25
                if guitar.starPower > 100:
                  guitar.starPower = 100
          self.firstUnisonDone = False
        if pos - self.unisonConfirm[self.unisonIndex][1] > self.song.period * 2:
          self.unisonIndex+=1
          self.unisonActive = False
          self.unisonEarn  = [False for i in self.playerList]
          self.haveUnison = [False for i in self.playerList]
          self.inUnison = [False for i in self.playerList]
      #akedrou Song/Crowd logic
      if self.numDeadPlayers == 0:
        if self.crowdsEnabled == 3 and self.crowdsCheering == False and not self.countdown: #prevents cheer-cut-cheer
          #self.song.setCrowdVolume(self.crowdVolume)
          self.crowdsCheering = True
        elif self.crowdsEnabled == 0 and self.crowdsCheering == True: #setting change
          #self.song.setCrowdVolume(0.0)
          self.crowdsCheering = False
        elif self.crowdsEnabled == 1:
          if self.starPowersActive > 0:
            if self.crowdsCheering == False:
              #self.song.setCrowdVolume(self.crowdVolume)
              self.crowdsCheering = True
          else:
            if self.crowdsCheering == True:
              #self.song.setCrowdVolume(0.0)
              self.crowdsCheering = False
        elif self.crowdsEnabled == 2:
          if self.starPowersActive > 0 or self.playersInGreen > 0:
            if self.crowdsCheering == False:
              #self.song.setCrowdVolume(self.crowdVolume)
              self.crowdsCheering = True
          else:
            if self.crowdsCheering == True:
              #self.song.setCrowdVolume(0.0)
              self.crowdsCheering = False
        
      #Crowd fade-in/out
      if self.crowdsCheering == True and self.crowdFaderVolume < self.crowdVolume:
        self.crowdFaderVolume += self.crowdCheerFadeInChunk
        if self.crowdFaderVolume > self.crowdVolume:
          self.crowdFaderVolume = self.crowdVolume
        self.song.setCrowdVolume(self.crowdFaderVolume)
      
      if self.crowdsCheering == False and self.crowdFaderVolume > 0.0:
        self.crowdFaderVolume -= self.crowdCheerFadeOutChunk
        if self.crowdFaderVolume < 0.0:
          self.crowdFaderVolume = 0.0
        self.song.setCrowdVolume(self.crowdFaderVolume)
            
      if self.countdown > 0: #MFH won't start song playing if you failed or pause
        self.countdown = max(self.countdown - ticks / self.song.period, 0)
        self.countdownSeconds = self.countdown / self.songBPS + 1
        
        if not self.countdown:  #MFH - when countdown reaches zero, will only be executed once
          #RF-mod should we collect garbage when we start?
          self.engine.collectGarbage()
          self.getHandicap()
          self.song.setGuitarVolume(self.guitarVolume)
          self.song.setRhythmVolume(self.rhythmVolume)
          self.song.setBackgroundVolume(self.songVolume)
          self.song.setCrowdVolume(0.0)
          self.song.clearPause()
          self.crowdsCheering = False #catches crowdsEnabled != 3, pause before countdown, set to 3
          self.starPowersActive = 0
          self.playersInGreen = 0
          if self.playerList[0].practiceMode and self.engine.audioSpeedFactor == 1:
            self.playerList[0].startPos[0] -= self.song.period*4
            if self.playerList[0].startPos[0] < 0.0:
              self.playerList[0].startPos[0] = 0.0
            self.song.play(start = self.playerList[0].startPos[0])
          else:
            self.song.play()
      
      if self.resumeCountdown > 0: #unpause delay
        self.resumeCountdown = max(self.resumeCountdown - ticks / self.song.period, 0)
        self.resumeCountdownSeconds = self.resumeCountdown / self.songBPS + 1
        
        if not self.resumeCountdown:
          self.song.unpause()
          self.pause = False
          missedNotes = []
          for guitar in self.guitars:
            guitar.paused = False

      if self.timeLeft == "0:01" and not self.mutedLastSecondYet and self.muteLastSecond == 1:
        self.song.setAllTrackVolumes(0.0)
        self.mutedLastSecondYet = True


      #myfingershurt: this detects the end of the song and displays "you rock"
      if self.countdown <= 0 and not self.song.isPlaying() and not self.done:        
        #must render fail message in render function, set and check flag here
        self.youRock = True

      #myfingershurt: This ends the song after 100 ticks of displaying "you rock" - if the use hasn't paused the game.
      if self.rockFinished and not self.pause:
        self.goToResults()
        return
 
      #MFH
      if self.midiLyricMode == 1 and self.numMidiLyricLines > 0 and (not self.noMoreMidiLineLyrics):   #line-by-line lyrics mode:

        if pos >= (self.nextMidiLyricStartTime-self.lineByLineStartSlopMs): 
          self.currentSimpleMidiLyricLine = self.nextMidiLyricLine

          if ( self.numMidiLyricLines > self.midiLyricLineIndex+1 ):
            self.midiLyricLineIndex += 1
            self.nextMidiLyricStartTime, self.nextMidiLyricLine = self.midiLyricLines[self.midiLyricLineIndex]
          else:
            self.noMoreMidiLineLyrics = True
            
      elif self.midiLyricMode == 2 and self.numMidiLyricLines > 0 and (not self.noMoreMidiLineLyrics):   #MFH - handle 2-line lyric mode with current-word highlighting advancement
        #MFH - first, prepare / handle the active / top line (which will have highlighted words / syllables):
        if pos >= self.nextLyricWordTime:      #time to switch to this word
          if self.nextLyricIsOnNewLine:
            self.activeMidiLyricLineIndex += 1
            self.activeMidiLyricWordSubIndex = 0
            self.nextLyricIsOnNewLine = False
            self.activeMidiLyricLine_GreyWords = ""
            self.activeMidiLyricLine_GreenWords = "%s " % self.nextLyricEvent.text
            
            self.numWordsInCurrentMidiLyricLine = 0
            for nextLyricTime, nextLyricEvent in self.midiLyricLineEvents[self.activeMidiLyricLineIndex]:   #populate the first active line
              self.numWordsInCurrentMidiLyricLine += 1
            
            if self.numWordsInCurrentMidiLyricLine > self.activeMidiLyricWordSubIndex+1:  #there is another word in this line
              self.activeMidiLyricWordSubIndex += 1
              self.nextLyricWordTime, self.nextLyricEvent = self.midiLyricLineEvents[self.activeMidiLyricLineIndex][self.activeMidiLyricWordSubIndex]
              self.activeMidiLyricLine_WhiteWords = ""
              for nextLyricTime, nextLyricEvent in self.midiLyricLineEvents[self.activeMidiLyricLineIndex]:
                if nextLyricTime > pos:
                  self.activeMidiLyricLine_WhiteWords = "%s %s" % (self.activeMidiLyricLine_WhiteWords, nextLyricEvent.text)
          
          else:   #next lyric is on the same line
            if self.activeMidiLyricWordSubIndex > 0:  #set previous word as grey
              lastLyricTime, lastLyricEvent = self.midiLyricLineEvents[self.activeMidiLyricLineIndex][self.activeMidiLyricWordSubIndex-1]
              self.activeMidiLyricLine_GreyWords = "%s%s " % (self.activeMidiLyricLine_GreyWords, lastLyricEvent.text)
            self.activeMidiLyricLine_GreenWords = "%s " % self.nextLyricEvent.text
            if self.numWordsInCurrentMidiLyricLine > self.activeMidiLyricWordSubIndex+1:  #there is another word in this line
              self.activeMidiLyricWordSubIndex += 1
              self.nextLyricWordTime, self.nextLyricEvent = self.midiLyricLineEvents[self.activeMidiLyricLineIndex][self.activeMidiLyricWordSubIndex]
              self.activeMidiLyricLine_WhiteWords = ""
              for nextLyricTime, nextLyricEvent in self.midiLyricLineEvents[self.activeMidiLyricLineIndex]:
                if nextLyricTime > pos:
                  self.activeMidiLyricLine_WhiteWords = "%s %s" % (self.activeMidiLyricLine_WhiteWords, nextLyricEvent.text)
        
            else:   #no more words in this line
              if self.numMidiLyricLines > self.activeMidiLyricLineIndex+1:  #there is another line
                self.nextLyricIsOnNewLine = True
                self.nextLyricWordTime, self.nextLyricEvent = self.midiLyricLineEvents[self.activeMidiLyricLineIndex+1][0]
                self.activeMidiLyricLine_WhiteWords = ""


              else:   #no more lines
                self.noMoreMidiLineLyrics = True
                self.activeMidiLyricLine_WhiteWords = ""
                self.currentSimpleMidiLyricLine = ""
                #Log.notice("No more MIDI lyric lines to handle!")

          #MFH - then, prepare / handle the next / bottom line (which will just be a simple line with all white text):  
          if self.numMidiLyricLines > self.activeMidiLyricLineIndex+1: 
            tempTime, self.currentSimpleMidiLyricLine = self.midiLyricLines[self.activeMidiLyricLineIndex+1]
          else:
            self.currentSimpleMidiLyricLine = ""



  def endPick(self, num):
    score = self.getExtraScoreForCurrentlyPlayedNotes(num)
    if not self.guitars[num].endPick(self.song.getPosition()):
      #if self.hopoDebugDisp == 1:
      #  Log.debug("MFH: An early sustain release was detected, and it was deemed too early, and muting was attempted.")
      if self.muteSustainReleases > 0:
        self.song.setInstrumentVolume(0.0, self.players[num].part)
    #elif self.hopoDebugDisp == 1:
    #  Log.debug("MFH: An early sustain release was detected, and it was not deemed too early, so muting was not attempted.")

    if score != 0:
      scoreTemp = score*self.multi[num]
      if self.coOpType:
        if not self.coOpGH:
          self.coOpScoreCard.score += (scoreTemp*self.scoring[num].getScoreMultiplier())
        else: #shared mult
          self.coOpScoreCard.addScore(scoreTemp)
      else:
        self.scoring[num].addScore(scoreTemp)

  def render3D(self):
    self.stage.render(self.visibility)
    
  def renderGuitar(self):
    for i in range(self.numOfPlayers):
      self.engine.view.setViewport(self.numOfPlayers,i)
      if self.theme == 0 or self.theme == 1 or self.theme == 2:
        if not self.pause and not self.failed:
          self.guitars[i].render(self.visibility, self.song, self.getSongPosition(), self.controls, self.killswitchEngaged[i])  #QQstarS: new
      else:
        self.guitars[i].render(self.visibility, self.song, self.getSongPosition(), self.controls, self.killswitchEngaged[i]) #QQstarS: new

    for i, player in enumerate(self.playerList):
      if self.coOp or self.coOpGH:
        if self.rock[self.coOpPlayerMeter]< self.rockMax/3.0 and self.failingEnabled:
          self.guitars[i].isFailing = True
        else:
          self.guitars[i].isFailing = False
      elif self.coOpRB:
        if self.rock[i]< self.rockMax/3.0 and self.failingEnabled:
          self.guitars[i].isFailing = True
        elif self.numDeadPlayers > 0 and self.rock[self.coOpPlayerMeter]< self.rockMax/6.0 and self.failingEnabled:
          self.guitars[i].isFailing = True
        else:
          self.guitars[i].isFailing = False
      else:
        #if self.rock[i]< self.rockMax/3.0:
        if self.rock[i]< self.rockMax/3.0 and self.failingEnabled:
          self.guitars[i].isFailing = True
        else:
          self.guitars[i].isFailing = False
         
    self.engine.view.setViewport(1,0)
    
    
  def getSongPosition(self):
    if self.song and self.song.readyToGo:
      if not self.done:
        self.lastSongPos = self.song.getPosition()
        return self.lastSongPos - self.countdown * self.song.period
      else:
        # Nice speeding up animation at the end of the song
        return self.lastSongPos + 4.0 * (1 - self.visibility) * self.song.period
    return 0.0


  def screwUp(self, num, controls):
    if self.screwUpVolume > 0.0:
      #self.sfxChannel.setVolume(self.screwUpVolume)
      #if `self.playerList[num].part` == "Bass Guitar":
      if self.guitars[num].isBassGuitar:
        #self.sfxChannel.play(self.engine.data.screwUpSoundBass)
        self.engine.data.screwUpSoundBass.play()
      elif self.guitars[num].isDrum:
        
        if self.drumMisses > 0: #MFH's cleaned-up - Faaa Drum sound

          self.guitars[num].playDrumSounds(controls)

#-          if self.guitars[num].lastFretWasT1:
#-            self.engine.data.T1DrumSound.play()
#-          elif self.guitars[num].lastFretWasT2:
#-            self.engine.data.T2DrumSound.play()
#-          elif self.guitars[num].lastFretWasT3:
#-            self.engine.data.T3DrumSound.play()
#-          elif self.guitars[num].lastFretWasC:
#-            self.engine.data.CDrumSound.play()

        else:
          self.engine.data.screwUpSoundDrums.play()   #plays random drum sounds
      else:   #guitar
        self.engine.data.screwUpSound.play()
      


  def doPick(self, num):
    if not self.song:
      return

    pos = self.getSongPosition()
    
    if self.guitars[num].playedNotes:
      # If all the played notes are tappable, there are no required notes and
      # the last note was played recently enough, ignore this pick
      if self.guitars[num].areNotesTappable(self.guitars[num].playedNotes) and \
         not self.guitars[num].getRequiredNotes(self.song, pos) and \
         pos - self.lastPickPos[num] <= self.song.period / 2:
        return
      self.endPick(num)

    self.lastPickPos[num] = pos
    
    if self.coOpType:
      scoreCard = self.coOpScoreCard
    else:
      scoreCard = self.scoring[num]

    
    self.killswitchEngaged[num] = False   #always reset killswitch status when picking / tapping
    
    #volshebnyi - disable failing if BRE is active
    if self.guitars[num].startPick(self.song, pos, self.controls):
    
      if self.guitars[num].isDrum:
        self.drumStart = True
      self.song.setInstrumentVolume(self.guitarVolume, self.playerList[num].part)
      self.currentlyAnimating = True
      
      self.notesHit[num] = True #QQstarS:Set [0] to [i]
      
      tempScoreValue = len(self.guitars[num].playedNotes) * self.baseScore * self.multi[num]
      if self.coOpType and not self.coOpGH:
        scoreCard.score += (tempScoreValue*self.scoring[num].getScoreMultiplier())
      else:
        self.scoring[num].addScore(tempScoreValue) 
      
      scoreCard.notesHit += 1
      scoreCard.streak += 1
      if self.coOpType:
        self.scoring[num].notesHit += 1
        self.scoring[num].streak += 1
      scoreCard.updateAvMult()
      star = scoreCard.stars
      a = scoreCard.getStarScores()
      if a > star and self.engine.data.starDingSoundFound and ((self.inGameStars == 1 and self.theme == 2) or self.inGameStars == 2):
        self.engine.data.starDingSound.play()
      
      self.stage.triggerPick(pos, [n[1].number for n in self.guitars[num].playedNotes])
      if self.coOpGH:
        if scoreCard.streak%10 == 0:
          self.lastMultTime[num] = pos
          self.guitars[num].setMultiplier(scoreCard.getScoreMultiplier())
      else:
        if self.scoring[num].streak % 10 == 0:
          self.lastMultTime[num] = pos
          self.guitars[num].setMultiplier(self.scoring[num].getScoreMultiplier())

      #myfingershurt
      if self.showAccuracy:
        self.accuracy[num] = self.guitars[num].playedNotes[0][0] - pos
        self.dispAccuracy[num] = True

      isFirst = True
      noteList = self.guitars[num].playedNotes
      for tym, noat in noteList:
        if noat.star and isFirst:
          self.guitars[num].isStarPhrase = True
        isFirst = False

    else:
      ApplyPenalty = True
      if self.guitars[num].isDrum:
        if self.guitars[num].drumFillWasJustActive:
          ApplyPenalty = False
          self.guitars[num].freestylePick(self.song, pos, self.controls)    #MFH - to allow late drum fill SP activation
          self.guitars[num].drumFillWasJustActive = False

      if ApplyPenalty:
        self.song.setInstrumentVolume(0.0, self.playerList[num].part)
        if self.whammyEffect == 1:    #pitchbend
          self.song.resetInstrumentPitch(self.playerList[num].part)
        scoreCard.streak = 0
        if self.coOpType:
          self.scoring[num].streak = 0
          self.scoring[num].endingStreakBroken = True
        self.guitars[num].setMultiplier(1)
        self.currentlyAnimating = False
        self.stage.triggerMiss(pos)
        self.guitarSoloBroken[num] = True
        scoreCard.endingStreakBroken = True   #MFH
        self.notesMissed[num] = True #QQstarS:Set [0] to [i]
  
        isFirst = True
        noteList = self.guitars[num].matchingNotes
        for tym, noat in noteList:
          if (noat.star or noat.finalStar) and isFirst:
            self.starNotesMissed[num] = True
          isFirst = False
  
        self.screwUp(num, self.controls) #MFH - call screw-up sound handling function
  
        #myfingershurt: ensure accuracy display off when miss
        self.dispAccuracy[num] = False

    #myfingershurt: bass drum sound play
    if self.guitars[num].isDrum and self.bassKickSoundEnabled:
      self.guitars[num].playDrumSounds(self.controls, playBassDrumOnly = True)
      #if self.guitars[num].lastFretWasBassDrum:
      #  #self.sfxChannel.setVolume(self.screwUpVolume)
      #  self.engine.data.bassDrumSound.play()


  def doPick2(self, num, hopo = False):
    if not self.song:
      return
  
    pos = self.getSongPosition()
    #clear out any missed notes before this pick since they are already missed by virtue of the pick
    missedNotes = self.guitars[num].getMissedNotes(self.song, pos, catchup = True)
    
    if self.coOpType:
      scoreCard = self.coOpScoreCard
    else:
      scoreCard = self.scoring[num]

    if len(missedNotes) > 0:
      self.processedFirstNoteYet = True
      scoreCard.streak = 0
      if self.coOpType:
        self.scoring[num].streak = 0
        self.scoring[num].endingStreakBroken = True
      self.guitars[num].setMultiplier(1)
      self.guitars[num].hopoActive = 0
      self.guitars[num].wasLastNoteHopod = False
      self.guitars[num].hopoLast = -1
      self.guitarSoloBroken[num] = True
      scoreCard.endingStreakBroken = True   #MFH

      self.notesMissed[num] = True #QQstarS:Set [0] to [i]
      for tym, theNote in missedNotes:  #MFH
        if theNote.star or theNote.finalStar:
          self.starNotesMissed[num] = True
      
      if hopo == True:
        return

    #hopo fudge
    hopoFudge = abs(abs(self.guitars[num].hopoActive) - pos)
    activeList = [k for k in self.keysList[num] if self.controls.getState(k)]

    if len(activeList) == 1 and self.guitars[num].keys[self.guitars[num].hopoLast] == activeList[0]:
      if self.guitars[num].wasLastNoteHopod and hopoFudge > 0 and hopoFudge < self.guitars[num].lateMargin:
        return

    self.killswitchEngaged[num] = False   #always reset killswitch status when picking / tapping
    if self.guitars[num].startPick2(self.song, pos, self.controls, hopo):
      self.song.setInstrumentVolume(self.guitarVolume, self.playerList[num].part)
      if self.guitars[num].playedNotes:
        scoreCard.streak += 1
        self.currentlyAnimating = True
        if self.coOpType:
          self.scoring[num].streak += 1
          self.scoring[num].notesHit += 1

        self.notesHit[num] = True #QQstarS:Set [0] to [i]
        
        scoreCard.notesHit += 1  # glorandwarf: was len(self.guitars[num].playedNotes)
        tempScoreValue = len(self.guitars[num].playedNotes) * self.baseScore * self.multi[num]

      if self.coOpType and not self.coOpGH:
        scoreCard.score += (tempScoreValue*self.scoring[num].getScoreMultiplier())
      else:
        scoreCard.addScore(tempScoreValue)
      
      scoreCard.updateAvMult()
      star = scoreCard.stars
      a = scoreCard.getStarScores()
      if a > star and self.engine.data.starDingSoundFound and ((self.inGameStars == 1 and self.theme == 2) or self.inGameStars == 2):
        self.engine.data.starDingSound.play()
      #self.updateStars(num)
      #self.playerList[num].stars, self.partialStar[num], self.starRatio[num] = self.getStarScores(num)
      self.stage.triggerPick(pos, [n[1].number for n in self.guitars[num].playedNotes])    
      if self.coOpGH:
        if scoreCard.streak%10 == 0:
          self.lastMultTime[num] = pos
          self.guitars[num].setMultiplier(scoreCard.getScoreMultiplier())
      else:
        if self.scoring[num].streak % 10 == 0:
          self.lastMultTime[num] = pos
          self.guitars[num].setMultiplier(self.scoring[num].getScoreMultiplier())
        

      isFirst = True
      noteList = self.guitars[num].playedNotes
      for tym, noat in noteList:
        if noat.star and isFirst:
          self.guitars[num].isStarPhrase = True
        isFirst = False

    else:
      self.guitars[num].hopoActive = 0
      self.guitars[num].wasLastNoteHopod = False
      self.currentlyAnimating = False
      self.guitars[num].hopoLast = -1
      self.song.setInstrumentVolume(0.0, self.playerList[num].part)
      if self.whammyEffect == 1:    #pitchbend
        self.song.resetInstrumentPitch(self.playerList[num].part)
      scoreCard.streak = 0
      if self.coOpType:
        self.scoring[num].streak = 0
        self.scoring[num].endingStreakBroken = True
      self.guitars[num].setMultiplier(1)
      self.stage.triggerMiss(pos)
      self.guitarSoloBroken[num] = True
      scoreCard.endingStreakBroken = True   #MFH

      self.notesMissed[num] = True #QQstarS:Set [0] to [i]

      
      
      isFirst = True
      noteList = self.guitars[num].matchingNotes
      for tym, noat in noteList:
        if (noat.star or noat.finalStar) and isFirst:
          self.starNotesMissed[num] = True
        isFirst = False
      
      self.screwUp(num, self.controls)

#-----------------------
  def doPick3RF(self, num, hopo = False):
    if not self.song:
      return
  
    pos = self.getSongPosition()
    #clear out any past the window missed notes before this pick since they are already missed by virtue of the pick
    missedNotes = self.guitars[num].getMissedNotes(self.song, pos, catchup = True)

    if self.coOpType:
      scoreCard = self.coOpScoreCard
    else:
      scoreCard = self.scoring[num]
    
    if len(missedNotes) > 0:
      self.processedFirstNoteYet = True
      scoreCard.streak = 0
      if self.coOpType:
        self.scoring[num].streak = 0
        self.scoring[num].endingStreakBroken = True
      self.guitars[num].setMultiplier(1)
      self.guitars[num].hopoActive = 0
      self.guitars[num].wasLastNoteHopod = False
      self.guitars[num].hopoLast = -1
      self.guitarSoloBroken[num] = True
      scoreCard.endingStreakBroken = True   #MFH

      self.notesMissed[num] = True  #qqstars 
      for tym, theNote in missedNotes:  #MFH
        if theNote.star or theNote.finalStar:
          self.starNotesMissed[num] = True
        
      if hopo == True:
        return

    #hopo fudge
    hopoFudge = abs(abs(self.guitars[num].hopoActive) - pos)
    activeList = [k for k in self.keysList[num] if self.controls.getState(k)]

    if len(activeList) == 1 and self.guitars[num].keys[self.guitars[num].hopoLast] == activeList[0]:
      if self.guitars[num].wasLastNoteHopod and hopoFudge > 0 and hopoFudge < self.guitars[num].lateMargin:
        return

    self.killswitchEngaged[num] = False   #always reset killswitch status when picking / tapping
    if self.guitars[num].startPick3(self.song, pos, self.controls, hopo):
      self.processedFirstNoteYet = True
      self.song.setInstrumentVolume(self.guitarVolume, self.playerList[num].part)
      #Any previous notes missed, but new ones hit, reset streak counter
      if len(self.guitars[num].missedNotes) != 0:
        scoreCard.streak = 0
        if self.coOpType:
          self.scoring[num].streak = 0
          self.scoring[num].endingStreakBroken = True
        self.guitarSoloBroken[num] = True
        scoreCard.endingStreakBroken = True   #MFH

        self.notesMissed[num] = True  #qqstars

        for chord in self.guitars[num].missedNotes:
          for tym, theNote in chord:  #MFH
            if not theNote.played and (theNote.star or theNote.finalStar):
              self.starNotesMissed[num] = True
        
      isFirst = True
      noteList = self.guitars[num].playedNotes
      for tym, noat in noteList:
        if noat.star and isFirst:
          self.guitars[num].isStarPhrase = True
        isFirst = False

      scoreCard.streak += 1
      self.notesHit[num] = True #qqstars
      self.currentlyAnimating = True        
      scoreCard.notesHit += 1  # glorandwarf: was len(self.guitars[num].playedNotes)
      tempScoreValue = len(self.guitars[num].playedNotes) * self.baseScore * self.multi[num]
      
      if self.coOpType:
        self.scoring[num].streak += 1
        self.scoring[num].notesHit += 1
        if self.coOpGH:
          scoreCard.addScore(tempScoreValue)
        else:
          scoreCard.score += (tempScoreValue*self.scoring[num].getScoreMultiplier())
      else:
        scoreCard.addScore(tempScoreValue)
      
      scoreCard.updateAvMult()
      star = scoreCard.stars
      a = scoreCard.getStarScores()
      
      if a > star and self.engine.data.starDingSoundFound and ((self.inGameStars == 1 and self.theme == 2) or self.inGameStars == 2):
        self.engine.data.starDingSound.play()

      self.stage.triggerPick(pos, [n[1].number for n in self.guitars[num].playedNotes])    
      if self.coOpGH:
        if scoreCard.streak%10 == 0:
          self.lastMultTime[num] = pos
          self.guitars[num].setMultiplier(scoreCard.getScoreMultiplier())
      else:
        if self.scoring[num].streak % 10 == 0:
          self.lastMultTime[num] = pos
          self.guitars[num].setMultiplier(self.scoring[num].getScoreMultiplier())
        
      #myfingershurt
      if self.showAccuracy:
        self.accuracy[num] = self.guitars[num].playedNotes[0][0] - pos
        self.dispAccuracy[num] = True

    else:
      self.currentlyAnimating = False
      self.guitars[num].hopoActive = 0
      self.guitars[num].wasLastNoteHopod = False
      self.guitars[num].hopoLast = 0
      self.song.setInstrumentVolume(0.0, self.playerList[num].part)
      if self.whammyEffect == 1:    #pitchbend
        self.song.resetInstrumentPitch(self.playerList[num].part)
      scoreCard.streak = 0
      if self.coOpType:
        self.scoring[num].streak = 0
        self.scoring[num].endingStreakBroken = True
      self.guitarSoloBroken[num] = True
      scoreCard.endingStreakBroken = True   #MFH
      self.guitars[num].setMultiplier(1)
      self.stage.triggerMiss(pos)

      self.notesMissed[num] = True  #qqstars

      isFirst = True
      noteList = self.guitars[num].matchingNotes
      for tym, noat in noteList:
        if (noat.star or noat.finalStar) and isFirst:
          self.starNotesMissed[num] = True
        isFirst = False

      self.screwUp(num, self.controls)
      
      #myfingershurt: ensure accuracy display off when miss
      self.dispAccuracy[num] = False


#-----------------------
  def doPick3GH2(self, num, hopo = False, pullOff = False): #MFH - so DoPick knows when a pull-off was performed
    if not self.song:
      return

    pos = self.getSongPosition()

    chordFudge = 1  #MFH - was 10  #myfingershurt - needed to detect chords
    
    if self.coOpType:
      scoreCard = self.coOpScoreCard
    else:
      scoreCard = self.scoring[num]

    missedNotes = self.guitars[num].getMissedNotesMFH(self.song, pos, catchup = True)
    if len(missedNotes) > 0:
      self.processedFirstNoteYet = True
      scoreCard.streak = 0
      if self.coOpType:
        self.scoring[num].streak = 0
        self.scoring[num].endingStreakBroken = True
      self.guitarSoloBroken[num] = True
      scoreCard.endingStreakBroken = True   #MFH
      self.guitars[num].setMultiplier(1)
      self.guitars[num].hopoActive = 0
      self.guitars[num].sameNoteHopoString = False
      self.guitars[num].hopoProblemNoteNum = -1
      #self.problemNotesP1 = []
      #self.problemNotesP2 = []
      self.guitars[num].wasLastNoteHopod = False
      self.guitars[num].hopoLast = -1
      self.notesMissed[num] = True #QQstarS:Set [0] to [i]
      for tym, theNote in missedNotes:  #MFH
        if theNote.star or theNote.finalStar:
          if self.logStarpowerMisses == 1:
            Log.debug("SP Miss: doPick3GH2(), foundMissedCatchupNote: %d, gameTime: %s" % (theNote.number, self.timeLeft) )
          self.starNotesMissed[num] = True
          if self.unisonActive:
            self.inUnison[num] = False
      
      if self.hopoDebugDisp == 1:
        missedNoteNums = [noat.number for time, noat in missedNotes]
        #Log.debug("Miss: dopick3gh2(), found missed note(s).... %s" % str(missedNoteNums) + ", Time left=" + str(self.timeLeft))
        Log.debug("Miss: dopick3gh2(), found missed note(s)... %(missedNotes)s, Song time=%(songTime)s" % \
          {'missedNotes': str(missedNoteNums), 'songTime': str(self.timeLeft)})

      if hopo == True:
        return

    #hopo fudge
    hopoFudge = abs(abs(self.guitars[num].hopoActive) - pos)
    activeList = [k for k in self.keysList[num] if self.controls.getState(k)]

    #myfingershurt
    #Perhaps, if I were to just treat all tappable = 3's as problem notes, and just accept a potential overstrum, that would cover all the bases...
    # maybe, instead of checking against a known list of chord notes that might be associated, just track whether or not
    # the original problem note (tappable = 3) is still held.  If it is still held, whether or not it matches the notes, it means
    #  it can still be involved in the problematic pattern - so continue to monitor for an acceptable overstrum.
    
    #On areas where it's just a tappable = 3 note with no other notes in the hitwindow, it will be marked as a problem and then
    # if strummed, that would be considered the acceptable overstrum and it would behave the same.  MUCH simpler logic!



    activeKeyList = []
    #myfingershurt: the following checks should be performed every time so GH2 Strict pull-offs can be detected properly.
    LastHopoFretStillHeld = False
    HigherFretsHeld = False
    problemNoteStillHeld = False

    for n, k in enumerate(self.keysList[num]):
      if self.controls.getState(k):
        activeKeyList.append(k)
        if self.guitars[num].hopoLast == n:
          LastHopoFretStillHeld = True
        elif n > self.guitars[num].hopoLast:
          HigherFretsHeld = True
        if self.guitars[num].hopoProblemNoteNum == n:
          problemNoteStillHeld = True

    #ImpendingProblem = False
    if not hopo and self.guitars[num].wasLastNoteHopod and not self.guitars[num].LastStrumWasChord and not self.guitars[num].sameNoteHopoString:
    #if not hopo and self.guitars[num].wasLastNoteHopod:
      if LastHopoFretStillHeld == True and HigherFretsHeld == False:
        if self.guitars[num].wasLastNoteHopod and hopoFudge >= 0 and hopoFudge < self.guitars[num].lateMargin:
          if self.guitars[num].hopoActive < 0:
            self.guitars[num].wasLastNoteHopod = False
            #if self.hopoDebugDisp == 1:
            #  Log.debug("HOPO Strum ignored: Standard HOPO strum (hopoActive < 0).  Time left=" + str(self.timeLeft))
            return
          elif self.guitars[num].hopoActive > 0:  #make sure it's hopoActive!
            self.guitars[num].wasLastNoteHopod = False
            #if self.hopoDebugDisp == 1:
            #  Log.debug("HOPO Strum ignored: Standard HOPO strum (hopoActive not < 0).  Time left=" + str(self.timeLeft))
            return

    #MFH - here, just check to see if we can release the expectation for an acceptable overstrum:
    if self.guitars[num].sameNoteHopoString and not problemNoteStillHeld:
      self.guitars[num].sameNoteHopoString = False
      self.guitars[num].hopoProblemNoteNum = -1

    self.killswitchEngaged[num] = False   #always reset killswitch status when picking / tapping
    if self.guitars[num].startPick3(self.song, pos, self.controls, hopo):
      self.processedFirstNoteYet = True
      self.song.setInstrumentVolume(self.guitarVolume, self.playerList[num].part)
      #Any previous notes missed, but new ones hit, reset streak counter
      if len(self.guitars[num].missedNotes) > 0:

        if self.hopoDebugDisp == 1  and not self.guitars[num].isDrum:
          #Log.debug("Skipped note(s) detected in startpick3: " + str(self.guitars[num].missedNoteNums))
          problemNoteMatchingList = [(int(tym), noat.number, noat.played) for tym, noat in self.guitars[num].matchingNotes]
          #Log.debug("Skipped note(s) detected in startpick3: " + str(self.guitars[num].missedNoteNums) + ", problemMatchingNotes: " + str(problemNoteMatchingList) + ", activeKeys= " + str(activeKeyList) + ", Time left=" + str(self.timeLeft))
          Log.debug("Skipped note(s) detected in startpick3: %(missedNotes)s, notesToMatch: %(matchNotes)s, activeFrets: %(activeFrets)s, Song time=%(songTime)s" % \
            {'missedNotes': str(self.guitars[num].missedNoteNums), 'matchNotes': str(problemNoteMatchingList), 'activeFrets': str(activeKeyList), 'songTime': str(self.timeLeft)})
      
        scoreCard.streak = 0
        if self.coOpType:
          self.scoring[num].streak = 0
          self.scoring[num].endingStreakBroken = True
        self.guitarSoloBroken[num] = True
        scoreCard.endingStreakBroken = True   #MFH
        self.notesMissed[num] = True #QQstarS:Set [0] to [i]

        for chord in self.guitars[num].missedNotes:
          for tym, theNote in chord:  #MFH
            if not theNote.played and (theNote.star or theNote.finalStar):
              if self.logStarpowerMisses == 1:
                Log.debug("SP Miss: doPick3GH2(), afterStartPick3Ok-foundMissedCatchupNote: %d, gameTime: %s" % (theNote.number, self.timeLeft) )
              self.starNotesMissed[num] = True
              if self.unisonActive:
                self.inUnison[num] = False
        
      isFirst = True
      noteList = self.guitars[num].playedNotes
      for tym, noat in noteList:
        if noat.star and isFirst:
          self.guitars[num].isStarPhrase = True
        isFirst = False

      scoreCard.streak += 1
      self.notesHit[num] = True #QQstarS:Set [0] to [i]
      self.currentlyAnimating = True        

      scoreCard.notesHit += 1  # glorandwarf: was len(self.guitars[num].playedNotes)
      tempScoreValue = len(self.guitars[num].playedNotes) * self.baseScore * self.multi[num]
      
      if self.coOpType:
        self.scoring[num].streak += 1 #needed in co-op GH for RF HO/PO
        self.scoring[num].notesHit += 1
        if self.coOpGH:
          scoreCard.addScore(tempScoreValue)
        else:
          scoreCard.score += (tempScoreValue*self.scoring[num].getScoreMultiplier())
      else:
        scoreCard.addScore(tempScoreValue)
      
      scoreCard.updateAvMult()
      star = scoreCard.stars
      a = scoreCard.getStarScores()
      
      if a > star and self.engine.data.starDingSoundFound and ((self.inGameStars == 1 and self.theme == 2) or self.inGameStars == 2):
        self.engine.data.starDingSound.play()
      
      self.stage.triggerPick(pos, [n[1].number for n in self.guitars[num].playedNotes])    
      if self.scoring[num].streak % 10 == 0:
        self.lastMultTime[num] = self.getSongPosition()
        self.guitars[num].setMultiplier(self.scoring[num].getScoreMultiplier())
      
      if self.showAccuracy:
        self.accuracy[num] = self.guitars[num].playedNotes[0][0] - pos
        self.dispAccuracy[num] = True
      
    else:
      ApplyPenalty = True
      
      if self.hopoDebugDisp == 1:
        sameNoteHopoFlagWas = self.guitars[num].sameNoteHopoString    #MFH - need to store this for debug info
        lastStrumWasChordWas = self.guitars[num].LastStrumWasChord    #MFH - for debug info
        #problemNotesForP1Were = self.problemNotesP1


      if pullOff:   #always ignore bad pull-offs
        ApplyPenalty = False
      
      if (self.hopoStyle == 2 and hopo == True):  #GH2 Strict
        if (self.guitars[num].LastStrumWasChord or (self.guitars[num].wasLastNoteHopod and LastHopoFretStillHeld)):
          ApplyPenalty = False

      if (self.hopoStyle == 4 and hopo == True):  #GH2 Sloppy
        ApplyPenalty = False

      if (self.hopoStyle == 3 and hopo == True):  #GH2
        ApplyPenalty = False
        if not (self.guitars[num].LastStrumWasChord or (self.guitars[num].wasLastNoteHopod and LastHopoFretStillHeld)):
          self.guitars[num].hopoActive = 0
          self.guitars[num].wasLastNoteHopod = False
          self.guitars[num].LastStrumWasChord = False
          self.guitars[num].sameNoteHopoString = False
          self.guitars[num].hopoProblemNoteNum = -1
          self.guitars[num].hopoLast = -1

      if self.guitars[num].sameNoteHopoString:
        #if LastHopoFretStillHeld and not HigherFretsHeld:
        if LastHopoFretStillHeld:
          ApplyPenalty = False
          self.guitars[num].playedNotes = self.guitars[num].lastPlayedNotes   #restore played notes status
          self.guitars[num].sameNoteHopoString = False
          self.guitars[num].hopoProblemNoteNum = -1
        elif HigherFretsHeld:
          self.guitars[num].sameNoteHopoString = False
          self.guitars[num].hopoProblemNoteNum = -1
      
      
      if ApplyPenalty == True:

        self.currentlyAnimating = False
        self.guitars[num].hopoActive = 0
        self.guitars[num].wasLastNoteHopod = False
        self.guitars[num].sameNoteHopoString = False
        self.guitars[num].hopoProblemNoteNum = -1
        self.guitars[num].hopoLast = -1
        self.song.setInstrumentVolume(0.0, self.playerList[num].part)
        if self.whammyEffect == 1:    #pitchbend
          self.song.resetInstrumentPitch(self.playerList[num].part)
        scoreCard.streak = 0
        if self.coOpType:
          self.scoring[num].streak = 0
          self.scoring[num].endingStreakBroken = True
        self.guitarSoloBroken[num] = True
        scoreCard.endingStreakBroken = True   #MFH
        self.guitars[num].setMultiplier(1)
        self.stage.triggerMiss(pos)
        if self.hopoDebugDisp == 1 and not self.guitars[num].isDrum:
          problemNoteMatchingList = [(int(tym), noat.number, noat.played) for tym, noat in self.guitars[num].matchingNotes]  
          #Log.debug("Miss: dopick3gh2(), fail-startpick3()...HigherFretsHeld: " + str(HigherFretsHeld) + ", LastHopoFretHeld: " + str(LastHopoFretStillHeld) + ", lastStrumWasChord: " + str(lastStrumWasChordWas) + ", sameNoteHopoStringFlag: " + str(sameNoteHopoFlagWas) + ", problemNoteMatchingList: " + str(problemNoteMatchingList) + ", activeKeys= " + str(activeKeyList) + ", Time left=" + str(self.timeLeft))
          Log.debug("Miss: dopick3gh2(), fail-startpick3()...HigherFretsHeld: %(higherFrets)s, LastHopoFretHeld: %(lastHopoFret)s, lastStrumWasChord: %(lastStrumChord)s, sameNoteHopoStringFlag: %(sameNoteHopoFlag)s, notesToMatch: %(matchNotes)s, activeFrets: %(activeFrets)s, Song time=%(songTime)s" % \
            {'higherFrets': str(HigherFretsHeld), 'lastHopoFret': str(LastHopoFretStillHeld), 'lastStrumChord': str(lastStrumWasChordWas), 'sameNoteHopoFlag': str(sameNoteHopoFlagWas), 'matchNotes': str(problemNoteMatchingList), 'activeFrets': str(activeKeyList), 'songTime': str(self.timeLeft)})
          
        self.notesMissed[num] = True #QQstarS:Set [0] to [i]

        isFirst = True
        noteList = self.guitars[num].matchingNotes
        for tym, noat in noteList:
          if (noat.star or noat.finalStar) and isFirst:
            if self.logStarpowerMisses == 1:
              Log.debug("SP Miss: doPick3GH2(), afterStartPick3Fail, matchingNote: %d, gameTime: %s" % (noat.number, self.timeLeft) )
            self.starNotesMissed[num] = True
            if self.unisonActive:
              self.inUnison[num] = False
          isFirst = False

        self.screwUp(num, self.controls)

        self.dispAccuracy[num] = False

    #myfingershurt: bass drum sound play
    if self.guitars[num].isDrum and self.bassKickSoundEnabled:
      self.guitars[num].playDrumSounds(self.controls, playBassDrumOnly = True)
      #if self.guitars[num].lastFretWasBassDrum:
      #  #self.sfxChannel.setVolume(self.screwUpVolume)
      #  self.engine.data.bassDrumSound.play()
  
  def activateSP(self, num): #QQstarS: Fix this function, add a element "num"
    if self.coOpGH:
      if self.coOpStarPower >= (50 * self.numOfPlayers) and self.guitars[num].starPowerActive == False:
        time = self.getSongPosition()
        Log.debug("Star Power Activated at: " + str(time))
        self.coOpStarPowerActive[num] = time
        if time - min(self.coOpStarPowerActive) < 300.0:
          self.engine.data.starActivateSound.play()
          for i, guitar in enumerate(self.guitars):
            guitar.starPowerActive = True
            guitar.overdriveFlashCount = 0  #MFH - this triggers the oFlash strings & timer
            guitar.ocount = 0  #MFH - this triggers the oFlash strings & timer
        else:
          if time - self.coOpStarPowerTimer > 1000.0:
            for i, guitar in enumerate(self.guitars):
              Log.debug(str(time - self.coOpStarPowerActive[i]))
              if time - self.coOpStarPowerActive[i] < 300.0:
                continue
              if guitar.isDrum and self.autoDrumStarpowerActivate == 0 and self.numDrumFills < 2:
                self.activateSP(i)
                break
              if self.phrases > 1:
                self.newScalingText(i, self.tsCoOpStarPower )
            self.coOpStarPowerTimer = time
        
    else:
      if self.guitars[num].starPower >= 50 and self.guitars[num].starPowerActive == False: #QQstarS:Set [0] to [i]
        #self.sfxChannel.setVolume(self.sfxVolume)
        #if self.engine.data.cheerSoundFound:
          #self.engine.data.crowdSound.play()
        if self.coOpRB:
          while len(self.deadPlayerList) > 0:
            i = self.deadPlayerList.pop(0) #keeps order intact (with >2 players)
            if self.guitars[i].coOpFailed and self.timesFailed[i]<3:
              self.guitars[i].coOpRescue(self.getSongPosition())
              self.rock[i] = self.rockMax * 0.667
              self.guitars[num].starPower -= 50
              self.engine.data.rescueSound.play()
              self.coOpFailDone[i] = False
              self.numDeadPlayers -= 1
              break
          else:
            self.engine.data.starActivateSound.play()
            self.guitars[num].starPowerActive = True #QQstarS:Set [0] to [i]
        else:
          self.engine.data.starActivateSound.play()
          self.guitars[num].starPowerActive = True #QQstarS:Set [0] to [i]
        self.guitars[num].overdriveFlashCount = 0  #MFH - this triggers the oFlash strings & timer
        self.guitars[num].ocount = 0  #MFH - this triggers the oFlash strings & timer

  def goToResults(self):
    self.ending = True
    if self.song:
      self.song.stop()
      self.done  = True
      noScore = False
      for i,guitar in enumerate(self.guitars):
        self.playerList[i].twoChord = guitar.twoChord
      for i, player in enumerate(self.playerList):
        if self.playerList[0].practiceMode:
          self.scoring[i].score = 0
        if self.scoring[i].score > 0:
          noScore = False
          break
      else:
        if not (self.coOpType and self.coOpScoreCard.score > 0):
          noScore = True

        #Reset Score if Jurgen played -- Spikehead777 - handled by GameResults now. You can watch your score evaporate!
        # if self.jurgPlayer[i]:
          # self.playerList[i].score = 0
        # if self.coOpType and True in self.jurgPlayer:
          # self.coOpScore = 0


      # if not self.engine.audioSpeedFactor == 1:  #MFH - only allow score uploads and unlocking when songs are played at full speed.
        # noScore = True
        # self.changeSong()

      #if self.playerList[0].score == 0:
        #if self.numOfPlayers == 1:
          #noScore = True
          #self.changeSong()
      
      #if self.numOfPlayers == 2:
      #  if self.coOpType:
      #    if self.coOpScore == 0:
      #      noScore = True
      #      self.changeSong()
      #  if self.playerList[0].score == 0 and self.playerList[1].score == 0:
      #    noScore = True
      #    self.changeSong()
      
      
      if not noScore:

        #MFH/akedrou - force one stat update before gameresults just in case:
        self.getHandicap()
        for scoreCard in self.scoring:
          scoreCard.updateAvMult()
          scoreCard.getStarScores()
          if self.coOpType:
            #self.updateStars(self.coOpPlayerIndex, forceUpdate = True)
            self.coOpScoreCard.updateAvMult()
            self.coOpScoreCard.getStarScores()
          
          #akedrou - begin the implementation of the ScoreCard
        
        if self.coOpType:
          scoreList = self.scoring
          scoreList.append(self.coOpScoreCard)
          if self.coOp:
            coOpType = 1
          elif self.coOpRB:
            coOpType = 2
          elif self.coOpGH:
            coOpType = 3
          else:
            coOpType = 1
        else:
          scoreList = self.scoring
          coOpType = 0

        self.engine.view.setViewport(1,0)
        self.session.world.deleteScene(self)
        self.freeResources()
        self.session.world.createScene("GameResultsScene", libraryName = self.libraryName, songName = self.songName, players = self.playerList, scores = scoreList, coOpType = coOpType, careerMode = self.careerMode)
      
      else:
        self.changeSong()

  def keyPressed(self, key, unicode, control = None):
    #RF style HOPO playing
    
    #myfingershurt: drums :)
    if self.guitars[0].isDrum and control in (self.guitars[0].keys):
      #self.doPick(0)
      self.handlePick(0)
      return True  
    elif self.numOfPlayers > 1 and self.guitars[1].isDrum and control in (self.guitars[1].keys):
      #self.doPick(1)
      self.handlePick(1)
      return True

    if self.hopoStyle > 0:  #HOPOs enabled 
      res = self.keyPressed3(key, unicode, control)
      return res

    if not control:
      control = self.controls.keyPressed(key)

    num = self.getPlayerNum(control)

    if control in (self.guitars[num].actions):
      for k in self.keysList[num]:
        if self.controls.getState(k):
          self.keyBurstTimeout[num] = None
          break
      else:
        #self.keyBurstTimeout[num] = self.engine.timer.time + self.keyBurstPeriod
        return True

    if control in (self.guitars[num].actions) and self.song:
      self.doPick(num)
    elif control in self.keysList[num] and self.song:
      # Check whether we can tap the currently required notes
      pos   = self.getSongPosition()
      notes = self.guitars[num].getRequiredNotes(self.song, pos)

      if self.scoring[num].streak > 0 and \
         self.guitars[num].areNotesTappable(notes) and \
         self.guitars[num].controlsMatchNotes(self.controls, notes):
        self.doPick(num)
    elif control in Player.CANCELS:
      if self.ending == True:
        return True
      self.pauseGame()
      self.engine.view.pushLayer(self.menu)
      return True
    elif key >= ord('a') and key <= ord('z'):
      # cheat codes
      n = len(self.enteredCode)
      for code, func in self.cheatCodes:
        if n < len(code):
          if key == code[n]:
            self.enteredCode.append(key)
            if self.enteredCode == code:
              self.enteredCode     = []
              self.player.cheating = True
              func()
            break
      else:
        self.enteredCode = []

    #myfingershurt: Adding starpower and killswitch for "no HOPOs" mode
    if control == Player.STAR:
      self.activateSP(0)
    elif self.numOfPlayers > 1 and control == Player.PLAYER_2_STAR: #QQstarS:Add the 2nd palyers active SP key
      self.activateSP(1) #QQstarS:ADD
    if control == Player.KILL and not self.isKillAnalog[0]:  #MFH - only use this logic if digital killswitch
      self.killswitchEngaged[0] = True
    elif self.numOfPlayers > 1 and control == Player.PLAYER_2_KILL and not self.isKillAnalog[1]: #QQstarS: new
      self.killswitchEngaged[1] = True


  def keyPressed2(self, key, unicode, control = None):
    hopo = False
    if not control:
      control = self.controls.keyPressed(key)
    else:
      hopo = True
      
    if True:
      pressed = -1
      if control in (self.guitars[0].actions):
        hopo = False
        pressed = 0;  
      elif self.numOfPlayers > 1 and control in (self.guitars[1].actions):
        hopo = False
        pressed = 1;

      numpressed = [len([1 for k in guitar.keys if self.controls.getState(k)]) for guitar in self.guitars]

      activeList = [k for k in self.keysList[pressed] if self.controls.getState(k)]
      if control in (self.guitars[0].keys) and self.song and numpressed[0] >= 1:
        if self.guitars[0].wasLastNoteHopod and self.guitars[0].hopoActive >= 0:
          hopo = True
          pressed = 0;
      elif self.numOfPlayers > 1 and control in (self.guitars[1].keys) and numpressed[1] >= 1:
        if self.guitars[1].wasLastNoteHopod and self.guitars[1].hopoActive >= 0:
          hopo = True
          pressed = 1;

      if pressed >= 0:
        for k in self.keysList[pressed]:
          if self.controls.getState(k):
            self.keyBurstTimeout[pressed] = None
            break
        else:
          self.keyBurstTimeout[pressed] = self.engine.timer.time + self.keyBurstPeriod
          return True

      if pressed >= 0 and self.song:
        self.doPick2(pressed, hopo)
      
    if control in Player.CANCELS:
      if self.ending == True:
        return True
      self.pauseGame()
      self.engine.view.pushLayer(self.menu)
      return True
    elif key >= ord('a') and key <= ord('z'):
      # cheat codes
      n = len(self.enteredCode)
      for code, func in self.cheatCodes:
        if n < len(code):
          if key == code[n]:
            self.enteredCode.append(key)
            if self.enteredCode == code:
              self.enteredCode     = []
              for player in self.playerList:
                player.cheating = True
              func()
            break
      else:
        self.enteredCode = []

    if control == Player.STAR:
      self.activateSP(0)
    elif self.numOfPlayers > 1 and control == Player.PLAYER_2_STAR: #QQstarS:Add the 2nd palyers active SP key
      self.activateSP(1) #QQstarS:ADD
    if control == Player.KILL and not self.isKillAnalog[0]:  #MFH - only use this logic if digital killswitch
      self.killswitchEngaged[0] = True
    elif self.numOfPlayers > 1 and control == Player.PLAYER_2_KILL and not self.isKillAnalog[1]: #QQstarS: new
      self.killswitchEngaged[1] = True

 
  def keyPressed3(self, key, unicode, control = None, pullOff = False):  #MFH - gonna pass whether this was called from a pull-off or not
    hopo = False
    if not control:
      control = self.controls.keyPressed(key)
    else:
      hopo = True
      
    #if True: #MFH: WTF?
    
    pressed = -1
    if control in (self.guitars[0].actions):
      hopo = False
      pressed = 0;  
    elif self.numOfPlayers > 1 and control in (self.guitars[1].actions):
      hopo = False
      pressed = 1;

    numpressed = [len([1 for k in guitar.keys if self.controls.getState(k)]) for guitar in self.guitars]


    activeList = [k for k in self.keysList[pressed] if self.controls.getState(k)]

    if self.ignoreOpenStrums and len(activeList) < 1:   #MFH - filter out strums without frets
      pressed = -1


    if control in (self.guitars[0].keys) and numpressed[0] >= 1:
      if self.guitars[0].hopoActive > 0 or (self.guitars[0].wasLastNoteHopod and self.guitars[0].hopoActive == 0):

        if not pullOff and (self.hopoStyle == 2 or self.hopoStyle == 3): #GH2 or GH2 Strict, don't allow lower-fret tapping while holding a higher fret

          activeKeyList = []
          LastHopoFretStillHeld = False
          HigherFretsHeld = False
          for k in self.keysList[0]:
            if self.controls.getState(k):
              activeKeyList.append(k)
              if self.guitars[0].keys[self.guitars[0].hopoLast] == k:
                LastHopoFretStillHeld = True
              elif k > self.guitars[0].keys[self.guitars[0].hopoLast]:
                HigherFretsHeld = True


          if not(LastHopoFretStillHeld and not HigherFretsHeld):  #tapping a lower note should do nothing.
            hopo = True
            pressed = 0;

        else:   #GH2 Sloppy or RF-Mod 
          hopo = True
          pressed = 0;
        
        
    elif self.numOfPlayers > 1 and control in (self.guitars[1].keys) and numpressed[1] >= 1:
      if self.guitars[1].hopoActive > 0  or (self.guitars[1].wasLastNoteHopod and self.guitars[1].hopoActive == 0):

        if not pullOff and (self.hopoStyle == 2 or self.hopoStyle == 3): #GH2 or GH2 Strict, don't allow lower-fret tapping while holding a higher fret

          activeKeyList = []
          LastHopoFretStillHeld = False
          HigherFretsHeld = False
          for k in self.keysList[1]:
            if self.controls.getState(k):
              activeKeyList.append(k)
              if self.guitars[1].keys[self.guitars[1].hopoLast] == k:
                LastHopoFretStillHeld = True
              elif k > self.guitars[1].keys[self.guitars[1].hopoLast]:
                HigherFretsHeld = True


          if not(LastHopoFretStillHeld and not HigherFretsHeld):  #tapping a lower note should do nothing.
            hopo = True
            pressed = 1;

        else:   #GH2 Sloppy or RF-Mod 
          hopo = True
          pressed = 1;


    
    #MFH - this is where the marked little block above used to be - possibly causing false "late pick" detections from HOPOs...

    if pressed >= 0:
      #myfingershurt:

      self.handlePick(pressed, hopo = hopo, pullOff = pullOff)

      #if self.hopoStyle ==  1:   #1 = rf-mod
      #  self.doPick3RF(pressed, hopo)
      #elif self.hopoStyle == 2 or self.hopoStyle == 3 or self.hopoStyle == 4:  #GH2 style HOPO 
      #  self.doPick3GH2(pressed, hopo, pullOff)
      #else:   #2 = no HOPOs
      #  self.doPick(pressed)
      
    if control in Player.CANCELS:
      if self.ending == True:
        return True
      self.pauseGame()
      self.engine.view.pushLayer(self.menu)
      return True
    elif key >= ord('a') and key <= ord('z'):
      # cheat codes
      n = len(self.enteredCode)
      for code, func in self.cheatCodes:
        if n < len(code):
          if key == code[n]:
            self.enteredCode.append(key)
            if self.enteredCode == code:
              self.enteredCode     = []
              for player in self.playerList:
                player.cheating = True
              func()
            break
      else:
        self.enteredCode = []

    if control == Player.STAR:
      self.activateSP(0)
    elif self.numOfPlayers > 1 and control == Player.PLAYER_2_STAR: #QQstarS:Add the 2nd palyers active SP key
      self.activateSP(1) #QQstarS:ADD
    if control == Player.KILL and not self.isKillAnalog[0]:  #MFH - only use this logic if digital killswitch
      self.killswitchEngaged[0] = True
    elif self.numOfPlayers > 1 and control == Player.PLAYER_2_KILL and not self.isKillAnalog[1]: #QQstarS: new
      self.killswitchEngaged[1] = True


  def CheckForValidKillswitchNote(self, num):
    if not self.song:
      return False
 
    noteCount  = len(self.guitars[num].playedNotes)
    if noteCount > 0:
      pickLength = self.guitars[num].getPickLength(self.getSongPosition())
      if pickLength > 0.5 * (self.song.period / 4):
        return True
      else:
        return False
    else:
      return False

  def getExtraScoreForCurrentlyPlayedNotes(self, num):
    if not self.song or self.guitars[num].isDrum:
      return 0
    if self.coOpType:
      scoreCard = self.coOpScoreCard
    else:
      scoreCard = self.scoring[num]
    noteCount  = len(self.guitars[num].playedNotes)
    pickLength = self.guitars[num].getPickLength(self.getSongPosition())
    if pickLength > 1.1 * self.song.period / 4:
      tempExtraScore = self.baseSustainScore * pickLength * noteCount
      if self.starScoreUpdates == 1:
        scoreCard.updateAvMult()
        star = scoreCard.stars
        a = scoreCard.getStarScores(tempExtraScore = tempExtraScore)
        if a > star and self.engine.data.starDingSoundFound and ((self.inGameStars == 1 and self.theme == 2) or self.inGameStars == 2):
          self.engine.data.starDingSound.play()
      return int(tempExtraScore)   #original FoF sustain scoring
    return 0

  def keyReleased(self, key):
    #RF style HOPO playing
  
    control = self.controls.keyReleased(key)
    num = self.getPlayerNum(control) 

    #myfingershurt: drums :)
    #MFH - cleaning up Faaa's drum tracking code: (which appears to determine which drum fret after key release?  TODO: why not before?)
    if self.guitars[num].isDrum:
      if control in (self.guitars[num].keys):
        if not self.controls.getState(self.guitars[num].keys[0]):
          self.guitars[num].bassDrumPedalDown = False    #MFH - this is all that's needed here...
          #self.guitars[num].lastFretWasBassDrum = False
      return True
    
#-      if not self.controls.getState(self.guitars[num].keys[1]):
#-        self.guitars[num].lastFretWasT1 = False
#-      return True
#-      if not self.controls.getState(self.guitars[num].keys[2]):
#-        self.guitars[num].lastFretWasT2 = False
#-      return True  
#-      if not self.controls.getState(self.guitars[num].keys[3]):
#-        self.guitars[num].lastFretWasT3 = False
#-      return True
#-      if not self.controls.getState(self.guitars[num].keys[4]):
#-        self.guitars[num].lastFretWasC = False
#-      return True   


    #myfingershurt:
  
    if self.hopoStyle > 0:  #hopos enabled
      res = self.keyReleased3(key)
      return res


    if control in self.keysList[num] and self.song:
      # Check whether we can tap the currently required notes
      pos   = self.getSongPosition()
      notes = self.guitars[num].getRequiredNotes(self.song, pos)

      if self.scoring[num].streak > 0 and \
         self.guitars[num].areNotesTappable(notes) and \
         self.guitars[num].controlsMatchNotes(self.controls, notes):
        self.doPick(num)
      # Otherwise we end the pick if the notes have been playing long enough
      elif self.lastPickPos[num] is not None and pos - self.lastPickPos[num] > self.song.period / 2:
        self.endPick(num)

    #Digital killswitch disengage:
    if control == Player.KILL and not self.isKillAnalog[0]:  #MFH - only use this logic if digital killswitch
      self.killswitchEngaged[0] = False
    elif self.numOfPlayers > 1 and control == Player.PLAYER_2_KILL and not self.isKillAnalog[1]: #QQstarS: new
      self.killswitchEngaged[1] = False


  def keyReleased2(self, key):
    control = self.controls.keyReleased(key)
    for i, keys in enumerate(self.keysList):
      if control in keys and self.song:
        for time, note in self.guitars[i].playedNotes:
          if not self.guitars[i].wasLastNoteHopod or (self.guitars[i].hopoActive < 0 and control == self.keysList[i][note.number]):
            self.endPick(i)

    #Digital killswitch disengage:
    if control == Player.KILL and not self.isKillAnalog[0]:  #MFH - only use this logic if digital killswitch
      self.killswitchEngaged[0] = False
    elif self.numOfPlayers > 1 and control == Player.PLAYER_2_KILL and not self.isKillAnalog[1]: #QQstarS: new
      self.killswitchEngaged[1] = False

    
    for i, guitar in enumerate(self.guitars):
      activeList = [k for k in self.keysList[i] if self.controls.getState(k) and k != control]
      if len(activeList) != 0 and guitar.wasLastNoteHopod and activeList[0] != self.keysList[i][guitar.hopoLast] and control in self.keysList[i]:
        self.keyPressed2(None, 0, activeList[0])

  def keyReleased3(self, key):
    control = self.controls.keyReleased(key)
    #myfingershurt: this is where the lower-fret-release causes a held note to break:
    for i, keys in enumerate(self.keysList):
      if control in keys and self.song:   #myfingershurt: if the released control was a fret:
        for time, note in self.guitars[i].playedNotes:
          #if self.guitars[i].hopoActive == 0 or (self.guitars[i].hopoActive < 0 and control == self.keysList[i][note.number]):
          #if not self.guitars[i].wasLastNoteHopod or (self.guitars[i].hopoActive < 0 and control == self.keysList[i][note.number]):
            #myfingershurt: only end the pick if no notes are being held.
          if (self.guitars[i].hit[note.number] == True and control == self.keysList[i][note.number]):
          #if control == self.keysList[i][note.number]:
            #if self.hopoDebugDisp == 1:
            #  Log.debug("MFH: An early sustain release was just detected.")
            self.endPick(i)

    #Digital killswitch disengage:
    if control == Player.KILL and not self.isKillAnalog[0]:  #MFH - only use this logic if digital killswitch
      self.killswitchEngaged[0] = False
    elif self.numOfPlayers > 1 and control == Player.PLAYER_2_KILL and not self.isKillAnalog[1]: #QQstarS: new
      self.killswitchEngaged[1] = False
    
    for i, guitar in enumerate(self.guitars):
      activeList = [k for k in self.keysList[i] if self.controls.getState(k) and k != control]
      #myfingershurt: removing check for hopolast for GH2 system after-chord HOPOs
      #myfingershurt: also added self.hopoAfterChord conditional to ensure this logic doesn't apply without HOPOs after chord
      if self.hopoAfterChord and (self.hopoStyle == 2 or self.hopoStyle == 3 or self.hopoStyle == 4):   #for GH2 systems: so user can release lower fret from chord to "tap" held HOPO
        #if len(activeList) != 0 and guitar.wasLastNoteHopod and control in self.keysList[i]:
        if len(activeList) != 0 and guitar.hopoActive > 0 and control in self.keysList[i]:
          self.keyPressed3(None, 0, activeList[0], pullOff = True)
      
      else:
        #if len(activeList) != 0 and guitar.wasLastNoteHopod and activeList[0] != self.keysList[i][guitar.hopoLast] and control in self.keysList[i]:
        if len(activeList) != 0 and guitar.hopoActive > 0 and activeList[0] != self.keysList[i][guitar.hopoLast] and control in self.keysList[i]:
          self.keyPressed3(None, 0, activeList[0], pullOff = True)
        
  def getPlayerNum(self, control):
    if control in (self.guitars[0].keys + self.guitars[0].actions):
      return(0) 
    elif self.numOfPlayers > 1 and control in (self.guitars[1].keys + self.guitars[1].actions):
      return(1)
    else:
      return(-1)



  #MFH -- OK - new way to handle star and partial star scoring in-game without needing to calculate the average multiplier in realtime:
  #   Gonna precalculate all thresholds for star scoring as score thresholds for simple integer comparisons.
  #   Furthermore, this will naturally reduce some of the nesting as the scoring type and instrument won't have to be checked in-game -
  #     this information will be included in the precalculated score thresholds.
  #   Also, instead of nesting the partial star scoring in one level, and checking each possible level from the top down each cycle,
  #     reverse logic to check star score thresholds sequentially from the bottom up, stop when a threshold is reached, and remember the position.
  #     then, next time, start checking from the last threshold instead of the bottom (since score won't be decreasing...)
  #     for RB scoring: 6 star thresholds above 0, with 8 steps for stars 1,2,3,4, and 5 -- 41 thresholds to calculate
  #     for GH scoring: 6 star thresholds above 0, with 8 steps for stars 2,3,4, and 5 -- 34 thresholds to calculate
  #     for FoF scoring: hmm, this still uses hit percentage alone and not average multiplier
  #       For FoF (and 5* GH) scoring, also need to precalculate the important accuracy thresholds in terms of number of notes hit (since that is also an integer quantity we have on hand)
  #     To handle all of the above cases, perhaps a list of tuples that can be retrieved that can indicate:
  #       (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>)
  #       if either threshold is set to 0 in the tuple, then it essentially does not matter.  
  #       The proposed unified star scoring system will step the user through the list of tuples as the progressively-ordered requirements are met
  #       Also must jump ahead and check if the last condition tuple in the list is met (which will always contain the 6* condition and, in GH scoring, might not be met sequentially)
        
  def render(self, visibility, topMost):  #QQstarS: Fix this function for mostly. And there are lots of change in this, I just show the main ones

    #MFH render function reorganization notes:
    #Want to render all background / single-viewport graphics first

    #if self.song:

    #myfingershurt: Alarian's auto-stage scaling update
    w = self.wFull
    h = self.hFull
    wBak = w
    hBak = h

    if self.fontShadowing:
      font    = self.engine.data.shadowfont
    else:
      font    = self.engine.data.font
    lyricFont = self.engine.data.font
    bigFont = self.engine.data.bigFont
    sphraseFont = self.engine.data.streakFont2

    scoreFont = self.engine.data.scoreFont
    streakFont = self.engine.data.streakFont


    if self.song and self.song.readyToGo:
      pos = self.getSongPosition()
  
      if self.boardY <= 1:
        self.boardY == 1
        self.setCamera()
      elif self.boardY > 1:
        self.boardY -= 0.01
        self.setCamera()
      #self.setCamera()
  
      #Theme.setBaseColor()

      SceneClient.render(self, visibility, topMost) #MFH - I believe this eventually calls the renderGuitar function, which also involves two viewports... may not be easy to move this one...
        
      self.visibility = v = 1.0 - ((1 - visibility) ** 2)
  
      self.engine.view.setOrthogonalProjection(normalize = True)

      #MFH: render the note sheet just on top of the background:
      if self.lyricSheet != None:
        self.engine.drawImage(self.lyricSheet, scale = (self.lyricSheetScaleFactor,-self.lyricSheetScaleFactor), coord = (w/2, h*0.935))
        #the timing line on this lyric sheet image is approx. 1/4 over from the left
  
      #MFH - also render the scrolling lyrics & sections before changing viewports:
      minPos = pos - ((self.guitars[0].currentPeriod * self.guitars[0].beatsPerBoard) / 2)
      maxPos = pos + ((self.guitars[0].currentPeriod * self.guitars[0].beatsPerBoard) * 1.5)
      eventWindow = (maxPos - minPos)
      #lyricSlop = ( self.guitars[0].currentPeriod / (maxPos - minPos) ) / 4
      lyricSlop = ( self.guitars[0].currentPeriod / ((maxPos - minPos)/2) ) / 2

      if (self.readTextAndLyricEvents == 2 or (self.readTextAndLyricEvents == 1 and self.theme == 2)) and (not self.pause and not self.failed and not self.ending):
  
        if self.countdown <= 0: #MFH - only attempt to handle sections / lyrics / text events if the countdown is complete!

          #handle the sections track
          if self.midiSectionsEnabled > 0: 
            for time, event in self.song.eventTracks[Song.TK_SECTIONS].getEvents(minPos, maxPos):
              if self.theme == 2:
                #xOffset = 0.5
                yOffset = 0.715
                txtSize = 0.00170
              else:
                #gh3 or other standard mod
                #xOffset = 0.5
                yOffset = 0.69
                txtSize = 0.00175
              #is event happening now?
              #this version will turn events green right as they hit the line and then grey shortly afterwards
              #instead of an equal margin on both sides.
              xOffset = (time - pos) / eventWindow
              EventHappeningNow = False
              if xOffset < (0.0 - lyricSlop * 2.0):   #past
                glColor3f(0.5, 0.5, 0.5)    #I'm hoping this is some sort of grey.
              elif xOffset < lyricSlop / 16.0:   #present
                EventHappeningNow = True
                glColor3f(0, 1, 0.6)    #green-blue
              else:   #future, and all other text
                glColor3f(1, 1, 1)    #cracker white
              xOffset += 0.250
    
              text = event.text
              yOffset = 0.00005     #last change -.00035
              txtSize = 0.00150
              lyricFont.render(text, (xOffset, yOffset),(1, 0, 0),txtSize)
    
  
          #handle the lyrics track
          if self.midiLyricsEnabled > 0:
            if self.midiLyricMode == 0:   #scrolling lyrics mode:
              for time, event in self.song.eventTracks[Song.TK_LYRICS].getEvents(minPos, maxPos):
                if self.theme == 2:
                  #xOffset = 0.5
                  yOffset = 0.715
                  txtSize = 0.00170
                else:
                  #gh3 or other standard mod
                  #xOffset = 0.5
                  yOffset = 0.69
                  txtSize = 0.00175
                #is event happening now?
                #this version will turn events green right as they hit the line and then grey shortly afterwards
                #instead of an equal margin on both sides.
                xOffset = (time - pos) / eventWindow
                EventHappeningNow = False
                if xOffset < (0.0 - lyricSlop * 2.0):   #past
                  glColor3f(0.5, 0.5, 0.5)    #I'm hoping this is some sort of grey.
                elif xOffset < lyricSlop / 16.0:   #present
                  EventHappeningNow = True
                  glColor3f(0, 1, 0.6)    #green-blue
                else:   #future, and all other text
                  glColor3f(1, 1, 1)    #cracker white
                xOffset += 0.250
      
                yOffset = 0.0696    #last change +0.0000
                txtSize = 0.00160
                text = event.text
                if text.find("+") >= 0:   #shift the pitch adjustment markers down one line
                  text = text.replace("+","~")
                  txtSize = 0.00145   #last change +.0000
                  yOffset -= 0.0115   #last change -.0005
                lyricFont.render(text, (xOffset, yOffset),(1, 0, 0),txtSize)
  
            #MFH - TODO - handle line-by-line lyric display and coloring here:
            elif self.midiLyricMode == 1:   #line-by-line lyrics mode:
  
              if self.theme == 2:
                txtSize = 0.00170
              else:
                #gh3 or other standard mod
                txtSize = 0.00175
              yOffset = 0.0696  
              xOffset = 0.5 - (lyricFont.getStringSize(self.currentSimpleMidiLyricLine, scale = txtSize)[0] / 2.0)
              glColor3f(1, 1, 1)
              lyricFont.render(self.currentSimpleMidiLyricLine, (xOffset, yOffset),(1, 0, 0),txtSize)                
                
            elif self.midiLyricMode == 2 and (self.numMidiLyricLines > self.activeMidiLyricLineIndex):   #line-by-line lyrics mode:
  
              if self.theme == 2:
                txtSize = 0.00170
              else:
                #gh3 or other standard mod
                txtSize = 0.00175
              yOffset = 0.0696  
              #xOffset = 0.5 - (lyricFont.getStringSize(self.currentSimpleMidiLyricLine, scale = txtSize)[0] / 2.0)
  
              tempTime, tempLyricLine = self.midiLyricLines[self.activeMidiLyricLineIndex]
  
              xOffset = 0.5 - (lyricFont.getStringSize(tempLyricLine, scale = txtSize)[0] / 2.0)
              glColor3f(0.75, 0.75, 0.75)
              lyricFont.render(self.activeMidiLyricLine_GreyWords, (xOffset, yOffset),(1, 0, 0),txtSize)
              
              xOffset += lyricFont.getStringSize(self.activeMidiLyricLine_GreyWords, scale = txtSize)[0]
              glColor3f(0, 1, 0)
              lyricFont.render(self.activeMidiLyricLine_GreenWords, (xOffset, yOffset),(1, 0, 0),txtSize)
              
              xOffset += lyricFont.getStringSize(self.activeMidiLyricLine_GreenWords, scale = txtSize)[0]
              glColor3f(1, 1, 1)
              lyricFont.render(self.activeMidiLyricLine_WhiteWords, (xOffset, yOffset),(1, 0, 0),txtSize)
                        
              yOffset += self.lyricHeight
              xOffset = 0.25
              glColor3f(1, 1, 1)
              lyricFont.render(self.currentSimpleMidiLyricLine, (xOffset, yOffset),(1, 0, 0),txtSize)                
  
  
  
  
  
          #finally, handle the unused text events track
          if self.showUnusedTextEvents:
            for time, event in self.song.eventTracks[Song.TK_UNUSED_TEXT].getEvents(minPos, maxPos):
              if self.theme == 2:
                #xOffset = 0.5
                yOffset = 0.715
                txtSize = 0.00170
              else:
                #gh3 or other standard mod
                #xOffset = 0.5
                yOffset = 0.69
                txtSize = 0.00175
              #is event happening now?
              #this version will turn events green right as they hit the line and then grey shortly afterwards
              #instead of an equal margin on both sides.
              xOffset = (time - pos) / eventWindow
              EventHappeningNow = False
              if xOffset < (0.0 - lyricSlop * 2.0):   #past
                glColor3f(0.5, 0.5, 0.5)    #I'm hoping this is some sort of grey.
              elif xOffset < lyricSlop / 16.0:   #present
                EventHappeningNow = True
                glColor3f(0, 1, 0.6)    #green-blue
              else:   #future, and all other text
                glColor3f(1, 1, 1)    #cracker white
              xOffset += 0.250
          
              yOffset = 0.0190      #last change -.0020
              txtSize = 0.00124
              lyricFont.render(event.text, (xOffset, yOffset),(1, 0, 0),txtSize)
  
      try:
        now = self.getSongPosition()
        countdownPos = self.lastEvent - now

        

        for i,player in enumerate(self.playerList): #QQstarS: This part has big fix. I add the code into it,So he can shown corect
          self.engine.view.setViewportHalf(self.numOfPlayers,i)  
          



          streakFlag = 0  #set the flag to 0
          #if not self.coOpGH or self.rmtype == 2:
            #self.engine.view.setViewportHalf(self.numOfPlayers,i)
          if self.coOpGH and self.rmtype != 2:
            self.engine.view.setViewport(1,0)
          Theme.setBaseColor()
          if self.coOpGH:
            multStreak = self.coOpScoreCard.streak
          else:
            multStreak = self.scoring[i].streak
          if self.guitars[i].isBassGuitar and self.bassGrooveEnabled:
            maxMult = 60
          else:
            maxMult = 40
          
          # show the streak counter and miss message
          #============Blazingamer's GHII Rock Meter=============#
  
          if self.rmtype == 0:   #GH2 theme
           if not self.pauseScreen == None:
              w = self.wPlayer[i]
              h = self.hPlayer[i]
              wBak = w
              hBak = h
              if self.guitars[i].starPowerActive: #QQstarS:Set [0] to [i]
                #death_au: check for bass groove
                #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnableMode == 2:
                if self.guitars[i].isBassGuitar and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnabled:
                  if multStreak >= 50:
                    multiplier = 6
                    multRange = (0.75,1.00)  #MFH division->constant: [(3.0/4.0,4.0/4.0)]->[(0.75,1.00)]
                    color = (.3,.7,.9,1)
                  else:
                    multiplier = 5
                    multRange = (0.5,0.75) #MFH division->constant: [(2.0/4.0,3.0/4.0)]->[(0.5,0.75)]
                    color = (.3,.7,.9,1)
                #death_au: end check for bass groove
                elif multStreak >= 30:
                  multiplier = 4
                  multRange = (0.875,1.0) #MFH division->constant: was [(7.0/8.0,8.0/8.0)]
                  color = (.3,.7,.9,1)
                elif multStreak >= 20:
                  multiplier = 3
                  multRange = (0.75,0.875) #MFH division->constant: was [(6.0/8.0,7.0/8.0)]
                  color = (.3,.7,.9,1)
                elif multStreak >= 10:
                  multiplier = 2
                  multRange = (0.625,0.75) #MFH division->constant: was [(5.0/8.0,6.0/8.0)]
                  color = (.3,.7,.9,1)
                else:
                  multiplier = 1
                  multRange = (0.5,0.625) #MFH division->constant: was [(4.0/8.0,5.0/8.0)]
                  color = (.3,.7,.9,1)
              else:
                #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnableMode == 2:
                if self.guitars[i].isBassGuitar and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnabled:
                  if multStreak >= 50:
                    multiplier = 6
                    multRange = (0.25,0.5) #MFH division->constant: was [(1.0/4.0,2.0/4.0)]
                    color = (.3,.7,.9,1)
                  else:
                    multiplier = 5
                    multRange = (0.0,0.25) #MFH division->constant: was [(0.0/4.0,1.0/4.0)]
                    color = (.3,.7,.9,1)
                elif multStreak >= 30:
                  multiplier = 4
                  multRange = (0.375,0.5) #MFH division->constant: was [(3.0/8.0,4.0/8.0)]
                  color = (1,-1,1,1)
                elif multStreak >= 20:
                  multiplier = 3
                  multRange = (0.25,0.375) #MFH division->constant: was [(2.0/8.0,3.0/8.0)]
                  color = (-1,1,-.75,1)
                elif multStreak >= 10:
                  multiplier = 2
                  multRange = (0.125,0.25) #MFH division->constant: was (1.0/8.0,2.0/8.0)
                  color = (1,1,-1,1)
                else:
                  multiplier = 1
                  multRange = (0.0,0.125) #MFH division->constant: was (0.0/8.0,1.0/8.0)
                  color = (1,1,-1,1)
                        
              #myfingershurt: GH bass groove multiplier:            
              #if self.playerList[i].part.text == "Bass Guitar" and multStreak >= 40 and self.bassGrooveEnableMode == 2:   #bass groove!
              if self.guitars[i].isBassGuitar and multStreak >= 40 and self.bassGrooveEnabled:   #bass groove!
                if self.bassgroovemult != None: #death_au : bassgroovemult image found, draw image
                  self.engine.drawImage(self.bassgroovemult, scale = (.5,-.125), coord = (w*0.134,h*0.19 + self.hOffset[i]), rect = (0,1,multRange[0],multRange[1]))
                else: #death_au: bassgroovemult not found
                  #myfingershurt: Temp text bass groove multiplier:
                  glColor3f(0,0.75,1)
                  text = str(self.scoring[i].getScoreMultiplier() * self.multi[i])
                  wid, hig = font.getStringSize(text,0.00325)
                  font.render(text, (.133 - wid / 2, .566),(1, 0, 0),0.00325)     #replacing GH multiplier large text
  
  
              else:
                self.engine.drawImage(self.mult, scale = (.5,-.0625), coord = (w*0.134,h*0.19 + self.hOffset[i]), rect = (0,1,multRange[0],multRange[1]))
  
              self.engine.drawImage(self.rockmeter, scale = (.5, -.5), coord = (w*.134, h*.22 + self.hOffset[i]))
              
              #===============blazingamer GH2 scoremeter
              
              
              #if (self.coOp and i == 0) or not self.coOp:  #MFH only render for player 0 if co-op mode
              if (self.coOpType and i == self.coOpPlayerMeter) or not self.coOpType or (self.coOpRB and i==0):  #MFH only render for player 1 if co-op mode. only go through once for coOpRB

                if self.coOpType:
                  score=self.coOpScoreCard.score
                  for playaNum, playa in enumerate(self.playerList):
                    score += self.getExtraScoreForCurrentlyPlayedNotes(playaNum)
                else:
                  score=self.scoring[i].score
                  score += self.getExtraScoreForCurrentlyPlayedNotes(i)

                scoretext = locale.format("%d", score, grouping=True)
                scoretext = scoretext.replace(",","   ")
                scW, scH = scoreFont.getStringSize(scoretext)
    
                score6 = score/1000000
                score5 = (score-score6*1000000)/100000
                score4 = (score-score6*1000000-score5*100000)/10000
                score3 = (score-score6*1000000-score5*100000 - score4*10000)/1000
                score2 = (score-score6*1000000-score5*100000 - score4*10000-score3*1000)/100
                score1 = (score-score6*1000000-score5*100000 - score4*10000-score3*1000-score2*100)/10
                score0 = (score-score6*1000000-score5*100000 - score4*10000-score3*1000-score2*100-score1*10)
               
                glColor4f(0,0,0,1)
                text = str(score0)
                size = scoreFont.getStringSize(text)
                scoreFont.render(text, (.189, 0.519))
                if score >= 10:
                  text = str(score1)
                  size = streakFont.getStringSize(text)
                  scoreFont.render(text, (.168, 0.522))
                if score >= 100:
                  text = str(score2)
                  size = streakFont.getStringSize(text)
                  scoreFont.render(text, (.148, 0.524))
                if score >= 1000:
                  text = str(score3)
                  size = streakFont.getStringSize(text)
                  scoreFont.render(text, (.118, 0.527))
                if score >= 10000:
                  text = str(score4)
                  size = streakFont.getStringSize(text)
                  scoreFont.render(text, (.095, 0.530))
                if score >= 100000:
                  text = str(score5)
                  size = streakFont.getStringSize(text)
                  scoreFont.render(text, (.074, 0.532))
              #============end blazingamer gh2 scoremeter
  
              #MFH - rock measurement tristate
              #if self.rock[i] > self.rockMax/3.0*2:
              if self.rock[i] > self.rockHiThreshold:
                rock = self.rockHi
              #elif self.rock[i] > self.rockMax/3.0:
              elif self.rock[i] > self.rockMedThreshold:
                rock = self.rockMed
              else:
                rock = self.rockLo
    
              if self.failingEnabled:
                self.engine.drawImage(rock, scale = (.5,-.5), coord = (w*.86,h*.2 + self.hOffset[i]))
              else:
                self.engine.drawImage(self.rockOff, scale = (.5,-.5), coord = (w*.86,h*.2 + self.hOffset[i]))
    
              currentRock = (0.0 + self.rock[i]) / (self.rockMax)
              if self.rock[i] >= 0:
                self.arrowRotation[i] += ( 0.0 + currentRock - self.arrowRotation[i]) / 5.0
              else:  #QQstarS: Fix the arrow let him never rotation to bottom
                self.arrowRotation[i] = self.arrowRotation[i]
              angle = -(.460 / 2) * math.pi + .460 * math.pi * self.arrowRotation[i]
              wfactor = self.arrow.widthf(pixelw = 60.000)
            
              if self.failingEnabled:
                self.engine.drawImage(self.arrow, scale = (wfactor,-wfactor), coord = (w*.86,h*.136 + self.hOffset[i]), rot = -angle)

              self.engine.drawImage(self.rockTop, scale = (.5,-.5), coord = (w*.86,h*.2 + self.hOffset[i]))
    
              self.engine.drawImage(self.counter, scale = (.5,-.5), coord = (w*.15,h*(self.counterY) + self.hOffset[i]))
  
              if multStreak == 0:
                r = self.basedots
              elif multStreak - ((multiplier-1)*10) == 1:
                r = self.dt1
              elif multStreak - ((multiplier-1)*10) == 2:
                r = self.dt2
              elif multStreak - ((multiplier-1)*10) == 3:
                r = self.dt3
              elif multStreak - ((multiplier-1)*10) == 4:
                r = self.dt4
              elif multStreak - ((multiplier-1)*10) == 5:
                r = self.dt5
              elif multStreak - ((multiplier-1)*10) == 6:
                r = self.dt6
              elif multStreak - ((multiplier-1)*10) == 7:
                r = self.dt7
              elif multStreak - ((multiplier-1)*10) == 8:
                r = self.dt8
              elif multStreak - ((multiplier-1)*10) == 9:
                r = self.dt9
              else:
                r = self.dt10
             
              self.engine.drawImage(r, scale = (.65,-.65), coord = (w*0.137, h*0.23+self.hOffset[i]), color = color)
   
              currentSP = self.guitars[i].starPower/100.0
              widthChange = w*0.11

              self.engine.drawImage(self.oBottom, scale = (.6,.6), coord = (w*.86,h*.34 + self.hOffset[i]))
              self.engine.drawImage(self.oFill, scale = (.6*currentSP,.6), coord = (w*.86-widthChange+widthChange*currentSP,h*.34 + self.hOffset[i]), rect = (0,currentSP,0,1))
              self.engine.drawImage(self.oTop, scale = (.6,.6), coord = (w*.86,h*.34 + self.hOffset[i]))
    
              if multStreak >= 25 and not self.counterY >= 0.1125:
                self.counterY += 0.01
              elif multStreak < 25 and not self.counterY <= -0.1:
                self.counterY -= 0.01
              if self.counterY > 0.1125 or ( self.numOfPlayers==2 ):
                self.counterY = 0.1125
              
              if self.coOpRB:
                multstreak = self.coOpScoreCard.streak
    
              if self.counterY == 0.1125 or ( self.numOfPlayers==2 and multStreak >0 ):
                glColor4f(0,0,0,1)
                streak3 = multStreak/1000
                streak2 = (multStreak-streak3*1000)/100
                streak1 = (multStreak-streak3*1000-streak2*100)/10
                streak0 = (multStreak-streak3*1000-streak2*100-streak1*10)
                text = str(streak0)
                size = streakFont.getStringSize(text)
                streakFont.render(text, (.193-size[0]/2, 0.667-size[1]/2+self.hFontOffset[i]))
                glColor4f(1,1,1,1)
                text = str(streak1)
                size = streakFont.getStringSize(text)
                streakFont.render(text, (.161-size[0]/2, 0.667-size[1]/2+self.hFontOffset[i]))
                text = str(streak2)
                size = streakFont.getStringSize(text)
                streakFont.render(text, (.132-size[0]/2, 0.667-size[1]/2+self.hFontOffset[i]))
    
  
              if self.displayText[i] != None:
                glColor3f(.8,.75,.01)
                size = sphraseFont.getStringSize(self.displayText[i], scale = self.displayTextScale[i])
                sphraseFont.render(self.displayText[i], (.5-size[0]/2,self.textY[i]-size[1]), scale = self.displayTextScale[i])
    
              if self.youRock == True:
                if self.rockTimer == 1:
                  #self.sfxChannel.setVolume(self.sfxVolume)
                  self.engine.data.rockSound.play()
                if self.rockTimer < self.rockCountdown:
                  self.rockTimer += 1
                  self.engine.drawImage(self.rockMsg, scale = (0.5, -0.5), coord = (w/2,h/2))
                if self.rockTimer >= self.rockCountdown:
                  self.rockFinished = True
    
              if self.failed:
                if self.failTimer == 0:
                  self.song.pause()
                if self.failTimer == 1:
                  #self.sfxChannel.setVolume(self.sfxVolume)
                  self.engine.data.failSound.play()
                if self.failTimer < 100:
                  self.failTimer += 1
                  self.engine.drawImage(self.failMsg, scale = (0.5, -0.5), coord = (w/2,h/2))
                else:
                  self.finalFailed = True
                
            
              if self.pause:
                self.engine.view.setViewport(1,0)
                self.engine.drawImage(self.pauseScreen, scale = (self.pause_bkg[2], -self.pause_bkg[3]), coord = (w*self.pause_bkg[0],h*self.pause_bkg[1]), stretched = 3)
                
              if self.finalFailed and self.song:
                self.engine.view.setViewport(1,0)
                self.engine.drawImage(self.failScreen, scale = (self.fail_bkg[2], -self.fail_bkg[3]), coord = (w*self.fail_bkg[0],h*self.fail_bkg[1]), stretched = 3)
    

                text = Dialogs.removeSongOrderPrefixFromName(self.song.info.name)
                size = font.getStringSize(text)
                font.render(text, (.5-size[0]/2.0,.35-size[1]))
                #now = self.getSongPosition()
                pctComplete = min(100, int(now/self.lastEvent*100))
                #text = str(pctComplete) + _("% Complete")
                text = "%s%s" % ( str(pctComplete), self.tsPercentComplete )
                size = font.getStringSize(text)
                font.render(text, (.5-size[0]/2.0, .35))
                if not self.failEnd:
                  self.failGame()
  

              if self.hopoIndicatorEnabled and not self.guitars[i].isDrum and not self.pause and not self.failed: #MFH - HOPO indicator (grey = strums required, white = strums not required)
                text = self.tsHopoIndicator
                if self.guitars[i].hopoActive > 0:
                  c1,c2,c3 = self.hopoIndicatorActiveColor
                  glColor3f(c1,c2,c3)  #white
                else:
                  c1,c2,c3 = self.hopoIndicatorInactiveColor
                  glColor3f(c1,c2,c3)  #grey
                w, h = font.getStringSize(text,0.00150)
                font.render(text, (self.hopoIndicatorX - w / 2, self.hopoIndicatorY),(1, 0, 0),0.00150)     #off to the right slightly above fretboard
                glColor3f(1, 1, 1)  #cracker white
  
    
          #===================================================#
  
          elif self.rmtype == 1:
            if not self.pauseScreen == None:
              w = self.wPlayer[i]
              h = self.hPlayer[i]
              wBak = w
              hBak = h
              if self.guitars[i].starPowerActive and not self.coOpRB: #QQstarS:Set [0] to [i]
                
                #myfingershurt: so that any GH theme can use dotshalf.png:
                if self.theme < 2:
                  if self.halfDots:
                    #death_au: check for bass groove
                    #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnableMode == 2:
                    if self.guitars[i].isBassGuitar and self.bassgroovemult != None and multStreak >= 40 and not self.coOpGH and self.bassGrooveEnabled:
                      if multStreak >= 50:
                        multiplier = 6
                        multRange = (0.75,1.00) #MFH division->constant: was (3.0/4.0,4.0/4.0)
                        color = (1,0,0.75,1)
                      else:
                        multiplier = 5
                        multRange = (0.5,0.75) #MFH division->constant: was (2.0/4.0,3.0/4.0)
                        color = (1,0,0.75,1)
                      xs = (0.75,1)
                    #death_au: end check for bass groove
                    elif multStreak >= 30:
                      multiplier = 4
                      multRange = (0.875,1.0) #MFH division->constant: was (7.0/8.0,8.0/8.0)
                      color = (.3,.7,.9,1)
                      xs = (0.75,1)
                    elif multStreak >= 20:
                      multiplier = 3
                      multRange = (0.75,0.875) #MFH division->constant: was (6.0/8.0,7.0/8.0)
                      color = (.3,.7,.9,1)
                      xs = (0.75,1)
                    elif multStreak >= 10:
                      multiplier = 2
                      multRange = (0.625,0.75) #MFH division->constant: was (5.0/8.0,6.0/8.0)
                      color = (.3,.7,.9,1)
                      xs = (0.75,1)
                    else:
                      multiplier = 1
                      multRange = (0.5,0.625) #MFH division->constant: was (4.0/8.0,5.0/8.0)
                      color = (.3,.7,.9,1)
                      xs = (0.75,1)
                  else:
                    #death_au: check for bass groove
                    #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnableMode == 2:
                    if self.guitars[i].isBassGuitar and self.bassgroovemult != None and multStreak >= 40 and not self.coOpGH and self.bassGrooveEnabled:
                      if multStreak >= 50:
                        multiplier = 6
                        multRange = (0.75,1.0) #MFH division->constant: was (3.0/4.0,4.0/4.0)
                        color = (1,0,0.75,1)
                      else:
                        multiplier = 5
                        multRange = (0.5,0.75) #MFH division->constant: was (2.0/4.0,3.0/4.0)
                        color = (1,0,0.75,1)
                    #death_au: end check for bass groove
                    elif multStreak >= 30:
                      multiplier = 4
                      multRange = (0.875,1.0) #MFH division->constant: was (7.0/8.0,8.0/8.0)
                      color = (.3,.7,.9,1)
                    elif multStreak >= 20:
                      multiplier = 3
                      multRange = (0.75,0.875) #MFH division->constant: was (6.0/8.0,7.0/8.0)
                      color = (.3,.7,.9,1)
                    elif multStreak >= 10:
                      multiplier = 2
                      multRange = (0.625,0.75) #MFH division->constant: was (5.0/8.0,6.0/8.0)
                      color = (.3,.7,.9,1)
                    else:
                      multiplier = 1
                      multRange = (0.5,0.625) #MFH division->constant: was (4.0/8.0,5.0/8.0)
                      color = (.3,.7,.9,1)
              else:
                #myfingershurt: so that any GH theme can use dotshalf.png:
                if self.theme < 2:
                  if self.halfDots:
                    #death_au: check for bass groove
                    #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnableMode == 2:
                    if self.guitars[i].isBassGuitar and self.bassgroovemult != None and multStreak >= 40 and not self.coOpGH and self.bassGrooveEnabled:
                      if multStreak >= 50:
                        multiplier = 6
                        multRange = (0.25,0.5) #MFH division->constant: was (1.0/4.0,2.0/4.0)
                        color = (1,0,0.75,1)
                      else:
                        multiplier = 5
                        multRange = (0.0,0.25) #MFH division->constant: was (0.0/4.0,1.0/4.0)
                        color = (1,0,0.75,1)
                      xs = (0.75,1)
                    #death_au: end check for bass groove
                    elif multStreak >= 30:
                      multiplier = 4
                      multRange = (0.375,0.5) #MFH division->constant: was (3.0/8.0,4.0/8.0)
                      color = (1,-1,1,1)
                      xs = (0.5,0.75)
                    elif multStreak >= 20:
                      multiplier = 3
                      multRange = (0.25,0.375) #MFH division->constant: was (2.0/8.0,3.0/8.0)
                      color = (-1,1,-.75,1)
                      xs = (0.25,0.5)
                    elif multStreak >= 10:
                      multiplier = 2
                      multRange = (0.125,0.25) #MFH division->constant: was (1.0/8.0,2.0/8.0)
                      color = (1,1,-1,1)
                      xs = (0,0.25)
                    else:
                      multiplier = 1
                      multRange = (0.0,0.125) #MFH division->constant: was (0.0/8.0,1.0/8.0)
                      color = (1,1,-1,1)
                      xs = (0,0.25)
                  else:
                     #death_au: check for bass groove
                    #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnableMode == 2:
                    if self.guitars[i].isBassGuitar and self.bassgroovemult != None and multStreak >= 40 and not self.coOpGH and self.bassGrooveEnabled:
                      if multStreak >= 50:
                        multiplier = 6
                        multRange = (0.25,0.5) #MFH division->constant: was (1.0/4.0,2.0/4.0)
                        color = (1,0,0.75,1)
                      else:
                        multiplier = 5
                        multRange = (0.0,0.25) #MFH division->constant: was (0.0/4.0,1.0/4.0)
                        color = (1,0,0.75,1)
                      xs = (0.75,1)
                    #death_au: end check for bass groove
                    elif multStreak >= 30:
                      multiplier = 4
                      multRange = (0.375,0.5) #MFH division->constant: was (3.0/8.0,4.0/8.0)
                      color = (1,-1,1,1)
                    elif multStreak >= 20:
                      multiplier = 3
                      multRange = (0.25,0.375) #MFH division->constant: was (2.0/8.0,3.0/8.0)
                      color = (-1,1,-.75,1)
                    elif multStreak >= 10:
                      multiplier = 2
                      multRange = (0.125,0.25) #MFH division->constant: was (1.0/8.0,2.0/8.0)
                      color = (1,1,-1,1)
                    else:
                      multiplier = 1
                      multRange = (0.0,0.125) #MFH division->constant: was (0.0/8.0,1.0/8.0)
                      color = (1,1,-1,1)
            
              
              #myfingershurt: GH bass groove multiplier: 
              # death_au: added drawing of bassgroovemult image             
              #if self.playerList[i].part.text == "Bass Guitar" and multStreak >= 40 and self.bassGrooveEnableMode == 2:   #bass groove!
              if self.guitars[i].isBassGuitar and multStreak >= 40 and not self.coOpGH and self.bassGrooveEnabled:   #bass groove!
                if self.bassgroovemult != None: #death_au : bassgroovemult image found, draw image
                  self.engine.drawImage(self.bassgroovemult, scale = (.5,-.125), coord = (w*0.134,h*0.19 + self.hOffset[i]), rect = (0,1,multRange[0],multRange[1]))
                
                else: #death_au: bassgroovemult not found
                  #myfingershurt: Temp text bass groove multiplier:
                  glColor3f(0,0.75,1)
                  text = str(self.scoring[i].getScoreMultiplier() * self.multi[i])
                  wid, hig = font.getStringSize(text,0.00325)
                  font.render(text, (.133 - wid / 2, .566),(1, 0, 0),0.00325)     #replacing GH multiplier large text
  
  
              else:
                multcoord = (w*0.134,h*0.19 + self.hOffset[i]) #QQstarS:Set  new postion. I only shown it once.
                
                if not self.coOpType: #akedrou - mult must be above co-op rockmeter.
                  self.engine.drawImage(self.mult, scale = (.5,-.0625), coord = multcoord, rect = (0,1,multRange[0],multRange[1]))
  
              if multStreak == 0:
                streak = 0
                hstreak = 0
              elif multStreak - ((multiplier-1)*10) == 1:
                streak = 0
                hstreak = 1  
              elif multStreak - ((multiplier-1)*10) == 2:
                streak = 1
                hstreak = 0
              elif multStreak - ((multiplier-1)*10) == 3:
                streak = 1
                hstreak = 1
              elif multStreak - ((multiplier-1)*10) == 4:
                streak = 2
                hstreak = 0
              elif multStreak - ((multiplier-1)*10) == 5:
                streak = 2
                hstreak = 1
              elif multStreak - ((multiplier-1)*10) == 6:
                streak = 3
                hstreak = 0
              elif multStreak - ((multiplier-1)*10) == 7:
                streak = 3
                hstreak = 1
              elif multStreak - ((multiplier-1)*10) == 8:
                streak = 4
                hstreak = 0
              elif multStreak - ((multiplier-1)*10) == 9:
                streak = 4
                hstreak = 1
              else:
                streak = 5
                hstreak = 0
    
              r = self.dots
    
              s = 0
              hs = 0
              for t in range(0,5):
                if s < streak:
                  ys = (0.66666667,1.0)  #MFH division->constant: was (2.0/3.0,1.0)
                  s += 1
                elif hs < hstreak:
                  ys = (0.33333333,0.66666667)  #MFH division->constant: was (1.0/3.0,2.0/3.0)
                  hs += 1
                else:
                  ys = (0.0,0.33333333)  #MFH division->constant: was (0.0,1.0/3.0)
                  
                #myfingershurt: using half dots if the file was found earlier:
                # if self.theme < 2: # (already did the rmtype check)
                if self.halfDots:
                  dotscale = (0.125,-.166666667) #MFH division->constant: was (.5*(1.0/4.0),-.5*(1.0/3.0))
                  color = (1,1,1,1)
                  if self.coOpGH:
                    dotrot = -(-.5235987756 - (t * .5235987756))
                    dotcoord = (w*(.446+(t*.027)),(h*.295)-h*(.035*(math.sqrt(5-(t-2)**2))))
                    dotrect = (xs[0],xs[1],ys[1],ys[0])
                  else:
                    dotrot = 0
                    dotcoord = (w*.0425,h*.12+t*(h*.034) + self.hOffset[i])
                    dotrect = (xs[0],xs[1],ys[0],ys[1])
                else:
                  dotrot = 0
                  dotscale = (.5,-.166666667) #MFH division->constant: was (.5,-.5*(1.0/3.0))
                  dotcoord = (w*.044,h*.12+t*(h*.034) + self.hOffset[i])
                  dotrect = (0.0,1.0,ys[0],ys[1])

                self.engine.drawImage(r, scale = dotscale, coord = dotcoord, rect = dotrect, rot = dotrot, color = color)
  
    

              if self.coOpGH and self.numOfPlayers == 2:
                if self.x1[self.coOpPhrase] == 0:
                  self.x1[self.coOpPhrase] = .5
                  self.y1[self.coOpPhrase] = .365
                  self.x2[self.coOpPhrase] = .5
                  self.y2[self.coOpPhrase] = .365
                  self.x3[self.coOpPhrase] = .5
                  self.y3[self.coOpPhrase] = .365
              elif self.coOp:
                if self.x1[i] == 0:
                  self.x1[i] = .134
                  self.y1[i] = .22
                  self.x2[i] = .124
                  self.y2[i] = .23
                  self.x3[i] = .114
                  self.y3[i] = .24
              else:
                if self.x1[i] == 0: #QQstarS:Set [0] to [i]
                  self.x1[i] = .86
                  self.y1[i] = .2
                  self.x2[i] = .86
                  self.y2[i] = .2
                  self.x3[i] = .86
                  self.y3[i] = .2
  
  
              if self.coOpGH and i == self.coOpPlayerMeter:
                if self.starfx: #blazingamer, corrected by myfingershurt, adjusted by worldrave
                  starPowerAmount = (self.coOpStarPower/self.numOfPlayers)
                  if starPowerAmount >= 50 or self.guitars[i].starPowerActive:
                    if self.x1[self.coOpPhrase] < 0.522:   
                      self.x1[self.coOpPhrase] += 0.01
                      if self.x1[self.coOpPhrase] > 0.522:   
                        self.x1[self.coOpPhrase] = 0.522     #Worldrave Notes - Controls 4th Bulbs X axis. Was .526
                    if self.y1[self.coOpPhrase] < 0.464: 
                      self.y1[self.coOpPhrase] += 0.01
                      if self.y1[self.coOpPhrase] > 0.464:
                        self.y1[self.coOpPhrase] = 0.464     #Worldrave Notes - Controls 4th Bulbs Y axis. Was .471
                    if self.x2[self.coOpPhrase] < 0.563:
                      self.x2[self.coOpPhrase] += 0.01
                      if self.x2[self.coOpPhrase] > 0.563:
                        self.x2[self.coOpPhrase] = 0.563     #Worldrave Notes - Controls 5th Bulbs X axis. Was .562
                    if self.y2[self.coOpPhrase] < 0.445:
                      self.y2[self.coOpPhrase] += 0.01
                      if self.y2[self.coOpPhrase] > 0.445:
                        self.y2[self.coOpPhrase] = 0.445     #Worldrave Notes - Controls 5th Bulbs Y axis. Was .449
                    if self.x3[self.coOpPhrase] < 0.597:
                      self.x3[self.coOpPhrase] += 0.01
                      if self.x3[self.coOpPhrase] > 0.597:
                        self.x3[self.coOpPhrase] = 0.597     #Worldrave Notes - Controls 6th Bulbs X axis. Was .597
                    if self.y3[self.coOpPhrase] < 0.403:
                      self.y3[self.coOpPhrase] += 0.01
                      if self.y3[self.coOpPhrase] > 0.403:
                        self.y3[self.coOpPhrase] = 0.403     #Worldrave Notes - Controls 6th Bulbs Y axis. Was .403
                  else:
                    if self.x1[self.coOpPhrase] > 0.5:
                      self.x1[self.coOpPhrase] -= 0.01
                    if self.y1[self.coOpPhrase] > 0.365:
                      self.y1[self.coOpPhrase] -= 0.01
                    if self.x2[self.coOpPhrase] > 0.5:
                      self.x2[self.coOpPhrase] -= 0.01
                    if self.y2[self.coOpPhrase] > 0.365:
                      self.y2[self.coOpPhrase] -= 0.01
                    if self.x3[self.coOpPhrase] > 0.5:
                      self.x3[self.coOpPhrase] -= 0.01
                    if self.y3[self.coOpPhrase] > 0.365:
                      self.y3[self.coOpPhrase] -= 0.01
        
                  if starPowerAmount >= 50 or self.guitars[i].starPowerActive: #QQstarS:Set [0] to [i]
                    lightPos = (0.689655172,1)  #MFH division->constant: was (2.0/2.9,1)
                  else:
                    lightPos = (1.0/2.9,2.0/3.1)  #MFH division->constant: ok any preprocessor worth it's salt would take care of this before runtime... this is pointless.
        
                  if starPowerAmount >= 16.6:
                    lightVis = 1
                  else:
                    lightVis = starPowerAmount/16.6
      
                  wfactor = self.SP.widthf(pixelw = 23.000) #bulb 1
                  spcoord = (w*0.414 ,h*0.407)
                  sprot = .68
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))                   
        
                  if starPowerAmount >= 33.2:
                    lightVis = 1
                  else:
                    lightVis = (starPowerAmount-16.6)/16.6
                  wfactor = self.SP.widthf(pixelw = 23.000) #bulb 2
                  spcoord = (w*0.439,h*0.438)
                  sprot = .46
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))         
                  if starPowerAmount >= 49.8:
                    lightVis = 1
                  else:
                    lightVis = (starPowerAmount-32.2)/16.6
      
                  wfactor = self.SP.widthf(pixelw = 23.000) #bulb 3
                  spcoord = (w*0.468,h*0.455)
                  sprot = .24
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis)) 
        
                  if starPowerAmount >= 66.4:
                    lightVis = 1
                  else:
                    lightVis = (starPowerAmount-49.8)/16.6
      
                  wfactor = self.SP.widthf(pixelw = 32.000) #Worldrave Change - Bulb 4
                  spcoord = (w*self.x1[self.coOpPhrase]*0.96852469,h*self.y1[self.coOpPhrase]*1.011455279)
                  sprot = 0
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis)) 
        
                  if starPowerAmount >= 83:
                    lightVis = 1
                  else:
                    lightVis = (starPowerAmount-66.4)/16.6
      
                  wfactor = self.SP.widthf(pixelw = 32.000)  #Worldrave Change - Bulb 5  
                  spcoord = (w*self.x2[self.coOpPhrase]*0.978698075,h*self.y2[self.coOpPhrase]*1.02813143)
                  sprot = -.34
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis)) 
        
                  if starPowerAmount >= 100:
                    lightVis = 1
                  else:
                    lightVis = (starPowerAmount-83)/16.6
      
                  wfactor = self.SP.widthf(pixelw = 32.000) #Worldrave Change - Bulb 6
                  spcoord = (w*self.x3[self.coOpPhrase]*0.990664588,h*self.y3[self.coOpPhrase]*1.04973235)
                  sprot = -.70
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis)) 
                if self.coopRockmeter:
                  self.engine.drawImage(self.coopRockmeter, scale = (.5,-.5), coord = (w*.5, h*.365))
              
                        
              elif self.coOp:
                if self.starfx:
                  starPowerAmount = self.guitars[i].starPower
                  if starPowerAmount >= 50 or self.guitars[i].starPowerActive:
                    if self.x1[i] < 0.165:
                      self.x1[i] += 0.01
                      if self.x1[i] > 0.165:
                        self.x1[i] = 0.165
                    if self.x2[i] < 0.165:
                      self.x2[i] += 0.01
                      if self.x2[i] > 0.165:
                        self.x2[i] = 0.165
                    if self.x3[i] < 0.165:
                      self.x3[i] += 0.01
                      if self.x3[i] > 0.165:
                        self.x3[i] = 0.165
                  else:
                    if self.x1[i] > 0.134:
                      self.x1[i] -= 0.01
                    if self.x2[i] > 0.124:
                      self.x2[i] -= 0.01
                    if self.x3[i] > 0.114:
                      self.x3[i] -= 0.01
        
                  if starPowerAmount >= 50 or self.guitars[i].starPowerActive: #QQstarS:Set [0] to [i]
                    lightPos = (0.689655172,1)  #MFH division->constant: was (2.0/2.9,1)
                  else:
                    lightPos = (1.0/2.9,2.0/3.1)  #MFH division->constant: ok any preprocessor worth it's salt would take care of this before runtime... this is pointless.
        
                  if starPowerAmount >= 16.6: #QQstarS:Set [0] to [i]
                    lightVis = 1
                  else:
                    lightVis = starPowerAmount/16.6
      
                  wfactor = self.SP.widthf(pixelw = 23.000) #Worldrave Change - Bulb 1
                  spcoord = (w*0.165 ,h*0.21 + self.hOffset[i])
                  sprot = -1.570796
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
        
                  if starPowerAmount >= 33.2: #QQstarS:Set [0] to [i]
                    lightVis = 1
                  else:
                    lightVis = (starPowerAmount-16.6)/16.6
                  wfactor = self.SP.widthf(pixelw = 23.000) #Worldrave Change - Bulb 2
                  spcoord = (w*0.165,h*0.2 + self.hOffset[i])
                  sprot = -1.570796
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
                  
                  if starPowerAmount >= 49.8:
                    lightVis = 1
                  else:
                    lightVis = (starPowerAmount-32.2)/16.6
      
                  wfactor = self.SP.widthf(pixelw = 23.000)  #Worldrave Change - Bulb 3
                  spcoord = (w*0.165,h*0.19 + self.hOffset[i])
                  sprot = -1.570796
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
        
                  if starPowerAmount >= 66.4:
                    lightVis = 1
                  else:
                    lightVis = (starPowerAmount-49.8)/16.6
      
                  wfactor = self.SP.widthf(pixelw = 32.000) #Worldrave Change - Bulb 4
                  spcoord = (w*self.x1[i]*0.96852469,h*self.y1[i]*1.011455279 + self.hOffset[i])
                  sprot = -1.570796
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis)) 
        
                  if starPowerAmount >= 83:
                    lightVis = 1
                  else:
                    lightVis = (starPowerAmount-66.4)/16.6
      
                  wfactor = self.SP.widthf(pixelw = 32.000)  #Worldrave Change - Bulb 5  
                  spcoord = (w*self.x2[i]*0.978698075,h*self.y2[i]*1.02813143 + self.hOffset[i])
                  sprot = -1.570796
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis)) 
        
                  if starPowerAmount >= 100:
                    lightVis = 1
                  else:
                    lightVis = (starPowerAmount-83)/16.6
      
                  wfactor = self.SP.widthf(pixelw = 32.000) #Worldrave Change - Bulb 6
                  spcoord = (w*self.x3[i]*0.990664588,h*self.y3[i]*1.04973235 + self.hOffset[i])
                  sprot = -1.570796
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))  

                self.engine.drawImage(self.rockmeter, scale = (.5,-.5), coord = (w*.134, h*.22 + self.hOffset[i]))

              elif not self.coOpType:
                if self.starfx:
                  starPowerAmount = self.guitars[i].starPower
                  if starPowerAmount >= 50 or self.guitars[i].starPowerActive:
                    if self.x1[i] < 0.886:
                      self.x1[i] += 0.01
                      if self.x1[i] > 0.886:
                        self.x1[i] = 0.886
                    if self.y1[i] < 0.341:
                      self.y1[i] += 0.01
                      if self.y1[i] > 0.341:
                        self.y1[i] = 0.341
                    if self.x2[i] < 0.922:
                      self.x2[i] += 0.01
                      if self.x2[i] > 0.922:
                        self.x2[i] = 0.922
                    if self.y2[i] < 0.324:
                      self.y2[i] += 0.01
                      if self.y2[i] > 0.324:
                        self.y2[i] = 0.324
                    if self.x3[i] < 0.952:
                      self.x3[i] += 0.01
                      if self.x3[i] > 0.952:
                        self.x3[i] = 0.952
                    if self.y3[i] < 0.288:
                      self.y3[i] += 0.01
                      if self.y3[i] > 0.288:
                        self.y3[i] = 0.288
                  else:
                    if self.x1[i] > 0.86:
                      self.x1[i] -= 0.01
                    if self.y1[i] > 0.2:
                      self.y1[i] -= 0.01
                    if self.x2[i] > 0.86:
                      self.x2[i] -= 0.01
                    if self.y2[i] > 0.2:
                      self.y2[i] -= 0.01
                    if self.x3[i] > 0.86:
                      self.x3[i] -= 0.01
                    if self.y3[i] > 0.2:
                      self.y3[i] -= 0.01
        
                  if starPowerAmount >= 50 or self.guitars[i].starPowerActive: #QQstarS:Set [0] to [i]
                    lightPos = (0.689655172,1)  #MFH division->constant: was (2.0/2.9,1)
                  else:
                    lightPos = (1.0/2.9,2.0/3.1)  #MFH division->constant: ok any preprocessor worth it's salt would take care of this before runtime... this is pointless.
        
                  if starPowerAmount >= 16.6: #QQstarS:Set [0] to [i]
                    lightVis = 1
                  else:
                    lightVis = starPowerAmount/16.6
      
                  wfactor = self.SP.widthf(pixelw = 23.000) #Worldrave Change - Bulb 1
                  spcoord = (w*0.772 ,h*0.284 + self.hOffset[i])
                  sprot = .87
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
        
                  if starPowerAmount >= 33.2: #QQstarS:Set [0] to [i]
                    lightVis = 1
                  else:
                    lightVis = (starPowerAmount-16.6)/16.6
                  wfactor = self.SP.widthf(pixelw = 23.000) #Worldrave Change - Bulb 2
                  spcoord = (w*0.795,h*0.312 + self.hOffset[i])
                  sprot = .58
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
        
                  if starPowerAmount >= 49.8:
                    lightVis = 1
                  else:
                    lightVis = (starPowerAmount-32.2)/16.6
      
                  wfactor = self.SP.widthf(pixelw = 23.000)  #Worldrave Change - Bulb 3
                  spcoord = (w*0.822,h*0.329 + self.hOffset[i])
                  sprot = .37
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
        
                  if starPowerAmount >= 66.4:
                    lightVis = 1
                  else:
                    lightVis = (starPowerAmount-49.8)/16.6
      
                  wfactor = self.SP.widthf(pixelw = 32.000) #Worldrave Change - Bulb 4
                  spcoord = (w*self.x1[i]*0.96852469,h*self.y1[i]*1.011455279 + self.hOffset[i])
                  sprot = 0
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
        
                  if starPowerAmount >= 83:
                    lightVis = 1
                  else:
                    lightVis = (starPowerAmount-66.4)/16.6
      
                  wfactor = self.SP.widthf(pixelw = 32.000)  #Worldrave Change - Bulb 5  
                  spcoord = (w*self.x2[i]*0.978698075,h*self.y2[i]*1.02813143 + self.hOffset[i])
                  sprot = -.34
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
        
                  if starPowerAmount >= 100:
                    lightVis = 1
                  else:
                    lightVis = (starPowerAmount-83)/16.6
      
                  wfactor = self.SP.widthf(pixelw = 32.000) #Worldrave Change - Bulb 6
                  spcoord = (w*self.x3[i]*0.990664588,h*self.y3[i]*1.04973235 + self.hOffset[i])
                  sprot = -.70
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                  self.engine.drawImage(self.SP, scale = (wfactor,-wfactor*3), coord = spcoord, rot = sprot,
                                        rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))                        
              
                self.engine.drawImage(self.rockmeter, scale = (.5, -.5), coord = (w*.134, h*.22 + self.hOffset[i]))

              #if (self.coOp and i == 0) or not self.coOp:  #MFH only render for player 0 if co-op mode
              if (self.coOpType and i == self.coOpPlayerMeter) or not self.coOpType:  #MFH only render for player 1 if co-op mode

                #MFH - rock measurement tristate
                #if self.rock[i] > self.rockMax/3.0*2:
                if self.rock[i] > self.rockHiThreshold:
                  rock = self.rockHi
                  useRock = 2
                #elif self.rock[i] > self.rockMax/3.0:
                elif self.rock[i] > self.rockMedThreshold:
                  rock = self.rockMed
                  useRock = 1
                else:
                  rock = self.rockLo
                  useRock = 0

                currentRock = (0.0 + self.rock[i]) / (self.rockMax)
                if self.coOpType:
                  if self.rock[i] >= 0:
                    self.arrowRotation[i] += ( 0.0 + currentRock - self.arrowRotation[i])
                  else:  #QQstarS: Fix the arrow let him never rotation to bottom
                    self.arrowRotation[i] = self.arrowRotation[i]
                  angle = -.48 * math.pi + (self.arrowRotation[i] * math.pi * .96)
                else:
                  if self.rock[i] >= 0:
                    self.arrowRotation[i] += ( 0.0 + currentRock - self.arrowRotation[i]) / 5.0
                  else:  #QQstarS: Fix the arrow let him never rotation to bottom
                    self.arrowRotation[i] = self.arrowRotation[i]
                  angle = -(.460 / 2) * math.pi + .460 * math.pi * self.arrowRotation[i]
                wfactor = self.arrow.widthf(pixelw = 60.000)

                if self.coOpType:
                  score=self.coOpScoreCard.score
                  for playaNum, playa in enumerate(self.playerList):
                    score += self.getExtraScoreForCurrentlyPlayedNotes(playaNum)
                else:
                  score=self.scoring[i].score
                  score += self.getExtraScoreForCurrentlyPlayedNotes(i)

                size      = scoreFont.getStringSize(str(score))
                if self.coOpType:
                  if self.scorePicBand:
                    if self.coOpGH:
                      picbandscale = (.41,-.5)            #Worldrave Notes - Controls Co-Op Score Meter X and Y sizing. Was (.41,-5)
                      picbandcoord = (w*.5,h*.785)    #Worldrave Notes - Controls Co-Op Score Meter X and Y positions.
                    else:
                      picbandscale = (1, -1)
                      picbandcoord = (0, h*1.44)
                    self.engine.drawImage(self.scorePicBand, scale = picbandscale, coord = picbandcoord)
                  if self.coOpGH:
                    x = 0.5-(size[0]/2)  #Worldrave Notes - Controls Co-Op Score X Pos.
                    y = 0.152              #Worldrave Notes - Controls Co-Op Score Y Pos.
                  else:
                    x = 0-(size[0]/2)
                    y = -1.2
                else:
                  x = 0.19-size[0]
                  y = 0.518+self.hFontOffset[i]
                # evilynux - Changed upon worldrave's request
                c1,c2,c3 = self.rockmeter_score_color
                glColor3f(c1,c2,c3)
                #if self.numOfPlayers > 1 and i == 0:
                #  scoreFont.render("%d" % (score), (x, 0.518+self.hFontOffset[i]))
                #else:
                scoreFont.render("%d" % (score),  (x, y))
                
                if self.coOpGH:
                  if self.numOfPlayers == 2:
                    if self.coopRockmeter:
                      if self.failingEnabled:
                        if rock:    
                          if useRock == 0:
                            corockcoord = (w*.45,h*.335)
                          elif useRock == 2:
                            corockcoord = (w*.55,h*.335)
                          else:
                            corockcoord = (w*.5,h*.37)
                          self.engine.drawImage(rock, scale = (.5,-.5), coord = corockcoord)
                        self.engine.drawImage(self.arrow, scale = (wfactor,-wfactor), coord = (w*.5,h*.29), rot = -angle)
                      self.engine.drawImage(self.mult, scale = (.5,-.0625), coord = (w*0.505,h*0.295), rect = (0,1,multRange[0],multRange[1]))
                      if self.rockTop:
                        self.engine.drawImage(self.rockTop, scale = (.5,-.5), coord = (w*.5,h*.3))
                  
                  self.engine.drawImage(self.counter, scale = (.505,-.5), coord = (w*.494,h*.63))
                  
                  if self.coOpRB:
                    multstreak = self.coOpScoreCard.streak
                  
                  glColor4f(0,0,0,1)
                  streak3 = multStreak/1000
                  streak2 = (multStreak-streak3*1000)/100
                  streak1 = (multStreak-streak3*1000-streak2*100)/10
                  streak0 = (multStreak-streak3*1000-streak2*100-streak1*10)
                  text = str(streak0)
                  size = streakFont.getStringSize(text)
                  streakFont.render(text, (.543-size[0]/2, 0.265))
                  glColor4f(1,1,1,1)
                  text = str(streak1)
                  size = streakFont.getStringSize(text)
                  streakFont.render(text, (.511-size[0]/2, 0.265))
                  text = str(streak2)
                  size = streakFont.getStringSize(text)
                  streakFont.render(text, (.482-size[0]/2, 0.265))
                elif self.coOp:
                  self.engine.view.setViewport(1,0)
                  if self.numOfPlayers == 2:
                    if self.coopRockmeter:
                      self.engine.drawImage(self.coopRockmeter, scale = (.5,-.5), coord = (w*.5, h*.265))
                      if self.failingEnabled:
                        if rock:
                          if useRock == 0:
                            corockcoord = (w*.45,h*.235)
                          elif useRock == 2:
                            corockcoord = (w*.55,h*.235)
                          else:
                            corockcoord = (w*.5,h*.27)
                          self.engine.drawImage(rock, scale = (.5,-.5), coord = corockcoord)
                        self.engine.drawImage(self.arrow, scale = (wfactor,-wfactor), coord = (w*.5,h*.19), rot = -angle)
                      self.engine.drawImage(self.mult, scale = (.5,-.0625), coord = (w*0.505,h*0.295), rect = (0,1,0.0,0.125)) 
                      if self.rockTop:
                        self.engine.drawImage(self.rockTop, scale = (.5,-.5), coord = (w*.5,h*.2))
                  
                  self.engine.drawImage(self.counter, scale = (.5,-.5), coord = (w*.5,h*.63))
                  
                  glColor4f(0,0,0,1)
                  streak3 = self.coOpScoreCard.streak/1000
                  streak2 = (self.coOpScoreCard.streak-streak3*1000)/100
                  streak1 = (self.coOpScoreCard.streak-streak3*1000-streak2*100)/10
                  streak0 = (self.coOpScoreCard.streak-streak3*1000-streak2*100-streak1*10)
                  text = str(streak0)
                  size = streakFont.getStringSize(text)
                  streakFont.render(text, (.543-size[0]/2, 0.265))
                  glColor4f(1,1,1,1)
                  text = str(streak1)
                  size = streakFont.getStringSize(text)
                  streakFont.render(text, (.511-size[0]/2, 0.265))
                  text = str(streak2)
                  size = streakFont.getStringSize(text)
                  streakFont.render(text, (.482-size[0]/2, 0.265))
                else:
                  if self.failingEnabled:
                    self.engine.drawImage(rock, scale = (.5,-.5), coord = (w*.86,h*.2 + self.hOffset[i]))
                    self.engine.drawImage(self.arrow, scale = (wfactor,-wfactor), coord = (w*.86,h*.136 + self.hOffset[i]), rot = -angle)
                  else:
                    self.engine.drawImage(self.rockOff, scale = (.5,-.5), coord = (w*.86,h*.2 + self.hOffset[i]))

                  self.engine.drawImage(self.rockTop, scale = (.5,-.5), coord = (w*.86,h*.2 + self.hOffset[i]))

                  self.engine.drawImage(self.counter, scale = (.5,-.5), coord = (w*.15,h*(self.counterY) + self.hOffset[i]))
    
                  if multStreak >= 25 and not self.counterY >= 0.1125:
                    self.counterY += 0.01
                  elif multStreak < 25 and not self.counterY <= -0.1:
                    self.counterY -= 0.01
                  if self.counterY > 0.1125 or ( self.numOfPlayers > 1 ):
                    self.counterY = 0.1125
     
                  if self.counterY == 0.1125 or ( self.numOfPlayers > 1 and multStreak >0 ):
                    glColor4f(0,0,0,1)
                    streak3 = multStreak/1000
                    streak2 = (multStreak-streak3*1000)/100
                    streak1 = (multStreak-streak3*1000-streak2*100)/10
                    streak0 = (multStreak-streak3*1000-streak2*100-streak1*10)
                    text = str(streak0)
                    size = streakFont.getStringSize(text)
                    streakFont.render(text, (.193-size[0]/2, 0.667-size[1]/2+self.hFontOffset[i]))
                    glColor4f(1,1,1,1)
                    text = str(streak1)
                    size = streakFont.getStringSize(text)
                    streakFont.render(text, (.161-size[0]/2, 0.667-size[1]/2+self.hFontOffset[i]))
                    text = str(streak2)
                    size = streakFont.getStringSize(text)
                    streakFont.render(text, (.132-size[0]/2, 0.667-size[1]/2+self.hFontOffset[i]))
    
              if self.youRock == True:
                if self.rockTimer == 1:
                  #self.sfxChannel.setVolume(self.sfxVolume)
                  self.engine.data.rockSound.play()
                if self.rockTimer < self.rockCountdown:
                  self.rockTimer += 1
                  self.engine.drawImage(self.rockMsg, scale = (0.5, -0.5), coord = (w/2,h/2))
                if self.rockTimer >= self.rockCountdown:
                  self.rockFinished = True
    
              if self.failed:
                if self.failTimer == 0:
                  self.song.pause()
                if self.failTimer == 1:
                  #self.sfxChannel.setVolume(self.sfxVolume)
                  self.engine.data.failSound.play()
                if self.failTimer < 100:
                  self.failTimer += 1
                  self.engine.drawImage(self.failMsg, scale = (0.5, -0.5), coord = (w/2,h/2))
                else:
                  self.finalFailed = True
              
              if self.pause:
                self.engine.view.setViewport(1,0)
                self.engine.drawImage(self.pauseScreen, scale = (self.pause_bkg[2], -self.pause_bkg[3]), coord = (w*self.pause_bkg[0],h*self.pause_bkg[1]), stretched = 3)
                
              if self.finalFailed and self.song:
                self.engine.view.setViewport(1,0)
                self.engine.drawImage(self.failScreen, scale = (self.fail_bkg[2], -self.fail_bkg[3]), coord = (w*self.fail_bkg[0],h*self.fail_bkg[1]), stretched = 3) 
    
                # evilynux - Closer to actual GH3
                font = self.engine.data.pauseFont
                text = Dialogs.removeSongOrderPrefixFromName(self.song.info.name).upper()
                scale = font.scaleText(text, maxwidth = 0.398, scale = 0.0038)
                size = font.getStringSize(text, scale = scale)
                font.render(text, (.5-size[0]/2.0,.37-size[1]), scale = scale)
  
                #now = self.getSongPosition()
  
                diff = str(self.playerList[0].difficulty)
                # compute initial position
                pctComplete = min(100, int(now/self.lastEvent*100))

                
                curxpos = font.getStringSize("%s " % self.tsCompleted, scale = 0.0015)[0]
                curxpos += font.getStringSize(str(pctComplete), scale = 0.003)[0]
                curxpos += font.getStringSize(self.tsPercentOn, scale = 0.0015)[0]
                curxpos += font.getStringSize(diff, scale = 0.003)[0]
                curxpos = .5-curxpos/2.0
                c1,c2,c3 = self.fail_completed_color
                glColor3f(c1,c2,c3)              
  
                # now render
                text = "%s " % self.tsCompleted
                size = font.getStringSize(text, scale = 0.0015)
                # evilynux - Again, for this very font, the "real" height value is 75% of returned value
                font.render(text, (curxpos, .37+(font.getStringSize(text, scale = 0.003)[1]-size[1])*.75), scale = 0.0015)
                text = str(pctComplete)
                curxpos += size[0]
  
                size = font.getStringSize(text, scale = 0.003)
                font.render(text, (curxpos, .37), scale = 0.003)
                text = self.tsPercentOn
                curxpos += size[0]
                size = font.getStringSize(text, scale = 0.0015)
                font.render(text, (curxpos, .37+(font.getStringSize(text, scale = 0.003)[1]-size[1])*.75), scale = 0.0015)
                text = diff
                curxpos += size[0]
                font.render(text, (curxpos, .37), scale = 0.003)
  
                if not self.failEnd:
                  self.failGame()

              if self.coOpType: #since it hasn't been set yet...
                self.engine.view.setViewportHalf(self.numOfPlayers,i)
                
              if not self.pause and not self.failed and not self.ending:
                if self.displayText[i] != None:
                  glColor3f(.8,.75,.01)
                  size = sphraseFont.getStringSize(self.displayText[i], scale = self.displayTextScale[i])
                  sphraseFont.render(self.displayText[i], (.5-size[0]/2,self.textY[i]-size[1]), scale = self.displayTextScale[i])
  
              if self.hopoIndicatorEnabled and not self.guitars[i].isDrum and not self.pause and not self.failed: #MFH - HOPO indicator (grey = strums required, white = strums not required)
                text = self.tsHopoIndicator
                if self.guitars[i].hopoActive > 0:
                  c1,c2,c3 = self.hopoIndicatorActiveColor
                  glColor3f(c1,c2,c3)  #white
                else:
                  c1,c2,c3 = self.hopoIndicatorInactiveColor
                  glColor3f(c1,c2,c3)  #grey
                w, h = font.getStringSize(text,0.00150)
                font.render(text, (self.hopoIndicatorX - w / 2, self.hopoIndicatorY),(1, 0, 0),0.00150)     #off to the right slightly above fretboard
                glColor3f(1, 1, 1)  #cracker white
    
                  
          elif (self.rmtype == 2):# and self.countdown<=4) or (self.theme == 1 and self.numOfPlayers==1):
            if not self.pauseScreen == None:
              w = self.wPlayer[i]
              h = self.hPlayer[i]
              wBak = w
              hBak = h
              if self.guitars[i].starPowerActive and not self.coOpRB:
                #death_au: added checks for bass groove here so multiplier is correct    
                #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnableMode > 0:
                if self.guitars[i].isBassGuitar and not self.coOpGH and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnabled:
                  if multStreak >= 50:
                    multiplier = 6
                    multRange = (3.0/4.0,4.0/4.0)
                    color = (.3,.7,.9,1)
                  else:
                    multiplier = 5
                    multRange = (2.0/4.0,3.0/4.0)
                    color = (.3,.7,.9,1)
                #death_au: end bass groove check
                elif multStreak >= 30:
                  multiplier = 4
                  multRange = (7.0/8.0,8.0/8.0)
                  color = (.3,.7,.9,1)
                elif multStreak >= 20:
                  multiplier = 3
                  multRange = (6.0/8.0,7.0/8.0)
                  color = (.3,.7,.9,1)
                elif multStreak >= 10:
                  multiplier = 2
                  multRange = (5.0/8.0,6.0/8.0)
                  color = (.3,.7,.9,1)
                else:
                  multiplier = 1
                  multRange = (4.0/8.0,5.0/8.0)
                  color = (.3,.7,.9,1)
              else:
                #death_au: added checks for bass groove here so multiplier is correct    
                #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnableMode > 0:
                if self.guitars[i].isBassGuitar and not self.coOpGH and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnabled:
                  if multStreak >= 50:
                    multiplier = 6
                    multRange = (1.0/4.0,2.0/4.0)
                    color = (1,1,-1,1)
                  else:
                    multiplier = 5
                    multRange = (0.0/4.0,1.0/4.0)
                    color = (1,1,-1,1)
                #death_au: end bass groove check
                elif multStreak >= 30:
                  multiplier = 4
                  multRange = (3.0/8.0,4.0/8.0)
                  color = (1,-1,1,1)
                elif multStreak >= 20:
                  multiplier = 3
                  multRange = (2.0/8.0,3.0/8.0)
                  color = (-1,1,-.75,1)
                elif multStreak >= 10:
                  multiplier = 2
                  multRange = (1.0/8.0,2.0/8.0)
                  color = (1,1,-1,1)
                else:
                  multiplier = 1
                  multRange = (0.0/8.0,1.0/8.0)
                  color = (1,1,-1,1)
    
              #myfingershurt: for UC's RB mult
              if self.multRbFill:
                if multStreak == 0:
                  streak = 0
    
                elif multStreak - ((multiplier-1)*10) == 1:
                  streak = 0
    
                elif multStreak - ((multiplier-1)*10) == 2:
                  streak = 1
    
                elif multStreak - ((multiplier-1)*10) == 3:
                  streak = 2
    
                elif multStreak - ((multiplier-1)*10) == 4:
                  streak = 3
    
                elif multStreak - ((multiplier-1)*10) == 5:
                  streak = 4
    
                elif multStreak - ((multiplier-1)*10) == 6:
                  streak = 5
    
                elif multStreak - ((multiplier-1)*10) == 7:
                  streak = 6
    
                elif multStreak - ((multiplier-1)*10) == 8:
                  streak = 7
    
                elif multStreak - ((multiplier-1)*10) == 9:
                  streak = 8
    
                else:
                  streak = 9
  
              else:
                if multStreak == 0:
                  streak = 0
                  hstreak = 0
                elif multStreak - ((multiplier-1)*10) == 1:
                  streak = 0
                  hstreak = 1
                elif multStreak - ((multiplier-1)*10) == 2:
                  streak = 1
                  hstreak = 0
                elif multStreak - ((multiplier-1)*10) == 3:
                  streak = 1
                  hstreak = 1
                elif multStreak - ((multiplier-1)*10) == 4:
                  streak = 2
                  hstreak = 0
                elif multStreak - ((multiplier-1)*10) == 5:
                  streak = 2
                  hstreak = 1
                elif multStreak - ((multiplier-1)*10) == 6:
                  streak = 3
                  hstreak = 0
                elif multStreak - ((multiplier-1)*10) == 7:
                  streak = 3
                  hstreak = 1
                elif multStreak - ((multiplier-1)*10) == 8:
                  streak = 4
                  hstreak = 0
                elif multStreak - ((multiplier-1)*10) == 9:
                  streak = 4
                  hstreak = 1
                else:
                  streak = 5
                  hstreak = 0
 
              if self.rock[i] >= 0: 
                currentRock = (0.0 + self.rock[i]) / (self.rockMax)
              else:
                currentRock = (0.0 + 0) / (self.rockMax)
              heightIncrease = h*0.6234375*currentRock*0.65
              if self.coOpRB and i == 0:
                if self.rock[self.coOpPlayerMeter] >= 0:
                  currentRockCoOp = (0.0 + self.rock[self.coOpPlayerMeter]) / self.rockMax
                else:
                  currentRockCoOp = (0.0 + 0) / (self.rockMax)
                heightIncreaseCoOp = h*0.6234375*currentRockCoOp*0.65
    

    
              if not self.pause and not self.failed and not (self.guitars[i].coOpFailed and not self.guitars[i].coOpRestart):
                if self.coOpGH:
                  currentSP = self.coOpStarPower/(100.0*self.numOfPlayers)
                else:
                  currentSP = self.guitars[i].starPower/100.0
                  
                #volshebnyi - overdrive bar positioning - simplified
                self.engine.view.setViewportHalf(self.numOfPlayers,i)
                vCoord = 0
                if self.countdown>3.0:
                  vCoord = - 75 * (self.countdown - 3.0)
                  self.oBarScale = Theme.oBarHScale * self.guitars[i].boardWidth / math.sqrt(self.camera.origin[1]**2+(self.camera.origin[2]-0.5-vCoord/125)**2) * self.oBarScaleCoef

                self.engine.drawImage(self.oBottom, scale = (self.oBarScale,.5), coord = (w/2,h/12+ vCoord), stretched = 1)
                
                if self.oBarScale == 0.0:
                  self.oBarScale = Theme.oBarHScale * self.guitars[i].boardWidth / math.sqrt(self.camera.origin[1]**2+(self.camera.origin[2]-0.5-vCoord/125)**2) * self.oBarScaleCoef
                
                if Theme.oBar3dFill:
                  offset=(currentSP-0.5)*(1-currentSP) / self.camera.origin[1] * 0.8
                  self.engine.drawImage(self.oFill, scale = (self.oBarScale*currentSP,.5), coord = (w/2*(1+self.oBarScale*(currentSP-1)),h/12+ vCoord), rect = (0,currentSP,0,1), stretched = 1, rOffset = offset)
                else:
                  self.engine.drawImage(self.oFill, scale = (self.oBarScale*currentSP,.5), coord = (w/2*(1+self.oBarScale*(currentSP-1)),h/12+ vCoord), rect = (0,currentSP,0,1), stretched = 1)

                self.engine.drawImage(self.oTop, scale = (self.oBarScale,.5), coord = (w/2,h/12+ vCoord), stretched = 1)
            
                if self.rb_sp_neck_glow and self.guitars[i].starPower >= 50 and not self.guitars[i].starPowerActive:
                  self.engine.drawImage(self.oFull, scale = (self.oBarScale,.5), coord = (w/2,h/12), color = (1,1,1,self.rbOverdriveBarGlowVisibility), stretched = 1)
                
                #must duplicate to other theme 
                #if self.playerList[i].part.text == "Bass Guitar" and multStreak >= 40 and self.bassGrooveEnableMode > 0:   #bass groove!
                if self.guitars[i].isBassGuitar and not self.coOpGH and multStreak >= 40 and self.bassGrooveEnabled:   #bass groove!
                  #death_au: bassgroove multiplier image
                  if self.bassgroovemult != None:
                    text = self.tsBassGroove   #kk69: displays "Bass Groove" whenever active, like Rock Band (only for RB theme)
                    wid, hig = font.getStringSize(text,0.00150)
                    
                    #MFH - if Jurgen is active on the current player, raise "Bass Groove" up above "Jurgen Is Here":
                    if self.jurgPlayer[i]:
                      font.render(text, (0.47 - wid / 2, 0.165),(1, 0, 0),0.00210)#end kk69
                    else:
                      font.render(text, (0.47 - wid / 2, 0.190),(1, 0, 0),0.00210)#end kk69
  
                    #UC's mult
                    if self.multRbFill and multStreak > 0:
                      self.engine.drawImage(self.mult2, scale = (.95,-.82/8.0), coord = (w*0.5023,h*0.0585), rect = (0,1,(streak/10.0),(streak+1)/10.0))
                      
                    if self.multRbFill:
                      multscale = (.8,-.8/4.0)
                      multcoord = (w*0.5,h*0.05)                  
                    else:
                      multscale = (.5,-.5/4.0)
                      multcoord = (w*0.5,h*0.05)
                    self.engine.drawImage(self.bassgroovemult, scale = multscale, coord = multcoord, rect = (0,1,multRange[0],multRange[1]))
  
                  else:
                    #myfingershurt: Temp text bass groove multiplier:
                    glColor3f(0,0.75,1)


                    #text = self.tsBassGrooveLabel + str(self.playerList[i].getScoreMultiplier() * self.multi[i]) + "x"
                    text = "%s%d%s" % (self.tsBassGrooveLabel, self.scoring[i].getScoreMultiplier() * self.multi[i], "x")
                    wid, hig = font.getStringSize(text,0.00150)
                    font.render(text, (.500 - wid / 2, .690),(1, 0, 0),0.00150)     #replacing normal rock band multiplier text
                
                else:              
    
                  #myfingershurt: UC's mult
                  if self.multRbFill and multStreak > 0:
                    if self.rbmfx: #blazingamer
                      if multStreak > 9:   #draw bigger!
                        multscale = (.95,-.82/8.0)
                        multcoord = (w*0.5023,h*0.0585)
                      else:
                        #myfingershurt: overlay streak perfectly:
                        multscale = (.6,-.5/8.0)
                        multcoord = (w*0.501,h*0.055)
                    else:
                      multscale = (.95,-.82/8.0)
                      multcoord = (w*0.5023,h*0.0585)         
                    self.engine.drawImage(self.mult2, scale = multscale, coord = multcoord, rect = (0,1,(streak/10.0),(streak+1)/10.0))
  
                  if self.multRbFill:
                    if self.rbmfx:  #blazingamer
                      if multStreak > 9:   #draw bigger!
                        multscale = (.8,-.8/8.0)
                        multcoord = (w*0.5,h*0.05)
                      else:
                        multscale = (.5,-.5/8.0)
                        multcoord = (w*0.5,h*0.05)
                    else:
                      multscale = (.8,-.8/8.0)
                      multcoord = (w*0.5,h*0.05)                  
                  else:
                    multscale = (.5,-.5/8.0)
                    multcoord = (w*0.5,h*0.05)
                  self.engine.drawImage(self.mult, scale = multscale, coord = multcoord, rect = (0,1,multRange[0],multRange[1]))
  
              glColor4f(1,1,1,1)
 
              if not self.coOpType:
                self.engine.view.setViewportHalf(self.numOfPlayers,i)
              else:
                self.engine.view.setViewportHalf(1,i)  

              if currentRock == 1 and self.failingEnabled and not self.coOpRB:
                if (self.coOpType and i == self.coOpPlayerMeter) or not self.coOpType:  #MFH only render for player 1 if co-op mode
                  self.engine.drawImage(self.rockFull, scale = (.5,.5), coord = (w*0.07,h*0.5))
                  failUse = False
              else:
                if self.coOpRB:
                  fillColor = (0,0,0,0)
                  if currentRock < 0.333:
                    failUse = True
                    self.failViz[i] -= .025
                    if self.failViz[i] < 0.0:
                      self.failViz[i] = 1.0
                  else:
                    failUse = False
                    self.failViz[i] = 1.0
                else:
                  if currentRock < 0.333:
                    fillColor = (1,0,0,1)
                    failUse = True
                    self.failViz[i] -= .025
                    if self.failViz[i] < 0.0:
                      self.failViz[i] = 1.0
                  elif currentRock < 0.666:
                    fillColor = (1,1,0,1)
                    failUse = False
                    self.failViz[i] = 1.0
                  else:
                    fillColor = (0,1,0,1)
                    failUse = False
                if self.coOpRB and i == 0:
                  if self.numDeadPlayers > 0:
                    fillColorCoOp = (.67, 0, 0, 1)
                  else:
                    if currentRockCoOp < 0.333:
                      fillColorCoOp = (1,0,0,1)
                    elif currentRockCoOp < 0.666:
                      fillColorCoOp = (1,1,0,1)
                    else:
                      fillColorCoOp = (0,1,0,1)
                      
                if (self.coOpType and i == self.coOpPlayerMeter) or (self.coOpRB and i == 0) or not self.coOpType:  #MFH only render for player 1 if co-op mode
                  self.engine.drawImage(self.rockBottom, scale = (.5,.5), coord = (w*0.07, h*0.5))
  
                if self.failingEnabled == False:
                  if (self.coOpType and i == self.coOpPlayerMeter) or (self.coOpRB and i == 0) or not self.coOpType:  #MFH only render for player 1 if co-op mode
                    self.engine.drawImage(self.rockOff, scale = (.5,.5), coord = (w*0.07, h*0.5))
                else:
                  if (self.coOpType and i == self.coOpPlayerMeter) or not self.coOpType:  #MFH only render for player 1 if co-op mode
                    self.engine.drawImage(self.rockFill, scale = (.5,.5*currentRock), coord = (w*0.07, h*0.3-heightIncrease/2+heightIncrease), color = fillColor)
                  if self.coOpRB and i == 0:
                    self.engine.drawImage(self.rockFill, scale = (.5,.5*currentRockCoOp), coord = (w*0.07, h*0.3-heightIncreaseCoOp/2+heightIncreaseCoOp), color = fillColorCoOp)

                if (self.coOpType and i == self.coOpPlayerMeter) or (self.coOpRB and i == 0) or not self.coOpType:  #MFH only render for player 1 if co-op mode
                  self.engine.drawImage(self.rockTop, scale = (.5,.5), coord = (w*0.07, h*0.5))
                  if self.coOpRB and self.numDeadPlayers > 0:
                    self.rockFailViz += .025
                    if self.rockFailViz > 1.0:
                      self.rockFailViz = 0.0
                    if not (self.guitars[i].coOpFailed and not self.guitars[i].coOpRestart):
                      failUse = True
                      self.failViz[i] = self.rockFailViz
                    if self.rockFailFound:
                      self.engine.drawImage(self.rockTopFail, scale = (.5,.5), coord = (w*0.07, h*0.5), color = (1,1,1,self.rockFailViz))
  
              wfactor = self.rockArr[i].widthf(pixelw = 60.000)
              
              if self.coOpRB:
                if self.numDeadPlayers > 0 and not (self.guitars[i].coOpFailed and not self.guitars[i].coOpRestart) and not self.failed:
                  failUse = True
                  self.failViz[i] = 1.0 - self.rockFailViz

              if failUse:
                if (self.guitars[i].coOpFailed and not self.guitars[i].coOpRestart) or self.failed:
                  failUse = True
                  redBlink = 0.4
                  self.failViz[i] = 0
                else:
                  redBlink = .7 + (.3 * self.failViz[i])
                failColor = (redBlink,self.failViz[i],self.failViz[i],1)
                
              if not self.coOpType:  #MFH only render for player 1 if co-op mode
                if self.failingEnabled:  
                  if failUse:
                    failColor = failColor
                  else:
                    failColor = (1,1,1,1)
                  self.engine.drawImage(self.rockArr[i], scale = (wfactor,-wfactor), coord = (w*.1,h*.3+heightIncrease), color = failColor)
                  if self.guitars[i].starPowerActive and self.rockArrGlow:
                    self.engine.drawImage(self.rockArrGlow, scale = (wfactor,-wfactor), coord = (w*.1,h*.3+heightIncrease))

                whichScorePic = self.scorePic[i]
              elif self.coOpRB:
                spreadOut = 0.0
                for j in range(i+1, self.numOfPlayers):
                  if abs(self.rock[i]-self.rock[j]) < 250.0:
                    spreadOut += .04
                if self.failingEnabled:  
                  if failUse:
                    failColor = failColor
                  else:
                    failColor = (1,1,1,1)
                  self.engine.drawImage(self.rockArr[i], scale = (wfactor,-wfactor), coord = (w*(.1+spreadOut),h*.3+heightIncrease), color = failColor)
                  if self.guitars[i].starPowerActive and self.rockArrGlow:
                    self.engine.drawImage(self.rockArrGlow, scale = (wfactor,-wfactor), coord = (w*(.1+spreadOut),h*.3+heightIncrease))
                if i == 0:
                  whichScorePic = self.scorePicBand
              
              elif self.coOpType and i == self.coOpPlayerMeter:
                if self.failingEnabled:  
                  if failUse:
                    failColor = failColor
                  else:
                    failColor = (1,1,1,1)
                  self.engine.drawImage(self.rockArr[i], scale = (wfactor,-wfactor), coord = (w*.1,h*.3+heightIncrease), color = failColor)
                  if not self.coOp and self.guitars[i].starPowerActive and self.rockArrGlow:
                    self.engine.drawImage(self.rockArrGlow, scale = (wfactor,-wfactor), coord = (w*.1,h*.3+heightIncrease))
                if self.coOp or self.coOpGH:
                  whichScorePic = self.scorePicBand
                else:
                  whichScorePic = self.scorePic[i]

              if self.unisonActive:
                if self.unisonPic and i == 0:
                  self.engine.drawImage(self.unisonPic, scale = (.5,-.5), coord = (w*.5,h*.65))
                unisonX = .05*(self.unisonNum-1)
                unisonI = .05*self.unisonNum
                if self.haveUnison[i]:
                  if self.unisonEarn[i]:
                    partcolor = (1,1,1,1)
                  elif self.inUnison[i]:
                    partcolor = (.8, .8, .8, 1)
                  else:
                    partcolor = (.6,.6,.6,1)
                  self.engine.drawImage(self.part[i], scale = (.15,-.15), coord = (w*(.5-unisonX+unisonI*i),h*.58), color = partcolor)
              try:
  
  
                #myfingershurt: locale.format call adds commas to separate numbers just like Rock Band

                #if (self.coOp and i == 0) or not self.coOp:  #MFH only render for player 0 if co-op mode
                if (self.coOpType and i == self.coOpPlayerMeter) or (self.coOpRB and i == 0) or not self.coOpType:  #MFH only render for player 1 if co-op mode
  
                  if self.coOpType:
                    score=self.coOpScoreCard.score
                    for playaNum, playa in enumerate(self.playerList):
                      score += self.getExtraScoreForCurrentlyPlayedNotes(playaNum)
                  else:
                    score= self.scoring[i].score
                    score += self.getExtraScoreForCurrentlyPlayedNotes(i)

                  scoretext = locale.format("%d", score, grouping=True)
                  #myfingershurt: swapping the number "0" and the letter "O" in the score font for accurate Rock Band score type!
                  scoretext = scoretext.replace("0","O")
                  scW, scH = scoreFont.getStringSize(scoretext)
  
                  scorepicheight = whichScorePic.height1()
                  self.engine.drawImage(whichScorePic, scale = (.5,.5), coord = (w*0.9, h*0.8304))
                  
                  if self.coOpRB and self.starPowersActive > 0 and self.bandMultFound:
                    if self.starPowersActive == 1:
                      bandMultRange = (0.0, (1.0/3.0))
                    elif self.starPowersActive == 2:
                      bandMultRange = ((1.0/3.0), (2.0/3.0))
                    else:
                      bandMultRange = ((2.0/3.0), 1.0)
                    self.engine.drawImage(self.bandStarMult, scale = (.2,(-.2/3.0)), coord = (w*0.6994, h*0.8304), rect = (0,1,bandMultRange[0],bandMultRange[1]))
                  scoreFont.render(scoretext, (0.97-scW, 0.1050 ))    #last change +0.0015
  
              except Exception, e:
                #Log.warn("Unable to render score/streak text: %s" % e)
                scorepicheight = 0  #exception placeholder



              #myfingershurt: locale.format call adds commas to separate numbers just like Rock Band
              if self.coOpRB or self.coOpGH:
                streaktext = locale.format("%d", self.coOpScoreCard.streak, grouping=True)
              else:
                streaktext = locale.format("%d", multStreak, grouping=True)
              #myfingershurt: swapping the number "0" and the letter "O" in the score font for accurate Rock Band score type!
              streaktext = streaktext.replace("0","O")
              stW, stH = streakFont.getStringSize(streaktext)
              
              #streak counter box:
              if self.coOpType and not self.coOp:
                if i == 0:
                  counterimgheight = self.counter.height1()
                  self.engine.drawImage(self.counter, scale = (.5,-.5), coord = (w*.915, h*0.7720)) 
                  streakFont.render(streaktext, (0.97-stW,0.1500 ))    #last change +0.0015

              self.engine.view.setViewportHalf(self.numOfPlayers,i)

              if not self.coOpType or self.coOp:
                counterimgheight = self.counter.height1()
                self.engine.drawImage(self.counter, scale = (.5,-.5), coord = (w*.915, h*0.7720))
                streakFont.render(streaktext, (0.97-stW,0.1500 ))    #last change +0.0015
                

              if not self.pause and not self.failed and not self.ending:
                if self.displayText[i] != None:
                  glColor3f(.8,.75,.01)
                  size = sphraseFont.getStringSize(self.displayText[i], scale = self.displayTextScale[i])
                  sphraseFont.render(self.displayText[i], (.5-size[0]/2,self.textY[i]-size[1]), scale = self.displayTextScale[i])
    
              if self.youRock == True:
                if self.rockTimer == 1:
                  #self.sfxChannel.setVolume(self.sfxVolume)
                  self.engine.data.rockSound.play()
                  for num, thePlayer in enumerate(self.playerList):   #MFH - flash overdrive strings in RB theme
                    self.guitars[num].overdriveFlashCount = 0  #MFH - this triggers the oFlash strings & timer
                    self.guitars[num].ocount = 0  #MFH - this triggers the oFlash strings & timer
                if self.rockTimer < self.rockCountdown:
                  self.rockTimer += 1
                  self.engine.drawImage(self.rockMsg, scale = (0.5, -0.5), coord = (w/2,h/2))
                if self.rockTimer >= self.rockCountdown:
                  self.rockFinished = True
              
              if self.guitars[i].coOpFailed and not self.guitars[i].coOpRestart and self.coOpRB and not self.failed:
                self.engine.drawImage(self.coOpFailImg, scale = (.5,-.5), coord = (w*.5, h*0.65))
                
                checks = self.timesFailed[i] - 1
                for box in range(3):
                  if box <= checks:
                    self.engine.drawImage(self.rescueCheck, scale = (.1,-.1), coord = (w*(.42+(.080*box)), h*0.5))
                  else:
                    self.engine.drawImage(self.rescueBox, scale = (.1,-.1), coord = (w*(.42+(.080*box)), h*0.5))
         
              if self.failed:
                if self.failTimer == 0:
                  self.song.pause()
                if self.failTimer == 1:
                  #self.sfxChannel.setVolume(self.sfxVolume)
                  self.engine.data.failSound.play()
                if self.failTimer < 100:
                  self.failTimer += 1
                  self.engine.drawImage(self.failMsg, scale = (0.5, -0.5), coord = (w/2,h/2))
                else:
                  self.finalFailed = True
            
              if self.pause:
                self.engine.view.setViewport(1,0)
                self.engine.drawImage(self.pauseScreen, scale = (self.pause_bkg[2], -self.pause_bkg[3]), coord = (w*self.pause_bkg[0],h*self.pause_bkg[1]), stretched = 3)
                
              if self.finalFailed and self.song:
                self.engine.view.setViewport(1,0)
                self.engine.drawImage(self.failScreen, scale = (self.fail_bkg[2], -self.fail_bkg[3]), coord = (w*self.fail_bkg[0],h*self.fail_bkg[1]), stretched = 3)
    
                text = Dialogs.removeSongOrderPrefixFromName(self.song.info.name)
                size = font.getStringSize(text)
                font.render(text, (0.5-size[0]/2.0,0.3-size[1]))
                #now = self.getSongPosition()

                pctComplete = min(100, int(now/self.lastEvent*100))
                #MFH string concatenation -> modulo formatting
                #text = str(pctComplete) + self.tsPercentComplete
                text = "%d%s" % (pctComplete, self.tsPercentComplete)
                size = font.getStringSize(text)
                font.render(text, (0.5-size[0]/2.0, 0.3))
                if not self.failEnd:
                  self.failGame()
    
               #QQstarS:add the code in for loop end of here
  
              if self.hopoIndicatorEnabled and not self.guitars[i].isDrum and not self.pause and not self.failed: #MFH - HOPO indicator (grey = strums required, white = strums not required)
                text = self.tsHopoIndicator
                if self.guitars[i].hopoActive > 0:
                  c1,c2,c3 = self.hopoIndicatorActiveColor
                  glColor3f(c1,c2,c3)  #white
                else:
                  c1,c2,c3 = self.hopoIndicatorInactiveColor
                  glColor3f(c1,c2,c3)  #grey
                w, h = font.getStringSize(text,0.00150)
                font.render(text, (self.hopoIndicatorX - w / 2, self.hopoIndicatorY),(1, 0, 0),0.00150)     #off to the right slightly above fretboard
                glColor3f(1, 1, 1)  #cracker white
  
          elif self.rmtype == 3:
            if not self.pauseScreen == None:
              w = self.wPlayer[i]
              h = self.hPlayer[i]
              wBak = w
              hBak = h
              if self.guitars[i].starPowerActive: #QQstarS:Set [0] to [i]
                
                #myfingershurt: so that any GH theme can use dotshalf.png:
                if self.theme < 2:
                  if self.halfDots:
                    #death_au: check for bass groove
                    #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnableMode == 2:
                    if self.guitars[i].isBassGuitar and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnabled:
                      if multStreak >= 50:
                        multiplier = 6
                        multRange = (0.75,1.00) #MFH division->constant: was (3.0/4.0,4.0/4.0)
                        color = (1,0,0.75,1)
                      else:
                        multiplier = 5
                        multRange = (0.5,0.75) #MFH division->constant: was (2.0/4.0,3.0/4.0)
                        color = (1,0,0.75,1)
                      xs = (0.75,1)
                    #death_au: end check for bass groove
                    elif multStreak >= 30:
                      multiplier = 4
                      multRange = (0.875,1.0) #MFH division->constant: was (7.0/8.0,8.0/8.0)
                      color = (.3,.7,.9,1)
                      xs = (0.75,1)
                    elif multStreak >= 20:
                      multiplier = 3
                      multRange = (0.75,0.875) #MFH division->constant: was (6.0/8.0,7.0/8.0)
                      color = (.3,.7,.9,1)
                      xs = (0.75,1)
                    elif multStreak >= 10:
                      multiplier = 2
                      multRange = (0.625,0.75) #MFH division->constant: was (5.0/8.0,6.0/8.0)
                      color = (.3,.7,.9,1)
                      xs = (0.75,1)
                    else:
                      multiplier = 1
                      multRange = (0.5,0.625) #MFH division->constant: was (4.0/8.0,5.0/8.0)
                      color = (.3,.7,.9,1)
                      xs = (0.75,1)
                  else:
                    #death_au: check for bass groove
                    #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnableMode == 2:
                    if self.guitars[i].isBassGuitar and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnabled:
                      if multStreak >= 50:
                        multiplier = 6
                        multRange = (0.75,1.0) #MFH division->constant: was (3.0/4.0,4.0/4.0)
                        color = (1,0,0.75,1)
                      else:
                        multiplier = 5
                        multRange = (0.5,0.75) #MFH division->constant: was (2.0/4.0,3.0/4.0)
                        color = (1,0,0.75,1)
                    #death_au: end check for bass groove
                    elif multStreak >= 30:
                      multiplier = 4
                      multRange = (0.875,1.0) #MFH division->constant: was (7.0/8.0,8.0/8.0)
                      color = (.3,.7,.9,1)
                    elif multStreak >= 20:
                      multiplier = 3
                      multRange = (0.75,0.875) #MFH division->constant: was (6.0/8.0,7.0/8.0)
                      color = (.3,.7,.9,1)
                    elif multStreak >= 10:
                      multiplier = 2
                      multRange = (0.625,0.75) #MFH division->constant: was (5.0/8.0,6.0/8.0)
                      color = (.3,.7,.9,1)
                    else:
                      multiplier = 1
                      multRange = (0.5,0.625) #MFH division->constant: was (4.0/8.0,5.0/8.0)
                      color = (.3,.7,.9,1)
              else:
                #myfingershurt: so that any GH theme can use dotshalf.png:
                if self.theme < 2:
                  if self.halfDots:
                    #death_au: check for bass groove
                    #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnableMode == 2:
                    if self.guitars[i].isBassGuitar and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnabled:
                      if multStreak >= 50:
                        multiplier = 6
                        multRange = (0.25,0.5) #MFH division->constant: was (1.0/4.0,2.0/4.0)
                        color = (1,0,0.75,1)
                      else:
                        multiplier = 5
                        multRange = (0.0,0.25) #MFH division->constant: was (0.0/4.0,1.0/4.0)
                        color = (1,0,0.75,1)
                      xs = (0.75,1)
                    #death_au: end check for bass groove
                    elif multStreak >= 30:
                      multiplier = 4
                      multRange = (0.375,0.5) #MFH division->constant: was (3.0/8.0,4.0/8.0)
                      color = (1,-1,1,1)
                      xs = (0.5,0.75)
                    elif multStreak >= 20:
                      multiplier = 3
                      multRange = (0.25,0.375) #MFH division->constant: was (2.0/8.0,3.0/8.0)
                      color = (-1,1,-.75,1)
                      xs = (0.25,0.5)
                    elif multStreak >= 10:
                      multiplier = 2
                      multRange = (0.125,0.25) #MFH division->constant: was (1.0/8.0,2.0/8.0)
                      color = (1,1,-1,1)
                      xs = (0,0.25)
                    else:
                      multiplier = 1
                      multRange = (0.0,0.125) #MFH division->constant: was (0.0/8.0,1.0/8.0)
                      color = (1,1,-1,1)
                      xs = (0,0.25)
                  else:
                     #death_au: check for bass groove
                    #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnableMode == 2:
                    if self.guitars[i].isBassGuitar and self.bassgroovemult != None and multStreak >= 40 and self.bassGrooveEnabled:
                      if multStreak >= 50:
                        multiplier = 6
                        multRange = (0.25,0.5) #MFH division->constant: was (1.0/4.0,2.0/4.0)
                        color = (1,0,0.75,1)
                      else:
                        multiplier = 5
                        multRange = (0.0,0.25) #MFH division->constant: was (0.0/4.0,1.0/4.0)
                        color = (1,0,0.75,1)
                      xs = (0.75,1)
                    #death_au: end check for bass groove
                    elif multStreak >= 30:
                      multiplier = 4
                      multRange = (0.375,0.5) #MFH division->constant: was (3.0/8.0,4.0/8.0)
                      color = (1,-1,1,1)
                    elif multStreak >= 20:
                      multiplier = 3
                      multRange = (0.25,0.375) #MFH division->constant: was (2.0/8.0,3.0/8.0)
                      color = (-1,1,-.75,1)
                    elif multStreak >= 10:
                      multiplier = 2
                      multRange = (0.125,0.25) #MFH division->constant: was (1.0/8.0,2.0/8.0)
                      color = (1,1,-1,1)
                    else:
                      multiplier = 1
                      multRange = (0.0,0.125) #MFH division->constant: was (0.0/8.0,1.0/8.0)
                      color = (1,1,-1,1)
            
              
              #myfingershurt: GH bass groove multiplier: 
              # death_au: added drawing of bassgroovemult image             
              #if self.playerList[i].part.text == "Bass Guitar" and multStreak >= 40 and self.bassGrooveEnableMode == 2:   #bass groove!
              if self.guitars[i].isBassGuitar and multStreak >= 40 and self.bassGrooveEnabled:   #bass groove!
                if self.bassgroovemult != None: #death_au : bassgroovemult image found, draw image
                      
                  self.engine.drawImage(self.bassgroovemult, scale = (.5,-.125), coord = (w*0.134,h*0.19 + self.hOffset[i]),
                                        rect = (0,1,multRange[0],multRange[1]))
                
                else: #death_au: bassgroovemult not found
                  #myfingershurt: Temp text bass groove multiplier:
                  glColor3f(0,0.75,1)
                  text = str(self.scoring[i].getScoreMultiplier() * self.multi[i])
                  wid, hig = font.getStringSize(text,0.00325)
                  font.render(text, (.133 - wid / 2, .566),(1, 0, 0),0.00325)     #replacing GH multiplier large text
  
  
              else:
                if self.numOfPlayers > 1:
                  multcoord = (w*0.752,h*0.397)
                else:
                  multcoord = (w*0.674,h*0.397 + self.hOffset[i])
                self.engine.drawImage(self.mult, scale = (.5,-.0625), coord = multcoord, rect = (0,1,multRange[0],multRange[1]))
  
              if multStreak == 0:
                streak = 0
                hstreak = 0
              elif multStreak - ((multiplier-1)*10) == 1:
                streak = 0
                hstreak = 1  
              elif multStreak - ((multiplier-1)*10) == 2:
                streak = 1
                hstreak = 0
              elif multStreak - ((multiplier-1)*10) == 3:
                streak = 1
                hstreak = 1
              elif multStreak - ((multiplier-1)*10) == 4:
                streak = 2
                hstreak = 0
              elif multStreak - ((multiplier-1)*10) == 5:
                streak = 2
                hstreak = 1
              elif multStreak - ((multiplier-1)*10) == 6:
                streak = 3
                hstreak = 0
              elif multStreak - ((multiplier-1)*10) == 7:
                streak = 3
                hstreak = 1
              elif multStreak - ((multiplier-1)*10) == 8:
                streak = 4
                hstreak = 0
              elif multStreak - ((multiplier-1)*10) == 9:
                streak = 4
                hstreak = 1
              else:
                streak = 5
                hstreak = 0
    
              r = self.dots
    
              s = 0
              hs = 0
              for t in range(0,5):
                if s < streak:
                  ys = (0.66666667,1.0)  #MFH division->constant: was (2.0/3.0,1.0)
                  s += 1
                elif hs < hstreak:
                  ys = (0.33333333,0.66666667)  #MFH division->constant: was (1.0/3.0,2.0/3.0)
                  hs += 1
                else:
                  ys = (0.0,0.33333333)  #MFH division->constant: was (0.0,1.0/3.0)
                  

                if self.halfDots:
                  if self.numOfPlayers > 1:
                    rcoord = transform.translate(w*.777+t*(w*-.0129),h*.256+t*(h*.026))
                  else:
                    rcoord = (w*.701+t*(w*-.0106),h*.256+t*(h*.026))
                  self.engine.drawImage(r, scale = (0.125,-.166666667), coord = rcoord,
                                        rect = (xs[0],xs[1],ys[0],ys[1]))
                else:
                  self.engine.drawImage(r, scale = (.5,-.166666667), coord = (w*.044,h*.12+t*(h*.034) + self.hOffset[i]),
                                        color = color, rect = (0.0,1.0,ys[0],ys[1]))
  
    
              if self.x1[i] == 0: #QQstarS:Set [0] to [i]
                self.x1[i] = .14
                self.y1[i] = .4
                self.x2[i] = .14
                self.y2[i] = .4
                self.x3[i] = .14
                self.y3[i] = .4
  
  
              if self.starfx: #blazingamer, corrected by myfingershurt, adjusted by worldrave
                if self.guitars[i].starPower >= 50 or self.guitars[i].starPowerActive:
                  if self.x1[i] < 0.141:
                    self.x1[i] += 0.01
                    if self.x1[i] > 0.141:
                      self.x1[i] = 0.141
                  if self.y1[i] < 0.544:
                    self.y1[i] += 0.01
                    if self.y1[i] > 0.544:
                      self.y1[i] = 0.544
                  if self.x2[i] < 0.176:
                    self.x2[i] += 0.01
                    if self.x2[i] > 0.176:
                      self.x2[i] = 0.176
                  if self.y2[i] < 0.527:
                    self.y2[i] += 0.01
                    if self.y2[i] > 0.527:
                      self.y2[i] = 0.527
                  if self.x3[i] < 0.202:
                    self.x3[i] += 0.01
                    if self.x3[i] > 0.202:
                      self.x3[i] = 0.202
                  if self.y3[i] < 0.491:
                    self.y3[i] += 0.01
                    if self.y3[i] > 0.491:
                      self.y3[i] = 0.491
                else:
                  if self.x1[i] > 0.14:
                    self.x1[i] -= 0.01
                  if self.y1[i] > 0.4:
                    self.y1[i] -= 0.01
                  if self.x2[i] > 0.14:
                    self.x2[i] -= 0.01
                  if self.y2[i] > 0.4:
                    self.y2[i] -= 0.01
                  if self.x3[i] > 0.14:
                    self.x3[i] -= 0.01
                  if self.y3[i] > 0.4:
                    self.y3[i] -= 0.01
      
                if self.guitars[i].starPower >= 50 or self.guitars[i].starPowerActive: #QQstarS:Set [0] to [i]
                  lightPos = (0.689655172,1)  #MFH division->constant: was (2.0/2.9,1)
                else:
                  lightPos = (1.0/2.9,2.0/3.1)  #MFH division->constant: ok any preprocessor worth it's salt would take care of this before runtime... this is pointless.
      
                if self.guitars[i].starPower >= 16.6: #QQstarS:Set [0] to [i]
                  lightVis = 1
                else:
                  lightVis = self.guitars[i].starPower/16.6
    
                wfactor = self.SP.widthf(pixelw = 23.000) #Worldrave Change - Bulb 1
                spscale = (wfactor,-wfactor*3)
                
                sprot = .87
                
                self.engine.drawImage(self.SP, scale = spscale, coord = (w*.036,h*.487 + self.hOffset[i]), rot = sprot,
                                      rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.engine.drawImage(self.SP, scale = spscale, coord = (w*.036,h*.487 + self.hOffset[i]), rot = sprot,
                                      rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
                
      
                if self.guitars[i].starPower >= 33.2: #QQstarS:Set [0] to [i]
                  lightVis = 1
                else:
                  lightVis = (self.guitars[i].starPower-16.6)/16.6

                sprot = .58
                
                self.engine.drawImage(self.SP, scale = spscale, coord = (w*.059,h*.515 + self.hOffset[i]), rot = sprot,
                                      rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.engine.drawImage(self.SP, scale = spscale, coord = (w*.059,h*.515 + self.hOffset[i]), rot = sprot,
                                      rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
      
                if self.guitars[i].starPower >= 49.8:
                  lightVis = 1
                else:
                  lightVis = (self.guitars[i].starPower-32.2)/16.6

                sprot = .37
                
                self.engine.drawImage(self.SP, scale = spscale, coord = (w*.086,h*.532 + self.hOffset[i]), rot = sprot,
                                      rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.engine.drawImage(self.SP, scale = spscale, coord = (w*.086,h*.532 + self.hOffset[i]), rot = sprot,
                                      rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
                
                if self.guitars[i].starPower >= 66.4:
                  lightVis = 1
                else:
                  lightVis = (self.guitars[i].starPower-49.8)/16.6

                wfactor = self.SP.widthf(pixelw = 32.000)
                sprot = .0

                self.engine.drawImage(self.SP, scale = spscale, coord = (w*self.x1[i]*0.96652469,h*self.y1[i]*1.011455279 + self.hOffset[i]), rot = sprot,
                                      rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.engine.drawImage(self.SP, scale = spscale, coord = (w*self.x1[i]*0.96652469,h*self.y1[i]*1.011455279 + self.hOffset[i]), rot = sprot,
                                      rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
      
                if self.guitars[i].starPower >= 83:
                  lightVis = 1
                else:
                  lightVis = (self.guitars[i].starPower-66.4)/16.6
    
                sprot = -.40
                self.engine.drawImage(self.SP, scale = spscale, coord = (w*self.x2[i]*0.976698075,h*self.y2[i]*1.02813143 + self.hOffset[i]), rot = sprot,
                                      rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.engine.drawImage(self.SP, scale = spscale, coord = (w*self.x2[i]*0.976698075,h*self.y2[i]*1.02813143 + self.hOffset[i]), rot = sprot,
                                      rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
      
                if self.guitars[i].starPower >= 100:
                  lightVis = 1
                else:
                  lightVis = (self.guitars[i].starPower-83)/16.6
    
                wfactor = self.SP.widthf(pixelw = 32.000) #Worldrave Change - Bulb 6
                sprot = -.75
                self.engine.drawImage(self.SP, scale = spscale, coord = (w*self.x3[i]*0.986664588,h*self.y3[i]*1.04973235 + self.hOffset[i]), rot = sprot,
                                      rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.engine.drawImage(self.SP, scale = spscale, coord = (w*self.x3[i]*0.986664588,h*self.y3[i]*1.04973235 + self.hOffset[i]), rot = sprot,
                                      rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
                
              self.engine.drawImage(self.rockmeter, scale = (.5,-.5), coord = (w*.134, h*.23 + self.hOffset[i]))
                  
              if (self.coOp and i == self.coOpPlayerMeter) or not self.coOp:  #MFH only render for player 1 if co-op mode

                if self.coOp:
                  score=self.coOpScoreCard.score
                  for playaNum, playa in enumerate(self.playerList):
                    score += self.getExtraScoreForCurrentlyPlayedNotes(playaNum)
                else:
                  score=self.scoring[i].score
                  score += self.getExtraScoreForCurrentlyPlayedNotes(i)

                size      = scoreFont.getStringSize(str(score))
                x = 0.19-size[0]
                # evilynux - Changed upon worldrave's request
                c1,c2,c3 = self.rockmeter_score_color
                glColor3f(c1,c2,c3)
                scoreFont.render("%d" % (score),  (x, 0.507+self.hFontOffset[i]))
    
              #MFH - rock measurement tristate
              if self.rock[i] > self.rockHiThreshold:
                rock = self.rockHi
              elif self.rock[i] > self.rockMedThreshold:
                rock = self.rockMed
              else:
                rock = self.rockLo
    
              rockx = .13
              rocky = .426
              if self.failingEnabled:
                self.engine.drawImage(rock, scale = (.5,-.5), coord = (w*rockx,h*rocky + self.hOffset[i]))
              else:
                self.engine.drawImage(self.rockOff, scale = (.5,-.5), coord = (w*rockx,h*rocky + self.hOffset[i]))
    
              currentRock = (0.0 + self.rock[i]) / (self.rockMax)
              if self.rock[i] >= 0:
                self.arrowRotation[i] += ( 0.0 + currentRock - self.arrowRotation[i]) / 5.0
              else:  #QQstarS: Fix the arrow let him never rotation to bottom
                self.arrowRotation[i] = self.arrowRotation[i]
              angle = -(.460 / 2) * math.pi + .460 * math.pi * self.arrowRotation[i]
              wfactor = self.arrow.widthf(pixelw = 60.000)
  
              if self.failingEnabled:
                self.engine.drawImage(self.arrow, scale = (wfactor,-wfactor), coord = (w*rockx,h*(rocky-.056 + self.hOffset[i])), rot = -angle)
    
              self.engine.drawImage(self.rockTop, scale = (.5,-.5), coord = (w*rockx,h*rocky + self.hOffset[i]))
    

              glColor4f(.85,.47,0,1)
              streak = multStreak
              text = str(streak)
              size = streakFont.getStringSize(text)
              streakFont.render(text, (.193-size[0], 0.548+self.hFontOffset[i]))
    
              if not self.pause and not self.failed and not self.ending:
                if self.displayText[i] != None:
                  glColor3f(.8,.75,.01)
                  size = sphraseFont.getStringSize(self.displayText[i], scale = self.displayTextScale[i])
                  sphraseFont.render(self.displayText[i], (.5-size[0]/2,self.textY[i]-size[1]), scale = self.displayTextScale[i])
    
              if self.youRock == True:
                if self.rockTimer == 1:
                  #self.sfxChannel.setVolume(self.sfxVolume)
                  self.engine.data.rockSound.play()
                if self.rockTimer < self.rockCountdown:
                  self.rockTimer += 1
                  self.engine.drawImage(self.rockMsg, scale = (0.5, -0.5), coord = (w/2,h/2))
                if self.rockTimer >= self.rockCountdown:
                  self.rockFinished = True
    
              if self.failed:
                if self.failTimer == 0:
                  self.song.pause()
                if self.failTimer == 1:
                  #self.sfxChannel.setVolume(self.sfxVolume)
                  self.engine.data.failSound.play()
                if self.failTimer < 100:
                  self.failTimer += 1
                  self.engine.drawImage(self.failMsg, scale = (0.5, -0.5), coord = (w/2,h/2))
                else:
                  self.finalFailed = True
                
            
              if self.pause:
                self.engine.view.setViewport(1,0)
                self.engine.drawImage(self.pauseScreen, scale = (self.pause_bkg[2], -self.pause_bkg[3]), coord = (w*self.pause_bkg[0],h*self.pause_bkg[1]), stretched = 3)
                
              if self.finalFailed and self.song:
                self.engine.view.setViewport(1,0)
                self.engine.drawImage(self.failScreen, scale = (self.fail_bkg[2], -self.fail_bkg[3]), coord = (w*self.fail_bkg[0],h*self.fail_bkg[1]), stretched = 3)
    
                # evilynux - Closer to actual GH3
                font = self.engine.data.pauseFont
                text = Dialogs.removeSongOrderPrefixFromName(self.song.info.name).upper()
                scale = font.scaleText(text, maxwidth = 0.398, scale = 0.0038)
                size = font.getStringSize(text, scale = scale)
                font.render(text, (.5-size[0]/2.0,.37-size[1]), scale = scale)
  
                #now = self.getSongPosition()
  
                diff = str(self.playerList[0].difficulty)
                # compute initial position
                pctComplete = min(100, int(now/self.lastEvent*100))
                
                curxpos = font.getStringSize(_("COMPLETED")+" ", scale = 0.0015)[0]
                curxpos += font.getStringSize(str(pctComplete), scale = 0.003)[0]
                curxpos += font.getStringSize( _(" % ON "), scale = 0.0015)[0]
                curxpos += font.getStringSize(diff, scale = 0.003)[0]
                curxpos = .5-curxpos/2.0
                c1,c2,c3 = self.fail_completed_color
                glColor3f(c1,c2,c3)              
  
                # now render
                text = _("COMPLETED") + " "
                size = font.getStringSize(text, scale = 0.0015)
                # evilynux - Again, for this very font, the "real" height value is 75% of returned value
                font.render(text, (curxpos, .37+(font.getStringSize(text, scale = 0.003)[1]-size[1])*.75), scale = 0.0015)
                text = str(pctComplete)
                curxpos += size[0]
  
                size = font.getStringSize(text, scale = 0.003)
                font.render(text, (curxpos, .37), scale = 0.003)
                text = _(" % ON ")
                curxpos += size[0]
                size = font.getStringSize(text, scale = 0.0015)
                font.render(text, (curxpos, .37+(font.getStringSize(text, scale = 0.003)[1]-size[1])*.75), scale = 0.0015)
                text = diff
                curxpos += size[0]
                font.render(text, (curxpos, .37), scale = 0.003)
  
                if not self.failEnd:
                  self.failGame()
  
              if self.hopoIndicatorEnabled and not self.guitars[i].isDrum and not self.pause and not self.failed: #MFH - HOPO indicator (grey = strums required, white = strums not required)
                text = _("HOPO")
                if self.guitars[i].hopoActive > 0:
                  glColor3f(1.0, 1.0, 1.0)  #white
                else:
                  glColor3f(0.4, 0.4, 0.4)  #grey
                w, h = font.getStringSize(text,0.00150)
                font.render(text, (.950 - w / 2, .710),(1, 0, 0),0.00150)     #off to the right slightly above fretboard
                glColor3f(1, 1, 1)  #cracker white
  
          #MFH - new location for star system support - outside theme-specific logic:

          #if (self.coOp and i == 0) or not self.coOp:  #MFH only render for player 0 if co-op mode
          if (self.coOp and i == self.coOpPlayerMeter) or ((self.coOpRB or self.coOpGH) and i == 0) or not self.coOpType:  #MFH only render for player 1 if co-op mode

            if self.coOpType:
              stars=self.coOpScoreCard.stars
              partialStars=self.coOpScoreCard.partialStars
              self.engine.view.setViewport(1,0)
              ratio=self.coOpScoreCard.starRatio
            else:
              stars=self.scoring[i].stars
              partialStars=self.scoring[i].partialStars
              ratio=self.scoring[i].starRatio

            w = wBak
            h = hBak
            if (self.inGameStars == 2 or (self.inGameStars == 1 and self.theme == 2) )  and not self.pause and not self.failed: #MFH - only show stars if in-game stars enabled
              if self.starGrey != None:
                for starNum in range(0, 5):
                  if stars == 7:    #full combo!
                    self.engine.drawImage(self.starFC, scale = (.080,-.080), coord = (w*(0.802 + 0.040*(starNum)),h*0.7160))
                  elif stars == 6:    #perfect!
                    self.engine.drawImage(self.starPerfect, scale = (.080,-.080), coord = (w*(0.802 + 0.040*(starNum)),h*0.7160))
                  elif starNum == stars:
                    if self.starContinuousAvailable:
                      #stump: continuous fillup (akedrou - the ratio will pass correctly from rewritten star score)
                      degrees = int(360*ratio) - (int(360*ratio) % 5)
                      self.engine.drawImage(self.starGrey, scale = (.080,-.080), coord = (w*(0.802 + 0.040*(starNum)),h*0.7160))
                      self.engine.drawImage(self.drawnOverlays[degrees], scale = (.080,-.080), coord = (w*(0.802 + 0.040*(starNum)),h*0.7160))
                    #if self.starGrey1 and self.starScoring == 2:  #if more complex star system is enabled, and we're using Rock Band style scoring
                    elif self.starGrey1:
                      if partialStars == 0:
                        self.engine.drawImage(self.starGrey, scale = (.080,-.080), coord = (w*(0.802 + 0.040*(starNum)),h*0.7160))
                      elif partialStars == 1:
                        self.engine.drawImage(self.starGrey1, scale = (.080,-.080), coord = (w*(0.802 + 0.040*(starNum)),h*0.7160))
                      elif partialStars == 2:
                        self.engine.drawImage(self.starGrey2, scale = (.080,-.080), coord = (w*(0.802 + 0.040*(starNum)),h*0.7160))
                      elif partialStars == 3:
                        self.engine.drawImage(self.starGrey3, scale = (.080,-.080), coord = (w*(0.802 + 0.040*(starNum)),h*0.7160))
                      elif partialStars == 4:
                        self.engine.drawImage(self.starGrey4, scale = (.080,-.080), coord = (w*(0.802 + 0.040*(starNum)),h*0.7160))
                      elif partialStars == 5:
                        self.engine.drawImage(self.starGrey5, scale = (.080,-.080), coord = (w*(0.802 + 0.040*(starNum)),h*0.7160))
                      elif partialStars == 6:
                        self.engine.drawImage(self.starGrey6, scale = (.080,-.080), coord = (w*(0.802 + 0.040*(starNum)),h*0.7160))
                      elif partialStars == 7:
                        self.engine.drawImage(self.starGrey7, scale = (.080,-.080), coord = (w*(0.802 + 0.040*(starNum)),h*0.7160))
                      
                    else:
                      self.engine.drawImage(self.starGrey, scale = (.080,-.080), coord = (w*(0.802 + 0.040*(starNum)),h*0.7160))
    
                  elif starNum > stars:
                    if self.displayAllGreyStars:
                      self.engine.drawImage(self.starGrey, scale = (.080,-.080), coord = (w*(0.802 + 0.040*(starNum)),h*0.7160))
    
                  else:   #white star
                    self.engine.drawImage(self.starWhite, scale = (.080,-.080), coord = (w*(0.802 + 0.040*(starNum)),h*0.7160))
  
          if self.song and self.song.readyToGo:
    
            if not self.coOpRB and not self.coOpGH:
              self.engine.view.setViewportHalf(self.numOfPlayers,i)

            #MFH: Realtime hit accuracy display:
            
            #if ((self.inGameStats == 2 or (self.inGameStats == 1 and self.theme == 2)) and (not self.pause and not self.failed)) and ( (not self.pause and not self.failed) or self.hopoDebugDisp == 1 ):
            if ((self.inGameStats == 2 or (self.inGameStats == 1 and self.theme == 2) or self.hopoDebugDisp == 1 ) and (not self.pause and not self.failed) and not (self.coOpType and not i==0 and not self.coOp)):
              #will not show on pause screen, unless HOPO debug is on (for debugging)
              if self.coOpRB or self.coOpGH:
                sNotesHit   = self.coOpScoreCard.notesHit
                sTotalNotes = self.coOpScoreCard.totalStreakNotes
                sHitAcc = self.coOpScoreCard.hitAccuracy
                sAvMult = self.coOpScoreCard.avMult
                sEfHand = self.coOpScoreCard.handicapValue
              else:
                sNotesHit   = self.scoring[i].notesHit
                sTotalNotes = self.scoring[i].totalStreakNotes
                sHitAcc = self.scoring[i].hitAccuracy
                sAvMult = self.scoring[i].avMult
                sEfHand = self.scoring[i].handicapValue
              trimmedTotalNoteAcc = self.decimal(str(sHitAcc)).quantize(self.decPlaceOffset)
              #text = str(self.playerList[i].notesHit) + "/" + str(self.playerList[i].totalStreakNotes) + ": " + str(trimmedTotalNoteAcc) + "%"
              text = "%(notesHit)s/%(totalNotes)s: %(hitAcc)s%%" % \
                {'notesHit': str(sNotesHit), 'totalNotes': str(sTotalNotes), 'hitAcc': str(trimmedTotalNoteAcc)}
              c1,c2,c3 = self.ingame_stats_color
              glColor3f(c1, c2, c3)  #wht
              w, h = font.getStringSize(text,0.00160)
              if self.theme == 2:
                if self.numDecimalPlaces < 2:
                  accDispX = 0.755
                else:
                  accDispX = 0.740  #last change -0.015
                accDispYac = 0.147
                accDispYam = 0.170
              else:
                accDispX = 0.890      #last change -0.010
                accDispYac = 0.140
                accDispYam = 0.164
              font.render(text, (accDispX - w/2, accDispYac),(1, 0, 0),0.00140)     #top-centered by streak under score
              trimmedAvMult = self.decimal(str(sAvMult)).quantize(self.decPlaceOffset)
              #text = _("Avg: ") + str(trimmedAvMult) + "x"

              #avgLabel = _("Avg")
              text = "%(avLab)s: %(avMult)sx" % \
                {'avLab': self.tsAvgLabel, 'avMult': str(trimmedAvMult)}
              glColor3f(c1, c2, c3)
              w, h = font.getStringSize(text,0.00160)
              font.render(text, (accDispX - w/2, accDispYam),(1, 0, 0),0.00140)     #top-centered by streak under score
              
              if sEfHand != 100.0:
                text = "%s: %.1f%%" % (self.tsHandicapLabel, sEfHand)
                w, h = font.getStringSize(text, .00160)
                font.render(text, (.98 - w, .246), (1, 0, 0),0.00140)
            
            if self.coOpRB or self.coOpGH:
              self.engine.view.setViewportHalf(self.numOfPlayers,i)
            
            if self.dispSoloReview[i] and not self.pause and not self.failed:
              if self.soloReviewCountdown[i] < self.soloReviewDispDelay:
                self.soloReviewCountdown[i] += 1
                if not (self.guitars[i].freestyleActive or self.scoring[i].freestyleWasJustActive):
                  #glColor3f(0, 0.85, 1)  #grn-blu
                  glColor3f(1, 1, 1)  #cracker white
                  text1 = self.soloReviewText[i][0]
                  text2 = self.soloReviewText[i][1]
                  xOffset = 0.950
                  if self.hitAccuracyPos == 0: #Center - need to move solo review above this!
                    yOffset = 0.080
                  elif self.jurgPlayer[i] and self.autoPlay:
                    yOffset = 0.115    #above Jurgen Is Here
                  else:   #no jurgens here:
                    yOffset = 0.155   #was 0.180, occluded notes
                  txtSize = 0.00185
                  Tw, Th = self.solo_soloFont.getStringSize(text1,txtSize)
                  Tw2, Th2 = self.solo_soloFont.getStringSize(text2,txtSize)
  
                  #MFH - scale and display self.soloFrame behind / around the text
                  lineSpacing = self.solo_soloFont.getLineSpacing(txtSize)
                  if self.soloFrame:
                    frameWidth = (max(Tw,Tw2))*1.15
                    #frameHeight = (Th+Th2)*1.10
                    frameHeight = lineSpacing*2.05
                    boxXOffset = 0.5
                    boxYOffset = self.hPlayer[i]-(self.hPlayer[i]* ((yOffset + lineSpacing) / self.fontScreenBottom) )
                    
                    tempWScale = frameWidth*self.soloFrameWFactor
                    tempHScale = -(frameHeight)*self.soloFrameWFactor

                    self.engine.drawImage(self.soloFrame, scale = (tempWScale,tempHScale), coord = (self.wPlayer[i]*boxXOffset,boxYOffset))
                    #self.soloFrame.transform.reset()
                    #self.soloFrame.transform.scale(tempWScale,tempHScale)
                    #self.soloFrame.transform.translate(self.wPlayer[i]*boxXOffset,boxYOffset)
                    #self.soloFrame.draw()

  
                  self.solo_soloFont.render(text1, (0.5 - Tw/2, yOffset),(1, 0, 0),txtSize)   #centered
                  self.solo_soloFont.render(text2, (0.5 - Tw2/2, yOffset+lineSpacing),(1, 0, 0),txtSize)   #centered
              else:
                self.dispSoloReview[i] = False 
              
              
              
            if self.hopoDebugDisp == 1 and not self.pause and not self.failed and not self.guitars[i].isDrum:
              #MFH: PlayedNote HOPO tappable marking
              if self.guitars[i].playedNotes:
                
               
                if len(self.guitars[i].playedNotes) > 1:
                  self.lastTapText = "tapp: %d, %d" % (self.guitars[i].playedNotes[0][1].tappable, self.guitars[i].playedNotes[1][1].tappable)
                else:
                  self.lastTapText = "tapp: %d" % (self.guitars[i].playedNotes[0][1].tappable)

                #self.lastTapText = "tapp: " + str(self.guitars[i].playedNotes[0][1].tappable)
                #if len(self.guitars[i].playedNotes) > 1:
                # self.lastTapText += ", " + str(self.guitars[i].playedNotes[1][1].tappable)
                 
                 
              w, h = font.getStringSize(self.lastTapText,0.00170)
              font.render(self.lastTapText, (.750 - w / 2, .440),(1, 0, 0),0.00170)     #off to the right slightly above fretboard
              
              #MFH: HOPO active debug
              #text = "HOact: "
              if self.guitars[i].hopoActive > 0:
                glColor3f(1, 1, 0)  #yel
                #text += "+"
                hoActDisp = "+"
              elif self.guitars[i].hopoActive < 0:
                glColor3f(0, 1, 1)  #blu-grn
                #text += "-"
                hoActDisp = "-"
              else:
                glColor3f(0.5, 0.5, 0.5)  #gry
                #text += "0"
                hoActDisp = "0"
              text = "HOact: %s" % hoActDisp              
              w, h = font.getStringSize(text,0.00175)
              font.render(text, (.750 - w / 2, .410),(1, 0, 0),0.00170)     #off to the right slightly above fretboard
              glColor3f(1, 1, 1)  #whitey
              
              
              #MFH: HOPO intention determination flag debug
              if self.guitars[i].sameNoteHopoString:
                glColor3f(1, 1, 0)  #yel
              else:
                glColor3f(0.5, 0.5, 0.5)  #gry
            
              #text = "HOflag: " + str(self.guitars[i].sameNoteHopoString)
              text = "HOflag: %s" % str(self.guitars[i].sameNoteHopoString)
            
              w, h = font.getStringSize(text,0.00175)
              font.render(text, (.750 - w / 2, .385),(1, 0, 0),0.00170)     #off to the right slightly above fretboard
              glColor3f(1, 1, 1)  #whitey
              
              ##MFH: HOPO intention determination flag problematic note list debug
              ##glColor3f(1, 1, 1)  #whitey
              #text = "pNotes: " + str(self.problemNotesP1)
              #w, h = font.getStringSize(text,0.00175)
              #font.render(text, (.750 - w / 2, .355),(1, 0, 0),0.00170)     #off to the right slightly above fretboard
              ##glColor3f(1, 1, 1)  #whitey
              
              
              
              #MFH: guitarSoloNoteCount list debug
              text = str(self.guitarSolos[i])
              glColor3f(0.9, 0.9, 0.9)  #offwhite
              w, h = font.getStringSize(text,0.00110)
              font.render(text, (.900 - w / 2, .540),(1, 0, 0),0.00110)     #off to the right slightly above fretboard
    
      
            if self.killDebugEnabled and not self.pause and not self.failed:
              killXpos = 0.760    #last change: +0.010
              killYpos = 0.365    #last change: -0.010
              killTsize = 0.00160  #last change:  -0.00010
              
              #if self.playerList[i].part.text != "Drums":
              if not self.guitars[i].isDrum:
                if self.isKillAnalog[i]:
                  
                  if self.analogKillMode[i] == 2: #xbox mode:
                    if self.actualWhammyVol[i] < 1.0:
                      glColor3f(1, 1, 0)  #yel
                    else:
                      glColor3f(0.5, 0.5, 0.5)  #gry
                  else: #ps2 mode:
                    if self.actualWhammyVol[i] > 0.0:
                      glColor3f(1, 1, 0)  #yel
                    else:
                      glColor3f(0.5, 0.5, 0.5)  #gry
                  text = str(self.decimal(str(self.actualWhammyVol[i])).quantize(self.decPlaceOffset))
                  w, h = font.getStringSize(text,killTsize)
                  font.render(text, (killXpos - w / 2, killYpos),(1, 0, 0),killTsize)     #off to the right slightly above fretboard
                else:
                  if self.killswitchEngaged[i]:
                    glColor3f(1, 1, 0)  #yel
                  else:
                    glColor3f(0.5, 0.5, 0.5)  #gry
                  text = str(self.killswitchEngaged[i])
                  w, h = font.getStringSize(text,killTsize)
                  font.render(text, (killXpos - w / 2, killYpos),(1, 0, 0),killTsize)     #off to the right slightly above fretboard
            glColor3f(1, 1, 1)  #whitey reset (cracka cracka)

            #MFH - TODO - freestyle active status debug display
            if self.showFreestyleActive == 1 and not self.pause and not self.failed:    #MFH - shows when freestyle is active
              if self.guitars[i].isDrum:    #also show the active status of drum fills
                text = "BRE: %s, Fill: %s" % ( str(self.guitars[i].freestyleActive), str(self.guitars[i].drumFillsActive) )
              else:
                text = "BRE: %s" % str(self.guitars[i].freestyleActive)
              freeX = .685
              freeY = .510
              freeTsize = 0.00150
              font.render(text, (freeX, freeY),(1, 0, 0),freeTsize)
    
            #myfingershurt: lyrical display conditional logic:
            # show the comments (lyrics)
    
            #myfingershurt: first display the accuracy readout:
            if self.dispAccuracy[i] and not self.pause and not self.failed:
  
              trimmedAccuracy = self.decimal(str(self.accuracy[i])).quantize(self.decPlaceOffset)
    
            
              if self.showAccuracy == 1:    #numeric mode
                
                #MFH string concatenation -> modulo formatting
                #text = str(trimmedAccuracy) + " ms"
                text = "%s %s" % (str(trimmedAccuracy), self.msLabel)

              elif self.showAccuracy >= 2:    #friendly / descriptive mode
    
                #MFH Precalculated these hit accuracy thresholds instead of every frame
                if (self.accuracy[i] >= self.guitars[i].accThresholdWorstLate) and (self.accuracy[i] < self.guitars[i].accThresholdVeryLate):
                  text = self.tsAccVeryLate
                  glColor3f(1, 0, 0)
                elif (self.accuracy[i] >= self.guitars[i].accThresholdVeryLate) and (self.accuracy[i] < self.guitars[i].accThresholdLate):
                  text = self.tsAccLate
                  glColor3f(1, 1, 0)
                elif (self.accuracy[i] >= self.guitars[i].accThresholdLate) and (self.accuracy[i] < self.guitars[i].accThresholdSlightlyLate):
                  text = self.tsAccSlightlyLate
                  glColor3f(1, 1, 0)
                elif (self.accuracy[i] >= self.guitars[i].accThresholdSlightlyLate) and (self.accuracy[i] < self.guitars[i].accThresholdExcellentLate):
                  text = self.tsAccExcellentLate
                  glColor3f(0, 1, 0)
                elif (self.accuracy[i] >= self.guitars[i].accThresholdExcellentLate) and (self.accuracy[i] < self.guitars[i].accThresholdPerfect):
                  #give the "perfect" reading some slack, -1.0 to 1.0
                  text = self.tsAccPerfect
                  glColor3f(0, 1, 1) #changed color
                elif (self.accuracy[i] >= self.guitars[i].accThresholdPerfect) and (self.accuracy[i] < self.guitars[i].accThresholdExcellentEarly):
                  text = self.tsAccExcellentEarly
                  glColor3f(0, 1, 0)
                elif (self.accuracy[i] >= self.guitars[i].accThresholdExcellentEarly) and (self.accuracy[i] < self.guitars[i].accThresholdSlightlyEarly):
                  text = self.tsAccSlightlyEarly
                  glColor3f(1, 1, 0)
                elif (self.accuracy[i] >= self.guitars[i].accThresholdSlightlyEarly) and (self.accuracy[i] < self.guitars[i].accThresholdEarly):
                  text = self.tsAccEarly
                  glColor3f(1, 1, 0)
                elif (self.accuracy[i] >= self.guitars[i].accThresholdEarly) and (self.accuracy[i] < self.guitars[i].accThresholdVeryEarly):
                  text = self.tsAccVeryEarly
                  glColor3f(1, 0, 0)
                else:
                  #bug catch - show the problematic number:            
                  #text = str(trimmedAccuracy) + _(" ms")
                  text = "%(acc)s %(ms)s" % \
                    {'acc': str(trimmedAccuracy), 'ms': self.msLabel}
                  glColor3f(1, 0, 0)
    
              w, h = font.getStringSize(text,0.00175)
    
              posX = 0.98 - (w / 2)
              if self.theme == 2:
                posY = 0.284
              else:
                if self.coOpGH:
                  posY = 0.25
                else:
                  posY = 0.296
    
              if self.hitAccuracyPos == 0: #Center
                posX = .500
                posY = .305 + h
                if self.showAccuracy == 3:    #for displaying numerical below descriptive
                  posY = .305
                #if self.pov != 1: #not GH POV
                #  posY = y + 4 * h   -- MFH: this line causes a bad hang.
              elif self.hitAccuracyPos == 2:#Left-bottom
                posX = .193
                posY = .700  #(.193-size[0]/2, 0.667-size[1]/2+self.hFontOffset[i]))
              elif self.hitAccuracyPos == 3: #Center-bottom
                posX = .500
                posY = .710
    
    
              font.render(text, (posX - w / 2, posY - h / 2),(1, 0, 0),0.00170)    

    
              if self.showAccuracy == 3:    #for displaying numerical below descriptive
                #text = str(self.accuracy)
                #text = str(trimmedAccuracy) + " ms"
                #msText = _("ms")
                text = "%(acc)s %(ms)s" % \
                  {'acc': str(trimmedAccuracy), 'ms': self.msLabel}
                w, h = font.getStringSize(text,0.00140)
                font.render(text, (posX - w / 2, posY - h / 2 + .030),(1, 0, 0),0.00140) 
                  
    
            glColor3f(1, 1, 1)
            

            #handle the guitar solo track
            #if (self.readTextAndLyricEvents == 2 or (self.readTextAndLyricEvents == 1 and self.theme == 2)) and (not self.pause and not self.failed and not self.ending):
            if (not self.pause and not self.failed and not self.ending):

              #MFH - only use the TK_GUITAR_SOLOS track if at least one player has no MIDI solos marked:
              if self.guitars[i].useMidiSoloMarkers:   #mark using the new MIDI solo marking system
                for time, event in self.song.midiEventTrack[i].getEvents(minPos, maxPos):
                  if isinstance(event, Song.MarkerNote):
                    if (event.number == Song.starPowerMarkingNote) and (self.song.midiStyle == Song.MIDI_TYPE_RB):    #solo marker note.
                      soloChangeNow = False
                      xOffset = (time - pos) / eventWindow
                      if xOffset < lyricSlop / 16.0:   #present
                        soloChangeNow = True
                      if soloChangeNow:
                        if event.endMarker:   #solo ending
                          if self.guitars[i].guitarSolo and not event.happened:
                            self.endSolo(i)
                            event.happened = True
                        else:   #solo beginning
                          if not self.guitars[i].guitarSolo and not event.happened:
                            self.startSolo(i)
                            event.happened = True


              else:   #fall back on old guitar solo marking system
                for time, event in self.song.eventTracks[Song.TK_GUITAR_SOLOS].getEvents(minPos, maxPos):
                  #is event happening now?
                  xOffset = (time - pos) / eventWindow
                  EventHappeningNow = False
                  if xOffset < (0.0 - lyricSlop * 2.0):   #past
                    EventHappeningNow = False
                  elif xOffset < lyricSlop / 16.0:   #present
                    EventHappeningNow = True
                  if EventHappeningNow:   #process the guitar solo event
                    if event.text.find("ON") >= 0:
                      if self.guitars[i].canGuitarSolo:
                        if not self.guitars[i].guitarSolo:
                          self.startSolo(i)
                    else:
                      #if self.guitars[i].canGuitarSolo:
                      if self.guitars[i].guitarSolo:
                        self.endSolo(i)
    
    
              #MFH - render guitar solo in progress - stats
              #try:
              #if self.guitars[i].canGuitarSolo:
              if self.guitars[i].guitarSolo:

                    #MFH - scale and display self.soloFrame behind / around the solo accuracy text display

                    if self.fontMode==0:      #0 = oGL Hack, 1=LaminaScreen, 2=LaminaFrames
                      if self.soloFrame:
                        frameWidth = self.solo_Tw[i]*1.15
                        frameHeight = self.solo_Th[i]*1.07
                        self.solo_boxYOffset[i] = self.hPlayer[i]-(self.hPlayer[i]* ((self.solo_yOffset[i] + self.solo_Th[i]/2.0 ) / self.fontScreenBottom) )   
                        tempWScale = frameWidth*self.soloFrameWFactor
                        tempHScale = -(frameHeight)*self.soloFrameWFactor
                        self.engine.drawImage(self.soloFrame, scale = (tempWScale,tempHScale), coord = (self.wPlayer[i]*self.solo_boxXOffset[i],self.solo_boxYOffset[i]))
                      self.solo_soloFont.render(self.solo_soloText[i], (self.solo_xOffset[i], self.solo_yOffset[i]),(1, 0, 0),self.solo_txtSize)

                      #self.solo_soloFont.render("test", (0.5,0.0) )     #appears to render text from given position, down / right...
                      #self.solo_soloFont.render("test", (0.5,0.5) )     #this test confirms that the Y scale is in units relative to the X pixel width - 1280x960 yes but 1280x1024 NO

                      #this test locates the constant that the font rendering routine always considers the "bottom" of the screen   
                      #self.solo_soloFont.render("test", (0.5,0.75-self.solo_Th[i]), scale=self.solo_txtSize )    #ah-ha!  4:3 AR viewport = 0.75 max!


                  #self.engine.view.setViewport(1,0)
              #except Exception, e:
              #  Log.warn("Unable to render guitar solo accuracy text: %s" % e)
              if self.coOpType: #1 BRE in co-op
                scoreCard = self.coOpScoreCard
                if i == 0:
                  self.engine.view.setViewportHalf(1,0)
                  oneTime = True
                else:
                  oneTime = False
              else:
                scoreCard = self.scoring[i]
                oneTime = True
              #MFH - show BRE temp score frame
              if (self.guitars[i].freestyleActive or (scoreCard.freestyleWasJustActive and not scoreCard.endingStreakBroken and not scoreCard.endingAwarded)) and oneTime == True:
                #to render BEFORE the bonus is awarded.

                text = "End Bonus"
                yOffset = 0.110
                xOffset = 0.500
                tW, tH = self.solo_soloFont.getStringSize(text, scale = self.solo_txtSize/2.0)

                if self.breScoreFrame:
                  frameWidth = tW*1.15
                  frameHeight = tH*1.07
                  if self.coOpType:
                    boxYOffset = (1.0-((yOffset + tH/2.0 ) / self.fontScreenBottom))*self.hFull
                    boxXOffset = xOffset*self.wFull
                  else:
                    boxYOffset = self.hPlayer[i]-(self.hPlayer[i]* ((yOffset + tH/2.0 ) / self.fontScreenBottom) )   
                    boxXOffset = self.wPlayer[i]*xOffset
                  #self.breScoreFrame.transform.reset()                  
                  tempWScale = frameWidth*self.breScoreFrameWFactor
                  tempHScale = -(frameHeight)*self.breScoreFrameWFactor
                  self.engine.drawImage(self.breScoreFrame, scale = (tempWScale,tempHScale), coord = (boxXOffset,boxYOffset))
                  #self.breScoreFrame.transform.scale(tempWScale,tempHScale)
                  #self.breScoreFrame.transform.translate(self.wPlayer[i]*xOffset,boxYOffset)
                  #self.breScoreFrame.draw()

                self.solo_soloFont.render(text, (xOffset - tW/2.0, yOffset),(1, 0, 0),self.solo_txtSize/2.0)

                if self.coOpType and self.partImage:
                  freeX = .05*(self.numOfPlayers-1)
                  freeI = .05*self.numOfPlayers
                  for j in xrange(self.numOfPlayers):
                    self.engine.drawImage(self.part[j], scale = (.15,-.15), coord = (self.wFull*(.5-freeX+freeI*j),self.hFull*.58), color = (.8, .8, .8, 1))

                text = "%s" % scoreCard.endingScore
                if self.theme == 2:
                  text = text.replace("0","O")
                tW, tH = self.solo_soloFont.getStringSize(text, scale = self.solo_txtSize)
                yOffset = 0.175
                xOffset = 0.500
                

                if self.breScoreBackground:
                  #frameWidth = tW*3.0
                  frameHeight = tH*4.0
                  frameWidth = frameHeight
                  if self.coOpType:
                    boxYOffset = self.hFull*(1.0-(yOffset + tH/2.0 ) / self.fontScreenBottom)
                    boxXOffset = xOffset*self.wFull
                  else:
                    boxYOffset = self.hPlayer[i]-(self.hPlayer[i]* ((yOffset + tH/2.0 ) / self.fontScreenBottom) )   
                    boxXOffset = self.wPlayer[i]*xOffset
                  tempWScale = frameWidth*self.breScoreBackgroundWFactor
                  tempHScale = -(frameHeight)*self.breScoreBackgroundWFactor
                  self.engine.drawImage(self.breScoreBackground, scale = (tempWScale,tempHScale), coord = (boxXOffset,boxYOffset))


                if self.breScoreFrame:
                  frameWidth = tW*1.15
                  frameHeight = tH*1.07
                  if self.coOpType:
                    boxYOffset = self.hFull*(1.0-(yOffset + tH/2.0 ) / self.fontScreenBottom)
                    boxXOffset = xOffset*self.wFull
                  else:
                    boxYOffset = self.hPlayer[i]-(self.hPlayer[i]* ((yOffset + tH/2.0 ) / self.fontScreenBottom) )   
                    boxXOffset = self.wPlayer[i]*xOffset
                  tempWScale = frameWidth*self.breScoreFrameWFactor
                  tempHScale = -(frameHeight)*self.breScoreFrameWFactor
                  self.engine.drawImage(self.breScoreFrame, scale = (tempWScale,tempHScale), coord = (boxXOffset,boxYOffset))
                self.solo_soloFont.render(text, (xOffset - tW/2.0, yOffset),(1, 0, 0),self.solo_txtSize)
              
              elif scoreCard.freestyleWasJustActive and not scoreCard.endingStreakBroken and scoreCard.endingAwarded and oneTime == True:
                #MFH - TODO - ending bonus was awarded - scale up obtained score & box to signify rockage

                text = "Success!"
                yOffset = 0.110
                xOffset = 0.500
                tW, tH = self.solo_soloFont.getStringSize(text, scale = self.solo_txtSize/2.0)

                if self.breScoreFrame:
                  frameWidth = tW*1.15
                  frameHeight = tH*1.07
                  if self.coOpType:
                    boxYOffset = self.hFull*(1.0-(yOffset + tH/2.0 ) / self.fontScreenBottom)
                    boxXOffset = xOffset*self.wFull
                  else:
                    boxYOffset = self.hPlayer[i]-(self.hPlayer[i]* ((yOffset + tH/2.0 ) / self.fontScreenBottom) )   
                    boxXOffset = self.wPlayer[i]*xOffset
                  tempWScale = frameWidth*self.breScoreFrameWFactor
                  tempHScale = -(frameHeight)*self.breScoreFrameWFactor
                  self.engine.drawImage(self.breScoreFrame, scale = (tempWScale,tempHScale), coord = (boxXOffset,boxYOffset))

                self.solo_soloFont.render(text, (xOffset - tW/2.0, yOffset),(1, 0, 0),self.solo_txtSize/2.0)

                if self.coOpType and self.partImage:
                  freeX = .05*(self.numOfPlayers-1)
                  freeI = .05*self.numOfPlayers
                  for j in xrange(self.numOfPlayers):
                    self.engine.drawImage(self.part[j], scale = (.15,-.15), coord = (self.wFull*(.5-freeX+freeI*j),self.hFull*.58))

                text = "%s" % scoreCard.endingScore
                if self.theme == 2:
                  text = text.replace("0","O")
                tW, tH = self.solo_soloFont.getStringSize(text, scale = self.solo_txtSize)
                yOffset = 0.175
                xOffset = 0.500
                

                if self.breScoreBackground:
                  #frameWidth = tW*3.0
                  frameHeight = tH*4.0
                  frameWidth = frameHeight
                  if self.coOpType:
                    boxYOffset = self.hFull*(1.0-(yOffset + tH/2.0 ) / self.fontScreenBottom)
                    boxXOffset = xOffset*self.wFull
                  else:
                    boxYOffset = self.hPlayer[i]-(self.hPlayer[i]* ((yOffset + tH/2.0 ) / self.fontScreenBottom) )   
                    boxXOffset = self.wPlayer[i]*xOffset
                  tempWScale = frameWidth*self.breScoreBackgroundWFactor
                  tempHScale = -(frameHeight)*self.breScoreBackgroundWFactor
                  self.engine.drawImage(self.breScoreBackground, scale = (tempWScale,tempHScale), coord = (boxXOffset,boxYOffset))

                if self.breScoreFrame:
                  frameWidth = tW*1.15
                  frameHeight = tH*1.07
                  if self.coOpType:
                    boxYOffset = self.hFull*(1.0-(yOffset + tH/2.0 ) / self.fontScreenBottom)
                    boxXOffset = xOffset*self.wFull
                  else:
                    boxYOffset = self.hPlayer[i]-(self.hPlayer[i]* ((yOffset + tH/2.0 ) / self.fontScreenBottom) )   
                    boxXOffset = self.wPlayer[i]*xOffset
                  tempWScale = frameWidth*self.breScoreFrameWFactor
                  tempHScale = -(frameHeight)*self.breScoreFrameWFactor
                  self.engine.drawImage(self.breScoreFrame, scale = (tempWScale,tempHScale), coord = (boxXOffset,boxYOffset))
                self.solo_soloFont.render(text, (xOffset - tW/2.0, yOffset),(1, 0, 0),self.solo_txtSize)
              
              elif scoreCard.freestyleWasJustActive and scoreCard.endingStreakBroken and oneTime == True:
                #akedrou - ending bonus was not awarded - scale up to signify failure

                text = "Failed!"
                yOffset = 0.110
                xOffset = 0.500
                tW, tH = self.solo_soloFont.getStringSize(text, scale = self.solo_txtSize/2.0)

                if self.breScoreFrame:
                  frameWidth = tW*1.15
                  frameHeight = tH*1.07
                  if self.coOpType:
                    boxYOffset = self.hFull*(1.0-(yOffset + tH/2.0 ) / self.fontScreenBottom)
                    boxXOffset = xOffset*self.wFull
                  else:
                    boxYOffset = self.hPlayer[i]-(self.hPlayer[i]* ((yOffset + tH/2.0 ) / self.fontScreenBottom) )   
                    boxXOffset = self.wPlayer[i]*xOffset
                  tempWScale = frameWidth*self.breScoreFrameWFactor
                  tempHScale = -(frameHeight)*self.breScoreFrameWFactor
                  self.engine.drawImage(self.breScoreFrame, scale = (tempWScale,tempHScale), coord = (boxXOffset,boxYOffset))

                self.solo_soloFont.render(text, (xOffset - tW/2.0, yOffset),(1, 0, 0),self.solo_txtSize/2.0)

                if self.coOpType and self.partImage:
                  freeX = .05*(self.numOfPlayers-1)
                  freeI = .05*self.numOfPlayers
                  for j in xrange(self.numOfPlayers):
                    if self.scoring[j].endingStreakBroken:
                      partcolor = (.4, .4, .4, 1)
                    else:
                      partcolor = (.8, .8, .8, 1)
                    self.engine.drawImage(self.part[j], scale = (.15,-.15), coord = (self.wFull*(.5-freeX+freeI*j),self.hFull*.58), color = partcolor)

                text = "%s" % 0
                if self.theme == 2:
                  text = text.replace("0","O")
                tW, tH = self.solo_soloFont.getStringSize(text, scale = self.solo_txtSize)
                yOffset = 0.175
                xOffset = 0.500
                

                if self.breScoreBackground:
                  #frameWidth = tW*3.0
                  frameHeight = tH*4.0
                  frameWidth = frameHeight
                  if self.coOpType:
                    boxYOffset = self.hFull*(1.0-(yOffset + tH/2.0 ) / self.fontScreenBottom)
                    boxXOffset = xOffset*self.wFull
                  else:
                    boxYOffset = self.hPlayer[i]-(self.hPlayer[i]* ((yOffset + tH/2.0 ) / self.fontScreenBottom) )   
                    boxXOffset = self.wPlayer[i]*xOffset
                  tempWScale = frameWidth*self.breScoreBackgroundWFactor
                  tempHScale = -(frameHeight)*self.breScoreBackgroundWFactor
                  self.engine.drawImage(self.breScoreBackground, scale = (tempWScale,tempHScale), coord = (boxXOffset,boxYOffset))

                if self.breScoreFrame:
                  frameWidth = tW*1.15
                  frameHeight = tH*1.07
                  if self.coOpType:
                    boxYOffset = self.hFull*(1.0-(yOffset + tH/2.0 ) / self.fontScreenBottom)
                    boxXOffset = xOffset*self.wFull
                  else:
                    boxYOffset = self.hPlayer[i]-(self.hPlayer[i]* ((yOffset + tH/2.0 ) / self.fontScreenBottom) )   
                    boxXOffset = self.wPlayer[i]*xOffset
                  tempWScale = frameWidth*self.breScoreFrameWFactor
                  tempHScale = -(frameHeight)*self.breScoreFrameWFactor
                  self.engine.drawImage(self.breScoreFrame, scale = (tempWScale,tempHScale), coord = (boxXOffset,boxYOffset))
                self.solo_soloFont.render(text, (xOffset - tW/2.0, yOffset),(1, 0, 0),self.solo_txtSize)
            
            self.engine.view.setViewportHalf(1,0)
            # evilynux - Display framerate
            if self.engine.show_fps: #probably only need to once through.
              c1,c2,c3 = self.ingame_stats_color
              glColor3f(c1, c2, c3)
              text = _("FPS: %.2f" % self.engine.fpsEstimate)
              w, h = font.getStringSize(text, scale = 0.00140)
              font.render(text, (.85, .055 - h/2), (1,0,0), 0.00140)
 
            pos = self.getSongPosition()
    
            if self.showScriptLyrics and not self.pause and not self.failed:
              #for time, event in self.song.track[i].getEvents(pos - self.song.period * 2, pos + self.song.period * 4):
              for time, event in self.song.eventTracks[Song.TK_SCRIPT].getEvents(pos - self.song.period * 2, pos + self.song.period * 4): #MFH - script track
              
                if isinstance(event, PictureEvent):
                  if pos < time or pos > time + event.length:
                    continue
                  
                  try:
                    picture = event.picture
                  except:
                    self.engine.loadImgDrawing(event, "picture", os.path.join(self.libraryName, self.songName, event.fileName))
                    picture = event.picture
                    
                  w = self.wFull
                  h = self.hFull
  
                  if self.theme == 2:
                    yOffset = 0.715
                  else:
                    #gh3 or other standard mod
                    yOffset = 0.69
  
                  fadePeriod = 500.0
                  f = (1.0 - min(1.0, abs(pos - time) / fadePeriod) * min(1.0, abs(pos - time - event.length) / fadePeriod)) ** 2

                  self.engine.drawImage(picture, scale = (1, -1), coord = (w / 2, (f * -2 + 1) * h/2+yOffset))
                  
                elif isinstance(event, TextEvent):
                  if pos >= time and pos <= time + event.length and not self.ending:    #myfingershurt: to not display events after ending!
                    
                    xOffset = 0.5
                    if self.scriptLyricPos == 0:
                      if self.theme == 2:
                        yOffset = 0.715
                        txtSize = 0.00170
                      else:
                        #gh3 or other standard mod
                        yOffset = 0.69
                        txtSize = 0.00175
                    else:   #display in lyric bar position
                      yOffset = 0.0696    #last change +0.0000
                      txtSize = 0.00160
                    
    
                    #MFH TODO - pre-retrieve and translate all current tutorial script.txt events, if applicable.
                    if self.song.info.tutorial:
                      text = _(event.text)
                      w, h = lyricFont.getStringSize(text,txtSize)
                      lyricFont.render(text, (xOffset - w / 2, yOffset),(1, 0, 0),txtSize) 
    
                    #elif event.text.find("TXT:") < 0 and event.text.find("LYR:") < 0 and event.text.find("SEC:") < 0 and event.text.find("GSOLO") < 0:   #filter out MIDI text events, only show from script here.
                    else:
                      text = event.text
                      w, h = lyricFont.getStringSize(text,txtSize)
                      lyricFont.render(text, (xOffset - w / 2, yOffset),(1, 0, 0),txtSize) 
    
    
    
            #-------------after "if showlyrics"
            
            #self.engine.view.setViewport(1,0) 
            #scrolling lyrics & sections: moved to before player viewport split
  

  
  
  
                    #Show Jurgen played Spikehead777
          if self.jurgPlayer[i] == True:
            if self.autoPlay:
              if self.jurg == i or self.jurg == 2: #or whatever the "all/both players" is
                text = self.tsJurgenIsHere
              else:
                text = self.tsJurgenWasHere
            else:
              text = self.tsJurgenWasHere
            #jurgScale = .001/self.numOfPlayers
            jurgScale = float(self.jurgenText[2])
            w, h = bigFont.getStringSize(text, scale = jurgScale)
            Theme.setBaseColor()
            jurgX = float(self.jurgenText[0])
            if jurgX > 1 - w:
              jurgX = 1 - w
            jurgY = float(self.jurgenText[1])
            if jurgY > .75 - h:
              jurgY = .75 - h
            
            bigFont.render(text,  (jurgX, jurgY), scale = jurgScale)#MFH - y was 0.4 - more positioning weirdness.

          #End Jurgen Code
        #MFH - Get Ready to Rock & countdown, song info during countdown, and song time left display on top of everything else
        self.engine.view.setViewport(1,0)


        if (not self.pause and not self.failed and not self.ending):
          if self.coOpType: #render co-op phrases (full screen width) above the rest.
            if self.displayText[self.coOpPhrase] != None:
              glColor3f(.8,.75,.01)
              size = sphraseFont.getStringSize(self.displayText[self.coOpPhrase], scale = self.displayTextScale[self.coOpPhrase])
              sphraseFont.render(self.displayText[self.coOpPhrase], (.5-size[0]/2,self.textY[self.coOpPhrase]-size[1]), scale = self.displayTextScale[self.coOpPhrase])
          
          # show countdown
          # glorandwarf: fixed the countdown timer
          if self.countdownSeconds > 1:
            Theme.setBaseColor(min(1.0, 3.0 - abs(4.0 - self.countdownSeconds)))
            text = self.tsGetReady
            w, h = font.getStringSize(text)
            font.render(text,  (.5 - w / 2, .3))              
            if self.countdownSeconds < 6:
              if self.counting:
                for i,player in enumerate(self.playerList):
                  w = self.wPlayer[i]
                  h = self.hPlayer[i]
                  partImgwidth = self.part[i].width1()
                  partwFactor = 250.000/partImgwidth
                  partX = ((i*2)+1) / (self.numOfPlayers*2.0)
                  self.engine.drawImage(self.part[i], scale = (partwFactor*0.25,partwFactor*-0.25), coord = (w*partX,h*.4), color = (1,1,1, 3.0 - abs(4.0 - self.countdownSeconds)))
                  Theme.setBaseColor(min(1.0, 3.0 - abs(4.0 - self.countdownSeconds)))
                  text = player.part.text
                  w, h = font.getStringSize(text)
                  font.render(text,  (partX - w*.5, .5))
              else:
                scale = 0.002 + 0.0005 * (self.countdownSeconds % 1) ** 3
                text = "%d" % (self.countdownSeconds)
                w, h = bigFont.getStringSize(text, scale = scale)
                Theme.setBaseColor()
                bigFont.render(text,  (.5 - w / 2, .45 - h / 2), scale = scale)
          
          if self.resumeCountdownSeconds > 1:
            scale = 0.002 + 0.0005 * (self.resumeCountdownSeconds % 1) ** 3
            text = "%d" % (self.resumeCountdownSeconds)
            w, h = bigFont.getStringSize(text, scale = scale)
            Theme.setBaseColor()
            bigFont.render(text,  (.5 - w / 2, .45 - h / 2), scale = scale)
    
          w, h = font.getStringSize(" ")
          y = .05 - h / 2 - (1.0 - v) * .2
    
          songFont = self.engine.data.songFont
    
          # show song name
          if self.countdown and self.song:
            cover = ""
            if self.song.info.findTag("cover") == True: #kk69: misc changes to make it more GH/RB
              cover = "%s  \n " % self.tsAsMadeFamousBy #kk69: no more ugly colon! ^_^
            else:
              if self.theme == 2:
                cover = "" #kk69: for RB
              else:
                cover = self.tsBy   #kk69: for GH
            Theme.setBaseColor(min(1.0, 4.0 - abs(4.0 - self.countdown)))
            comma = ""
            extra = ""
            if self.song.info.year: #add comma between year and artist
              comma = ", "
            if self.song.info.frets:
              extra = "%s \n %s%s" % (extra, self.tsFrettedBy, self.song.info.frets)
            if self.song.info.version:
              extra = "%s \n v%s" % (extra, self.song.info.version)
    
            if self.theme != 1:   #shift this stuff down so it don't look so bad over top the lyricsheet:
              Dialogs.wrapText(songFont, (self.songInfoDisplayX, self.songInfoDisplayX - h / 2), "%s \n %s%s%s%s%s" % (Dialogs.removeSongOrderPrefixFromName(self.song.info.name), cover, self.song.info.artist, comma, self.song.info.year, extra), rightMargin = .6, scale = self.songInfoDisplayScale)#kk69: incorporates song.ttf
            else:
              Dialogs.wrapText(songFont, (self.songInfoDisplayX, self.songInfoDisplayY - h / 2), "%s \n %s%s%s%s%s" % (Dialogs.removeSongOrderPrefixFromName(self.song.info.name), cover, self.song.info.artist, comma, self.song.info.year, extra), rightMargin = .6, scale = self.songInfoDisplayScale)
          else:
            #mfh: this is where the song countdown display is generated:
            if pos < 0:
              pos = 0
            if countdownPos < 0:
              countdownPos = 0
            Theme.setBaseColor()
    
    
            #if countdownPos == 0:   #MFH - reset drumStart so that the drummer can get down with his bad self at the end of the song without penalty.
            #  self.drumStart = False  #faaa's drum sound mod restart


            
            
            if (self.gameTimeMode > 0 or self.muteLastSecond == 1 or self.hopoDebugDisp == 1) and (not self.pause and not self.failed and not self.ending and not self.youRock):
              #MFH: making this a global variable so it may be easily accessed for log entries where appropriate
              if self.gameTimeMode == 1:    #countdown
                self.timeLeft = "%d:%02d" % (countdownPos / 60000, (countdownPos % 60000) / 1000)
              elif self.gameTimeMode == 2:  #elapsed
                self.timeLeft = "%d:%02d" % (pos / 60000, (pos % 60000) / 1000)
              if self.gameTimeMode > 0 or self.hopoDebugDisp == 1:
                w, h = font.getStringSize(self.timeLeft)
                if self.lyricSheet != None:   #shift this stuff down so it don't look so bad over top the lyricsheet:
                  font.render(self.timeLeft,  (.5 - w / 2, .055 - h / 2 - (1.0 - v) * .2))
                else:
                  font.render(self.timeLeft,  (.5 - w / 2, y))
    
    
    
    
            #Not ready for 2player yet
            #if self.notesCum:
            #  f = int(100 * (float(self.playerList[0].notesHit) / self.notesCum))
            #  font.render("%d%%" % f, (.5 - w / 2, y + h))
    
    
          
    
    #-        if self.rock[0]<=0 and self.battle and self.numOfPlayers>1: #QQstarS:new2 Bettle failing
    #-          self.displayText = "You Failed!!!!"
    #-          self.streakFlag = "0"   #QQstarS:Set [0] to [i] #if player0 streak50, set the flag to 1. 
    #-          self.guitars[0].actions = [0,0,0]
    #-          #self.keysList   = [PLAYER2KEYS]
    #-        elif self.rock[1]<=0 and self.battle and self.numOfPlayers>1: #QQstarS:new2 Bettle failing
    #-          self.displayText = "You Failed!!!!"
    #-          self.streakFlag = "1"   #QQstarS:Set [0] to [i] #if player0 streak50, set the flag to 1. 
    #-          self.guitars[1].actions = [0,0,0]
    
            #Party mode
            if self.partyMode == True:
              timeleft = (now - self.partySwitch) / 1000
              if timeleft > self.partyTime:
                self.partySwitch = now
                if self.partyPlayer == 0:
                  self.guitars[0].keys = PLAYER2KEYS
                  self.guitars[0].actions = PLAYER2ACTIONS
                  self.keysList   = [PLAYER2KEYS]
                  self.partyPlayer = 1
                else:
                  self.guitars[0].keys = PLAYER1KEYS
                  self.guitars[0].actions = PLAYER1ACTIONS
                  self.keysList   = [PLAYER1KEYS]
                  self.partyPlayer = 0
              t = "%d" % (self.partyTime - timeleft + 1)
              if self.partyTime - timeleft < 5:
                glColor3f(1, 0, 0)
                w, h = font.getStringSize(t)#QQstarS:party
                font.render(t,  (.5 - w / 2, 0.4))  #QQstarS:party
              elif self.partySwitch != 0 and timeleft < 1:
                t = "Switch"
                glColor3f(0, 1, 0)
                w, h = font.getStringSize(t)#QQstarS:party
                font.render(t,  (.5 - w / 2, 0.4))#QQstarS:party
              else:#QQstarS:party
                w, h = font.getStringSize(t)
                font.render(t,  (.5 - w / 2, y + h))


  
      finally:
        if self.fontMode==1:      #0 = oGL Hack, 1=LaminaScreen, 2=LaminaFrames
          self.laminaScreen.refreshPosition() 
          self.laminaScreen.display()
        elif self.fontMode==2:  #0 = oGL Hack, 1=LaminaScreen, 2=LaminaFrames
          self.laminaFrame_soloAcc.display()
        #self.engine.view.setViewport(1,0)
        self.engine.view.resetProjection()


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

import math
import pygame
import random
import os

#myfingershurt: decimal class allows for better handling of fixed-point numbers
import decimal
import Log
import locale


from OpenGL.GL import *

class GuitarScene:
  pass

class GuitarSceneServer(GuitarScene, SceneServer):
  pass

class GuitarSceneClient(GuitarScene, SceneClient):
  def createClient(self, libraryName, songName, Players):
    self.playerList   = [self.player]

    self.partyMode = False
    self.battle = False #QQstarS:new2 Bettle
    self.coOp = False
    Log.debug("GuitarSceneClient init...")


    #MFH - testing new traceback logging:
    #raise TypeError
    
    splash = Dialogs.showLoadingSplashScreen(self.engine, _("Preparing...") ) 

    
    #MFH - retrieve game parameters:
    self.gamePlayers = self.engine.config.get("game", "players")
    self.gameMode1p = self.engine.config.get("player0","mode_1p")
    self.gameMode2p = self.engine.config.get("player1","mode_2p")

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
        self.battle = True
        self.coOp = False
      elif self.gameMode2p == 3:
        self.battle = False
        self.coOp = True
      else:
        self.battle = False
        self.coOp = False

    self.splayers = Players #Spikehead777

    #myfingershurt: drums :)
    self.guitars = []
    self.keysList = []
    for i,player in enumerate(self.playerList):
      if player.part.text == "Drums":
        self.guitars.append(Drum(self.engine,False,i))
      else:
        self.guitars.append(Guitar(self.engine,False,i))
        if player.part.text == "Lead Guitar" or player.part.text == "Guitar":    #both these selections should get guitar solos
          self.guitars[i].canGuitarSolo = True
        elif player.part.text == "Bass Guitar":
          self.guitars[i].isBassGuitar = True
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
    
    self.visibility       = 0.0
    self.libraryName      = libraryName
    self.songName         = songName
    self.done             = False
    
    #try:
    #  self.sfxChannel = self.engine.audio.getChannel(4)
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

    #Spikehead777
    self.jurg             = self.engine.config.get("game", "jurgtype")
    
    #MFH
    self.jurgenLogic = self.engine.config.get("game", "jurglogic")    #logic 0 = original, logic 1 = MFH-1
    self.timeLeft = None
    self.processedFirstNoteYet = False
    
    self.autoPlay         = self.engine.config.get("game", "jurgdef")
    
    self.jurg1            = False
    self.jurg2            = False

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
    self.failTimer = 0
    self.rockTimer = 0  #myfingershurt
    self.youRock = False    #myfingershurt
    self.rockCountdown = 100
    self.soloReviewDispDelay = 300
    self.rockFinished = False


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
    

    #MFH - precalculation variable definition
    self.numOfPlayers = len(self.playerList)    #MFH - MUST be in front of loadSettings call!

    #Get theme
    themename = self.engine.data.themeLabel
    self.theme = self.engine.data.theme

    if Theme.rmtype != None:
      self.rmtype = Theme.rmtype
    else:
      self.rmtype = self.theme

    stage = os.path.join("themes",themename,"stage.ini")
    self.stage = Stage.Stage(self, self.engine.resource.fileName(stage))

    self.loadSettings()

    #MFH pre-translate text strings:
    self.tsNoteStreak = _("Note Streak!!!")
    if self.theme == 2:
      self.tsStarPowerReady = _("Overdrive Ready")
    else:
      self.tsStarPowerReady = _("Star Power Ready")
    self.tsYouFailedBattle = _("You Failed!!!!")
    self.tsJurgenIsHere = _("Jurgen is here")
    self.tsJurgenWasHere = _("Jurgen was here")
    self.tsPercentComplete = _("% Complete")
    self.tsHopoIndicator = _("HOPO")
    self.tsCompleted = _("COMPLETED")
    self.tsPercentOn = _(" % ON ")
    self.tsBassGroove = _("BASS GROOVE")
    self.tsBassGrooveLabel = _("Bass Groove:")
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
    self.tsGuitarSolo = _("Guitar Solo!")
    self.tsPerfectSolo = _("Perfect Solo!")
    self.tsAwesomeSolo = _("Awesome Solo!")
    self.tsGreatSolo = _("Great Solo!")
    self.tsGoodSolo = _("Good Solo!")
    self.tsSolidSolo = _("Solid Solo!")
    self.tsOkaySolo = _("Okay Solo!")
    self.tsMessySolo = _("Messy Solo!")
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
    self.wPlayer = []
    self.hPlayer = []
    self.hOffset = []
    self.hFontOffset = []
    self.stage.wFull = self.wFull   #MFH - needed for new stage background handling
    self.stage.hFull = self.hFull
    
    
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
    self.digitalKillswitchStarpowerChunkSize = 0.05
    # evilynux: was 0.10, now much closer to actual GH3
    self.analogKillswitchStarpowerChunkSize = 0.15
    self.rbOverdriveBarGlowFadeInChunk = .07     #this amount added to visibility every run() cycle when fading in - original .2
    self.rbOverdriveBarGlowFadeOutChunk = .03   #this amount subtracted from visibility every run() cycle when fading out - original .07
    self.maxDisplayTextScale = 0.0024       #orig 0.0024
    self.displayTextScaleStep2 = 0.00008    #orig 0.00008
    self.displayTextScaleStep1 = 0.0001     #orig 0.0001
    self.textTimeToDisplay = 100
    self.songInfoDisplayScale = Theme.songInfoDisplayScale
    self.lyricMode = self.engine.config.get("game", "lyric_mode")
    self.scriptLyricPos = self.engine.config.get("game", "script_lyric_pos")
    self.starClaps = self.engine.config.get("game", "star_claps")
    self.rb_sp_neck_glow = self.engine.config.get("game", "rb_sp_neck_glow")
    self.accuracy = [0 for i in self.playerList]
    self.countdownSeconds = 5   #MFH - don't change this initialization value unless you alter the other related variables to match
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
    self.whammySavesSP = self.engine.config.get("game", "whammy_saves_starpower") #MFH
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



    #racer: practice beat claps:
    self.beatClaps = self.engine.config.get("game", "beat_claps")
    

    self.killDebugEnabled = self.engine.config.get("game", "kill_debug")

    self.bassGrooveEnableMode = self.engine.config.get("game", "bass_groove_enable")

    
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
    self.autoDrumStarpowerActivate = self.engine.config.get("game", "auto_drum_sp")


    #MFH - TODO - rewrite in an expandable fashion; requires creation of some new Player object constants that will link to the appropriate player's control based on which player the object is set to
    if self.analogKillMode[0] > 0:
      KillKeyCode[0] = self.controls.getReverseMapping(Player.KILL)
      self.isKillAnalog[0], self.whichJoy[0], self.whichAxis[0] = self.engine.input.getWhammyAxis(KillKeyCode[0])
    if self.numOfPlayers > 1 and self.analogKillMode[1] > 0:
      KillKeyCode[1] = self.controls.getReverseMapping(Player.PLAYER_2_KILL)
      self.isKillAnalog[1], self.whichJoy[1], self.whichAxis[1] = self.engine.input.getWhammyAxis(KillKeyCode[1])

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
    splash = Dialogs.showLoadingSplashScreen(self.engine, phrase)

    self.playerList[0].hopoFreq = self.song.info.hopofreq



    #MFH - single audio track song detection
    self.isSingleAudioTrack = self.song.isSingleAudioTrack


    #myfingershurt: also want to go through song and search for guitar solo parts, and count notes in them in each diff.
    self.inGameStats = self.engine.config.get("performance","in_game_stats")
    self.inGameStars = self.engine.config.get("game","in_game_stars")
    self.partialStars = self.engine.config.get("game","partial_stars")

    
    self.guitarSoloAccuracyDisplayMode = self.engine.config.get("game", "gsolo_accuracy_disp")
    self.guitarSoloAccuracyDisplayPos = self.engine.config.get("game", "gsolo_acc_pos")
    

    #need a new flag for each player, showing whether or not they've missed a note during a solo section.
    #this way we have a backup detection of Perfect Solo in case a note got left out, picks up the other side of the solo slop
    self.guitarSoloBroken = [False for i in self.playerList]


    self.avMult = [0.0 for i in self.playerList]
    self.lastStars = [0 for i in self.playerList]
    #self.stars = [0,0]
    for i, thePlayer in enumerate(self.playerList):   
      thePlayer.stars = 0

    
    self.partialStar = [0 for i in self.playerList]
    self.dispSoloReview = [False for i in self.playerList]
    self.soloReviewText = [[] for i in self.playerList]
    self.soloReviewCountdown = [0 for i in self.playerList]
    self.hitAccuracy = [0.0 for i in self.playerList]
    self.guitarSoloAccuracy = [0.0 for i in self.playerList]
    self.guitarSoloActive = [False for i in self.playerList]
    self.currentGuitarSolo = [0 for i in self.playerList]

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
    for i,guitar in enumerate(self.guitars):
      if guitar.isDrum:
        self.playerList[i].totalStreakNotes = len([1 for time, event in self.song.track[i].getAllEvents() if isinstance(event, Note)])
      else:
        self.playerList[i].totalStreakNotes = len(set(time for time, event in self.song.track[i].getAllEvents() if isinstance(event, Note)))
      self.playerList[i].totalNotes = len([1 for Ntime, event in self.song.track[i].getAllEvents() if isinstance(event, Note)])
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
        Ntime = Ntime - soloSlop
        guitarSoloNoteCount = len([1 for Gtime, Gevent in self.song.track[i].getEvents(guitarSoloStartTime, Ntime) if isinstance(Gevent, Note)])
        self.guitarSolos[i].append(guitarSoloNoteCount - 1)
        newEvent = TextEvent("GSOLO OFF", 100.0)
        #self.song.eventTracks[Song.TK_GUITAR_SOLOS].addEvent(time - soloSlop,newEvent) #adding the missing GSOLO OFF event
        self.song.eventTracks[Song.TK_GUITAR_SOLOS].addEvent(Ntime, newEvent) #adding the missing GSOLO OFF event
        Log.debug("GuitarScene: Guitar Solo until end of song found - (guitarSoloStartTime - Ntime = guitarSoloNoteCount): " + str(guitarSoloStartTime) + "-" + str(Ntime) + " = " + str(guitarSoloNoteCount) )


    #MFH - now, handle MIDI starpower / overdrive / other special marker notes:
    if self.starpowerMode == 2:     #auto-MIDI mode only
      if self.song.hasStarpowerPaths:
        for i,guitar in enumerate(self.guitars):
          for time, event in self.song.track[i].getAllEvents():
            if isinstance(event, Song.MarkerNote):
              markStarpower = False
              if event.number == Song.overDriveMarkingNote:
                markStarpower = True
              if event.number == Song.starPowerMarkingNote:
                if self.song.midiStyle == Song.MIDI_TYPE_GH:
                  markStarpower = True
                #else:  #RB solo marking!
              
              if markStarpower:
                tempStarpowerNoteList = self.song.track[i].getEvents(time, time+event.length) 
                for spTime, spEvent in tempStarpowerNoteList:
                  if isinstance(spEvent, Note):
                    spEvent.star = True
                #now, go back and mark all of the last chord as finalStar
                lastChordTime = spTime
                for spTime, spEvent in tempStarpowerNoteList:
                  if isinstance(spEvent, Note):
                    if spTime == lastChordTime:
                      spEvent.finalStar = True
                if self.logMarkerNotes == 1:
                  Log.debug("GuitarScene: P%d starpower phrase marked between %f and %f" % ( i+1, time, time+event.length ) )
      
      else:
        for guitar in self.guitars:
          guitar.starNotesSet = False     #fallback on auto generation.
    


    self.initializeStarScoringThresholds()    #MFH
      
    

    #glorandwarf: need to store the song's beats per second (bps) for later
    self.songBPS = self.song.bpm / 60.0
      
    
    self.failingEnabled = self.engine.config.get("coffee", "failingEnabled")

    if self.careerMode:
      self.failingEnabled = True


    self.tut = self.engine.config.get("game", "tut")
    
    if self.playerList[0].practiceMode or self.song.info.tutorial or self.tut:
      self.failingEnabled = False

    #MFH - no Jurgen in Career mode or tutorial mode or practice mode:
    if self.careerMode or self.tut or self.playerList[0].practiceMode:
      self.autoPlay = False

    
    self.phrases = self.engine.config.get("coffee", "phrases")#blazingamer
    self.starfx = self.engine.config.get("game", "starfx")#blazingamer
    self.rbmfx = self.engine.config.get("game", "rbmfx")#blazingamer
    self.boardY = 2
    self.rbOverdriveBarGlowVisibility = 0
    self.rbOverdriveBarGlowFadeOut = False

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
      
    
    try:
      self.engine.loadImgDrawing(self, "soloFrame", os.path.join("themes",themename,"soloframe.png"))
      soloImgwidth = self.soloFrame.width1()
      self.soloFrameWFactor = 640.000/soloImgwidth
    except IOError:
      self.soloFrame = None
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
      self.engine.loadImgDrawing(self, "rockmeter", os.path.join("themes",themename,"rockmeter.png"))
      self.engine.loadImgDrawing(self, "counter", os.path.join("themes",themename,"counter.png"))
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
      try:
        self.engine.loadImgDrawing(self, "dots", os.path.join("themes",themename,"dotshalf.png"))
      except IOError:
        self.engine.loadImgDrawing(self, "dots", os.path.join("themes",themename,"dots.png"))
        self.halfDots = False
      
      
      #rockmeter
      self.engine.loadImgDrawing(self, "rockHi", os.path.join("themes",themename,"rock_hi.png"))
      self.engine.loadImgDrawing(self, "rockLo", os.path.join("themes",themename,"rock_low.png"))
      self.engine.loadImgDrawing(self, "rockMed", os.path.join("themes",themename,"rock_med.png"))
      self.engine.loadImgDrawing(self, "arrow", os.path.join("themes",themename,"rock_arr.png"))
      self.engine.loadImgDrawing(self, "rockTop", os.path.join("themes",themename,"rock_top.png"))
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
      self.engine.loadImgDrawing(self, "failScreen", os.path.join("themes",themename,"pause.png"))
      #Rockmeter
      self.engine.loadImgDrawing(self, "counter", os.path.join("themes",themename,"counter.png"))



      #MFH - TODO - rewrite scorePic code to be more expandable, create a list of scorePic objects so each player can have one without special initializations
      #kuzux: instrument-dependant score meter for Rock Band theme
      try:
        #if self.playerList[0].part.text == "Drums":
        if self.guitars[0].isDrum:
          self.engine.loadImgDrawing(self, "scorePic", os.path.join("themes",themename,"score_drums.png"))
        #elif self.playerList[0].part.text == "Bass Guitar":
        elif self.guitars[0].isBassGuitar:
          self.engine.loadImgDrawing(self, "scorePic", os.path.join("themes",themename,"score_bass.png"))
        else:
          self.engine.loadImgDrawing(self, "scorePic", os.path.join("themes",themename,"score_guitar.png"))
      except IOError:
        self.engine.loadImgDrawing(self, "scorePic", os.path.join("themes",themename,"score.png"))      

      if self.numOfPlayers > 1:
        #Log.debug("P2 RB Score Icon for: " + self.playerList[1].part.text)
        try:
          #if self.playerList[1].part.text == "Drums":
          if self.guitars[1].isDrum:
            self.engine.loadImgDrawing(self, "scorePicP2", os.path.join("themes",themename,"score_drums.png"))
          #elif self.playerList[1].part.text == "Bass Guitar":
          elif self.guitars[1].isBassGuitar:
            self.engine.loadImgDrawing(self, "scorePicP2", os.path.join("themes",themename,"score_bass.png"))
          else:
            self.engine.loadImgDrawing(self, "scorePicP2", os.path.join("themes",themename,"score_guitar.png"))
        except IOError:
          self.engine.loadImgDrawing(self, "scorePicP2", os.path.join("themes",themename,"score.png"))      




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

      #myfingershurt: Rock Band theme gets instrument-dependant rock meter arrows:
      try:
        #if self.playerList[0].part.text == "Drums":
        if self.guitars[0].isDrum:
          self.engine.loadImgDrawing(self, "arrow", os.path.join("themes",themename,"rockarr_drums.png"))
        #elif self.playerList[0].part.text == "Bass Guitar":
        elif self.guitars[0].isBassGuitar:
          self.engine.loadImgDrawing(self, "arrow", os.path.join("themes",themename,"rockarr_bass.png"))
        else:
          self.engine.loadImgDrawing(self, "arrow", os.path.join("themes",themename,"rockarr_guitar.png"))
      except IOError:
        self.engine.loadImgDrawing(self, "arrow", os.path.join("themes",themename,"rock_arr.png"))
        
      if self.numOfPlayers > 1:
        try:
          #if self.playerList[1].part.text == "Drums":
          if self.guitars[1].isDrum:
            self.engine.loadImgDrawing(self, "arrowP2", os.path.join("themes",themename,"rockarr_drums.png"))
          #elif self.playerList[1].part.text == "Bass Guitar":
          elif self.guitars[1].isBassGuitar:
            self.engine.loadImgDrawing(self, "arrowP2", os.path.join("themes",themename,"rockarr_bass.png"))
          else:
            self.engine.loadImgDrawing(self, "arrowP2", os.path.join("themes",themename,"rockarr_guitar.png"))
        except IOError:
          self.engine.loadImgDrawing(self, "arrowP2", os.path.join("themes",themename,"rock_arr.png"))



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

    self.starGrey1 = None
    if self.starWhite and self.starGrey and self.starPerfect and self.partialStars == 1:   #MFH - even better in-game star display, stargrey1.png - stargrey7.png (stargrey8.png is useless - that's a white star.)
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

    self.counterY = -0.1

    self.scaleText = [0.0 for i in self.playerList]
    self.displayText = [None for i in self.playerList]
    self.dislayTextScale = [0.0 for i in self.playerList]
    #self.streakFlag = None #QQstarS:Set the flag,to show which one has reach the 50 note
    self.textTimer = [0.0 for i in self.playerList]
    #self.textChanged = False
    self.textY = [.3 for i in self.playerList]
    self.scaleText2 = [0.0 for i in self.playerList]
    self.goingUP = [False for i in self.playerList]
    self.lastStreak = [0 for i in self.playerList]

    self.killswitchEngaged = [None for i in self.playerList]


    # glorandwarf: hide the splash screen
    Dialogs.hideLoadingSplashScreen(self.engine, splash)
    splash = None

    settingsMenu = Settings.GameSettingsMenu(self.engine)
    settingsMenu.fadeScreen = True


    #MFH - retrieve theme.ini pause background & text positions 
    self.pause_bkg_x = Theme.pause_bkg_xPos
    self.pause_bkg_y = Theme.pause_bkg_yPos
    self.pause_text_x = Theme.pause_text_xPos
    self.pause_text_y = Theme.pause_text_yPos

    if self.pause_bkg_x == None:
      self.pause_bkg_x = 0

    if self.pause_bkg_y == None:
      self.pause_bkg_y = 0

    if self.pause_text_x == None:
      self.pause_text_x = .3

    if self.pause_text_y == None:
      self.pause_text_y = .31


    #MFH - new theme.ini color options:

    self.pause_text_color = Theme.hexToColor(Theme.pause_text_colorVar)
    self.pause_selected_color = Theme.hexToColor(Theme.pause_selected_colorVar)
    self.fail_text_color = Theme.hexToColor(Theme.fail_text_colorVar)
    self.fail_selected_color = Theme.hexToColor(Theme.fail_selected_colorVar)

    # evilynux - More themeable options
    self.rockmeter_score_color = Theme.hexToColor(Theme.rockmeter_score_colorVar)
    
    #self.fail_completed_color = Theme.hexToColor(Theme.song_name_selected_colorVar) # text same color as selected song
    self.fail_completed_color = Theme.hexToColor(Theme.fail_text_colorVar)  #No, now same as fail_text color.
    
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

    Log.debug("Pause text / selected colors: " + str(self.pause_text_color) + " / " + str(self.pause_selected_color))



#racer: theme.ini fail positions
    size = self.engine.data.pauseFont.getStringSize("Quit to Main")
    self.fail_bkg_x = Theme.fail_bkg_xPos
    self.fail_bkg_y = Theme.fail_bkg_yPos
    self.fail_text_x = Theme.fail_text_xPos
    self.fail_text_y = Theme.fail_text_yPos

    if self.fail_bkg_x == None:
      self.fail_bkg_x = 0

    if self.fail_bkg_y == None:
      self.fail_bkg_y = 0

    if self.fail_text_x == None:
      self.fail_text_x = .5-size[0]/2.0

    if self.fail_text_y == None:
      self.fail_text_y = .47



    if self.theme == 1: #GH3-like theme
      if self.careerMode:
        self.menu = Menu(self.engine, [
          (_("        RESUME"), self.resumeSong),
          (_("       RESTART"), self.restartSong),
          (_("        GIVE UP"), self.changeSong),
          (_("       PRACTICE"), self.practiceSong), #evilynux
          (_("       OPTIONS"), settingsMenu),
          (_("           QUIT"), self.quit),
        ], fadeScreen = False, onClose = self.resumeGame, font = self.engine.data.pauseFont, pos = (self.pause_text_x, self.pause_text_y), textColor = self.pause_text_color, selectedColor = self.pause_selected_color, append_submenu_char = False)
      else:
        self.menu = Menu(self.engine, [
          (_("        RESUME"), self.resumeSong),
          (_("       RESTART"), self.restartSong),
          (_("        GIVE UP"), self.changeSong),
          (_("      END SONG"), self.endSong),
          (_("       OPTIONS"), settingsMenu),
          (_("           QUIT"), self.quit),
        ], fadeScreen = False, onClose = self.resumeGame, font = self.engine.data.pauseFont, pos = (self.pause_text_x, self.pause_text_y), textColor = self.pause_text_color, selectedColor = self.pause_selected_color, append_submenu_char = False)
      size = self.engine.data.pauseFont.getStringSize("Quit to Main")
      if self.careerMode:
        self.failMenu = Menu(self.engine, [
          (_("RETRY SONG"), self.restartAfterFail),
          (_("  PRACTICE"), self.practiceSong), #evilynux
          (_(" NEW SONG"), self.changeAfterFail),
          (_("     QUIT"), self.quit),
        ], fadeScreen = False, onCancel = self.changeAfterFail, font = self.engine.data.pauseFont, pos = (self.fail_text_x, self.fail_text_y), textColor = self.fail_text_color, selectedColor = self.fail_selected_color)
      else:
        self.failMenu = Menu(self.engine, [
          (_("RETRY SONG"), self.restartAfterFail),
          (_(" NEW SONG"), self.changeAfterFail),
          (_("     QUIT"), self.quit),
        ], fadeScreen = False, onCancel = self.changeAfterFail, font = self.engine.data.pauseFont, pos = (self.fail_text_x, self.fail_text_y), textColor = self.fail_text_color, selectedColor = self.fail_selected_color)
      FirstTime = True
      self.restartSong(FirstTime)
    elif self.theme == 0:   #GH2-like theme
      if self.careerMode:
        self.menu = Menu(self.engine, [
          (_("  Resume"),       self.resumeSong),
          (_("  Start Over"),      self.restartSong),
          (_("  Change Song"),       self.changeSong),
          (_("  Practice"),       self.practiceSong), #evilynux
          (_("  Settings"),          settingsMenu),
          (_("  Quit to Main Menu"), self.quit),
        ], fadeScreen = False, onClose = self.resumeGame, font = self.engine.data.pauseFont, pos = (self.pause_text_x, self.pause_text_y), textColor = self.pause_text_color, selectedColor = self.pause_selected_color)
      else:
        self.menu = Menu(self.engine, [
          (_("  Resume"),       self.resumeSong),
          (_("  Start Over"),      self.restartSong),
          (_("  Change Song"),       self.changeSong),
          (_("  End Song"),          self.endSong),
          (_("  Settings"),          settingsMenu),
          (_("  Quit to Main Menu"), self.quit),
        ], fadeScreen = False, onClose = self.resumeGame, font = self.engine.data.pauseFont, pos = (self.pause_text_x, self.pause_text_y), textColor = self.pause_text_color, selectedColor = self.pause_selected_color)
      size = self.engine.data.pauseFont.getStringSize("Quit to Main")
      if self.careerMode:
        self.failMenu = Menu(self.engine, [
          (_(" Try Again?"), self.restartAfterFail),
          (_("  Give Up?"), self.changeAfterFail),
          (_("  Practice?"), self.practiceSong), #evilynux
          (_("Quit to Main"), self.quit),
        ], fadeScreen = False, onCancel = self.changeAfterFail, font = self.engine.data.pauseFont, pos = (self.fail_text_x, self.fail_text_y), textColor = self.fail_text_color, selectedColor = self.fail_selected_color)
      else:
        self.failMenu = Menu(self.engine, [
          (_(" Try Again?"), self.restartAfterFail),
          (_("  Give Up?"), self.changeAfterFail),
          (_("Quit to Main"), self.quit),
        ], fadeScreen = False, onCancel = self.changeAfterFail, font = self.engine.data.pauseFont, pos = (self.fail_text_x, self.fail_text_y), textColor = self.fail_text_color, selectedColor = self.fail_selected_color)
      FirstTime = True
      self.restartSong(FirstTime)
    elif self.theme == 2:   #RB-like theme
      size = self.engine.data.pauseFont.getStringSize("Quit to Main Menu")
      if self.careerMode:
        self.menu = Menu(self.engine, [
          (_("   RESUME"),       self.resumeSong),
          (_("   RESTART"),      self.restartSong),
          (_("   CHANGE SONG"),       self.changeSong),
          (_("   PRACTICE"),       self.practiceSong), #evilynux
          (_("   SETTINGS"),          settingsMenu),
          (_("   QUIT"), self.quit),
        ], fadeScreen = False, onClose = self.resumeGame, font = self.engine.data.pauseFont, pos = (self.pause_text_x, self.pause_text_y), textColor = self.pause_text_color, selectedColor = self.pause_selected_color)
      else:      
        self.menu = Menu(self.engine, [
          (_("   RESUME"),       self.resumeSong),
          (_("   RESTART"),      self.restartSong),
          (_("   CHANGE SONG"),       self.changeSong),
          (_("   END SONG"),          self.endSong),
          (_("   SETTINGS"),          settingsMenu),
          (_("   QUIT"), self.quit),
        ], fadeScreen = False, onClose = self.resumeGame, font = self.engine.data.pauseFont, pos = (self.pause_text_x, self.pause_text_y), textColor = self.pause_text_color, selectedColor = self.pause_selected_color)
      size = self.engine.data.pauseFont.getStringSize("Quit to Main")
      if self.careerMode:
        self.failMenu = Menu(self.engine, [
          (_(" TRY AGAIN?"), self.restartAfterFail),
          (_(" GIVE UP?"), self.changeAfterFail),
          (_(" PRACTICE?"), self.practiceSong), #evilynux
          (_(" QUIT"), self.quit),
        ], fadeScreen = False, onCancel = self.changeAfterFail, font = self.engine.data.pauseFont, pos = (self.fail_text_x, self.fail_text_y), textColor = self.fail_text_color, selectedColor = self.fail_selected_color)
      else:
        self.failMenu = Menu(self.engine, [
          (_(" TRY AGAIN?"), self.restartAfterFail),
          (_(" GIVE UP?"), self.changeAfterFail),
          (_(" QUIT"), self.quit),
        ], fadeScreen = False, onCancel = self.changeAfterFail, font = self.engine.data.pauseFont, pos = (self.fail_text_x, self.fail_text_y), textColor = self.fail_text_color, selectedColor = self.fail_selected_color)
      FirstTime = True
      self.restartSong(FirstTime)



  def pauseGame(self):
    if self.song:
      self.song.pause()
      self.pause = True
      self.guitars[0].paused = True
      if self.numOfPlayers == 2:
        self.guitars[1].paused = True

  def failGame(self):
    self.engine.view.pushLayer(self.failMenu)
    self.failEnd = True

  def resumeGame(self):
    self.loadSettings()
    self.setCamera()
    if self.song:
      self.song.unpause()
      self.pause = False
      self.guitars[0].paused = False
      if self.numOfPlayers == 2:
        self.guitars[1].paused = False

  def resumeSong(self):
    self.engine.view.popLayer(self.menu)
    self.resumeGame()
  
  def setCamera(self):
    #x=0 middle
    #x=1 rotate left
    #x=-1 rotate right
    #y=3 middle
    #y=4 rotate back
    #y=2 rotate front
    #z=-3

    if self.pov == 1:
      self.camera.target    = (0.0, 1.4, 1.8) #kk69:More like GH3
      self.camera.origin    = (0.0, 2.8*self.boardY, -3.6)
    elif self.pov == 2:
      self.camera.target    = (self.targetX, self.targetY, self.targetZ)
      self.camera.origin    = (self.originX, self.originY*self.boardY, self.originZ)
    elif self.pov == 3: #Racer
      self.camera.target    = (0.0, 0.0, 3.7)
      self.camera.origin    = (0.0, 2.9*self.boardY, -2.9)
    elif self.pov == 4: #Racer
      self.camera.target    = (0.0, 1.6, 2.0)
      self.camera.origin    = (0.0, 2.6*self.boardY, -3.6)
    elif self.pov == 5: #blazingamer
      self.camera.target    = (0.0, -6.0, 2.6666666666)
      self.camera.origin    = (0.0, 6.0, 2.6666666665)  
    elif self.pov == 6: #Blazingamer theme-dependant 
      if self.rmtype == 0:
        self.camera.target    = (0.0, 1.6, 2.0)
        self.camera.origin    = (0.0, 2.6*self.boardY, -3.6)
      elif self.rmtype == 1:
        self.camera.target    = (0.0, 1.4, 1.8) #kk69:More like GH3
        self.camera.origin    = (0.0, 2.8*self.boardY, -3.6)
      elif self.rmtype == 2:
        self.camera.target    = (0.0, 0.0, 3.7)
        self.camera.origin    = (0.0, 2.9*self.boardY, -2.9)
    else:
      self.camera.target    = (0.0, 0.0, 4.0)
      self.camera.origin    = (0.0, 3.0*self.boardY, -3.0)

    if self.rmtype == 3:
      self.camera.target    = (0.0, 1.4, 1.8) #kk69:More like GH3
      self.camera.origin    = (0.0, 2.8*self.boardY, -3.6)
           
  def freeResources(self):
    self.engine.view.setViewport(1,0)
    self.arrow = None
    self.counter = None
    self.failScreen = None
    self.failMsg = None
    self.menu = None
    self.mult = None
    self.pauseScreen = None
    self.rockTop = None
    self.rockMsg = None
    self.song = None
    self.rockOff = None
    if self.rmtype == 0:
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
      self.rockmeter = None
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
      self.scorePic = None
      self.scorePicP2 = None
      self.arrowP2 = None
      self.mult2 = None
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

    
  def loadSettings(self):
    self.stage.updateDelays()

    self.guitarVolume     = self.engine.config.get("audio", "guitarvol")
    self.songVolume       = self.engine.config.get("audio", "songvol")
    self.rhythmVolume     = self.engine.config.get("audio", "rhythmvol")
    self.screwUpVolume    = self.engine.config.get("audio", "screwupvol")
    self.killVolume    = self.engine.config.get("audio", "kill_volume")
    self.sfxVolume    = self.engine.config.get("audio", "SFX_volume")
    self.engine.data.sfxVolume = self.sfxVolume   #MFH - keep Data updated

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
      self.autoPlay         = self.engine.config.get("game", "jurgdef")

    self.hopoStyle        = self.engine.config.get("game", "hopo_style")
    self.hopoAfterChord = self.engine.config.get("game", "hopo_after_chord")

    self.pov              = self.engine.config.get("game", "pov")
    #CoffeeMod

    if self.numOfPlayers == 1:
      #De-emphasize non played part
      self.rhythmVolume *= 0.6
      
    for i,guitar in enumerate(self.guitars):
      guitar.leftyMode = self.engine.config.get("player%d" % (i), "leftymode")
      guitar.twoChordMax  = self.engine.config.get("player%d" % (i), "two_chord_max")

    if self.song:
      #myfingershurt: ensure that after a pause or restart, the a/v sync delay is refreshed:
      self.song.refreshAudioDelay()
      #myfingershurt: ensuring the miss volume gets refreshed:
      self.song.refreshMissVolume()
      self.song.setBackgroundVolume(self.songVolume)
      self.song.setRhythmVolume(self.rhythmVolume)
      self.song.setDrumVolume(self.rhythmVolume)
      
  def songLoaded(self, song):

    for i, player in enumerate(self.playerList):
      song.difficulty[i] = player.difficulty

  def endSong(self):
    self.engine.view.popLayer(self.menu)
    validScoreFound = False
    for i, thePlayer in enumerate(self.playerList):   #MFH - what if 2p (human) battles 1p (Jurgen / CPU)?  He needs a valid score too!
      if thePlayer.score > 0:
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


  def resetVariablesToDefaults(self):
    self.drumStart = False  #faaa's drum sound mod restart
    self.avMult = [0.0 for i in self.playerList]
    self.lastStars = [0 for i in self.playerList]
    #self.stars = [0,0]
    self.dispAccuracy = [False for i in self.playerList]
    for playaNum, thePlayer in enumerate(self.playerList): 
      thePlayer.stars = 0
      self.guitars[playaNum].spEnabled = True
    self.partialStar = [0 for i in self.playerList]
    self.resetStarThresholds()
    self.coOpScore = 0
    self.coOpStars = 0
    self.lastCoOpStars = 0
    self.coOpPartialStars = 0
    self.coOpNotesHit = 0
    self.mutedLastSecondYet = False
    self.dispSoloReview = [False for i in self.playerList]
    self.soloReviewCountdown = [0 for i in self.playerList]
    self.hitAccuracy = [0.0 for i in self.playerList]
    self.guitarSoloAccuracy = [0.0 for i in self.playerList]
    self.guitarSoloActive = [False for i in self.playerList]
    self.currentGuitarSolo = [0 for i in self.playerList]
    self.guitarSoloBroken = [False for i in self.playerList]
    self.failTimer = 0  #myfingershurt
    self.rockTimer = 0  #myfingershurt
    self.youRock = False    #myfingershurt
    self.rockFinished = False    #myfingershurt
    self.rock = [self.rockMax/2 for i in self.playerList]
    self.minusRock = [0.0 for i in self.playerList]
    self.plusRock = [0.0 for i in self.playerList]
    for i, thePlayer in enumerate(self.playerList):
      self.guitars[i].starPower = 0      
    self.failed = False
    self.finalFailed = False
    self.failEnd = False
    self.failTimer = 0
    self.rockTimer = 0  #myfingershurt
    self.youRock = False    #myfingershurt
    self.rockFinished = False    #myfingershurt
    ###Capo###
    if self.song:
      self.beatTime = []
      if (self.starClaps or self.beatClaps):
        for time, event in self.song.track[0].getAllEvents():
          if isinstance(event, Bars):
            if (event.barType == 1 or event.barType == 2):
              self.beatTime.append(time)
    ###endCapo###
  

  def restartSong(self, firstTime = False):  #QQstarS: Fix this function
    self.resetVariablesToDefaults()
    self.engine.data.startSound.play()
    self.engine.view.popLayer(self.menu)
    for player in self.playerList:
      player.reset()
    self.stage.reset()
    self.enteredCode     = []
    self.jurg1            = False #Jurgen hasn't played the restarted song =P
    self.jurg2            = False
    
    for guitar in self.guitars:
      guitar.twoChord = 0
      guitar.hopoActive = 0
      guitar.wasLastNoteHopod = False
      guitar.sameNoteHopoString = False
      guitar.hopoLast = -1
      guitar.guitarSolo = False
      guitar.currentGuitarSoloHitNotes = 0
      
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

    if not self.song:
      return
    
    # glorandwarf: the countdown is now the number of beats to run
    # before the song begins
    self.countdown = 4.0 * self.songBPS
    
    self.partySwitch = 0
    for i,guitar in enumerate(self.guitars):
      guitar.endPick(i)
    self.song.stop()

    for i, guitar in enumerate(self.guitars):
      #myfingershurt: preventing ever-thickening BPM lines after restarts
      if firstTime:
        self.song.track[i].markBars()
      #myfingershurt
      if self.hopoStyle > 0 or self.song.info.hopo == "on":
        
        #myfingershurt: drums :)
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

    
    self.lastEvent = lastTime + 1000
    self.lastEvent = round(self.lastEvent / 1000) * 1000
    #self.notesCum = 0
    self.noteLastTime = 0
            
  def restartAfterFail(self):  #QQstarS: Fix this function
    self.resetVariablesToDefaults()
    self.engine.data.startSound.play()
    self.engine.view.popLayer(self.failMenu)
    for player in self.playerList:
      player.reset()
    self.stage.reset()
    self.enteredCode     = []

    self.jurg1            = False #Jurgen hasn't played the restarted song =P
    self.jurg2            = False

    for guitar in self.guitars:
      guitar.twoChord = 0
      guitar.hopoActive = 0
      guitar.wasLastNoteHopod = False
      guitar.sameNoteHopoString = False
      guitar.hopoLast = -1
      guitar.guitarSolo = False
      guitar.currentGuitarSoloHitNotes = 0
      
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
    
    if not self.song:
      return
      
    # glorandwarf: the countdown is now the number of beats to run
    # before the song begins
    self.countdown = 4.0 * self.songBPS

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

  def handleWhammy(self, playerNum):
    i = playerNum
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
              if self.guitars[i].killPoints or (self.guitars[i].starPowerActive and self.whammySavesSP):
                self.guitars[i].starPower += self.analogKillswitchStarpowerChunkSize
                if self.guitars[i].starPower > 100:
                  self.guitars[i].starPower = 100
  
            self.lastWhammyVol[i] = self.whammyVol[i]
            
            #here, scale whammyVol to match kill volume setting:
            self.targetWhammyVol[i] = self.whammyVol[i] * (1.0 - self.killVolume)
  
            if self.actualWhammyVol[i] < self.targetWhammyVol[i]:
              self.actualWhammyVol[i] += self.whammyVolAdjStep
              whammyVolSet = 1.0 - self.actualWhammyVol[i]
              self.song.setInstrumentVolume(whammyVolSet, self.players[i].part)
            elif self.actualWhammyVol[i] > self.targetWhammyVol[i]:
              self.actualWhammyVol[i] -= self.whammyVolAdjStep
              whammyVolSet = 1.0 - self.actualWhammyVol[i]
              self.song.setInstrumentVolume(whammyVolSet, self.players[i].part)
            
          elif self.playerList[i].streak > 0:
            self.song.setInstrumentVolume(1.0, self.players[i].part)
            self.actualWhammyVol[i] = self.defaultWhammyVol[i]
  
        else:   #digital killswitch:
          if self.CheckForValidKillswitchNote(i):    #if a note has length and is being held enough to get score
            if self.killswitchEngaged[i] == True: #QQstarS:new Fix the killswitch
              if self.guitars[i].isKillswitchPossible() == True:
                self.killswitchEngaged[i] = True
                #self.song.setInstrumentVolume(0.0, self.players[i].part)
                self.song.setInstrumentVolume(self.killVolume, self.players[i].part)  #MFH
                if self.guitars[i].killPoints or (self.guitars[i].starPowerActive and self.whammySavesSP):
                  self.guitars[i].starPower += self.digitalKillswitchStarpowerChunkSize
                  if self.guitars[i].starPower > 100:
                    self.guitars[i].starPower = 100
                  
              else:
                self.killswitchEngaged[i] = None
            elif self.playerList[i].streak > 0:
              self.song.setInstrumentVolume(1.0, self.players[i].part)
              self.killswitchEngaged[i] = False
          elif self.playerList[i].streak > 0:
            self.song.setInstrumentVolume(1.0, self.players[i].part)
            self.killswitchEngaged[i] = False
          else:
            self.killswitchEngaged[i] = False
          
    except Exception, e:
      self.whammyVol[i] = self.defaultWhammyVol[i] 



  def handlePhrases(self, playerNum, playerStreak):
    if self.phrases == True:
  
      i = playerNum
      
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
        self.dislayTextScale[i] = self.scaleText[i] + self.scaleText2[i]
        if self.scaleText2[i] <= -0.0005:
          self.goingUP[i] = True
        elif self.scaleText2[i] >= 0.0005:
          self.goingUP[i] = False
        if self.goingUP[i]:
          self.scaleText2[i] += self.displayTextScaleStep2
        else:
          self.scaleText2[i] -= self.displayTextScaleStep2
      else:
        self.dislayTextScale[i] = self.scaleText[i]
  
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


  def handleJurgen(self, pos):
    #chordFudge = 1   #MFH - was 10 - #myfingershurt - needed to detect chords
    chordFudge = self.song.track[0].chordFudge
    
    if self.autoPlay:
      for i,guitar in enumerate(self.guitars):
  
        #Allow Jurgen per player...Spikehead777
        if i == 0: #Player 1
          if self.jurg == 1: #Player 2 only?
            continue #Next player
          self.jurg1 = True #Jurgen Played for Player 1
        elif i == 1: #Player 2
          if self.jurg == 0: #Player 1 only?
            continue #Next Player
          self.jurg2 = True #Jurgen Played for Player 2
        else: #All else
          continue #Next Player
  
        if self.jurgenLogic == 0:   #original FoF / RF-Mod style Jurgen Logic (cannot handle fast notes / can only handle 1 strum per notewindow)
          notes = guitar.getRequiredNotesMFH(self.song, pos)  #mfh - needed updatin' 
          notes = [note.number for time, note in notes]
          changed = False
          held = 0
          for n, k in enumerate(self.keysList[i]):
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
            if self.hopoStyle ==  1:   #1 = rf-mod
              self.doPick3RF(i)
            elif self.hopoStyle == 2 or self.hopoStyle == 3 or self.hopoStyle == 4:  #GH2 style HOPO 
              self.doPick3GH2(i)
            else:   #2 = no HOPOs
              self.doPick(i)
        
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
            if self.hopoStyle ==  1:   #1 = rf-mod
              self.doPick3RF(i)
            elif self.hopoStyle == 2 or self.hopoStyle == 3 or self.hopoStyle == 4:  #GH2 style HOPO 
              self.doPick3GH2(i)
            else:   #2 = no HOPOs
              self.doPick(i)
  
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
            if self.hopoStyle ==  1:   #1 = rf-mod
              self.doPick3RF(i)
            elif self.hopoStyle == 2 or self.hopoStyle == 3 or self.hopoStyle == 4:  #GH2 style HOPO 
              self.doPick3GH2(i)
            else:   #2 = no HOPOs
              self.doPick(i)
  
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
              if self.hopoStyle ==  1:   #1 = rf-mod
                self.doPick3RF(i)
              elif self.hopoStyle == 2 or self.hopoStyle == 3 or self.hopoStyle == 4:  #GH2 style HOPO 
                self.doPick3GH2(i)
              else:   #2 = no HOPOs
                self.doPick(i)
            #MFH - release all frets - who cares about held notes, I want a test player (actually if no keyReleased call, will hold notes fine)
            for n, k in enumerate(self.keysList[i]):
              if self.controls.getState(k):
                self.controls.toggle(k, False)
  

  def rockmeterDecrease(self, playerNum):
    i = playerNum
    if self.guitars[i].isDrum: 
      self.drumStart = True
    if self.battle and self.numOfPlayers > 1: #battle mode
      if self.starNotesMissed[i] or self.guitars[i].isStarPhrase:
        self.guitars[i].isStarPhrase = True
        self.guitars[i].spEnabled = False
        #self.guitars[i].spNote = False 
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
    
    #MFH TODO - maintain separate rock status for each player in co-op mode
    elif self.coOp and self.numOfPlayers > 1: #battle mode
      if self.starNotesMissed[i] or self.guitars[i].isStarPhrase:
        self.guitars[i].isStarPhrase = True
        self.guitars[i].spEnabled = False
        #self.guitars[i].spNote = False 
      if self.notesMissed[i]:
        self.minusRock[0] += self.minGain/self.multi[i]
        self.rock[0] -= self.minusRock[0]/self.multi[i]
        if self.plusRock[0] > self.pluBase:
          self.plusRock[0] -= self.pluGain*2.0/self.multi[i]
        if self.plusRock[0] <= self.pluBase:
          self.plusRock[0] = self.pluBase/self.multi[i]
      if self.lessMissed[i]:
        self.minusRock[0] += self.minGain/5.0/self.multi[i]
        self.rock[0] -= self.minusRock[0]/5.0/self.multi[i]
        if self.plusRock[0] > self.pluBase:
          self.plusRock[0] -= self.pluGain/2.5/self.multi[i]
    
    else:   #normal mode
      if self.starNotesMissed[i] or self.guitars[i].isStarPhrase:
        self.guitars[i].isStarPhrase = True
        self.guitars[i].spEnabled = False
        #self.guitars[i].spNote = False 
      if self.notesMissed[i]:
        self.minusRock[i] += self.minGain/self.multi[i]
        self.rock[i] -= self.minusRock[i]/self.multi[i]
        if self.plusRock[i] > self.pluBase:
          self.plusRock[i] -= self.pluGain*2.0/self.multi[i]
        if self.plusRock[i] <= self.pluBase:
          self.plusRock[i] = self.pluBase/self.multi[i]
      if self.lessMissed[i]:
        self.minusRock[i] += self.minGain/5.0/self.multi[i]
        self.rock[i] -= self.minusRock[i]/5.0/self.multi[i]
        if self.plusRock[i] > self.pluBase:
          self.plusRock[i] -= self.pluGain/2.5/self.multi[i]

    if self.minusRock[i] <= self.minBase:
      self.minusRock[i] = self.minBase
    if self.plusRock[i] <= self.pluBase:
      self.plusRock[i] = self.pluBase



  def rockmeterIncrease(self, playerNum):
    i = playerNum
    if self.guitars[i].isDrum: 
      self.drumStart = True
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
    elif self.coOp and self.numOfPlayers > 1: 
      if self.rock[0] < self.rockMax:
        self.plusRock[0] += self.pluGain*self.multi[i]
        self.rock[0] += self.plusRock[0]*self.multi[i]
      if self.rock[0] >= self.rockMax:
        self.rock[0] = self.rockMax
      if self.minusRock[0] > self.minBase:
        self.minusRock[0] -= self.minGain/2.0*self.multi[i]
    
    else:   #normal mode
      if self.rock[i] < self.rockMax:
        self.plusRock[i] += self.pluGain*self.multi[i]
        self.rock[i] += self.plusRock[i]*self.multi[i]
      if self.rock[i] >= self.rockMax:
        self.rock[i] = self.rockMax
      if self.minusRock[i] > self.minBase:
        self.minusRock[i] -= self.minGain/2.0*self.multi[i]

    if self.minusRock[i] <= self.minBase:
      self.minusRock[i] = self.minBase
    if self.plusRock[i] <= self.pluBase:
      self.plusRock[i] = self.pluBase


  def run(self, ticks): #QQstarS: Fix this funcion
    SceneClient.run(self, ticks)
    
    #MFH - testing new traceback logging:
    #raise TypeError
    
    # update song
    #if self.song:
    if self.song and not self.pause and not self.failed:
      pos = self.getSongPosition()
      self.song.update(ticks)
      # update stage

      #MFH - new failing detection logic
      if self.failingEnabled:
        #if self.numOfPlayers > 1:
        #MFH TODO - maintain separate rock status, just combine into single rockmeter (2 arrows) for RB theme
        # this will also allow separate failing, and saving with starpower
        if self.numOfPlayers > 1 and self.coOp:
          if self.rock[0] <= 0:
            self.failed = True
        else:
          somebodyStillAlive = False
          for i, player in enumerate(self.playerList):
            if self.rock[i] > 0:
              somebodyStillAlive = True
          if not somebodyStillAlive:    #only if everybody has failed
            self.failed = True
      
      #if self.rock[0] <= 0 and self.numOfPlayers>1 and self.rock[1] <= 0 and self.failingEnabled: #QQstarS: all two are "die" that failing
      #  self.failed = True
      #elif self.rock[0] <= 0 and self.numOfPlayers<=1 and self.failingEnabled: #QQstarS: one player, die,failed
      #  self.failed = True
      
      
      for i,guitar in enumerate(self.guitars):  #QQstarS:add the for loop to let it do with both player
        self.stage.run(pos, self.guitars[i].currentPeriod)  #QQstarS:Set [0] to [i]

        if self.guitars[i].starPowerGained == True:  #QQstarS:Set [0] to [i]
          #myfingershurt: auto drum starpower activation option:
          if guitar.isDrum and self.autoDrumStarpowerActivate:
            self.activateSP(i)
          if self.guitars[i].starPower >= 50:
            self.engine.data.starReadySound.play()
          else:
            self.engine.data.starSound.play()
            


          self.guitars[i].starPowerGained = False  #QQstarS:Set [0] to [i]
          if self.phrases == True and self.guitars[i].starPower >= 50:  #QQstarS:Set [0] to [i]
            self.newScalingText(i, self.tsStarPowerReady )

#-            if self.theme == 0 or self.theme == 1:
#-              #self.displayText[i] = _("Star Power Ready") #kk69: more GH3-like
#-              self.newScalingText(i, _("Star Power Ready") )
#-              #self.streakFlag = "%d" % (i)  #QQstarS:Set  the flag
#-            elif self.theme == 2:
#-              #self.displayText[i] = _("Overdrive Ready") #kk69: more GH3-like, even though it's RB (just for people who use phrases on RB theme)
#-              self.newScalingText(i, _("Overdrive Ready") )
#-              #self.streakFlag = "%d" % (i) #QQstarS:Set the flag

      # update board
      #for i,guitar in enumerate(self.guitars):
        if not guitar.run(ticks, pos, self.controls):
          # done playing the current notes
          self.endPick(i)

        missedNotes = guitar.getMissedNotesMFH(self.song, pos)
        if missedNotes:
          if guitar.isDrum:
            self.drumStart = True
          self.lessMissed[i] = True  #QQstarS:Set [0] to [i]
          for tym, theNote in missedNotes:  #MFH
            if theNote.star or theNote.finalStar:
              self.starNotesMissed[i] = True
        
        if (self.playerList[i].streak != 0 or not self.processedFirstNoteYet) and not guitar.playedNotes and len(missedNotes) > 0:
          if not self.processedFirstNoteYet:
            self.stage.triggerMiss(pos)
            self.notesMissed[i] = True
          self.processedFirstNoteYet = True
          self.playerList[i].streak = 0
          self.currentlyAnimating = False
          guitar.setMultiplier(1)
          guitar.hopoLast = -1
          self.song.setInstrumentVolume(0.0, self.players[i].part)
          self.guitarSoloBroken[i] = True
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
        self.handlePhrases(playerNum, thePlayer.streak)
      self.handleJurgen(pos)

      #stage rotation
      #MFH - logic to prevent advancing rotation frames if you have screwed up, until you resume a streak
      if (self.currentlyAnimating and self.missPausesAnim == 1) or self.missPausesAnim == 0:
        self.stage.rotate()
       
      #MFH - new logic to update the starpower pre-multiplier
      for i, thePlayer in enumerate(self.playerList):
        if self.guitars[i].starPowerActive: 
          self.multi[i] = 2
        else:
          self.multi[i] = 1

        #MFH - rewritten rockmeter / starpower miss logic, and Faaa's drum sounds:
        #the old logic was ridiculously complicated (see below commented block).  
      # For each existing player (already in this loop)
        if self.notesMissed[i] or self.lessMissed[i]:   #(detects missed note or overstrum)
          if self.guitars[i].isDrum:
            if self.drumMisses == 0:    #mode: always
              self.rockmeterDecrease(i)
            elif self.drumMisses == 1 and self.countdownSeconds < 1:    #mode: song start
              self.rockmeterDecrease(i)
            elif self.drumMisses == 2 and self.drumStart:    #mode: song start
              self.rockmeterDecrease(i)
          else:   #not drums
            self.rockmeterDecrease(i)
        if self.notesHit[i]:
          self.rockmeterIncrease(i)

        self.notesMissed[i] = False 
        self.starNotesMissed[i] = False
        self.notesHit[i] = False 
        self.lessMissed[i] = False 



        #battle failing
        if self.battle and self.numOfPlayers>1:
          if self.rock[i] <= 0:
            #self.displayText[i] = "You Failed!!!!"
            #self.newScalingText(i, _("You Failed!!!!") )
            self.newScalingText(i, self.tsYouFailedBattle )
            #self.streakFlag = str(i)   #QQstarS:Set [0] to [i] #if player0 streak50, set the flag to 1. 
            self.guitars[i].actions = [0,0,0]


      if self.countdown > 0: #MFH won't start song playing if you failed or pause
        self.countdown = max(self.countdown - ticks / self.song.period, 0)
        self.countdownSeconds = self.countdown / self.songBPS + 1
        
        if not self.countdown:  #MFH - when countdown reaches zero, will only be executed once
          #RF-mod should we collect garbage when we start?
          self.engine.collectGarbage()
          self.song.setGuitarVolume(self.guitarVolume)
          self.song.setBackgroundVolume(self.songVolume)
          self.song.setRhythmVolume(self.rhythmVolume)
          if self.playerList[0].practiceMode:
            self.playerList[0].startPos[0] -= self.song.period*4
            if self.playerList[0].startPos[0] < 0.0:
              self.playerList[0].startPos[0] = 0.0
            self.song.play(start = self.playerList[0].startPos[0])
          else:
            self.song.play()

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
      self.players[num].addScore(scoreTemp)
      self.coOpScore += (scoreTemp*self.players[num].getScoreMultiplier())
      

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
      
    self.engine.view.setViewport(1,0)

  def getSongPosition(self):
    if self.song:
      if not self.done:
        self.lastSongPos = self.song.getPosition()
        return self.lastSongPos - self.countdown * self.song.period
      else:
        # Nice speeding up animation at the end of the song
        return self.lastSongPos + 4.0 * (1 - self.visibility) * self.song.period
    return 0.0


  def screwUp(self, num):
    if self.screwUpVolume > 0.0:
      #self.sfxChannel.setVolume(self.screwUpVolume)
      #if `self.playerList[num].part` == "Bass Guitar":
      if self.guitars[num].isBassGuitar:
        #self.sfxChannel.play(self.engine.data.screwUpSoundBass)
        self.engine.data.screwUpSoundBass.play()
      elif self.guitars[num].isDrum:
        if self.drumMisses > 0: #MFH's cleaned-up - Faaa Drum sound
          if self.guitars[num].lastFretWasT1:
            self.engine.data.T1DrumSound.play()
          elif self.guitars[num].lastFretWasT2:
            self.engine.data.T2DrumSound.play()
          elif self.guitars[num].lastFretWasT3:
            self.engine.data.T3DrumSound.play()
          elif self.guitars[num].lastFretWasC:
            self.engine.data.CDrumSound.play()
        else:
          self.engine.data.screwUpSoundDrums.play()
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

    
    self.killswitchEngaged[num] = False   #always reset killswitch status when picking / tapping
    if self.guitars[num].startPick(self.song, pos, self.controls):
      if self.guitars[num].isDrum:
        self.drumStart = True
      self.song.setInstrumentVolume(self.guitarVolume, self.playerList[num].part)
      self.currentlyAnimating = True
      self.playerList[num].streak += 1

      self.notesHit[num] = True #QQstarS:Set [0] to [i]
      
      self.playerList[num].notesHit += 1  # glorandwarf: was len(self.guitars[num].playedNotes)
      tempScoreValue = len(self.guitars[num].playedNotes) * 50 * self.multi[num]
      self.playerList[num].addScore(tempScoreValue) 
      
      if self.coOp:
        self.coOpScore += (tempScoreValue*self.players[num].getScoreMultiplier())
        self.coOpNotesHit += 1
        self.updateStars(self.coOpPlayerIndex)
      else:
        self.updateStars(num)
      
      self.updateAvMult(num)
      
      
      self.stage.triggerPick(pos, [n[1].number for n in self.guitars[num].playedNotes])
      if self.playerList[num].streak % 10 == 0:
        self.lastMultTime[num] = pos
        self.guitars[num].setMultiplier(self.playerList[num].getScoreMultiplier())

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
      self.song.setInstrumentVolume(0.0, self.playerList[num].part)
      self.playerList[num].streak = 0
      self.guitars[num].setMultiplier(1)
      self.currentlyAnimating = False
      self.stage.triggerMiss(pos)
      self.guitarSoloBroken[num] = True

      self.notesMissed[num] = True #QQstarS:Set [0] to [i]

      isFirst = True
      noteList = self.guitars[num].matchingNotes
      for tym, noat in noteList:
        if (noat.star or noat.finalStar) and isFirst:
          self.starNotesMissed[num] = True
        isFirst = False

      self.screwUp(num) #MFH - call screw-up sound handling function

      #myfingershurt: ensure accuracy display off when miss
      self.dispAccuracy[num] = False

    #myfingershurt: bass drum sound play
    if self.guitars[num].isDrum and self.bassKickSoundEnabled:
      if self.guitars[num].lastFretWasBassDrum:
        #self.sfxChannel.setVolume(self.screwUpVolume)
        self.engine.data.bassDrumSound.play()


  def doPick2(self, num, hopo = False):
    if not self.song:
      return
  
    pos = self.getSongPosition()
    #clear out any missed notes before this pick since they are already missed by virtue of the pick
    missedNotes = self.guitars[num].getMissedNotes(self.song, pos, catchup = True)

    if len(missedNotes) > 0:
      self.processedFirstNoteYet = True
      self.playerList[num].streak = 0
      self.guitars[num].setMultiplier(1)
      self.guitars[num].hopoActive = 0
      self.guitars[num].wasLastNoteHopod = False
      self.guitars[num].hopoLast = -1
      self.guitarSoloBroken[num] = True

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
        self.playerList[num].streak += 1
        self.currentlyAnimating = True

        self.notesHit[num] = True #QQstarS:Set [0] to [i]
        
      self.playerList[num].notesHit += 1  # glorandwarf: was len(self.guitars[num].playedNotes)
      tempScoreValue = len(self.guitars[num].playedNotes) * 50 * self.multi[num]
      self.playerList[num].addScore(tempScoreValue)
      
      if self.coOp:
        self.coOpScore += (tempScoreValue*self.players[num].getScoreMultiplier())
        self.coOpNotesHit += 1
        self.updateStars(self.coOpPlayerIndex)
      else:
        self.updateStars(num)
      
      self.updateAvMult(num)
      self.stage.triggerPick(pos, [n[1].number for n in self.guitars[num].playedNotes])    
      if self.players[num].streak % 10 == 0:
        self.lastMultTime[num] = self.getSongPosition()
        self.guitars[num].setMultiplier(self.playerList[num].getScoreMultiplier())
        

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
      self.playerList[num].streak = 0
      self.guitars[num].setMultiplier(1)
      self.stage.triggerMiss(pos)
      self.guitarSoloBroken[num] = True

      self.notesMissed[num] = True #QQstarS:Set [0] to [i]

      
      
      isFirst = True
      noteList = self.guitars[num].matchingNotes
      for tym, noat in noteList:
        if (noat.star or noat.finalStar) and isFirst:
          self.starNotesMissed[num] = True
        isFirst = False
      
      self.screwUp(num)

#-----------------------
  def doPick3RF(self, num, hopo = False):
    if not self.song:
      return
  
    pos = self.getSongPosition()
    #clear out any past the window missed notes before this pick since they are already missed by virtue of the pick
    missedNotes = self.guitars[num].getMissedNotes(self.song, pos, catchup = True)

    if len(missedNotes) > 0:
      self.processedFirstNoteYet = True
      self.playerList[num].streak = 0
      self.guitars[num].setMultiplier(1)
      self.guitars[num].hopoActive = 0
      self.guitars[num].wasLastNoteHopod = False
      self.guitars[num].hopoLast = -1
      self.guitarSoloBroken[num] = True

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
        self.playerList[num].streak = 0
        self.guitarSoloBroken[num] = True

        self.notesMissed[num] = True  #qqstars

        for chord in self.guitars[num].missedNotes:
          for tym, theNote in chord:  #MFH
            if theNote.star or theNote.finalStar:
              self.starNotesMissed[num] = True
        
      isFirst = True
      noteList = self.guitars[num].playedNotes
      for tym, noat in noteList:
        if noat.star and isFirst:
          self.guitars[num].isStarPhrase = True
        isFirst = False

      self.playerList[num].streak += 1
      self.notesHit[num] = True #qqstars

      self.currentlyAnimating = True        
      self.playerList[num].notesHit += 1  # glorandwarf: was len(self.guitars[num].playedNotes)
      tempScoreValue = len(self.guitars[num].playedNotes) * 50 * self.multi[num]
      self.playerList[num].addScore(tempScoreValue)
      
      if self.coOp:
        self.coOpScore += (tempScoreValue*self.players[num].getScoreMultiplier())
        self.coOpNotesHit += 1
        self.updateStars(self.coOpPlayerIndex)
      else:
        self.updateStars(num)
      
      self.updateAvMult(num)

      self.stage.triggerPick(pos, [n[1].number for n in self.guitars[num].playedNotes])    
      if self.players[num].streak % 10 == 0:
        self.lastMultTime[num] = self.getSongPosition()
        self.guitars[num].setMultiplier(self.playerList[num].getScoreMultiplier())
        
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
      self.playerList[num].streak = 0
      self.guitarSoloBroken[num] = True
      self.guitars[num].setMultiplier(1)
      self.stage.triggerMiss(pos)

      self.notesMissed[num] = True  #qqstars

      isFirst = True
      noteList = self.guitars[num].matchingNotes
      for tym, noat in noteList:
        if (noat.star or noat.finalStar) and isFirst:
          self.starNotesMissed[num] = True
        isFirst = False

      self.screwUp(num)
      
      #myfingershurt: ensure accuracy display off when miss
      self.dispAccuracy[num] = False


#-----------------------
  def doPick3GH2(self, num, hopo = False, pullOff = False): #MFH - so DoPick knows when a pull-off was performed
    if not self.song:
      return
  
    chordFudge = 1  #MFH - was 10  #myfingershurt - needed to detect chords
    
    pos = self.getSongPosition()

    missedNotes = self.guitars[num].getMissedNotesMFH(self.song, pos, catchup = True)
    if len(missedNotes) > 0:
      self.processedFirstNoteYet = True
      self.playerList[num].streak = 0
      self.guitarSoloBroken[num] = True
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
          self.starNotesMissed[num] = True
      
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
      
        self.playerList[num].streak = 0
        self.guitarSoloBroken[num] = True
        self.notesMissed[num] = True #QQstarS:Set [0] to [i]

        for chord in self.guitars[num].missedNotes:
          for tym, theNote in chord:  #MFH
            if theNote.star or theNote.finalStar:
              self.starNotesMissed[num] = True
        
      isFirst = True
      noteList = self.guitars[num].playedNotes
      for tym, noat in noteList:
        if noat.star and isFirst:
          self.guitars[num].isStarPhrase = True
        isFirst = False

      self.playerList[num].streak += 1
      self.notesHit[num] = True #QQstarS:Set [0] to [i]
      self.currentlyAnimating = True        

      self.playerList[num].notesHit += 1  # glorandwarf: was len(self.guitars[num].playedNotes)
      tempScoreValue = len(self.guitars[num].playedNotes) * 50 * self.multi[num]
      self.playerList[num].addScore(tempScoreValue)
      
      if self.coOp:
        self.coOpScore += (tempScoreValue*self.players[num].getScoreMultiplier())
        self.coOpNotesHit += 1
        self.updateStars(self.coOpPlayerIndex)
      else:
        self.updateStars(num)
      
      self.updateAvMult(num)
      self.stage.triggerPick(pos, [n[1].number for n in self.guitars[num].playedNotes])    
      if self.players[num].streak % 10 == 0:
        self.lastMultTime[num] = self.getSongPosition()
        self.guitars[num].setMultiplier(self.playerList[num].getScoreMultiplier())
      
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

      if (self.hopoStyle == 3 and hopo == True):  #GH2 Sloppy
        ApplyPenalty = False

      if (self.hopoStyle == 4 and hopo == True):  #GH2
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
        self.playerList[num].streak = 0
        self.guitarSoloBroken[num] = True
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
            self.starNotesMissed[num] = True
          isFirst = False

        self.screwUp(num)

        self.dispAccuracy[num] = False

    #myfingershurt: bass drum sound play
    if self.guitars[num].isDrum and self.bassKickSoundEnabled:
      if self.guitars[num].lastFretWasBassDrum:
        self.engine.data.bassDrumSound.play()

  def activateSP(self, num): #QQstarS: Fix this function, add a element "num"
    if self.guitars[num].starPower >= 50 and self.guitars[num].starPowerActive == False: #QQstarS:Set [0] to [i]
      #self.sfxChannel.setVolume(self.sfxVolume)
      if self.engine.data.cheerSoundFound:
        self.engine.data.crowdSound.play()
      self.engine.data.starActivateSound.play()
      self.guitars[num].starPowerActive = True #QQstarS:Set [0] to [i]
      self.guitars[num].overdriveFlashCount = 0  #MFH - this triggers the oFlash strings & timer
      self.guitars[num].ocount = 0  #MFH - this triggers the oFlash strings & timer

  def goToResults(self):
    self.ending = True
    if self.song:
      self.song.stop()
      self.done  = True
      for i,guitar in enumerate(self.guitars):
        self.playerList[i].twoChord = guitar.twoChord

        if self.playerList[0].practiceMode:
          self.playerList[i].score = 0

        #Reset Score if Jurgen played -- Spikehead777
        if i == 0 and self.jurg1:
          self.playerList[i].score = 0
        elif i == 1 and self.jurg2:
          self.playerList[i].score = 0


      noScore = False

      if self.playerList[0].score == 0:
        if self.numOfPlayers == 1:
          noScore = True
          self.changeSong()
      
      if self.numOfPlayers == 2:
        if self.playerList[0].score == 0 and self.playerList[1].score == 0:
          noScore = True
          self.changeSong()
      
      
      if not noScore:

        #coolguy567 - completing a song in career mode
        if self.careerMode and not self.song.info.completed:
          Log.debug("Song completed")
          songInfo = self.song.info
          songInfo.completed = True
          songInfo.save()
        
        #MFH - force one star scoring update before gameresults just in case star scoring is disabled:
        for i, thePlayer in enumerate(self.playerList):
          self.updateStars(i, forceUpdate = True)


        self.engine.view.setViewport(1,0)
        self.session.world.deleteScene(self)
        self.freeResources()
        self.session.world.createScene("GameResultsScene", libraryName = self.libraryName, songName = self.songName, players = self.playerList)

  def keyPressed(self, key, unicode, control = None):
    #RF style HOPO playing
    
    #myfingershurt: drums :)
    if self.guitars[0].isDrum and control in (self.guitars[0].keys):
      self.doPick(0)
      return True  
    elif self.numOfPlayers > 1 and self.guitars[1].isDrum and control in (self.guitars[1].keys):
      self.doPick(1)
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
        self.keyBurstTimeout[num] = self.engine.timer.time + self.keyBurstPeriod
        return True

    if control in (self.guitars[num].actions) and self.song:
      self.doPick(num)
    elif control in self.keysList[num] and self.song:
      # Check whether we can tap the currently required notes
      pos   = self.getSongPosition()
      notes = self.guitars[num].getRequiredNotes(self.song, pos)

      if self.playerList[num].streak > 0 and \
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

        if not pullOff and (self.hopoStyle == 2 or self.hopoStyle == 4): #GH2 or GH2 Strict, don't allow lower-fret tapping while holding a higher fret

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

        if not pullOff and (self.hopoStyle == 2 or self.hopoStyle == 4): #GH2 or GH2 Strict, don't allow lower-fret tapping while holding a higher fret

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
      if self.hopoStyle ==  1:   #1 = rf-mod
        self.doPick3RF(pressed, hopo)
      elif self.hopoStyle == 2 or self.hopoStyle == 3 or self.hopoStyle == 4:  #GH2 style HOPO 
        self.doPick3GH2(pressed, hopo, pullOff)
      else:   #2 = no HOPOs
        self.doPick(pressed)
      
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
    if not self.song:
      return 0
 
    noteCount  = len(self.guitars[num].playedNotes)
    pickLength = self.guitars[num].getPickLength(self.getSongPosition())
    if pickLength > 1.1 * self.song.period / 4:
      tempExtraScore = .1 * pickLength * noteCount
      if self.starScoreUpdates == 1:
        if self.coOp:
          self.updateStars(self.coOpPlayerIndex, tempExtraScore = tempExtraScore)
        else:
          self.updateStars(num, tempExtraScore = tempExtraScore)
      return int(tempExtraScore)   #original FoF sustain scoring
    return 0

  def keyReleased(self, key):
    #RF style HOPO playing
  
    control = self.controls.keyReleased(key)
    num = self.getPlayerNum(control) 

    #myfingershurt: drums :)
    #MFH - cleaning up Faaa's drum tracking code: (which appears to determine which drum fret after key release?  TODO: why not before?)
    if self.guitars[num].isDrum and control in (self.guitars[num].keys):
      if not self.controls.getState(self.guitars[num].keys[0]):
        self.guitars[num].lastFretWasBassDrum = False
      return True
      if not self.controls.getState(self.guitars[num].keys[1]):
        self.guitars[num].lastFretWasT1 = False
      return True
      if not self.controls.getState(self.guitars[num].keys[2]):
        self.guitars[num].lastFretWasT2 = False
      return True  
      if not self.controls.getState(self.guitars[num].keys[3]):
        self.guitars[num].lastFretWasT3 = False
      return True    	  
      if not self.controls.getState(self.guitars[num].keys[4]):
        self.guitars[num].lastFretWasC = False
      return True    	  


    #myfingershurt:
  
    if self.hopoStyle > 0:  #hopos enabled
      res = self.keyReleased3(key)
      return res


    if control in self.keysList[num] and self.song:
      # Check whether we can tap the currently required notes
      pos   = self.getSongPosition()
      notes = self.guitars[num].getRequiredNotes(self.song, pos)

      if self.playerList[num].streak > 0 and \
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
  def initializeStarScoringThresholds(self):
    #so, a 1.0x multiplier's score would be self.playerList[playerNum].totalNotes*50.0
    #a 2.0x multiplier's score would be (2.0)(self.playerList[playerNum].totalNotes*50.0)
    #and so on...

    #for playerNum, thePlayer in enumerate(self.playerList):
    
    self.starThresholdsP1 = []  #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>)
    self.starThresholdsP2 = []  #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>)
    self.starThresholdIndex = []
    self.nextScoreThreshold = []
    self.nextHitNotesThreshold = []
    self.nextStar = []
    self.nextPartialStar = []
    self.maxStarThresholdIndex = []
    self.avg1xScore = []
    self.finalScoreThreshold = []
    self.finalHitNotesThreshold = []

    #MFH - add separate co-op star scoring structure
    #  must maintain separate scores and star scores for uploading and highscore saving
    #  and a setting to not play star ding sounds when catching up at end of song 
    #    (co op mode will catch up and calculate individual star scores here at the end of a song)
    #  Only display co-op score and star score for co-op mode; hide individual scores & stars
    self.coOpScore = 0
    self.coOpStars = 0
    self.lastCoOpStars = 0
    self.coOpPartialStars = 0
    self.coOpNotesHit = 0
    self.starThresholdsCoOp = []
    self.coOpTotalStreakNotes = 0
    self.coOpPlayerIndex = len(self.playerList)
    #if self.coOp:

    
    #player1:
    playerNum = 0
    self.avg1xScore.append(self.playerList[playerNum].totalNotes*50.0)
    baseScore = self.avg1xScore[playerNum]
    self.starThresholdIndex.append(0)
    self.nextScoreThreshold.append(0)
    self.nextHitNotesThreshold.append(0)
    self.nextStar.append(0)
    self.nextPartialStar.append(0)
    self.maxStarThresholdIndex.append(0)
    self.finalScoreThreshold.append(0)
    self.finalHitNotesThreshold.append(0)

    if self.starScoring == 1:     #GH style scoring
      #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (0, 0, int(0.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - first always all 0's
      self.starThresholdsP1.append( (1, 0, int(0.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - first threshold(s) to surpass
      self.starThresholdsP1.append( (1, 1, int(0.05*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (1, 2, int(0.10*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (1, 3, int(0.15*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (1, 4, int(0.20*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (1, 5, int(0.25*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (1, 6, int(0.30*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (1, 7, int(0.35*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (2, 0, int(0.40*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (2, 1, int(0.50*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (2, 2, int(0.60*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (2, 3, int(0.70*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (2, 4, int(0.80*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (2, 5, int(0.90*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (2, 6, int(1.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (2, 7, int(1.10*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (3, 0, int(1.20*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (3, 1, int(1.30*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (3, 2, int(1.40*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (3, 3, int(1.50*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (3, 4, int(1.60*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (3, 5, int(1.70*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (3, 6, int(1.80*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (3, 7, int(1.90*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (4, 0, int(2.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (4, 1, int(2.10*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (4, 2, int(2.20*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (4, 3, int(2.30*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (4, 4, int(2.40*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (4, 5, int(2.50*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (4, 6, int(2.60*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (4, 7, int(2.70*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (5, 0, int(2.80*baseScore), int(0.90*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (6, 0, int(0.00*baseScore), int(1.00*self.playerList[playerNum].totalStreakNotes) ) )
  
        
    elif self.starScoring == 2 or self.starScoring == 3:   #RB style scoring
      #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (0, 0, int(0.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - first always all 0's
      self.starThresholdsP1.append( (0, 1, int(0.03125*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (0, 2, int(0.0625*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (0, 3, int(0.09375*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (0, 4, int(0.125*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (0, 5, int(0.15625*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (0, 6, int(0.1875*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (0, 7, int(0.21875*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (1, 0, int(0.25*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (1, 1, int(0.28125*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (1, 2, int(0.3125*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (1, 3, int(0.34375*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (1, 4, int(0.375*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (1, 5, int(0.40625*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (1, 6, int(0.4375*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (1, 7, int(0.46875*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (2, 0, int(0.5*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (2, 1, int(0.5625*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (2, 2, int(0.625*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (2, 3, int(0.6875*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (2, 4, int(0.75*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (2, 5, int(0.8125*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (2, 6, int(0.875*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (2, 7, int(0.9375*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (3, 0, int(1.0*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (3, 1, int(1.125*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (3, 2, int(1.25*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (3, 3, int(1.375*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (3, 4, int(1.5*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (3, 5, int(1.625*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (3, 6, int(1.75*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (3, 7, int(1.875*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (4, 0, int(2.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (4, 1, int(2.125*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (4, 2, int(2.25*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (4, 3, int(2.375*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (4, 4, int(2.5*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (4, 5, int(2.625*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (4, 6, int(2.75*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (4, 7, int(2.875*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      self.starThresholdsP1.append( (5, 0, int(3.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      if self.guitars[playerNum].isBassGuitar:
        #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP1.append( (6, 0, int(4.80*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      elif self.guitars[playerNum].isDrum:
        #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP1.append( (6, 0, int(4.65*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
      else:   #guitar parts
        #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP1.append( (6, 0, int(5.30*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )

      if self.starScoring == 3:   #if RB+GH scoring, 100% automatically skips you to 6 stars
        self.starThresholdsP1.append( (6, 0, int(0.00*baseScore), int(1.00*self.playerList[playerNum].totalStreakNotes) ) )
  
    else:   #0 = FoF scoring
      #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (0, 0, int(0.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - first always all 0's
      self.starThresholdsP1.append( (1, 0, int(0.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (1, 1, int(0.00*baseScore), int(0.03125*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (1, 2, int(0.00*baseScore), int(0.0625*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (1, 3, int(0.00*baseScore), int(0.09375*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (1, 4, int(0.00*baseScore), int(0.125*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (1, 5, int(0.00*baseScore), int(0.15625*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (1, 6, int(0.00*baseScore), int(0.1875*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (1, 7, int(0.00*baseScore), int(0.21875*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (2, 0, int(0.00*baseScore), int(0.25*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (2, 1, int(0.00*baseScore), int(0.28125*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (2, 2, int(0.00*baseScore), int(0.3125*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (2, 3, int(0.00*baseScore), int(0.34375*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (2, 4, int(0.00*baseScore), int(0.375*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (2, 5, int(0.00*baseScore), int(0.40625*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (2, 6, int(0.00*baseScore), int(0.4375*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (2, 7, int(0.00*baseScore), int(0.46875*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (3, 0, int(0.00*baseScore), int(0.50*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (3, 1, int(0.00*baseScore), int(0.53125*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (3, 2, int(0.00*baseScore), int(0.5625*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (3, 3, int(0.00*baseScore), int(0.59375*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (3, 4, int(0.00*baseScore), int(0.625*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (3, 5, int(0.00*baseScore), int(0.65625*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (3, 6, int(0.00*baseScore), int(0.6875*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (3, 7, int(0.00*baseScore), int(0.71875*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (4, 0, int(0.00*baseScore), int(0.75*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (4, 1, int(0.00*baseScore), int(0.775*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (4, 2, int(0.00*baseScore), int(0.80*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (4, 3, int(0.00*baseScore), int(0.825*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (4, 4, int(0.00*baseScore), int(0.85*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (4, 5, int(0.00*baseScore), int(0.875*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (4, 6, int(0.00*baseScore), int(0.90*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (4, 7, int(0.00*baseScore), int(0.925*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (5, 0, int(0.00*baseScore), int(0.95*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
      self.starThresholdsP1.append( (6, 0, int(0.00*baseScore), int(1.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass

    self.maxStarThresholdIndex[playerNum]=len(self.starThresholdsP1) - 1
    self.getNextStarThresholds(playerNum)   #start it at the first threshold pair to surpass
    tempFS, tempPS, self.finalScoreThreshold[playerNum], self.finalHitNotesThreshold[playerNum] = self.starThresholdsP1[-1]

    #--------
    if self.numOfPlayers > 1:   #repeat above for second array of thresholds
      #player2:
      playerNum = 1
      self.avg1xScore.append(self.playerList[playerNum].totalNotes*50.0)
      baseScore = self.avg1xScore[playerNum]
      self.starThresholdIndex.append(0)
      self.nextScoreThreshold.append(0)
      self.nextHitNotesThreshold.append(0)
      self.nextStar.append(0)
      self.nextPartialStar.append(0)
      self.maxStarThresholdIndex.append(0)
      self.finalScoreThreshold.append(0)
      self.finalHitNotesThreshold.append(0)
  
      if self.starScoring == 1:     #GH style scoring
        #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (0, 0, int(0.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - first always all 0's
        self.starThresholdsP2.append( (1, 0, int(0.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - first threshold(s) to surpass
        self.starThresholdsP2.append( (1, 1, int(0.05*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (1, 2, int(0.10*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (1, 3, int(0.15*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (1, 4, int(0.20*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (1, 5, int(0.25*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (1, 6, int(0.30*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (1, 7, int(0.35*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (2, 0, int(0.40*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (2, 1, int(0.50*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (2, 2, int(0.60*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (2, 3, int(0.70*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (2, 4, int(0.80*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (2, 5, int(0.90*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (2, 6, int(1.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (2, 7, int(1.10*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (3, 0, int(1.20*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (3, 1, int(1.30*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (3, 2, int(1.40*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (3, 3, int(1.50*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (3, 4, int(1.60*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (3, 5, int(1.70*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (3, 6, int(1.80*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (3, 7, int(1.90*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (4, 0, int(2.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (4, 1, int(2.10*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (4, 2, int(2.20*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (4, 3, int(2.30*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (4, 4, int(2.40*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (4, 5, int(2.50*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (4, 6, int(2.60*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (4, 7, int(2.70*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (5, 0, int(2.80*baseScore), int(0.90*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (6, 0, int(0.00*baseScore), int(1.00*self.playerList[playerNum].totalStreakNotes) ) )
    
          
      elif self.starScoring == 2 or self.starScoring == 3:   #RB style scoring
        #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (0, 0, int(0.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - first always all 0's
        self.starThresholdsP2.append( (0, 1, int(0.03125*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (0, 2, int(0.0625*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (0, 3, int(0.09375*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (0, 4, int(0.125*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (0, 5, int(0.15625*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (0, 6, int(0.1875*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (0, 7, int(0.21875*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (1, 0, int(0.25*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (1, 1, int(0.28125*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (1, 2, int(0.3125*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (1, 3, int(0.34375*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (1, 4, int(0.375*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (1, 5, int(0.40625*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (1, 6, int(0.4375*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (1, 7, int(0.46875*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (2, 0, int(0.5*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (2, 1, int(0.5625*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (2, 2, int(0.625*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (2, 3, int(0.6875*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (2, 4, int(0.75*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (2, 5, int(0.8125*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (2, 6, int(0.875*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (2, 7, int(0.9375*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (3, 0, int(1.0*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (3, 1, int(1.125*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (3, 2, int(1.25*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (3, 3, int(1.375*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (3, 4, int(1.5*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (3, 5, int(1.625*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (3, 6, int(1.75*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (3, 7, int(1.875*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (4, 0, int(2.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (4, 1, int(2.125*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (4, 2, int(2.25*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (4, 3, int(2.375*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (4, 4, int(2.5*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (4, 5, int(2.625*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (4, 6, int(2.75*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (4, 7, int(2.875*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        self.starThresholdsP2.append( (5, 0, int(3.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        if self.guitars[playerNum].isBassGuitar:
          #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsP2.append( (6, 0, int(4.80*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        elif self.guitars[playerNum].isDrum:
          #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsP2.append( (6, 0, int(4.65*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
        else:   #guitar parts
          #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsP2.append( (6, 0, int(5.30*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) )
  
        if self.starScoring == 3:   #if RB+GH scoring, 100% automatically skips you to 6 stars
          self.starThresholdsP2.append( (6, 0, int(0.00*baseScore), int(1.00*self.playerList[playerNum].totalStreakNotes) ) )
  
      
      else:   #0 = FoF scoring
        #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (0, 0, int(0.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - first always all 0's
        self.starThresholdsP2.append( (1, 0, int(0.00*baseScore), int(0.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (1, 1, int(0.00*baseScore), int(0.03125*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (1, 2, int(0.00*baseScore), int(0.0625*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (1, 3, int(0.00*baseScore), int(0.09375*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (1, 4, int(0.00*baseScore), int(0.125*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (1, 5, int(0.00*baseScore), int(0.15625*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (1, 6, int(0.00*baseScore), int(0.1875*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (1, 7, int(0.00*baseScore), int(0.21875*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (2, 0, int(0.00*baseScore), int(0.25*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (2, 1, int(0.00*baseScore), int(0.28125*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (2, 2, int(0.00*baseScore), int(0.3125*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (2, 3, int(0.00*baseScore), int(0.34375*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (2, 4, int(0.00*baseScore), int(0.375*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (2, 5, int(0.00*baseScore), int(0.40625*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (2, 6, int(0.00*baseScore), int(0.4375*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (2, 7, int(0.00*baseScore), int(0.46875*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (3, 0, int(0.00*baseScore), int(0.50*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (3, 1, int(0.00*baseScore), int(0.53125*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (3, 2, int(0.00*baseScore), int(0.5625*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (3, 3, int(0.00*baseScore), int(0.59375*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (3, 4, int(0.00*baseScore), int(0.625*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (3, 5, int(0.00*baseScore), int(0.65625*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (3, 6, int(0.00*baseScore), int(0.6875*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (3, 7, int(0.00*baseScore), int(0.71875*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (4, 0, int(0.00*baseScore), int(0.75*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (4, 1, int(0.00*baseScore), int(0.775*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (4, 2, int(0.00*baseScore), int(0.80*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (4, 3, int(0.00*baseScore), int(0.825*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (4, 4, int(0.00*baseScore), int(0.85*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (4, 5, int(0.00*baseScore), int(0.875*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (4, 6, int(0.00*baseScore), int(0.90*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (4, 7, int(0.00*baseScore), int(0.925*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (5, 0, int(0.00*baseScore), int(0.95*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
        self.starThresholdsP2.append( (6, 0, int(0.00*baseScore), int(1.00*self.playerList[playerNum].totalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
  
      
      self.maxStarThresholdIndex[playerNum]=len(self.starThresholdsP2) - 1
      self.getNextStarThresholds(playerNum)   #start it at the first threshold pair to surpass
      tempFS, tempPS, self.finalScoreThreshold[playerNum], self.finalHitNotesThreshold[playerNum] = self.starThresholdsP2[-1]
    
      #MFH - still numOfPlayers > 1:
      if self.coOp:   #now create array of tuples for co-op mode star score thresholds
        self.coOpTotalStreakNotes = 0
        baseScore = 0
        for playerNum, playa in enumerate(self.playerList):   #accumulate base scoring values for co-op
          self.coOpTotalStreakNotes += self.playerList[playerNum].totalStreakNotes
          baseScore += self.avg1xScore[playerNum]
        self.avg1xScore.append(baseScore)
        self.starThresholdIndex.append(0)   #to index self.coOpPlayerIndex
        self.nextScoreThreshold.append(0)
        self.nextHitNotesThreshold.append(0)
        self.nextStar.append(0)
        self.nextPartialStar.append(0)
        self.maxStarThresholdIndex.append(0)
        self.finalScoreThreshold.append(0)
        self.finalHitNotesThreshold.append(0)

        if self.starScoring == 1:     #GH style scoring
          #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (0, 0, int(0.00*baseScore), int(0.00*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - first always all 0's
          self.starThresholdsCoOp.append( (1, 0, int(0.00*baseScore), int(0.00*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - first threshold(s) to surpass
          self.starThresholdsCoOp.append( (1, 1, int(0.05*baseScore), int(0.00*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (1, 2, int(0.10*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (1, 3, int(0.15*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (1, 4, int(0.20*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (1, 5, int(0.25*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (1, 6, int(0.30*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (1, 7, int(0.35*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (2, 0, int(0.40*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (2, 1, int(0.50*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (2, 2, int(0.60*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (2, 3, int(0.70*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (2, 4, int(0.80*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (2, 5, int(0.90*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (2, 6, int(1.00*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (2, 7, int(1.10*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (3, 0, int(1.20*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (3, 1, int(1.30*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (3, 2, int(1.40*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (3, 3, int(1.50*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (3, 4, int(1.60*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (3, 5, int(1.70*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (3, 6, int(1.80*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (3, 7, int(1.90*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (4, 0, int(2.00*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (4, 1, int(2.10*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (4, 2, int(2.20*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (4, 3, int(2.30*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (4, 4, int(2.40*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (4, 5, int(2.50*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (4, 6, int(2.60*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (4, 7, int(2.70*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (5, 0, int(2.80*baseScore), int(0.90*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (6, 0, int(0.00*baseScore), int(1.00*self.coOpTotalStreakNotes) ) )
      
            
        elif self.starScoring == 2 or self.starScoring == 3:   #RB style scoring
          #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (0, 0, int(0.00*baseScore), int(0.00*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - first always all 0's
          self.starThresholdsCoOp.append( (0, 1, int(0.03125*baseScore), int(0.00*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (0, 2, int(0.0625*baseScore), int(0.00*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (0, 3, int(0.09375*baseScore), int(0.00*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (0, 4, int(0.125*baseScore), int(0.00*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (0, 5, int(0.15625*baseScore), int(0.00*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (0, 6, int(0.1875*baseScore), int(0.00*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (0, 7, int(0.21875*baseScore), int(0.00*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (1, 0, int(0.25*baseScore), int(0.00*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (1, 1, int(0.28125*baseScore), int(0.00*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (1, 2, int(0.3125*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (1, 3, int(0.34375*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (1, 4, int(0.375*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (1, 5, int(0.40625*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (1, 6, int(0.4375*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (1, 7, int(0.46875*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (2, 0, int(0.5*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (2, 1, int(0.5625*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (2, 2, int(0.625*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (2, 3, int(0.6875*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (2, 4, int(0.75*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (2, 5, int(0.8125*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (2, 6, int(0.875*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (2, 7, int(0.9375*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (3, 0, int(1.0*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (3, 1, int(1.125*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (3, 2, int(1.25*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (3, 3, int(1.375*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (3, 4, int(1.5*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (3, 5, int(1.625*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (3, 6, int(1.75*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (3, 7, int(1.875*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (4, 0, int(2.00*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (4, 1, int(2.125*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (4, 2, int(2.25*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (4, 3, int(2.375*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (4, 4, int(2.5*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (4, 5, int(2.625*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (4, 6, int(2.75*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (4, 7, int(2.875*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          self.starThresholdsCoOp.append( (5, 0, int(3.00*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          if self.guitars[playerNum].isBassGuitar:
            #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
            self.starThresholdsCoOp.append( (6, 0, int(4.80*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          elif self.guitars[playerNum].isDrum:
            #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
            self.starThresholdsCoOp.append( (6, 0, int(4.65*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
          else:   #guitar parts
            #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
            self.starThresholdsCoOp.append( (6, 0, int(5.30*baseScore), int(0.00*self.coOpTotalStreakNotes) ) )
    
          if self.starScoring == 3:   #if RB+GH scoring, 100% automatically skips you to 6 stars
            self.starThresholdsCoOp.append( (6, 0, int(0.00*baseScore), int(1.00*self.coOpTotalStreakNotes) ) )
    
        
        else:   #0 = FoF scoring
          #                           (<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (0, 0, int(0.00*baseScore), int(0.00*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - first always all 0's
          self.starThresholdsCoOp.append( (1, 0, int(0.00*baseScore), int(0.00*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (1, 1, int(0.00*baseScore), int(0.03125*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (1, 2, int(0.00*baseScore), int(0.0625*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (1, 3, int(0.00*baseScore), int(0.09375*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (1, 4, int(0.00*baseScore), int(0.125*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (1, 5, int(0.00*baseScore), int(0.15625*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (1, 6, int(0.00*baseScore), int(0.1875*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (1, 7, int(0.00*baseScore), int(0.21875*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (2, 0, int(0.00*baseScore), int(0.25*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (2, 1, int(0.00*baseScore), int(0.28125*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (2, 2, int(0.00*baseScore), int(0.3125*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (2, 3, int(0.00*baseScore), int(0.34375*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (2, 4, int(0.00*baseScore), int(0.375*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (2, 5, int(0.00*baseScore), int(0.40625*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (2, 6, int(0.00*baseScore), int(0.4375*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (2, 7, int(0.00*baseScore), int(0.46875*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (3, 0, int(0.00*baseScore), int(0.50*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (3, 1, int(0.00*baseScore), int(0.53125*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (3, 2, int(0.00*baseScore), int(0.5625*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (3, 3, int(0.00*baseScore), int(0.59375*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (3, 4, int(0.00*baseScore), int(0.625*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (3, 5, int(0.00*baseScore), int(0.65625*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (3, 6, int(0.00*baseScore), int(0.6875*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (3, 7, int(0.00*baseScore), int(0.71875*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (4, 0, int(0.00*baseScore), int(0.75*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (4, 1, int(0.00*baseScore), int(0.775*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (4, 2, int(0.00*baseScore), int(0.80*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (4, 3, int(0.00*baseScore), int(0.825*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (4, 4, int(0.00*baseScore), int(0.85*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (4, 5, int(0.00*baseScore), int(0.875*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (4, 6, int(0.00*baseScore), int(0.90*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (4, 7, int(0.00*baseScore), int(0.925*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (5, 0, int(0.00*baseScore), int(0.95*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
          self.starThresholdsCoOp.append( (6, 0, int(0.00*baseScore), int(1.00*self.coOpTotalStreakNotes) ) ) #(<full stars>, <partial stars>, <score threshold>, <number of notes hit threshold>) - threshold(s) to surpass
    
        
        self.maxStarThresholdIndex[self.coOpPlayerIndex]=len(self.starThresholdsP2) - 1
        self.getNextStarThresholds(self.coOpPlayerIndex)   #start it at the first threshold pair to surpass
        tempFS, tempPS, self.finalScoreThreshold[self.coOpPlayerIndex], self.finalHitNotesThreshold[self.coOpPlayerIndex] = self.starThresholdsCoOp[-1]
      

  def resetStarThresholds(self):
    for i, player in enumerate(self.playerList):
      self.starThresholdIndex[i] = 0
      self.getNextStarThresholds(i)
    if self.coOp:
      self.starThresholdIndex[self.coOpPlayerIndex] = 0
      self.getNextStarThresholds(self.coOpPlayerIndex)

  def getNextStarThresholds(self, playerNum):
    #ready for a new tuple o' data
    self.starThresholdIndex[playerNum] = self.starThresholdIndex[playerNum] + 1
    if playerNum == 0:
      self.nextStar[playerNum], self.nextPartialStar[playerNum], self.nextScoreThreshold[playerNum], self.nextHitNotesThreshold[playerNum] = self.starThresholdsP1[self.starThresholdIndex[playerNum]]
    elif playerNum == 1:
      self.nextStar[playerNum], self.nextPartialStar[playerNum], self.nextScoreThreshold[playerNum], self.nextHitNotesThreshold[playerNum] = self.starThresholdsP2[self.starThresholdIndex[playerNum]]
    elif playerNum == self.coOpPlayerIndex:
      self.nextStar[playerNum], self.nextPartialStar[playerNum], self.nextScoreThreshold[playerNum], self.nextHitNotesThreshold[playerNum] = self.starThresholdsCoOp[self.starThresholdIndex[playerNum]]    


  def updateStars(self, playerNum, forceUpdate = False, tempExtraScore = 0):    #MFH - merging the two star update functions
    if playerNum == self.coOpPlayerIndex:
      if forceUpdate or ( (self.inGameStars == 2 or (self.inGameStars == 1 and self.theme == 2) ) and self.coOpStars < 6 ):
        self.lastCoOpStars = self.coOpStars
  
        if (self.coOpScore + tempExtraScore) >= self.finalScoreThreshold[playerNum] and self.coOpNotesHit >= self.finalHitNotesThreshold[playerNum]:
          #force last index, max stars
          self.coOpStars = 6
          self.coOpPartialStars = 0
          self.starThresholdIndex[playerNum] = self.maxStarThresholdIndex[playerNum]
  
        #make sure we're not at the last threshold tuple, or the following might cause an infinite loop!
        while (self.starThresholdIndex[playerNum] < self.maxStarThresholdIndex[playerNum]) and ( (self.coOpScore + tempExtraScore) >= self.nextScoreThreshold[playerNum]) and (self.coOpNotesHit >= self.nextHitNotesThreshold[playerNum]):
          #may be ready for a new tuple, check to see if stars and partialstars already match or not:
          #if (self.playerList[playerNum].stars < self.nextStar[playerNum]) or (self.partialStar[playerNum] < self.nextPartialStar[playerNum]):
          self.coOpStars = self.nextStar[playerNum]
          self.coOpPartialStars = self.nextPartialStar[playerNum]
          self.getNextStarThresholds(playerNum)
    
        if self.coOpStars != self.lastCoOpStars and self.engine.data.starDingSoundFound:  #new star gained!
          #self.engine.data.starDingSound.setVolume(self.sfxVolume) #MFH - no need to retrieve from INI file every star ding...
          self.engine.data.starDingSound.play()
    
    elif forceUpdate or ( (self.inGameStars == 2 or (self.inGameStars == 1 and self.theme == 2) ) and self.playerList[playerNum].stars < 6 ):
      self.lastStars[playerNum] = self.playerList[playerNum].stars

      #if self.nextStar[playerNum] == 0 and self.nextPartialStar[playerNum] == 0:    #need to get first threshold to surpass
      #  self.getNextStarThresholds(playerNum)

      if (self.playerList[playerNum].score + tempExtraScore) >= self.finalScoreThreshold[playerNum] and self.playerList[playerNum].notesHit >= self.finalHitNotesThreshold[playerNum]:
        #force last index, max stars
        self.playerList[playerNum].stars = 6
        self.partialStar[playerNum] = 0
        self.starThresholdIndex[playerNum] = self.maxStarThresholdIndex[playerNum]

      #make sure we're not at the last threshold tuple, or the following might cause an infinite loop!
      while (self.starThresholdIndex[playerNum] < self.maxStarThresholdIndex[playerNum]) and ( (self.playerList[playerNum].score + tempExtraScore) >= self.nextScoreThreshold[playerNum]) and (self.playerList[playerNum].notesHit >= self.nextHitNotesThreshold[playerNum]):
        #may be ready for a new tuple, check to see if stars and partialstars already match or not:
        #if (self.playerList[playerNum].stars < self.nextStar[playerNum]) or (self.partialStar[playerNum] < self.nextPartialStar[playerNum]):
        self.playerList[playerNum].stars = self.nextStar[playerNum]
        self.partialStar[playerNum] = self.nextPartialStar[playerNum]
        self.getNextStarThresholds(playerNum)
  
      if self.playerList[playerNum].stars != self.lastStars[playerNum] and self.engine.data.starDingSoundFound:  #new star gained!
        #self.engine.data.starDingSound.setVolume(self.sfxVolume) #MFH - no need to retrieve from INI file every star ding...
        self.engine.data.starDingSound.play()

#----------------------------------------------  
  def updateAvMult(self, playerNum):
  
    #if (self.inGameStats == 2 or (self.inGameStats == 1 and self.theme == 2) ) or (self.inGameStars == 2 or (self.inGameStars == 1 and self.theme == 2) ):   #MFH -- only process if in-game stats are enabled
    if (self.inGameStats == 2 or (self.inGameStats == 1 and self.theme == 2) ):
  
      self.hitAccuracy[playerNum] = (float(self.playerList[playerNum].notesHit) / float(self.playerList[playerNum].totalStreakNotes) ) * 100.0
      self.avMult[playerNum] = self.playerList[playerNum].score/(self.playerList[playerNum].totalNotes*50.0)


        
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

    pos = self.getSongPosition()

    if self.boardY <= 1:
      self.boardY == 1
      self.setCamera()
    elif self.boardY > 1:
      self.boardY -= 0.01
      self.setCamera()
    #self.setCamera()

    #Theme.setBaseColor()

    if self.song:
      self.stage.renderBackground()

      #MFH: render the note sheet just on top of the background:
      if self.lyricSheet != None:
        self.lyricSheet.transform.reset()
        self.lyricSheet.transform.translate(w/2, h*0.935)   #last change: -0.015
        self.lyricSheet.transform.scale(self.lyricSheetScaleFactor,-self.lyricSheetScaleFactor)
        self.lyricSheet.draw()  
        #the timing line on this lyric sheet image is approx. 1/4 over from the left
  
      SceneClient.render(self, visibility, topMost) #MFH - I believe this eventually calls the renderGuitar function, which also involves two viewports... may not be easy to move this one...
        
      self.visibility = v = 1.0 - ((1 - visibility) ** 2)
  
      self.engine.view.setOrthogonalProjection(normalize = True)
  
      #MFH - also render the scrolling lyrics & sections before changing viewports:
      if (self.readTextAndLyricEvents == 2 or (self.readTextAndLyricEvents == 1 and self.theme == 2)) and (not self.pause and not self.failed and not self.ending):
        minPos = pos - ((self.guitars[0].currentPeriod * self.guitars[0].beatsPerBoard) / 2)
        maxPos = pos + ((self.guitars[0].currentPeriod * self.guitars[0].beatsPerBoard) * 1.5)
        eventWindow = (maxPos - minPos)
        #lyricSlop = ( self.guitars[0].currentPeriod / (maxPos - minPos) ) / 4
        lyricSlop = ( self.guitars[0].currentPeriod / ((maxPos - minPos)/2) ) / 2
  
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
  
  
  
  
        #finally, handle the unused text events track
        if self.showUnusedTextEvents:
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
        
            yOffset = 0.0190      #last change -.0020
            txtSize = 0.00124
            lyricFont.render(event.text, (xOffset, yOffset),(1, 0, 0),txtSize)
  
      try:
        now = self.getSongPosition()
        countdownPos = self.lastEvent - now

        #MFH TODO - rewrite this Jurgen block and rename variables to be multiplayer-friendly (for >2 players)
        #Show Jurgen played Spikehead777
        #Player 1
        if self.jurg1 == True and self.splayers == 2:
          if self.autoPlay:
            if self.jurg == 0 or self.jurg == 2:
              text = self.tsJurgenIsHere
            else:
              text = self.tsJurgenWasHere
          else:
            text = self.tsJurgenWasHere
          w, h = bigFont.getStringSize(text, scale = 0.0005)
          Theme.setBaseColor()
          bigFont.render(text,  (0.25-(w/2), 0.34), scale = 0.0005)  #MFH - y was 0.4
        elif self.jurg1 == True and self.splayers == 1:
          if self.autoPlay:
            if self.jurg == 0 or self.jurg == 2:
              text = self.tsJurgenIsHere
            else:
              text = self.tsJurgenWasHere
          else:
            text = self.tsJurgenWasHere
          w, h = bigFont.getStringSize(text, scale = 0.001)
          Theme.setBaseColor()
          bigFont.render(text,  (0.5-(w/2), 0.2), scale = 0.001)
        #Player 2
        if self.jurg2 == True and self.splayers == 2:
          if self.autoPlay:
            if self.jurg == 1 or self.jurg == 2:
              text = self.tsJurgenIsHere
            else:
              text = self.tsJurgenWasHere
          else:
            text = self.tsJurgenWasHere
          w, h = bigFont.getStringSize(text, scale = 0.0005)
          Theme.setBaseColor()
          bigFont.render(text,  (0.75-(w/2), 0.34), scale = 0.0005)
        #End Jurgen Code
  
        for i,player in enumerate(self.playerList): #QQstarS: This part has big fix. I add the code into it,So he can shown corect
  
          streakFlag = 0  #set the flag to 0
          self.engine.view.setViewportHalf(self.numOfPlayers,i)
          Theme.setBaseColor()
          
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
                #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                if self.guitars[i].isBassGuitar and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                  if player.streak >= 50:
                    multiplier = 6
                    multRange = (0.75,1.00)  #MFH division->constant: [(3.0/4.0,4.0/4.0)]->[(0.75,1.00)]
                    color = (.3,.7,.9,1)
                  else:
                    multiplier = 5
                    multRange = (0.5,0.75) #MFH division->constant: [(2.0/4.0,3.0/4.0)]->[(0.5,0.75)]
                    color = (.3,.7,.9,1)
                #death_au: end check for bass groove
                elif player.streak >= 30:
                  multiplier = 4
                  multRange = (0.875,1.0) #MFH division->constant: was [(7.0/8.0,8.0/8.0)]
                  color = (.3,.7,.9,1)
                elif player.streak >= 20:
                  multiplier = 3
                  multRange = (0.75,0.875) #MFH division->constant: was [(6.0/8.0,7.0/8.0)]
                  color = (.3,.7,.9,1)
                elif player.streak >= 10:
                  multiplier = 2
                  multRange = (0.625,0.75) #MFH division->constant: was [(5.0/8.0,6.0/8.0)]
                  color = (.3,.7,.9,1)
                else:
                  multiplier = 1
                  multRange = (0.5,0.625) #MFH division->constant: was [(4.0/8.0,5.0/8.0)]
                  color = (.3,.7,.9,1)
              else:
                #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                if self.guitars[i].isBassGuitar and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                  if player.streak >= 50:
                    multiplier = 6
                    multRange = (0.25,0.5) #MFH division->constant: was [(1.0/4.0,2.0/4.0)]
                    color = (.3,.7,.9,1)
                  else:
                    multiplier = 5
                    multRange = (0.0,0.25) #MFH division->constant: was [(0.0/4.0,1.0/4.0)]
                    color = (.3,.7,.9,1)
                elif player.streak >= 30:
                  multiplier = 4
                  multRange = (0.375,0.5) #MFH division->constant: was [(3.0/8.0,4.0/8.0)]
                  color = (1,-1,1,1)
                elif player.streak >= 20:
                  multiplier = 3
                  multRange = (0.25,0.375) #MFH division->constant: was [(2.0/8.0,3.0/8.0)]
                  color = (-1,1,-.75,1)
                elif player.streak >= 10:
                  multiplier = 2
                  multRange = (0.125,0.25) #MFH division->constant: was (1.0/8.0,2.0/8.0)
                  color = (1,1,-1,1)
                else:
                  multiplier = 1
                  multRange = (0.0,0.125) #MFH division->constant: was (0.0/8.0,1.0/8.0)
                  color = (1,1,-1,1)
                        
              #myfingershurt: GH bass groove multiplier:            
              #if self.playerList[i].part.text == "Bass Guitar" and player.streak >= 40 and self.bassGrooveEnableMode == 2:   #bass groove!
              if self.guitars[i].isBassGuitar and player.streak >= 40 and self.bassGrooveEnableMode == 2:   #bass groove!
                if self.bassgroovemult != None: #death_au : bassgroovemult image found, draw image
                      
                  self.bassgroovemult.transform.reset()
                  self.bassgroovemult.transform.scale(.5,-.125) #MFH division->constant: was (.5,-.5/4.0)
                  self.bassgroovemult.transform.translate(w*0.134,h*0.19 + self.hOffset[i]) #QQstarS:Set  new postion. I only shown it once.
                  self.bassgroovemult.draw(rect = (0,1,multRange[0],multRange[1]))
                
                else: #death_au: bassgroovemult not found
                  #myfingershurt: Temp text bass groove multiplier:
                  glColor3f(0,0.75,1)
                  text = str(self.playerList[i].getScoreMultiplier() * self.multi[i])
                  wid, hig = font.getStringSize(text,0.00325)
                  font.render(text, (.133 - wid / 2, .566),(1, 0, 0),0.00325)     #replacing GH multiplier large text
  
  
              else:
                self.mult.transform.reset()
                self.mult.transform.scale(.5,-.0625) #MFH division->constant: was (.5,-.5/8.0)
                self.mult.transform.translate(w*0.134,h*0.19 + self.hOffset[i]) #QQstarS:Set  new postion. I only shown it once.
                self.mult.draw(rect = (0,1,multRange[0],multRange[1]))
  
  
     
          
              self.rockmeter.transform.reset()
              self.rockmeter.transform.scale(.5,-.5)
              self.rockmeter.transform.translate(w*.134, h*.22 + self.hOffset[i])
              self.rockmeter.draw()
              
              #===============blazingamer GH2 scoremeter
              
              
              #if (self.coOp and i == 0) or not self.coOp:  #MFH only render for player 0 if co-op mode
              if (self.coOp and i == 1) or not self.coOp:  #MFH only render for player 1 if co-op mode

                if self.coOp:
                  score=self.coOpScore
                  for playaNum, playa in enumerate(self.playerList):
                    score += self.getExtraScoreForCurrentlyPlayedNotes(playaNum)
                else:
                  score=player.score
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
                if player.score >= 10:
                  text = str(score1)
                  size = streakFont.getStringSize(text)
                  scoreFont.render(text, (.168, 0.522))
                if player.score >= 100:
                  text = str(score2)
                  size = streakFont.getStringSize(text)
                  scoreFont.render(text, (.148, 0.524))
                if player.score >= 1000:
                  text = str(score3)
                  size = streakFont.getStringSize(text)
                  scoreFont.render(text, (.118, 0.527))
                if player.score >= 10000:
                  text = str(score4)
                  size = streakFont.getStringSize(text)
                  scoreFont.render(text, (.095, 0.530))
                if player.score >= 100000:
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
                rock.transform.reset()
                rock.transform.scale(.5,-.5)
                rock.transform.translate(w*.86,h*.2 + self.hOffset[i])
                rock.draw()
              else:
                self.rockOff.transform.reset()
                self.rockOff.transform.scale(.5,-.5)
                self.rockOff.transform.translate(w*.86,h*.2 + self.hOffset[i])
                self.rockOff.draw()
    
              currentRock = (0.0 + self.rock[i]) / (self.rockMax)
              if self.rock[i] >= 0:
                self.arrowRotation[i] += ( 0.0 + currentRock - self.arrowRotation[i]) / 5.0
              else:  #QQstarS: Fix the arrow let him never rotation to bottom
                self.arrowRotation[i] = self.arrowRotation[i]
              angle = -(.460 / 2) * math.pi + .460 * math.pi * self.arrowRotation[i]
              wfactor = self.arrow.widthf(pixelw = 60.000)
            
              if self.failingEnabled:
                self.arrow.transform.reset()
                self.arrow.transform.scale(wfactor,-wfactor)
                self.arrow.transform.rotate(angle) 
                self.arrow.transform.translate(w*.86,h*.136 + self.hOffset[i])
                self.arrow.draw()
    
              self.rockTop.transform.reset()
              self.rockTop.transform.scale(.5,-.5)
              self.rockTop.transform.translate(w*.86,h*.2 + self.hOffset[i])
              self.rockTop.draw()
    
              self.counter.transform.reset()
              self.counter.transform.translate(w*.15,h*(self.counterY) + self.hOffset[i])
              self.counter.transform.scale(.5,-.5)
              self.counter.draw()
  
              if player.streak == 0:
                r = self.basedots
              elif player.streak - ((multiplier-1)*10) == 1:
                r = self.dt1
              elif player.streak - ((multiplier-1)*10) == 2:
                r = self.dt2
              elif player.streak - ((multiplier-1)*10) == 3:
                r = self.dt3
              elif player.streak - ((multiplier-1)*10) == 4:
                r = self.dt4
              elif player.streak - ((multiplier-1)*10) == 5:
                r = self.dt5
              elif player.streak - ((multiplier-1)*10) == 6:
                r = self.dt6
              elif player.streak - ((multiplier-1)*10) == 7:
                r = self.dt7
              elif player.streak - ((multiplier-1)*10) == 8:
                r = self.dt8
              elif player.streak - ((multiplier-1)*10) == 9:
                r = self.dt9
              else:
                r = self.dt10
  
  
    
              r.transform.reset()
              r.transform.scale(.65,-.65)
              r.transform.translate(w*0.137, h*0.23+self.hOffset[i])
              r.draw(color = color)            
  
   
              currentSP = self.guitars[i].starPower/100.0
              widthChange = w*0.11
   
              self.oBottom.transform.reset()
              self.oBottom.transform.scale(.6,.6)
              self.oBottom.transform.translate(w*.86,h*.34 + self.hOffset[i])
              self.oBottom.draw()
                
              self.oFill.transform.reset()
              self.oFill.transform.scale(.6*currentSP,.6)
              self.oFill.transform.translate(w*.86-widthChange+widthChange*currentSP,h*.34 + self.hOffset[i])
              self.oFill.draw(rect = (0,currentSP,0,1))
   
              self.oTop.transform.reset()
              self.oTop.transform.scale(.6,.6)
              self.oTop.transform.translate(w*.86,h*.34 + self.hOffset[i])
              self.oTop.draw()
  
    
              if player.streak >= 25 and not self.counterY >= 0.1125:
                self.counterY += 0.01
              elif player.streak < 25 and not self.counterY <= -0.1:
                self.counterY -= 0.01
              if self.counterY > 0.1125 or ( self.numOfPlayers==2 ):
                self.counterY = 0.1125
    
              if self.counterY == 0.1125 or ( self.numOfPlayers==2 and player.streak >0 ):
                glColor4f(0,0,0,1)
                streak3 = player.streak/1000
                streak2 = (player.streak-streak3*1000)/100
                streak1 = (player.streak-streak3*1000-streak2*100)/10
                streak0 = (player.streak-streak3*1000-streak2*100-streak1*10)
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
                size = sphraseFont.getStringSize(self.displayText[i], scale = self.dislayTextScale[i])
                sphraseFont.render(self.displayText[i], (.5-size[0]/2,self.textY[i]-size[1]), scale = self.dislayTextScale[i])
    
              if self.youRock == True:
                if self.rockTimer == 1:
                  #self.sfxChannel.setVolume(self.sfxVolume)
                  self.engine.data.rockSound.play()
                if self.rockTimer < self.rockCountdown:
                  self.rockTimer += 1
                  self.rockMsg.transform.reset()
                  self.rockMsg.transform.scale(0.5, -0.5)
                  self.rockMsg.transform.translate(w/2,h/2)
                  self.rockMsg.draw()
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
                  self.failMsg.transform.reset()
                  self.failMsg.transform.scale(0.5, -0.5)
                  self.failMsg.transform.translate(w/2,h/2)
                  self.failMsg.draw()
                else:
                  self.finalFailed = True
                
            
              if self.pause:
                self.engine.view.setViewport(1,0)
                self.pauseScreen.transform.reset()
                self.pauseScreen.transform.scale(0.75, -0.75)
                self.pauseScreen.transform.translate(w/2+self.pause_bkg_x,h/2+self.pause_bkg_y) 
                self.pauseScreen.draw()
                
              if self.finalFailed and self.song:
                self.engine.view.setViewport(1,0)
                self.failScreen.transform.reset()
                self.failScreen.transform.scale(0.75, -0.75)
                self.failScreen.transform.translate(w/2+self.fail_bkg_x,h/2+self.fail_bkg_y)
                self.failScreen.draw()
    

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
                  glColor3f(1.0, 1.0, 1.0)  #white
                else:
                  glColor3f(0.4, 0.4, 0.4)  #grey
                w, h = font.getStringSize(text,0.00150)
                font.render(text, (.950 - w / 2, .710),(1, 0, 0),0.00150)     #off to the right slightly above fretboard
                glColor3f(1, 1, 1)  #cracker white
  
    
          #===================================================#
  
          elif self.rmtype == 1:
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
                    #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                    if self.guitars[i].isBassGuitar and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                      if player.streak >= 50:
                        multiplier = 6
                        multRange = (0.75,1.00) #MFH division->constant: was (3.0/4.0,4.0/4.0)
                        color = (1,0,0.75,1)
                      else:
                        multiplier = 5
                        multRange = (0.5,0.75) #MFH division->constant: was (2.0/4.0,3.0/4.0)
                        color = (1,0,0.75,1)
                      xs = (0.75,1)
                    #death_au: end check for bass groove
                    elif player.streak >= 30:
                      multiplier = 4
                      multRange = (0.875,1.0) #MFH division->constant: was (7.0/8.0,8.0/8.0)
                      color = (.3,.7,.9,1)
                      xs = (0.75,1)
                    elif player.streak >= 20:
                      multiplier = 3
                      multRange = (0.75,0.875) #MFH division->constant: was (6.0/8.0,7.0/8.0)
                      color = (.3,.7,.9,1)
                      xs = (0.75,1)
                    elif player.streak >= 10:
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
                    #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                    if self.guitars[i].isBassGuitar and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                      if player.streak >= 50:
                        multiplier = 6
                        multRange = (0.75,1.0) #MFH division->constant: was (3.0/4.0,4.0/4.0)
                        color = (1,0,0.75,1)
                      else:
                        multiplier = 5
                        multRange = (0.5,0.75) #MFH division->constant: was (2.0/4.0,3.0/4.0)
                        color = (1,0,0.75,1)
                    #death_au: end check for bass groove
                    elif player.streak >= 30:
                      multiplier = 4
                      multRange = (0.875,1.0) #MFH division->constant: was (7.0/8.0,8.0/8.0)
                      color = (.3,.7,.9,1)
                    elif player.streak >= 20:
                      multiplier = 3
                      multRange = (0.75,0.875) #MFH division->constant: was (6.0/8.0,7.0/8.0)
                      color = (.3,.7,.9,1)
                    elif player.streak >= 10:
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
                    #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                    if self.guitars[i].isBassGuitar and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                      if player.streak >= 50:
                        multiplier = 6
                        multRange = (0.25,0.5) #MFH division->constant: was (1.0/4.0,2.0/4.0)
                        color = (1,0,0.75,1)
                      else:
                        multiplier = 5
                        multRange = (0.0,0.25) #MFH division->constant: was (0.0/4.0,1.0/4.0)
                        color = (1,0,0.75,1)
                      xs = (0.75,1)
                    #death_au: end check for bass groove
                    elif player.streak >= 30:
                      multiplier = 4
                      multRange = (0.375,0.5) #MFH division->constant: was (3.0/8.0,4.0/8.0)
                      color = (1,-1,1,1)
                      xs = (0.5,0.75)
                    elif player.streak >= 20:
                      multiplier = 3
                      multRange = (0.25,0.375) #MFH division->constant: was (2.0/8.0,3.0/8.0)
                      color = (-1,1,-.75,1)
                      xs = (0.25,0.5)
                    elif player.streak >= 10:
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
                    #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                    if self.guitars[i].isBassGuitar and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                      if player.streak >= 50:
                        multiplier = 6
                        multRange = (0.25,0.5) #MFH division->constant: was (1.0/4.0,2.0/4.0)
                        color = (1,0,0.75,1)
                      else:
                        multiplier = 5
                        multRange = (0.0,0.25) #MFH division->constant: was (0.0/4.0,1.0/4.0)
                        color = (1,0,0.75,1)
                      xs = (0.75,1)
                    #death_au: end check for bass groove
                    elif player.streak >= 30:
                      multiplier = 4
                      multRange = (0.375,0.5) #MFH division->constant: was (3.0/8.0,4.0/8.0)
                      color = (1,-1,1,1)
                    elif player.streak >= 20:
                      multiplier = 3
                      multRange = (0.25,0.375) #MFH division->constant: was (2.0/8.0,3.0/8.0)
                      color = (-1,1,-.75,1)
                    elif player.streak >= 10:
                      multiplier = 2
                      multRange = (0.125,0.25) #MFH division->constant: was (1.0/8.0,2.0/8.0)
                      color = (1,1,-1,1)
                    else:
                      multiplier = 1
                      multRange = (0.0,0.125) #MFH division->constant: was (0.0/8.0,1.0/8.0)
                      color = (1,1,-1,1)
            
              
              #myfingershurt: GH bass groove multiplier: 
              # death_au: added drawing of bassgroovemult image             
              #if self.playerList[i].part.text == "Bass Guitar" and player.streak >= 40 and self.bassGrooveEnableMode == 2:   #bass groove!
              if self.guitars[i].isBassGuitar and player.streak >= 40 and self.bassGrooveEnableMode == 2:   #bass groove!
                if self.bassgroovemult != None: #death_au : bassgroovemult image found, draw image
                      
                  self.bassgroovemult.transform.reset()
                  self.bassgroovemult.transform.scale(.5,-.125) #MFH division->constant: was (.5,-.5/4.0)
                  self.bassgroovemult.transform.translate(w*0.134,h*0.19 + self.hOffset[i]) #QQstarS:Set  new postion. I only shown it once.
                  self.bassgroovemult.draw(rect = (0,1,multRange[0],multRange[1]))
                
                else: #death_au: bassgroovemult not found
                  #myfingershurt: Temp text bass groove multiplier:
                  glColor3f(0,0.75,1)
                  text = str(self.playerList[i].getScoreMultiplier() * self.multi[i])
                  wid, hig = font.getStringSize(text,0.00325)
                  font.render(text, (.133 - wid / 2, .566),(1, 0, 0),0.00325)     #replacing GH multiplier large text
  
  
              else:
                self.mult.transform.reset()
                self.mult.transform.scale(.5,-.0625) #MFH division->constant: was (.5,-.5/8.0)
                self.mult.transform.translate(w*0.134,h*0.19 + self.hOffset[i]) #QQstarS:Set  new postion. I only shown it once.
                self.mult.draw(rect = (0,1,multRange[0],multRange[1]))
  
              if player.streak == 0:
                streak = 0
                hstreak = 0
              elif player.streak - ((multiplier-1)*10) == 1:
                streak = 0
                hstreak = 1  
              elif player.streak - ((multiplier-1)*10) == 2:
                streak = 1
                hstreak = 0
              elif player.streak - ((multiplier-1)*10) == 3:
                streak = 1
                hstreak = 1
              elif player.streak - ((multiplier-1)*10) == 4:
                streak = 2
                hstreak = 0
              elif player.streak - ((multiplier-1)*10) == 5:
                streak = 2
                hstreak = 1
              elif player.streak - ((multiplier-1)*10) == 6:
                streak = 3
                hstreak = 0
              elif player.streak - ((multiplier-1)*10) == 7:
                streak = 3
                hstreak = 1
              elif player.streak - ((multiplier-1)*10) == 8:
                streak = 4
                hstreak = 0
              elif player.streak - ((multiplier-1)*10) == 9:
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
                if self.theme < 2:
                  if self.halfDots:
                    r.transform.reset()
                    r.transform.scale(0.125,-.166666667) #MFH division->constant: was (.5*(1.0/4.0),-.5*(1.0/3.0))
                    r.transform.translate(w*.0425,h*.12+t*(h*.034) + self.hOffset[i])
                    r.draw(rect = (xs[0],xs[1],ys[0],ys[1]))
                  else:
                    r.transform.reset()
                    r.transform.scale(.5,-.166666667) #MFH division->constant: was (.5,-.5*(1.0/3.0))
                    r.transform.translate(w*.044,h*.12+t*(h*.034) + self.hOffset[i])
                    r.draw(color = color, rect = (0.0,1.0,ys[0],ys[1]))
  
    
              if self.x1[i] == 0: #QQstarS:Set [0] to [i]
                self.x1[i] = .86
                self.y1[i] = .2
                self.x2[i] = .86
                self.y2[i] = .2
                self.x3[i] = .86
                self.y3[i] = .2
  
  
              if self.starfx: #blazingamer, corrected by myfingershurt, adjusted by worldrave
                if self.guitars[i].starPower >= 50 or self.guitars[i].starPowerActive:
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
      
                if self.guitars[i].starPower >= 50 or self.guitars[i].starPowerActive: #QQstarS:Set [0] to [i]
                  lightPos = (0.689655172,1)  #MFH division->constant: was (2.0/2.9,1)
                else:
                  lightPos = (1.0/2.9,2.0/3.1)  #MFH division->constant: ok any preprocessor worth it's salt would take care of this before runtime... this is pointless.
      
                if self.guitars[i].starPower >= 16.6: #QQstarS:Set [0] to [i]
                  lightVis = 1
                else:
                  lightVis = self.guitars[i].starPower/16.6
    
                wfactor = self.SP.widthf(pixelw = 23.000) #Worldrave Change - Bulb 1
                self.SP.transform.reset()
                self.SP.transform.rotate(.87)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*0.772,h*0.284 + self.hOffset[i]) #Worldrave Width and Height was h*0.310
                self.SP.draw(rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.SP.transform.reset()
                self.SP.transform.rotate(.87) #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*0.772 ,h*0.284 + self.hOffset[i]) #Worldrave Change
                self.SP.draw(rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
      
                if self.guitars[i].starPower >= 33.2: #QQstarS:Set [0] to [i]
                  lightVis = 1
                else:
                  lightVis = (self.guitars[i].starPower-16.6)/16.6
                wfactor = self.SP.widthf(pixelw = 23.000) #Worldrave Change - Bulb 2
                self.SP.transform.reset()
                self.SP.transform.rotate(.58)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*0.795,h*0.312 + self.hOffset[i])  #Worldrave Change
                self.SP.draw(rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.SP.transform.reset()
                self.SP.transform.rotate(.58)  #evilynux - should be the same
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*0.795,h*0.312 + self.hOffset[i])  #Worldrave Change
                self.SP.draw(rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
      
                if self.guitars[i].starPower >= 49.8:
                  lightVis = 1
                else:
                  lightVis = (self.guitars[i].starPower-32.2)/16.6
    
                wfactor = self.SP.widthf(pixelw = 23.000)  #Worldrave Change - Bulb 3
                self.SP.transform.reset()
                self.SP.transform.rotate(.37)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*0.822,h*0.329 + self.hOffset[i]) #Worldrave Width and Height was h*0.338
                self.SP.draw(rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.SP.transform.reset()
                self.SP.transform.rotate(.37)  #evilynux - should be the same
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*0.822,h*0.329 + self.hOffset[i])  #Worldrave Change
                self.SP.draw(rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
      
                if self.guitars[i].starPower >= 66.4:
                  lightVis = 1
                else:
                  lightVis = (self.guitars[i].starPower-49.8)/16.6
    
                wfactor = self.SP.widthf(pixelw = 32.000) #Worldrave Change - Bulb 4
                self.SP.transform.reset()
                self.SP.transform.rotate(.0)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*self.x1[i]*0.96852469,h*self.y1[i]*1.011455279 + self.hOffset[i])  #evilynux - fixed for all resolutions
                self.SP.draw(rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.SP.transform.reset()
                self.SP.transform.rotate(.0)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*self.x1[i]*0.96852469,h*self.y1[i]*1.011455279 + self.hOffset[i])  #evilynux - fixed for all resolutions
                self.SP.draw(rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
      
                if self.guitars[i].starPower >= 83:
                  lightVis = 1
                else:
                  lightVis = (self.guitars[i].starPower-66.4)/16.6
    
                wfactor = self.SP.widthf(pixelw = 32.000)  #Worldrave Change - Bulb 5  
                self.SP.transform.reset()
                self.SP.transform.rotate(-.34)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*self.x2[i]*0.978698075,h*self.y2[i]*1.02813143 + self.hOffset[i])  #evilynux - fixed for all resolutions
                self.SP.draw(rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.SP.transform.reset()
                self.SP.transform.rotate(-.34)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*self.x2[i]*0.978698075,h*self.y2[i]*1.02813143 + self.hOffset[i])  #evilynux - fixed for all resolutions
                self.SP.draw(rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
      
                if self.guitars[i].starPower >= 100:
                  lightVis = 1
                else:
                  lightVis = (self.guitars[i].starPower-83)/16.6
    
                wfactor = self.SP.widthf(pixelw = 32.000) #Worldrave Change - Bulb 6
                self.SP.transform.reset()
                self.SP.transform.rotate(-.70)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*self.x3[i]*0.990664588,h*self.y3[i]*1.04973235 + self.hOffset[i])  #evilynux - fixed for all resolutions
                self.SP.draw(rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.SP.transform.reset()
                self.SP.transform.rotate(-.70)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*self.x3[i]*0.990664588,h*self.y3[i]*1.04973235 + self.hOffset[i])  #evilynux - fixed for all resolutions
                self.SP.draw(rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
                        
              self.rockmeter.transform.reset()
              self.rockmeter.transform.scale(.5,-.5)
              self.rockmeter.transform.translate(w*.134, h*.22 + self.hOffset[i])
              self.rockmeter.draw()

              #if (self.coOp and i == 0) or not self.coOp:  #MFH only render for player 0 if co-op mode
              if (self.coOp and i == 1) or not self.coOp:  #MFH only render for player 1 if co-op mode

                if self.coOp:
                  score=self.coOpScore
                  for playaNum, playa in enumerate(self.playerList):
                    score += self.getExtraScoreForCurrentlyPlayedNotes(playaNum)
                else:
                  score=player.score
                  score += self.getExtraScoreForCurrentlyPlayedNotes(i)

                size      = scoreFont.getStringSize(str(score))
                x = 0.19-size[0]
                # evilynux - Changed upon worldrave's request
                c1,c2,c3 = self.rockmeter_score_color
                glColor3f(c1,c2,c3)
                #if self.numOfPlayers > 1 and i == 0:
                #  scoreFont.render("%d" % (score), (x, 0.518+self.hFontOffset[i]))
                #else:
                scoreFont.render("%d" % (score),  (x, 0.518+self.hFontOffset[i]))
    
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
                rock.transform.reset()
                rock.transform.scale(.5,-.5)
                rock.transform.translate(w*.86,h*.2 + self.hOffset[i])
                rock.draw()
              else:
                self.rockOff.transform.reset()
                self.rockOff.transform.scale(.5,-.5)
                self.rockOff.transform.translate(w*.86,h*.2 + self.hOffset[i])
                self.rockOff.draw()
    
              currentRock = (0.0 + self.rock[i]) / (self.rockMax)
              if self.rock[i] >= 0:
                self.arrowRotation[i] += ( 0.0 + currentRock - self.arrowRotation[i]) / 5.0
              else:  #QQstarS: Fix the arrow let him never rotation to bottom
                self.arrowRotation[i] = self.arrowRotation[i]
              angle = -(.460 / 2) * math.pi + .460 * math.pi * self.arrowRotation[i]
              wfactor = self.arrow.widthf(pixelw = 60.000)
  
              if self.failingEnabled:
                self.arrow.transform.reset()
                self.arrow.transform.scale(wfactor,-wfactor)
                self.arrow.transform.rotate(angle) 
                self.arrow.transform.translate(w*.86,h*.136 + self.hOffset[i])
                self.arrow.draw()
    
              self.rockTop.transform.reset()
              self.rockTop.transform.scale(.5,-.5)
              self.rockTop.transform.translate(w*.86,h*.2 + self.hOffset[i])
              self.rockTop.draw()
    
              self.counter.transform.reset()
              self.counter.transform.translate(w*.15,h*(self.counterY) + self.hOffset[i])
              self.counter.transform.scale(.5,-.5)
              self.counter.draw()
  
  
    
              if player.streak >= 25 and not self.counterY >= 0.1125:
                self.counterY += 0.01
              elif player.streak < 25 and not self.counterY <= -0.1:
                self.counterY -= 0.01
              if self.counterY > 0.1125 or ( self.numOfPlayers==2 ):
                self.counterY = 0.1125
    
              if self.counterY == 0.1125 or ( self.numOfPlayers==2 and player.streak >0 ):
                glColor4f(0,0,0,1)
                streak3 = player.streak/1000
                streak2 = (player.streak-streak3*1000)/100
                streak1 = (player.streak-streak3*1000-streak2*100)/10
                streak0 = (player.streak-streak3*1000-streak2*100-streak1*10)
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
                size = sphraseFont.getStringSize(self.displayText[i], scale = self.dislayTextScale[i])
                sphraseFont.render(self.displayText[i], (.5-size[0]/2,self.textY[i]-size[1]), scale = self.dislayTextScale[i])
    
              if self.youRock == True:
                if self.rockTimer == 1:
                  #self.sfxChannel.setVolume(self.sfxVolume)
                  self.engine.data.rockSound.play()
                if self.rockTimer < self.rockCountdown:
                  self.rockTimer += 1
                  self.rockMsg.transform.reset()
                  self.rockMsg.transform.scale(0.5, -0.5)
                  self.rockMsg.transform.translate(w/2,h/2)
                  self.rockMsg.draw()
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
                  self.failMsg.transform.reset()
                  self.failMsg.transform.scale(0.5, -0.5)
                  self.failMsg.transform.translate(w/2,h/2)
                  self.failMsg.draw()
                else:
                  self.finalFailed = True
                
            
              if self.pause:
                self.engine.view.setViewport(1,0)
                self.pauseScreen.transform.reset()
                self.pauseScreen.transform.scale(0.75, -0.75)
                self.pauseScreen.transform.translate(w/2+self.pause_bkg_x,h/2+self.pause_bkg_y)
                self.pauseScreen.draw()
                
              if self.finalFailed and self.song:
                self.engine.view.setViewport(1,0)
                self.failScreen.transform.reset()
                self.failScreen.transform.scale(0.75, -0.75)
                self.failScreen.transform.translate(w/2+self.fail_bkg_x,h/2+self.fail_bkg_y)
                self.failScreen.draw()
    
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

  
              if self.hopoIndicatorEnabled and not self.guitars[i].isDrum and not self.pause and not self.failed: #MFH - HOPO indicator (grey = strums required, white = strums not required)
                text = self.tsHopoIndicator
                if self.guitars[i].hopoActive > 0:
                  glColor3f(1.0, 1.0, 1.0)  #white
                else:
                  glColor3f(0.4, 0.4, 0.4)  #grey
                w, h = font.getStringSize(text,0.00150)
                font.render(text, (.950 - w / 2, .710),(1, 0, 0),0.00150)     #off to the right slightly above fretboard
                glColor3f(1, 1, 1)  #cracker white
    
                  
          elif (self.rmtype == 2):# and self.countdown<=4) or (self.theme == 1 and self.numOfPlayers==1):
            if not self.pauseScreen == None:
              w = self.wPlayer[i]
              h = self.hPlayer[i]
              wBak = w
              hBak = h
              if self.guitars[i].starPowerActive:
                #death_au: added checks for bass groove here so multiplier is correct    
                #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode > 0:
                if self.guitars[i].isBassGuitar and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode > 0:
                  if player.streak >= 50:
                    multiplier = 6
                    multRange = (3.0/4.0,4.0/4.0)
                    color = (.3,.7,.9,1)
                  else:
                    multiplier = 5
                    multRange = (2.0/4.0,3.0/4.0)
                    color = (.3,.7,.9,1)
                #death_au: end bass groove check
                elif player.streak >= 30:
                  multiplier = 4
                  multRange = (7.0/8.0,8.0/8.0)
                  color = (.3,.7,.9,1)
                elif player.streak >= 20:
                  multiplier = 3
                  multRange = (6.0/8.0,7.0/8.0)
                  color = (.3,.7,.9,1)
                elif player.streak >= 10:
                  multiplier = 2
                  multRange = (5.0/8.0,6.0/8.0)
                  color = (.3,.7,.9,1)
                else:
                  multiplier = 1
                  multRange = (4.0/8.0,5.0/8.0)
                  color = (.3,.7,.9,1)
              else:
                #death_au: added checks for bass groove here so multiplier is correct    
                #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode > 0:
                if self.guitars[i].isBassGuitar and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode > 0:
                  if player.streak >= 50:
                    multiplier = 6
                    multRange = (1.0/4.0,2.0/4.0)
                    color = (1,1,-1,1)
                  else:
                    multiplier = 5
                    multRange = (0.0/4.0,1.0/4.0)
                    color = (1,1,-1,1)
                #death_au: end bass groove check
                elif player.streak >= 30:
                  multiplier = 4
                  multRange = (3.0/8.0,4.0/8.0)
                  color = (1,-1,1,1)
                elif player.streak >= 20:
                  multiplier = 3
                  multRange = (2.0/8.0,3.0/8.0)
                  color = (-1,1,-.75,1)
                elif player.streak >= 10:
                  multiplier = 2
                  multRange = (1.0/8.0,2.0/8.0)
                  color = (1,1,-1,1)
                else:
                  multiplier = 1
                  multRange = (0.0/8.0,1.0/8.0)
                  color = (1,1,-1,1)
    
              #myfingershurt: for UC's RB mult
              if self.multRbFill:
                if player.streak == 0:
                  streak = 0
    
                elif player.streak - ((multiplier-1)*10) == 1:
                  streak = 0
    
                elif player.streak - ((multiplier-1)*10) == 2:
                  streak = 1
    
                elif player.streak - ((multiplier-1)*10) == 3:
                  streak = 2
    
                elif player.streak - ((multiplier-1)*10) == 4:
                  streak = 3
    
                elif player.streak - ((multiplier-1)*10) == 5:
                  streak = 4
    
                elif player.streak - ((multiplier-1)*10) == 6:
                  streak = 5
    
                elif player.streak - ((multiplier-1)*10) == 7:
                  streak = 6
    
                elif player.streak - ((multiplier-1)*10) == 8:
                  streak = 7
    
                elif player.streak - ((multiplier-1)*10) == 9:
                  streak = 8
    
                else:
                  streak = 9
    
  
              else:
                if player.streak == 0:
                  streak = 0
                  hstreak = 0
                elif player.streak - ((multiplier-1)*10) == 1:
                  streak = 0
                  hstreak = 1
                elif player.streak - ((multiplier-1)*10) == 2:
                  streak = 1
                  hstreak = 0
                elif player.streak - ((multiplier-1)*10) == 3:
                  streak = 1
                  hstreak = 1
                elif player.streak - ((multiplier-1)*10) == 4:
                  streak = 2
                  hstreak = 0
                elif player.streak - ((multiplier-1)*10) == 5:
                  streak = 2
                  hstreak = 1
                elif player.streak - ((multiplier-1)*10) == 6:
                  streak = 3
                  hstreak = 0
                elif player.streak - ((multiplier-1)*10) == 7:
                  streak = 3
                  hstreak = 1
                elif player.streak - ((multiplier-1)*10) == 8:
                  streak = 4
                  hstreak = 0
                elif player.streak - ((multiplier-1)*10) == 9:
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
    
              if currentRock == 1 and self.failingEnabled:
                if (self.coOp and i == 1) or not self.coOp:  #MFH only render for player 1 if co-op mode
                #if self.numOfPlayers > 1 and self.coOp:
                #  if i == 0:
                #    self.rockFull.transform.reset()
                #    self.rockFull.transform.translate(w*0.07,h*0.5)
                #    self.rockFull.transform.scale(.5,.5)
                #    self.rockFull.draw()
                #else:
                  self.rockFull.transform.reset()
                  self.rockFull.transform.translate(w*0.07,h*0.5)
                  self.rockFull.transform.scale(.5,.5)
                  self.rockFull.draw()
              else:
                if currentRock < 0.333:
                  fillColor = (1,0,0,1)
                elif currentRock < 0.666:
                  fillColor = (1,1,0,1)
                else:
                  fillColor = (0,1,0,1)
    

                if (self.coOp and i == 1) or not self.coOp:  #MFH only render for player 1 if co-op mode
                #if self.numOfPlayers > 1 and self.coOp:
                #  if i == 0:
                #    self.rockBottom.transform.reset()
                #    self.rockBottom.transform.scale(.5,.5)
                #    self.rockBottom.transform.translate(w*0.07, h*0.5)
                #    self.rockBottom.draw()
                #else:
                  self.rockBottom.transform.reset()
                  self.rockBottom.transform.scale(.5,.5)
                  self.rockBottom.transform.translate(w*0.07, h*0.5)
                  self.rockBottom.draw()
  
                if self.failingEnabled == False:
                  if (self.coOp and i == 1) or not self.coOp:  #MFH only render for player 1 if co-op mode
                  #if self.numOfPlayers > 1 and self.coOp:
                  #  if i == 0:
                  #    self.rockOff.transform.reset()
                  #    self.rockOff.transform.translate(w*0.07,h*0.5)
                  #    self.rockOff.transform.scale(.5,.5)
                  #    self.rockOff.draw()
                  #else:
                    self.rockOff.transform.reset()
                    self.rockOff.transform.translate(w*0.07,h*0.5)
                    self.rockOff.transform.scale(.5,.5)
                    self.rockOff.draw()
                else:
                  if (self.coOp and i == 1) or not self.coOp:  #MFH only render for player 1 if co-op mode
                  #if self.numOfPlayers > 1 and self.coOp:
                  #  if i == 0:
                  #    self.rockFill.transform.reset()
                  #    self.rockFill.transform.scale(.5,.5*currentRock)
                  #    self.rockFill.transform.translate(w*0.07, h*0.3-heightIncrease/2+heightIncrease)
                  #    self.rockFill.draw(color = fillColor)
                  #else:
                    self.rockFill.transform.reset()
                    self.rockFill.transform.scale(.5,.5*currentRock)
                    self.rockFill.transform.translate(w*0.07, h*0.3-heightIncrease/2+heightIncrease)
                    self.rockFill.draw(color = fillColor)
              
                if (self.coOp and i == 1) or not self.coOp:  #MFH only render for player 1 if co-op mode
                #if self.numOfPlayers > 1 and self.coOp:
                #  if i == 0:
                #    self.rockTop.transform.reset()
                #    self.rockTop.transform.scale(.5,.5)
                #    self.rockTop.transform.translate(w*0.07, h*0.5)
                #    self.rockTop.draw()
                #else:
                  self.rockTop.transform.reset()
                  self.rockTop.transform.scale(.5,.5)
                  self.rockTop.transform.translate(w*0.07, h*0.5)
                  self.rockTop.draw()
  
              wfactor = self.arrow.widthf(pixelw = 60.000)
  
            
              #myfingershurt: separate 2 player instrument icons
              if i == 0:
                #if self.numOfPlayers > 1 and self.coOp:
                #  self.arrow.transform.reset()
                #  self.arrow.transform.scale(wfactor,-wfactor)
                #  self.arrow.transform.translate(w*.1,h*.3+heightIncrease)
                #  if self.failingEnabled:  
                #    self.arrow.draw()
                #else:
                if not self.coOp:  #MFH only render for player 1 if co-op mode
                  self.arrow.transform.reset()
                  self.arrow.transform.scale(wfactor,-wfactor)
                  self.arrow.transform.translate(w*.1,h*.3+heightIncrease)
                  if self.failingEnabled:  
                    self.arrow.draw()
                whichScorePic = self.scorePic
              elif i == 1:
                #if self.numOfPlayers > 1 and self.coOp:
                #  self.arrowP2.transform.reset()
                #else:
                self.arrowP2.transform.reset()
                self.arrowP2.transform.scale(wfactor,-wfactor)
                self.arrowP2.transform.translate(w*.1,h*.3+heightIncrease)
                if self.failingEnabled:  
                  self.arrowP2.draw()
                whichScorePic = self.scorePicP2
    
              if not self.pause and not self.failed:
                currentSP = self.guitars[i].starPower/100.0
                widthChange = w*0.25
    
                self.oBottom.transform.reset()
                self.oBottom.transform.scale(.5,.5)
                self.oBottom.transform.translate(w/2,h/12)
                self.oBottom.draw()
                
                self.oFill.transform.reset()
                self.oFill.transform.scale(.5*currentSP,.5)
                self.oFill.transform.translate(w*0.5-widthChange+widthChange*currentSP,h/12)
                self.oFill.draw(rect = (0,currentSP,0,1))
    
  
                self.oTop.transform.reset()
                self.oTop.transform.scale(.5,.5)
                self.oTop.transform.translate(w/2,h/12)
                self.oTop.draw()
                if self.rb_sp_neck_glow and self.guitars[i].starPower >= 50 and not self.guitars[i].starPowerActive:
                  self.oFull.transform.reset()
                  self.oFull.transform.scale(.5,.5)
                  self.oFull.transform.translate(w/2,h/12)
                  self.oFull.draw(color = (1,1,1,self.rbOverdriveBarGlowVisibility))
                  
  
  #-              if self.rb_sp_neck_glow and self.guitars[i].starPower >= 50: #kk69: glow when star power is ready instead of when active
  #-                if self.guitars[i].starPowerActive:
  #-                  self.oTop.transform.reset()
  #-                  self.oTop.transform.scale(.5,.5)
  #-                  self.oTop.transform.translate(w/2,h/12)
  #-                  self.oTop.draw()
  #-                else:
  #-                  self.oTop.transform.reset()
  #-                  self.oTop.transform.scale(.5,.5)
  #-                  self.oTop.transform.translate(w/2,h/12)
  #-                  self.oTop.draw()
  #-
  #-                  self.oFull.transform.reset()
  #-                  self.oFull.transform.scale(.5,.5)
  #-                  self.oFull.transform.translate(w/2,h/12)
  #-                  self.oFull.draw(color = (1,1,1,self.rbOverdriveBarGlowVisibility))
  #-              else:
  #-                self.oTop.transform.reset()
  #-                self.oTop.transform.scale(.5,.5)
  #-                self.oTop.transform.translate(w/2,h/12)
  #-                self.oTop.draw()
  

                
                #must duplicate to other theme 
                #if self.playerList[i].part.text == "Bass Guitar" and player.streak >= 40 and self.bassGrooveEnableMode > 0:   #bass groove!
                if self.guitars[i].isBassGuitar and player.streak >= 40 and self.bassGrooveEnableMode > 0:   #bass groove!
                  #death_au: bassgroove multiplier image
                  if self.bassgroovemult != None:
                    text = self.tsBassGroove   #kk69: displays "Bass Groove" whenever active, like Rock Band (only for RB theme)
                    wid, hig = font.getStringSize(text,0.00150)
                    
                    #MFH - if Jurgen is active on the current player, raise "Bass Groove" up above "Jurgen Is Here":
                    if (i == 0 and self.jurg1) or (i == 1 and self.jurg2):
                      font.render(text, (0.47 - wid / 2, 0.165),(1, 0, 0),0.00210)#end kk69
                    else:
                      font.render(text, (0.47 - wid / 2, 0.190),(1, 0, 0),0.00210)#end kk69
  
                    #UC's mult
                    if self.multRbFill and player.streak > 0:
                      self.mult2.transform.reset()
                      self.mult2.transform.scale(.95,-.82/8.0)
                      self.mult2.transform.translate(w*0.5023,h*0.0585)         
                      self.mult2.draw(rect = (0,1,(streak/10.0),(streak+1)/10.0))
                      
                    self.bassgroovemult.transform.reset()
                    if self.multRbFill:
                      self.bassgroovemult.transform.scale(.8,-.8/4.0)
                      self.bassgroovemult.transform.translate(w*0.5,h*0.05)                  
                    else:
                      self.bassgroovemult.transform.scale(.5,-.5/4.0)
                      self.bassgroovemult.transform.translate(w*0.5,h*0.05)
                    self.bassgroovemult.draw(rect = (0,1,multRange[0],multRange[1]))
  
  
                  else:
                    #myfingershurt: Temp text bass groove multiplier:
                    glColor3f(0,0.75,1)


                    #text = self.tsBassGrooveLabel + str(self.playerList[i].getScoreMultiplier() * self.multi[i]) + "x"
                    text = "%s%d%s" % (self.tsBassGrooveLabel, self.playerList[i].getScoreMultiplier() * self.multi[i], "x")
                    wid, hig = font.getStringSize(text,0.00150)
                    font.render(text, (.500 - wid / 2, .690),(1, 0, 0),0.00150)     #replacing normal rock band multiplier text
                
                else:              
    
                  #myfingershurt: UC's mult
                  if self.multRbFill and player.streak > 0:
                    self.mult2.transform.reset()
                    if self.rbmfx: #blazingamer
                      if player.streak > 9:   #draw bigger!
                        self.mult2.transform.scale(.95,-.82/8.0)
                        self.mult2.transform.translate(w*0.5023,h*0.0585)
                      else:
                        #myfingershurt: overlay streak perfectly:
                        self.mult2.transform.scale(.6,-.5/8.0)
                        self.mult2.transform.translate(w*0.501,h*0.055)
                    else:
                      self.mult2.transform.scale(.95,-.82/8.0)
                      self.mult2.transform.translate(w*0.5023,h*0.0585)         
                    self.mult2.draw(rect = (0,1,(streak/10.0),(streak+1)/10.0))
  
                  self.mult.transform.reset()
                  if self.multRbFill:
                    if self.rbmfx:  #blazingamer
                      if player.streak > 9:   #draw bigger!
                        self.mult.transform.scale(.8,-.8/8.0)
                        self.mult.transform.translate(w*0.5,h*0.05)
                      else:
                        self.mult.transform.scale(.5,-.5/8.0)
                        self.mult.transform.translate(w*0.5,h*0.05)
                    else:
                      self.mult.transform.scale(.8,-.8/8.0)
                      self.mult.transform.translate(w*0.5,h*0.05)                  
                  else:
                    self.mult.transform.scale(.5,-.5/8.0)
                    self.mult.transform.translate(w*0.5,h*0.05)
                  self.mult.draw(rect = (0,1,multRange[0],multRange[1]))
  
                
              glColor4f(1,1,1,1)
   
              
              try:
  
  
                #myfingershurt: locale.format call adds commas to separate numbers just like Rock Band

                #if (self.coOp and i == 0) or not self.coOp:  #MFH only render for player 0 if co-op mode
                if (self.coOp and i == 1) or not self.coOp:  #MFH only render for player 1 if co-op mode
  
                  if self.coOp:
                    score=self.coOpScore
                    for playaNum, playa in enumerate(self.playerList):
                      score += self.getExtraScoreForCurrentlyPlayedNotes(playaNum)
                  else:
                    score=player.score
                    score += self.getExtraScoreForCurrentlyPlayedNotes(i)

                  scoretext = locale.format("%d", score, grouping=True)
                  #myfingershurt: swapping the number "0" and the letter "O" in the score font for accurate Rock Band score type!
                  scoretext = scoretext.replace("0","O")
                  scW, scH = scoreFont.getStringSize(scoretext)
  
                  scorepicheight = whichScorePic.height1()
                  whichScorePic.transform.reset()
                  whichScorePic.transform.scale(.5,.5)
                  whichScorePic.transform.translate(w*0.9, h*0.8304)    #just below lyric sheet, last change -.0000
                  whichScorePic.draw()

                  scoreFont.render(scoretext, (0.97-scW, 0.1050 ))    #last change +0.0015

                #myfingershurt: locale.format call adds commas to separate numbers just like Rock Band
                streaktext = locale.format("%d", player.streak, grouping=True)
                #myfingershurt: swapping the number "0" and the letter "O" in the score font for accurate Rock Band score type!
                streaktext = streaktext.replace("0","O")
                stW, stH = streakFont.getStringSize(streaktext)
  
  
                #streak counter box:
  
                counterimgheight = self.counter.height1()
                self.counter.transform.reset()
                self.counter.transform.translate(w*.915, h*0.7720)    #just below score box, last change -.0000
                self.counter.transform.scale(.5,-.5)
                self.counter.draw()
                streakFont.render(streaktext, (0.97-stW,0.1500 ))    #last change +0.0015
  
              except Exception, e:
                #Log.warn("Unable to render score/streak text: %s" % e)
                scorepicheight = 0  #exception placeholder
    
  
              if self.displayText[i] != None:
                glColor3f(.8,.75,.01)
                size = sphraseFont.getStringSize(self.displayText[i], scale = self.dislayTextScale[i])
                sphraseFont.render(self.displayText[i], (.5-size[0]/2,self.textY[i]-size[1]), scale = self.dislayTextScale[i])
    
              if self.youRock == True:
                if self.rockTimer == 1:
                  #self.sfxChannel.setVolume(self.sfxVolume)
                  self.engine.data.rockSound.play()
                  for num, thePlayer in enumerate(self.playerList):   #MFH - flash overdrive strings in RB theme
                    self.guitars[num].overdriveFlashCount = 0  #MFH - this triggers the oFlash strings & timer
                    self.guitars[num].ocount = 0  #MFH - this triggers the oFlash strings & timer
                if self.rockTimer < self.rockCountdown:
                  self.rockTimer += 1
                  self.rockMsg.transform.reset()
                  self.rockMsg.transform.scale(0.5, -0.5)
                  self.rockMsg.transform.translate(w/2,h/2)
                  self.rockMsg.draw()
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
                  self.failMsg.transform.reset()
                  self.failMsg.transform.scale(0.5, -0.5)
                  self.failMsg.transform.translate(w/2,h/2)
                  self.failMsg.draw()
                else:
                  self.finalFailed = True
                
            
              if self.pause:
                self.engine.view.setViewport(1,0)
                self.pauseScreen.transform.reset()
                self.pauseScreen.transform.scale(0.75, -0.75)
                self.pauseScreen.transform.translate(w/2+self.pause_bkg_x,h/2+self.pause_bkg_y)
                self.pauseScreen.draw()
                
              if self.finalFailed and self.song:
                self.engine.view.setViewport(1,0)
                self.failScreen.transform.reset()
                self.failScreen.transform.scale(0.75, -0.75)
                self.failScreen.transform.translate(w/2+self.fail_bkg_x,h/2+self.fail_bkg_y)
                self.failScreen.draw()
    
                text = Dialogs.removeSongOrderPrefixFromName(self.song.info.name)
                size = font.getStringSize(text)
                font.render(text, (.5-size[0]/2.0,.3-size[1]))
                #now = self.getSongPosition()

                pctComplete = min(100, int(now/self.lastEvent*100))
                #MFH string concatenation -> modulo formatting
                #text = str(pctComplete) + self.tsPercentComplete
                text = "%s%s" % (str(pctComplete), self.tsPercentComplete)
                size = font.getStringSize(text)
                font.render(text, (.5-size[0]/2.0, .3))
                if not self.failEnd:
                  self.failGame()
    
               #QQstarS:add the code in for loop end of here		
  
              if self.hopoIndicatorEnabled and not self.guitars[i].isDrum and not self.pause and not self.failed: #MFH - HOPO indicator (grey = strums required, white = strums not required)
                text = self.tsHopoIndicator
                if self.guitars[i].hopoActive > 0:
                  glColor3f(1.0, 1.0, 1.0)  #white
                else:
                  glColor3f(0.4, 0.4, 0.4)  #grey
                w, h = font.getStringSize(text,0.00150)
                font.render(text, (.950 - w / 2, .725),(1, 0, 0),0.00150)     #off to the right slightly above fretboard
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
                    #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                    if self.guitars[i].isBassGuitar and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                      if player.streak >= 50:
                        multiplier = 6
                        multRange = (0.75,1.00) #MFH division->constant: was (3.0/4.0,4.0/4.0)
                        color = (1,0,0.75,1)
                      else:
                        multiplier = 5
                        multRange = (0.5,0.75) #MFH division->constant: was (2.0/4.0,3.0/4.0)
                        color = (1,0,0.75,1)
                      xs = (0.75,1)
                    #death_au: end check for bass groove
                    elif player.streak >= 30:
                      multiplier = 4
                      multRange = (0.875,1.0) #MFH division->constant: was (7.0/8.0,8.0/8.0)
                      color = (.3,.7,.9,1)
                      xs = (0.75,1)
                    elif player.streak >= 20:
                      multiplier = 3
                      multRange = (0.75,0.875) #MFH division->constant: was (6.0/8.0,7.0/8.0)
                      color = (.3,.7,.9,1)
                      xs = (0.75,1)
                    elif player.streak >= 10:
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
                    #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                    if self.guitars[i].isBassGuitar and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                      if player.streak >= 50:
                        multiplier = 6
                        multRange = (0.75,1.0) #MFH division->constant: was (3.0/4.0,4.0/4.0)
                        color = (1,0,0.75,1)
                      else:
                        multiplier = 5
                        multRange = (0.5,0.75) #MFH division->constant: was (2.0/4.0,3.0/4.0)
                        color = (1,0,0.75,1)
                    #death_au: end check for bass groove
                    elif player.streak >= 30:
                      multiplier = 4
                      multRange = (0.875,1.0) #MFH division->constant: was (7.0/8.0,8.0/8.0)
                      color = (.3,.7,.9,1)
                    elif player.streak >= 20:
                      multiplier = 3
                      multRange = (0.75,0.875) #MFH division->constant: was (6.0/8.0,7.0/8.0)
                      color = (.3,.7,.9,1)
                    elif player.streak >= 10:
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
                    #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                    if self.guitars[i].isBassGuitar and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                      if player.streak >= 50:
                        multiplier = 6
                        multRange = (0.25,0.5) #MFH division->constant: was (1.0/4.0,2.0/4.0)
                        color = (1,0,0.75,1)
                      else:
                        multiplier = 5
                        multRange = (0.0,0.25) #MFH division->constant: was (0.0/4.0,1.0/4.0)
                        color = (1,0,0.75,1)
                      xs = (0.75,1)
                    #death_au: end check for bass groove
                    elif player.streak >= 30:
                      multiplier = 4
                      multRange = (0.375,0.5) #MFH division->constant: was (3.0/8.0,4.0/8.0)
                      color = (1,-1,1,1)
                      xs = (0.5,0.75)
                    elif player.streak >= 20:
                      multiplier = 3
                      multRange = (0.25,0.375) #MFH division->constant: was (2.0/8.0,3.0/8.0)
                      color = (-1,1,-.75,1)
                      xs = (0.25,0.5)
                    elif player.streak >= 10:
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
                    #if self.playerList[i].part.text == "Bass Guitar" and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                    if self.guitars[i].isBassGuitar and self.bassgroovemult != None and player.streak >= 40 and self.bassGrooveEnableMode == 2:
                      if player.streak >= 50:
                        multiplier = 6
                        multRange = (0.25,0.5) #MFH division->constant: was (1.0/4.0,2.0/4.0)
                        color = (1,0,0.75,1)
                      else:
                        multiplier = 5
                        multRange = (0.0,0.25) #MFH division->constant: was (0.0/4.0,1.0/4.0)
                        color = (1,0,0.75,1)
                      xs = (0.75,1)
                    #death_au: end check for bass groove
                    elif player.streak >= 30:
                      multiplier = 4
                      multRange = (0.375,0.5) #MFH division->constant: was (3.0/8.0,4.0/8.0)
                      color = (1,-1,1,1)
                    elif player.streak >= 20:
                      multiplier = 3
                      multRange = (0.25,0.375) #MFH division->constant: was (2.0/8.0,3.0/8.0)
                      color = (-1,1,-.75,1)
                    elif player.streak >= 10:
                      multiplier = 2
                      multRange = (0.125,0.25) #MFH division->constant: was (1.0/8.0,2.0/8.0)
                      color = (1,1,-1,1)
                    else:
                      multiplier = 1
                      multRange = (0.0,0.125) #MFH division->constant: was (0.0/8.0,1.0/8.0)
                      color = (1,1,-1,1)
            
              
              #myfingershurt: GH bass groove multiplier: 
              # death_au: added drawing of bassgroovemult image             
              #if self.playerList[i].part.text == "Bass Guitar" and player.streak >= 40 and self.bassGrooveEnableMode == 2:   #bass groove!
              if self.guitars[i].isBassGuitar and player.streak >= 40 and self.bassGrooveEnableMode == 2:   #bass groove!
                if self.bassgroovemult != None: #death_au : bassgroovemult image found, draw image
                      
                  self.bassgroovemult.transform.reset()
                  self.bassgroovemult.transform.scale(.5,-.125) #MFH division->constant: was (.5,-.5/4.0)
                  self.bassgroovemult.transform.translate(w*0.134,h*0.19 + self.hOffset[i]) #QQstarS:Set  new postion. I only shown it once.
                  self.bassgroovemult.draw(rect = (0,1,multRange[0],multRange[1]))
                
                else: #death_au: bassgroovemult not found
                  #myfingershurt: Temp text bass groove multiplier:
                  glColor3f(0,0.75,1)
                  text = str(self.playerList[i].getScoreMultiplier() * self.multi[i])
                  wid, hig = font.getStringSize(text,0.00325)
                  font.render(text, (.133 - wid / 2, .566),(1, 0, 0),0.00325)     #replacing GH multiplier large text
  
  
              else:
                self.mult.transform.reset()
                self.mult.transform.scale(.5,-.0625) #MFH division->constant: was (.5,-.5/8.0)
                self.mult.transform.translate(w*0.674,h*0.397 + self.hOffset[i]) #QQstarS:Set  new postion. I only shown it once.
                self.mult.draw(rect = (0,1,multRange[0],multRange[1]))
  
              if player.streak == 0:
                streak = 0
                hstreak = 0
              elif player.streak - ((multiplier-1)*10) == 1:
                streak = 0
                hstreak = 1  
              elif player.streak - ((multiplier-1)*10) == 2:
                streak = 1
                hstreak = 0
              elif player.streak - ((multiplier-1)*10) == 3:
                streak = 1
                hstreak = 1
              elif player.streak - ((multiplier-1)*10) == 4:
                streak = 2
                hstreak = 0
              elif player.streak - ((multiplier-1)*10) == 5:
                streak = 2
                hstreak = 1
              elif player.streak - ((multiplier-1)*10) == 6:
                streak = 3
                hstreak = 0
              elif player.streak - ((multiplier-1)*10) == 7:
                streak = 3
                hstreak = 1
              elif player.streak - ((multiplier-1)*10) == 8:
                streak = 4
                hstreak = 0
              elif player.streak - ((multiplier-1)*10) == 9:
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
                  r.transform.reset()
                  r.transform.scale(0.125,-.166666667) #MFH division->constant: was (.5*(1.0/4.0),-.5*(1.0/3.0))
                  r.transform.translate(w*.701+t*(w*-.0106),h*.256+t*(h*.026) + self.hOffset[i])
                  r.draw(rect = (xs[0],xs[1],ys[0],ys[1]))
                else:
                  r.transform.reset()
                  r.transform.scale(.5,-.166666667) #MFH division->constant: was (.5,-.5*(1.0/3.0))
                  r.transform.translate(w*.044,h*.12+t*(h*.034) + self.hOffset[i])
                  r.draw(color = color, rect = (0.0,1.0,ys[0],ys[1]))
  
    
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
                self.SP.transform.reset()
                self.SP.transform.rotate(.87)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*.036,h*.487 + self.hOffset[i]) #Worldrave Width and Height was h*0.310
                self.SP.draw(rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.SP.transform.reset()
                self.SP.transform.rotate(.87) #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*.036, h*.487 + self.hOffset[i]) #Worldrave Change
                self.SP.draw(rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
      
                if self.guitars[i].starPower >= 33.2: #QQstarS:Set [0] to [i]
                  lightVis = 1
                else:
                  lightVis = (self.guitars[i].starPower-16.6)/16.6
                wfactor = self.SP.widthf(pixelw = 23.000) #Worldrave Change - Bulb 2
                self.SP.transform.reset()
                self.SP.transform.rotate(.58)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*.059,h*.515 + self.hOffset[i])  #Worldrave Change
                self.SP.draw(rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.SP.transform.reset()
                self.SP.transform.rotate(.58)  #evilynux - should be the same
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*.059,h*.515 + self.hOffset[i])  #Worldrave Change
                self.SP.draw(rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
      
                if self.guitars[i].starPower >= 49.8:
                  lightVis = 1
                else:
                  lightVis = (self.guitars[i].starPower-32.2)/16.6
    
                wfactor = self.SP.widthf(pixelw = 23.000)  #Worldrave Change - Bulb 3
                self.SP.transform.reset()
                self.SP.transform.rotate(.37)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*.086,h*.532 + self.hOffset[i]) #Worldrave Width and Height was h*0.338
                self.SP.draw(rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.SP.transform.reset()
                self.SP.transform.rotate(.37)  #evilynux - should be the same
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*.086,h*.532 + self.hOffset[i])  #Worldrave Change
                self.SP.draw(rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
      
                if self.guitars[i].starPower >= 66.4:
                  lightVis = 1
                else:
                  lightVis = (self.guitars[i].starPower-49.8)/16.6
    
                wfactor = self.SP.widthf(pixelw = 32.000) #Worldrave Change - Bulb 4
                self.SP.transform.reset()
                self.SP.transform.rotate(.0)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*self.x1[i]*0.96652469,h*self.y1[i]*1.011455279 + self.hOffset[i])  #evilynux - fixed for all resolutions
                self.SP.draw(rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.SP.transform.reset()
                self.SP.transform.rotate(.0)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*self.x1[i]*0.96652469,h*self.y1[i]*1.011455279 + self.hOffset[i])  #evilynux - fixed for all resolutions
                self.SP.draw(rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
      
                if self.guitars[i].starPower >= 83:
                  lightVis = 1
                else:
                  lightVis = (self.guitars[i].starPower-66.4)/16.6
    
                wfactor = self.SP.widthf(pixelw = 32.000)  #Worldrave Change - Bulb 5  
                self.SP.transform.reset()
                self.SP.transform.rotate(-.40)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*self.x2[i]*0.976698075,h*self.y2[i]*1.02813143 + self.hOffset[i])  #evilynux - fixed for all resolutions
                self.SP.draw(rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.SP.transform.reset()
                self.SP.transform.rotate(-.40)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*self.x2[i]*0.976698075,h*self.y2[i]*1.02813143 + self.hOffset[i])  #evilynux - fixed for all resolutions
                self.SP.draw(rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))
      
                if self.guitars[i].starPower >= 100:
                  lightVis = 1
                else:
                  lightVis = (self.guitars[i].starPower-83)/16.6
    
                wfactor = self.SP.widthf(pixelw = 32.000) #Worldrave Change - Bulb 6
                self.SP.transform.reset()
                self.SP.transform.rotate(-.75)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*self.x3[i]*0.986664588,h*self.y3[i]*1.04973235 + self.hOffset[i])  #evilynux - fixed for all resolutions
                self.SP.draw(rect = (0,1.0/3.1,0,1), color = (1,1,1,1))
                self.SP.transform.reset()
                self.SP.transform.rotate(-.75)  #Worldrave Change
                self.SP.transform.scale(wfactor,-wfactor*3)
                self.SP.transform.translate(w*self.x3[i]*0.986664588,h*self.y3[i]*1.04973235 + self.hOffset[i])  #evilynux - fixed for all resolutions
                self.SP.draw(rect = (lightPos[0],lightPos[1],0,1), color = (1,1,1,lightVis))

                        
              self.rockmeter.transform.reset()
              self.rockmeter.transform.scale(.5,-.5)
              self.rockmeter.transform.translate(w*.134, h*.23 + self.hOffset[i])
              self.rockmeter.draw()

              #if (self.coOp and i == 0) or not self.coOp:  #MFH only render for player 0 if co-op mode
              if (self.coOp and i == 1) or not self.coOp:  #MFH only render for player 1 if co-op mode

                if self.coOp:
                  score=self.coOpScore
                  for playaNum, playa in enumerate(self.playerList):
                    score += self.getExtraScoreForCurrentlyPlayedNotes(playaNum)
                else:
                  score=player.score
                  score += self.getExtraScoreForCurrentlyPlayedNotes(i)

                size      = scoreFont.getStringSize(str(score))
                x = 0.19-size[0]
                # evilynux - Changed upon worldrave's request
                c1,c2,c3 = self.rockmeter_score_color
                glColor3f(c1,c2,c3)
                #if self.numOfPlayers > 1 and i == 0:
                #  scoreFont.render("%d" % (player.score + self.getExtraScoreForCurrentlyPlayedNotes(i)), (x, 0.507+self.hFontOffset[i]))
                #else:
                scoreFont.render("%d" % (score),  (x, 0.507+self.hFontOffset[i]))
    
              #MFH - rock measurement tristate
              #if self.rock[i] > self.rockMax/3.0*2:
              if self.rock[i] > self.rockHiThreshold:
                rock = self.rockHi
              #elif self.rock[i] > self.rockMax/3.0:
              elif self.rock[i] > self.rockMedThreshold:
                rock = self.rockMed
              else:
                rock = self.rockLo
    
              rockx = .13
              rocky = .426
              if self.failingEnabled:
                rock.transform.reset()
                rock.transform.scale(.5,-.5)
                rock.transform.translate(w*rockx,h*rocky + self.hOffset[i])
                rock.draw()
              else:
                self.rockOff.transform.reset()
                self.rockOff.transform.scale(.5,-.5)
                self.rockOff.transform.translate(w*rockx,h*rocky + self.hOffset[i])
                self.rockOff.draw()
    
              currentRock = (0.0 + self.rock[i]) / (self.rockMax)
              if self.rock[i] >= 0:
                self.arrowRotation[i] += ( 0.0 + currentRock - self.arrowRotation[i]) / 5.0
              else:  #QQstarS: Fix the arrow let him never rotation to bottom
                self.arrowRotation[i] = self.arrowRotation[i]
              angle = -(.460 / 2) * math.pi + .460 * math.pi * self.arrowRotation[i]
              wfactor = self.arrow.widthf(pixelw = 60.000)
  
              if self.failingEnabled:
                self.arrow.transform.reset()
                self.arrow.transform.scale(wfactor,-wfactor)
                self.arrow.transform.rotate(angle) 
                self.arrow.transform.translate(w*rockx,h*(rocky-.056 + self.hOffset[i]))
                self.arrow.draw()
    
              self.rockTop.transform.reset()
              self.rockTop.transform.scale(.5,-.5)
              self.rockTop.transform.translate(w*rockx,h*rocky + self.hOffset[i])
              self.rockTop.draw()
    

              glColor4f(.85,.47,0,1)
              streak = player.streak
              text = str(streak)
              size = streakFont.getStringSize(text)
              streakFont.render(text, (.193-size[0], 0.548+self.hFontOffset[i]))
    
  
              if self.displayText[i] != None:
                glColor3f(.8,.75,.01)
                size = sphraseFont.getStringSize(self.displayText[i], scale = self.dislayTextScale[i])
                sphraseFont.render(self.displayText[i], (.5-size[0]/2,self.textY[i]-size[1]), scale = self.dislayTextScale[i])
    
              if self.youRock == True:
                if self.rockTimer == 1:
                  #self.sfxChannel.setVolume(self.sfxVolume)
                  self.engine.data.rockSound.play()
                if self.rockTimer < self.rockCountdown:
                  self.rockTimer += 1
                  self.rockMsg.transform.reset()
                  self.rockMsg.transform.scale(0.5, -0.5)
                  self.rockMsg.transform.translate(w/2,h/2)
                  self.rockMsg.draw()
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
                  self.failMsg.transform.reset()
                  self.failMsg.transform.scale(0.5, -0.5)
                  self.failMsg.transform.translate(w/2,h/2)
                  self.failMsg.draw()
                else:
                  self.finalFailed = True
                
            
              if self.pause:
                self.engine.view.setViewport(1,0)
                self.pauseScreen.transform.reset()
                self.pauseScreen.transform.scale(0.75, -0.75)
                self.pauseScreen.transform.translate(w/2+self.pause_bkg_x,h/2+self.pause_bkg_y)
                self.pauseScreen.draw()
                
              if self.finalFailed and self.song:
                self.engine.view.setViewport(1,0)
                self.failScreen.transform.reset()
                self.failScreen.transform.scale(0.75, -0.75)
                self.failScreen.transform.translate(w/2+self.fail_bkg_x,h/2+self.fail_bkg_y)
                self.failScreen.draw()
    
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
          if (self.coOp and i == 1) or not self.coOp:  #MFH only render for player 1 if co-op mode

            if self.coOp:
              stars=self.coOpStars
              partialStars=self.coOpPartialStars
            else:
              stars=player.stars
              partialStars=self.partialStar[i]

            w = wBak
            h = hBak
            if (self.inGameStars == 2 or (self.inGameStars == 1 and self.theme == 2) )  and not self.pause and not self.failed: #MFH - only show stars if in-game stars enabled
              if self.starGrey != None:
                for starNum in range(0, 5):
                  if stars == 6:    #perfect!
                    self.starPerfect.transform.reset()
                    self.starPerfect.transform.scale(.080,-.080)
                    self.starPerfect.transform.translate(w*(0.802 + 0.040*(starNum)),h*0.7160)
                    self.starPerfect.draw()
                  elif starNum == stars:
                    #if self.starGrey1 and self.starScoring == 2:  #if more complex star system is enabled, and we're using Rock Band style scoring
                    if self.starGrey1:
                      if partialStars == 0:
                        self.starGrey.transform.reset()
                        self.starGrey.transform.scale(.080,-.080)
                        self.starGrey.transform.translate(w*(0.802 + 0.040*(starNum)),h*0.7160)
                        self.starGrey.draw()
                      elif partialStars == 1:
                        self.starGrey1.transform.reset()
                        self.starGrey1.transform.scale(.080,-.080)
                        self.starGrey1.transform.translate(w*(0.802 + 0.040*(starNum)),h*0.7160)
                        self.starGrey1.draw()
                      elif partialStars == 2:
                        self.starGrey2.transform.reset()
                        self.starGrey2.transform.scale(.080,-.080)
                        self.starGrey2.transform.translate(w*(0.802 + 0.040*(starNum)),h*0.7160)
                        self.starGrey2.draw()
                      elif partialStars == 3:
                        self.starGrey3.transform.reset()
                        self.starGrey3.transform.scale(.080,-.080)
                        self.starGrey3.transform.translate(w*(0.802 + 0.040*(starNum)),h*0.7160)
                        self.starGrey3.draw()
                      elif partialStars == 4:
                        self.starGrey4.transform.reset()
                        self.starGrey4.transform.scale(.080,-.080)
                        self.starGrey4.transform.translate(w*(0.802 + 0.040*(starNum)),h*0.7160)
                        self.starGrey4.draw()
                      elif partialStars == 5:
                        self.starGrey5.transform.reset()
                        self.starGrey5.transform.scale(.080,-.080)
                        self.starGrey5.transform.translate(w*(0.802 + 0.040*(starNum)),h*0.7160)
                        self.starGrey5.draw()
                      elif partialStars == 6:
                        self.starGrey6.transform.reset()
                        self.starGrey6.transform.scale(.080,-.080)
                        self.starGrey6.transform.translate(w*(0.802 + 0.040*(starNum)),h*0.7160)
                        self.starGrey6.draw()
                      elif partialStars == 7:
                        self.starGrey7.transform.reset()
                        self.starGrey7.transform.scale(.080,-.080)
                        self.starGrey7.transform.translate(w*(0.802 + 0.040*(starNum)),h*0.7160)
                        self.starGrey7.draw()
                      
                    else:
                      self.starGrey.transform.reset()
                      self.starGrey.transform.scale(.080,-.080)
                      self.starGrey.transform.translate(w*(0.802 + 0.040*(starNum)),h*0.7160)
                      self.starGrey.draw()
    
                  elif starNum > stars:
                    if self.displayAllGreyStars:
                      self.starGrey.transform.reset()
                      self.starGrey.transform.scale(.080,-.080)
                      self.starGrey.transform.translate(w*(0.802 + 0.040*(starNum)),h*0.7160)
                      self.starGrey.draw()
    
                  else:   #white star
                    self.starWhite.transform.reset()
                    self.starWhite.transform.scale(.080,-.080)
                    self.starWhite.transform.translate(w*(0.802 + 0.040*(starNum)),h*0.7160)
                    self.starWhite.draw()
  
          if self.song:
    
  
            if self.dispSoloReview[i] and not self.pause and not self.failed:
              self.engine.view.setViewportHalf(self.numOfPlayers,i)
              if self.soloReviewCountdown[i] < self.soloReviewDispDelay:
                self.soloReviewCountdown[i] += 1
                #glColor3f(0, 0.85, 1)  #grn-blu
                glColor3f(1, 1, 1)  #cracker white
                text1 = self.soloReviewText[i][0]
                text2 = self.soloReviewText[i][1]
                xOffset = 0.950
                if self.hitAccuracyPos == 0: #Center - need to move solo review above this!
                  yOffset = 0.080
                elif i == 0 and self.jurg1 and self.autoPlay:
                  yOffset = 0.115    #above Jurgen Is Here
                elif i == 1 and self.jurg2 and self.autoPlay:
                  yOffset = 0.115    #above Jurgen Is Here
                else:   #no jurgens here:
                  yOffset = 0.190
                txtSize = 0.00185
                
                if self.theme == 2:
                  soloFont = scoreFont
                else:
                  soloFont = font
                


                Tw, Th = soloFont.getStringSize(text1,txtSize)
                Tw2, Th2 = soloFont.getStringSize(text2,txtSize)

                

                #MFH - scale and display self.soloFrame behind / around the text
                if self.soloFrame:
                  frameWidth = (max(Tw,Tw2))*1.15
                  frameHeight = (Th+Th2)*1.05
                  boxXOffset = 0.5
                  #MFH - font Y position = top of text to be written
                  boxYOffset = self.hPlayer[i]-(self.wFull* (yOffset+(frameHeight/1.97)) )
                  self.soloFrame.transform.reset()
                  tempWScale = frameWidth*self.soloFrameWFactor
                  tempHScale = -(frameHeight)*self.soloFrameWFactor
                  self.soloFrame.transform.scale(tempWScale,tempHScale)
                  self.soloFrame.transform.translate(self.wPlayer[i]*boxXOffset,boxYOffset)
                  self.soloFrame.draw()

                soloFont.render(text1, (0.5 - Tw/2, yOffset),(1, 0, 0),txtSize)   #centered
                soloFont.render(text2, (0.5 - Tw2/2, yOffset+Th+txtSize),(1, 0, 0),txtSize)   #centered
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
    
      
            #MFH: Realtime hit accuracy display:
            
            #if ((self.inGameStats == 2 or (self.inGameStats == 1 and self.theme == 2)) and (not self.pause and not self.failed)) and ( (not self.pause and not self.failed) or self.hopoDebugDisp == 1 ):
            if ((self.inGameStats == 2 or (self.inGameStats == 1 and self.theme == 2) or self.hopoDebugDisp == 1 ) and (not self.pause and not self.failed)):
              #will not show on pause screen, unless HOPO debug is on (for debugging)
              trimmedTotalNoteAcc = self.decimal(str(self.hitAccuracy[i])).quantize(self.decPlaceOffset)
              #text = str(self.playerList[i].notesHit) + "/" + str(self.playerList[i].totalStreakNotes) + ": " + str(trimmedTotalNoteAcc) + "%"
              text = "%(notesHit)s/%(totalNotes)s: %(hitAcc)s%%" % \
                {'notesHit': str(self.playerList[i].notesHit), 'totalNotes': str(self.playerList[i].totalStreakNotes), 'hitAcc': str(trimmedTotalNoteAcc)}
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
              trimmedAvMult = self.decimal(str(self.avMult[i])).quantize(self.decPlaceOffset)
              #text = _("Avg: ") + str(trimmedAvMult) + "x"

              #avgLabel = _("Avg")
              text = "%(avLab)s: %(avMult)sx" % \
                {'avLab': self.tsAvgLabel, 'avMult': str(trimmedAvMult)}
              glColor3f(c1, c2, c3)
              w, h = font.getStringSize(text,0.00160)
              font.render(text, (accDispX - w/2, accDispYam),(1, 0, 0),0.00140)     #top-centered by streak under score
            
            
            
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
    
              posX = 0.90
              posY = 0.250
    
              if self.hitAccuracyPos == 0: #Center
                posX = .500
                posY = .305 + h
                if self.showAccuracy == 3:    #for displaying numerical below descriptive
                  posY = .305
                #if self.pov != 1: #not GH POV
                #  posY = y + 4 * h   -- MFH: this line causes a bad hang.
              elif self.hitAccuracyPos == 2:#Left-bottom
                posX = .193
                posY = .700		#(.193-size[0]/2, 0.667-size[1]/2+self.hFontOffset[i]))
              elif self.hitAccuracyPos == 3: #Center-bottom
                posX = .500
                posY = .710			
    
    
              if self.theme == 2:
                #RB mod
                font.render(text, (posX - w / 2, posY - h / 2),(1, 0, 0),0.00170)    
              else:
                #gh3 or other standard mod
                font.render(text, (posX - w / 2, posY - h / 2),(1, 0, 0),0.00170)    

    
              if self.showAccuracy == 3:    #for displaying numerical below descriptive
                #text = str(self.accuracy)
                #text = str(trimmedAccuracy) + " ms"
                #msText = _("ms")
                text = "%(acc)s %(ms)s" % \
                  {'acc': str(trimmedAccuracy), 'ms': self.msLabel}
                w, h = font.getStringSize(text,0.00140)
                if self.theme == 2:   #RB mod
                  font.render(text, (posX - w / 2, posY - h / 2 + .030),(1, 0, 0),0.00140) 
                else:   #GH3 or other standard mod
                  font.render(text, (posX - w / 2, posY - h / 2 + .030),(1, 0, 0),0.00140) 
                  
    
            glColor3f(1, 1, 1)
  
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
                  picture.transform.reset()
                  picture.transform.translate(w / 2, (f * -2 + 1) * h/2+yOffset)
                  
                  picture.transform.scale(1, -1)
                  picture.draw()
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
  
            #handle the guitar solo track
            if (self.readTextAndLyricEvents == 2 or (self.readTextAndLyricEvents == 1 and self.theme == 2)) and (not self.pause and not self.failed and not self.ending):

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
                        #Guitar Solo Start
                        self.currentGuitarSoloTotalNotes[i] = self.guitarSolos[i][self.currentGuitarSolo[i]]
                        self.guitarSoloBroken[i] = False
                        self.guitars[i].guitarSolo = True
                        #self.displayText[i] = _("Guitar Solo!")
                        self.newScalingText(i, self.tsGuitarSolo )
                        #self.sfxChannel.setVolume(self.sfxVolume)
                        self.engine.data.crowdSound.play()
                  else:
                    if self.guitars[i].canGuitarSolo:
                      if self.guitars[i].guitarSolo:
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
                          soloDesc = self.tsPerfectSolo
                          soloScoreMult = 100
                          self.engine.data.crowdSound.play()    #liquid
                        elif self.guitarSoloAccuracy[i] >= 95.0:
                          soloDesc = self.tsAwesomeSolo
                          soloScoreMult = 50
                          self.engine.data.crowdSound.play()    #liquid
                        elif self.guitarSoloAccuracy[i] >= 90.0:
                          soloDesc = self.tsGreatSolo
                          soloScoreMult = 30
                          self.engine.data.crowdSound.play()    #liquid
                        elif self.guitarSoloAccuracy[i] >= 80.0:
                          soloDesc = self.tsGoodSolo
                          soloScoreMult = 20
                        elif self.guitarSoloAccuracy[i] >= 70.0:
                          soloDesc = self.tsSolidSolo
                          soloScoreMult = 10
                        elif self.guitarSoloAccuracy[i] >= 60.0:
                          soloDesc = self.tsOkaySolo
                          soloScoreMult = 5
                        else:   #0% - 59.9%
                          soloDesc = self.tsMessySolo
                          soloScoreMult = 0
                          self.engine.data.failSound.play()    #liquid
                        soloBonusScore = soloScoreMult * self.guitars[i].currentGuitarSoloHitNotes
                        player.score += soloBonusScore
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
    
    
              #MFH - render guitar solo in progress - stats
              #try:
              if self.guitars[i].canGuitarSolo:
                if self.guitars[i].guitarSolo:
                  #self.engine.view.setViewportHalf(self.numOfPlayers,i)
                  if self.guitarSoloAccuracyDisplayPos == 0:    #right
                    xOffset = 0.950
                  else:
                    xOffset = 0.150
                  yOffset = 0.320   #last change -.040
                  txtSize = 0.00250
                  #if we hit more notes in the solo than were counted, update the solo count (for the slop)
                  if self.guitars[i].currentGuitarSoloHitNotes > self.currentGuitarSoloTotalNotes[i]:
                    self.currentGuitarSoloTotalNotes[i] = self.guitars[i].currentGuitarSoloHitNotes
                  if not self.pause and not self.failed:
                    tempSoloAccuracy = (float(self.guitars[i].currentGuitarSoloHitNotes)/float(self.currentGuitarSoloTotalNotes[i]) * 100.0)
                    trimmedIntSoloNoteAcc = self.decimal(str(tempSoloAccuracy)).quantize(self.decPlaceOffset)
                    if self.guitarSoloAccuracyDisplayMode == 1:   #percentage only
                      #soloText = str(trimmedIntSoloNoteAcc) + "%"
                      soloText = "%s%%" % str(trimmedIntSoloNoteAcc)
                      if self.guitarSoloAccuracyDisplayPos == 0:    #right
                        xOffset = 0.890
                    elif self.guitarSoloAccuracyDisplayMode == 2:   #detailed
                      #soloText = str(self.guitars[i].currentGuitarSoloHitNotes) + "/" + str(self.currentGuitarSoloTotalNotes[i]) + ": " + str(trimmedIntSoloNoteAcc) + "%"
                      soloText = "%(hitSoloNotes)d/ %(totalSoloNotes)d: %(soloAcc)s%%" % \
                        {'hitSoloNotes': self.guitars[i].currentGuitarSoloHitNotes, 'totalSoloNotes': self.currentGuitarSoloTotalNotes[i], 'soloAcc': str(trimmedIntSoloNoteAcc)}
                    if self.guitarSoloAccuracyDisplayMode > 0:    #if not off:
                      soloText = soloText.replace("0","O")
                      glColor3f(1.0, 1.0, 1.0)  #cracker white
    
                      if self.theme == 2:
                        soloFont = scoreFont
                      else:
                        soloFont = font
    
                      Tw, Th = soloFont.getStringSize(soloText,txtSize)
                      
                      boxXOffset = xOffset
                      
                      if self.guitarSoloAccuracyDisplayPos == 0:  #right
                        xOffset -= Tw
                        boxXOffset -= Tw/2
                        #soloFont.render(soloText, (xOffset - Tw, yOffset),(1, 0, 0),txtSize)   #right-justified
                      elif self.guitarSoloAccuracyDisplayPos == 1:  #centered
                        xOffset = 0.5 - Tw/2
                        boxXOffset = 0.5
                        #soloFont.render(soloText, (0.5 - Tw/2, yOffset),(1, 0, 0),txtSize)   #centered
                      elif self.guitarSoloAccuracyDisplayPos == 3:  #racer: rock band 
                        if self.hitAccuracyPos == 0: #Center - need to move solo text above this!
                          yOffset = 0.100    #above Jurgen Is Here
                        elif i == 0 and self.jurg1 and self.autoPlay:
                          yOffset = 0.140    #above Jurgen Is Here
                        elif i == 1 and self.jurg2 and self.autoPlay:
                          yOffset = 0.140    #above Jurgen Is Here
                        else:   #no jurgens here:
                          yOffset = 0.210 #kk69: lower
                        xOffset = 0.5 - Tw/2
                        boxXOffset = 0.5
                        #soloFont.render(soloText, (0.5 - Tw/2, yOffset),(1, 0, 0),txtSize)   #rock band
                      else:   #left
                        boxXOffset += Tw/2
                        #soloFont.render(soloText, (xOffset, yOffset),(1, 0, 0),txtSize)   #left-justified

                      #MFH - scale and display self.soloFrame behind / around the solo accuracy text display
                      if self.soloFrame:
                        frameWidth = Tw*1.15
                        frameHeight = Th*1.05
                        #MFH - font Y position = top of text to be written
                        boxYOffset = self.hPlayer[i]-(self.wFull* (yOffset+(frameHeight/1.97)) )
                        self.soloFrame.transform.reset()
                        tempWScale = frameWidth*self.soloFrameWFactor
                        tempHScale = -(frameHeight)*self.soloFrameWFactor
                        self.soloFrame.transform.scale(tempWScale,tempHScale)
                        self.soloFrame.transform.translate(self.wPlayer[i]*boxXOffset,boxYOffset)
                        self.soloFrame.draw()

                      soloFont.render(soloText, (xOffset, yOffset),(1, 0, 0),txtSize)
                      
                  #self.engine.view.setViewport(1,0)
              #except Exception, e:
              #  Log.warn("Unable to render guitar solo accuracy text: %s" % e)
  
  
  
        #MFH - Get Ready to Rock & countdown, song info during countdown, and song time left display on top of everything else
        self.engine.view.setViewport(1,0)


        if (not self.pause and not self.failed and not self.ending):
          # show countdown
          # glorandwarf: fixed the countdown timer
          if self.countdownSeconds > 1:
            Theme.setBaseColor(min(1.0, 3.0 - abs(4.0 - self.countdownSeconds)))
            text = self.tsGetReady
            w, h = font.getStringSize(text)
            font.render(text,  (.5 - w / 2, .3))
            if self.countdownSeconds < 6:
              scale = 0.002 + 0.0005 * (self.countdownSeconds % 1) ** 3
              text = "%d" % (self.countdownSeconds)
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
              Dialogs.wrapText(songFont, (.05, .0895 - h / 2), "%s \n %s%s%s%s%s" % (Dialogs.removeSongOrderPrefixFromName(self.song.info.name), cover, self.song.info.artist, comma, self.song.info.year, extra), rightMargin = .6, scale = self.songInfoDisplayScale)#kk69: incorporates song.ttf
            else:
              Dialogs.wrapText(songFont, (.05, .05 - h / 2), "%s \n %s%s%s%s%s" % (Dialogs.removeSongOrderPrefixFromName(self.song.info.name), cover, self.song.info.artist, comma, self.song.info.year, extra), rightMargin = .6, scale = self.songInfoDisplayScale)
          else:
            #mfh: this is where the song countdown display is generated:
            if pos < 0:
              pos = 0
            if countdownPos < 0:
              countdownPos = 0
            Theme.setBaseColor()
    
  
            
            
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
        #self.engine.view.setViewport(1,0)
        self.engine.view.resetProjection()


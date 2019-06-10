#####################################################################
# -*- coding: utf-8 -*-                                             #
#                                                                   #
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2006 Sami Kyöstilä                                  #
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
#               2009-2019 FoFiX Team                                #
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

from __future__ import with_statement

from math import degrees, atan
import logging
import os
import random

import OpenGL.GL as gl

from fofix.core import Player
from fofix.core import Settings
from fofix.core.Image import drawImage
from fofix.core.Language import _
from fofix.core.Player import STAR, KILL, CANCEL, KEY1A
from fofix.core.Scene import Scene
from fofix.core.Shader import shaders
from fofix.core.constants import *
from fofix.game import Dialogs
from fofix.game import song
from fofix.game.Menu import Menu
from fofix.game.Scorekeeper import ScoreCard
from fofix.game.guitarscene import Stage
from fofix.game.guitarscene.instruments import *
from fofix.game.song import Note, TextEvent, PictureEvent, loadSong, Bars, VocalPhrase


log = logging.getLogger(__name__)


# The plan with this is to move gamemodes to being subclasses of this
class BandPlayBaseScene(Scene):
    def __init__(self, engine, libraryName, songName):
        superClass = super(BandPlayBaseScene, self)
        superClass.__init__(engine)

        log.debug("BandPlayBaseScene init...")

        self.engine.world.sceneName = "GuitarScene"
        self.ready = False

        self.countdownSeconds = 3  # don't change this initialization value unless you alter the other related variables to match
        self.countdown = 100  # arbitrary value to prevent song from starting right away
        self.countdownOK = False

        # new loading place for "loading" screen for song preparation:
        # new loading phrases
        self.sinfo = song.loadSongInfo(self.engine, songName, library=libraryName)
        self.phrase = self.sinfo.loadingPhrase
        if self.phrase == "":
            self.phrase = random.choice(self.engine.theme.loadingPhrase)
        self.splash = Dialogs.showSongLoadingSplashScreen(self.engine, songName, libraryName, self.phrase + " \n " + _("Initializing..."))
        Dialogs.changeLoadingSplashScreenText(self.engine, self.splash, self.phrase + " \n " + _("Initializing..."))

        self.lostFocusPause = self.engine.config.get("game", "lost_focus_pause")

        self.instruments = []  # this combines Guitars, Drums, and Vocalists
        self.keysList = []
        self.soloKeysList = []
        self.soloShifts   = []
        self.playingVocals = False
        self.numberOfGuitars = len(self.players)
        self.numOfPlayers    = len(self.players)
        self.numOfSingers    = 0
        self.firstGuitar     = None
        self.neckrender = []

        self.visibility       = 1.0
        self.libraryName      = libraryName
        self.songName         = songName
        self.done             = False
        self.pause            = False

        self.lastMultTime     = [None for i in self.players]
        self.cheatCodes       = [
            ([102, 97, 115, 116, 102, 111, 114, 119, 97, 114, 100], self.goToResults)
        ]
        self.enteredCode      = []
        self.song             = None

        self.lastPickPos      = [None for i in self.players]
        self.keyBurstTimeout  = [None for i in self.players]
        self.keyBurstPeriod   = 30

        self.camera.target    = (0.0, 1.0, 8.0)
        self.camera.origin    = (0.0, 2.0, -3.4)

        self.targetX          = self.engine.theme.povTarget[0]
        self.targetY          = self.engine.theme.povTarget[1]
        self.targetZ          = self.engine.theme.povTarget[2]
        self.originX          = self.engine.theme.povOrigin[0]
        self.originY          = self.engine.theme.povOrigin[1]
        self.originZ          = self.engine.theme.povOrigin[2]
        self.customPOV        = False
        self.ending           = False

        self.countdownPosX = self.engine.theme.countdownPosX
        self.countdownPosY = self.engine.theme.countdownPosY

        self.fpsRenderPos = self.engine.theme.fpsRenderPos

        self.povTheme = self.engine.theme.povPreset

        self.neckintroAnimationType = self.engine.config.get("fretboard", "neck_intro_animation")
        self.neckintroThemeType = self.engine.theme.povIntroAnimation

        if None not in [self.targetX, self.targetY, self.targetZ, self.originX, self.originY, self.originZ]:
            self.customPOV = True
            log.debug("All theme POV set. Using custom camera POV.")

        # sets the distances the neck has to move in the animation
        if self.neckintroAnimationType == 0:  # Original
            self.boardY = 2
        elif self.neckintroAnimationType == 1:  # Guitar Hero
            self.boardY = 10
        elif self.neckintroAnimationType == 2:  # Rock Band
            self.boardZ = 5
        elif self.neckintroAnimationType == 4:  # By Theme
            if self.neckintroThemeType == "fofix":  # Original
                self.boardY = 2
            elif self.neckintroThemeType == "guitar hero":  # Guitar Hero
                self.boardY = 10
            elif self.neckintroThemeType == "rockband":  # Rock Band
                self.boardZ = 5

        self.counting = self.engine.config.get("video", "counting")

        self.phrases = self.engine.config.get("coffee", "game_phrases")

        # Song related init
        #TODO - single, global BPM here instead of in instrument objects:
        #self.tempoBpm = song.DEFAULT_BPM
        #self.actualBpm = 0.0
        #self.targetPeriod   = 60000.0 / self.targetBpm
        self.audioDelay = self.engine.config.get("audio", "delay")
        self.songTime = -self.audioDelay
        self.disableVBPM  = self.engine.config.get("game", "disable_vbpm")
        self.currentBpm     = song.DEFAULT_BPM
        self.currentPeriod  = 60000.0 / self.currentBpm
        self.targetBpm      = self.currentBpm
        self.lastBpmChange  = -1.0
        self.baseBeat       = 0.0

    def loadmages(self, w, h):
        # lyric sheet!
        if not self.playingVocals:
            if self.song.hasMidiLyrics and self.midiLyricsEnabled > 0:
                lyricsheet_path = os.path.join("themes", self.themeName, "lyricsheet.png")
                lyricsheet2_path = os.path.join("themes", self.themeName, "lyricsheet2.png")

                if self.midiLyricMode == 0:
                    if not self.engine.loadImgDrawing(self, "lyricSheet", lyricsheet_path):
                        self.lyricSheet = None
                else:
                    if not self.engine.loadImgDrawing(self, "lyricSheet", lyricsheet2_path):
                        if not self.engine.loadImgDrawing(self, "lyricSheet", lyricsheet_path):
                            self.lyricSheet = None
            else:
                self.lyricSheet = None
        else:
            self.lyricSheet = None

        # brescorebackground.png
        self.breScoreBackground = None
        brescorebackground_path = os.path.join("themes", self.themeName, "brescorebackground.png")
        if self.engine.loadImgDrawing(self, "breScoreBackground", brescorebackground_path):
            self.breScoreBackgroundWFactor = (w * self.engine.theme.breScoreBackgroundScale) / self.breScoreBackground.width1()
        else:
            log.debug("BRE score background image loading problem!")
            self.breScoreBackground = None
            self.breScoreBackgroundWFactor = None

        # brescoreframe.png
        self.breScoreFrame = None
        brescoreframe_path = os.path.join("themes", self.themeName, "brescoreframe.png")
        soloframe_path = os.path.join("themes", self.themeName, "soloframe.png")
        if self.engine.loadImgDrawing(self, "breScoreFrame", brescoreframe_path):
            self.breScoreFrameWFactor = (w * self.engine.theme.breScoreFrameScale) / self.breScoreFrame.width1()
        else:
            # fallback on using soloframe.png if no brescoreframe.png is found
            if self.engine.loadImgDrawing(self, "breScoreFrame", soloframe_path):
                self.breScoreFrameWFactor = (w * self.engine.theme.breScoreFrameScale) / self.breScoreFrame.width1()
            else:
                self.breScoreFrame = None
                self.breScoreFrameWFactor = None

        if self.soloFrameMode != 0 and self.engine.loadImgDrawing(self, "soloFrame", soloframe_path):
            self.soloFrameWFactor = (w * self.engine.theme.soloFrameScale) / self.soloFrame.width1()
        else:
            self.soloFrame = None
            self.soloFrameWFactor = None

        self.partImage = True
        self.part = [None for i in self.players]
        self.partLoad = None
        if self.counting or self.coOpType:
            for i in range(self.numOfPlayers):
                if not self.partImage:
                    break
                if self.instruments[i].isDrum:
                    drum_path = os.path.join("themes", self.themeName, "drum.png")
                    if not self.engine.loadImgDrawing(self, "partLoad", drum_path):
                        if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("drum.png")):
                            self.counting = False
                            self.partImage = False
                elif self.instruments[i].isBassGuitar:
                    bass_path = os.path.join("themes", self.themeName, "bass.png")
                    if not self.engine.loadImgDrawing(self, "partLoad", bass_path):
                        if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("bass.png")):
                            self.counting = False
                            self.partImage = False
                elif self.instruments[i].isVocal:
                    mic_path = os.path.join("themes", self.themeName, "mic.png")
                    if not self.engine.loadImgDrawing(self, "partLoad", mic_path):
                        if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("mic.png")):
                            self.counting = False
                            self.partImage = False
                else:
                    guitar_path = os.path.join("themes", self.themeName, "guitar.png")
                    if not self.engine.loadImgDrawing(self, "partLoad", guitar_path):
                        if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("guitar.png")):
                            self.counting = False
                            self.partImage = False
                if self.partLoad:
                    self.part[i] = self.partLoad

        self.partLoad = None

        # Pause Screen
        self.engine.loadImgDrawing(self, "pauseScreen", os.path.join("themes", self.themeName, "pause.png"))
        if not self.engine.loadImgDrawing(self, "failScreen", os.path.join("themes", self.themeName, "fail.png")):
            self.engine.loadImgDrawing(self, "failScreen", os.path.join("themes", self.themeName, "pause.png"))

        # failMessage
        self.engine.loadImgDrawing(self, "failMsg", os.path.join("themes", self.themeName, "youfailed.png"))
        # youRockMessage
        self.engine.loadImgDrawing(self, "rockMsg", os.path.join("themes", self.themeName, "yourock.png"))

    def loadSettings(self):
        self.stage.updateDelays()

        self.activeVolume     = self.engine.config.get("audio", "guitarvol")
        self.screwUpVolume    = self.engine.config.get("audio", "screwupvol")
        self.killVolume       = self.engine.config.get("audio", "kill_volume")
        self.crowdVolume      = self.engine.config.get("audio", "crowd_volume")
        self.crowdsEnabled    = self.engine.config.get("audio", "enable_crowd_tracks")
        self.engine.data.crowdVolume = self.crowdVolume

        # now update volume of all screwup sounds and other SFX
        self.engine.data.SetAllScrewUpSoundFxObjectVolumes(self.screwUpVolume)

        # Re-apply Jurgen Settings
        self.autoPlay = False
        self.jurg     = [False for i in self.players]
        self.aiSkill  = [0 for i in self.players]

        for i, player in enumerate(self.players):
            jurgen = self.engine.config.get("game", "jurg_p%d" % i)
            if jurgen:
                self.jurg[i] = True
                self.autoPlay = True
            self.aiSkill[i] = self.engine.config.get("game", "jurg_skill_p%d" % i)
            if player.part.id == song.VOCAL_PART:
                self.instruments[i].jurgenEnabled = jurgen
                self.instruments[i].jurgenSkill   = self.aiSkill[i]

        # no Jurgen in Career mode
        if self.careerMode:
            self.autoPlay = False

        self.allTaps          = 0
        self.autoKickBass     = [0 for i in self.players]
        self.hopoAfterChord = self.engine.config.get("game", "hopo_after_chord")

        self.pov = self.engine.config.get("fretboard", "point_of_view")

        # CoffeeMod
        self.activeGameControls = self.engine.input.activeGameControls

        for i, player in enumerate(self.players):
            if player.part.id == song.VOCAL_PART:
                continue
            self.instruments[i].leftyMode   = False
            self.instruments[i].twoChordMax = False
            self.instruments[i].drumFlip    = False
            if player.lefty > 0:
                self.instruments[i].leftyMode = True
            if player.drumflip > 0:
                self.instruments[i].drumFlip = True
            if player.twoChordMax > 0:
                self.instruments[i].twoChordMax = True

        self.keysList = []
        for i, player in enumerate(self.players):
            if self.instruments[i].isDrum:
                self.keysList.append(player.drums)
            elif self.instruments[i].isVocal:
                self.keysList.append([])
                continue
            else:
                self.keysList.append(player.keys)
            if not self.instruments[i].twoChordMax:
                if self.controls.twoChord[self.activeGameControls[i]] > 0:
                    self.instruments[i].twoChordMax = True

        if self.song and self.song.readyToGo:
            self.getHandicap()  # to be sure scoring objects are created
            # ensure that after a pause or restart, the a/v sync delay is refreshed
            self.song.refreshAudioDelay()
            # ensuring the miss volume gets refreshed
            self.song.refreshVolumes()
            self.song.setAllTrackVolumes(1)
            if self.crowdsCheering:
                self.song.setCrowdVolume(1)
            else:
                self.song.setCrowdVolume(0.0)

    def quit(self):
        if self.song:
            self.song.stop()
        self.resetVariablesToDefaults()
        self.done = True

        self.engine.view.setViewport(1, 0)
        self.engine.view.popLayer(self.menu)
        self.engine.view.popLayer(self.failMenu)
        self.freeResources()
        self.engine.world.finishGame()

    def restartSong(self, firstTime=False):
        self.resetVariablesToDefaults()
        self.engine.data.startSound.play()
        self.engine.view.popLayer(self.menu)

        if not self.song:
            return

        # the countdown is now the number of beats to run before the song begins
        for instrument in self.instruments:
            if instrument.isVocal:
                instrument.stopMic()
            else:
                instrument.endPick(0)  # position of the song
        self.song.stop()

        self.initBeatAndSpClaps()

        if self.stage.mode == 3:
            self.stage.restartVideo()

    def restartAfterFail(self):
        self.resetVariablesToDefaults()
        self.engine.data.startSound.play()
        self.engine.view.popLayer(self.failMenu)

        if not self.song:
            return

        for i, instrument in enumerate(self.instruments):
            if instrument.isVocal:
                instrument.stopMic()
            else:
                instrument.endPick(0)  # position of the song
        self.song.stop()

        if self.stage.mode == 3:
            self.stage.restartVideo()

    def pauseGame(self):
        if self.song and self.song.readyToGo:
            self.pausePos = self.songTime
            self.song.pause()
            self.pause = True
            for instrument in self.instruments:
                instrument.paused = True
                if instrument.isVocal:
                    instrument.stopMic()
                else:
                    instrument.neck.paused = True

    def failGame(self):
        self.engine.view.pushLayer(self.failMenu)
        # don't let the pause menu overlap the fail menu
        if self.song and self.song.readyToGo and self.pause:
            self.engine.view.popLayer(self.menu)
            self.pause = False
            for instrument in self.instruments:
                instrument.paused = False
                if instrument.isVocal:
                    instrument.stopMic()
                else:
                    instrument.neck.paused = False
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
                if not self.failed:  # don't resume the song if you have already failed
                    self.song.unpause()
                self.pause = False
                for instrument in self.instruments:
                    instrument.paused = False
                    if instrument.isVocal:
                        instrument.startMic()
                    else:
                        instrument.neck.paused = False

    def songLoaded(self, song):
        for i, player in enumerate(self.players):
            if self.instruments[i].isVocal:
                song.difficulty[i] = song.difficulties[song.EXP_DIF]  # for track-finding purposes
                continue
            song.difficulty[i] = player.difficulty
        self.song.readyToGo = False

    def endSong(self):
        self.engine.view.popLayer(self.menu)
        validScoreFound = False
        for scoreCard in self.scoring:  # what if 2p (human) battles 1p (Jurgen / CPU)? He needs a valid score too!
            if scoreCard.score > 0:
                validScoreFound = True
                break
        if self.coOpType:
            if self.coOpScoreCard.score > 0:
                validScoreFound = True
        if validScoreFound:
            self.goToResults()
        else:
            self.changeSong()

    def changeSong(self):
        prevMode = self.engine.world.gameMode
        if self.song:
            self.song.stop()
            self.song = None
        self.resetVariablesToDefaults()
        self.engine.view.setViewport(1, 0)
        self.engine.view.popLayer(self.menu)
        self.engine.view.popLayer(self.failMenu)
        self.freeResources()
        self.engine.world.gameMode = prevMode
        self.engine.world.createScene("SongChoosingScene")

    def changeAfterFail(self):
        if self.song:
            self.song.stop()
            self.song = None
        self.resetVariablesToDefaults()

        self.engine.view.setViewport(1, 0)
        self.engine.view.popLayer(self.failMenu)
        self.freeResources()
        self.engine.world.createScene("SongChoosingScene")

    def resumeSong(self):
        self.engine.view.popLayer(self.menu)
        self.resumeGame()

    def lostFocus(self):  # catch to pause on lostFocus
        if self.song and self.song.readyToGo:
            if not self.failed and not self.pause and self.lostFocusPause:
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

        if self.customPOV:
            self.camera.target = (self.targetX, self.targetY, self.targetZ)
            self.camera.origin = (self.originX, self.originY, self.originZ)
        else:
            if self.pov == 1:  # GH3
                self.camera.target = (0.0, 0.6, 4.4)
                self.camera.origin = (0.0, 3.5, -3.8)
            elif self.pov == 2:  # RB
                self.camera.target = (0.0, 0.0, 3.7)
                self.camera.origin = (0.0, 2.9, -2.9)
            elif self.pov == 3:  # GH2
                self.camera.target = (0.0, 1.6, 2.0)
                self.camera.origin = (0.0, 2.6, -3.6)
            elif self.pov == 4:  # Rock Rev
                self.camera.target = (0.0, -6.0, 2.6666666666)
                self.camera.origin = (0.0, 6.0, 2.6666666665)
            elif self.pov == 5:  # Theme
                if self.povTheme == "gh2":
                    self.camera.target = (0.0, 1.6, 2.0)
                    self.camera.origin = (0.0, 2.6, -3.6)
                elif self.povTheme == "gh3":
                    self.camera.target = (0.0, 0.6, 4.4)
                    self.camera.origin = (0.0, 3.5, -3.8)
                elif self.povTheme == "rb":
                    self.camera.target = (0.0, 0.0, 3.7)
                    self.camera.origin = (0.0, 2.9, -2.9)
                elif self.povTheme == "fof":
                    self.camera.target = (0.0, 0.0, 4.0)
                    self.camera.origin = (0.0, 3.0, -3.0)
            else:  # FoF
                self.camera.target = (0.0, 0.0, 4.0)
                self.camera.origin = (0.0, 3.0, -3.0)

        # different types of fretbord into animations
        if self.neckintroAnimationType == 0:  # Original FoFiX rotate down into place
            self.camera.origin = (self.camera.origin[0], self.camera.origin[1]*self.boardY, self.camera.origin[2])
        elif self.neckintroAnimationType == 1:  # Guitar Hero type (from bottom of screen)
            self.camera.target    = (self.camera.target[0], self.camera.target[1]+self.boardY-1, self.camera.target[2])
            self.camera.origin    = (self.camera.origin[0], self.camera.origin[1]+self.boardY-1, self.camera.origin[2])
        elif self.neckintroAnimationType == 2:  # Rock Band type (goes into screen)
            self.camera.target    = (self.camera.target[0], self.camera.target[1], self.camera.target[2]+self.boardZ-1)
            self.camera.origin    = (self.camera.origin[0], self.camera.origin[1], self.camera.origin[2]+self.boardZ-1)
        elif self.neckintroAnimationType == 3:  # Off game starts with the pov as is
            self.camera.origin    = self.camera.origin
        elif self.neckintroAnimationType == 4:  # By Theme
            if self.neckintroThemeType == "fofix":
                self.camera.origin = (self.camera.origin[0], self.camera.origin[1]*self.boardY, self.camera.origin[2])
            elif self.neckintroThemeType == "guitar hero":
                self.camera.target    = (self.camera.target[0], self.camera.target[1]+self.boardY-1, self.camera.target[2])
                self.camera.origin    = (self.camera.origin[0], self.camera.origin[1]+self.boardY-1, self.camera.origin[2])
            elif self.neckintroThemeType == "rockband":
                self.camera.target    = (self.camera.target[0], self.camera.target[1], self.camera.target[2]+self.boardZ-1)
                self.camera.origin    = (self.camera.origin[0], self.camera.origin[1], self.camera.origin[2]+self.boardZ-1)

    def handleTempo(self, song, pos):
        if not song:
            return
        if self.lastBpmChange > 0 and self.disableVBPM:  # only handle tempo once if the VBPM feature is off
            return
        tempEventHolder = song.tempoEventTrack.getNextTempoChange(pos)
        if tempEventHolder:
            time, event = tempEventHolder
            if ( (time < pos or self.lastBpmChange < 0) or (pos - time < self.currentPeriod or self.lastBpmChange < 0) ) and time > self.lastBpmChange:
                self.baseBeat += (time - self.lastBpmChange) / self.currentPeriod
                self.targetBpm = event.bpm
                song.tempoEventTrack.currentIndex += 1  # manually increase current event
                self.lastBpmChange = time

        # adjust tempo gradually to meet new target
        if self.targetBpm != self.currentBpm:
            diff = self.targetBpm - self.currentBpm
            tempDiff = round((diff * .03), 4)  # better to calculate this once and reuse the variable instead of recalculating every use
            if tempDiff != 0:
                self.currentBpm = self.currentBpm + tempDiff
            else:
                self.currentBpm = self.targetBpm

            # recalculate all variables dependent on the tempo, apply to instrument objects - only if currentBpm has changed
            self.currentPeriod = 60000.0 / self.currentBpm
            for instrument in self.instruments:
                instrument.setBPM(self.currentBpm)
                instrument.lastBpmChange = self.lastBpmChange
                instrument.baseBeat = self.baseBeat

    def hopFretboard(self, num, height):
        """ Hop a fretboard """
        if self.instruments[num].fretboardHop < height:
            self.instruments[num].fretboardHop = height

    def getPlayerNum(self, control):
        for i, player in enumerate(self.players):
            if control and control in player.keyList:
                return i
        else:
            return -1

    def render(self, visibility, topMost):
        super(BandPlayBaseScene, self).render(visibility, topMost)

    def run(self, ticks):
        super(BandPlayBaseScene, self).run(ticks)


class GuitarScene(BandPlayBaseScene):
    def __init__(self, engine, libraryName, songName):
        superClass = super(GuitarScene, self)
        superClass.__init__(engine, libraryName, songName)

        self.battle = False
        self.coOp = False
        self.coOpRB = False
        self.coOpType = False
        self.practiceMode = False

        log.debug("GuitarScene init...")

        self.coOpPlayerMeter = 0

        # retrieve game parameters
        self.gamePlayers = len(self.players)
        self.gameMode1p = self.engine.world.gameMode
        self.gameMode2p = self.engine.world.multiMode

        if self.gameMode1p == 2:
            self.careerMode = True
        else:
            self.careerMode = False

        if self.gameMode1p == 1:
            self.practiceMode = True

        if self.gamePlayers > 1:
            # check for battle mode
            if self.gameMode2p == 1:
                self.battle   = True
                self.coOp     = False
                self.coOpRB   = False
                self.coOpType = False
            # Mode 2 was party mode
            elif self.gameMode2p == 3:
                self.battle   = False
                self.coOp     = True
                self.coOpRB   = False
                self.coOpType = True
            elif self.gameMode2p == 4:
                self.battle   = False
                self.coOp     = False
                self.coOpRB   = True
                self.coOpType = True
            # mode 5 was coop gh
            # mode 6 was GH3 battle
                self.coOpType = False
            else:
                self.battle   = False
                self.coOp     = False
                self.coOpRB   = False
                self.coOpType = False

        gNum = 0
        for j, player in enumerate(self.players):
            guitar = True
            if player.part.id == song.VOCAL_PART:
                inst = Vocalist(self.engine, player, self, player=j)
                if self.coOpRB:
                    inst.coOpRB = True
                self.instruments.append(inst)
                self.playingVocals = True
                self.numOfSingers += 1
                self.numberOfGuitars -= 1
                guitar = False
            elif player.part.id == song.DRUM_PART:
                inst = Drum(self.engine, player, self, player=j)
                self.instruments.append(inst)
            else:
                bass = False
                if player.part.id == song.BASS_PART:
                    bass = True
                inst = Guitar(self.engine, player, self, player=j, bass=bass)
                self.instruments.append(inst)
                # both these selections should get guitar solos
                if player.part.id == song.LEAD_PART or player.part.id == song.GUITAR_PART:
                    self.instruments[j].canGuitarSolo = True

            if player.practiceMode:
                self.practiceMode = True
            if guitar:
                player.guitarNum = gNum
                gNum += 1
                if self.firstGuitar is None:
                    self.firstGuitar = j
                self.neckrender.append(self.instruments[j].neck)
                if self.instruments[j].isDrum:
                    self.keysList.append(player.drums)
                    self.soloKeysList.append(player.drumSolo)
                    self.soloShifts.append(None)
                    self.instruments[j].keys    = player.drums
                    self.instruments[j].actions = player.drums
                else:
                    self.keysList.append(player.keys)
                    self.soloKeysList.append(player.soloKeys)
                    self.soloShifts.append(player.soloShift)
                    self.instruments[j].keys    = player.keys
                    self.instruments[j].actions = player.actions
            else:
                self.neckrender.append(None)
                self.keysList.append([])
                self.soloKeysList.append([])
                self.soloShifts.append([])

        log.debug("GuitarScene keysList: %s" % str(self.keysList))

        self.aiSkill                 = [0 for i in self.players]
        self.aiHitPercentage         = [0 for i in self.players]
        self.aiPlayNote              = [True for i in self.players]
        self.aiUseSP                 = [0 for i in self.players]
        self.battleTarget            = [0 for i in self.players]

        self.jurgenText = self.engine.theme.jurgTextPos
        if float(self.jurgenText[2]) < 0.00035:
            self.jurgenText[2] = 0.00035
        if float(self.jurgenText[0]) < 0:
            self.jurgenText[0] = 0
        if float(self.jurgenText[1]) < 0:
            self.jurgenText[1] = 0

        self.whammySavesSP = self.engine.config.get("game", "whammy_saves_starpower")
        self.failingEnabled = self.engine.config.get("coffee", "failingEnabled")

        self.timeLeft = None
        self.processedFirstNoteYet = False

        self.playerAssist = [0 for i in self.players]
        for i, player in enumerate(self.players):
            if self.instruments[i].isDrum:
                if player.autoKick:
                    self.playerAssist[i] = 3
            elif not self.instruments[i].isVocal:
                self.playerAssist[i] = player.assistMode
                if self.playerAssist[i] == 2 and player.getDifficultyInt() > 1:
                    self.playerAssist[i] = 0
                elif self.playerAssist[i] == 1 and player.getDifficultyInt() > 2:
                    self.playerAssist[i] = 0
        for assistMode in self.playerAssist:
            if assistMode > 0:
                self.assisting = True
                break
        else:
            self.assisting = False

        self.autoPlay         = False
        self.jurgPlayer       = [False for i in self.players]
        self.jurg             = [False for i in self.players]
        self.customBot        = [None for i in self.players]
        for i in range(self.numOfPlayers):
            if self.instruments[i].isVocal:
                continue
            if self.engine.config.get("game", "jurg_p%d" % i):
                self.jurg[i] = True
                self.autoPlay = True

        self.failed = False
        self.finalFailed = False
        self.failEnd = False
        self.crowdsCheering = False
        self.inUnison = [False for i in self.players]
        self.haveUnison = [False for i in self.players]
        self.firstUnison = False
        self.firstUnisonDone = False
        self.unisonActive = False
        self.unisonNum = 0
        self.unisonEarn = [False for i in self.players]
        self.starPowersActive = 0
        self.playersInGreen = 0
        self.crowdFaderVolume = 0.0
        self.coOpStarPower = 0
        self.coOpStarPowerTimer = 0
        self.coOpStarPowerActive = [0 for i in self.players]
        self.failTimer = 0
        self.rockTimer = 0
        self.youRock = False
        self.rockCountdown = 100
        self.soloReviewDispDelay = 300
        self.baseScore = 50
        self.baseSustainScore = .1
        self.rockFinished = False
        self.spTimes = [[] for i in self.players]
        self.midiSP = False
        self.oBarScale = 0.0  # overdrive bar scale factor
        self.firstClap = True

        self.multi = [1 for i in self.players]

        # Get theme
        self.themeName = self.engine.data.themeLabel
        self.theme = self.engine.data.theme

        if self.engine.theme.hopoIndicatorX is not None:
            self.hopoIndicatorX = self.engine.theme.hopoIndicatorX
        else:
            self.hopoIndicatorX = .950

        if self.engine.theme.hopoIndicatorY is not None:
            self.hopoIndicatorY = self.engine.theme.hopoIndicatorY
        else:
            self.hopoIndicatorY = .710

        self.hopoIndicatorActiveColor = self.engine.theme.hopoIndicatorActiveColor
        self.hopoIndicatorInactiveColor = self.engine.theme.hopoIndicatorInactiveColor

        self.rockMax = 30000.0
        self.rockMedThreshold = self.rockMax / 3.0
        self.rockHiThreshold = self.rockMax / 3.0 * 2
        self.rock = [self.rockMax / 2 for i in self.players]
        self.arrowRotation = [.5 for i in self.players]
        self.starNotesMissed = [False for i in self.players]
        self.notesMissed = [False for i in self.players]
        self.lessMissed = [False for i in self.players]
        self.notesHit = [False for i in self.players]
        self.lessHit = False
        self.minBase = 400
        self.pluBase = 15
        self.minGain = 2
        self.pluGain = 7
        self.battleMax = 300
        self.minusRock = [self.minBase for i in self.players]
        self.plusRock = [self.pluBase for i in self.players]
        self.coOpMulti = 1
        self.coOpFailDone = [False for i in self.players]
        if self.coOpRB:
            self.coOpPlayerMeter = len(self.rock)
            self.rock.append(self.rockMax / 2)
            self.minusRock.append(0.0)
            self.plusRock.append(0.0)
            self.timesFailed = [0 for i in self.players]
        if self.coOp:
            self.coOpPlayerMeter = len(self.rock) - 1  # make sure it's the last one

        stage = os.path.join("themes", self.themeName, "stage.ini")
        self.stage = Stage.Stage(self, self.engine.resource.fileName(stage))

        self.loadSettings()
        self.tsBotNames = [_("KiD"), _("Stump"), _("AkedRobot"), _("Q"), _("MFH"), _("Jurgen")]
        # pre-translate text strings
        self.powerUpName = self.engine.theme.power_up_name
        self.tsNoteStreak       = _("%d Note Streak")
        self.tsPhraseStreak     = _("%d Phrase Streak")
        self.tsStarPowerReady   = _("%s Ready") % self.powerUpName
        self.tsCoOpStarPower    = _("Activate %s!") % self.powerUpName
        self.tsYouFailedBattle  = _("You Failed")
        self.tsJurgenIsHere     = _("%s is here")
        self.tsJurgenWasHere    = _("%s was here")
        self.tsPercentComplete  = _("% Complete")
        self.tsHopoIndicator    = _("HOPO")
        self.tsCompleted        = _("COMPLETED")
        self.tsPercentOn        = _(" % ON ")
        self.tsBassGroove       = _("BASS GROOVE")
        self.tsBassGrooveLabel  = _("Bass Groove:")
        self.tsHandicapLabel    = _("Handicap")
        self.tsAvgLabel         = _("Avg")
        self.tsAccVeryLate      = _("Very Late")
        self.tsAccLate          = _("Late")
        self.tsAccSlightlyLate  = _("Slightly Late")
        self.tsAccExcellentLate = _("-Excellent!")
        self.tsAccPerfect       = _("Perfect!!")
        self.tsAccExcellentEarly= _("+Excellent!")
        self.tsAccSlightlyEarly = _("Slightly Early")
        self.tsAccEarly         = _("Early")
        self.tsAccVeryEarly     = _("Very Early")
        self.msLabel            = _("ms")
        self.tsSolo             = _("Solo!")
        self.tsPerfectSolo      = _("Perfect Solo!")
        self.tsAwesomeSolo      = _("Awesome Solo!")
        self.tsGreatSolo        = _("Great Solo!")
        self.tsGoodSolo         = _("Good Solo!")
        self.tsSolidSolo        = _("Solid Solo!")
        self.tsOkaySolo         = _("Okay Solo")
        self.tsMessySolo        = _("Messy Solo")
        self.tsPtsLabel         = _("pts")
        self.tsGetReady         = _("Get Ready to Rock")
        self.tsAsMadeFamousBy   = _("as made famous by")
        self.tsBy               = _("by ")
        self.tsFrettedBy        = _(" fretted by ")

        for player in self.players:
            player.currentTheme = self.theme

        # precalculate full and player viewports
        self.engine.view.setViewport(1, 0)
        self.wFull, self.hFull = self.engine.view.geometry[2:4]
        self.wPlayer = []
        self.hPlayer = []
        self.hOffset = []
        self.hFontOffset = []
        # needed for new stage background handling
        self.stage.wFull = self.wFull
        self.stage.hFull = self.hFull
        self.fontScreenBottom = self.engine.data.fontScreenBottom
        self.oBarScaleCoef = (0.6 + 0.4 * self.numberOfGuitars) * 1.256 * self.hFull / self.wFull  # depends on resolution and number of players

        for i, player in enumerate(self.players):
            if not self.instruments[i].isVocal:
                self.engine.view.setViewportHalf(self.numberOfGuitars, player.guitarNum)
                w = self.engine.view.geometryAllHalf[self.numberOfGuitars-1, player.guitarNum, 2]
                h = self.engine.view.geometryAllHalf[self.numberOfGuitars-1, player.guitarNum, 3]
            else:
                w = self.wFull
                h = self.hFull
            self.wPlayer.append(w)
            self.hPlayer.append(h)
            self.hOffset.append(h)
            self.hFontOffset.append(h)
            if not self.instruments[i].isVocal:
                self.wPlayer[i] = self.wPlayer[i] * self.numberOfGuitars  # set the width
                if self.numberOfGuitars > 1:
                    self.hPlayer[i] = self.hPlayer[i] * self.numberOfGuitars / 1.5  # set the hight
                    self.hOffset[i] = self.hPlayer[i] * .4 * (self.numberOfGuitars - 1)
                else:
                    self.hPlayer[i] = self.hPlayer[i] * self.numberOfGuitars  # set the hight
                    self.hOffset[i] = 0
                self.hFontOffset[i] = -self.hOffset[i] / self.hPlayer[i] * 0.752  # font Height Offset when there are 2 players

        self.engine.view.setViewport(1, 0)

        self.drumMisses = self.engine.config.get("game", "T_sound")  # Faaa Drum sound

        # constant definitions, ini value retrievals
        self.pitchBendSemitones = -1.0  # perhaps read this from song.ini and fall back on a specific value?
        self.lineByLineLyricMaxLineWidth = 0.5
        self.lineByLineStartSlopMs = 750
        self.digitalKillswitchStarpowerChunkSize = 0.05 * self.engine.audioSpeedFactor
        self.digitalKillswitchActiveStarpowerChunkSize = self.digitalKillswitchStarpowerChunkSize / 3.0
        # was 0.10, now much closer to actual GH3
        self.analogKillswitchStarpowerChunkSize = 0.15 * self.engine.audioSpeedFactor
        self.analogKillswitchActiveStarpowerChunkSize = self.analogKillswitchStarpowerChunkSize / 3.0
        self.rbOverdriveBarGlowFadeInChunk = .07  # this amount added to visibility every run() cycle when fading in - original .2
        self.crowdCheerFadeInChunk =  .02         # added to crowdVolume every run() when fading in
        self.crowdCheerFadeOutChunk = .03         # subtracted from crowdVolume every run() on fade out.
        self.maxDisplayTextScale = 0.0024       # orig 0.0024
        self.displayTextScaleStep2 = 0.00008    # orig 0.00008
        self.displayTextScaleStep1 = 0.0001     # orig 0.0001
        self.textTimeToDisplay = 100
        self.songInfoDisplayScale = self.engine.theme.songInfoDisplayScale
        self.songInfoDisplayX = self.engine.theme.songInfoDisplayX  # This controls the X position of song info display during countdown
        self.songInfoDisplayY = self.engine.theme.songInfoDisplayY  # This controls the Y position of song info display during countdown
        self.lyricMode = self.engine.config.get("game", "lyric_mode")
        self.scriptLyricPos = self.engine.config.get("game", "script_lyric_pos")
        self.starClaps = self.engine.config.get("game", "star_claps")
        self.rb_sp_neck_glow = self.engine.config.get("game", "rb_sp_neck_glow")
        self.accuracy = [0 for i in self.players]
        self.resumeCountdownEnabled = self.engine.config.get("game", "resume_countdown")
        self.resumeCountdown = 0
        self.resumeCountdownSeconds = 0
        self.pausePos = 0
        self.dispAccuracy = [False for i in self.players]
        self.showAccuracy = self.engine.config.get("game", "accuracy_mode")
        self.hitAccuracyPos = self.engine.config.get("game", "accuracy_pos")
        self.showUnusedTextEvents = self.engine.config.get("game", "show_unused_text_events")
        self.bassKickSoundEnabled = self.engine.config.get("game", "bass_kick_sound")
        self.midiLyricsEnabled = self.engine.config.get("game", "rb_midi_lyrics")
        self.midiSectionsEnabled = self.engine.config.get("game", "rb_midi_sections")
        if self.numOfPlayers > 1 and self.midiLyricsEnabled == 1:
            self.midiLyricsEnabled = 0
        if self.numOfPlayers > 1 and self.midiSectionsEnabled == 1:
            self.midiSectionsEnabled = 0
        self.hopoDebugDisp = self.engine.config.get("game", "hopo_debug_disp")
        if self.hopoDebugDisp == 1:
            for instrument in self.instruments:
                if not instrument.isDrum and not instrument.isVocal:
                    instrument.debugMode = True
        self.numDecimalPlaces = self.engine.config.get("game", "decimal_places")
        self.roundDecimalForDisplay = lambda n: ('%%.%df' % self.numDecimalPlaces) % float(n)
        self.starScoring = self.engine.config.get("game", "star_scoring")
        self.ignoreOpenStrums = self.engine.config.get("game", "ignore_open_strums")
        self.muteSustainReleases = self.engine.config.get("game", "sustain_muting")
        self.hopoIndicatorEnabled = self.engine.config.get("game", "hopo_indicator")
        self.muteLastSecond = self.engine.config.get("audio", "mute_last_second")
        self.mutedLastSecondYet = False
        self.muteDrumFill = self.engine.config.get("game", "mute_drum_fill")
        self.starScoreUpdates = self.engine.config.get("performance", "star_score_updates")
        self.currentlyAnimating = True
        self.missPausesAnim = self.engine.config.get("game", "miss_pauses_anim")
        self.starpowerMode = self.engine.config.get("game", "starpower_mode")
        self.useMidiSoloMarkers = False
        self.soloFrameMode = self.engine.config.get("game", "solo_frame")
        self.whammyEffect = self.engine.config.get("audio", "whammy_effect")
        shaders.var["whammy"] = self.whammyEffect
        self.bigRockEndings = self.engine.config.get("game", "big_rock_endings")
        self.showFreestyleActive = self.engine.config.get("debug", "show_freestyle_active")
        self.showBpm = self.engine.config.get("debug", "show_bpm")

        self.vbpmLogicType = self.engine.config.get("debug", "use_new_vbpm_beta")

        # switch to midi lyric mode option
        self.midiLyricMode = self.engine.config.get("game", "midi_lyric_mode")
        self.currentSimpleMidiLyricLine = ""
        self.noMoreMidiLineLyrics = False

        # practice beat claps
        self.beatClaps = self.engine.config.get("game", "beat_claps")

        self.killDebugEnabled = self.engine.config.get("game", "kill_debug")

        # for checking if killswitch key is analog for whammy
        self.whammyVolAdjStep = 0.1
        self.analogKillMode = [self.engine.input.getAnalogKill(i) for i in range(self.numOfPlayers)]
        self.isKillAnalog = [False for i in self.players]
        self.isSPAnalog   = [False for i in self.players]
        self.isSlideAnalog = [False for i in self.players]
        self.whichJoyKill  = [0 for i in self.players]
        self.whichAxisKill = [0 for i in self.players]
        self.whichJoyStar  = [0 for i in self.players]
        self.whichAxisStar = [0 for i in self.players]
        self.whichJoySlide = [0 for i in self.players]
        self.whichAxisSlide = [0 for i in self.players]
        self.whammyVol = [0.0 for i in self.players]
        self.starAxisVal = [0.0 for i in self.players]
        self.starDelay   = [0.0 for i in self.players]
        self.starActive  = [False for i in self.players]
        self.slideValue  = [-1 for i in self.players]
        self.targetWhammyVol = [0.0 for i in self.players]

        self.defaultWhammyVol = [self.analogKillMode[i] - 1.0 for i in range(self.numOfPlayers)]  # makes xbox defaults 1.0, PS2 defaults 0.0
        for i in range(self.numOfPlayers):
            if self.analogKillMode[i] == 3:  # XBOX inverted mode
                self.defaultWhammyVol[i] = -1.0

        self.actualWhammyVol = [self.defaultWhammyVol[i] for i in range(self.numOfPlayers)]

        self.lastWhammyVol = [self.defaultWhammyVol[i] for i in range(self.numOfPlayers)]

        KillKeyCode = [0 for i in self.players]
        StarKeyCode = [0 for i in self.players]
        SlideKeyCode = [0 for i in self.players]

        self.lastTapText = "tapp: -"

        # auto drum starpower activation option
        self.autoDrumStarpowerActivate = self.engine.config.get("game", "drum_sp_mode")

        self.analogSlideMode = [self.engine.input.getAnalogSlide(i) for i in range(self.numOfPlayers)]

        self.analogSPMode   = [self.engine.input.getAnalogSP(i) for i in range(self.numOfPlayers)]
        self.analogSPThresh = [self.engine.input.getAnalogSPThresh(i) for i in range(self.numOfPlayers)]
        self.analogSPSense  = [self.engine.input.getAnalogSPSense(i) for i in range(self.numOfPlayers)]

        self.numDrumFills = 0  # count drum fills to see whether or not we should use auto SP

        # TODO - rewrite in an expandable fashion; requires creation of some new Player object constants that will link to the appropriate player's control based on which player the object is set to
        for i, player in enumerate(self.players):
            if self.analogKillMode[i] > 0:
                KillKeyCode[i] = self.controls.getReverseMapping(player.keyList[KILL])
                self.isKillAnalog[i], self.whichJoyKill[i], self.whichAxisKill[i] = self.engine.input.getWhammyAxis(KillKeyCode[i])
                if self.isKillAnalog[i]:
                    try:
                        self.engine.input.joysticks[self.whichJoyKill[i]].get_axis(self.whichAxisKill[i])
                    except IndexError:
                        self.isKillAnalog[i] = False
            if self.analogSPMode[i] > 0:
                StarKeyCode[i] = self.controls.getReverseMapping(player.keyList[STAR])
                self.isSPAnalog[i], self.whichJoyStar[i], self.whichAxisStar[i] = self.engine.input.getWhammyAxis(StarKeyCode[i])
                if self.isSPAnalog[i]:
                    try:
                        self.engine.input.joysticks[self.whichJoyStar[i]].get_axis(self.whichAxisStar[i])
                    except IndexError:
                        self.isSPAnalog[i] = False
            if player.controlType == 4:
                SlideKeyCode[i] = self.controls.getReverseMapping(player.keyList[KEY1A])
                self.isSlideAnalog[i], self.whichJoySlide[i], self.whichAxisSlide[i] = self.engine.input.getWhammyAxis(SlideKeyCode[i])
                if self.isSlideAnalog[i]:
                    try:
                        self.engine.input.joysticks[self.whichJoySlide[i]].get_axis(self.whichAxisSlide[i])
                    except IndexError:
                        self.isSlideAnalog[i] = False

        self.inGameStats = self.engine.config.get("performance", "in_game_stats")
        self.inGameStars = self.engine.config.get("game", "in_game_stars")

        self.guitarSoloAccuracyDisplayMode = self.engine.config.get("game", "gsolo_accuracy_disp")
        self.guitarSoloAccuracyDisplayPos = self.engine.config.get("game", "gsolo_accuracy_pos")

        # need a new flag for each player, showing whether or not they've missed a note during a solo section.
        # this way we have a backup detection of Perfect Solo in case a note got left out, picks up the other side of the solo slop
        self.guitarSoloBroken = [False for i in self.players]

        self.deadPlayerList = []
        self.numDeadPlayers = 0
        coOpInstruments = []
        self.scoring = []
        for instrument in self.instruments:
            if instrument.isDrum:
                this = song.DRUM_PART
                coOpInstruments.append(this)
            elif instrument.isBassGuitar:
                this = song.BASS_PART
                coOpInstruments.append(this)
            elif instrument.isVocal:
                this = song.VOCAL_PART
                coOpInstruments.append(this)
            else:
                this = song.GUITAR_PART
                coOpInstruments.append(this)  # while different guitars exist, they don't affect scoring
            self.scoring.append(ScoreCard([this]))
        if self.coOpType:
            self.coOpScoreCard = ScoreCard(coOpInstruments, coOpType=True)
        else:
            self.coOpScoreCard = None

        self.partialStar = [0 for i in self.players]
        self.starRatio = [0.0 for i in self.players]
        self.dispSoloReview = [False for i in self.players]
        self.soloReviewText = [[] for i in self.players]
        self.soloReviewCountdown = [0 for i in self.players]
        self.guitarSoloAccuracy = [0.0 for i in self.players]
        self.guitarSoloActive = [False for i in self.players]
        self.currentGuitarSolo = [0 for i in self.players]

        self.solo_soloFont = self.engine.data.scoreFont

        self.guitarSoloShown = [False for i in self.players]
        self.currentGuitarSoloLastHitNotes = [1 for i in self.players]
        self.solo_xOffset = [0.0 for i in self.players]
        self.solo_yOffset = [0.0 for i in self.players]
        self.solo_boxXOffset = [0.0 for i in self.players]
        self.solo_boxYOffset = [0.0 for i in self.players]
        self.solo_Tw = [0.0 for i in self.players]
        self.solo_Th = [0.0 for i in self.players]
        self.solo_soloText = ["solo" for i in self.players]
        self.soloAcc_Rect = [None for i in self.players]
        self.solo_txtSize = 0.00250
        for i, playa in enumerate(self.players):
            if self.guitarSoloAccuracyDisplayPos == 0:  # right
                if self.guitarSoloAccuracyDisplayMode == 1:  # percentage only
                    self.solo_xOffset[i] = 0.890
                else:
                    self.solo_xOffset[i] = 0.950
            else:
                self.solo_xOffset[i] = 0.150
            self.solo_yOffset[i] = 0.320  # last change -.040

        self.currentGuitarSoloTotalNotes = [0 for i in self.players]
        self.guitarSolos = [[] for i in self.players]
        guitarSoloStartTime = 0
        isGuitarSoloNow = False
        guitarSoloNoteCount = 0
        self.drumStart = False
        unisonCheck = []

        if self.careerMode:
            self.failingEnabled = True

        self.tut = self.engine.config.get("game", "tut")

        # no Jurgen in Career mode or tutorial mode or practice mode
        if self.careerMode or self.tut or self.players[0].practiceMode:
            self.autoPlay = False

        self.rockFailUp = True  # fading mech
        self.rockFailViz = 0.0
        self.failViz = [0.0 for i in self.players]

        #
        # Begin song loading
        #
        Dialogs.changeLoadingSplashScreenText(self.engine, self.splash, self.phrase + " \n " + _("Loading song..."))

        # this is where song loading originally took place, and the loading screen was spawned.

        self.engine.resource.load(
            self,
            "song",
            lambda: loadSong(self.engine, songName, library=libraryName, part=[player.part for player in self.players], practiceMode=self.players[0].practiceMode, practiceSpeed=self.players[0].practiceSpeed),
            synch=True,
            onLoad=self.songLoaded
        )

        Dialogs.changeLoadingSplashScreenText(self.engine, self.splash, self.phrase + " \n " + _("Preparing Note Phrases..."))

        if self.players[0].practiceMode or self.song.info.tutorial or self.tut:
            self.failingEnabled = False

        self.players[0].hopoFreq = self.song.info.hopofreq

        bassGrooveEnableSet = self.engine.config.get("game", "bass_groove_enable")
        if bassGrooveEnableSet == 1:
            self.bassGrooveEnabled = True
        elif bassGrooveEnableSet == 2 and self.song.midiStyle == song.MIDI_TYPE_RB:
            self.bassGrooveEnabled = True
        elif bassGrooveEnableSet == 3:
            self.bassGrooveEnabled = True
        else:
            self.bassGrooveEnabled = False

        for i, drum in enumerate(self.instruments):
            if not drum.isDrum:
                continue
            if drum.drumFlip:
                for d in range(len(song.difficulties)):
                    self.song.tracks[i][d].flipDrums()

        for scoreCard in self.scoring:
            scoreCard.bassGrooveEnabled = self.bassGrooveEnabled

        # single audio track song detection
        self.isSingleAudioTrack = self.song.isSingleAudioTrack

        # also want to go through song and search for guitar solo parts, and count notes in them in each diff.
        # now, handle MIDI starpower / overdrive / other special marker notes:
        # first, count the markers for each instrument.  If a particular instrument does not have at least two starpower phrases
        # marked, ignore them and force auto-generation of SP paths.
        for i in range(self.numOfPlayers):  # count number of drum fills
            if self.instruments[i].isDrum:  # count number of drum fill markers
                self.numDrumFills = len([1 for time, event in self.song.midiEventTrack[i].getAllEvents() if (isinstance(event, song.MarkerNote) and (event.number == song.FREESTYLE_MARKING_NOTE))])
                log.debug("Drum part found, scanning for drum fills.... %d freestyle markings found (the last one may be a Big Rock Ending)." % self.numDrumFills)

        # handle early hit window automatic type determination, and how it compares to the forced handicap if not auto
        self.effectiveEarlyHitWindow = song.EARLY_HIT_WINDOW_HALF
        self.automaticEarlyHitWindow = song.EARLY_HIT_WINDOW_HALF
        self.forceEarlyHitWindowSetting = self.engine.config.get("handicap", "early_hit_window")
        if self.song.info.early_hit_window_size:
            log.debug("song.ini setting found specifying early_hit_window_size - %s" % self.song.info.early_hit_window_size)
            if self.song.info.early_hit_window_size.lower() == "none":
                self.automaticEarlyHitWindow = song.EARLY_HIT_WINDOW_NONE
            elif self.song.info.early_hit_window_size.lower() == "half":
                self.automaticEarlyHitWindow = song.EARLY_HIT_WINDOW_HALF
            else:  # all other unrecognized cases, default to "full"
                self.automaticEarlyHitWindow = song.EARLY_HIT_WINDOW_FULL

        else:
            log.debug("No song.ini setting found specifying early_hit_window_size - using automatic detection...")

            if self.song.midiStyle == song.MIDI_TYPE_RB:
                log.debug("Basic RB1/RB2 type MIDI found - early hitwindow of NONE is set as handicap base.")
                self.automaticEarlyHitWindow = song.EARLY_HIT_WINDOW_NONE

        if self.forceEarlyHitWindowSetting > 0:  # if user is specifying a specific early hitwindow, then calculate handicap...
            self.effectiveEarlyHitWindow = self.forceEarlyHitWindowSetting
            tempHandicap = 1.00
            if self.automaticEarlyHitWindow > self.effectiveEarlyHitWindow:  # positive handicap
                tempHandicap += ((self.automaticEarlyHitWindow - self.effectiveEarlyHitWindow) * 0.05)
            elif self.automaticEarlyHitWindow < self.effectiveEarlyHitWindow:  # negative handicap
                tempHandicap -= ((self.effectiveEarlyHitWindow - self.automaticEarlyHitWindow) * 0.05)
            for scoreCard in self.scoring:
                scoreCard.earlyHitWindowSizeHandicap = tempHandicap
            if self.coOpType:
                self.coOpScoreCard.earlyHitWindowSizeHandicap = tempHandicap

        else:
            self.effectiveEarlyHitWindow = self.automaticEarlyHitWindow

        tempEarlyHitWindowSizeFactor = 0.5
        if self.effectiveEarlyHitWindow == 1:  # none
            tempEarlyHitWindowSizeFactor = 0.10  # really, none = about 10%
        elif self.effectiveEarlyHitWindow == 2:  # half
            tempEarlyHitWindowSizeFactor = 0.5
        else:                                    # any other value will be full
            tempEarlyHitWindowSizeFactor = 1.0

        for instrument in self.instruments:  # force update of early hit window
            instrument.earlyHitWindowSizeFactor = tempEarlyHitWindowSizeFactor
            instrument.actualBpm = 0.0
            instrument.currentBpm = song.DEFAULT_BPM
            instrument.setBPM(instrument.currentBpm)

        self.markSolos = self.engine.config.get("game", "mark_solo_sections")
        if self.markSolos == 2:
            if self.engine.theme.markSolos == 2:
                self.markSolos = 1
            else:
                self.markSolos = self.engine.theme.markSolos

        if self.song.hasStarpowerPaths:
            for i, guitar in enumerate(self.instruments):
                if guitar.isVocal:
                    continue

                # first, count the SP marker notes!
                numOfSpMarkerNotes = len([1 for time, event in self.song.midiEventTrack[i].getAllEvents() if (isinstance(event, song.MarkerNote) and not event.endMarker and (event.number == song.OD_MARKING_NOTE or (event.number == song.SP_MARKING_NOTE and self.song.midiStyle == song.MIDI_TYPE_GH)))])

                # also want to count RB solo sections in this track, if the MIDI type is RB.  Then we'll know to activate MIDI guitar solo markers or not
                # for this instrument
                if self.song.midiStyle == song.MIDI_TYPE_RB:
                    numMidiSoloMarkerNotes = len([1 for time, event in self.song.midiEventTrack[i].getAllEvents() if (isinstance(event, song.MarkerNote) and not event.endMarker and event.number == song.SP_MARKING_NOTE)])
                    if numMidiSoloMarkerNotes > 0 and self.markSolos > 0:  # if at least 1 solo marked in this fashion, tell that guitar to ignore text solo events
                        self.useMidiSoloMarkers = True
                        guitar.useMidiSoloMarkers = True
                        if self.neckrender[self.players[i].guitarNum] is not None:
                            self.neckrender[self.players[i].guitarNum].useMidiSoloMarkers = True

                if numOfSpMarkerNotes > 1:

                    for time, event in self.song.midiEventTrack[i].getAllEvents():
                        if isinstance(event, song.MarkerNote) and not event.endMarker:
                            markStarpower = False
                            if event.number == song.OD_MARKING_NOTE:
                                markStarpower = True
                            if event.number == song.SP_MARKING_NOTE:
                                if self.song.midiStyle == song.MIDI_TYPE_GH:
                                    markStarpower = True

                            if markStarpower and self.starpowerMode == 2:  # auto-MIDI mode only
                                tempStarpowerNoteList = self.song.track[i].getEvents(time, time+event.length)
                                self.spTimes[i].append((time, time+event.length))
                                lastSpNoteTime = 0
                                for spTime, spEvent in tempStarpowerNoteList:
                                    if isinstance(spEvent, Note):
                                        if spTime > lastSpNoteTime:
                                            lastSpNoteTime = spTime
                                        spEvent.star = True
                                # now, go back and mark all of the last chord as finalStar
                                # BUT only if not drums!  If drums, mark only ONE of the last notes!
                                #lastChordTime = spTime
                                oneLastSpNoteMarked = False
                                for spTime, spEvent in tempStarpowerNoteList:
                                    if isinstance(spEvent, Note):
                                        if spTime == lastSpNoteTime:
                                            if (guitar.isDrum and not oneLastSpNoteMarked) or (not guitar.isDrum):
                                                spEvent.finalStar = True
                                                oneLastSpNoteMarked = True
                                # Marker notes logs
                                log.debug("GuitarScene: P%d overdrive / starpower phrase marked between %f and %f" % (i+1, time, time+event.length))
                                if lastSpNoteTime == 0:
                                    log.warning("This starpower phrase doesn't appear to have any finalStar notes marked... probably will not reward starpower!")
                    self.midiSP = True
                    unisonCheck.extend(self.spTimes[i])

                elif self.starpowerMode == 2:  # this particular instrument only has one starpower path marked!  Force auto-generation of SP paths
                    log.warning("Instrument %s only has one starpower path marked!  ...falling back on auto-generated paths for this instrument." % self.players[i].part.text)
                    guitar.starNotesSet = False  # fallback on auto generation.

        elif self.starpowerMode == 2:
            if self.numberOfGuitars > 0:
                log.warning("This song does not appear to have any starpower or overdrive paths marked, falling back on auto-generated paths.")
                for instrument in self.instruments:
                    if instrument.isVocal:
                        continue
                    instrument.starNotesSet = False  # fallback on auto generation.

        if self.useMidiSoloMarkers or self.song.midiStyle == song.MIDI_TYPE_RB or self.markSolos == 3:  # assume RB Midi-types with no solos don't want any, dammit!
            self.markSolos = 0
        for i, player in enumerate(self.players):
            if player.guitarNum is not None:
                self.instruments[i].markSolos = self.markSolos
                if self.neckrender[player.guitarNum] is not None:
                    self.neckrender[player.guitarNum].markSolos = self.markSolos

        self.lastDrumNoteTime = 0.0
        self.lastNoteTimes = [0.0 for i in self.players]
        self.drumScoringEnabled = True

        # moved this to the part where it loads notes...
        for i in range(self.numOfPlayers):
            if self.instruments[i].isVocal:
                self.song.track[i].removeTempoEvents()
                self.song.track[i].markPhrases()
                holdingTap = False
                holdingTapLength = 0
                holdingTapNotes = 0
                phraseId = 0
                for time, event in self.song.track[i].getAllEvents():
                    if isinstance(event, VocalPhrase):
                        if event.tapPhrase:
                            if not holdingTap:
                                holdingTap = True
                                self.instruments[i].tapPartStart.append(phraseId)
                            holdingTapLength += 1
                            holdingTapNotes += len(event)
                        else:
                            if holdingTap:
                                self.instruments[i].tapPartLength.append(holdingTapLength)
                                self.instruments[i].tapNoteTotals.append(holdingTapNotes)
                                self.instruments[i].tapNoteHits.append(0)
                                holdingTap = False
                                holdingTapLength = 0
                                holdingTapNotes = 0
                        phraseId += 1
                else:
                    self.instruments[i].totalPhrases = phraseId
                    if holdingTap:
                        self.instruments[i].tapPartLength.append(holdingTapLength)
                        self.instruments[i].tapNoteTotals.append(holdingTapNotes)
                        self.instruments[i].tapNoteHits.append(0)
            else:
                # preventing ever-thickening BPM lines after restarts
                self.song.track[i].markBars()
                # should only be done the first time
                if not self.instruments[i].isDrum and not self.instruments[i].isVocal:
                    self.song.track[i].markHopo(self.song.info.eighthNoteHopo, self.hopoAfterChord, self.song.info.hopofreq)

        lastTime = 0
        for i in range(self.numOfPlayers):
            for time, event in self.song.track[i].getAllEvents():
                if not isinstance(event, Note) and not isinstance(event, VocalPhrase):
                    continue
                if time + event.length > lastTime:
                    lastTime = time + event.length

        self.lastEvent = lastTime + 1000
        self.lastEvent = round(self.lastEvent / 1000) * 1000
        self.noteLastTime = 0

        totalBreNotes = 0
        # count / init solos and notes
        for i, instrument in enumerate(self.instruments):
            # go through, locate, and mark the last drum note.  When this is encountered, drum scoring should be turned off.
            lastDrumNoteTime = 0.0
            lastDrumNoteEvent = None
            for time, event in self.song.track[i].getAllEvents():
                if isinstance(event, Note) or isinstance(event, VocalPhrase):
                    if time >= lastDrumNoteTime:
                        lastDrumNoteTime = time
                        lastDrumNoteEvent = event
            if instrument.isDrum:
                self.lastDrumNoteTime = lastDrumNoteTime
                log.debug("Last drum note located at time = " + str(self.lastDrumNoteTime))
                self.scoring[i].totalStreakNotes = len([1 for time, event in self.song.track[i].getEvents(self.players[i].startPos, self.lastEvent) if isinstance(event, Note)])
            elif instrument.isVocal:
                self.scoring[i].totalStreakNotes = len([1 for time, event in self.song.track[i].getEvents(self.players[i].startPos, self.lastEvent) if isinstance(event, VocalPhrase)])
            else:
                self.scoring[i].totalStreakNotes = len(set(time for time, event in self.song.track[i].getEvents(self.players[i].startPos, self.lastEvent) if isinstance(event, Note)))
            self.scoring[i].lastNoteEvent = lastDrumNoteEvent
            self.scoring[i].lastNoteTime  = lastDrumNoteTime
            self.lastNoteTimes[i] = lastDrumNoteTime
            if lastDrumNoteEvent:
                if isinstance(lastDrumNoteEvent, Note):
                    log.debug("Last note (number %d) found for player %d at time %f" % (lastDrumNoteEvent.number, i, lastDrumNoteTime))
                elif isinstance(lastDrumNoteEvent, VocalPhrase):
                    log.debug("Last vocal phrase found for player %d at time %f" % (i, lastDrumNoteTime))
            else:
                log.debug("Last note event not found and is None!")

            if instrument.isVocal:
                self.scoring[i].totalNotes = self.scoring[i].totalStreakNotes - len(instrument.tapNoteTotals)
                self.scoring[i].totalPercNotes = sum(instrument.tapNoteTotals)
                self.scoring[i].baseScore = (instrument.vocalBaseScore * self.scoring[i].totalNotes) + (self.scoring[i].totalPercNotes * instrument.baseScore)
            else:
                self.scoring[i].totalNotes = len([1 for Ntime, event in self.song.track[i].getAllEvents() if isinstance(event, Note)])

            if self.song.midiEventTrack[i] is not None:  # filters out vocals
                # determine which marker is BRE, and count streak notes behind it to remove from the scorecard
                if self.song.hasFreestyleMarkings:
                    for time, event in self.song.midiEventTrack[i].getAllEvents():
                        if isinstance(event, song.MarkerNote) and not event.endMarker:
                            if (event.number == song.FREESTYLE_MARKING_NOTE):
                                thisIsABre = False
                                if not instrument.isDrum:
                                    thisIsABre = True

                                if thisIsABre:  # only deal with guitar/bass BRE notes here.  Drum notes will be handled in realtime as they are encountered under a fill or BRE.
                                    breStart = time
                                    breEnd = time + event.length
                                    numBreStreakNotes = len(set(time for time, event in self.song.track[i].getEvents(breStart, breEnd) if isinstance(event, Note)))
                                    self.scoring[i].totalStreakNotes -= numBreStreakNotes   # remove BRE notes correctly from streak count.
                                    log.debug("Removed %d streak notes from player %d" % (numBreStreakNotes, i))
                                    totalBreNotes += numBreStreakNotes

                if instrument.useMidiSoloMarkers:  # mark using the new MIDI solo marking system
                    for time, event in self.song.midiEventTrack[i].getAllEvents():
                        if isinstance(event, song.MarkerNote) and not event.endMarker:
                            if (event.number == song.SP_MARKING_NOTE) and (self.song.midiStyle == song.MIDI_TYPE_RB):  # solo marker note.
                                startTime = time
                                endTime = time + event.length
                                guitarSoloNoteCount = len([1 for Gtime, Gevent in self.song.track[i].getEvents(startTime, endTime) if isinstance(Gevent, Note)])
                                self.guitarSolos[i].append(guitarSoloNoteCount - 1)
                                log.debug("P" + str(i+1) + " MIDI " + self.players[i].part.text + " Solo found from: " + str(startTime) + " to: " + str(endTime) + ", containing " + str(guitarSoloNoteCount) + " notes.")

                elif instrument.markSolos == 1:  # mark using the old text-based system
                    # Ntime now should contain the last note time - this can be used for guitar solo finishing
                    # use new self.song.eventTracks[song.TK_GUITAR_SOLOS] -- retrieve a gsolo on / off combo, then use it to count notes
                    # just like before, detect if end reached with an open solo - and add a GSOLO OFF event just before the end of the song.
                    for time, event in self.song.eventTracks[song.TK_GUITAR_SOLOS].getAllEvents():
                        if event.text.find("GSOLO") >= 0:
                            if event.text.find("ON") >= 0:
                                isGuitarSoloNow = True
                                guitarSoloStartTime = time
                            else:
                                isGuitarSoloNow = False
                                guitarSoloNoteCount = len([1 for Gtime, Gevent in self.song.track[i].getEvents(guitarSoloStartTime, time) if isinstance(Gevent, Note)])
                                self.guitarSolos[i].append(guitarSoloNoteCount - 1)
                                log.debug("GuitarScene: Guitar Solo found: " + str(guitarSoloStartTime) + "-" + str(time) + " = " + str(guitarSoloNoteCount))
                    if isGuitarSoloNow:  # open solo until end - needs end event!
                        isGuitarSoloNow = False
                        # must find the real "last note" time, requires another iteration...
                        for lnTime, lnEvent in self.song.track[i].getAllEvents():
                            if isinstance(lnEvent, Note):
                                if lnTime > Ntime:
                                    Ntime = lnTime
                        guitarSoloNoteCount = len([1 for Gtime, Gevent in self.song.track[i].getEvents(guitarSoloStartTime, Ntime) if isinstance(Gevent, Note)])
                        self.guitarSolos[i].append(guitarSoloNoteCount - 1)
                        newEvent = TextEvent("GSOLO OFF", 100.0)
                        self.song.eventTracks[song.TK_GUITAR_SOLOS].addEvent(Ntime, newEvent)  # adding the missing GSOLO OFF event
                        log.debug("GuitarScene: Guitar Solo until end of song found - (guitarSoloStartTime - Ntime = guitarSoloNoteCount): " + str(guitarSoloStartTime) + "-" + str(Ntime) + " = " + str(guitarSoloNoteCount))

        self.unisonConfirm = []
        self.unisonPlayers = []
        self.unisonIndex = 0
        if self.coOpRB:
            for spNoted in unisonCheck:
                if unisonCheck.count(spNoted) > 1:
                    if spNoted not in self.unisonConfirm:
                        self.unisonConfirm.append(spNoted)
            if len(self.unisonConfirm) > 0:
                self.unisonPlayers = [[] for i in self.unisonConfirm]
                for i in range(len(self.unisonConfirm)):
                    for j in range(len(self.spTimes)):
                        if self.unisonConfirm[i] in self.spTimes[j]:
                            self.unisonPlayers[i].append(j)
                log.debug("Unisons confirmed: " + str(self.unisonConfirm))
                log.debug("Unisons between: " + str(self.unisonPlayers))

        # handle gathering / sizing / grouping line-by-line lyric display here, during initialization:
        self.midiLyricLineEvents = []  # this is a list of sublists of tuples.
                                       # The tuples will contain (time, event)
                                       # The sublists will contain
                                       # references to Lyric text events that will be treated as lines
                                       # such that the game can still use song position to determine each text event's color
        self.midiLyricLines = []  # this is a list of text strings
                                  # it will contain a list of the concatenated midi lines for a simpler lyric display mode
        self.nextMidiLyricLine = ""
        self.lyricHeight = 0

        if self.midiLyricsEnabled > 0 and (self.midiLyricMode == 1 or self.midiLyricMode == 2) and not self.playingVocals:  # line-by-line lyrics mode is selected and enabled:
            lyricFont = self.engine.data.songFont
            txtSize = 0.00170
            self.lyricHeight = lyricFont.getStringSize("A", scale=txtSize)[1]

            # now we need an appropriate array to store and organize the lyric events into "lines"
            #  -- the first attempt at coding this will probably butcher the measures and timing horribly, but at least
            #     those of us with older systems can read the lyrics without them jumping all over the place.
            tempLyricLine = ""
            tempLyricLineEvents = []
            firstTime = None
            for time, event in self.song.eventTracks[song.TK_LYRICS].getAllEvents():
                if not firstTime:
                    firstTime = time
                lastLyricLineContents = tempLyricLine
                tempLyricLine = tempLyricLine + " " + event.text
                if lyricFont.getStringSize(tempLyricLine, scale=txtSize)[0] > self.lineByLineLyricMaxLineWidth:
                    self.midiLyricLineEvents.append(tempLyricLineEvents)
                    self.midiLyricLines.append((firstTime, lastLyricLineContents))
                    firstTime = None
                    tempLyricLine = event.text
                    tempLyricLineEvents = []
                tempLyricLineEvents.append((time, event))
            else:  # after last line is accumulated
                if len(self.midiLyricLines) > 0:
                    self.midiLyricLineEvents.append(tempLyricLineEvents)
                    self.midiLyricLines.append((firstTime, tempLyricLine))

            # test unpacking / decoding the lyrical lines:
            for midiLyricSubList in self.midiLyricLineEvents:
                # Lyric events log
                log.debug("... New MIDI lyric line:")
                for lyricTuple in midiLyricSubList:
                    time, event = lyricTuple
                    # Lyric events log
                    log.debug("MIDI Line-by-line lyric unpack test - time, event = " + str(time) + ", " + event.text)

            for lineStartTime, midiLyricSimpleLineText in self.midiLyricLines:
                # Lyric events log
                log.debug("MIDI Line-by-line simple lyric line starting at time: " + str(lineStartTime) + ", " + midiLyricSimpleLineText)

        self.numMidiLyricLines = len(self.midiLyricLines)

        self.coOpTotalStreakNotes = 0
        self.coOpTotalNotes = 0
        if self.coOpScoreCard:
            self.coOpScoreCard.lastNoteTime = max(self.lastNoteTimes)
            log.debug("Last note for co-op mode found at %.2f" % self.coOpScoreCard.lastNoteTime)
        for i, scoreCard in enumerate(self.scoring):  # accumulate base scoring values for co-op
            if self.coOpScoreCard:
                self.coOpScoreCard.totalStreakNotes += scoreCard.totalStreakNotes
                self.coOpScoreCard.totalNotes += scoreCard.totalNotes
        self.coOpPlayerIndex = len(range(self.numOfPlayers))
        if self.coOpScoreCard:
            self.coOpScoreCard.totalStreakNotes -= totalBreNotes

        # need to store the song's beats per second (bps) for later
        self.songBPS = self.song.bpm / 60.0

        Dialogs.changeLoadingSplashScreenText(self.engine, self.splash, self.phrase + " \n " + _("Loading Graphics..."))

        # Load stage background(s)
        if self.stage.mode == 3:
            self.stage.loadVideo(self.libraryName, self.songName)

        self.stage.load(self.libraryName, self.songName, self.players[0].practiceMode)

        # this determination logic should happen once, globally -- not repeatedly.
        self.showScriptLyrics = False
        if not self.playingVocals:
            if self.song.hasMidiLyrics and self.lyricMode == 3:  # new option for double lyrics
                self.showScriptLyrics = False
            elif not self.song.hasMidiLyrics and self.lyricMode == 3:
                self.showScriptLyrics = True
            elif self.song.info.tutorial:
                self.showScriptLyrics = True
            elif self.lyricMode == 1 and self.song.info.lyrics:  # lyrics: song.ini
                self.showScriptLyrics = True
            elif self.lyricMode == 2:  # lyrics: Auto
                self.showScriptLyrics = True

        self.ready = True

        self.loadmages(w, h)

        self.counterY = -0.1
        self.coOpPhrase = 0

        self.scaleText = [0.0 for i in self.players]
        self.displayText = [None for i in self.players]
        self.displayTextScale = [0.0 for i in self.players]
        self.textTimer = [0.0 for i in self.players]
        self.textY = [.3 for i in self.players]
        self.scaleText2 = [0.0 for i in self.players]
        self.goingUP = [False for i in self.players]
        self.lastStreak = [0 for i in self.players]
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

        self.killswitchEngaged = [None for i in self.players]

        # retrieve theme.ini pause background & text positions
        self.pause_bkg = [float(i) for i in self.engine.theme.pause_bkg_pos]
        self.pause_text_x = self.engine.theme.pause_text_xPos
        self.pause_text_y = self.engine.theme.pause_text_yPos

        if self.pause_text_x is None:
            self.pause_text_x = .3

        if self.pause_text_y is None:
            self.pause_text_y = .31

        # new theme.ini color options
        self.ingame_stats_color = self.engine.theme.ingame_stats_colorVar
        self.pause_text_color = self.engine.theme.pause_text_colorVar
        self.pause_selected_color = self.engine.theme.pause_selected_colorVar
        self.fail_text_color = self.engine.theme.fail_text_colorVar
        self.fail_selected_color = self.engine.theme.fail_selected_colorVar
        self.fail_completed_color = self.engine.theme.fail_completed_colorVar

        settingsMenu = Settings.GameSettingsMenu(self.engine, self.pause_text_color, self.pause_selected_color, players=self.players)
        careerSettingsMenu = Settings.GameCareerSettingsMenu(self.engine, self.pause_text_color, self.pause_selected_color, players=self.players)
        settingsMenu.fadeScreen = False
        careerSettingsMenu.fadeScreen = False

        log.debug("Pause text / selected colors: " + str(self.pause_text_color) + " / " + str(self.pause_selected_color))

        # theme.ini fail positions
        size = self.engine.data.pauseFont.getStringSize("Quit to Main")
        self.fail_bkg = [float(i) for i in self.engine.theme.fail_bkg_pos]
        self.fail_text_x = self.engine.theme.fail_text_xPos
        self.fail_text_y = self.engine.theme.fail_text_yPos
        self.failSongPos = (self.engine.theme.fail_songname_xPos, self.engine.theme.fail_songname_yPos)

        if self.fail_text_x is None:
            self.fail_text_x = .5 - size[0] / 2.0

        if self.fail_text_y is None:
            self.fail_text_y = .47

        self.pauseTextType = self.engine.theme.pauseMenuType

        if self.pauseTextType == "GH3":  # GH3-like theme
            if self.careerMode:
                # adjusted proper spacing
                self.menu = Menu(self.engine, [
                    (_("         RESUME"), self.resumeSong),
                    (_("        RESTART"), self.restartSong),
                    (_("       PRACTICE"), self.practiceSong),
                    (_("        OPTIONS"), careerSettingsMenu),
                    (_("           QUIT"), self.quit),
                ], name="careerpause", fadeScreen=False, onClose=self.resumeGame, font=self.engine.data.pauseFont, pos=(self.pause_text_x, self.pause_text_y), textColor=self.pause_text_color, selectedColor=self.pause_selected_color, append_submenu_char=False)
            else:
                self.menu = Menu(self.engine, [
                    (_("        RESUME"), self.resumeSong),
                    (_("       RESTART"), self.restartSong),
                    (_("      END SONG"), self.endSong),
                    (_("       OPTIONS"), settingsMenu),
                    (_("           QUIT"), self.quit),
                ], name="pause", fadeScreen=False, onClose=self.resumeGame, font=self.engine.data.pauseFont, pos=(self.pause_text_x, self.pause_text_y), textColor=self.pause_text_color, selectedColor=self.pause_selected_color, append_submenu_char=False)
            size = self.engine.data.pauseFont.getStringSize("Quit to Main")
            if self.careerMode:
                self.failMenu = Menu(self.engine, [
                    (_("RETRY SONG"), self.restartAfterFail),
                    (_("  PRACTICE"), self.practiceSong),
                    (_(" NEW SONG"), self.changeAfterFail),
                    (_("     QUIT"), self.quit),
                ], name="careerfail", fadeScreen=False, onCancel=self.changeAfterFail, font=self.engine.data.pauseFont, pos=(self.fail_text_x, self.fail_text_y), textColor=self.fail_text_color, selectedColor=self.fail_selected_color)
            else:
                self.failMenu = Menu(self.engine, [
                    (_("RETRY SONG"), self.restartAfterFail),
                    (_(" NEW SONG"), self.changeAfterFail),
                    (_("     QUIT"), self.quit),
                ], name="fail", fadeScreen=False, onCancel=self.changeAfterFail, font=self.engine.data.pauseFont, pos=(self.fail_text_x, self.fail_text_y), textColor=self.fail_text_color, selectedColor=self.fail_selected_color)

        elif self.pauseTextType == "GH2":  # GH2-like theme
            if self.careerMode:
                self.menu = Menu(self.engine, [
                    (_("  Resume"), self.resumeSong),
                    (_("  Start Over"), self.restartSong),
                    (_("  Change Song"), self.changeSong),
                    (_("  Practice"), self.practiceSong),
                    (_("  Settings"), careerSettingsMenu),
                    (_("  Quit to Main Menu"), self.quit),
                ], name="careerpause", fadeScreen=False, onClose=self.resumeGame, font=self.engine.data.pauseFont, pos=(self.pause_text_x, self.pause_text_y), textColor=self.pause_text_color, selectedColor=self.pause_selected_color)
            else:
                self.menu = Menu(self.engine, [
                    (_("  Resume"), self.resumeSong),
                    (_("  Start Over"), self.restartSong),
                    (_("  Change Song"), self.changeSong),
                    (_("  End Song"), self.endSong),
                    (_("  Settings"), settingsMenu),
                    (_("  Quit to Main Menu"), self.quit),
                ], name="pause", fadeScreen=False, onClose=self.resumeGame, font=self.engine.data.pauseFont, pos=(self.pause_text_x, self.pause_text_y), textColor=self.pause_text_color, selectedColor=self.pause_selected_color)
            size = self.engine.data.pauseFont.getStringSize("Quit to Main")
            if self.careerMode:
                self.failMenu = Menu(self.engine, [
                    (_(" Try Again?"), self.restartAfterFail),
                    (_("  Give Up?"), self.changeAfterFail),
                    (_("  Practice?"), self.practiceSong),
                    (_("Quit to Main"), self.quit),
                ], name="careerfail", fadeScreen=False, onCancel=self.changeAfterFail, font=self.engine.data.pauseFont, pos=(self.fail_text_x, self.fail_text_y), textColor=self.fail_text_color, selectedColor=self.fail_selected_color)
            else:
                self.failMenu = Menu(self.engine, [
                    (_(" Try Again?"), self.restartAfterFail),
                    (_("  Give Up?"), self.changeAfterFail),
                    (_("Quit to Main"), self.quit),
                ], name="fail", fadeScreen=False, onCancel=self.changeAfterFail, font=self.engine.data.pauseFont, pos=(self.fail_text_x, self.fail_text_y), textColor=self.fail_text_color, selectedColor=self.fail_selected_color)

        elif self.pauseTextType == "RB":  # RB-like theme
            size = self.engine.data.pauseFont.getStringSize("Quit to Main Menu")
            if self.careerMode:
                self.menu = Menu(self.engine, [
                    (_("   RESUME"), self.resumeSong),
                    (_("   RESTART"), self.restartSong),
                    (_("   CHANGE SONG"), self.changeSong),
                    (_("   PRACTICE"), self.practiceSong),
                    (_("   SETTINGS"), careerSettingsMenu),
                    (_("   QUIT"), self.quit),
                ], name="careerpause", fadeScreen=False, onClose=self.resumeGame, font=self.engine.data.pauseFont, pos=(self.pause_text_x, self.pause_text_y), textColor=self.pause_text_color, selectedColor=self.pause_selected_color)
            else:
                self.menu = Menu(self.engine, [
                    (_("   RESUME"), self.resumeSong),
                    (_("   RESTART"), self.restartSong),
                    (_("   CHANGE SONG"), self.changeSong),
                    (_("   END SONG"), self.endSong),
                    (_("   SETTINGS"), settingsMenu),
                    (_("   QUIT"), self.quit),
                ], name="pause", fadeScreen=False, onClose=self.resumeGame, font=self.engine.data.pauseFont, pos=(self.pause_text_x, self.pause_text_y), textColor=self.pause_text_color, selectedColor=self.pause_selected_color)
            size = self.engine.data.pauseFont.getStringSize("Quit to Main")
            if self.careerMode:
                self.failMenu = Menu(self.engine, [
                    (_(" RETRY"), self.restartAfterFail),
                    (_(" NEW SONG"), self.changeAfterFail),
                    (_(" PRACTICE"), self.practiceSong),
                    (_(" QUIT"), self.quit),
                ], name="careerfail", fadeScreen=False, onCancel=self.changeAfterFail, font=self.engine.data.pauseFont, pos=(self.fail_text_x, self.fail_text_y), textColor=self.fail_text_color, selectedColor=self.fail_selected_color)
            else:
                self.failMenu = Menu(self.engine, [
                    (_(" RETRY"), self.restartAfterFail),
                    (_(" NEW SONG"), self.changeAfterFail),
                    (_(" QUIT"), self.quit),
                ], name="fail", fadeScreen=False, onCancel=self.changeAfterFail, font=self.engine.data.pauseFont, pos=(self.fail_text_x, self.fail_text_y), textColor=self.fail_text_color, selectedColor=self.fail_selected_color)

        self.restartSong(firstTime=True)

        # hide the splash screen
        Dialogs.hideLoadingSplashScreen(self.engine, self.splash)
        self.splash = None

        #
        # end of GuitarScene client initialization routine
        #

    def freeResources(self):
        self.engine.view.setViewport(1, 0)
        self.counter = None
        self.failScreen = None
        self.failMsg = None
        self.menu = None
        self.mult = None
        self.pauseScreen = None
        self.rockTop = None
        self.rockMsg = None
        for instrument in self.instruments:
            if instrument.isVocal:
                instrument.stopMic()

        # Ensure all event tracks are destroyed before removing Song object!
        if self.song:
            self.song.tracks = None
            self.song.eventTracks = None
            self.song.midiEventTracks = None
        self.song = None

        # additional cleanup!
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
        self.part = [None for i in self.players]
        for scoreCard in self.scoring:
            scoreCard.lastNoteEvent = None
        if self.coOpType:
            self.coOpScoreCard.lastNoteEvent = None

        if self.stage.mode == 3:
            self.engine.view.popLayer(self.stage.vidPlayer)

    def getHandicap(self):
        hopoFreq = self.engine.config.get("coffee", "hopo_frequency")
        try:
            songHopo = int(self.song.info.hopofreq)
        except Exception:
            songHopo = 1
        for i, scoreCard in enumerate(self.scoring):
            if self.instruments[i].isVocal:
                if self.engine.audioSpeedFactor != 1 or scoreCard.earlyHitWindowSizeHandicap != 1.0:  # scalable handicaps
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
                continue
            if self.engine.audioSpeedFactor != 1 or scoreCard.earlyHitWindowSizeHandicap != 1.0:  # scalable handicaps
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
            if self.instruments[i].twoChordApply:
                if (scoreCard.handicap>>3)&1 != 1:
                    scoreCard.handicap += 0x8
                if self.coOpType:
                    if (self.coOpScoreCard.handicap>>3)&1 != 1:
                        self.coOpScoreCard.handicap += 0x8
            if self.instruments[i].hitw == 0.70:
                if (scoreCard.handicap>>4)&1 != 1:
                    scoreCard.handicap += 0x10
                if self.coOpType:
                    if (self.coOpScoreCard.handicap>>4)&1 != 1:
                        self.coOpScoreCard.handicap += 0x10
            elif self.instruments[i].hitw == 1.0:
                if (scoreCard.handicap>>5)&1 != 1:
                    scoreCard.handicap += 0x20
                if self.coOpType:
                    if (self.coOpScoreCard.handicap>>5)&1 != 1:
                        self.coOpScoreCard.handicap += 0x20
            elif self.instruments[i].hitw == 1.9:
                if (scoreCard.handicap>>6)&1 != 1:
                    scoreCard.handicap += 0x40
                if self.coOpType:
                    if (self.coOpScoreCard.handicap>>6)&1 != 1:
                        self.coOpScoreCard.handicap += 0x40
            elif self.instruments[i].hitw == 2.3:
                if (scoreCard.handicap>>7)&1 != 1:
                    scoreCard.handicap += 0x80
                if self.coOpType:
                    if (self.coOpScoreCard.handicap>>7)&1 != 1:
                        self.coOpScoreCard.handicap += 0x80
            elif hopoFreq == 0 and songHopo != 1 and not self.instruments[i].isDrum:
                if (scoreCard.handicap>>9)&1 != 1:
                    scoreCard.handicap += 0x200
                if self.coOpType:
                    if (self.coOpScoreCard.handicap>>9)&1 != 1:
                        self.coOpScoreCard.handicap += 0x200
            elif hopoFreq == 1 and songHopo != 1 and not self.instruments[i].isDrum:
                if (scoreCard.handicap>>10)&1 != 1:
                    scoreCard.handicap += 0x400
                if self.coOpType:
                    if (self.coOpScoreCard.handicap>>10)&1 != 1:
                        self.coOpScoreCard.handicap += 0x400
            elif hopoFreq == 3 and songHopo != 1 and not self.instruments[i].isDrum:
                if (scoreCard.handicap>>11)&1 != 1:
                    scoreCard.handicap += 0x800
                if self.coOpType:
                    if (self.coOpScoreCard.handicap>>11)&1 != 1:
                        self.coOpScoreCard.handicap += 0x800
            elif hopoFreq == 4 and songHopo != 1 and not self.instruments[i].isDrum:
                if (scoreCard.handicap>>12)&1 != 1:
                    scoreCard.handicap += 0x1000
                if self.coOpType:
                    if (self.coOpScoreCard.handicap>>12)&1 != 1:
                        self.coOpScoreCard.handicap += 0x1000
            elif hopoFreq == 5 and songHopo != 1 and not self.instruments[i].isDrum:
                if (scoreCard.handicap>>13)&1 != 1:
                    scoreCard.handicap += 0x2000
                if self.coOpType:
                    if (self.coOpScoreCard.handicap>>13)&1 != 1:
                        self.coOpScoreCard.handicap += 0x2000
            elif self.allTaps == 1 and not self.instruments[i].isDrum:
                if (scoreCard.handicap>>14)&1 != 1:
                    scoreCard.handicap += 0x4000
                if self.coOpType:
                    if (self.coOpScoreCard.handicap>>14)&1 != 1:
                        self.coOpScoreCard.handicap += 0x4000
            if self.whammySavesSP and not self.instruments[i].isDrum:
                if (scoreCard.handicap>>15)&1 != 1:
                    scoreCard.handicap += 0x8000
                if self.coOpType:
                    if (self.coOpScoreCard.handicap>>15)&1 != 1:
                        self.coOpScoreCard.handicap += 0x8000
            if self.autoPlay and self.jurg[i]:
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

    def practiceSong(self):
        """ Switch to Practice """
        if self.song:
            self.song.stop()
            self.song = None
        self.resetVariablesToDefaults()
        self.engine.view.setViewport(1, 0)
        self.engine.view.popLayer(self.menu)
        self.engine.view.popLayer(self.failMenu)
        self.freeResources()
        self.engine.world.gameMode = 1
        self.engine.world.createScene("SongChoosingScene")

    def initBeatAndSpClaps(self):
        if self.song:
            self.beatTime = []
            if self.starClaps or self.beatClaps:
                for time, event in self.song.track[0].getAllEvents():
                    if isinstance(event, Bars):
                        if event.barType == 1 or event.barType == 2:
                            self.beatTime.append(time)

    def resetVariablesToDefaults(self):
        if self.song:
            self.song.readyToGo = False
        self.countdownSeconds = 3  # This needs to be reset for song restarts, too!
        self.countdown = float(self.countdownSeconds) * self.songBPS
        self.countdownOK = False
        self.scaleText = [0.0 for i in self.players]
        self.displayText = [None for i in self.players]
        self.displayTextScale = [0.0 for i in self.players]
        self.textTimer = [0.0 for i in self.players]
        self.textY = [.3 for i in self.players]
        self.scaleText2 = [0.0 for i in self.players]
        self.goingUP = [False for i in self.players]
        self.lastStreak = [0 for i in self.players]
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
        self.dispAccuracy = [False for i in self.players]
        for instrument in self.instruments:
            instrument.spEnabled = True
            instrument.bigRockEndingMarkerSeen = False
        for scoreCard in self.scoring:
            scoreCard.reset()
        self.crowdsCheering = False
        if self.coOpType:
            self.coOpScoreCard.reset()
            self.coOpStarPower = 0
            self.coOpStarPowerTimer = 0
            self.coOpStarPowerActive = [0 for i in self.players]
        self.mutedLastSecondYet = False
        self.dispSoloReview = [False for i in self.players]
        self.soloReviewCountdown = [0 for i in self.players]
        self.guitarSoloAccuracy = [0.0 for i in self.players]
        self.guitarSoloActive = [False for i in self.players]
        self.currentGuitarSolo = [0 for i in self.players]
        self.guitarSoloBroken = [False for i in self.players]
        self.inUnison = [False for i in self.players]
        self.haveUnison = [False for i in self.players]
        self.firstUnison = False
        self.firstUnisonDone = False
        self.unisonNum = 0
        self.unisonIndex = 0
        self.unisonActive = False
        self.unisonEarn = [False for i in self.players]
        self.resumeCountdown = 0
        self.resumeCountdownSeconds = 0
        self.pausePos = 0
        self.failTimer = 0
        self.rockTimer = 0
        self.youRock = False
        self.rockFinished = False
        self.rock = [self.rockMax / 2 for i in self.players]
        self.minusRock = [0.0 for i in self.players]
        self.plusRock = [0.0 for i in self.players]
        self.coOpMulti = 1
        self.deadPlayerList = []
        self.numDeadPlayers = 0
        self.coOpFailDone = [False for i in self.players]
        self.rockFailUp = True
        self.rockFailViz = 0.0
        self.failViz = [0.0 for i in self.players]
        if self.coOpRB:
            self.rock.append(self.rockMax / 2)
            self.minusRock.append(0.0)
            self.plusRock.append(0.0)
            self.timesFailed = [0 for i in self.players]
        for instrument in self.instruments:
            instrument.starPower = 0
            instrument.coOpFailed = False
            # BRE variables reset
            instrument.freestyleStart = 0
            instrument.freestyleFirstHit = 0
            instrument.freestyleLength = 0
            instrument.freestyleBonusFret = 0
            if instrument.isDrum:
                instrument.drumFillsCount = 0
                instrument.drumFillsHits = 0
            instrument.freestyleLastFretHitTime = [0 for i in range(5)]
            if instrument.isVocal:
                instrument.doneLastPhrase = False
                instrument.phraseIndex = 0
                instrument.currentTapPhrase = -1
                instrument.phraseInTune = 0
                instrument.phraseNoteTime = 0
                instrument.phraseTaps = 0
                instrument.phraseTapsHit = 0
        # shaders reset
        shaders.reset()
        if shaders.turnon:
            for i, player in enumerate(self.players):
                shaders.var["fret"][i] = [-10.0] * 5
                shaders.var["fretpos"][i] = [-10.0] * 5
                shaders.var["color"][i] = (.0, ) * 4
                shaders.var["scoreMult"][i] = 1
                shaders.var["multChangePos"][i] = -10.0
        self.failed = False
        self.finalFailed = False
        self.failEnd = False
        self.drumScoringEnabled = True
        self.initBeatAndSpClaps()

        # init vars for the next time & lyric line to display
        self.midiLyricLineIndex = 0
        self.nextMidiLyricStartTime = 0
        if self.numMidiLyricLines > 0:
            self.nextMidiLyricStartTime, self.nextMidiLyricLine = self.midiLyricLines[self.midiLyricLineIndex]

        # initialize word-by-word 2-line MIDI lyric display / highlighting system
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

        # reset global tempo variables
        self.currentBpm     = song.DEFAULT_BPM
        self.currentPeriod  = 60000.0 / self.currentBpm
        self.targetBpm      = self.currentBpm
        self.lastBpmChange  = -1.0
        self.baseBeat       = 0.0
        self.songTime = -self.engine.config.get('audio', 'delay')

        if self.midiLyricMode == 2 and not self.playingVocals:

            if self.numMidiLyricLines > self.activeMidiLyricLineIndex:
                self.numWordsInCurrentMidiLyricLine = 0
                for nextLyricTime, nextLyricEvent in self.midiLyricLineEvents[self.activeMidiLyricLineIndex]:  # populate the first active line
                    self.numWordsInCurrentMidiLyricLine += 1

                if self.numWordsInCurrentMidiLyricLine > self.activeMidiLyricWordSubIndex + 1:  # there is another word in this line
                    self.nextLyricWordTime, self.nextLyricEvent = self.midiLyricLineEvents[self.activeMidiLyricLineIndex][self.activeMidiLyricWordSubIndex]
                else:
                    self.noMoreMidiLineLyrics = True  # t'aint no lyrics t'start wit!
                for nextLyricTime, nextLyricEvent in self.midiLyricLineEvents[self.activeMidiLyricLineIndex]:  # populate the first active line
                    self.activeMidiLyricLine_WhiteWords = "%s %s" % (self.activeMidiLyricLine_WhiteWords, nextLyricEvent.text)
                if self.numMidiLyricLines > self.activeMidiLyricLineIndex + 2:  # is there a second line of lyrics?
                    tempTime, self.currentSimpleMidiLyricLine = self.midiLyricLines[self.activeMidiLyricLineIndex+1]

        for player in self.players:
            player.reset()
        self.stage.reset()
        self.stage.rockmeter.reset()
        self.enteredCode = []
        self.jurgPlayer = [False for i in self.players]  # Jurgen hasn't played the restarted song =P

        for instrument in self.instruments:
            instrument.scoreMultiplier = 1
            if instrument.isVocal:
                instrument.phraseIndex = 0
                instrument.currentTapPhrase = -1
                instrument.tapNoteHits = [0 for i in instrument.tapNoteTotals]
                instrument.currentPhraseTime = 0
                instrument.currentPhraseLength = 0
                instrument.activePhrase = None
                continue
            instrument.twoChord = 0
            instrument.hopoActive = 0
            instrument.wasLastNoteHopod = False
            instrument.sameNoteHopoString = False
            instrument.hopoLast = -1
            instrument.guitarSolo = False
            instrument.neck.guitarSolo = False
            instrument.currentGuitarSoloHitNotes = 0

        if self.battle:
            for i in range(self.numOfPlayers):
                self.instruments[i].actions = self.players[i].actions

        self.engine.collectGarbage()
        # sets the default distances the neck has to move in the animation
        if self.neckintroAnimationType == 0:  # Original
            self.boardY = 2
        elif self.neckintroAnimationType == 1:  # Guitar Hero
            self.boardY = 10
        elif self.neckintroAnimationType == 2:  # Rock Band
            self.boardZ = 5
        elif self.neckintroAnimationType == 4:  # By Theme
            if self.neckintroThemeType == "fofix":  # Original
                self.boardY = 2
            elif self.neckintroThemeType == "guitar hero":  # Guitar Hero
                self.boardY = 10
            elif self.neckintroThemeType == "rockband":  # Rock Band
                self.boardZ = 5
        self.setCamera()

        if self.song:
            self.song.readyToGo = True

    def startSolo(self, playerNum):  # more modular and general handling of solos
        i = playerNum
        # Guitar Solo Start
        self.currentGuitarSoloTotalNotes[i] = self.guitarSolos[i][self.currentGuitarSolo[i]]
        self.guitarSoloBroken[i] = False
        self.instruments[i].guitarSolo = True
        if not self.instruments[i].isVocal:
            self.instruments[i].neck.guitarSolo = True
        instrumentSoloString = "%s %s" % (self.players[i].part.text, self.tsSolo)
        if self.phrases > 1:
            self.newScalingText(self.players[i].number, instrumentSoloString)
        if self.engine.data.cheerSoundFound > 0:
            self.engine.data.crowdSound.play()

    def endSolo(self, playerNum):  # more modular and general handling of solos
        i = playerNum
        # Guitar Solo End
        self.instruments[i].guitarSolo = False
        if not self.instruments[i].isVocal:
            self.instruments[i].neck.guitarSolo = False
        self.guitarSoloAccuracy[i] = (float(self.instruments[i].currentGuitarSoloHitNotes) / float(self.currentGuitarSoloTotalNotes[i])) * 100.0
        if not self.guitarSoloBroken[i]:  # backup perfect solo detection
            if self.instruments[i].currentGuitarSoloHitNotes > 0:  # need to make sure someone didn't just not play a guitar solo at all - and still wind up with 100%
                self.guitarSoloAccuracy[i] = 100.0
        if self.guitarSoloAccuracy[i] > 100.0:
            self.guitarSoloAccuracy[i] = 100.0
        if self.guitarSoloBroken[i] and self.guitarSoloAccuracy[i] == 100.0:  # streak was broken, not perfect solo, force 99%
            self.guitarSoloAccuracy[i] = 99.0

        if self.guitarSoloAccuracy[i] == 100.0:  # soloDescs changed
            soloDesc = self.tsPerfectSolo
            soloScoreMult = 100
            if self.engine.data.cheerSoundFound > 0:
                self.engine.data.crowdSound.play()  # liquid
        elif self.guitarSoloAccuracy[i] >= 95.0:
            soloDesc = self.tsAwesomeSolo
            soloScoreMult = 50
            if self.engine.data.cheerSoundFound > 0:
                self.engine.data.crowdSound.play()  # liquid
        elif self.guitarSoloAccuracy[i] >= 90.0:
            soloDesc = self.tsGreatSolo
            soloScoreMult = 30
            if self.engine.data.cheerSoundFound > 0:
                self.engine.data.crowdSound.play()  # liquid
        elif self.guitarSoloAccuracy[i] >= 80.0:
            soloDesc = self.tsGoodSolo
            soloScoreMult = 20
        elif self.guitarSoloAccuracy[i] >= 70.0:
            soloDesc = self.tsSolidSolo
            soloScoreMult = 10
        elif self.guitarSoloAccuracy[i] >= 60.0:
            soloDesc = self.tsOkaySolo
            soloScoreMult = 5
        else:  # 0% - 59.9%
            soloDesc = self.tsMessySolo
            soloScoreMult = 0
            self.engine.data.failSound.play()  # liquid
        soloBonusScore = soloScoreMult * self.instruments[i].currentGuitarSoloHitNotes
        self.scoring[i].score += soloBonusScore
        if self.coOpType:
            self.coOpScoreCard.score += soloBonusScore
        trimmedSoloNoteAcc = self.roundDecimalForDisplay(self.guitarSoloAccuracy[i])
        self.soloReviewText[i] = [
            soloDesc,
            "%(soloNoteAcc)s%% = %(soloBonus)d %(pts)s" % {'soloNoteAcc': str(trimmedSoloNoteAcc), 'soloBonus': soloBonusScore, 'pts': self.tsPtsLabel}
        ]
        self.dispSoloReview[i] = True
        self.soloReviewCountdown[i] = 0
        # reset for next solo
        self.instruments[i].currentGuitarSoloHitNotes = 0
        self.currentGuitarSolo[i] += 1

    def updateGuitarSolo(self, playerNum):
        i = playerNum
        if self.instruments[i].guitarSolo:
            # update guitar solo for player i

            # if we hit more notes in the solo than were counted, update the solo count (for the slop)
            if self.instruments[i].currentGuitarSoloHitNotes > self.currentGuitarSoloTotalNotes[i]:
                self.currentGuitarSoloTotalNotes[i] = self.instruments[i].currentGuitarSoloHitNotes

            if self.instruments[i].currentGuitarSoloHitNotes != self.currentGuitarSoloLastHitNotes[i]:  # changed!
                self.currentGuitarSoloLastHitNotes[i] = self.instruments[i].currentGuitarSoloHitNotes  # update.
                if self.guitarSoloAccuracyDisplayMode > 0:  # if not off:
                    tempSoloAccuracy = (float(self.instruments[i].currentGuitarSoloHitNotes) / float(self.currentGuitarSoloTotalNotes[i]) * 100.0)
                    trimmedIntSoloNoteAcc = self.roundDecimalForDisplay(tempSoloAccuracy)
                    if self.guitarSoloAccuracyDisplayMode == 1:  # percentage only
                        self.solo_soloText[i] = "%s%%" % str(trimmedIntSoloNoteAcc)
                    elif self.guitarSoloAccuracyDisplayMode == 2:   #detailed
                        self.solo_soloText[i] = "%(hitSoloNotes)d/ %(totalSoloNotes)d: %(soloAcc)s%%" % {'hitSoloNotes': self.instruments[i].currentGuitarSoloHitNotes, 'totalSoloNotes': self.currentGuitarSoloTotalNotes[i], 'soloAcc': str(trimmedIntSoloNoteAcc)}
                    self.solo_soloText[i] = self.solo_soloText[i].replace("0", "O")

                    self.solo_Tw[i], self.solo_Th[i] = self.solo_soloFont.getStringSize(self.solo_soloText[i], self.solo_txtSize)
                    self.solo_boxXOffset[i] = self.solo_xOffset[i]

                    if self.guitarSoloAccuracyDisplayPos == 0:  # right
                        self.solo_xOffset[i] -= self.solo_Tw[i]
                        self.solo_boxXOffset[i] -= self.solo_Tw[i] / 2
                    elif self.guitarSoloAccuracyDisplayPos == 1:  # centered
                        self.solo_xOffset[i] = 0.5 - self.solo_Tw[i] / 2
                        self.solo_boxXOffset[i] = 0.5
                    elif self.guitarSoloAccuracyDisplayPos == 3:  # rock band
                        if self.hitAccuracyPos == 0:  # Center - need to move solo text above this!
                            self.solo_yOffset[i] = 0.100  # above Jurgen Is Here
                        elif self.jurgPlayer[i] and self.autoPlay:
                            self.solo_yOffset[i] = 0.140  # above Jurgen Is Here
                        else:  # no jurgens here:
                            self.solo_yOffset[i] = 0.175  # was 0.210, occluded notes
                        self.solo_xOffset[i] = 0.5 - self.solo_Tw[i] / 2
                        self.solo_boxXOffset[i] = 0.5
                    else:  # left
                        self.solo_boxXOffset[i] += self.solo_Tw[i] / 2

                    self.guitarSoloShown[i] = True

        else:  # not currently a guitar solo - clear Lamina solo accuracy surface (but only once!)
            if self.guitarSoloShown[i]:
                self.guitarSoloShown[i] = False
                self.currentGuitarSoloLastHitNotes[i] = 1

    def handleWhammy(self, playerNum):
        i = playerNum
        if self.resumeCountdown > 0:  # conditions to completely ignore whammy
            return

        try:  # since analog axis might be set but joystick not present = crash
            # adding another nest of logic filtration; don't even want to run these checks unless there are playedNotes present!
            if self.instruments[i].playedNotes:
                # Player i kill / whammy check:
                if self.isKillAnalog[i]:
                    if self.CheckForValidKillswitchNote(i):  # if a note has length and is being held enough to get score
                        # rounding to integers, setting volumes 0-10 and only when changed from last time:
                        # want a whammy reading of 0.0 to = full volume, as that's what it reads at idle
                        if self.analogKillMode[i] == 2:  # XBOX mode: (1.0 at rest, -1.0 fully depressed)
                            self.whammyVol[i] = 1.0 - (round(10 * ((self.engine.input.joysticks[self.whichJoyKill[i]].get_axis(self.whichAxisKill[i]) + 1.0) / 2.0)) / 10.0)
                        elif self.analogKillMode[i] == 3:  # XBOX Inverted mode: (-1.0 at rest, 1.0 fully depressed)
                            self.whammyVol[i] = (round(10 * ((self.engine.input.joysticks[self.whichJoyKill[i]].get_axis(self.whichAxisKill[i]) + 1.0) / 2.0)) / 10.0)
                        else:  # PS2 mode: (0.0 at rest, fluctuates between 1.0 and -1.0 when pressed)
                            self.whammyVol[i] = (round(10 * (abs(self.engine.input.joysticks[self.whichJoyKill[i]].get_axis(self.whichAxisKill[i])))) / 10.0)
                        if self.whammyVol[i] > 0.0 and self.whammyVol[i] < 0.1:
                            self.whammyVol[i] = 0.1
                        # simple whammy tail determination:
                        if self.whammyVol[i] > 0.1:
                            self.killswitchEngaged[i] = True
                        else:
                            self.killswitchEngaged[i] = False

                        if self.whammyVol[i] != self.lastWhammyVol[i] and self.whammyVol[i] > 0.1:
                            if self.instruments[i].killPoints:
                                self.instruments[i].starPower += self.analogKillswitchStarpowerChunkSize
                                if self.instruments[i].starPower > 100:
                                    self.instruments[i].starPower = 100
                            elif (self.instruments[i].starPowerActive and self.whammySavesSP):
                                self.instruments[i].starPower += self.analogKillswitchActiveStarpowerChunkSize
                                if self.instruments[i].starPower > 100:
                                    self.instruments[i].starPower = 100

                        self.lastWhammyVol[i] = self.whammyVol[i]

                        # here, scale whammyVol to match kill volume setting:
                        self.targetWhammyVol[i] = self.whammyVol[i] * (self.activeVolume - self.killVolume)

                        if self.actualWhammyVol[i] < self.targetWhammyVol[i]:
                            self.actualWhammyVol[i] += self.whammyVolAdjStep
                            whammyVolSet = self.activeVolume - self.actualWhammyVol[i]
                            if self.whammyEffect == 0:  # killswitch
                                self.song.setInstrumentVolume(whammyVolSet, self.players[i].part)
                            elif self.whammyEffect == 1:  # pitchbend
                                self.song.setInstrumentPitch(self.pitchBendSemitones*self.whammyVol[i], self.players[i].part)

                        elif self.actualWhammyVol[i] > self.targetWhammyVol[i]:
                            self.actualWhammyVol[i] -= self.whammyVolAdjStep
                            whammyVolSet = 1.0 - self.actualWhammyVol[i]
                            if self.whammyEffect == 0:  # killswitch
                                self.song.setInstrumentVolume(whammyVolSet, self.players[i].part)
                            elif self.whammyEffect == 1:  # pitchbend
                                self.song.setInstrumentPitch(self.pitchBendSemitones*self.whammyVol[i], self.players[i].part)

                    elif self.scoring[i].streak > 0:
                        self.song.setInstrumentVolume(1.0, self.players[i].part)
                        if self.whammyEffect == 1:  # pitchbend
                            self.song.resetInstrumentPitch(self.players[i].part)
                        self.actualWhammyVol[i] = self.defaultWhammyVol[i]

                else:  # digital killswitch
                    if self.CheckForValidKillswitchNote(i):  # if a note has length and is being held enough to get score
                        if self.killswitchEngaged[i]:  # Fix the killswitch
                            if self.instruments[i].isKillswitchPossible():
                                self.killswitchEngaged[i] = True
                                if self.whammyEffect == 0:  # killswitch
                                    self.song.setInstrumentVolume(self.killVolume, self.players[i].part)
                                elif self.whammyEffect == 1:  # pitchbend
                                    self.song.setInstrumentPitch(self.pitchBendSemitones*(1.0-self.whammyVol[i]), self.players[i].part)
                                if self.instruments[i].killPoints:
                                    self.instruments[i].starPower += self.digitalKillswitchStarpowerChunkSize
                                    if self.instruments[i].starPower > 100:
                                        self.instruments[i].starPower = 100
                                elif (self.instruments[i].starPowerActive and self.whammySavesSP and not self.instruments[i].isVocal):
                                    self.instruments[i].starPower += self.digitalKillswitchActiveStarpowerChunkSize
                                    if self.instruments[i].starPower > 100:
                                        self.instruments[i].starPower = 100

                            else:
                                self.killswitchEngaged[i] = None
                        elif self.scoring[i].streak > 0:
                            self.song.setInstrumentVolume(1.0, self.players[i].part)
                            if self.whammyEffect == 1:  # pitchbend
                                self.song.resetInstrumentPitch(self.players[i].part)
                            self.killswitchEngaged[i] = False
                    elif self.scoring[i].streak > 0:
                        self.song.setInstrumentVolume(1.0, self.players[i].part)
                        if self.whammyEffect == 1:  # pitchbend
                            self.song.resetInstrumentPitch(self.players[i].part)
                        self.killswitchEngaged[i] = False
                    else:
                        self.killswitchEngaged[i] = False

        except Exception:
            self.whammyVol[i] = self.defaultWhammyVol[i]

    def handleAnalogSP(self, playerNum, ticks):
        i = playerNum
        if self.resumeCountdown > 0:
            return
        if self.isSPAnalog[i]:
            self.starAxisVal[i] = abs(self.engine.input.joysticks[self.whichJoyStar[i]].get_axis(self.whichAxisStar[i]))
            if self.starAxisVal[i] > (self.analogSPThresh[i] / 100.0):
                if self.starDelay[i] == 0 and not self.starActive[i]:
                    self.starDelay[i] = (10 - self.analogSPSense[i]) * 25
                else:
                    self.starDelay[i] -= ticks
                    if self.starDelay[i] <= 0 and not self.starActive[i]:
                        self.activateSP(i)
                        self.starActive[i] = True
            else:
                self.starActive[i] = False
                self.starDelay[i] = 0

    def handleAnalogSlider(self, playerNum):
        i = playerNum
        if self.resumeCountdown > 0:
            return
        if self.isSlideAnalog[i]:
            oldSlide = self.slideValue[i]
            if self.analogSlideMode[i] == 1:  # Inverted mode
                slideVal = -(self.engine.input.joysticks[self.whichJoySlide[i]].get_axis(self.whichAxisSlide[i]) + 1.0) / 2.0
            else:  # Default
                slideVal = (self.engine.input.joysticks[self.whichJoySlide[i]].get_axis(self.whichAxisSlide[i]) + 1.0) / 2.0
            if slideVal > 0.9 or slideVal < 0.01:
                self.slideValue[i] = 4
            elif slideVal > 0.77:
                self.slideValue[i] = 4
                self.markSlide(i)
            elif slideVal > 0.68:
                self.slideValue[i] = 3
            elif slideVal > 0.60:
                self.slideValue[i] = 3
                self.markSlide(i)
            elif slideVal > 0.54:
                self.slideValue[i] = 2
            elif slideVal > 0.43:
                self.slideValue[i] = -1
                # mark that sliding is not happening
            elif slideVal > 0.34:
                self.slideValue[i] = 2
                self.markSlide(i)
            elif slideVal > 0.28:
                self.slideValue[i] = 1
            elif slideVal > 0.16:
                self.slideValue[i] = 1
                self.markSlide(i)
            else:
                self.slideValue[i] = 0

            if self.slideValue[i] != oldSlide:
                for n, k in enumerate(self.keysList[i]):
                    if n == self.slideValue[i] and not self.controls.getState(k):
                        self.controls.toggle(k, True)
                        self.keyPressed(None, 0, k)
                    elif self.controls.getState(k):
                        self.controls.toggle(k, False)
                        self.keyReleased(k)

                if self.slideValue[i] > -1:
                    self.handlePick(i)

    def markSlide(self, playerNum):
        pass  # this will eventually handle the switch that you are, in fact, sliding up the analog fret bar.

    def handlePhrases(self, playerNum, playerStreak):
        if self.phrases > 0:

            i = playerNum
            vocalPart = False
            if not (self.coOpType and i == self.coOpPhrase):
                if self.instruments[i].isVocal:
                    vocalPart = True
            if (self.coOpType and i == self.coOpPhrase) or not self.coOpType:
                if self.lastStreak[i] < playerStreak:
                    textChanged = True
                else:
                    textChanged = False
                self.lastStreak[i] = playerStreak

                if vocalPart:
                    streakModulo = playerStreak % 5
                    if ((streakModulo == 0) or (self.lastStreak[i] % 5 > streakModulo)) and playerStreak > 4 and textChanged:
                        self.newScalingText(i, self.tsPhraseStreak % (playerStreak - streakModulo))
                elif (playerStreak == 50 or (self.lastStreak[i] < 50 and playerStreak > 50)) and textChanged:
                    self.newScalingText(i, self.tsNoteStreak % 50)
                # I think a simple integer modulo would be more efficient here:
                else:
                    streakModulo = playerStreak % 100
                    if ((streakModulo == 0) or (self.lastStreak[i] % 100 > streakModulo)) and playerStreak > 50 and textChanged:
                        self.newScalingText(i, self.tsNoteStreak % (playerStreak - streakModulo))

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

            if self.displayText[i] is not None and self.scaleText[i] < self.maxDisplayTextScale:
                self.scaleText[i] += self.displayTextScaleStep1
            if self.scaleText[i] > self.maxDisplayTextScale:
                self.scaleText[i] = self.maxDisplayTextScale
            if self.displayText[i] is not None:
                self.textTimer[i] += 1
            if self.textTimer[i] > self.textTimeToDisplay:
                self.textY[i] -= 0.02
            if self.textY[i] < 0:
                self.scaleText[i] = 0
                self.textTimer[i] = 0
                self.displayText[i] = None
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

    def handlePick(self, playerNum, hopo=False, pullOff=False):
        i = playerNum
        num = playerNum
        guitar = self.instruments[num]

        if self.resumeCountdown > 0:  # conditions to completely ignore picks
            return

        # only actually pick if the player has not failed already!
        if self.rock[i] > 0:

            # new BRE and drum fills scoring
            if guitar.freestyleActive or (guitar.isDrum and guitar.drumFillsActive):
                if guitar.freestyleActive:  # only for BREs, not drum fills.  Will depend on BRE sound option when implemented.
                    self.song.setInstrumentVolume(1.0, self.players[i].part)  # ensure that every freestyle pick, the volume for that track is set to 1.0
                score = 0
                numFreestyleHits = guitar.freestylePick(self.song, self.songTime, self.controls)
                if numFreestyleHits > 0 or guitar.isDrum:
                    if guitar.freestyleFirstHit + guitar.freestyleLength < self.songTime:
                        guitar.freestyleFirstHit = self.songTime
                        guitar.freestylePeriod = 1500
                        guitar.freestyleBaseScore = 150
                        score = 600 * numFreestyleHits
                        if guitar.isDrum:
                            guitar.drumFillsHits = 0
                        guitar.freestyleLastHit = self.songTime - guitar.freestylePeriod
                        for fret in range(0, 5):
                            guitar.freestyleLastFretHitTime[fret] = self.songTime - guitar.freestylePeriod

                    if guitar.isDrum:
                        guitar.drumFillsHits += 1
                    for fret in range(5):
                        if self.controls.getState(guitar.keys[fret]) or (self.players[i].controlType == 0 and self.controls.getState(guitar.keys[fret+5])):
                            hitspeed = min((self.songTime - guitar.freestyleLastFretHitTime[fret]) / guitar.freestylePeriod, 1.0)
                            score += guitar.freestyleBaseScore * hitspeed
                    if numFreestyleHits > 0:  # to prevent a float division!
                        score = int(score / numFreestyleHits)

                    for fret in range(5):
                        if self.controls.getState(guitar.keys[fret]) or (self.players[i].controlType == 0 and self.controls.getState(guitar.keys[fret+5])):
                            guitar.freestyleLastFretHitTime[fret] = self.songTime

                    # Add all BRE score to a temporary score accumulator with a separate display box
                    # and only reward if all notes after the BRE are hit without breaking streak!
                    if guitar.freestyleActive:  # only want to add the score if this is a BRE - drum fills get no scoring...
                        if self.coOpType:
                            self.scoring[num].endingScore += score
                            self.scoring[num].endingStreakBroken = False
                            self.scoring[num].freestyleWasJustActive = True
                            self.coOpScoreCard.endingScore += score
                            self.coOpScoreCard.endingStreakBroken = False
                            self.coOpScoreCard.freestyleWasJustActive = True
                        else:
                            self.scoring[num].endingScore += score
                            # also, when this happens, want to set a flag indicating that all of the remaining notes in the song must be hit without
                            # breaking streak, or this score will not be kept!
                            self.scoring[num].endingStreakBroken = False
                            self.scoring[num].freestyleWasJustActive = True

                # also must ensure notes that pass during this time are marked as skipped without resetting the streak
                #missedNotes = self.guitars[num].getMissedNotes(self.song, self.songTime, catchup = True)
                missedNotes = guitar.getMissedNotes(self.song, self.songTime + guitar.earlyMargin, catchup=True)  # check slightly ahead here.
                for tym, theNote in missedNotes:  # also want to mark these notes as Played so they don't count against the note total!
                    theNote.skipped = True
                    if guitar.isDrum:
                        if self.coOpType:
                            self.coOpScoreCard.totalStreakNotes -= 1
                        else:
                            self.scoring[num].totalStreakNotes -= 1

            else:
                self.doPick3GH2(i, hopo, pullOff)

    def handleJurgen(self, pos):
        chordFudge = 1  # was 10 - needed to detect chords
        if self.firstGuitar is not None:
            chordFudge = self.song.track[self.firstGuitar].chordFudge
        if self.autoPlay or self.assisting:
            for i, instrument in enumerate(self.instruments):
                # Allow Jurgen per player...
                if self.jurg[i]:
                    # if it is this player
                    self.jurgPlayer[i] = True
                else:
                    if self.playerAssist[i] == 0:  # and no assist
                        continue
                if instrument.isVocal:
                    continue

                # Have Jurgen attempt to strum on time instead of as early as possible
                # This method retrieves all notes in the window and only attempts to play them as they pass the current position, like a real player
                notes = self.instruments[i].getRequiredNotes(self.song, pos)  # needed updatin'

                # now, want to isolate the first note or set of notes to strum - then do it, and then release the controls
                if notes:
                    jurgStrumTime = notes[0][0]
                    jurgStrumNotes = [note.number for time, note in notes if abs(time - jurgStrumTime) <= chordFudge]
                else:
                    jurgStrumTime = 0
                    jurgStrumNotes = []

                changed = False
                held = 0

                # check if jurgStrumTime is close enough to the current position (or behind it) before actually playing the notes
                if (not notes or jurgStrumTime <= (pos + 30)) and self.aiPlayNote[i]:
                    for n, k in enumerate(self.keysList[i]):
                        if n > 4:
                            break
                        if (self.autoPlay and self.jurg[i]) or (k == instrument.keys[4] and self.playerAssist[i] == 2) or ((k == instrument.keys[4] or k == instrument.keys[3]) and self.playerAssist[i] == 1) or (instrument.isDrum and self.playerAssist[i] == 3 and k == instrument.keys[0]):
                            if n in jurgStrumNotes and not self.controls.getState(k):
                                changed = True
                                self.controls.toggle(k, True)
                                self.keyPressed(None, 0, k)
                            elif n not in jurgStrumNotes and self.controls.getState(k):
                                changed = True
                                self.controls.toggle(k, False)
                                self.keyReleased(k)
                            if self.controls.getState(k):
                                held += 1

                    if changed and held and not instrument.isDrum:  # dont need the extra pick for drums
                        self.handlePick(i)
                    # release all frets - who cares about held notes, I want a test player (actually if no keyReleased call, will hold notes fine)
                    for n, k in enumerate(self.keysList[i]):
                        if (self.autoPlay and self.jurg[i]) or (k == instrument.keys[4] and self.playerAssist[i] == 2) or ((k == instrument.keys[4] or k == instrument.keys[3]) and self.playerAssist[i] == 1) or (instrument.isDrum and self.playerAssist[i] == 3 and k == instrument.keys[0]):
                            if self.controls.getState(k):
                                self.controls.toggle(k, False)

    def rockmeterDecrease(self, playerNum, vScore=0):
        """ Decreases the rockmeter for the player when a note is missed """
        i = playerNum

        rockMinusAmount = 0  # simplify the various incarnations of minusRock.
        if self.instruments[i].isDrum:
            self.drumStart = True
            if not self.drumScoringEnabled:  # ignore when drum scoring is disabled
                return

        if not self.failingEnabled or self.practiceMode:
            return

        if self.instruments[i].isVocal:
            rockMinusAmount = 500 * (3 - vScore)
            self.rock[i] -= rockMinusAmount
            if (not self.coOpRB) and (self.rock[i] / self.rockMax <= 0.667) and ((self.rock[i] + rockMinusAmount) / self.rockMax > 0.667):
                self.playersInGreen -= 1
            return

        if self.battle and self.numOfPlayers > 1:  # battle mode
            if self.notesMissed[i]:
                self.minusRock[i] += self.minGain / self.multi[i]
                if self.plusRock[i] > self.pluBase:
                    self.plusRock[i] -= self.pluGain * 2.0 / self.multi[i]
                if self.plusRock[i] <= self.pluBase:
                    self.plusRock[i] = self.pluBase / self.multi[i]
            if self.lessMissed[i]:
                self.minusRock[i] += self.minGain / 5.0 / self.multi[i]
                if self.plusRock[i] > self.pluBase:
                    self.plusRock[i] -= self.pluGain / 2.5 / self.multi[i]

        elif self.coOp and self.numOfPlayers > 1:  # co-op mode
            if self.notesMissed[i]:
                self.minusRock[self.coOpPlayerMeter] += self.minGain / self.multi[i]
                rockMinusAmount = self.minusRock[self.coOpPlayerMeter] / self.multi[i]
                self.rock[self.coOpPlayerMeter] -= rockMinusAmount
                if self.plusRock[self.coOpPlayerMeter] > self.pluBase:
                    self.plusRock[self.coOpPlayerMeter] -= self.pluGain * 2.0 / self.multi[i]
                if self.plusRock[self.coOpPlayerMeter] <= self.pluBase:
                    self.plusRock[self.coOpPlayerMeter] = self.pluBase / self.multi[i]
            if self.lessMissed[i]:
                self.minusRock[self.coOpPlayerMeter] += self.minGain / 5.0 / self.multi[i]
                rockMinusAmount = self.minusRock[0] / 5.0 / self.multi[i]
                self.rock[self.coOpPlayerMeter] -= rockMinusAmount
                if self.plusRock[self.coOpPlayerMeter] > self.pluBase:
                    self.plusRock[self.coOpPlayerMeter] -= self.pluGain / 2.5 / self.multi[i]
            if (self.rock[self.coOpPlayerMeter] / self.rockMax <= 0.667) and ((self.rock[self.coOpPlayerMeter] + rockMinusAmount) / self.rockMax > 0.667):
                self.playersInGreen -= 1

        elif self.coOpRB and self.numOfPlayers > 1:  # RB co-op mode
            if self.notesMissed[i]:
                self.minusRock[i] += self.minGain / self.coOpMulti
                if self.numDeadPlayers > 0:
                    self.minusRock[self.coOpPlayerMeter] += self.minGain / self.coOpMulti
                    rockMinusAmount = self.minusRock[self.coOpPlayerMeter] / self.coOpMulti
                    self.rock[self.coOpPlayerMeter] -= rockMinusAmount / self.numOfPlayers
                self.rock[i] -= self.minusRock[i] / self.coOpMulti
                if self.plusRock[i] > self.pluBase:
                    self.plusRock[i] -= self.pluGain * 2.0 / self.coOpMulti
                if self.plusRock[i] <= self.pluBase:
                    self.plusRock[i] = self.pluBase / self.coOpMulti
            if self.lessMissed[i]:
                self.minusRock[i] += self.minGain / 5.0 / self.coOpMulti
                if self.numDeadPlayers > 0:
                    self.minusRock[self.coOpPlayerMeter] += self.minGain / 5.0 / self.coOpMulti
                    rockMinusAmount = self.minusRock[i] / 5.0 / self.coOpMulti
                    self.rock[self.coOpPlayerMeter] -= rockMinusAmount / (self.numOfPlayers - self.numDeadPlayers)
                self.rock[i] -= self.minusRock[i] / 5.0 / self.coOpMulti
                if self.plusRock[i] > self.pluBase:
                    self.plusRock[i] -= self.pluGain / 2.5 / self.coOpMulti

        else:  # normal mode
            if self.notesMissed[i]:
                self.minusRock[i] += self.minGain / self.multi[i]
                rockMinusAmount = self.minusRock[i] / self.multi[i]
                self.rock[i] -= rockMinusAmount
                if self.plusRock[i] > self.pluBase:
                    self.plusRock[i] -= self.pluGain * 2.0 / self.multi[i]
                if self.plusRock[i] <= self.pluBase:
                    self.plusRock[i] = self.pluBase / self.multi[i]
            if self.lessMissed[i]:
                self.minusRock[i] += self.minGain / 5.0 / self.multi[i]
                rockMinusAmount = self.minusRock[i] / 5.0 / self.multi[i]
                self.rock[i] -= rockMinusAmount
                if self.plusRock[i] > self.pluBase:
                    self.plusRock[i] -= self.pluGain / 2.5 / self.multi[i]
            if (self.rock[i] / self.rockMax <= 0.667) and ((self.rock[i] + rockMinusAmount) / self.rockMax > 0.667):
                self.playersInGreen -= 1

        if self.minusRock[i] <= self.minBase:
            self.minusRock[i] = self.minBase
        if self.plusRock[i] <= self.pluBase:
            self.plusRock[i] = self.pluBase

    def rockmeterIncrease(self, playerNum, vScore=0):
        """ Increases the rockmeter for a player when a note is hit """
        i = playerNum
        if self.instruments[i].isVocal:
            rockPlusAmt = 500 + (500 * (vScore - 2))
            self.rock[i] += rockPlusAmt
            if self.rock[i] >= self.rockMax:
                self.rock[i] = self.rockMax
            if not self.coOpRB:
                if (self.rock[i] / self.rockMax > 0.667) and ((self.rock[i] - rockPlusAmt) / self.rockMax <= 0.667):
                    self.playersInGreen += 1
                    if self.engine.data.cheerSoundFound > 0:  # haven't decided whether or not to cut crowdSound with crowdsEnabled = 0, but would have to do it at solos too...
                        self.engine.data.crowdSound.play()
            return
        if self.instruments[i].isDrum:
            self.drumStart = True
        if not self.failingEnabled or self.practiceMode:
            return
        if not self.notesHit[i]:
            return
        if self.battle and self.numOfPlayers > 1:  # battle mode
            if self.notesHit[i]:
                if self.rock[i] < self.rockMax:
                    self.plusRock[i] += self.pluGain * self.multi[i]
                    if self.plusRock[i] > self.battleMax:
                        self.plusRock[i] = self.battleMax
                    self.rock[i] += self.plusRock[i] * self.multi[i]
                    self.rock[self.battleTarget[i]] -= self.plusRock[i] * self.multi[i]
                if self.rock[self.battleTarget[i]] < 0:
                    self.rock[self.battleTarget[i]] = 0
                if self.rock[i] >= self.rockMax:
                    self.rock[i] = self.rockMax
                if self.minusRock[i] > self.minBase:
                    self.minusRock[i] -= self.minGain / 2.0 * self.multi[i]

        # TODO maintain separate rock status for each player
        elif self.coOp and self.numOfPlayers > 1:
            if self.rock[self.coOpPlayerMeter] < self.rockMax:
                self.plusRock[self.coOpPlayerMeter] += self.pluGain * self.multi[i]
                self.rock[self.coOpPlayerMeter] += self.plusRock[self.coOpPlayerMeter] * self.multi[i]
            if self.rock[self.coOpPlayerMeter] >= self.rockMax:
                self.rock[self.coOpPlayerMeter] = self.rockMax
            if self.minusRock[self.coOpPlayerMeter] > self.minBase:
                self.minusRock[self.coOpPlayerMeter] -= self.minGain / 2.0 * self.multi[i]
            if (self.rock[self.coOpPlayerMeter] / self.rockMax > 0.667) and ((self.rock[self.coOpPlayerMeter] - (self.plusRock[self.coOpPlayerMeter] * self.multi[i])) / self.rockMax <= 0.667):
                self.playersInGreen += 1
                if self.engine.data.cheerSoundFound > 0:  # haven't decided whether or not to cut crowdSound with crowdsEnabled = 0, but would have to do it at solos too...
                    self.engine.data.crowdSound.play()

        elif self.coOpRB and self.numOfPlayers > 1:
            if self.rock[i] < self.rockMax:
                self.plusRock[i] += self.pluGain * self.coOpMulti
                self.rock[i] += (self.plusRock[i] * self.coOpMulti)
            if self.rock[i] >= self.rockMax:
                self.rock[i] = self.rockMax
            if self.minusRock[i] > self.minBase:
                self.minusRock[i] -= self.minGain / 2.0 * self.coOpMulti

        else:  # normal mode
            if self.rock[i] < self.rockMax:
                self.plusRock[i] += self.pluGain * self.multi[i]
                self.rock[i] += self.plusRock[i] * self.multi[i]
            if self.rock[i] >= self.rockMax:
                self.rock[i] = self.rockMax
            if self.minusRock[i] > self.minBase:
                self.minusRock[i] -= self.minGain / 2.0 * self.multi[i]
            if (self.rock[i] / self.rockMax > 0.667) and ((self.rock[i] - (self.plusRock[i] * self.multi[i])) / self.rockMax <= 0.667):
                self.playersInGreen += 1
                if self.engine.data.cheerSoundFound > 0:  # haven't decided whether or not to cut crowdSound with crowdsEnabled = 0, but would have to do it at solos too...
                    self.engine.data.crowdSound.play()

        if self.minusRock[i] <= self.minBase:
            self.minusRock[i] = self.minBase
        if self.plusRock[i] <= self.pluBase:
            self.plusRock[i] = self.pluBase

    def rockmeterDrain(self, playerNum):
        self.rock[playerNum] -= 15.0
        self.minusRock[playerNum] += self.minGain / 10 / self.coOpMulti

    def run(self, ticks):
        super(GuitarScene, self).run(ticks)

        if self.song and self.song.readyToGo and not self.pause and not self.failed:
            sngPos = self.song.getPosition()
            # calculate song position during the song countdown
            if self.songTime <= -self.audioDelay and sngPos == -self.song.delay:
                self.songTime = sngPos - (self.countdown * self.song.period)
            if not self.countdown and not self.resumeCountdown and not self.pause:
                # increment song position
                self.songTime += ticks
                sngDiff = abs(sngPos - self.songTime)
                if sngDiff > 100:  # Correct for potential large lag spikes
                    self.songTime = sngPos
                elif sngDiff < 1.0:  # normal operation
                    pass
                elif self.songTime > sngPos:  # to fast
                    self.songTime -= 0.1
                elif self.songTime < sngPos:  # to slow
                    self.songTime += 0.1

                self.song.update(ticks)

            if self.vbpmLogicType == 1:
                self.handleTempo(self.song, self.songTime)  # new global tempo / BPM handling logic

            # new failing detection logic
            if self.failingEnabled:
                if self.numOfPlayers > 1 and self.coOpType:
                    if self.rock[self.coOpPlayerMeter] <= 0:
                        self.failed = True
                    else:
                        if self.coOpRB:
                            for i, player in enumerate(self.players):
                                if self.rock[i] <= 0 and not self.coOpFailDone[i]:
                                    self.instruments[i].coOpFailed = True
                                    self.instruments[i].starPower = 0.0
                                    self.engine.data.coOpFailSound.play()
                                    self.deadPlayerList.append(i)
                                    self.numDeadPlayers += 1
                                    self.timesFailed[i] += 1
                                    self.crowdsCheering = False
                                    self.song.setInstrumentVolume(0.0, self.players[i].part)
                                    if self.whammyEffect == 1:  # pitchbend
                                        self.song.resetInstrumentPitch(self.players[i].part)
                                    self.coOpFailDone[i] = True
                else:
                    somebodyStillAlive = False
                    for i, player in enumerate(self.players):
                        if self.rock[i] > 0:
                            somebodyStillAlive = True
                    if not somebodyStillAlive:  # only if everybody has failed
                        self.failed = True

            if self.songTime > self.lastDrumNoteTime:  # disable drum scoring so that the drummer can get down with his bad self at the end of the song without penalty.
                self.drumScoringEnabled = False  # ...is that what drummers do?

            for i, instrument in enumerate(self.instruments):
                if instrument.isVocal:
                    instrument.requiredNote = instrument.getRequiredNote(self.songTime, self.song)
                    instrument.run(ticks, self.songTime)
                    scoreBack = instrument.getScoreChange()
                    if scoreBack is not None:
                        points, scoreThresh, taps = scoreBack
                        self.scoring[i].score += points * instrument.scoreMultiplier * self.multi[i]
                        self.scoring[i].percNotesHit += taps
                        scoreThresh = 5 - scoreThresh
                        if scoreThresh > 3:
                            self.rockmeterIncrease(i, scoreThresh)
                            self.scoring[i].notesHit += 1
                            self.scoring[i].streak += 1
                        elif scoreThresh == 3:
                            self.scoring[i].streak = 0
                        elif scoreThresh < 3:
                            self.rockmeterDecrease(i, scoreThresh)
                            self.scoring[i].streak = 0
                        self.scoring[i].updateAvMult()
                        self.scoring[i].getStarScores()
                    if instrument.starPowerGained:
                        if instrument.starPower >= 50 and not instrument.starPowerActive:
                            self.engine.data.starReadySound.play()
                        else:
                            self.engine.data.starSound.play()
                        if self.phrases > 1:
                            if instrument.starPower >= 50 and not instrument.starPowerActive:
                                self.newScalingText(i, self.tsStarPowerReady)
                        instrument.starPowerGained = False
                    if instrument.starPowerActivate:
                        self.activateSP(i)
                        instrument.starPowerActivate = False
                    continue
                self.stage.run(self.songTime, instrument.currentPeriod)
                playerNum = i

                instrument.camAngle = -degrees(atan(abs(self.camera.origin[2] - self.camera.target[2]) / abs(self.camera.origin[1] - self.camera.target[1])))

                if instrument.isDrum and instrument.freestyleSP:  # this drum fill starpower activation logic should always be checked.
                    self.activateSP(i)
                    instrument.freestyleSP = False

                # check for any unplayed notes and for an unbroken streak since the BRE, then award bonus scores
                # does not work for co-op.
                if self.coOpType:
                    scoreCard = self.coOpScoreCard
                    if scoreCard.freestyleWasJustActive and not scoreCard.endingAwarded:
                        if scoreCard.lastNoteTime < self.songTime and not scoreCard.endingStreakBroken:
                            log.debug("Big Rock Ending bonus awarded for co-op players! %d points." % scoreCard.endingScore)
                            if scoreCard.endingScore > 0:
                                scoreCard.addEndingScore()
                                self.engine.data.starActivateSound.play()
                            scoreCard.endingAwarded = True
                else:
                    scoreCard = self.scoring[playerNum]
                    if scoreCard.freestyleWasJustActive and not scoreCard.endingAwarded:
                        if scoreCard.lastNoteEvent and not scoreCard.endingStreakBroken:
                            if scoreCard.lastNoteEvent.played or scoreCard.lastNoteEvent.hopod:
                                log.debug("Big Rock Ending bonus awarded for player %d: %d points" % (playerNum, scoreCard.endingScore))
                                if scoreCard.endingScore > 0:
                                    scoreCard.addEndingScore()
                                    self.engine.data.starActivateSound.play()
                                scoreCard.endingAwarded = True

                if instrument.starPowerGained:
                    if self.unisonActive and self.inUnison[i]:
                        self.unisonEarn[i] = True
                    # auto drum starpower activation option:
                    if instrument.isDrum and self.autoDrumStarpowerActivate == 0 and self.numDrumFills < 2:
                        self.activateSP(playerNum)
                    if instrument.starPower >= 50 and not instrument.starPowerActive:
                        self.engine.data.starReadySound.play()
                    else:
                        self.engine.data.starSound.play()

                    if self.phrases > 1:
                        if instrument.starPower >= 50 and not instrument.starPowerActive:
                            self.newScalingText(playerNum, self.tsStarPowerReady)

                    self.hopFretboard(i, 0.04)
                    instrument.starPowerGained = False

                if not instrument.run(ticks, self.songTime, self.controls):
                    # done playing the current notes
                    self.endPick(i)

                if instrument.drumFillsActive:
                    if self.muteDrumFill > 0 and not self.jurg[i]:
                        self.song.setInstrumentVolume(0.0, self.players[i].part)

                # ensure this missed notes check doesn't fail you during a freestyle section
                if instrument.freestyleActive or instrument.drumFillsActive:
                    missedNotes = instrument.getMissedNotes(self.song, self.songTime + instrument.lateMargin * 2, catchup=True)  # get all notes in the freestyle section.
                    for tym, theNote in missedNotes:  # also want to mark these notes as Played so they don't count against the note total!
                        theNote.skipped = True
                        if instrument.isDrum:
                            if self.coOpType:
                                self.coOpScoreCard.totalStreakNotes -= 1
                            self.scoring[playerNum].totalStreakNotes -= 1

                else:
                    missedNotes = instrument.getMissedNotes(self.song, self.songTime)
                    if instrument.paused:
                        missedNotes = []
                    if missedNotes:
                        if instrument.isDrum:
                            self.drumStart = True
                        self.lessMissed[i] = True
                        for tym, theNote in missedNotes:
                            self.scoring[playerNum].notesMissed += 1
                            if self.coOpType:
                                self.coOpScoreCard.notesMissed += 1
                            if theNote.star or theNote.finalStar:
                                # Starpower misses log
                                log.debug("SP Miss: run(), note: %d, gameTime: %s" % (theNote.number, self.timeLeft))
                                self.starNotesMissed[i] = True
                                if self.unisonActive:
                                    self.inUnison[i] = False

                    if (self.scoring[i].streak != 0 or not self.processedFirstNoteYet) and not instrument.playedNotes and len(missedNotes) > 0:
                        self.screwUp(playerNum)

            # Capo's starpower claps on a user setting
            if (self.starClaps or self.beatClaps) and len(self.beatTime) > 0:
                # Play a sound on each beat on starpower
                clap = False
                if self.players[0].practiceMode and self.beatClaps:
                    clap = True
                else:
                    for i, player in enumerate(self.players):
                        if self.instruments[i].starPowerActive:
                            clap = True
                            break
                if self.songTime >= (self.beatTime[0] - 100):
                    self.beatTime.pop(0)
                    if clap:
                        if not self.firstClap:
                            self.engine.data.clapSound.play()
                        else:
                            self.firstClap = False
                    else:
                        self.firstClap = True

            for playerNum in range(self.numOfPlayers):
                self.handlePhrases(playerNum, self.scoring[playerNum].streak)  # streak #1 for player #1...
                self.handleAnalogSP(playerNum, ticks)
                self.handleWhammy(playerNum)
                if self.players[playerNum].controlType == 4:
                    self.handleAnalogSlider(playerNum)
                self.updateGuitarSolo(playerNum)
            if self.coOpType:
                self.handlePhrases(self.coOpPhrase, self.coOpScoreCard.streak)
            self.handleJurgen(self.songTime)

            # stage rotation
            # logic to prevent advancing rotation frames if you have screwed up, until you resume a streak
            if (self.currentlyAnimating and self.missPausesAnim == 1) or self.missPausesAnim == 0:
                self.stage.rotate()
            self.starPowersActive = 0
            self.coOpStarPower = 0
            # new logic to update the starpower pre-multiplier
            # broken up to support RB Co-op properly.
            for i in range(self.numOfPlayers):
                if self.instruments[i].starPowerActive:
                    self.multi[i] = 2
                    self.starPowersActive += 1
                else:
                    self.multi[i] = 1
                sp = self.instruments[i].starPower
            if self.coOpRB:
                if self.unisonIndex < len(self.unisonConfirm) and not self.unisonActive:  # unison bonuses
                    while self.unisonConfirm[self.unisonIndex][0] < self.songTime:
                        self.unisonIndex += 1
                        if len(self.unisonConfirm) == self.unisonIndex:
                            break
                    if len(self.unisonConfirm) > self.unisonIndex:
                        if self.unisonConfirm[self.unisonIndex][0] - self.songTime < self.song.period * 2:
                            self.unisonActive = True
                            self.firstUnison = True
                            self.unisonNum = len(self.unisonPlayers[self.unisonIndex])
                if self.starPowersActive > 0:
                    self.coOpMulti = 2 * self.starPowersActive
                else:
                    self.coOpMulti = 1
                # rewritten rockmeter / starpower miss logic, and Faaa's drum sounds:
                # the old logic was ridiculously complicated
                # For each existing player
            if self.coOpRB:
                oldCoOpRock = self.rock[self.coOpPlayerMeter]
                coOpRock = 0.0
            for i in range(self.numOfPlayers):
                if (self.coOpRB and not instrument.coOpFailed) or not self.coOpRB:
                    if self.notesMissed[i] or self.lessMissed[i]:  # detects missed note or overstrum
                        if self.instruments[i].isDrum:
                            if self.drumMisses == 0:  # mode: always
                                self.rockmeterDecrease(i)
                            elif self.drumMisses == 1 and self.countdown < 1:  # mode: song start
                                self.rockmeterDecrease(i)
                            elif self.drumMisses == 2 and self.drumStart:  # mode: song start
                                self.rockmeterDecrease(i)
                        else:  # not drums
                            self.rockmeterDecrease(i)
                    if self.notesHit[i]:
                        self.rockmeterIncrease(i)
                    if self.coOpRB:
                        coOpRock += self.rock[i]
                else:
                    if not self.instruments[i].coOpRestart:
                        self.rockmeterDrain(self.coOpPlayerMeter)
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

                # battle failing
                if self.battle and self.numOfPlayers > 1:
                    if self.rock[i] <= 0:
                        self.newScalingText(i, self.tsYouFailedBattle)
                        instrument.actions = [0, 0, 0]
            if self.coOpRB:  # RB co-op meter is just an average until someone dies.
                if self.numDeadPlayers == 0:
                    self.rock[self.coOpPlayerMeter] = coOpRock / self.numOfPlayers
                    if (self.rock[self.coOpPlayerMeter] / self.rockMax > 0.667) and (oldCoOpRock / self.rockMax <= 0.667):
                        self.playersInGreen = 1
                        if self.engine.data.cheerSoundFound > 0:  # haven't decided whether or not to cut crowdSound with crowdsEnabled = 0, but would have to do it at solos too...
                            self.engine.data.crowdSound.play()
                if (self.rock[self.coOpPlayerMeter] / self.rockMax <= 0.667) and (oldCoOpRock / self.rockMax > 0.667):
                    self.playersInGreen = 0

            if self.unisonActive:  # unison bonuses
                if self.firstUnison:
                    self.firstUnison = False
                    self.firstUnisonDone = True
                if self.songTime - self.unisonConfirm[self.unisonIndex][1] > 0 and self.firstUnisonDone:
                    for i in range(len(self.inUnison)):
                        if self.inUnison[i] != self.haveUnison[i]:
                            break
                    else:
                        if self.engine.data.cheerSoundFound > 0:
                            self.engine.data.crowdSound.play()
                        for i, inst in enumerate(self.instruments):
                            if self.inUnison[i]:
                                inst.starPower += 25
                                if inst.starPower > 100:
                                    inst.starPower = 100
                    self.firstUnisonDone = False
                if self.songTime - self.unisonConfirm[self.unisonIndex][1] > self.song.period * 2:
                    self.unisonIndex += 1
                    self.unisonActive = False
                    self.unisonEarn = [False for i in self.players]
                    self.haveUnison = [False for i in self.players]
                    self.inUnison = [False for i in self.players]

            # Song/Crowd logic
            if self.numDeadPlayers == 0:
                if self.crowdsEnabled == 3 and not self.crowdsCheering and not self.countdown:  # prevents cheer-cut-cheer
                    self.crowdsCheering = True
                elif self.crowdsEnabled == 0 and self.crowdsCheering:  # setting change
                    self.crowdsCheering = False
                elif self.crowdsEnabled == 1:
                    if self.starPowersActive > 0:
                        if not self.crowdsCheering:
                            self.crowdsCheering = True
                    else:
                        if self.crowdsCheering:
                            self.crowdsCheering = False
                elif self.crowdsEnabled == 2:
                    if self.starPowersActive > 0 or self.playersInGreen > 0:
                        if not self.crowdsCheering:
                            self.crowdsCheering = True
                    else:
                        if self.crowdsCheering:
                            self.crowdsCheering = False

            # Crowd fade-in/out
            if self.crowdsCheering and self.crowdFaderVolume < self.crowdVolume:
                self.crowdFaderVolume += self.crowdCheerFadeInChunk
                if self.crowdFaderVolume > self.crowdVolume:
                    self.crowdFaderVolume = self.crowdVolume
                self.song.setCrowdVolume(self.crowdFaderVolume)

            if not self.crowdsCheering and self.crowdFaderVolume > 0.0:
                self.crowdFaderVolume -= self.crowdCheerFadeOutChunk
                if self.crowdFaderVolume < 0.0:
                    self.crowdFaderVolume = 0.0
                self.song.setCrowdVolume(self.crowdFaderVolume)

            if self.countdown > 0 and self.countdownOK:  # won't start song playing if you failed or pause
                self.countdown = max(self.countdown - ticks / self.song.period, 0)
                self.countdownSeconds = self.countdown / self.songBPS + 1

                if not self.countdown:  # when countdown reaches zero, will only be executed once
                    # should we collect garbage when we start?
                    self.engine.collectGarbage()
                    self.getHandicap()
                    self.song.setAllTrackVolumes(1)
                    self.song.setCrowdVolume(0.0)
                    self.crowdsCheering = False  # catches crowdsEnabled != 3, pause before countdown, set to 3
                    self.starPowersActive = 0
                    self.playersInGreen = 0
                    for instrument in self.instruments:
                        if instrument.isVocal:
                            instrument.mic.start()
                    if self.players[0].practiceMode and self.engine.audioSpeedFactor == 1:
                        self.players[0].startPos -= self.song.period * 4
                        if self.players[0].startPos < 0.0:
                            self.players[0].startPos = 0.0
                        self.song.play(start=self.players[0].startPos)
                    else:
                        self.song.play()

            if self.resumeCountdown > 0:  # unpause delay
                self.resumeCountdown = max(self.resumeCountdown - ticks / self.song.period, 0)
                self.resumeCountdownSeconds = self.resumeCountdown / self.songBPS + 1

                if not self.resumeCountdown:
                    self.song.unpause()
                    self.pause = False
                    missedNotes = []
                    for instrument in self.instruments:
                        instrument.paused = False
                        if instrument.isVocal:
                            instrument.startMic()

            if self.timeLeft == "0:01" and not self.mutedLastSecondYet and self.muteLastSecond == 1:
                self.song.setAllTrackVolumes(0.0)
                self.mutedLastSecondYet = True

            # this detects the end of the song and displays "you rock"
            if self.countdown <= 0 and not self.song.isPlaying() and not self.done:
                # must render fail message in render function, set and check flag here
                self.youRock = True

            # This ends the song after 100 ticks of displaying "you rock" - if the use hasn't paused the game.
            if self.rockFinished and not self.pause:
                self.goToResults()
                return

            if self.midiLyricMode == 1 and self.numMidiLyricLines > 0 and (not self.noMoreMidiLineLyrics) and not self.playingVocals:  # line-by-line lyrics mode

                if self.songTime >= (self.nextMidiLyricStartTime - self.lineByLineStartSlopMs):
                    self.currentSimpleMidiLyricLine = self.nextMidiLyricLine

                    if self.numMidiLyricLines > self.midiLyricLineIndex + 1:
                        self.midiLyricLineIndex += 1
                        self.nextMidiLyricStartTime, self.nextMidiLyricLine = self.midiLyricLines[self.midiLyricLineIndex]
                    else:
                        self.noMoreMidiLineLyrics = True

            elif self.midiLyricMode == 2 and self.numMidiLyricLines > 0 and (not self.noMoreMidiLineLyrics) and not self.playingVocals:  # handle 2-line lyric mode with current-word highlighting advancement
                # first, prepare / handle the active / top line (which will have highlighted words / syllables)
                if self.songTime >= self.nextLyricWordTime:  # time to switch to this word
                    if self.nextLyricIsOnNewLine:
                        self.activeMidiLyricLineIndex += 1
                        self.activeMidiLyricWordSubIndex = 0
                        self.nextLyricIsOnNewLine = False
                        self.activeMidiLyricLine_GreyWords = ""
                        self.activeMidiLyricLine_GreenWords = "%s " % self.nextLyricEvent.text

                        self.numWordsInCurrentMidiLyricLine = 0
                        for nextLyricTime, nextLyricEvent in self.midiLyricLineEvents[self.activeMidiLyricLineIndex]:  # populate the first active line
                            self.numWordsInCurrentMidiLyricLine += 1

                        if self.numWordsInCurrentMidiLyricLine > self.activeMidiLyricWordSubIndex + 1:  # there is another word in this line
                            self.activeMidiLyricWordSubIndex += 1
                            self.nextLyricWordTime, self.nextLyricEvent = self.midiLyricLineEvents[self.activeMidiLyricLineIndex][self.activeMidiLyricWordSubIndex]
                            self.activeMidiLyricLine_WhiteWords = ""
                            for nextLyricTime, nextLyricEvent in self.midiLyricLineEvents[self.activeMidiLyricLineIndex]:
                                if nextLyricTime > self.songTime:
                                    self.activeMidiLyricLine_WhiteWords = "%s %s" % (self.activeMidiLyricLine_WhiteWords, nextLyricEvent.text)

                    else:  # next lyric is on the same line
                        if self.activeMidiLyricWordSubIndex > 0:  # set previous word as grey
                            lastLyricTime, lastLyricEvent = self.midiLyricLineEvents[self.activeMidiLyricLineIndex][self.activeMidiLyricWordSubIndex-1]
                            self.activeMidiLyricLine_GreyWords = "%s%s " % (self.activeMidiLyricLine_GreyWords, lastLyricEvent.text)
                        self.activeMidiLyricLine_GreenWords = "%s " % self.nextLyricEvent.text
                        if self.numWordsInCurrentMidiLyricLine > self.activeMidiLyricWordSubIndex + 1:  # there is another word in this line
                            self.activeMidiLyricWordSubIndex += 1
                            self.nextLyricWordTime, self.nextLyricEvent = self.midiLyricLineEvents[self.activeMidiLyricLineIndex][self.activeMidiLyricWordSubIndex]
                            self.activeMidiLyricLine_WhiteWords = ""
                            for nextLyricTime, nextLyricEvent in self.midiLyricLineEvents[self.activeMidiLyricLineIndex]:
                                if nextLyricTime > self.songTime:
                                    self.activeMidiLyricLine_WhiteWords = "%s %s" % (self.activeMidiLyricLine_WhiteWords, nextLyricEvent.text)

                        else:  # no more words in this line
                            if self.numMidiLyricLines > self.activeMidiLyricLineIndex + 1:  # there is another line
                                self.nextLyricIsOnNewLine = True
                                self.nextLyricWordTime, self.nextLyricEvent = self.midiLyricLineEvents[self.activeMidiLyricLineIndex+1][0]
                                self.activeMidiLyricLine_WhiteWords = ""

                            else:  # no more lines
                                self.noMoreMidiLineLyrics = True
                                self.activeMidiLyricLine_WhiteWords = ""
                                self.currentSimpleMidiLyricLine = ""

                    # then, prepare / handle the next / bottom line (which will just be a simple line with all white text)
                    if self.numMidiLyricLines > self.activeMidiLyricLineIndex + 1:
                        tempTime, self.currentSimpleMidiLyricLine = self.midiLyricLines[self.activeMidiLyricLineIndex+1]
                    else:
                        self.currentSimpleMidiLyricLine = ""

    def endPick(self, num):
        score = self.getExtraScoreForCurrentlyPlayedNotes(num)
        if not self.instruments[num].endPick(self.song.getPosition()):
            if self.muteSustainReleases > 0:
                self.song.setInstrumentVolume(0.0, self.players[num].part)
        if score != 0:
            scoreTemp = score * self.multi[num]
            if self.coOpType:
                self.coOpScoreCard.addScore(scoreTemp)
            else:
                self.scoring[num].addScore(scoreTemp)

    def render3D(self):
        if self.stage.mode == 3:
            if self.countdown <= 0:
                if self.pause or self.failed:
                    self.stage.vidPlayer.pause()
                else:
                    self.stage.vidPlayer.play()
            else:
                self.stage.vidPlayer.pause()

        self.stage.render(self.visibility)

    def renderVocals(self):
        for i, vocalist in enumerate(self.instruments):
            if vocalist.isVocal:
                vocalist.render(self.visibility, self.song, self.songTime, self.numOfPlayers)

    def renderGuitar(self):
        for i, guitar in enumerate(self.instruments):
            if guitar.isVocal:
                continue
            self.engine.view.setViewport(self.numberOfGuitars, self.players[i].guitarNum)
            if self.theme not in (0, 1, 2) or (not self.pause and not self.failed):
                gl.glPushMatrix()
                if guitar.fretboardHop > 0.0:
                    gl.glTranslatef(0.0, guitar.fretboardHop, 0.0)  # fretboard hop
                    guitar.fretboardHop -= 0.005
                    if guitar.fretboardHop < 0.0:
                        guitar.fretboardHop = 0.0
                self.neckrender[i].render(self.visibility, self.song, self.songTime)
                guitar.render(self.visibility, self.song, self.songTime, self.controls, self.killswitchEngaged[i])
                gl.glPopMatrix()
            if self.coOp:
                guitar.rockLevel = self.rock[self.coOpPlayerMeter] / self.rockMax
                if self.rock[self.coOpPlayerMeter] < self.rockMax / 3.0 and self.failingEnabled:
                    self.neckrender[i].isFailing = True
                else:
                    self.neckrender[i].isFailing = False
            elif self.coOpRB:
                guitar.rockLevel = self.rock[i] / self.rockMax
                if self.rock[i] < self.rockMax / 3.0 and self.failingEnabled:
                    self.neckrender[i].isFailing = True
                elif self.numDeadPlayers > 0 and self.rock[self.coOpPlayerMeter] < self.rockMax / 6.0 and self.failingEnabled:
                    self.neckrender[i].isFailing = True
                else:
                    self.neckrender[i].isFailing = False
            else:
                guitar.rockLevel = self.rock[i] / self.rockMax
                if self.rock[i] < self.rockMax / 3.0 and self.failingEnabled:
                    self.neckrender[i].isFailing = True
                else:
                    self.neckrender[i].isFailing = False

        self.engine.view.setViewport(1, 0)

    def screwUp(self, num, sounds=True):
        if self.coOpType:
            scoreCard = self.coOpScoreCard
        else:
            scoreCard = self.scoring[num]

        self.song.setInstrumentVolume(0.0, self.players[num].part)

        if self.whammyEffect == 1:  # pitchbend
            self.song.resetInstrumentPitch(self.players[num].part)
        scoreCard.streak = 0

        if self.coOpType:
            self.scoring[num].streak = 0
            self.scoring[num].endingStreakBroken = True

        self.guitarSoloBroken[num] = True
        scoreCard.endingStreakBroken = True
        self.instruments[num].setMultiplier(1)
        self.stage.triggerMiss(self.songTime)

        self.notesMissed[num] = True

        isFirst = True
        noteList = self.instruments[num].matchingNotes
        for tym, noat in noteList:
            if (noat.star or noat.finalStar) and isFirst:
                self.starNotesMissed[num] = True
                if self.unisonActive:
                    self.inUnison[num] = False
            isFirst = False

        self.dispAccuracy[num] = False

        if self.screwUpVolume > 0.0 and sounds:
            if self.instruments[num].isBassGuitar:
                self.engine.data.screwUpSoundBass.play()
            elif self.instruments[num].isDrum:
                if self.drumMisses > 0:  # Faaa Drum sound
                    self.instruments[num].playDrumSounds(self.controls)
                else:
                    self.engine.data.screwUpSoundDrums.play()  # plays random drum sounds
            else:  # guitar
                self.engine.data.screwUpSound.play()

    def noteHit(self, num):
        if self.coOpType:
            scoreCard = self.coOpScoreCard
        else:
            scoreCard = self.scoring[num]

        if self.instruments[num].isDrum:
            self.drumStart = True

        self.processedFirstNoteYet = True

        self.song.setInstrumentVolume(1.0, self.players[num].part)
        self.currentlyAnimating = True

        isFirst = True
        noteList = self.instruments[num].playedNotes
        for tym, noat in noteList:
            if noat.star and isFirst:
                self.instruments[num].isStarPhrase = True
            isFirst = False

        scoreCard.streak += 1
        self.notesHit[num] = True
        scoreCard.notesHit += 1

        # tell ScoreCard to update its totalStreak counter if we've just passed 100% for some reason
        if scoreCard.notesHit > scoreCard.totalStreakNotes:
            scoreCard.totalStreakNotes = scoreCard.notesHit

        tempScoreValue = len(self.instruments[num].playedNotes) * self.baseScore * self.multi[num]
        if self.coOpType:
            self.scoring[num].streak += 1  # needed in co-op GH for RF HO/PO
            self.scoring[num].notesHit += 1

            # tell ScoreCard to update its totalStreak counter if we've just passed 100% for some reason
            if self.scoring[num].notesHit > self.scoring[num].totalStreakNotes:
                self.scoring[num].totalStreakNotes = self.scoring[num].notesHit

            scoreCard.score += (tempScoreValue * self.scoring[num].getScoreMultiplier())
        else:
            self.scoring[num].addScore(tempScoreValue)

        scoreCard.updateAvMult()
        star = scoreCard.stars
        a = scoreCard.getStarScores()
        if a > star and ((self.inGameStars == 1 and self.theme == 2) or self.inGameStars == 2):
            self.engine.data.starDingSound.play()

        self.stage.triggerPick(self.songTime, [n[1].number for n in self.instruments[num].playedNotes])
        if self.scoring[num].streak % 10 == 0:
            self.lastMultTime[num] = self.songTime
            self.instruments[num].setMultiplier(self.scoring[num].getScoreMultiplier())

        if self.showAccuracy:
            self.accuracy[num] = self.instruments[num].playedNotes[0][0] - self.songTime
            self.dispAccuracy[num] = True

    def doPick(self, num):
        if not self.song:
            return

        if self.instruments[num].playedNotes:
            self.endPick(num)

        self.lastPickPos[num] = self.songTime

        # self.killswitchEngaged[num] = False  # always reset killswitch status when picking / tapping

        # disable failing if BRE is active
        if self.instruments[num].startPick(self.song, self.songTime, self.controls):
            self.noteHit(num)
        else:
            if self.instruments[num].isDrum and self.instruments[num].drumFillWasJustActive:
                self.instruments[num].freestylePick(self.song, self.songTime, self.controls)  # to allow late drum fill SP activation
                self.instruments[num].drumFillWasJustActive = False
            else:
                self.screwUp(num)

        # bass drum sound play
        if self.instruments[num].isDrum and self.bassKickSoundEnabled:
            self.instruments[num].playDrumSounds(self.controls, playBassDrumOnly=True)

    def doPick3GH2(self, num, hopo=False, pullOff=False):  # so DoPick knows when a pull-off was performed
        if not self.song:
            return

        missedNotes = self.instruments[num].getMissedNotes(self.song, self.songTime, catchup=True)
        if len(missedNotes) > 0:
            self.processedFirstNoteYet = True

            self.screwUp(num, sounds=False)

            if hopo:
                return

        # hopo fudge
        hopoFudge = abs(abs(self.instruments[num].hopoActive) - self.songTime)

        #Perhaps, if I were to just treat all tappable = 3's as problem notes, and just accept a potential overstrum, that would cover all the bases...
        # maybe, instead of checking against a known list of chord notes that might be associated, just track whether or not
        # the original problem note (tappable = 3) is still held.  If it is still held, whether or not it matches the notes, it means
        #  it can still be involved in the problematic pattern - so continue to monitor for an acceptable overstrum.

        #On areas where it's just a tappable = 3 note with no other notes in the hitwindow, it will be marked as a problem and then
        # if strummed, that would be considered the acceptable overstrum and it would behave the same.  MUCH simpler logic!

        activeKeyList = []
        # the following checks should be performed every time so GH2 Strict pull-offs can be detected properly.
        LastHopoFretStillHeld = False
        HigherFretsHeld = False
        problemNoteStillHeld = False

        for n, k in enumerate(self.keysList[num]):
            if self.controls.getState(k):
                activeKeyList.append(k)
                if self.instruments[num].hopoLast == n or self.instruments[num].hopoLast == n - 5:
                    LastHopoFretStillHeld = True
                elif (n > self.instruments[num].hopoLast and n < 5) or (n - 5 > self.instruments[num].hopoLast and n > 4):
                    HigherFretsHeld = True
                if self.instruments[num].hopoProblemNoteNum == n or self.instruments[num].hopoProblemNoteNum == n - 5:
                    problemNoteStillHeld = True

        if not hopo and self.instruments[num].wasLastNoteHopod and not self.instruments[num].LastStrumWasChord and not self.instruments[num].sameNoteHopoString:
            if LastHopoFretStillHeld and not HigherFretsHeld:
                if self.instruments[num].wasLastNoteHopod and hopoFudge >= 0 and hopoFudge < self.instruments[num].lateMargin:
                    if self.instruments[num].hopoActive < 0:
                        self.instruments[num].wasLastNoteHopod = False
                        return
                    elif self.instruments[num].hopoActive > 0:  # make sure it's hopoActive!
                        self.instruments[num].wasLastNoteHopod = False
                        return

        # here, just check to see if we can release the expectation for an acceptable overstrum:
        if self.instruments[num].sameNoteHopoString and not problemNoteStillHeld:
            self.instruments[num].sameNoteHopoString = False
            self.instruments[num].hopoProblemNoteNum = -1

        self.killswitchEngaged[num] = False  # always reset killswitch status when picking / tapping
        if self.instruments[num].startPick3(self.song, self.songTime, self.controls, hopo):
            self.noteHit(num)
        else:
            ApplyPenalty = True

            if self.hopoDebugDisp == 1:
                sameNoteHopoFlagWas = self.instruments[num].sameNoteHopoString  # need to store this for debug info
                lastStrumWasChordWas = self.instruments[num].LastStrumWasChord  # for debug info

            if pullOff:  # always ignore bad pull-offs
                ApplyPenalty = False

            if hopo:
                ApplyPenalty = False
                if not (self.instruments[num].LastStrumWasChord or (self.instruments[num].wasLastNoteHopod and LastHopoFretStillHeld)):
                    self.instruments[num].hopoActive = 0
                    self.instruments[num].wasLastNoteHopod = False
                    self.instruments[num].LastStrumWasChord = False
                    self.instruments[num].sameNoteHopoString = False
                    self.instruments[num].hopoProblemNoteNum = -1
                    self.instruments[num].hopoLast = -1

            if self.instruments[num].sameNoteHopoString:
                if LastHopoFretStillHeld:
                    ApplyPenalty = False
                    self.instruments[num].playedNotes = self.instruments[num].lastPlayedNotes  # restore played notes status
                    self.instruments[num].sameNoteHopoString = False
                    self.instruments[num].hopoProblemNoteNum = -1
                elif HigherFretsHeld:
                    self.instruments[num].sameNoteHopoString = False
                    self.instruments[num].hopoProblemNoteNum = -1

            if ApplyPenalty:
                self.screwUp(num)

        # bass drum sound play
        if self.instruments[num].isDrum and self.bassKickSoundEnabled:
            self.instruments[num].playDrumSounds(self.controls, playBassDrumOnly=True)

    def activateSP(self, num):
        guitar = self.instruments[num]
        if guitar.starPower >= 50:
            if self.coOpRB:
                while len(self.deadPlayerList) > 0:
                    i = self.deadPlayerList.pop(0)  # keeps order intact (with >2 players)
                    if self.instruments[i].coOpFailed and self.timesFailed[i] < 3:
                        self.instruments[i].coOpRescue(self.songTime)
                        self.rock[i] = self.rockMax * 0.667
                        guitar.starPower -= 50
                        self.engine.data.rescueSound.play()
                        self.coOpFailDone[i] = False
                        self.numDeadPlayers -= 1
                        if not guitar.isVocal:
                            self.hopFretboard(num, 0.07)
                            guitar.neck.overdriveFlashCount = 0  # this triggers the oFlash strings & timer
                            guitar.neck.ocount = 0  # this triggers the oFlash strings & timer
                        break
                else:
                    if not guitar.starPowerActive:
                        self.engine.data.starActivateSound.play()
                        guitar.starPowerActive = True
                        if not guitar.isVocal:
                            self.hopFretboard(num, 0.07)
                            guitar.neck.overdriveFlashCount = 0  # this triggers the oFlash strings & timer
                            guitar.neck.ocount = 0  # this triggers the oFlash strings & timer
            else:
                if not guitar.starPowerActive:
                    self.engine.data.starActivateSound.play()
                    guitar.starPowerActive = True
                    if not guitar.isVocal:
                        self.hopFretboard(num, 0.07)
                        guitar.neck.overdriveFlashCount = 0  # this triggers the oFlash strings & timer
                        guitar.neck.ocount = 0  # this triggers the oFlash strings & timer

    def goToResults(self):
        self.ending = True
        if self.song:
            self.song.stop()
            self.done = True
            noScore = False
            for i, player in enumerate(self.players):
                player.twoChord = self.instruments[i].twoChord

                if self.players[0].practiceMode:
                    self.scoring[i].score = 0
                if self.scoring[i].score > 0:
                    noScore = False
                    break
            else:
                if not (self.coOpType and self.coOpScoreCard.score > 0):
                    noScore = True

            if not noScore:
                # force one stat update before gameresults just in case
                self.getHandicap()
                for scoreCard in self.scoring:
                    scoreCard.updateAvMult()
                    scoreCard.getStarScores()
                    if self.coOpType:
                        self.coOpScoreCard.updateAvMult()
                        self.coOpScoreCard.getStarScores()

                    # begin the implementation of the ScoreCard

                if self.coOpType:
                    scoreList = self.scoring
                    scoreList.append(self.coOpScoreCard)
                    if self.coOp:
                        coOpType = 1
                    elif self.coOpRB:
                        coOpType = 2
                    else:
                        coOpType = 1
                else:
                    scoreList = self.scoring
                    coOpType = 0

                self.engine.view.setViewport(1, 0)
                self.freeResources()
                self.engine.world.createScene("GameResultsScene", libraryName=self.libraryName, songName=self.songName, scores=scoreList, coOpType=coOpType, careerMode=self.careerMode)

            else:
                self.changeSong()

    def keyPressed(self, key, unicode, control=None, pullOff=False):
        if not control:
            control = self.controls.keyPressed(key)

        num = self.getPlayerNum(control)
        pressed = False

        if self.instruments[num].isDrum and control in self.instruments[num].keys:
            pressed = True
            if control in Player.bassdrums:
                self.instruments[num].drumsHeldDown[0] = 100
                self.instruments[num].playedSound[0] = False
            elif control in Player.drum1s:
                self.instruments[num].drumsHeldDown[1] = 100
                self.instruments[num].playedSound[1] = False
            elif control in Player.drum2s:
                self.instruments[num].drumsHeldDown[2] = 100
                self.instruments[num].playedSound[2] = False
            elif control in Player.drum3s:
                self.instruments[num].drumsHeldDown[3] = 100
                self.instruments[num].playedSound[3] = False
            elif control in Player.drum5s:
                self.instruments[num].drumsHeldDown[4] = 100
                self.instruments[num].playedSound[4] = False
            else:
                pressed = False
        else:
            activeList = [k for k in self.keysList[num] if self.controls.getState(k)]

            hopo = False
            if control in self.instruments[num].actions:
                pressed = True
            elif control in self.instruments[num].keys:
                if self.instruments[num].hopoActive > 0 or (self.instruments[num].wasLastNoteHopod and self.instruments[num].hopoActive == 0):

                    hopo = True
                    pressed = True
                    if not pullOff:
                        # don't allow lower-fret tapping while holding a higher fret
                        activeKeyList = []
                        LastHopoFretStillHeld = False
                        HigherFretsHeld = False
                        for p, k in enumerate(self.keysList[num]):
                            if self.controls.getState(k):
                                activeKeyList.append(k)
                                if self.instruments[num].hopoLast == p or self.instruments[num].hopoLast - 5 == p:
                                    LastHopoFretStillHeld = True
                                elif (p > self.instruments[num].hopoLast and p < 5) or (p > self.instruments[num].hopoLast and p > 4):
                                    HigherFretsHeld = True

                        if not(LastHopoFretStillHeld and not HigherFretsHeld):  # tapping a lower note should do nothing.
                            pressed = True

            if control in (self.instruments[num].actions):
                for k in self.keysList[num]:
                    if self.controls.getState(k):
                        self.keyBurstTimeout[num] = None
                        break
                else:
                    return True
        if pressed:
            if self.instruments[num].isDrum:
                self.doPick(num)
            else:
                self.handlePick(num, hopo=hopo)

        if control in Player.starts:
            if self.ending:
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
                            self.enteredCode = []
                            self.player.cheating = True
                            func()
                        break
            else:
                self.enteredCode = []

        for i, player in enumerate(self.players):
            if (control == player.keyList[STAR] and not self.isSPAnalog[i]) or control == player.keyList[CANCEL]:
                self.activateSP(i)
            if control == player.keyList[KILL] and not self.isKillAnalog[i]:  # only use this logic if digital killswitch
                self.killswitchEngaged[i] = True

    def keyReleased(self, key):
        control = self.controls.keyReleased(key)
        num = self.getPlayerNum(control)
        if num is None:
            return

        if self.instruments[num].isDrum:
            return True

        if control in self.keysList[num] and self.song:
            for time, note in self.instruments[num].playedNotes:
                # only end the pick if no notes are being held.
                if self.instruments[num].hit[note.number] and (control == self.keysList[num][note.number] or control == self.keysList[num][note.number+5]):
                    self.endPick(num)

        if self.keysList[num] is not None:
            activeList = [k for k in self.keysList[num] if self.controls.getState(k) and k != control]
            if len(activeList) != 0 and self.instruments[num].hopoActive > 0 and control in self.keysList[num]:
                self.keyPressed(None, 0, control=activeList[0], pullOff=True)

        # Digital killswitch disengage
        for i, player in enumerate(self.players):
            if control == player.keyList[KILL] and not self.isKillAnalog[i]:  # only use this logic if digital killswitch
                self.killswitchEngaged[i] = False

    def CheckForValidKillswitchNote(self, num):
        if not self.song:
            return False

        noteCount = len(self.instruments[num].playedNotes)
        if noteCount > 0:
            pickLength = self.instruments[num].getPickLength(self.songTime)
            if pickLength > 0.5 * (self.song.period / 4):
                return True
            else:
                return False
        else:
            return False

    def getExtraScoreForCurrentlyPlayedNotes(self, num):
        if not self.song or self.instruments[num].isDrum or self.instruments[num].isVocal:
            return 0
        if self.coOpType:
            scoreCard = self.coOpScoreCard
        else:
            scoreCard = self.scoring[num]
        noteCount = len(self.instruments[num].playedNotes)
        pickLength = self.instruments[num].getPickLength(self.songTime)
        if pickLength > 1.1 * self.song.period / 4:
            tempExtraScore = self.baseSustainScore * pickLength * noteCount
            if self.starScoreUpdates == 1:
                scoreCard.updateAvMult()
                star = scoreCard.stars
                a = scoreCard.getStarScores(tempExtraScore=tempExtraScore)
                if a > star and ((self.inGameStars == 1 and self.theme == 2) or self.inGameStars == 2):
                    self.engine.data.starDingSound.play()
            return int(tempExtraScore)  # original FoF sustain scoring
        return 0

    def render(self, visibility, topMost):
        # render function reorganization notes:
        # Want to render all background / single-viewport graphics first

        # Alarian's auto-stage scaling update
        w = self.wFull
        h = self.hFull

        font = self.engine.data.font
        lyricFont = self.engine.data.songFont
        bigFont = self.engine.data.bigFont
        sphraseFont = self.engine.data.streakFont2

        if self.song and self.song.readyToGo:
            # differant styles for the start animation of the fretboard
            if self.neckintroAnimationType == 0 or (self.neckintroAnimationType == 4 and self.neckintroThemeType == "fofix"):  # Original
                if self.boardY <= 1:
                    self.setCamera()
                    if self.countdown > 0:  # if the countdown is already at 0 ex. after pause
                        self.countdownOK = True
                        self.boardY = 1
                elif self.boardY > 1:
                    self.boardY -= 0.01  # speed of animation higher the number = the faster the animation
                    self.setCamera()
            elif self.neckintroAnimationType == 1 or (self.neckintroAnimationType == 4 and self.neckintroThemeType == "guitar hero"):  # Guitar Hero
                if self.boardY <= 1:
                    self.setCamera()
                    if self.countdown > 0:
                        self.countdownOK = True
                        self.boardY = 1
                elif self.boardY > 1:
                    self.boardY -= 0.2
                    self.setCamera()
            elif self.neckintroAnimationType == 2 or (self.neckintroAnimationType == 4 and self.neckintroThemeType == "rockband"): #Rock Band
                if self.boardZ <= 1:
                    self.setCamera()
                    if self.countdown > 0:
                        self.countdownOK = True
                        self.boardZ = 1
                elif self.boardZ > 1:
                    self.boardZ -= 0.2
                    self.setCamera()
            elif self.neckintroAnimationType == 3: #Off
                self.setCamera()
                if self.countdown > 0:
                    self.countdownOK = True

            super(GuitarScene, self).render(visibility, topMost)

            self.visibility = v = 1.0 - ((1 - visibility) ** 2)

            with self.engine.view.orthogonalProjection(normalize=True):
                self.renderVocals()

                # render the note sheet just on top of the background:
                if self.lyricSheet is not None and not self.playingVocals:
                    drawImage(self.lyricSheet, scale=(1.0, -1.0), coord=(w/2, h*0.935), stretched=FIT_WIDTH)
                    #the timing line on this lyric sheet image is approx. 1/4 over from the left
                # also render the scrolling lyrics & sections before changing viewports:

                # TODO - Lyrics rendering related code should be broken out into either its own class or function.
                for instrument in self.instruments:
                    if instrument.isVocal:
                        minInst = instrument.currentPeriod * 2
                        maxInst = instrument.currentPeriod * 7
                        slopPer = instrument.currentPeriod
                        break
                else:
                    if len(self.instruments) > 0:
                        minInst = (self.instruments[0].currentPeriod * self.instruments[0].beatsPerBoard) / 2
                        maxInst = (self.instruments[0].currentPeriod * self.instruments[0].beatsPerBoard) * 1.5
                        slopPer = self.instruments[0].currentPeriod
                    else: #This should never trigger...
                        minInst = 1000
                        maxInst = 3000
                        slopPer = 2000
                minPos = self.songTime - minInst
                maxPos = self.songTime + maxInst
                eventWindow = (maxPos - minPos)
                lyricSlop = (slopPer / ((maxPos - minPos)/2)) / 2

                if not self.pause and not self.failed and not self.ending:

                    if self.countdown <= 0:  # only attempt to handle sections / lyrics / text events if the countdown is complete!

                        # handle the sections track
                        if self.midiSectionsEnabled > 0:
                            for time, event in self.song.eventTracks[song.TK_SECTIONS].getEvents(minPos, maxPos):
                                if self.theme == 2:
                                    yOffset = 0.715
                                    txtSize = 0.00170
                                else:
                                    yOffset = 0.69
                                    txtSize = 0.00175
                                #is event happening now?
                                #this version will turn events green right as they hit the line and then grey shortly afterwards
                                #instead of an equal margin on both sides.
                                xOffset = (time - self.songTime) / eventWindow
                                EventHappeningNow = False
                                if xOffset < (0.0 - lyricSlop * 2.0):   #past
                                    gl.glColor3f(0.5, 0.5, 0.5)
                                elif xOffset < lyricSlop / 16.0:   #present
                                    EventHappeningNow = True
                                    gl.glColor3f(0, 1, 0.6)
                                else:   #future, and all other text
                                    gl.glColor3f(1, 1, 1)
                                xOffset += 0.250

                                text = event.text
                                yOffset = 0.00005
                                txtSize = 0.00150
                                lyricFont.render(text, (xOffset, yOffset), (1, 0, 0), txtSize)

                        # handle the lyrics track
                        if self.midiLyricsEnabled > 0 and not self.playingVocals:
                            if self.midiLyricMode == 0:   #scrolling lyrics mode:
                                for time, event in self.song.eventTracks[song.TK_LYRICS].getEvents(minPos, maxPos):
                                    if self.theme == 2:
                                        yOffset = 0.715
                                        txtSize = 0.00170
                                    else:
                                        #gh3 or other standard mod
                                        yOffset = 0.69
                                        txtSize = 0.00175
                                    xOffset = (time - self.songTime) / eventWindow
                                    EventHappeningNow = False
                                    if xOffset < (0.0 - lyricSlop * 2.0):   #past
                                        gl.glColor3f(0.5, 0.5, 0.5)
                                    elif xOffset < lyricSlop / 16.0:   #present
                                        EventHappeningNow = True
                                        gl.glColor3f(0, 1, 0.6)
                                    else:   #future, and all other text
                                        gl.glColor3f(1, 1, 1)
                                    xOffset += 0.250

                                    yOffset = 0.0696
                                    txtSize = 0.00160
                                    text = event.text
                                    if text.find("+") >= 0:  # shift the pitch adjustment markers down one line
                                        text = text.replace("+", "~")
                                        txtSize = 0.00145
                                        yOffset -= 0.0115
                                    lyricFont.render(text, (xOffset, yOffset), (1, 0, 0), txtSize)

                            # TODO - handle line-by-line lyric display and coloring here:
                            elif self.midiLyricMode == 1:   #line-by-line lyrics mode:

                                if self.theme == 2:
                                    txtSize = 0.00170
                                else:
                                    txtSize = 0.00175
                                yOffset = 0.0696
                                xOffset = 0.5 - (lyricFont.getStringSize(self.currentSimpleMidiLyricLine, scale=txtSize)[0] / 2.0)
                                gl.glColor3f(1, 1, 1)
                                lyricFont.render(self.currentSimpleMidiLyricLine, (xOffset, yOffset), (1, 0, 0), txtSize)

                            elif self.midiLyricMode == 2 and (self.numMidiLyricLines > self.activeMidiLyricLineIndex):   #line-by-line lyrics mode:

                                if self.theme == 2:
                                    txtSize = 0.00170
                                else:
                                    txtSize = 0.00175
                                yOffset = 0.0696

                                tempTime, tempLyricLine = self.midiLyricLines[self.activeMidiLyricLineIndex]

                                xOffset = 0.5 - (lyricFont.getStringSize(tempLyricLine, scale=txtSize)[0] / 2.0)
                                gl.glColor3f(0.75, 0.75, 0.75)
                                lyricFont.render(self.activeMidiLyricLine_GreyWords, (xOffset, yOffset), (1, 0, 0), txtSize)

                                xOffset += lyricFont.getStringSize(self.activeMidiLyricLine_GreyWords, scale=txtSize)[0]
                                gl.glColor3f(0, 1, 0)
                                lyricFont.render(self.activeMidiLyricLine_GreenWords, (xOffset, yOffset), (1, 0, 0), txtSize)

                                xOffset += lyricFont.getStringSize(self.activeMidiLyricLine_GreenWords, scale=txtSize)[0]
                                gl.glColor3f(1, 1, 1)
                                lyricFont.render(self.activeMidiLyricLine_WhiteWords, (xOffset, yOffset), (1, 0, 0), txtSize)

                                yOffset += self.lyricHeight
                                xOffset = 0.25
                                gl.glColor3f(1, 1, 1)
                                lyricFont.render(self.currentSimpleMidiLyricLine, (xOffset, yOffset), (1, 0, 0), txtSize)

                        #finally, handle the unused text events track
                        if self.showUnusedTextEvents:
                            for time, event in self.song.eventTracks[song.TK_UNUSED_TEXT].getEvents(minPos, maxPos):
                                if self.theme == 2:
                                    yOffset = 0.715
                                    txtSize = 0.00170
                                else:
                                    yOffset = 0.69
                                    txtSize = 0.00175
                                xOffset = (time - self.songTime) / eventWindow
                                EventHappeningNow = False
                                if xOffset < (0.0 - lyricSlop * 2.0):   #past
                                    gl.glColor3f(0.5, 0.5, 0.5)
                                elif xOffset < lyricSlop / 16.0:   #present
                                    EventHappeningNow = True
                                    gl.glColor3f(0, 1, 0.6)
                                else:   #future, and all other text
                                    gl.glColor3f(1, 1, 1)
                                xOffset += 0.250

                                yOffset = 0.0190
                                txtSize = 0.00124
                                lyricFont.render(event.text, (xOffset, yOffset), (1, 0, 0), txtSize)

                countdownPos = self.lastEvent - self.songTime

                for i, player in enumerate(self.players):
                    p = player.guitarNum
                    if p is not None:
                        self.engine.view.setViewportHalf(self.numberOfGuitars, p)
                    else:
                        self.engine.view.setViewportHalf(1, 0)

                    self.engine.theme.setBaseColor()

                    if i is not None:
                        if self.song:

                            if self.youRock:
                                if self.rockTimer == 1:
                                    self.engine.data.rockSound.play()
                                if self.rockTimer < self.rockCountdown:
                                    self.rockTimer += 1
                                    if self.rockMsg:
                                        drawImage(self.rockMsg, scale=(0.5, -0.5), coord=(w/2, h/2))
                                if self.rockTimer >= self.rockCountdown:
                                    self.rockFinished = True

                            if self.failed:
                                if self.failTimer == 0:
                                    self.song.pause()
                                if self.failTimer == 1:
                                    self.engine.data.failSound.play()
                                if self.failTimer < 100:
                                    self.failTimer += 1
                                    if self.failMsg:
                                        drawImage(self.failMsg, scale=(0.5, -0.5), coord=(w/2, h/2))
                                else:
                                    self.finalFailed = True

                            if self.pause:
                                self.engine.view.setViewport(1, 0)
                                if not self.engine.graphicMenuShown:
                                    drawImage(self.pauseScreen, scale=(self.pause_bkg[2], -self.pause_bkg[3]), coord=(w*self.pause_bkg[0], h*self.pause_bkg[1]), stretched=FULL_SCREEN)

                            # TODO - Break failscreen code out into a function/class
                            if self.finalFailed and self.song:
                                self.engine.view.setViewport(1, 0)
                                if not self.engine.graphicMenuShown:
                                    drawImage(self.failScreen, scale=(self.fail_bkg[2], -self.fail_bkg[3]), coord=(w*self.fail_bkg[0], h*self.fail_bkg[1]), stretched=FULL_SCREEN)

                                # Closer to actual GH3
                                font = self.engine.data.pauseFont
                                text = song.removeSongOrderPrefixFromName(self.song.info.name).upper()
                                scale = font.scaleText(text, maxwidth=0.398, scale=0.0038)
                                size = font.getStringSize(text, scale=scale)
                                font.render(text, (.5-size[0]/2.0, .37-size[1]), scale=scale)

                                diff = str(self.players[0].difficulty)
                                # compute initial position
                                pctComplete = min(100, int(self.songTime / self.lastEvent * 100))

                                curxpos = font.getStringSize(_("COMPLETED") + " ", scale=0.0015)[0]
                                curxpos += font.getStringSize(str(pctComplete), scale=0.003)[0]
                                curxpos += font.getStringSize(_(" % ON "), scale=0.0015)[0]
                                curxpos += font.getStringSize(diff, scale=0.003)[0]
                                curxpos = .5 - curxpos / 2.0
                                c1, c2, c3 = self.fail_completed_color
                                gl.glColor3f(c1, c2, c3)

                                # now render
                                text = _("COMPLETED") + " "
                                size = font.getStringSize(text, scale=0.0015)
                                # Again, for this very font, the "real" height value is 75% of returned value
                                font.render(text, (curxpos, .37+(font.getStringSize(text, scale = 0.003)[1]-size[1])*.75), scale=0.0015)
                                text = str(pctComplete)
                                curxpos += size[0]

                                size = font.getStringSize(text, scale=0.003)
                                font.render(text, (curxpos, .37), scale=0.003)
                                text = _(" % ON ")
                                curxpos += size[0]
                                size = font.getStringSize(text, scale=0.0015)
                                font.render(text, (curxpos, .37+(font.getStringSize(text, scale=0.003)[1]-size[1])*.75), scale=0.0015)
                                text = diff
                                curxpos += size[0]
                                font.render(text, (curxpos, .37), scale=0.003)

                                if not self.failEnd:
                                    self.failGame()

                            if self.hopoIndicatorEnabled and not self.instruments[i].isDrum and not self.pause and not self.failed:  # HOPO indicator (grey = strums required, white = strums not required)
                                text = _("HOPO")
                                if self.instruments[i].hopoActive > 0:
                                    gl.glColor3f(1.0, 1.0, 1.0)
                                else:
                                    gl.glColor3f(0.4, 0.4, 0.4)
                                w, h = font.getStringSize(text, 0.00150)
                                font.render(text, (.950 - w / 2, .710), (1, 0, 0), 0.00150)  # off to the right slightly above fretboard
                                gl.glColor3f(1, 1, 1)

                    # new location for star system support - outside theme-specific logic

                    if (self.coOp and i == self.coOpPlayerMeter) or (self.coOpRB and i == 0) or not self.coOpType:  # only render for player 1 if co-op mode

                        if self.coOpType:
                            self.engine.view.setViewport(1, 0)

                    if self.song and self.song.readyToGo:

                        if not self.coOpRB:
                            if self.players[i].guitarNum is not None:
                                self.engine.view.setViewportHalf(self.numberOfGuitars, self.players[i].guitarNum)
                            else:
                                self.engine.view.setViewportHalf(1, 0)

                        # Realtime hit accuracy display
                        # TODO - Maybe break degug overlays into a function.
                        if ((self.inGameStats == 2 or (self.inGameStats == 1 and self.theme == 2) or self.hopoDebugDisp == 1) and (not self.pause and not self.failed) and not (self.coOpType and not i == 0 and not self.coOp)):
                            # will not show on pause screen, unless HOPO debug is on (for debugging)
                            if self.coOpRB:
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
                            trimmedTotalNoteAcc = self.roundDecimalForDisplay(sHitAcc)
                            text = "%(notesHit)s/%(totalNotes)s: %(hitAcc)s%%" % {'notesHit': str(sNotesHit), 'totalNotes': str(sTotalNotes), 'hitAcc': str(trimmedTotalNoteAcc)}
                            c1, c2, c3 = self.ingame_stats_color
                            gl.glColor3f(c1, c2, c3)  #wht
                            w, h = font.getStringSize(text, 0.00160)
                            if self.theme == 2:
                                if self.numDecimalPlaces < 2:
                                    accDispX = 0.755
                                else:
                                    accDispX = 0.740
                                accDispYac = 0.147
                                accDispYam = 0.170
                            else:
                                accDispX = 0.890
                                accDispYac = 0.140
                                accDispYam = 0.164
                            font.render(text, (accDispX - w/2, accDispYac), (1, 0, 0), 0.00140)     #top-centered by streak under score
                            trimmedAvMult = self.roundDecimalForDisplay(sAvMult)
                            text = "%(avLab)s: %(avMult)sx" % {'avLab': self.tsAvgLabel, 'avMult': str(trimmedAvMult)}
                            gl.glColor3f(c1, c2, c3)
                            w, h = font.getStringSize(text, 0.00160)
                            font.render(text, (accDispX - w/2, accDispYam), (1, 0, 0), 0.00140)     #top-centered by streak under score

                            if sEfHand != 100.0:
                                text = "%s: %.1f%%" % (self.tsHandicapLabel, sEfHand)
                                w, h = font.getStringSize(text, .00160)
                                font.render(text, (.98 - w, .246), (1, 0, 0), 0.00140)

                        if self.coOpRB:
                            if not self.instruments[i].isVocal:
                                self.engine.view.setViewportHalf(self.numberOfGuitars, self.players[i].guitarNum)

                        if not self.instruments[i].isVocal:
                            if self.dispSoloReview[i] and not self.pause and not self.failed:
                                if self.soloReviewCountdown[i] < self.soloReviewDispDelay:
                                    self.soloReviewCountdown[i] += 1
                                    if not (self.instruments[i].freestyleActive or self.scoring[i].freestyleWasJustActive):
                                        gl.glColor3f(1, 1, 1)
                                        text1 = self.soloReviewText[i][0]
                                        text2 = self.soloReviewText[i][1]
                                        xOffset = 0.950
                                        if self.hitAccuracyPos == 0: #Center - need to move solo review above this!
                                            yOffset = 0.080
                                        elif self.jurgPlayer[i]: # and self.autoPlay: jurgPlayer checks if jurg was ever in town. This would block his notice if he came and left.
                                            yOffset = 0.115    #above Jurgen Is Here
                                        else:   #no jurgens here:
                                            yOffset = 0.155   #was 0.180, occluded notes
                                        txtSize = 0.00185
                                        Tw, Th = self.solo_soloFont.getStringSize(text1, txtSize)
                                        Tw2, Th2 = self.solo_soloFont.getStringSize(text2, txtSize)

                                        # scale and display self.soloFrame behind / around the text
                                        lineSpacing = self.solo_soloFont.getLineSpacing(txtSize)
                                        if self.soloFrame:
                                            frameWidth = (max(Tw, Tw2)) * 1.15
                                            frameHeight = lineSpacing * 2.05
                                            boxXOffset = 0.5
                                            boxYOffset = self.hPlayer[i] - (self.hPlayer[i] * ((yOffset + lineSpacing) / self.fontScreenBottom))

                                            tempWScale = frameWidth * self.soloFrameWFactor
                                            tempHScale = -(frameHeight) * self.soloFrameWFactor

                                            drawImage(self.soloFrame, scale=(tempWScale, tempHScale), coord=(self.wPlayer[i]*boxXOffset, boxYOffset))

                                        self.solo_soloFont.render(text1, (0.5 - Tw/2, yOffset), (1, 0, 0), txtSize)   #centered
                                        self.solo_soloFont.render(text2, (0.5 - Tw2/2, yOffset+lineSpacing), (1, 0, 0), txtSize)   #centered
                                else:
                                    self.dispSoloReview[i] = False

                            if self.hopoDebugDisp == 1 and not self.pause and not self.failed and not self.instruments[i].isDrum:
                                # PlayedNote HOPO tappable marking
                                if self.instruments[i].playedNotes:

                                    if len(self.instruments[i].playedNotes) > 1:
                                        self.lastTapText = "tapp: %d, %d" % (self.instruments[i].playedNotes[0][1].tappable, self.instruments[i].playedNotes[1][1].tappable)
                                    else:
                                        self.lastTapText = "tapp: %d" % (self.instruments[i].playedNotes[0][1].tappable)

                                w, h = font.getStringSize(self.lastTapText, 0.00170)
                                font.render(self.lastTapText, (.750 - w / 2, .440), (1, 0, 0), 0.00170)     #off to the right slightly above fretboard

                                if self.instruments[i].hopoActive > 0:
                                    gl.glColor3f(1, 1, 0)
                                    hoActDisp = "+"
                                elif self.instruments[i].hopoActive < 0:
                                    gl.glColor3f(0, 1, 1)
                                    hoActDisp = "-"
                                else:
                                    gl.glColor3f(0.5, 0.5, 0.5)
                                    hoActDisp = "0"
                                text = "HOact: %s" % hoActDisp
                                w, h = font.getStringSize(text, 0.00175)
                                font.render(text, (.750 - w / 2, .410), (1, 0, 0), 0.00170)     #off to the right slightly above fretboard
                                gl.glColor3f(1, 1, 1)

                                # HOPO intention determination flag debug
                                if self.instruments[i].sameNoteHopoString:
                                    gl.glColor3f(1, 1, 0)
                                else:
                                    gl.glColor3f(0.5, 0.5, 0.5)

                                text = "HOflag: %s" % str(self.instruments[i].sameNoteHopoString)

                                w, h = font.getStringSize(text, 0.00175)
                                font.render(text, (.750 - w / 2, .385), (1, 0, 0), 0.00170)     #off to the right slightly above fretboard
                                gl.glColor3f(1, 1, 1)
                                # guitarSoloNoteCount list debug
                                text = str(self.guitarSolos[i])
                                gl.glColor3f(0.9, 0.9, 0.9)
                                w, h = font.getStringSize(text, 0.00110)
                                font.render(text, (.900 - w / 2, .540), (1, 0, 0), 0.00110)     #off to the right slightly above fretboard

                            if self.killDebugEnabled and not self.pause and not self.failed:
                                killXpos = 0.760
                                killYpos = 0.365
                                killTsize = 0.00160

                                if not self.instruments[i].isDrum:
                                    if self.isKillAnalog[i]:

                                        if self.analogKillMode[i] == 2: #xbox mode:
                                            if self.actualWhammyVol[i] < 1.0:
                                                gl.glColor3f(1, 1, 0)
                                            else:
                                                gl.glColor3f(0.5, 0.5, 0.5)
                                        else: #ps2 mode:
                                            if self.actualWhammyVol[i] > 0.0:
                                                gl.glColor3f(1, 1, 0)
                                            else:
                                                gl.glColor3f(0.5, 0.5, 0.5)
                                        text = str(self.roundDecimalForDisplay(self.actualWhammyVol[i]))
                                        w, h = font.getStringSize(text,killTsize)
                                        font.render(text, (killXpos - w / 2, killYpos), (1, 0, 0), killTsize)     #off to the right slightly above fretboard
                                    else:
                                        if self.killswitchEngaged[i]:
                                            gl.glColor3f(1, 1, 0)
                                        else:
                                            gl.glColor3f(0.5, 0.5, 0.5)
                                        text = str(self.killswitchEngaged[i])
                                        w, h = font.getStringSize(text,killTsize)
                                        font.render(text, (killXpos - w / 2, killYpos), (1, 0, 0), killTsize)     #off to the right slightly above fretboard
                            gl.glColor3f(1, 1, 1)

                            # freestyle active status debug display
                            if self.showFreestyleActive == 1 and not self.pause and not self.failed:  # shows when freestyle is active
                                if self.instruments[i].isDrum:    #also show the active status of drum fills
                                    text = "BRE: %s, Fill: %s" % (str(self.instruments[i].freestyleActive), str(self.instruments[i].drumFillsActive))
                                else:
                                    text = "BRE: %s" % str(self.instruments[i].freestyleActive)
                                freeX = .685
                                freeY = .510
                                freeTsize = 0.00150
                                font.render(text, (freeX, freeY),(1, 0, 0),freeTsize)

                        # TODO - show current tempo / BPM and neckspeed if enabled for debugging
                        if self.showBpm == 1 and i == 0:
                            if self.vbpmLogicType == 0:   # VBPM (old)
                                currentBPM = self.instruments[i].currentBpm
                                targetBPM = self.instruments[i].targetBpm
                            else:
                                currentBPM = self.currentBpm
                                targetBPM = self.targetBpm
                            text = "BPM/Target:%.2f/%.2f, NS:%.2f" % (currentBPM, targetBPM, instrument.neckSpeed)
                            bpmX = .35
                            bpmY = .330
                            bpmTsize = 0.00120
                            font.render(text, (bpmX, bpmY), (1, 0, 0), bpmTsize)

                        # lyrical display conditional logic
                        # show the comments (lyrics)
                        if not self.instruments[i].isVocal:
                            # first display the accuracy readout:
                            if self.dispAccuracy[i] and not self.pause and not self.failed:

                                trimmedAccuracy = self.roundDecimalForDisplay(self.accuracy[i])

                                if self.showAccuracy == 1:    #numeric mode
                                    #string concatenation -> modulo formatting
                                    text = "%s %s" % (str(trimmedAccuracy), self.msLabel)
                                elif self.showAccuracy >= 2:    #friendly / descriptive mode
                                    # Precalculated these hit accuracy thresholds instead of every frame
                                    if (self.accuracy[i] >= self.instruments[i].accThresholdWorstLate) and (self.accuracy[i] < self.instruments[i].accThresholdVeryLate):
                                        text = self.tsAccVeryLate
                                        gl.glColor3f(1, 0, 0)
                                    elif (self.accuracy[i] >= self.instruments[i].accThresholdVeryLate) and (self.accuracy[i] < self.instruments[i].accThresholdLate):
                                        text = self.tsAccLate
                                        gl.glColor3f(1, 1, 0)
                                    elif (self.accuracy[i] >= self.instruments[i].accThresholdLate) and (self.accuracy[i] < self.instruments[i].accThresholdSlightlyLate):
                                        text = self.tsAccSlightlyLate
                                        gl.glColor3f(1, 1, 0)
                                    elif (self.accuracy[i] >= self.instruments[i].accThresholdSlightlyLate) and (self.accuracy[i] < self.instruments[i].accThresholdExcellentLate):
                                        text = self.tsAccExcellentLate
                                        gl.glColor3f(0, 1, 0)
                                    elif (self.accuracy[i] >= self.instruments[i].accThresholdExcellentLate) and (self.accuracy[i] < self.instruments[i].accThresholdPerfect):
                                        #give the "perfect" reading some slack, -1.0 to 1.0
                                        text = self.tsAccPerfect
                                        gl.glColor3f(0, 1, 1) #changed color
                                    elif (self.accuracy[i] >= self.instruments[i].accThresholdPerfect) and (self.accuracy[i] < self.instruments[i].accThresholdExcellentEarly):
                                        text = self.tsAccExcellentEarly
                                        gl.glColor3f(0, 1, 0)
                                    elif (self.accuracy[i] >= self.instruments[i].accThresholdExcellentEarly) and (self.accuracy[i] < self.instruments[i].accThresholdSlightlyEarly):
                                        text = self.tsAccSlightlyEarly
                                        gl.glColor3f(1, 1, 0)
                                    elif (self.accuracy[i] >= self.instruments[i].accThresholdSlightlyEarly) and (self.accuracy[i] < self.instruments[i].accThresholdEarly):
                                        text = self.tsAccEarly
                                        gl.glColor3f(1, 1, 0)
                                    elif (self.accuracy[i] >= self.instruments[i].accThresholdEarly) and (self.accuracy[i] < self.instruments[i].accThresholdVeryEarly):
                                        text = self.tsAccVeryEarly
                                        gl.glColor3f(1, 0, 0)
                                    else:
                                        #bug catch - show the problematic number:
                                        text = "%(acc)s %(ms)s" % {'acc': str(trimmedAccuracy), 'ms': self.msLabel}
                                        gl.glColor3f(1, 0, 0)

                                w, h = font.getStringSize(text, 0.00175)

                                posX = 0.98 - (w / 2)
                                posY = 0.296

                                if self.hitAccuracyPos == 0: #Center
                                    posX = .500
                                    posY = .305 + h
                                    if self.showAccuracy == 3:    #for displaying numerical below descriptive
                                        posY = .305
                                elif self.hitAccuracyPos == 2:#Left-bottom
                                    posX = .193
                                    posY = .700
                                elif self.hitAccuracyPos == 3: #Center-bottom
                                    posX = .500
                                    posY = .710

                                font.render(text, (posX - w / 2, posY - h / 2), (1, 0, 0), 0.00170)

                                if self.showAccuracy == 3:    #for displaying numerical below descriptive
                                    text = "%(acc)s %(ms)s" % {'acc': str(trimmedAccuracy), 'ms': self.msLabel}
                                    w, h = font.getStringSize(text, 0.00140)
                                    font.render(text, (posX - w / 2, posY - h / 2 + .030), (1, 0, 0), 0.00140)

                            gl.glColor3f(1, 1, 1)

                            #handle the guitar solo track
                            if (not self.pause and not self.failed and not self.ending):

                                # only use the TK_GUITAR_SOLOS track if at least one player has no MIDI solos marked:
                                if self.instruments[i].useMidiSoloMarkers:   #mark using the new MIDI solo marking system
                                    for time, event in self.song.midiEventTrack[i].getEvents(minPos, maxPos):
                                        if isinstance(event, song.MarkerNote):
                                            if (event.number == song.SP_MARKING_NOTE) and (self.song.midiStyle == song.MIDI_TYPE_RB):    #solo marker note.
                                                soloChangeNow = False
                                                xOffset = (time - self.songTime) / eventWindow + .15
                                                if xOffset < lyricSlop / 16.0:   #present
                                                    soloChangeNow = True
                                                if soloChangeNow:
                                                    if event.endMarker:   #solo ending
                                                        if self.instruments[i].guitarSolo and not event.happened:
                                                            self.endSolo(i)
                                                            event.happened = True
                                                    else:   #solo beginning
                                                        if not self.instruments[i].guitarSolo and not event.happened:
                                                            self.startSolo(i)
                                                            event.happened = True

                                elif self.markSolos == 1:   #fall back on old guitar solo marking system
                                    for time, event in self.song.eventTracks[song.TK_GUITAR_SOLOS].getEvents(minPos, maxPos):
                                        #is event happening now?
                                        xOffset = (time - self.songTime) / eventWindow + .15
                                        EventHappeningNow = False
                                        if xOffset < (0.0 - lyricSlop * 2.0):   #past
                                            EventHappeningNow = False
                                        elif xOffset < lyricSlop / 16.0:   #present
                                            EventHappeningNow = True
                                        if EventHappeningNow:   #process the guitar solo event
                                            if event.text.find("ON") >= 0:
                                                if self.instruments[i].canGuitarSolo:
                                                    if not self.instruments[i].guitarSolo:
                                                        self.startSolo(i)
                                            else:
                                                if self.instruments[i].guitarSolo:
                                                    self.endSolo(i)

                                # render guitar solo in progress - stats
                                if self.instruments[i].guitarSolo:

                                    # scale and display self.soloFrame behind / around the solo accuracy text display
                                    if self.soloFrame:
                                        frameWidth = self.solo_Tw[i] * 1.15
                                        frameHeight = self.solo_Th[i] * 1.07
                                        self.solo_boxYOffset[i] = self.hPlayer[i] - (self.hPlayer[i] * ((self.solo_yOffset[i] + self.solo_Th[i] / 2.0) / self.fontScreenBottom))
                                        tempWScale = frameWidth * self.soloFrameWFactor
                                        tempHScale = -(frameHeight) * self.soloFrameWFactor
                                        drawImage(self.soloFrame, scale=(tempWScale, tempHScale), coord=(self.wPlayer[i]*self.solo_boxXOffset[i], self.solo_boxYOffset[i]))
                                    self.solo_soloFont.render(self.solo_soloText[i], (self.solo_xOffset[i], self.solo_yOffset[i]), (1, 0, 0), self.solo_txtSize)

                                if self.coOpType: #1 BRE in co-op
                                    scoreCard = self.coOpScoreCard
                                    if i == 0:
                                        self.engine.view.setViewportHalf(1, 0)
                                        oneTime = True
                                    else:
                                        oneTime = False
                                else:
                                    scoreCard = self.scoring[i]
                                    oneTime = True
                                # show BRE temp score frame
                                if (self.instruments[i].freestyleActive or (scoreCard.freestyleWasJustActive and not scoreCard.endingStreakBroken and not scoreCard.endingAwarded)) and oneTime:
                                    # to render BEFORE the bonus is awarded.

                                    text = "End Bonus"
                                    yOffset = 0.110
                                    xOffset = 0.500
                                    tW, tH = self.solo_soloFont.getStringSize(text, scale=self.solo_txtSize/2.0)

                                    if self.breScoreFrame:
                                        frameWidth = tW * 1.15
                                        frameHeight = tH * 1.07
                                        if self.coOpType:
                                            boxYOffset = (1.0 - ((yOffset + tH / 2.0) / self.fontScreenBottom)) * self.hFull
                                            boxXOffset = xOffset * self.wFull
                                        else:
                                            boxYOffset = self.hPlayer[i] - (self.hPlayer[i] * ((yOffset + tH / 2.0) / self.fontScreenBottom))
                                            boxXOffset = self.wPlayer[i] * xOffset
                                        tempWScale = frameWidth * self.breScoreFrameWFactor
                                        tempHScale = -(frameHeight) * self.breScoreFrameWFactor
                                        drawImage(self.breScoreFrame, scale=(tempWScale, tempHScale), coord=(boxXOffset, boxYOffset))

                                    self.solo_soloFont.render(text, (xOffset - tW/2.0, yOffset), (1, 0, 0), self.solo_txtSize/2.0)

                                    if self.coOpType and self.partImage:
                                        freeX = .05 * (self.numOfPlayers - 1)
                                        freeI = .05 * self.numOfPlayers
                                        for j in xrange(self.numOfPlayers):
                                            drawImage(self.part[j], scale=(.15, -.15), coord=(self.wFull*(.5-freeX+freeI*j), self.hFull*.58), color=(.8, .8, .8, 1))

                                    text = "%s" % scoreCard.endingScore
                                    tW, tH = self.solo_soloFont.getStringSize(text, scale=self.solo_txtSize)
                                    yOffset = 0.175
                                    xOffset = 0.500

                                    if self.breScoreBackground:
                                        frameHeight = tH * 4.0
                                        frameWidth = frameHeight
                                        if self.coOpType:
                                            boxYOffset = self.hFull * (1.0 - (yOffset + tH / 2.0) / self.fontScreenBottom)
                                            boxXOffset = xOffset * self.wFull
                                        else:
                                            boxYOffset = self.hPlayer[i] - (self.hPlayer[i] * ((yOffset + tH / 2.0) / self.fontScreenBottom))
                                            boxXOffset = self.wPlayer[i] * xOffset
                                        tempWScale = frameWidth * self.breScoreBackgroundWFactor
                                        tempHScale = -(frameHeight) * self.breScoreBackgroundWFactor
                                        drawImage(self.breScoreBackground, scale=(tempWScale, tempHScale), coord=(boxXOffset, boxYOffset))

                                    if self.breScoreFrame:
                                        frameWidth = tW * 1.15
                                        frameHeight = tH * 1.07
                                        if self.coOpType:
                                            boxYOffset = self.hFull * (1.0 - (yOffset + tH / 2.0) / self.fontScreenBottom)
                                            boxXOffset = xOffset * self.wFull
                                        else:
                                            boxYOffset = self.hPlayer[i] - (self.hPlayer[i] * ((yOffset + tH / 2.0) / self.fontScreenBottom))
                                            boxXOffset = self.wPlayer[i] * xOffset
                                        tempWScale = frameWidth * self.breScoreFrameWFactor
                                        tempHScale = -(frameHeight) * self.breScoreFrameWFactor
                                        drawImage(self.breScoreFrame, scale=(tempWScale, tempHScale), coord=(boxXOffset, boxYOffset))
                                    self.solo_soloFont.render(text, (xOffset - tW/2.0, yOffset), (1, 0, 0), self.solo_txtSize)

                                elif scoreCard.freestyleWasJustActive and not scoreCard.endingStreakBroken and scoreCard.endingAwarded and oneTime:
                                    # TODO - ending bonus was awarded - scale up obtained score & box to signify rockage

                                    text = "Success!"
                                    yOffset = 0.110
                                    xOffset = 0.500
                                    tW, tH = self.solo_soloFont.getStringSize(text, scale=self.solo_txtSize/2.0)

                                    if self.breScoreFrame:
                                        frameWidth = tW * 1.15
                                        frameHeight = tH * 1.07
                                        if self.coOpType:
                                            boxYOffset = self.hFull * (1.0 - (yOffset + tH / 2.0) / self.fontScreenBottom)
                                            boxXOffset = xOffset * self.wFull
                                        else:
                                            boxYOffset = self.hPlayer[i] - (self.hPlayer[i] * ((yOffset + tH / 2.0) / self.fontScreenBottom))
                                            boxXOffset = self.wPlayer[i] * xOffset
                                        tempWScale = frameWidth * self.breScoreFrameWFactor
                                        tempHScale = -(frameHeight) * self.breScoreFrameWFactor
                                        drawImage(self.breScoreFrame, scale=(tempWScale, tempHScale), coord=(boxXOffset, boxYOffset))

                                    self.solo_soloFont.render(text, (xOffset - tW/2.0, yOffset), (1, 0, 0), self.solo_txtSize/2.0)

                                    if self.coOpType and self.partImage:
                                        freeX = .05 * (self.numOfPlayers - 1)
                                        freeI = .05 * self.numOfPlayers
                                        for j in xrange(self.numOfPlayers):
                                            drawImage(self.part[j], scale=(.15, -.15), coord=(self.wFull*(.5-freeX+freeI*j), self.hFull*.58))

                                    text = "%s" % scoreCard.endingScore
                                    tW, tH = self.solo_soloFont.getStringSize(text, scale=self.solo_txtSize)
                                    yOffset = 0.175
                                    xOffset = 0.500

                                    if self.breScoreBackground:
                                        frameHeight = tH * 4.0
                                        frameWidth = frameHeight
                                        if self.coOpType:
                                            boxYOffset = self.hFull * (1.0 - (yOffset + tH / 2.0) / self.fontScreenBottom)
                                            boxXOffset = xOffset * self.wFull
                                        else:
                                            boxYOffset = self.hPlayer[i] - (self.hPlayer[i] * ((yOffset + tH / 2.0) / self.fontScreenBottom))
                                            boxXOffset = self.wPlayer[i] * xOffset
                                        tempWScale = frameWidth * self.breScoreBackgroundWFactor
                                        tempHScale = -(frameHeight) * self.breScoreBackgroundWFactor
                                        drawImage(self.breScoreBackground, scale=(tempWScale, tempHScale), coord=(boxXOffset, boxYOffset))

                                    if self.breScoreFrame:
                                        frameWidth = tW * 1.15
                                        frameHeight = tH * 1.07
                                        if self.coOpType:
                                            boxYOffset = self.hFull * (1.0 - (yOffset + tH / 2.0) / self.fontScreenBottom)
                                            boxXOffset = xOffset * self.wFull
                                        else:
                                            boxYOffset = self.hPlayer[i] - (self.hPlayer[i] * ((yOffset + tH / 2.0) / self.fontScreenBottom))
                                            boxXOffset = self.wPlayer[i] * xOffset
                                        tempWScale = frameWidth * self.breScoreFrameWFactor
                                        tempHScale = -(frameHeight) * self.breScoreFrameWFactor
                                        drawImage(self.breScoreFrame, scale=(tempWScale, tempHScale), coord=(boxXOffset, boxYOffset))
                                    self.solo_soloFont.render(text, (xOffset - tW/2.0, yOffset), (1, 0, 0), self.solo_txtSize)

                                elif scoreCard.freestyleWasJustActive and scoreCard.endingStreakBroken and oneTime:
                                    # ending bonus was not awarded - scale up to signify failure
                                    text = "Failed!"
                                    yOffset = 0.110
                                    xOffset = 0.500
                                    tW, tH = self.solo_soloFont.getStringSize(text, scale=self.solo_txtSize/2.0)

                                    if self.breScoreFrame:
                                        frameWidth = tW * 1.15
                                        frameHeight = tH * 1.07
                                        if self.coOpType:
                                            boxYOffset = self.hFull * (1.0 - (yOffset + tH / 2.0) / self.fontScreenBottom)
                                            boxXOffset = xOffset * self.wFull
                                        else:
                                            boxYOffset = self.hPlayer[i] - (self.hPlayer[i] * ((yOffset + tH / 2.0) / self.fontScreenBottom))
                                            boxXOffset = self.wPlayer[i] * xOffset
                                        tempWScale = frameWidth * self.breScoreFrameWFactor
                                        tempHScale = -(frameHeight) * self.breScoreFrameWFactor
                                        drawImage(self.breScoreFrame, scale=(tempWScale, tempHScale), coord=(boxXOffset, boxYOffset))

                                    self.solo_soloFont.render(text, (xOffset - tW/2.0, yOffset), (1, 0, 0), self.solo_txtSize/2.0)

                                    if self.coOpType and self.partImage:
                                        freeX = .05 * (self.numOfPlayers - 1)
                                        freeI = .05 * self.numOfPlayers
                                        for j in xrange(self.numOfPlayers):
                                            if self.scoring[j].endingStreakBroken:
                                                partcolor = (.4, .4, .4, 1)
                                            else:
                                                partcolor = (.8, .8, .8, 1)
                                            drawImage(self.part[j], scale=(.15, -.15), coord=(self.wFull*(.5-freeX+freeI*j), self.hFull*.58), color=partcolor)

                                    text = "%s" % 0
                                    tW, tH = self.solo_soloFont.getStringSize(text, scale=self.solo_txtSize)
                                    yOffset = 0.175
                                    xOffset = 0.500

                                    if self.breScoreBackground:
                                        frameHeight = tH * 4.0
                                        frameWidth = frameHeight
                                        if self.coOpType:
                                            boxYOffset = self.hFull * (1.0 - (yOffset + tH / 2.0) / self.fontScreenBottom)
                                            boxXOffset = xOffset * self.wFull
                                        else:
                                            boxYOffset = self.hPlayer[i] - (self.hPlayer[i] * ((yOffset + tH / 2.0) / self.fontScreenBottom))
                                            boxXOffset = self.wPlayer[i] * xOffset
                                        tempWScale = frameWidth * self.breScoreBackgroundWFactor
                                        tempHScale = -(frameHeight) * self.breScoreBackgroundWFactor
                                        drawImage(self.breScoreBackground, scale=(tempWScale, tempHScale), coord=(boxXOffset, boxYOffset))

                                    if self.breScoreFrame:
                                        frameWidth = tW * 1.15
                                        frameHeight = tH * 1.07
                                        if self.coOpType:
                                            boxYOffset = self.hFull * (1.0 - (yOffset + tH / 2.0) / self.fontScreenBottom)
                                            boxXOffset = xOffset * self.wFull
                                        else:
                                            boxYOffset = self.hPlayer[i] - (self.hPlayer[i] * ((yOffset + tH / 2.0) / self.fontScreenBottom))
                                            boxXOffset = self.wPlayer[i] * xOffset
                                        tempWScale = frameWidth * self.breScoreFrameWFactor
                                        tempHScale = -(frameHeight) * self.breScoreFrameWFactor
                                        drawImage(self.breScoreFrame, scale=(tempWScale, tempHScale), coord=(boxXOffset, boxYOffset))
                                    self.solo_soloFont.render(text, (xOffset - tW/2.0, yOffset), (1, 0, 0), self.solo_txtSize)

                        self.engine.view.setViewportHalf(1, 0)
                        # Display framerate
                        if self.engine.show_fps:  # probably only need to once through.
                            c1, c2, c3 = self.ingame_stats_color
                            gl.glColor3f(c1, c2, c3)
                            text = _("FPS: %.2f" % self.engine.fpsEstimate)
                            w, h = font.getStringSize(text, scale=0.00140)
                            font.render(text, (self.fpsRenderPos[0], self.fpsRenderPos[1] - h/2), (1, 0, 0), 0.00140)

                        if self.showScriptLyrics and not self.pause and not self.failed:
                            for time, event in self.song.eventTracks[song.TK_SCRIPT].getEvents(self.songTime - self.song.period * 2, self.songTime + self.song.period * 4):  # script track

                                if isinstance(event, PictureEvent):
                                    if self.songTime < time or self.songTime > time + event.length:
                                        continue

                                    try:
                                        picture = event.picture
                                    except Exception:
                                        self.engine.loadImgDrawing(event, "picture", os.path.join(self.libraryName, self.songName, event.fileName))
                                        picture = event.picture

                                    w = self.wFull
                                    h = self.hFull

                                    yOffset = 0.715

                                    fadePeriod = 500.0
                                    f = (1.0 - min(1.0, abs(self.songTime - time) / fadePeriod) * min(1.0, abs(self.songTime - time - event.length) / fadePeriod)) ** 2

                                    drawImage(picture, scale=(1, -1), coord=(w / 2, (f * -2 + 1) * h/2+yOffset))

                                elif isinstance(event, TextEvent):
                                    if self.songTime >= time and self.songTime <= time + event.length and not self.ending:  # to not display events after ending!

                                        xOffset = 0.5
                                        if self.scriptLyricPos == 0:
                                            yOffset = 0.715
                                            txtSize = 0.00170
                                        else:   # display in lyric bar position
                                            yOffset = 0.0696    # last change +0.0000
                                            txtSize = 0.00160

                                        # TODO - pre-retrieve and translate all current tutorial script.txt events, if applicable.
                                        if self.song.info.tutorial:
                                            text = _(event.text)
                                            w, h = lyricFont.getStringSize(text, txtSize)
                                            lyricFont.render(text, (xOffset - w / 2, yOffset), (1, 0, 0), txtSize)
                                        else:
                                            text = event.text
                                            w, h = lyricFont.getStringSize(text, txtSize)
                                            lyricFont.render(text, (xOffset - w / 2, yOffset), (1, 0, 0), txtSize)

                self.engine.view.setViewport(1, 0)
                gN = 0
                for i in range(self.numOfPlayers):
                    if self.instruments[i].isVocal:
                        continue
                    if self.jurgPlayer[i]:
                        if self.jurg[i]:
                            if self.customBot[i]:
                                text = self.tsJurgenIsHere % self.customBot[i]
                            else:
                                text = self.tsJurgenIsHere % self.tsBotNames[self.aiSkill[i]]
                        else:
                            if self.customBot[i]:
                                text = self.tsJurgenWasHere % self.customBot[i]
                            else:
                                text = self.tsJurgenWasHere % self.tsBotNames[self.aiSkill[i]]
                        jurgScale = float(self.jurgenText[2])
                        w, h = bigFont.getStringSize(text, scale=jurgScale)
                        self.engine.theme.setBaseColor()
                        if jurgScale > .2 or jurgScale < .0001:
                            jurgScale = .001
                        jurgX = float(self.jurgenText[0])
                        if jurgX < 0:
                            jurgX = 0
                        jurgX = (jurgX + gN) / self.numberOfGuitars
                        if jurgX > ((gN + 1) / self.numberOfGuitars) - w:
                            jurgX = ((gN + 1) / self.numberOfGuitars) - w
                        jurgY = float(self.jurgenText[1])
                        if jurgY > .75 - h:
                            jurgY = .75 - h
                        if not self.failed:
                            bigFont.render(text, (jurgX, jurgY), scale=jurgScale)  # y was 0.4 - more positioning weirdness.
                    gN += 1

                    #End Jurgen Code
                # Get Ready to Rock & countdown, song info during countdown, and song time left display on top of everything else

                if not self.pause and not self.failed and not self.ending:
                    if self.coOpType: #render co-op phrases (full screen width) above the rest.
                        if self.displayText[self.coOpPhrase] is not None:
                            gl.glColor3f(.8, .75, .01)
                            size = sphraseFont.getStringSize(self.displayText[self.coOpPhrase], scale=self.displayTextScale[self.coOpPhrase])
                            sphraseFont.render(self.displayText[self.coOpPhrase], (.5-size[0]/2, self.textY[self.coOpPhrase]-size[1]), scale=self.displayTextScale[self.coOpPhrase])

                    # show countdown
                    # fixed the countdown timer
                    if self.countdownSeconds > 1:
                        self.engine.theme.setBaseColor(min(1.0, 3.0 - abs(4.0 - self.countdownSeconds)))
                        text = self.tsGetReady
                        w, h = font.getStringSize(text)
                        font.render(text, (.5 - w / 2, .3))
                        if self.countdownSeconds < 6:
                            if self.counting:
                                for i, player in enumerate(self.players):
                                    text = player.name
                                    w2, h2 = font.getStringSize(text)

                                    if not self.instruments[i].isVocal:
                                        w = self.wPlayer[i]
                                        h = self.hPlayer[i]
                                        partImgwidth = self.part[i].width1()
                                        partwFactor = 250.000 / partImgwidth
                                        partX = ((i * 2) + 1) / (self.numOfPlayers * 2.0)
                                        drawImage(self.part[i], scale=(partwFactor * 0.25, partwFactor * -0.25), coord=(w*partX, h*.4), color=(1, 1, 1, 3.0 - abs(4.0 - self.countdownSeconds)))
                                        self.engine.theme.setBaseColor(min(1.0, 3.0 - abs(4.0 - self.countdownSeconds)))

                                        font.render(text, (partX - w2*.5, .5))
                                    else:
                                        w = self.wFull
                                        h = self.hFull
                                        partImgWidth = self.part[i].width1()
                                        partwFactor = 250.000 / partImgWidth
                                        drawImage(self.part[i], scale=(partwFactor*0.25, partwFactor*-0.25), coord=(w*.5, h*.75), color=(1, 1, 1, 3.0 - abs(4.0 - self.countdownSeconds)))
                                        self.engine.theme.setBaseColor(min(1.0, 3.0 - abs(4.0 - self.countdownSeconds)))

                                        font.render(text, (.5 - w2*.5, .25))
                            else:
                                scale = 0.002 + 0.0005 * (self.countdownSeconds % 1) ** 3
                                text = "%d" % (self.countdownSeconds)
                                w, h = bigFont.getStringSize(text, scale=scale)
                                self.engine.theme.setBaseColor()
                                bigFont.render(text, (self.countdownPosX - w / 2, self.countdownPosY - h / 2), scale=scale)

                    if self.resumeCountdownSeconds > 1:
                        scale = 0.002 + 0.0005 * (self.resumeCountdownSeconds % 1) ** 3
                        text = "%d" % (self.resumeCountdownSeconds)
                        w, h = bigFont.getStringSize(text, scale=scale)
                        self.engine.theme.setBaseColor()
                        bigFont.render(text, (self.countdownPosX - w / 2, self.countdownPosY - h / 2), scale=scale)

                    w, h = font.getStringSize(" ")
                    y = .05 - h / 2 - (1.0 - v) * .2

                    songFont = self.engine.data.songFont

                    # show song name
                    if self.countdown and self.song:
                        self.songDisplayPrefix = ""
                        if self.song.info.findTag("cover"):  # misc changes to make it more GH/RB
                            self.songDisplayPrefix = "%s  \n " % self.tsAsMadeFamousBy # no more ugly colon! ^_^

                        self.engine.theme.setBaseColor(min(1.0, 4.0 - abs(4.0 - self.countdown)))

                        comma = ', ' if self.song.info.year else ""
                        extra = ""
                        if self.song.info.frets:
                            extra = "%s \n %s%s" % (extra, self.tsFrettedBy, self.song.info.frets)
                        if self.song.info.version:
                            extra = "%s \n v%s" % (extra, self.song.info.version)

                        Dialogs.wrapText(songFont, (self.songInfoDisplayX, self.songInfoDisplayY - h / 2), "%s \n %s%s%s%s%s" % (song.removeSongOrderPrefixFromName(self.song.info.name), self.songDisplayPrefix, self.song.info.artist, comma, self.song.info.year, extra), rightMargin=.6, scale=self.songInfoDisplayScale)
                    else:
                        # this is where the song countdown display is generated:
                        if countdownPos < 0:
                            countdownPos = 0

#####################################################################
# -*- coding: utf-8 -*-                                             #
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

import logging
import math
import os

import OpenGL.GL as gl
import numpy as np

from fofix.game.song import Note, Tempo, \
    MarkerNote, FREESTYLE_MARKING_NOTE
from fofix.core.Image import draw3Dtex
from fofix.core.Shader import shaders
from fofix.core.Mesh import Mesh
from fofix.core import cmgl


log = logging.getLogger(__name__)


class Instrument(object):
    def __init__(self, engine, playerObj, scene, player=0):
        self.engine = engine
        self.scene = scene
        self.song = self.scene.song

        self.starPowerDecreaseDivisor = 200.0 / self.engine.audioSpeedFactor

        self.bigRockEndingMarkerSeen = False

        self.isStarPhrase = False
        self.finalStarSeen = False

        self.time = 0.0
        self.pickStartPos = 0
        self.leftyMode = False
        self.drumFli = False

        self.freestyleActive = False
        self.drumFillsActive = False

        self.incomingNeckMode = self.engine.config.get("game", "incoming_neck_mode")
        self.guitarSoloNeckMode = self.engine.config.get("game", "guitar_solo_neck")
        self.bigRockEndings = self.engine.config.get("game", "big_rock_endings")

        # For Animated notes
        self.noteSpinFrames = 16
        self.Animspeed = 30  # Lower value = Faster animations
        self.indexCount = 0
        self.noteSpinFrameIndex = 0

        # BRE scoring variables
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

        # empty variables for class compatibility
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

        self.tempoBpm = 120  # default is NEEDED here...

        self.beatsPerBoard            = 5.0
        self.boardWidth               = self.engine.theme.neckWidth
        self.boardLength              = self.engine.theme.neckLength
        self.beatsPerUnit             = self.beatsPerBoard / self.boardLength
        self.fretColors               = self.engine.theme.noteColors
        self.spColor                  = self.engine.theme.spNoteColor
        self.useFretColors            = self.engine.theme.use_fret_colors
        self.powerActiveColorToggle   = self.engine.theme.powerActiveColorToggle
        self.powerGainColorToggle     = self.engine.theme.powerGainColorToggle

        if not self.engine.theme.killNoteColor == "frets":
            kC = self.engine.theme.killNoteColor
            self.killColor = [kC, kC, kC, kC, kC]
        else:
            self.killColor = self.fretColors

        self.playedNotes = []
        self.missedNotes = []

        self.useMidiSoloMarkers = False
        self.canGuitarSolo = False
        self.guitarSolo = False
        self.sameNoteHopoString = False
        self.hopoProblemNoteNum = -1
        self.currentGuitarSoloHitNotes = 0

        self.cappedScoreMult = 0

        self.battleTarget = 0

        self.currentBpm     = 120.0  # need a default 120BPM to be set in case a custom song has no tempo events.
        self.currentPeriod  = 60000.0 / self.currentBpm
        self.targetBpm      = self.currentBpm
        self.targetPeriod   = 60000.0 / self.targetBpm
        self.lastBpmChange  = -1.0
        self.baseBeat       = 0.0

        self.camAngle = 0.0  # set from guitarScene

        self.indexFps = self.engine.config.get("video", "fps")

        self.Animspeed = 30  # Lower value = Faster animations
        # For Animated Starnotes
        self.indexCoun = 0

        # to keep track of pause status here as well
        self.paused = False

        self.spEnabled = True
        self.starPower = 0
        self.starPowerGained = False
        self.spNote = False

        self.starpowerMode = self.engine.config.get("game", "starpower_mode")
        self.killPoints = False

        # get difficulty
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

        # need a separate variable to track whether or not hopos are actually active
        self.wasLastNoteHopod = False

        self.hopoLast = -1
        self.hopoColor = (0, .5, .5)
        self.player = player

        self.hit = [False, False, False, False, False]
        self.freestyleHit = [False, False, False, False, False]

        # this should be retrieved once at init, not repeatedly in-game whenever tails are rendered.
        self.notedisappear = self.engine.config.get("game", "notedisappear")
        self.fretsUnderNotes = self.engine.config.get("game", "frets_under_notes")
        self.staticStrings = self.engine.config.get("performance", "static_strings")

        self.muteSustainReleases = self.engine.config.get("game", "sustain_muting")

        self.twoChord = 0
        self.twoChordApply = False
        self.hopoActive = 0

        self.LastStrumWasChord = False

        self.vbpmLogicType = self.engine.config.get("debug", "use_new_vbpm_beta")

        # Get theme
        self.theme = self.engine.data.theme

        self.spRefillMode = self.engine.config.get("game", "sp_notes_while_active")
        self.hitglow_color = self.engine.config.get("video", "hitglow_color")  # this should be global, not retrieved every fret render.

        # check if BRE enabled
        if self.bigRockEndings == 2 or self.bigRockEndings == 1:
            self.freestyleEnabled = True

        self.nstype = self.engine.config.get("game", "nstype")                  # neck style
        self.twoDnote = self.engine.theme.twoDnote                              # note style (2D or 3D)
        self.twoDkeys = self.engine.theme.twoDkeys                              # key style
        self.threeDspin = self.engine.theme.threeDspin                          # 3d notes spin when they are star power notes
        self.noterotate = self.engine.config.get("coffee", "noterotate")        # adjust notes for if they were designed for FoF 1.1 or 1.2
        self.billboardNote = self.engine.theme.billboardNote                    # 3D notes follow the angle of the camera

        # fixing neck speed
        if self.nstype < 3:
            # not constant mode
            self.speed = self.engine.config.get("coffee", "neckSpeed") * 0.01
        else:
            # constant mode
            self.speed = 410 - self.engine.config.get("coffee", "neckSpeed")  # invert this value

        self.boardScaleX = self.boardWidth / 3.0
        self.boardScaleY = self.boardLength / 9.0

        self.fretPress = self.engine.theme.fret_press

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

        self.disableVBPM = self.engine.config.get("game", "disable_vbpm")
        self.disableFretSFX = self.engine.config.get("video", "disable_fretsfx")
        self.disableFlameSFX = self.engine.config.get("video", "disable_flamesfx")

        self.meshColor = self.engine.theme.meshColor
        self.hopoColor = self.engine.theme.hopoColor
        self.spotColor = self.engine.theme.spotColor
        self.keyColor = self.engine.theme.keyColor
        self.key2Color = self.engine.theme.key2Color

        self.hitFlameYPos         = self.engine.theme.hitFlamePos[0]
        self.hitFlameZPos         = self.engine.theme.hitFlamePos[1]
        self.holdFlameYPos        = self.engine.theme.holdFlamePos[0]
        self.holdFlameZPos        = self.engine.theme.holdFlamePos[1]
        self.hitFlameSize         = self.engine.theme.hitFlameSize
        self.holdFlameSize        = self.engine.theme.holdFlameSize
        self.hitFlameBlackRemove  = self.engine.theme.hitFlameBlackRemove
        self.hitGlowsBlackRemove  = self.engine.theme.hitGlowsBlackRemove
        self.hitGlowOffset        = self.engine.theme.hitGlowOffset
        self.hitFlameOffset       = self.engine.theme.hitFlameOffset
        self.drumHitFlameOffset   = self.engine.theme.drumHitFlameOffset
        self.hitGlowsRotation     = self.engine.theme.hitFlameRotation
        self.hitFlameRotation     = self.engine.theme.hitFlameRotation

        # all flames/glows are set to there corresponding color else they are set to the fret colors
        if not self.engine.theme.flamesColor == "frets":
            fC = self.engine.theme.flamesColor
            self.flameColors = [fC, fC, fC, fC, fC]
        else:
            self.flameColors = self.fretColors

        if not self.engine.theme.hitGlowColor == "frets":
            hGC = self.engine.theme.hitGlowColor
            self.hitGlowColors = [hGC, hGC, hGC, hGC, hGC]
        else:
            self.hitGlowColors = self.fretColors

        if not self.engine.theme.glowColor == "frets":
            gC = self.engine.theme.glowColor
            self.glowColor = [gC, gC, gC, gC, gC]
        else:
            self.glowColor = self.fretColors

        self.twoChordMax = False

        self.canGuitarSolo = False
        self.guitarSolo = False
        self.fretboardHop = 0.00
        self.scoreMultiplier = 1
        self.coOpFailed = False
        self.coOpRestart = False
        self.starPowerActive = False

        # Tail's base arrays will get modified overtime
        self.tail_tex = np.array([[0.0, 0.0],
                                  [1.0, 0.0],
                                  [0.0, 1.0],
                                  [1.0, 1.0]], dtype=np.float32)

        self.tail_col = np.array([[0, 0, 0, 1],
                                  [0, 0, 0, 1],
                                  [0, 0, 0, 1],
                                  [0, 0, 0, 1]], dtype=np.float32)

        self.tail_vtx = np.array([[0, 0, 0],
                                  [0, 0, 0],
                                  [0, 0, 0],
                                  [0, 0, 0]], dtype=np.float32)

    def checkPath(self, subdirectory, s_file, lastResort=False):
        """
        Check if there is a "drum" or "bass" folder inside the subdirectory for
        image replacement.

        :param subdirectory: the folder in the theme to search
                             if the instrument is drum or bass it will extend this
        :param s_file: the file to search for
        :param lastResort: if the file isn't even found in the default path then
                           resort to using the file in the data folder
        :return: the path of the searched file.
        """

        # Get theme
        themename = self.engine.data.themeLabel

        defaultpath = os.path.join("themes", themename, subdirectory)
        themepath = os.path.join("themes", themename, subdirectory)
        if self.isDrum:
            themepath = os.path.join(themepath, "drum")
        elif self.isBassGuitar:
            themepath = os.path.join(themepath, "bass")

        if self.engine.fileExists(os.path.join(themepath, s_file)):
            return os.path.join(themepath, s_file)
        else:
            if lastResort and not self.engine.fileExists(os.path.join(defaultpath, s_file)):
                return s_file
            log.debug("Image not found: " + os.path.join(themepath, s_file))
            return os.path.join(defaultpath, s_file)

    def loadFlames(self):
        engine = self.engine
        themename = self.engine.data.themeLabel

        get = lambda s_file: self.checkPath("flames", s_file)

        self.HCount = 0
        self.HFrameLimit = self.engine.theme.HoldFlameFrameLimit
        self.HFrameLimit2 = self.engine.theme.HitFlameFrameLimit
        self.HCountAni = False

        if self.disableFretSFX:
            self.glowDrawing = None
        else:
            engine.loadImgDrawing(self, "glowDrawing", get("glow.png"))
            if not self.glowDrawing:
                engine.loadImgDrawing(self, "glowDrawing", "glow.png")

        if self.disableFlameSFX:
            self.hitglow2Drawing = None
            self.hitglowDrawing = None
            self.hitglowAnim = None
            self.hitflamesAnim = None
            self.hitflames2Drawing = None
            self.hitflames1Drawing = None
        else:
            engine.loadImgDrawing(self, "hitflames1Drawing", get("hitflames1.png"))
            engine.loadImgDrawing(self, "hitflames2Drawing", get("hitflames2.png"))
            engine.loadImgDrawing(self, "hitflamesAnim", get("hitflamesanimation.png"))
            engine.loadImgDrawing(self, "powerHitflamesAnim", get("powerhitflamesanimation.png"))
            engine.loadImgDrawing(self, "hitglowAnim", get("hitglowanimation.png"))
            engine.loadImgDrawing(self, "hitglowDrawing", get("hitglow.png"))
            engine.loadImgDrawing(self, "hitglow2Drawing", get("hitglow2.png"))

        engine.loadImgDrawing(self, "hitlightning", os.path.join("themes", themename, "lightning.png"), textureSize=(128, 128))

    def loadNotes(self):
        engine = self.engine

        get = lambda s_file: self.checkPath("notes", s_file)

        self.noteSpin = self.engine.config.get("performance", "animated_notes")

        self.spActTex = None
        self.noteTex = None
        self.noteButtons = None

        if self.twoDnote:
            if self.noteSpin:
                self.starSpinFrames = 16
                engine.loadImgDrawing(self, "noteAnimatedNormal", get("animated_normal.png"))
                engine.loadImgDrawing(self, "noteAnimatedHOPO", get("animated_hopo.png"))
                engine.loadImgDrawing(self, "noteAnimatedPower", get("animated_power.png"))
                engine.loadImgDrawing(self, "noteAnimatedPowerHOPO", get("animated_power_hopo.png"))
                engine.loadImgDrawing(self, "noteAnimatedPowerActive", get("animated_power_active.png"))
                engine.loadImgDrawing(self, "noteAnimatedPowerActiveHOPO", get("animated_power_active_hopo.png"))

            engine.loadImgDrawing(self, "noteButtons", get("notes.png"))

            size = (self.boardWidth / self.strings / 2, self.boardWidth / self.strings / 2)
            self.noteVtx = np.array([[-size[0], 0.0, size[1]],
                                     [size[0], 0.0, size[1]],
                                     [-size[0], 0.0, -size[1]],
                                     [size[0], 0.0, -size[1]]],
                                     dtype=np.float32)

            self.noteTexCoord = [[np.array([[i/float(self.strings), s/6.0],
                                           [(i+1)/float(self.strings), s/6.0],
                                           [i/float(self.strings), (s+1)/6.0],
                                           [(i+1)/float(self.strings), (s+1)/6.0]],
                                           dtype=np.float32)
                                  for i in range(self.strings)] for s in range(6)]
            self.animatedNoteTexCoord = [[np.array([[i/float(self.strings), s/float(self.noteSpinFrames)],
                                           [(i+1)/float(self.strings), s/float(self.noteSpinFrames)],
                                           [i/float(self.strings), (s+1)/float(self.noteSpinFrames)],
                                           [(i+1)/float(self.strings), (s+1)/float(self.noteSpinFrames)]],
                                           dtype=np.float32)
                                  for i in range(self.strings)] for s in range(self.noteSpinFrames)]
        else:
            defaultNote = False

            # can't use IOError for fallback logic for a Mesh() call...
            if self.engine.fileExists(get("note.dae")):
                # look in the notes folder for files
                self.engine.resource.load(self, "noteMesh", lambda: Mesh(engine.resource.fileName(get("note.dae"))))
            else:
                # default to files in data folder
                self.engine.resource.load(self, "noteMesh", lambda: Mesh(engine.resource.fileName("note.dae")))
                defaultNote = True

            if self.engine.fileExists(get("star.dae")):
                # look in the notes folder for files
                self.engine.resource.load(self, "starMesh", lambda: Mesh(self.engine.resource.fileName(get("star.dae"))))
            else:
                # No mesh for star notes
                self.starMesh = None

            if defaultNote:
                self.notetex = False
            else:
                self.notetex = True
                self.startex = True
                self.staratex = True

                for i in range(5):
                    if not engine.loadImgDrawing(self, "notetex"+chr(97+i), get("notetex_"+chr(97+i)+".png")):
                        self.notetex = False
                        break

                for i in range(5):
                    if not self.engine.loadImgDrawing(self, "startex"+chr(97+i), get("startex_"+chr(97+i)+".png")):
                        self.startex = False
                        break

                for i in range(5):
                    if not self.engine.loadImgDrawing(self, "staratex"+chr(97+i), get("staratex_"+chr(97+i)+".png")):
                        self.staratex = False
                        break

    def loadFrets(self):
        engine = self.engine

        get = lambda s_file: self.checkPath("frets", s_file)

        if self.twoDkeys:
            engine.loadImgDrawing(self, "fretButtons", get("fretbuttons.png"))
        else:
            defaultKey = False

            # can't use IOError for fallback logic for a Mesh() call...
            if self.engine.fileExists(get("key.dae")):
                # look in the frets folder for files
                engine.resource.load(self, "keyMesh", lambda: Mesh(engine.resource.fileName(get("key.dae"))))
            else:
                # default to files in data folder
                engine.resource.load(self, "keyMesh", lambda: Mesh(engine.resource.fileName("key.dae")))
                defaultKey = True

            if defaultKey:
                self.keytex = False
            else:
                self.keytex = True
                for i in range(5):
                    if not engine.loadImgDrawing(self, "keytex"+chr(97+i), get("keytex_"+chr(97+i)+".png")):
                        self.keytex = False
                        break

    def loadTails(self):
        engine = self.engine

        get = lambda s_file: self.checkPath("tails", s_file)
        getD = lambda s_file: self.checkPath("tails", s_file, True)  # resorts to checking data

        #MFH - freestyle tails (for drum fills & BREs)
        engine.loadImgDrawing(self, "freestyle1", getD("freestyletail1.png"), textureSize=(128, 128))
        engine.loadImgDrawing(self, "freestyle2", getD("freestyletail2.png"), textureSize=(128, 128))

        if self.tailsEnabled:
            self.simpleTails = False
            for i in range(0, 7):
                if not engine.loadImgDrawing(self, "tail"+str(i), get("tail"+str(i)+".png"), textureSize=(128, 128)):
                    self.simpleTails = True
                    break
                if not engine.loadImgDrawing(self, "taile"+str(i), get("taile"+str(i)+".png"), textureSize=(128, 128)):
                    self.simpleTails = True
                    break
                if not engine.loadImgDrawing(self, "btail"+str(i), get("btail"+str(i)+".png"), textureSize=(128, 128)):
                    self.simpleTails = True
                    break
                if not engine.loadImgDrawing(self, "btaile"+str(i), get("btaile"+str(i)+".png"), textureSize=(128, 128)):
                    self.simpleTails = True
                    break

            if self.simpleTails:
                log.debug("Simple tails used; complex tail loading error...")
                engine.loadImgDrawing(self, "tail1", getD("tail1.png"), textureSize=(128, 128))
                engine.loadImgDrawing(self, "tail2", getD("tail2.png"), textureSize=(128, 128))
                engine.loadImgDrawing(self, "bigTail1", getD("bigtail1.png"), textureSize=(128, 128))
                engine.loadImgDrawing(self, "bigTail2", getD("bigtail2.png"), textureSize=(128, 128))

            engine.loadImgDrawing(self, "kill1", getD("kill1.png"), textureSize=(128, 128))
            engine.loadImgDrawing(self, "kill2", getD("kill2.png"), textureSize=(128, 128))

        else:
            self.tail1 = None
            self.tail2 = None
            self.bigTail1 = None
            self.bigTail2 = None
            self.kill1 = None
            self.kill2 = None

    def loadImages(self):
        self.loadFrets()
        self.loadNotes()
        self.loadTails()
        self.loadFlames()

    def setMultiplier(self, multiplier):
        self.scoreMultiplier = multiplier
        self.neck.scoreMultiplier = multiplier

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

        # Filter out unnecessary BPM settings (when currentBPM is already set!)
        self.currentBpm = bpm  # update current BPM as well

        # Neck speed determination:
        if self.nstype == 0:
            # BPM mode
            self.neckSpeed = (340 - bpm) / self.speed
        elif self.nstype == 1:
            # Difficulty mode
            if self.difficulty == 0:
                # expert
                self.neckSpeed = 220 / self.speed
            elif self.difficulty == 1:
                self.neckSpeed = 250 / self.speed
            elif self.difficulty == 2:
                self.neckSpeed = 280 / self.speed
            else:
                # easy
                self.neckSpeed = 300 / self.speed
        elif self.nstype == 2:
            # BPM & Diff mode
            if self.difficulty == 0:
                # expert
                self.neckSpeed = (226-(bpm/10))/self.speed
            elif self.difficulty == 1:
                self.neckSpeed = (256-(bpm/10))/self.speed
            elif self.difficulty == 2:
                self.neckSpeed = (286-(bpm/10))/self.speed
            else:
                # easy
                self.neckSpeed = (306-(bpm/10))/self.speed
        else:
            # Percentage mode - pre-calculated
            self.neckSpeed = self.speed

        self.earlyMargin = 250 - bpm/5 - 70*self.hitw
        self.lateMargin = 250 - bpm/5 - 70*self.hitw

        if self.muteSustainReleases == 4:
            # tight
            self.noteReleaseMargin = (200 - bpm/5 - 70*1.2)
        elif self.muteSustainReleases == 3:
            # standard
            self.noteReleaseMargin = (200 - bpm/5 - 70*1.0)
        elif self.muteSustainReleases == 2:
            # wide
            self.noteReleaseMargin = (200 - bpm/5 - 70*0.7)
        else:
            # ultra-wide
            self.noteReleaseMargin = (200 - bpm/5 - 70*0.5)

        # TODO - only calculate the below values if the realtime hit accuracy feedback display is enabled - otherwise this is a waste!
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
        track = song.track[self.player]
        notes = [(time, event)
            for time, event in track.getEvents(pos - self.lateMargin, pos + self.earlyMargin)
                if isinstance(event, Note) and
                    not (event.hopod or event.played or event.skipped) and
                    (time >= (pos - self.lateMargin)) and (time <= (pos + self.earlyMargin))
        ]

        return sorted(notes, key=lambda x: x[0])

    def getMissedNotes(self, song, pos, catchup=False):
        if not song and not song.readyToGo:
            return

        m1 = self.lateMargin
        m2 = self.lateMargin * 2

        track = song.track[self.player]
        notes = [(time, event)
            for time, event in track.getEvents(pos - m2, pos - m1)
                if isinstance(event, Note) and
                    time >= (pos - m2) and time <= (pos - m1) and
                    not event.played and not event.hopod and not event.skipped
        ]

        if catchup:
            for time, event in notes:
                event.skipped = True

        return sorted(notes, key=lambda x: x[0])

    def getRequiredNotesForRender(self, song, pos):
        track = song.track[self.player]
        notes = [(time, event) for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard)]
        return notes

    def coOpRescue(self, pos):
        self.coOpRestart = True  # initializes Restart Timer
        self.coOpRescueTime = pos
        self.starPower = 0
        log.debug("Rescued at " + str(pos))

    def isKillswitchPossible(self):
        possible = False
        if self.isDrum:
            return possible
        for i in range(0, 5):
            if self.hit[i]:
                possible = True
        return possible

    def renderHitTrails(self, controls):
        """ Renders the tail glow hitflame """
        if self.hitGlowColors[0][0] == -1 or self.disableFlameSFX:
            return

        if self.HCountAni:
            for n in range(self.strings):
                f = self.fretWeight[n]

                if f and (controls.getState(self.actions[0]) or controls.getState(self.actions[1])):
                    f += 0.25

                w = self.boardWidth / self.strings
                x = (self.strings / 2 - n) * w

                y = f / 6
                y -= self.holdFlameYPos

                flameSize = self.holdFlameSize

                alphaEnabled = self.hitGlowsBlackRemove

                if self.fretActivity[n]:
                    ms = math.sin(self.time) * .25 + 1
                    ff = self.fretActivity[n] + 1.2
                    vtx = flameSize * ff
                    s = ff / 6

                    if not self.hitFlameYPos == 0:
                        y = s - self.holdFlameYPos
                    else:
                        y = 0

                    if not self.hitFlameZPos == 0:
                        z = s - self.holdFlameZPos
                    else:
                        z = 0

                    y -= self.hitGlowOffset[n]

                    color = self.hitGlowColors[n]
                    color = tuple([color[ifc] + .38 for ifc in range(3)])  # to make sure the final color looks correct on any color set

                    # Animated hitflames
                    if self.hitglowAnim:
                        self.HCount += 1
                        if self.HCount > self.Animspeed-1:
                            self.HCount = 0
                        HIndex = (self.HCount * self.HFrameLimit - (self.HCount * self.HFrameLimit) % self.Animspeed) / self.Animspeed
                        if HIndex >= self.HFrameLimit-1:
                            HIndex = 0
                        texX = (HIndex*(1.0/self.HFrameLimit), HIndex*(1.0/self.HFrameLimit)+(1.0/self.HFrameLimit))

                        draw3Dtex(self.hitglowAnim, coord=(x, y, z), rot=self.hitGlowsRotation, scale=(2.4, 1, 3.3),
                                              vertex=(-vtx,-vtx,vtx,vtx), texcoord=(texX[0],0.0,texX[1],1.0), multiples=True,
                                              alpha=alphaEnabled, color=(1,1,1))

                    if self.hitglowDrawing:
                        flameColorMod = (1.19, 1.97, 10.59)
                        flamecol = tuple([color[ifc]*flameColorMod[ifc] for ifc in range(3)])

                        if self.starPowerActive and self.powerActiveColorToggle:
                            flamecol = self.spColor

                        elif self.spNote and self.powerGainColorToggle:
                            flamecol = self.spColor

                        draw3Dtex(self.hitglowDrawing, coord=(x, y + .15, z), rot=self.hitGlowsRotation,
                                              scale=(0.5 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff),
                                              vertex=(-vtx,-vtx,vtx,vtx), texcoord=(0.0,0.0,1.0,1.0),
                                              multiples=True, alpha=alphaEnabled, color=flamecol)

                    if self.hitglow2Drawing:
                        ff += .3
                        vtx = flameSize * ff

                        flameColorMod = (1.19, 1.78, 12.22)
                        flamecol = tuple([color[ifc]*flameColorMod[ifc] for ifc in range(3)])

                        if self.starPowerActive and self.powerActiveColorToggle:
                            flamecol = self.spColor

                        elif self.spNote and self.powerGainColorToggle:
                            flamecol = self.spColor

                        draw3Dtex(self.hitglow2Drawing, coord=(x, y, z), rot=self.hitGlowsRotation,
                                              scale=(.40 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff),
                                              vertex=(-vtx,-vtx,vtx,vtx), texcoord=(0.0,0.0,1.0,1.0),
                                              multiples=True, alpha=alphaEnabled, color=flamecol)

    def renderAnimatedFlames(self, song, pos):
        """ Renders the flames that appear when a note is struck """
        if not song or self.flameColors[0][0] == -1:
            return

        flameSize = self.hitFlameSize
        w = self.boardWidth / self.strings
        renderedNotes = self.getRequiredNotesForRender(song, pos)

        alphaEnabled = self.hitFlameBlackRemove

        for time, event in renderedNotes:
            if not isinstance(event, Note):
                continue

            if event.played or event.hopod:
                if not self.disableFlameSFX:
                    if self.isDrum:
                        if event.number == 0:
                            # make the bass drum not render a flame
                            continue

                        x = (self.strings / 2 + .5 - event.number) * w
                    else:
                        x = ((self.strings / 2 - event.number) * w)

                    ff = 1 + 0.25
                    s = ff / 6

                    if not self.hitFlameYPos == 0:
                        y = s - self.hitFlameYPos
                    else:
                        y = 0

                    if not self.hitFlameZPos == 0:
                        z = s - self.hitFlameZPos
                    else:
                        z = 0

                    if self.isDrum:
                        y -= self.drumHitFlameOffset[event.number]
                    else:
                        y -= self.hitFlameOffset[event.number]

                    # y += .665  # XXX: see if it's useless
                    ff += 1.5  # ff first time is 2.75 after this
                    vtx = flameSize * ff

                    if self.hitflamesAnim:
                        event.HCount2 += 1
                        self.HCountAni = False
                        if event.HCount2 >= 5.0:
                            self.HCountAni = True
                        if event.HCount2 < self.HFrameLimit2:

                            HIndex = (event.HCount2 * self.HFrameLimit2 - (event.HCount2 * self.HFrameLimit2) % self.HFrameLimit2) / self.HFrameLimit2

                            texX = (HIndex*(1.0/self.HFrameLimit2), HIndex*(1.0/self.HFrameLimit2)+(1.0/self.HFrameLimit2))
                            if self.powerHitflamesAnim and self.starPowerActive:
                                texture = self.powerHitflamesAnim
                            else:
                                texture = self.hitflamesAnim

                            draw3Dtex(texture, coord=(x, y + .665, z), rot=self.hitFlameRotation,
                                                  scale=(1.6, 1.6, 4.9), vertex=(-vtx,-vtx,vtx,vtx),
                                                  texcoord=(texX[0],0.0,texX[1],1.0),  multiples=True,
                                                  alpha=alphaEnabled, color=(1,1,1))

    def renderFlames(self, song, pos):
        """ Renders the flames that appear when a note is struck """
        if not song or self.flameColors[0][0] == -1:
            return

        w = self.boardWidth / self.strings
        flameSize = self.hitFlameSize

        flameLimit = 10.0
        flameLimitHalf = round(flameLimit / 2.0)
        renderedNotes = self.getRequiredNotesForRender(song, pos)

        alphaEnabled = self.hitFlameBlackRemove

        for time, event in renderedNotes:
            if not isinstance(event, Note):
                continue

            if (event.played or event.hopod) and event.flameCount < flameLimit:
                if not self.disableFlameSFX:

                    if self.isDrum:
                        if event.number == 0:
                            continue

                        flameColor = self.flameColors[event.number]
                        x = (self.strings / 2 + .5 - event.number) * w
                    else:
                        flameColor = self.flameColors[event.number]
                        x = (self.strings / 2 - event.number) * w

                    if self.starPowerActive and self.powerActiveColorToggle:
                        flamecol = self.spColor
                    elif event.star and self.powerGainColorToggle:
                        flamecol = self.spColor

                    ms = math.sin(self.time) * .25 + 1

                    xlightning = (self.strings / 2 - event.number) * 2.2 * w
                    ff = 1 + 0.25
                    s = ff / 6

                    if not self.hitFlameYPos == 0:
                        y = s - self.hitFlameYPos
                    else:
                        y = 0

                    if not self.hitFlameZPos == 0:
                        z = s - self.hitFlameZPos
                    else:
                        z = 0

                    if self.isDrum:
                        y -= self.drumHitFlameOffset[event.number]
                    else:
                        y -= self.hitFlameOffset[event.number]

                    # y += .665  # XXX: see if it's useless
                    ff += 1.5  # ff first time is 2.75 after this
                    vtx = flameSize * ff

                    if not self.hitflamesAnim:
                        self.HCountAni = True

                    if event.flameCount < flameLimitHalf and self.hitflames2Drawing:
                        draw3Dtex(self.hitflames2Drawing, coord=(x, y + .20, z), rot=self.hitFlameRotation,
                                              scale=(.25 + .6 * ms * ff, event.flameCount/6.0 + .6 * ms * ff, event.flameCount / 6.0 + .6 * ms * ff),
                                              vertex=(-vtx,-vtx,vtx,vtx), texcoord=(0.0,0.0,1.0,1.0),
                                              multiples=True, alpha=alphaEnabled, color=flameColor)

                        for i in range(3):
                            draw3Dtex(self.hitflames2Drawing, coord=(x-.005, y + .255, z), rot=self.hitFlameRotation,
                                                  scale=(.30 + i*0.05 + .6 * ms * ff, event.flameCount/(5.5 - i*0.4) + .6 * ms * ff, event.flameCount / (5.5 - i*0.4) + .6 * ms * ff),
                                                  vertex=(-vtx,-vtx,vtx,vtx), texcoord=(0.0,0.0,1.0,1.0),
                                                  multiples=True, alpha=alphaEnabled, color=flameColor)

                    flameColor = tuple([flameColor[ifc] + .38 for ifc in range(3)])  # to make sure the final color looks correct on any color set
                    flameColorMod = 0.1 * (flameLimit - event.flameCount)
                    flamecol = tuple([ifc * flameColorMod for ifc in flameColor])
                    scaleChange = (3.0, 2.5, 2.0, 1.7)
                    yOffset = (.35, .405, .355, .355)
                    scaleMod = .6 * ms * ff

                    for step in range(4):
                        if step == 0:
                            yzscaleMod = event.flameCount / scaleChange[step]
                        else:
                            yzscaleMod = (event.flameCount + 1) / scaleChange[step]

                        if self.hitflames1Drawing:
                            draw3Dtex(self.hitflames1Drawing, coord=(x - .005, y + yOffset[step], z), rot=self.hitFlameRotation,
                                                  scale=(.25 + step*.05 + scaleMod, yzscaleMod + scaleMod, yzscaleMod + scaleMod),
                                                  vertex=(-vtx,-vtx,vtx,vtx), texcoord=(0.0,0.0,1.0,1.0),
                                                  multiples=True, alpha=alphaEnabled, color=flamecol)

                        # draw lightning in GH themes on SP gain
                        if step == 0 and event.finalStar and self.spEnabled and self.hitlightning:
                            draw3Dtex(self.hitlightning, coord=(xlightning, ff / 6, 3.3), rot=(90, 1, 0, 0),
                                                  scale=(.15 + .5 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, 2), vertex=(.4,-2,.4,2),
                                                  texcoord=(0.0,0.0,1.0,1.0), multiples=True, alpha=True, color=(1,1,1))

                event.flameCount += 1

    def render3DNote(self, texture, model, color, isTappable):
        """ Group rendering of 2D notes into method """
        if (self.billboardNote):
            gl.glRotatef(self.camAngle + 90, 1, 0, 0)
        if texture:
            gl.glColor3f(1, 1, 1)
            gl.glEnable(gl.GL_TEXTURE_2D)
            texture.texture.bind()
            gl.glMatrixMode(gl.GL_TEXTURE)
            gl.glScalef(1, -1, 1)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glScalef(self.boardScaleX, self.boardScaleY, 1)

            if isTappable:
                mesh = "Mesh_001"
            else:
                mesh = "Mesh"

            model.render(mesh)

            if shaders.enable("notes"):
                shaders.setVar("isTextured", True)
                model.render(mesh)
                shaders.disable()

            gl.glMatrixMode(gl.GL_TEXTURE)
            gl.glLoadIdentity()
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glDisable(gl.GL_TEXTURE_2D)

        else:
            # mesh = outer ring (black)
            # mesh_001 = main note (key color)
            # mesh_002 = top (spot or hopo if no mesh_003)
            # mesh_003 = hopo bump (hopo color)

            # fixed 3D note colours
            gl.glColor4f(*color)
            if shaders.enable("notes"):
                shaders.setVar("isTextured", False)
            model.render("Mesh_001")
            shaders.disable()
            gl.glColor3f(self.spotColor[0], self.spotColor[1], self.spotColor[2])
            if isTappable:
                if self.hopoColor[0] == -2:
                    gl.glColor4f(*color)
                else:
                    gl.glColor3f(self.hopoColor[0], self.hopoColor[1], self.hopoColor[2])
                if model.find("Mesh_003"):
                    model.render("Mesh_003")
                    gl.glColor3f(self.spotColor[0], self.spotColor[1], self.spotColor[2])
            model.render("Mesh_002")
            gl.glColor3f(self.meshColor[0], self.meshColor[1], self.meshColor[2])
            model.render("Mesh")

    def renderNote(self, length, sustain, color, tailOnly=False, isTappable=False, fret=0, spNote=False, isOpen=False, spAct=False):

        if tailOnly:
            return

        # this should be retrieved once at init, not repeatedly in-game whenever tails are rendered.

        if self.twoDnote:
            noteImage = self.noteButtons
            tailOnly = True

            y = 0
            if spNote:
                y += 2
            elif self.starPowerActive:
                y += 4
            if isTappable:
                y += 1

            if self.noteSpin:
                texCoord = self.animatedNoteTexCoord[self.noteSpinFrameIndex][fret]
                if isTappable:
                    if spNote:
                        noteImage = self.noteAnimatedPowerHOPO
                    elif self.starPowerActive:
                        noteImage = self.noteAnimatedPowerActiveHOPO
                    else:
                        noteImage = self.noteAnimatedHOPO
                else:
                    if spNote:
                        noteImage = self.noteAnimatedPower
                    elif self.starPowerActive:
                        noteImage = self.noteAnimatedPowerActive
                    else:
                        noteImage = self.noteAnimatedNormal
                if not noteImage:
                    noteImage = self.noteButtons
                    texCoord = self.noteTexCoord[y][fret]
            else:
                noteImage = self.noteButtons
                texCoord = self.noteTexCoord[y][fret]

            draw3Dtex(noteImage, vertex=self.noteVtx, texcoord=texCoord,
                                  scale=(1,1,1), rot=(self.camAngle,1,0,0), multiples=False, color=color)

        else:
            # 3d Notes
            shaders.setVar("Material", color, "notes")

            self.notepos = self.engine.theme.notepos
            self.noterot = self.engine.theme.noterot

            if spNote and self.starMesh is not None:
                meshObj = self.starMesh
            else:
                meshObj = self.noteMesh

            gl.glPushMatrix()
            gl.glEnable(gl.GL_DEPTH_TEST)
            gl.glDepthMask(1)
            gl.glShadeModel(gl.GL_SMOOTH)

            if spNote and self.threeDspin:
                gl.glRotate(90 + self.time / 3, 0, 1, 0)
            elif not spNote and self.noterotate:
                gl.glRotatef(90, 0, 1, 0)
                gl.glRotatef(-90, 1, 0, 0)

            if fret >= 0 and fret <= 4:
                gl.glRotate(self.noterot[fret], 0, 0, 1)
                gl.glTranslatef(0, self.notepos[fret], 0)

            if self.notetex:
                if self.startex and spNote:
                    texture = getattr(self,"startex"+chr(97+fret))
                elif self.staratex and self.starPowerActive:
                    texture = getattr(self,"staratex"+chr(97+fret))
                else:
                    texture = getattr(self,"notetex"+chr(97+fret))
            else:
                texture = None

            self.render3DNote(texture, meshObj, color, isTappable)

            gl.glDepthMask(0)
            gl.glPopMatrix()
            gl.glDisable(gl.GL_DEPTH_TEST)

    def renderNotes(self, visibility, song, pos):
        if not song:
            return
        if not song.readyToGo:
            return

        self.bigMax = 0
        # Update dynamic period

        self.currentPeriod = self.neckSpeed
        self.targetPeriod = self.neckSpeed

        self.killPoints = False

        w = self.boardWidth / self.strings

        self.starNotesInView = False
        self.openStarNotesInView = False

        renderedNotes = reversed(self.getRequiredNotesForRender(song, pos))
        for time, event in renderedNotes:

            if isinstance(event, Tempo):

                self.tempoBpm = event.bpm
                if self.lastBpmChange > 0 and self.disableVBPM:
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

            if event.noteBpm == 0.0:
                event.noteBpm = self.tempoBpm

            if event.number == 0 and self.isDrum:
                # skip all open notes
                continue

            if self.coOpFailed:
                if self.coOpRestart:
                    if time - self.coOpRescueTime < (self.currentPeriod * self.beatsPerBoard * 2):
                        continue
                    elif self.coOpRescueTime + (self.currentPeriod * self.beatsPerBoard * 2) < pos:
                        self.coOpFailed = False
                        self.coOpRestart = False
                        log.debug("Turning off coOpFailed. Rescue successful.")
                else:
                    # can't break. Tempo.
                    continue

            self.spNote = False

            if self.isDrum:
                x = (self.strings / 2 - .5 - (event.number - 1)) * w
                isOpen = False
                c = self.fretColors[event.number]
            else:
                x = (self.strings / 2 - (event.number)) * w
                isOpen = False
                c = self.fretColors[event.number]

            if event.number == 4 and self.isDrum:
                c = self.fretColors[0]  # need to swap note 0 and note 4 colors for drums:

            z = ((time - pos) / self.currentPeriod) / self.beatsPerUnit
            z2 = ((time + event.length - pos) / self.currentPeriod) / self.beatsPerUnit

            if z > self.boardLength * .8:
                f = (self.boardLength - z) / (self.boardLength * .2)
            elif z < 0:
                f = min(1, max(0, 1 + z2))
            else:
                f = 1.0

            # hide notes in BRE zone if BRE enabled
            if self.freestyleEnabled:
                if self.isDrum:
                    if self.drumFillsReady or self.freestyleReady:
                        if time > self.freestyleStart - self.freestyleOffset and time < self.freestyleStart + self.freestyleOffset + self.freestyleLength:
                            z = -2.0
                else:
                    if time > self.freestyleStart - self.freestyleOffset and time < self.freestyleStart + self.freestyleOffset + self.freestyleLength:
                        z = -2.0

            if self.twoDnote and not self.useFretColors:
                color = (1, 1, 1, 1 * visibility * f)
            else:
                color = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1 * visibility * f)

            if self.isDrum:
                length = 0
            else:
                if event.length > 120:
                    length = (event.length - 50) / self.currentPeriod / self.beatsPerUnit
                else:
                    length = 0

            tailOnly = False

            # user setting for starpower refill / replenish notes
            if self.starPowerActive:
                if self.spRefillMode == 0:
                    # mode 0 = no starpower / overdrive refill notes
                    self.spEnabled = False
                elif self.spRefillMode == 1 and self.theme != 2:
                    # mode 1 = overdrive refill notes in RB themes only
                    self.spEnabled = False
                elif self.spRefillMode == 2 and song.midiStyle != 1:
                    # mode 2 = refill based on MIDI type
                    self.spEnabled = False

            if event.star:
                self.starNotesInView = True
            if event.finalStar:
                self.finalStarSeen = True
                self.starNotesInView = True

            if event.star and self.spEnabled:
                self.spNote = True

            if event.finalStar and self.spEnabled:
                if event.played or event.hopod:
                    if event.flameCount < 1 and not self.starPowerGained:
                        if self.starPower < 50 and self.isDrum:
                            # not enough starpower to activate yet, kill existing drumfills
                            for dfEvent in self.drumFillEvents:
                                dfEvent.happened = True
                        log.debug("star power added")

                        if self.starPower < 100:
                            self.starPower += 25
                        if self.starPower > 100:
                            self.starPower = 100
                        self.overdriveFlashCount = 0  # this triggers the oFlash strings & timer
                        self.starPowerGained = True

            if event.tappable < 2 or self.isDrum:
                isTappable = False
            else:
                isTappable = True

            if event.played or event.hopod:
                # if the note is hit
                continue
            elif z < 0:
                # Notes past frets
                # if none of the below they keep on going, it would be self.notedisappear == 1
                if self.notedisappear == 0:
                    # Notes disappear
                    continue
                elif self.notedisappear == 2:
                    # Notes turn red
                    color = (1, 0, 0, 1)  # turn note red

            if self.isDrum:
                sustain = False

                gl.glPushMatrix()
                gl.glTranslatef(x, 0, z)
                self.renderNote(length, sustain=sustain, color=color, tailOnly=tailOnly, isTappable=isTappable, fret=event.number, spNote=self.spNote, isOpen=isOpen)
                gl.glPopMatrix()
            else:
                if z + length < -1.0:
                    continue
                if event.length <= 120:
                    length = None

                sustain = False
                if event.length > (1.4 * (60000.0 / event.noteBpm) / 4):
                    sustain = True

                gl.glPushMatrix()
                gl.glTranslatef(x, 0, z)

                if shaders.turnon:
                    shaders.setVar("note_position", (x, (1.0 - visibility) ** (event.number + 1), z), "notes")

                self.renderNote(length, sustain=sustain, color=color, tailOnly=tailOnly, isTappable=isTappable, fret=event.number, spNote=self.spNote)
                gl.glPopMatrix()

        # end FOR loop / note rendering loop
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
        self.targetPeriod = self.neckSpeed

        self.killPoints = False

        self.openStarNotesInView = False

        renderedNotes = reversed(self.getRequiredNotesForRender(song, pos))
        for time, event in renderedNotes:

            if isinstance(event, Tempo):

                self.tempoBpm = event.bpm
                if self.lastBpmChange > 0 and self.disableVBPM:
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

            if event.noteBpm == 0.0:
                event.noteBpm = self.tempoBpm

            if self.coOpFailed:
                if self.coOpRestart:
                    if time - self.coOpRescueTime < (self.currentPeriod * self.beatsPerBoard * 2):
                        continue
                    elif self.coOpRescueTime + (self.currentPeriod * self.beatsPerBoard * 2) < pos:
                        self.coOpFailed = False
                        self.coOpRestart = False
                        log.debug("Turning off coOpFailed. Rescue successful.")
                else:
                    # can't break. Tempo.
                    continue

            if not event.number == 0:
                # if Normal note exit
                continue

            isOpen = True
            x = 0
            c = self.openFretColor
            z = ((time - pos) / self.currentPeriod) / self.beatsPerUnit

            if z > self.boardLength * .8:
                f = (self.boardLength - z) / (self.boardLength * .2)
            else:
                f = 1.0

            # hide notes in BRE zone if BRE enabled
            if self.freestyleEnabled:
                if self.isDrum:
                    if self.drumFillsReady or self.freestyleReady:
                        if time > self.freestyleStart - self.freestyleOffset and time < self.freestyleStart + self.freestyleOffset + self.freestyleLength:
                            z = -2.0
                else:
                    if time > self.freestyleStart - self.freestyleOffset and time < self.freestyleStart + self.freestyleOffset + self.freestyleLength:
                        z = -2.0

            if self.twoDnote and not self.useFretColors:
                color = (1, 1, 1, 1 * visibility * f)
            else:
                color = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1 * visibility * f)

            length = 0

            tailOnly = False
            self.spNote = False

            # user setting for starpower refill / replenish notes
            if self.starPowerActive:
                if self.spRefillMode == 0:
                    # mode 0 = no starpower / overdrive refill notes
                    self.spEnabled = False
                elif self.spRefillMode == 1 and self.theme != 2:
                    # mode 1 = overdrive refill notes in RB themes only
                    self.spEnabled = False
                elif self.spRefillMode == 2 and song.midiStyle != 1:
                    # mode 2 = refill based on MIDI type
                    self.spEnabled = False

            if event.star:
                self.openStarNotesInView = True
            if event.finalStar:
                self.finalStarSeen = True
                self.openStarNotesInView = True

            if event.finalStar and self.spEnabled:
                if event.played or event.hopod:
                    if event.flameCount < 1 and not self.starPowerGained:

                        if self.starPower < 50:
                            # not enough starpower to activate yet, kill existing drumfills
                            for dfEvent in self.drumFillEvents:
                                dfEvent.happened = True

                        if self.starPower < 100:
                            self.starPower += 25
                        if self.starPower > 100:
                            self.starPower = 100
                        self.overdriveFlashCount = 0  # this triggers the oFlash strings & timer
                        self.starPowerGained = True

            isTappable = False

            if event.played or event.hopod:
                # if the note is hit
                continue
            elif z < 0: #Notes past frets
                # if none of the below they keep on going, it would be self.notedisappear == 1
                if self.notedisappear == 0:
                    # Notes disappear
                    continue
                elif self.notedisappear == 2:
                    # Notes turn red
                    color = (1, 0, 0, 1)  # turn note red

            sustain = False

            gl.glPushMatrix()
            gl.glTranslatef(x, 0, z)
            self.renderNote(length, sustain=sustain, color=color, tailOnly=tailOnly, isTappable=isTappable, fret=event.number, spNote=self.spNote, isOpen=isOpen)
            gl.glPopMatrix()

        # end FOR loop / note rendering loop
        if (not self.openStarNotesInView) and (not self.starNotesInView) and self.finalStarSeen:
            self.spEnabled = True
            self.finalStarSeen = False
            self.isStarPhrase = False

    def render3DKey(self, texture, model, x, y, color, fretNum, f):
        """ Group rendering of 3D keys/frets into method """
        gl.glPushMatrix()
        gl.glDepthMask(1)
        gl.glEnable(gl.GL_LIGHTING)
        gl.glShadeModel(gl.GL_SMOOTH)
        gl.glEnable(gl.GL_LIGHT0)
        gl.glRotatef(90, 0, 1, 0)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, np.array([5.0, 10.0, -10.0, 0.0], dtype=np.float32))
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, np.array([0.2, 0.2, 0.2, 0.0], dtype=np.float32))
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, np.array([1.0, 1.0, 1.0, 0.0], dtype=np.float32))

        gl.glRotatef(-90, 1, 0, 0)
        gl.glRotatef(-90, 0, 0, 1)

        if fretNum == 0:
            # green fret button
            gl.glRotate(self.keyrot[0], 0, 1, 0)
            gl.glTranslatef(0, 0, self.keypos[0])
        elif fretNum == 1:
            # red fret button
            gl.glRotate(self.keyrot[1], 0, 1, 0)
            gl.glTranslatef(0, 0, self.keypos[1])
        elif fretNum == 2:
            # yellow fret button
            gl.glRotate(self.keyrot[2], 0, 1, 0)
            gl.glTranslatef(0, 0, self.keypos[2])
        elif fretNum == 3:
            # blue fret button
            gl.glRotate(self.keyrot[3], 0, 1, 0)
            gl.glTranslatef(0, 0, self.keypos[3])
        elif fretNum == 4:
            # orange fret button
            gl.glRotate(self.keyrot[4], 0, 1, 0)
            gl.glTranslatef(0, 0, self.keypos[4])

        gl.glTranslatef(x, y + color[3] * 6, 0)

        if texture:
            gl.glColor4f(1, 1, 1, color[3] + 1.0)
            gl.glEnable(gl.GL_TEXTURE_2D)
            texture.bind()
            gl.glMatrixMode(gl.GL_TEXTURE)
            gl.glScalef(1, -1, 1)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glScalef(self.boardScaleX, self.boardScaleY, 1)
            if not self.hit[fretNum] and f:
                model.render("Mesh_001")
            elif self.hit[fretNum]:
                model.render("Mesh_002")
            else:
                model.render("Mesh")
            gl.glMatrixMode(gl.GL_TEXTURE)
            gl.glLoadIdentity()
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glDisable(gl.GL_TEXTURE_2D)
        else:
            gl.glColor4f(color[0], color[1], color[2], color[3]+1.0)

            # Mesh - Main fret
            # Key_001 - Top of fret (key_color)
            # Key_002 - Bottom of fret (key2_color)
            # Glow_001 - Only rendered when a note is hit along with the glow.svg
            if model.find("Glow_001"):
                model.render("Mesh")
                if model.find("Key_001"):
                    gl.glColor3f(self.keyColor[0], self.keyColor[1], self.keyColor[2])
                    model.render("Key_001")
                if model.find("Key_002"):
                    gl.glColor3f(self.key2Color[0], self.key2Color[1], self.key2Color[2])
                    model.render("Key_002")
            else:
                model.render()

        gl.glDisable(gl.GL_LIGHTING)
        gl.glDisable(gl.GL_LIGHT0)
        gl.glDepthMask(0)
        gl.glPopMatrix()

    def renderFrets(self, visibility, song, controls):
        pass

    def renderHitGlow(self):
        for n in range(self.strings2):
            c = self.glowColor[n]
            f = self.fretActivity[n]
            w = self.boardWidth / self.strings
            x = (self.strings / 2 - n) * w
            if self.fretPress:
                y = f / 6
            else:
                y = 0
            size = .22

            if f and not self.disableFretSFX:

                if self.glowColor[0] == -1:
                    s = 1.0
                else:
                    s = 0.0

                while s < 1:
                    ms = s * (math.sin(self.time) * .25 + 1)
                    gl.glColor3f(c[0] * (1 - ms), c[1] * (1 - ms), c[2] * (1 - ms))

                    gl.glPushMatrix()
                    gl.glTranslatef(x, y, 0)
                    gl.glScalef(.1 + .02 * ms * f, .1 + .02 * ms * f, .1 + .02 * ms * f)
                    gl.glRotatef( 90, 0, 1, 0)
                    gl.glRotatef(-90, 1, 0, 0)
                    gl.glRotatef(-90, 0, 0, 1)
                    if not self.twoDkeys and not self.keytex:
                        if self.keyMesh.find("Glow_001"):
                            self.keyMesh.render("Glow_001")
                        else:
                            self.keyMesh.render()
                    gl.glPopMatrix()
                    s += 0.2

                # Hitglow color
                if self.hitglow_color == 0:
                    glowcol = (c[0], c[1], c[2])  # Same as fret
                elif self.hitglow_color == 1:
                    glowcol = (1, 1, 1)  # Actual color

                f += 2

                draw3Dtex(self.glowDrawing, coord=(x, 0, 0.01), rot=(f * 90 + self.time, 0, 1, 0),
                                    texcoord=(0.0, 0.0, 1.0, 1.0), vertex=(-size * f, -size * f, size * f, size * f),
                                    multiples=True, alpha=True, color=glowcol)

    def renderTail(self, song, length, sustain, kill, color, tailOnly=False, isTappable=False, big=False, fret=0, spNote=False, freestyleTail=0, pos=0):
        """
        if freestyleTail == 0, act normally.
        if freestyleTail == 1, render an freestyle tail
        if freestyleTail == 2, render highlighted freestyle tail
        """

        def project(beat):
            return 0.125 * beat / self.beatsPerUnit  # was 0.12

        offset = (pos - self.lastBpmChange) / self.currentPeriod + self.baseBeat

        self.tailSpeed = self.engine.theme.noteTailSpeedMulti

        if not self.simpleTails:
            # Seperate Tail images dont color the images
            tailcol = (1, 1, 1, 1)

        elif self.starPowerActive and self.powerActiveColorToggle:
            tailcol = self.spColor

        elif spNote and self.powerGainColorToggle:
            tailcol = self.spColor

        elif not big and tailOnly:
            # grey because the note was missed
            tailcol = (.6, .6, .6, color[3])

        else:
            # normal colors
            tailcol = (color)

        if length > self.boardLength:
            s = self.boardLength
        else:
            s = length

        size = (.4, s)

        if kill and big:
            kEffect = (math.sin(pos / 50) + 1) / 2
            size = ((0.02 + (kEffect * 0.182) * 2), s)
            c = [self.killColor[fret][0], self.killColor[fret][1], self.killColor[fret][2]]
            if c != [0, 0, 0]:
                for i in range(0, 3):
                    c[i] = c[i] * kEffect + color[i] * (1 - kEffect)
                    tailcol = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1)

        if sustain:
            if length is not None:
                # so any theme containing appropriate files can use new tails
                if not self.simpleTails:
                    for n in range(5):
                        if big and tailOnly:
                            if kill and self.killfx == 0:
                                tex1 = self.kill1
                                tex2 = self.kill2
                            else:
                                if self.starPowerActive and self.powerActiveColorToggle and not color == (0, 0, 0, 1):
                                    tex1 = self.btail6
                                    tex2 = self.btaile6

                                elif spNote and self.powerGainColorToggle and not color == (0, 0, 0, 1):
                                    tex1 = self.btail6
                                    tex2 = self.btaile6
                                else:
                                    if fret == n:
                                        tex1 = getattr(self, "btail" + str(n+1))
                                        tex2 = getattr(self, "btaile" + str(n+1))
                        else:
                            if tailOnly:
                                # Note let go
                                tex1 = self.tail0
                                tex2 = self.taile0
                            else:
                                if self.starPowerActive and self.powerActiveColorToggle and not color == (0, 0, 0, 1):
                                    tex1 = self.tail6
                                    tex2 = self.taile6
                                elif spNote and self.powerGainColorToggle and not color == (0, 0, 0, 1):
                                    tex1 = self.tail6
                                    tex2 = self.taile6
                                else:
                                    if fret == n:
                                        tex1 = getattr(self, "tail" + str(n+1))
                                        tex2 = getattr(self, "taile" + str(n+1))
                else:
                    if big and tailOnly:
                        if kill:
                            tex1 = self.kill1
                            tex2 = self.kill2
                        else:
                            tex1 = self.bigTail1
                            tex2 = self.bigTail2
                    else:
                        tex1 = self.tail1
                        tex2 = self.tail2

                if big and tailOnly and shaders.enable("tail"):
                    color = (color[0]*1.5, color[1]*1.5, color[2]*1.5, 1.0)
                    shaders.setVar("color", color)
                    if kill and self.killfx == 0:
                        h = shaders.getVar("height")
                        shaders.modVar("height", 0.5, 0.06/h-0.1)
                    shaders.setVar("offset", (5.0-size[1], 0.0))
                    size = (size[0]*15, size[1])

                # Render the long part of the tail
                gl.glEnable(gl.GL_TEXTURE_2D)

                if length >= self.boardLength:
                    movement1 = (project((offset * self.tailSpeed) * self.beatsPerUnit)*3) - (project(offset * self.beatsPerUnit)*3)
                    movement2 = (project(((offset * self.tailSpeed) + s) * self.beatsPerUnit)*3) - (project(offset * self.beatsPerUnit)*3)
                else:
                    movement1 = (project((offset * self.tailSpeed) * self.beatsPerUnit)*3)
                    movement2 = (project(((offset * self.tailSpeed) + s) * self.beatsPerUnit)*3)

                self.tail_tex[0][1] = self.tail_tex[1][1] = movement1
                self.tail_tex[2][1] = self.tail_tex[3][1] = movement2

                self.tail_col[0][0] = self.tail_col[1][0] = self.tail_col[2][0] = self.tail_col[3][0] = tailcol[0]
                self.tail_col[0][1] = self.tail_col[1][1] = self.tail_col[2][1] = self.tail_col[3][1] = tailcol[1]
                self.tail_col[0][2] = self.tail_col[1][2] = self.tail_col[2][2] = self.tail_col[3][2] = tailcol[2]

                self.tail_vtx[0][0] = self.tail_vtx[2][0] = -size[0]
                self.tail_vtx[1][0] = self.tail_vtx[3][0] = size[0]
                self.tail_vtx[0][2] = self.tail_vtx[1][2] = size[1]

                tex1.texture.bind()

                cmgl.drawArrays(gl.GL_TRIANGLE_STRIP, vertices=self.tail_vtx, colors=self.tail_col, texcoords=self.tail_tex)

                gl.glDisable(gl.GL_TEXTURE_2D)

                draw3Dtex(tex2, vertex=(-size[0], size[1], size[0], size[1] + .6), texcoord=(0.0, 0.0, 1.0, 1.0), color=tailcol)  # render the end of a tail

                shaders.disable()

        if tailOnly:
            return

    def renderFreeStyleTail(self, length, color, fret, pos):

        if length is not None:
            if length > self.boardLength:
                s = self.boardLength
            else:
                s = length

            # render a freestyle tail  (self.freestyle1 & self.freestyle2)
            zsize = .25

            if self.freestyleActive:
                size = (.30, s - zsize)  # was .15
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

            c1, c2, c3, c4 = color
            tailGlow = 1 - (pos - self.freestyleLastFretHitTime[fret]) / self.freestylePeriod
            if tailGlow < 0:
                tailGlow = 0
            color = (c1 + c1*2.0*tailGlow, c2 + c2*2.0*tailGlow, c3 + c3*2.0*tailGlow, c4*0.6 + c4*0.4*tailGlow)  # this fades inactive tails' color darker
            tailcol = (color)

            tex1 = self.freestyle1
            tex2 = self.freestyle2

            draw3Dtex(tex1, vertex=(-size[0], 0, size[0], size[1]), texcoord=(0.0, 0.0, 1.0, 1.0), color=tailcol)  # Middle of freestyle tail
            draw3Dtex(tex2, vertex=(-size[0], size[1], size[0], size[1] + zsize), texcoord=(0.0, 0.05, 1.0, 0.95), color=tailcol)  # end of freestyle tail
            draw3Dtex(tex2, vertex=(-size[0], 0 - zsize, size[0], 0 + (.05)), texcoord=(0.0, 0.95, 1.0, 0.05), color=tailcol)  # beginning of freestyle tail

    def renderFreestyleLanes(self, visibility, song, pos, controls):
        if not song:
            return
        if not song.readyToGo:
            return

        # check for [section big_rock_ending] to set a flag to determine how to treat the last drum fill marker note:
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
                if isinstance(event, MarkerNote):
                    if event.number == FREESTYLE_MARKING_NOTE and (not event.happened or self.bigRockEndingMarkerSeen):
                        # don't kill the BRE!
                        if self.isDrum:
                            drumFillEvents.append(event)
                        length = (event.length - 50) / self.currentPeriod / beatsPerUnit
                        w = self.boardWidth / self.strings
                        self.freestyleLength = event.length
                        self.freestyleStart = time
                        z = ((time - pos) / self.currentPeriod) / beatsPerUnit
                        z2 = ((time + event.length - pos) / self.currentPeriod) / beatsPerUnit

                        if z > self.boardLength * .8:
                            f = (self.boardLength - z) / (self.boardLength * .2)
                        elif z < 0:
                            f = min(1, max(0, 1 + z2))
                        else:
                            f = 1.0

                        time -= self.freestyleOffset
                        # allow tail to move under frets
                        if self.isDrum:
                            if time > pos:
                                self.drumFillsHits = -1
                            if self.starPower >= 50 and not self.starPowerActive:
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
                                if self.drumFillsHits < 0:
                                    self.drumFillsCount += 1
                                    self.drumFillsHits = 0

                            if z < -1.5:
                                length += z + 1.5
                                z = -1.5

                        if self.isDrum:
                            breRangeStart = 1
                        else:
                            breRangeStart = 0

                        # render freestyle tails
                        if self.freestyleReady or self.drumFillsReady:
                            for theFret in range(breRangeStart, 5):
                                x = (self.strings / 2 - breLaneOffset - theFret) * w
                                if self.isDrum and theFret == 4:
                                    c = self.fretColors[0]
                                else:
                                    c = self.fretColors[theFret]
                                color = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1.0 * visibility * f)
                                gl.glPushMatrix()
                                gl.glTranslatef(x, (1.0 - visibility) ** (theFret + 1), z)

                                self.renderFreeStyleTail(length, color, theFret, pos)
                                gl.glPopMatrix()

                        if self.isDrum and ( self.drumFillsActive and self.drumFillsHits >= 4 and z + length < self.boardLength ):
                            gl.glPushMatrix()
                            color = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1.0 * visibility * f)
                            gl.glTranslatef(x, 0.0, z + length)
                            gl.glScalef(1, 1.7, 1.3)
                            self.renderNote(length, sustain=False, color=color, tailOnly=False, isTappable=False, fret=4, spNote=False, isOpen=False, spAct=True)
                            gl.glPopMatrix()

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

        num = 0
        renderedNotes = self.getRequiredNotesForRender(song, pos)

        for time, event in renderedNotes:
            if isinstance(event, Tempo):
                self.tempoBpm = event.bpm
                continue

            if not isinstance(event, Note):
                continue

            if event.length <= 120:
                continue

            if event.noteBpm == 0.0:
                event.noteBpm = self.tempoBpm

            if self.coOpFailed:
                if self.coOpRestart:
                    if time - self.coOpRescueTime < (self.currentPeriod * self.beatsPerBoard * 2):
                        continue
                    elif self.coOpRescueTime + (self.currentPeriod * self.beatsPerBoard * 2) < pos:
                        self.coOpFailed = False
                        self.coOpRestart = False
                        log.debug("Turning off coOpFailed. Rescue successful.")
                else:
                    continue

            c = self.fretColors[event.number]

            x = (self.strings / 2 - event.number) * w
            z = ((time - pos) / self.currentPeriod) / self.beatsPerUnit
            z2 = ((time + event.length - pos) / self.currentPeriod) / self.beatsPerUnit

            if z > self.boardLength * .8:
                f = (self.boardLength - z) / (self.boardLength * .2)
            elif z < 0:
                f = min(1, max(0, 1 + z2))
            else:
                f = 1.0

            color = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1 * visibility * f)
            if event.length > 120:
                length = (event.length - 50) / self.currentPeriod / self.beatsPerUnit
            else:
                length = 0
            tailOnly = False

            # user setting for starpower refill / replenish notes
            if self.spEnabled and (event.star or event.finalStar):
                spNote = event.star
            else:
                spNote = False

            if event.tappable < 2:
                isTappable = False
            else:
                isTappable = True

            if z < 0:
                # Note past frets
                if event.played or event.hopod:
                    # note hit
                    tailOnly = True
                    length += z
                    z = 0
                    if length <= 0:
                        continue
                else:
                    # note is missed
                    if self.notedisappear == 0:
                        # Notes keep on going when missed
                        color = (.6, .6, .6, .5 * visibility * f)
                    elif self.notedisappear == 1:
                        # Notes disappear when missed
                        color = (.6, .6, .6, .5 * visibility * f)
                    if self.notedisappear == 2:
                        # turn red when missed
                        color = (1, 0, 0, 1)

            big = False
            self.bigMax = 0
            for i in range(0, self.strings):
                if self.hit[i]:
                    big = True
                    self.bigMax += 1

            if self.spEnabled and killswitch:
                if event.star or event.finalStar:
                    if big and tailOnly:
                        self.killPoints = True
                        color = (1, 1, 1, 1)

            if z + length < -1.0:
                continue

            # crop to board edge
            if z + length > self.boardLength:
                length = self.boardLength - z

            sustain = False
            if event.length > (1.4 * (60000.0 / event.noteBpm) / 4):
                sustain = True

            gl.glPushMatrix()
            gl.glTranslatef(x, (1.0 - visibility) ** (event.number + 1), z)

            if big and num < self.bigMax:
                num += 1
                self.renderTail(song, length, sustain=sustain, kill=killswitch, color=color, tailOnly=tailOnly, isTappable=isTappable, big=True, fret=event.number, spNote=spNote, pos=pos)
            else:
                self.renderTail(song, length, sustain=sustain, kill=killswitch, color=color, tailOnly=tailOnly, isTappable=isTappable, fret=event.number, spNote=spNote, pos=pos)

            gl.glPopMatrix()

            if killswitch and self.killfx == 1:
                gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
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

                    gl.glBegin(gl.GL_TRIANGLE_STRIP)
                    f1 = 0
                    while t > time:

                        if ((t-pos)*proj) < self.boardLength:
                            z = (t - pos) * proj
                        else:
                            z = self.boardLength

                        if z < 0:
                            break
                        f2 = min((s - t) / (6 * step), 1.0)
                        a1 = waveForm(t) * f1
                        a2 = waveForm(t - step) * f2
                        gl.glColor4f(c[0], c[1], c[2], .5)
                        gl.glVertex3f(x - a1, 0, z)
                        gl.glVertex3f(x - a2, 0, z - zStep)
                        gl.glColor4f(1, 1, 1, .75)
                        gl.glVertex3f(x, 0, z)
                        gl.glVertex3f(x, 0, z - zStep)
                        gl.glColor4f(c[0], c[1], c[2], .5)
                        gl.glVertex3f(x + a1, 0, z)
                        gl.glVertex3f(x + a2, 0, z - zStep)
                        gl.glVertex3f(x + a2, 0, z - zStep)
                        gl.glVertex3f(x - a2, 0, z - zStep)
                        t -= step
                        f1 = f2
                    gl.glEnd()

                gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

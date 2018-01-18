#####################################################################
# -*- coding: utf-8 -*-                                             #
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

from copy import deepcopy
import logging
import math
import os

import OpenGL.GL as gl
import numpy as np

from fofix.game.guitarscene.instruments.Instrument import Instrument
from fofix.game.guitarscene.Neck import Neck
from fofix.game.song import Note, Tempo
from fofix.core.Image import draw3Dtex
from fofix.core.Shader import shaders
from fofix.core.Mesh import Mesh
from fofix.core import cmgl


log = logging.getLogger(__name__)


class Guitar(Instrument):
    def __init__(self, engine, playerObj, scene, player = 0, bass = False):
        super(Guitar, self).__init__(engine, playerObj, scene, player=player)

        self.isDrum = False
        self.isBassGuitar = bass
        self.isVocal = False

        self.strings        = 5
        self.strings2       = 5

        self.debugMode = False
        self.gameMode2p = self.engine.world.multiMode
        self.matchingNotes = []

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            log.debug("Guitar class init...")

        self.lastPlayedNotes = []   #MFH - for reverting when game discovers it implied incorrectly

        self.missedNotes    = []

        self.freestyleHitFlameCounts = [0 for n in range(self.strings+1)]    #MFH

        self.fretWeight     = [0.0] * self.strings
        self.fretActivity   = [0.0] * self.strings

        self.drumFretButtons = None

        self.sfxVolume    = self.engine.config.get("audio", "SFX_volume")

        #blazingamer
        self.killfx = self.engine.config.get("performance", "killfx")
        self.killCount         = 0

        self.bigMax = 1

        #Get theme
        #now theme determination logic is only in data.py:
        self.theme = self.engine.data.theme

        self.oFlash = None

        self.lanenumber     = float(5)
        self.fretImgColNumber = float(3)

        #myfingershurt:
        self.bassGrooveNeckMode = self.engine.config.get("game", "bass_groove_neck")

        self.tailsEnabled = True

        self.loadImages()

        self.twoChordMax = False

        self.rockLevel = 0.0

        self.neck = Neck(self.engine, self, playerObj)

    def renderFrets(self, visibility, song, controls):
        w = self.boardWidth / self.strings
        size = (.22, .22)
        v = 1.0 - visibility

        gl.glEnable(gl.GL_DEPTH_TEST)

        for n in range(self.strings2):
            keyNumb = n
            f = self.fretWeight[keyNumb]
            c = list(self.fretColors[keyNumb])

            y = v / 6
            x = (self.strings / 2 - n) * w

            if self.twoDkeys == True or not self.keyMesh:
                fretColor = (1,1,1,1)
                size = (self.boardWidth / self.strings / 2, self.boardWidth / self.strings / 2.4)
                texSize = (n / self.lanenumber, n / self.lanenumber + 1 / self.lanenumber)

                # fret normal guitar/bass/drums
                texY = (0.0, 1.0 / self.fretImgColNumber)

                # fret press
                if controls.getState(self.keys[n]) or controls.getState(self.keys[n+5]):
                    texY = (1.0 / self.fretImgColNumber, 2.0 / self.fretImgColNumber)

                #frets on note hit
                elif self.hit[n]:
                    texY = (2.0 / self.fretImgColNumber,1.0)

                draw3Dtex(self.fretButtons, vertex = (size[0],size[1],-size[0],-size[1]), texcoord = (texSize[0], texY[0], texSize[1], texY[1]),
                                        coord = (x,v,0), multiples = True,color = fretColor, depth = True)

            else:
                self.keypos = self.engine.theme.keypos
                self.keyrot = self.engine.theme.keyrot

                if self.keytex:
                    texture = getattr(self,"keytex"+chr(97+n)).texture
                else:
                    texture = None

                c = [.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, v]
                self.render3DKey(texture,self.keyMesh, x, y, c, n, f)

        gl.glDisable(gl.GL_DEPTH_TEST)

    def renderFreestyleFlames(self, visibility, controls):
        if self.flameColors[0][0] == -1:
            return

        w = self.boardWidth / self.strings

        v = 1.0 - visibility


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

                    flameSize = self.hitFlameSize
                    if self.theme == 0 or self.theme == 1: #THIS SETS UP GH3 COLOR, ELSE ROCKBAND(which is DEFAULT in Theme.py)
                        flameColor = self.gh3flameColor
                    else: #MFH - fixing crash!
                        flameColor = self.fretColors[fretNum]
                    if flameColor[0] == -2:
                        flameColor = self.fretColors[fretNum]

                    ff += 1.5 #ff first time is 2.75 after this

                    if self.freestyleHitFlameCounts[fretNum] < flameLimitHalf:
                        flamecol = tuple([flameColor[ifc] for ifc in range(3)])
                        rbStarColor = (.1, .1, .2, .3)
                        xOffset = (.0, - .005, .005, .0)
                        yOffset = (.20, .255, .255, .255)
                        scaleMod = .6 * ms * ff
                        scaleFix = (6.0, 5.5, 5.0, 4.7)
                        for step in range(4):
                            if self.starPowerActive and self.theme < 2:
                                flamecol = self.spColor
                            else: #Default starcolor (Rockband)
                                flamecol = (rbStarColor[step],)*3
                            hfCount = self.freestyleHitFlameCounts[fretNum]
                            if step == 0:
                                hfCount += 1
                            if self.disableFlameSFX != True:
                                draw3Dtex(self.hitflames2Drawing, coord = (x+xOffset[step], y+yOffset[step], 0), rot = (90, 1, 0, 0),
                                                    scale = (.25 + .05 * step + scaleMod, hfCount/scaleFix[step] + scaleMod, hfCount/scaleFix[step] + scaleMod),
                                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                                    texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)

                    else:
                        flameColorMod = 0.1 * (flameLimit - self.freestyleHitFlameCounts[fretNum])
                        flamecol = tuple([flameColor[ifc]*flameColorMod for ifc in range(3)])
                        xOffset = (.0, - .005, .005, .005)
                        yOffset = (.35, .405, .355, .355)
                        scaleMod = .6 * ms * ff
                        scaleFix = (3.0, 2.5, 2.0, 1.7)
                        for step in range(4):
                            hfCount = self.freestyleHitFlameCounts[fretNum]
                            if step == 0:
                                hfCount += 1
                            else:
                                if self.starPowerActive and self.theme < 2:
                                    flamecol = self.spColor
                                else: #Default starcolor (Rockband)
                                    flamecol = (.4+.1*step,)*3
                            if self.disableFlameSFX != True:
                                draw3Dtex(self.hitflames1Drawing, coord = (x+xOffset[step], y+yOffset[step], 0), rot = (90, 1, 0, 0),
                                                    scale = (.25 + .05 * step + scaleMod, hfCount/scaleFix[step] + scaleMod, hfCount/scaleFix[step] + scaleMod),
                                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                                    texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)

                    self.freestyleHitFlameCounts[fretNum] += 1

                else:   #MFH - flame count is done - reset it!
                    self.freestyleHitFlameCounts[fretNum] = 0    #MFH

    def render(self, visibility, song, pos, controls, killswitch):

        if shaders.turnon:
            shaders.globals["dfActive"] = self.drumFillsActive
            shaders.globals["breActive"] = self.freestyleActive
            shaders.globals["rockLevel"] = self.rockLevel
            if shaders.globals["killswitch"] != killswitch:
                shaders.globals["killswitchPos"] = pos
            shaders.globals["killswitch"] = killswitch
            shaders.modVar("height",0.2,0.2,1.0,"tail")


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
                    if time == q:   #MFH - no need to mark only the final SP phrase note as the finalStar as in drums, they will be hit simultaneously here.
                        event.finalStar = True
            self.starNotesSet = True

        if not (self.coOpFailed and not self.coOpRestart):
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
            gl.glEnable(gl.GL_COLOR_MATERIAL)

            if self.leftyMode:
                gl.glScalef(-1, 1, 1)

            if self.freestyleActive:
                self.renderFreestyleLanes(visibility, song, pos, None) #MFH - render the lanes on top of the notes.
                self.renderFrets(visibility, song, controls)

                self.renderFreestyleFlames(visibility, controls)    #MFH - freestyle hit flames

            else:
                self.renderTails(visibility, song, pos, killswitch)
                if self.fretsUnderNotes:  #MFH
                    if self.twoDnote == True:
                        self.renderFrets(visibility, song, controls)
                        self.renderNotes(visibility, song, pos)
                    else:
                        self.renderNotes(visibility, song, pos)
                        self.renderFrets(visibility, song, controls)
                else:
                    self.renderNotes(visibility, song, pos)
                    self.renderFrets(visibility, song, controls)

                self.renderFreestyleLanes(visibility, song, pos, None) #MFH - render the lanes on top of the notes.


                self.renderHitGlow()
                self.renderHitTrails(controls)
                self.renderAnimatedFlames(song, pos)
                self.renderFlames(song, pos)    #MFH - only when freestyle inactive!

            if self.leftyMode:
                gl.glScalef(-1, 1, 1)

    def controlsMatchNotes3(self, controls, notes, hopo = False):


        def matchNotes(chordTuple, requiredKeys):
            if len(chordTuple) > 1: #Chords must match exactly
                for n in range(self.strings):
                    if (n in requiredKeys and not (controls.getState(self.keys[n]) or controls.getState(self.keys[n+5]))) or (n not in requiredKeys and (controls.getState(self.keys[n]) or controls.getState(self.keys[n+5]))):
                        return False
            else: #Single Note must match that note
                requiredKey = requiredKeys[0]
                if not controls.getState(self.keys[requiredKey]) and not controls.getState(self.keys[requiredKey+5]):
                    return False

                # Check for higher numbered frets
                for n, k in enumerate(self.keys):
                    if (n > requiredKey and n < 5) or (n > 4 and n > requiredKey + 5):
                    #higher numbered frets cannot be held
                        if controls.getState(k):
                            return False
            return True

        # no notes?
        if not notes:
            return False

        # check each valid chord
        chords = {}
        for time, note in notes:
            if note.hopod == True and (controls.getState(self.keys[note.number]) or controls.getState(self.keys[note.number + 5])):
                self.playedNotes = []
                return True
            if not time in chords:
                chords[time] = []
            chords[time].append((time, note))

        #Make sure the notes are in the right time order
        chordlist = chords.values()
        chordlist.sort(key=lambda a: a[0][0])

        self.missedNotes = []
        twochord = 0

        for chord in chordlist:
            # matching keys?
            requiredKeys = self.uniqify([note.number for time, note in chord])

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

            if (matchNotes(chord, requiredKeys)):
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

        for chord in self.missedNotes:
            for time, note in chord:
                note.skipped = True
                note.played = False
        if twochord == 2:
            self.twoChord += skipped

        return True

    def uniqify(self, seq):
        result = []
        for marker in seq:
            if marker in result:
                continue
            result.append(marker)
        return result


    def startPick3(self, song, pos, controls, hopo = False):
        if not song:
            return False
        if not song.readyToGo:
            return False

        self.lastPlayedNotes = self.playedNotes
        self.playedNotes = []

        self.controlsMatchNotes3(controls, self.matchingNotes, hopo=hopo)

        #myfingershurt

        for time, note in self.matchingNotes:
            if note.played != True:
                continue

            self.pickStartPos = max(pos, time)

            if shaders.turnon:
                shaders.var["fret"][self.player][note.number]=shaders.time()
                shaders.var["fretpos"][self.player][note.number]=pos

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
                    else:
                        self.LastStrumWasChord = False
                lastPlayedNote = note

        elif len(self.playedNotes) > 0: #ensure at least that a note was played here
            self.LastStrumWasChord = False

        if len(self.playedNotes) != 0:
            return True
        return False

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

    def getPickLength(self, pos):
        if not self.playedNotes:
            return 0.0

        # The pick length is limited by the played notes
        pickLength = pos - self.pickStartPos
        for time, note in self.playedNotes:
            pickLength = min(pickLength, note.length)
        return pickLength

    def run(self, ticks, pos, controls):

        if not self.paused:
            self.time += ticks

        self.matchingNotes = self.getRequiredNotes(self.scene.song, pos)

        #MFH - Determine which frame to display for starpower notes
        if self.noteSpin:
            self.indexCount = self.indexCount + 1
            if self.indexCount > self.Animspeed-1:
                self.indexCount = 0
            self.noteSpinFrameIndex = (self.indexCount * self.noteSpinFrames - (self.indexCount * self.noteSpinFrames) % self.Animspeed) / self.Animspeed
            if self.noteSpinFrameIndex > self.noteSpinFrames - 1:
                self.noteSpinFrameIndex = 0

        #myfingershurt: must not decrease SP if paused.
        if self.starPowerActive == True and self.paused == False:
            self.starPower -= ticks/self.starPowerDecreaseDivisor
            if self.starPower <= 0:
                self.starPower = 0
                self.starPowerActive = False
                self.engine.data.starDeActivateSound.play()

        activeFrets = [note.number for time, note in self.playedNotes]

        for n in range(self.strings):
            if controls.getState(self.keys[n]) or controls.getState(self.keys[n+5]):
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

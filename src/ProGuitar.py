#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2011 nhydock(Blazingamer)                           #
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
from Guitar import Guitar
from Mesh import Mesh
import random
import os
from Shader import shaders
import Log

from OpenGL.GL import *

class ProGuitar(Guitar):
    def __init__(self, engine, playerObj, editorMode = False, player = 0, bass = False):
        super(ProGuitar, self).__init__(engine, playerObj, player = player, bass = bass)

        self.strings        = 6

    def loadNotes(self):
        engine = self.engine

        get = lambda file: self.checkPath(os.path.join("notes", "pro"), file)

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

                if self.gameMode2p == 6: #battle multiplayer
                    if engine.loadImgDrawing(self, "noteButtons", get("spinnotesbattle.png")):
                        self.starSpinFrames = 8

            if self.gameMode2p == 6: #battle multiplayer
                if not self.engine.loadImgDrawing(self, "noteButtons", get("notesbattle.png")):
                    engine.loadImgDrawing(self, "noteButtons", get("notes.png"))
            else:
                engine.loadImgDrawing(self, "noteButtons", get("notes.png"))

            #if special notes for pro aren't found then it will need to
            #draw using font the number of the fret over the note
            self.proNum = engine.loadImgDrawing(self, "fretNumbers", get("fretNumbers.png"))
        else:

            #Pro instruments must have a specially made note file if it's going to use
            #3d just so it can display the fret number, if it does not then it needs to
            #fall back to 2d
            if self.engine.fileExists(get("note.dae")): #look in the notes folder for files
                self.engine.resource.load(self,  "noteMesh",  lambda: Mesh(engine.resource.fileName(get("note.dae"))))
            else: #default to files in data folder
                self.twoDnote = True
                self.loadNotes()
                return

            if self.engine.fileExists(get("star.dae")): #look in the notes folder for files
                self.engine.resource.load(self,  "starMesh",  lambda: Mesh(self.engine.resource.fileName(get("star.dae"))))
            else: #No mesh for star notes
                self.twoDnote = True
                self.loadNotes()
                return

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

                #these are necessary, if they don't exist then you can't use 3d notes
                for i in range(13):
                    if not self.engine.loadImgDrawing(self,  "fretnumtex" + str(i),  get("fretnumtex_"+str(i)+".png")):
                        self.twoDnote = True
                        self.loadNotes()
                        return

    def renderNote(self, length, sustain, color, tailOnly = False, isTappable = False, string = 0, fret = 0, spNote = False, spAct = False):

        if tailOnly:
            return

        #myfingershurt: this should be retrieved once at init, not repeatedly in-game whenever tails are rendered.

        if self.twoDnote == True:

            noteImage = self.noteButtons

            tailOnly = True


            size = (self.boardWidth/self.strings/2, self.boardWidth/self.strings/2)
            texSize = (string/float(self.strings),(string+1)/float(self.strings))
            if spNote == True:
                if isTappable:
                    if self.noteAnimatedPowerHOPO:
                        noteImage = self.noteAnimatedPowerHOPO
                        texY = (self.noteSpinFrameIndex*.066667, (self.noteSpinFrameIndex - 1)*.066667)
                    else:
                        texY = (.5, 2.0/3.0)
                else:
                    if self.noteAnimatedPower:
                        noteImage = self.noteAnimatedPower
                        texY = (self.noteSpinFrameIndex*.066667, (self.noteSpinFrameIndex - 1)*.066667)
                    else:
                        texY = (1.0/3.0, .5)
            elif self.starPowerActive:
                if isTappable:
                    if self.noteAnimatedPowerActiveHOPO:
                        noteImage = self.noteAnimatedPowerActiveHOPO
                        texY = (self.noteSpinFrameIndex*.066667, (self.noteSpinFrameIndex - 1)*.066667)
                    else:
                        texY = (5.0/6.0, 1)
                else:
                    if self.noteAnimatedPowerActive:
                        noteImage = self.noteAnimatedPowerActive
                        texY = (self.noteSpinFrameIndex*.066667, (self.noteSpinFrameIndex - 1)*.066667)
                    else:
                        texY = (2.0/3.0, 5.0/6.0)

            else:
                if isTappable:
                    if self.noteAnimatedHOPO:
                        noteImage = self.noteAnimatedHOPO
                        texY = (self.noteSpinFrameIndex*.066667, (self.noteSpinFrameIndex - 1)*.066667)
                    else:
                        texY = (1.0/6.0, 1.0/3.0)
                else:
                    if self.noteAnimatedNormal:
                        noteImage = self.noteAnimatedNormal
                        texY = (self.noteSpinFrameIndex*.066667, (self.noteSpinFrameIndex - 1)*.066667)
                    else:
                        texY = (0, 1.0/6.0)

            self.engine.draw3Dtex(noteImage, vertex = (-size[0],size[1],size[0],-size[1]), texcoord = (texSize[0],texY[0],texSize[1],texY[1]),
                                  scale = (1,1,0), rot = (30,1,0,0), multiples = False, color = color, vertscale = .27)

            #draws the fret number over the note
            texSize = (string/self.lanenumber,string/self.lanenumber+1/self.lanenumber)
            texY = (fret/13.0, (fret+1)/13.0)
            self.engine.draw3Dtex(self.fretNumbers, vertex = (-size[0],size[1],size[0],-size[1]),
                                  texcoord = (texSize[0],texY[0],texSize[1],texY[1]),
                                  scale = (1,1,0), rot = (30,1,0,0), multiples = False, color = color, vertscale = .27)

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

        self.starNotesInView = False
        self.openStarNotesInView = False

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

            x  = (self.strings / 2 - (event.number)) * w
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
                if time > self.freestyleStart - self.freestyleOffset and time < self.freestyleStart + self.freestyleOffset + self.freestyleLength:
                    z = -2.0

            if self.twoDnote == True and not self.useFretColors:
                color      = (1,1,1, 1 * visibility * f)
            else:
                color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1 * visibility * f)

            if event.length > 120:
                length     = (event.length - 50) / self.currentPeriod / self.beatsPerUnit
            else:
                length     = 0

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


            if event.tappable < 2:
                isTappable = False
            else:
                isTappable = True


            if (event.played or event.hopod): #if the note is hit
                continue

            elif z < 0: #Notes past frets
                #if none of the below they keep on going, it would be self.notedisappear == 1
                if self.notedisappear == 0: #Notes disappear
                    continue

                elif self.notedisappear == 2: #Notes turn red
                    color = (1, 0, 0, 1)#turn note red


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
                self.renderNote(length, sustain = sustain, color = color, tailOnly = tailOnly, isTappable = isTappable, string = event.lane, fret = event.number, spNote = spNote)
            glPopMatrix()

        #myfingershurt: end FOR loop / note rendering loop
        if (not self.openStarNotesInView) and (not self.starNotesInView) and self.finalStarSeen:
            self.spEnabled = True
            self.isStarPhrase = False
            self.finalStarSeen = False

#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyostila                                  #
#               2008 Alarian                                        #
#               2008 myfingershurt                                  #
#               2008 Glorandwarf                                    #
#               2008 Capo                                           #
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

#altered by myfingershurt to adapt to Alarian mod

from Song import Note, Tempo
from Neck import Neck
from Shader import shaders

from OpenGL.GL import *
import math

#myfingershurt: needed for multi-OS file fetching
import os
import Log
import Song   #need the base song defines as well

#Normal guitar key color order: Green, Red, Yellow, Blue, Orange
#Drum fret color order: Red, Yellow, Blue, Green
#actual drum note numbers:
#0 = bass drum (stretched Orange fret), normally Green fret
#1 = drum Red fret, normally Red fret
#2 = drum Yellow fret, normally Yellow fret
#3 = drum Blue fret, normally Blue fret
#4 = drum Green fret, normally Orange fret
#
#So, with regard to note number coloring, swap note.number 0's color with note.number 4.

#akedrou - 5-drum support is now available.
# to enable it, only here and Player.drums should need changing.


from Instrument import *

class Drum(Instrument):
  def __init__(self, engine, playerObj, editorMode = False, player = 0):
    Instrument.__init__(self, engine, playerObj, player)

    self.isDrum = True
    self.isBassGuitar = False
    self.isVocal = False

    self.drumsHeldDown = [0, 0, 0, 0, 0]

    self.gameMode2p = self.engine.world.multiMode

    self.lastFretWasBassDrum = False
    self.lastFretWasT1 = False   #Faaa Drum sound
    self.lastFretWasT2 = False
    self.lastFretWasT3 = False
    self.lastFretWasC = False


    self.matchingNotes = None

    #MFH - I do not understand fully how the handicap scorecard works at the moment, nor do I have the time to figure it out.
    #... so for now, I'm just writing some extra code here for the early hitwindow size handicap.
    self.earlyHitWindowSizeFactor = 0.5

    self.starNotesInView = False
    self.openStarNotesInView = False

    self.drumFillsCount = 0
    self.drumFillsTotal = 0
    self.drumFillsHits = 0
    self.drumFillsReady = False

    self.drumFillEvents = []
    self.drumFillWasJustActive = False

    self.strings        = 4
    self.playedSound  = [True, True, True, True, True]

    self.openFretActivity = 0.0
    self.openFretColor  = self.fretColors[5]

    self.editorMode     = editorMode

    self.lanenumber     = float(4)
    self.fretImgColNumber = float(6)

    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("Drum class initialization!")


    self.freestyleHitFlameCounts = [0 for n in range(self.strings+1)]    #MFH

    self.fretWeight     = [0.0] * self.strings
    self.fretActivity   = [0.0] * self.strings

    #myfingershurt:
    self.hopoStyle = 0    

    if self.theme < 2:    #make board same size as guitar board if GH based theme so it rockmeters dont interfere
      self.boardWidth     = 3.0
      self.boardLength    = 9.0

    #blazingamer
    self.opencolor = self.fretColors[5]
    self.rockLevel = 0.0

    self.bigMax = 1

    if self.engine.config.get("game", "large_drum_neck"):
      self.boardWidth     *= (4.0/3.0)
      self.boardLength    *= (4.0/3.0)
    
    #Get theme
    themename = self.engine.data.themeLabel
    #now theme determination logic is only in data.py:
    self.theme = self.engine.data.theme

    self.tailsEnabled = False

    self.loadFrets()
    self.loadNotes()
    self.loadTails()

    self.barsColor = self.engine.theme.barsColor

    self.neck = Neck(self.engine, self, playerObj)

  #volshebnyi
  def renderFreestyleLanes(self, visibility, song, pos, controls):
    if not song:
      return
    if not song.readyToGo:
      return


    #MFH - check for [section big_rock_ending] to set a flag to determine how to treat the last drum fill marker note:
    if song.breMarkerTime and pos > song.breMarkerTime:
      self.bigRockEndingMarkerSeen = True




    boardWindowMax = pos + self.currentPeriod * self.beatsPerBoard
    track = song.midiEventTrack[self.player]
    beatsPerUnit = self.beatsPerBoard / self.boardLength
    if self.freestyleEnabled:
      freestyleActive = False
      self.drumFillsActive = False
      drumFillEvents = []
      for time, event in track.getEvents(pos - self.freestyleOffset, boardWindowMax + self.freestyleOffset):
        if isinstance(event, Song.MarkerNote):
          if event.number == Song.freestyleMarkingNote and (not event.happened or self.bigRockEndingMarkerSeen):  #MFH - don't kill the BRE!
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
            if time > pos:
              self.drumFillsHits = -1
            if self.starPower>=50 and not self.starPowerActive:
              self.drumFillsReady = True

            else:
              self.drumFillsReady = False
            if self.bigRockEndingMarkerSeen: # and ( (self.drumFillsCount == self.drumFillsTotal and time+event.length>pos) or (time > pos and self.drumFillsCount == self.drumFillsTotal-1) ):
              self.freestyleReady = True
              self.drumFillsReady = False
            else:
              self.freestyleReady = False
            if time < pos:
              if self.bigRockEndingMarkerSeen:  # and self.drumFillsCount == self.drumFillsTotal:
                freestyleActive = True
              else:
                if self.drumFillsReady:
                  self.drumFillsActive = True
                  self.drumFillWasJustActive = True
                if self.drumFillsHits<0:
                  self.drumFillsCount += 1
                  self.drumFillsHits = 0

              if z < -1.5:
                length += z +1.5
                z =  -1.5

            #volshebnyi - render 4 freestyle tails
            if self.freestyleReady or self.drumFillsReady:
              for theFret in range(1,5):
                x = (self.strings / 2 + .5 - theFret) * w
                if theFret == 4:
                  c = self.fretColors[0]
                else:
                  c = self.fretColors[theFret]
                color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1.0 * visibility * f)
                glPushMatrix()
                glTranslatef(x, (1.0 - visibility) ** (theFret + 1), z)
                freestyleTailMode = 1

                self.renderTail(length = length, color = color, fret = theFret, freestyleTail = freestyleTailMode, pos = pos)
                glPopMatrix()


            if ( self.drumFillsActive and self.drumFillsHits >= 4 and z + length<self.boardLength ):
              glPushMatrix()
              color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1.0 * visibility * f)
              glTranslatef(x, 0.0, z + length)
              glScalef(1,1.7,1.3)
              self.renderNote(length, sustain = False, color = color, flat = False, tailOnly = False, isTappable = False, fret = 4, spNote = False, isOpen = False, spAct = True)
              glPopMatrix()

      self.freestyleActive = freestyleActive
      self.drumFillEvents = drumFillEvents


  def renderTail(self, length, color, flat = False, fret = 0, freestyleTail = 0, pos = 0):

    beatsPerUnit = self.beatsPerBoard / self.boardLength

    if flat:
      tailscale = (1, .1, 1)
    else:
      tailscale = None

    size = (.08, length + 0.00001)

    if size[1] > self.boardLength:
      s = self.boardLength
    else:
      s = (length + 0.00001)

    # render an inactive freestyle tail  (self.freestyle1 & self.freestyle2)
    zsize = .25  
    size = (.15, s - zsize)

    if self.drumFillsActive:
      if self.drumFillsHits >= 4:
        size = (.30, s - zsize)
      if self.drumFillsHits >= 3:
        size = (.25, s - zsize)
      elif self.drumFillsHits >= 2:
        size = (.21, s - zsize)
      elif self.drumFillsHits >= 1:
        size = (.17, s - zsize)

    if self.freestyleActive:
      size = (.30, s - zsize)


    tex1 = self.freestyle1
    if self.freestyle2:
      tex2 = self.freestyle2
    elif not self.freestyle2:
      tex2 = None
    if freestyleTail == 1:
      c1, c2, c3, c4 = color
      tailGlow = 1 - (pos - self.freestyleLastFretHitTime[fret] ) / self.freestylePeriod
      if tailGlow < 0:
        tailGlow = 0
      color = (c1 + c1*2.0*tailGlow, c2 + c2*2.0*tailGlow, c3 + c3*2.0*tailGlow, c4*0.6 + c4*0.4*tailGlow)    #MFH - this fades inactive tails' color darker                   

    tailcol = (color)

    self.engine.draw3Dtex(tex1, vertex = (-size[0], 0, size[0], size[1]), texcoord = (0.0, 0.0, 1.0, 1.0),
                          scale = tailscale, color = tailcol)
    if tex2:
      self.engine.draw3Dtex(tex2, vertex = (-size[0], size[1] - (.05), size[0], size[1] + (zsize)),
                            scale = tailscale, texcoord = (0.0, 0.05, 1.0, 0.95), color = tailcol)
    if tex2:
      self.engine.draw3Dtex(tex2, vertex = (-size[0], 0-(zsize), size[0], 0 + (.05)),
                            scale = tailscale, texcoord = (0.0, 0.95, 1.0, 0.05), color = tailcol)





  def renderFlames(self, visibility, song, pos, controls):
    if not song or self.flameColors[0][0][0] == -1:
      return

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    w = self.boardWidth / self.strings
    track = song.track[self.player]

    size = (.22, .22)
    v = 1.0 - visibility


    flameLimit = 10.0
    flameLimitHalf = round(flameLimit/2.0)
    for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard):
      if isinstance(event, Tempo):
        continue

      if not isinstance(event, Note):
        continue

      if (event.played or event.hopod) and event.flameCount < flameLimit:
        ms = math.sin(self.time) * .25 + 1

        if event.number == 0:
          x  = (self.strings / 2 - 2) * w
        else:
          x  = (self.strings / 2 +.5 - event.number) * w

        xlightning = (self.strings / 2 - event.number)*2.2*w
        ff = 1 + 0.25       
        y = v + ff / 6

        if self.theme == 2:
          y -= 0.5

        flameSize = self.flameSizes[self.scoreMultiplier - 1][event.number]
        if self.theme == 0 or self.theme == 1: #THIS SETS UP GH3 COLOR, ELSE ROCKBAND(which is DEFAULT in Theme.py)
          flameColor = self.gh3flameColor
        else:
          flameColor = self.flameColors[self.scoreMultiplier - 1][event.number]
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
            if self.disableFlameSFX != True:
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
              else:
                flamecol = (.4,.4,.4)#Default starcolor (Rockband)
            if self.theme != 2 and event.finalStar and self.spEnabled:
              wid, hei, = self.engine.view.geometry[2:4]
              self.engine.draw3Dtex(self.hitlightning, coord = (xlightning, y, 3.3), rot = (90, 1, 0, 0),
                                    scale = (.15 + .5 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, 2), vertex = (.4,-2,-.4,2),
                                    texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = (1,1,1))
            else:
              if self.disableFlameSFX != True:
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
              else: #Default starcolor (Rockband)
                flamecol = (.5,.5,.5)
            if self.disableFlameSFX != True:
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
              else: #Default starcolor (Rockband)
                flamecol = (.6,.6,.6)
            if self.disableFlameSFX != True:
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
              else: #Default starcolor (Rockband)
                flamecol = (.7,.7,.7)
            if self.disableFlameSFX != True:
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
              else: #Default starcolor (Rockband)
                flamecol = (.1,.1,.1)
            if self.disableFlameSFX != True:
              self.engine.draw3Dtex(self.hitflames2Drawing, coord = (x, y + .20, 0), rot = (90, 1, 0, 0),
                                    scale = (.25 + .6 * ms * ff, event.flameCount/6.0 + .6 * ms * ff, event.flameCount / 6.0 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                    multiples = True, alpha = True, color = flamecol)

            flamecol = (flameColor[0], flameColor[1], flameColor[2])
            spcolmod = (.4,.4,.4)
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                flamecol = (self.spColor[0]*spcolmod[0], self.spColor[1]*spcolmod[1], self.spColor[2]*spcolmod[2])
              else: #Default starcolor (Rockband)
                flamecol = (.1,.1,.1)
            if self.disableFlameSFX != True:
              self.engine.draw3Dtex(self.hitflames2Drawing, coord = (x-.005, y + .255, 0), rot = (90, 1, 0, 0),
                                    scale = (.30 + .6 * ms * ff, event.flameCount/5.5 + .6 * ms * ff, event.flameCount / 5.5 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                    multiples = True, alpha = True, color = flamecol)

            flamecol = (flameColor[0], flameColor[1], flameColor[2])
            spcolmod = (.5,.5,.5)
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                flamecol = (self.spColor[0]*spcolmod[0], self.spColor[1]*spcolmod[1], self.spColor[2]*spcolmod[2])
              else: #Default starcolor (Rockband)
                flamecol = (.2,.2,.2)
            if self.disableFlameSFX != True:
              self.engine.draw3Dtex(self.hitflames2Drawing, coord = (x+.005, y+.255, 0), rot = (90, 1, 0, 0),
                                    scale = (.35 + .6 * ms * ff, event.flameCount/5.0 + .6 * ms * ff, event.flameCount / 5.0 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                    multiples = True, alpha = True, color = flamecol)

            flamecol = (flameColor[0], flameColor[1], flameColor[2])
            spcolmod = (.6,.6,.6)
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                flamecol = (self.spColor[0]*spcolmod[0], self.spColor[1]*spcolmod[1], self.spColor[2]*spcolmod[2])
              else: #Default starcolor (Rockband)
                flamecol = (.3,.3,.3)
            if self.disableFlameSFX != True:
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
              else:
                flamecol = (.4,.4,.4)#Default starcolor (Rockband)
            if self.theme != 2 and event.finalStar and self.spEnabled:
              wid, hei, = self.engine.view.geometry[2:4]
              self.engine.draw3Dtex(self.hitlightning, coord = (xlightning, y, 3.3), rot = (90, 1, 0, 0),
                                    scale = (.15 + .5 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, 2), vertex = (.4,-2,-.4,2),
                                    texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = (1,1,1))
            else:
              if self.disableFlameSFX != True:
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
              else: #Default starcolor (Rockband)
                flamecol = (.5,.5,.5)
            if self.disableFlameSFX != True:
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
              else: #Default starcolor (Rockband)
                flamecol = (.6,.6,.6)
            if self.disableFlameSFX != True:
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
              else: #Default starcolor (Rockband)
                flamecol = (.7,.7,.7)
            if self.disableFlameSFX != True:
              self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x+.005, y +.35 +.005, 0), rot = (90, 1, 0, 0),
                                    scale = (.40 + .6 * ms * ff, (event.flameCount + 1) / 1.7 + .6 * ms * ff, (event.flameCount + 1) / 1.7 + .6 * ms * ff),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff), texcoord = (0.0,0.0,1.0,1.0),
                                    multiples = True, alpha = True, color = flamecol)
        event.flameCount += 1




  def renderFreestyleFlames(self, visibility, controls):
    if self.flameColors[0][0][0] == -1:
      return

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    w = self.boardWidth / self.strings

    size = (.22, .22)
    v = 1.0 - visibility


    flameLimit = 10.0
    flameLimitHalf = round(flameLimit/2.0)
    for fretNum in range(self.strings+1):   #need to add 1 to string count to check this correctly (bass drum doesnt count as a string)
      #MFH - must include secondary drum keys here
      if controls.getState(self.keys[fretNum]) or controls.getState(self.keys[fretNum+5]):

        if self.freestyleHitFlameCounts[fretNum] < flameLimit:
          ms = math.sin(self.time) * .25 + 1

          if fretNum == 0:
            x  = (self.strings / 2 - 2) * w
          else:
            x  = (self.strings / 2 +.5 - fretNum) * w

          xlightning = (self.strings / 2 - fretNum)*2.2*w
          ff = 1 + 0.25       
          y = v + ff / 6
          glBlendFunc(GL_ONE, GL_ONE)

          if self.theme == 2:
            y -= 0.5

          flameSize = self.flameSizes[self.cappedScoreMult - 1][fretNum]
          if self.theme == 0 or self.theme == 1: #THIS SETS UP GH3 COLOR, ELSE ROCKBAND(which is DEFAULT in Theme.py)
            flameColor = self.gh3flameColor
          else: #MFH - fixing crash!
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
            if self.disableFlameSFX != True:
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
            if self.disableFlameSFX != True:
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
            if self.disableFlameSFX != True:
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
            if self.disableFlameSFX != True:
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
            if self.disableFlameSFX != True:
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
            if self.disableFlameSFX != True:
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
            if self.disableFlameSFX != True:
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
            if self.disableFlameSFX != True:
              self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x + .005, y + .35 + .005, 0), rot = (90, 1, 0, 0),
                                    scale = (.40 + .6 * ms * ff, (self.freestyleHitFlameCounts[fretNum] + 1) / 1.7 + .6 * ms * ff, (self.freestyleHitFlameCounts[fretNum] + 1) / 1.7 + .6 * ms * ff),
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
          if time == q and not event.finalStar:
            event.star = True
      self.starNotesSet = True
    if not (self.coOpFailed and not self.coOpRestart):
      glEnable(GL_BLEND)
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
      glEnable(GL_COLOR_MATERIAL)

      if self.freestyleActive or self.drumFillsActive:
        self.renderOpenNotes(visibility, song, pos)
        self.renderNotes(visibility, song, pos)
        self.renderFreestyleLanes(visibility, song, pos, controls) #MFH - render the lanes on top of the notes.
        self.renderFrets(visibility, song, controls)

        if self.hitFlamesPresent: #MFH - only when present!
          self.renderFreestyleFlames(visibility, controls)    #MFH - freestyle hit flames

      else:

        self.renderFreestyleLanes(visibility, song, pos, controls)

        if self.fretsUnderNotes and self.twoDnote != False:    #MFH
          self.renderFrets(visibility, song, controls)
          self.renderOpenNotes(visibility, song, pos)
          self.renderNotes(visibility, song, pos)
        else:
          self.renderOpenNotes(visibility, song, pos)
          self.renderNotes(visibility, song, pos)
          self.renderFrets(visibility, song, controls)

        if self.hitFlamesPresent: #MFH - only when present!
          self.renderFlames(visibility, song, pos, controls)    #MFH - only when freestyle inactive!


  def playDrumSounds(self, controls, playBassDrumOnly = False):   #MFH - handles playing of drum sounds.  
    #Returns list of drums that were just hit (including logic for detecting a held bass pedal)
    #pass playBassDrumOnly = True (optional paramater) to only play the bass drum sound, but still
    #  return a list of drums just hit (intelligently play the bass drum if it's held down during gameplay)
    drumsJustHit = [False, False, False, False, False]

    for i in range (5):
      if controls.getState(self.keys[i]) or controls.getState(self.keys[5+i]):
        if i == 0:
          if self.playedSound[i] == False:  #MFH - gotta check if bass drum pedal is just held down!
            self.engine.data.bassDrumSound.play()
            self.playedSound[i] = True
            drumsJustHit[0] = True
            if self.fretboardHop < 0.04:
              self.fretboardHop = 0.04  #stump
        if i == 1:
          if not playBassDrumOnly and self.playedSound[i] == False:
            self.engine.data.T1DrumSound.play()
          self.playedSound[i] = True
          drumsJustHit[i] = True
        if i == 2:
          if not playBassDrumOnly and self.playedSound[i] == False:
            self.engine.data.T2DrumSound.play()
          self.playedSound[i] = True
          drumsJustHit[i] = True
        if i == 3:
          if not playBassDrumOnly and self.playedSound[i] == False:
            self.engine.data.T3DrumSound.play()
          self.playedSound[i] = True
          drumsJustHit[i] = True
        if i == 4:   #MFH - must actually activate starpower!
          if not playBassDrumOnly and self.playedSound[i] == False:
            self.engine.data.CDrumSound.play()
          self.playedSound[i] = True
          drumsJustHit[i] = True

    return drumsJustHit


  #volshebnyi - handle freestyle picks here
  def freestylePick(self, song, pos, controls):
    drumsJustHit = self.playDrumSounds(controls)
    numHits = 0
    for i, drumHit in enumerate(drumsJustHit):
      if drumHit:
        numHits += 1
        if i == 4:
          if not self.bigRockEndingMarkerSeen and (self.drumFillsActive or self.drumFillWasJustActive) and self.drumFillsHits >= 4 and not self.starPowerActive:
            drumFillCymbalPos = self.freestyleStart+self.freestyleLength
            minDrumFillCymbalHitTime = drumFillCymbalPos - self.earlyMargin
            maxDrumFillCymbalHitTime = drumFillCymbalPos + self.lateMargin
            if (pos >= minDrumFillCymbalHitTime) and (pos <= maxDrumFillCymbalHitTime):
              self.freestyleSP = True

    return numHits


  def startPick(self, song, pos, controls, hopo = False):
    if not song:
      return False
    if not song.readyToGo:
      return

    self.matchingNotes = self.getRequiredNotesMFH(song, pos)    #MFH - ignore skipped notes please!


    # no self.matchingNotes?
    if not self.matchingNotes:
      return False
    self.playedNotes = []
    self.pickStartPos = pos

    #adding bass drum hit every bass fret:

    for time, note in self.matchingNotes:
      for i in range(5):
        if note.number == i and (controls.getState(self.keys[i]) or controls.getState(self.keys[i+5])) and self.drumsHeldDown[i] > 0:
          if self.guitarSolo:
            self.currentGuitarSoloHitNotes += 1
          if i == 0 and self.fretboardHop < 0.07:
            self.fretboardHop = 0.07  #stump

          if shaders.turnon:
            shaders.var["fret"][self.player][note.number]=shaders.time()
            shaders.var["fretpos"][self.player][note.number]=pos

          return self.hitNote(time, note)  



    return False

  def run(self, ticks, pos, controls):
    if not self.paused:
      self.time += ticks

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
    
    for i in range(len(self.drumsHeldDown)):
      if self.drumsHeldDown[i] > 0:
        self.drumsHeldDown[i] -= ticks
        if self.drumsHeldDown[i] < 0:
          self.drumsHeldDown[i] = 0

    activeFrets = [(note.number - 1) for time, note in self.playedNotes]

    
    if -1 in activeFrets:
      self.openFretActivity = min(self.openFretActivity + ticks / 24.0, 0.6)
    
    for n in range(self.strings):
      if n in activeFrets:
        self.fretActivity[n] = min(self.fretActivity[n] + ticks / 32.0, 1.0)
      else:
        self.fretActivity[n] = max(self.fretActivity[n] - ticks / 64.0, 0.0)

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


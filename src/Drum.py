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
from Mesh import Mesh
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
#So, with regard to note number coloring, swap note.number 0's color wih note.number 4.

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

    #self.drumFillOnScreen = False   #MFH 
    self.drumFillEvents = []
    self.drumFillWasJustActive = False

    self.strings        = 4
    self.playedSound  = [True, True, True, True, True]

    self.openFretActivity = 0.0
    self.openFretColor  = self.fretColors[5]

    self.editorMode     = editorMode


    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("Drum class initialization!")

    #myfingershurt:
    self.hopoStyle = 0    

    if self.theme < 2:    #make board same size as guitar board if GH based theme so it rockmeters dont interfere
      self.boardWidth     = 3.0
      self.boardLength    = 9.0

    #blazingamer
    self.opencolor = self.fretColors[5]
    self.rockLevel = 0.0

    self.bigMax = 1

    #death_au: fixed neck size
    # elif self.twoDnote == False or self.twoDkeys == False:
      # self.boardWidth     = Theme.neckWidth + 0.6
      # self.boardLength    = Theme.neckLength  

    if self.engine.config.get("game", "large_drum_neck"):
      self.boardWidth     *= (4.0/3.0)
      self.boardLength    *= (4.0/3.0)
    
    #Get theme
    themename = self.engine.data.themeLabel
    #now theme determination logic is only in data.py:
    self.theme = self.engine.data.theme


    if self.twoDkeys == True: #death_au
      #myfingershurt: adding drumfretshacked.png for image-corrected drum fret angles in RB:
      if not engine.loadImgDrawing(self, "fretButtons", os.path.join("themes",themename,"drumfretshacked.png")):
        engine.loadImgDrawing(self, "fretButtons", os.path.join("themes",themename,"fretbuttons.png"))
      #death_au: adding drumfrets.png (with bass drum frets seperate)
      if not engine.loadImgDrawing(self, "drumFretButtons", os.path.join("themes",themename,"drumfrets.png")):
        self.drumFretButtons = None
    else: #death_au
      defaultKey = False
      defaultOpenKey = False
      #MFH - can't use IOError for fallback logic for a Mesh() call... 
      if self.engine.fileExists(os.path.join("themes", themename, "key_drum.dae")):
        engine.resource.load(self,  "keyMesh",  lambda: Mesh(engine.resource.fileName("themes", themename, "key_drum.dae")))
      elif self.engine.fileExists(os.path.join("themes", themename, "key.dae")):
        engine.resource.load(self,  "keyMesh",  lambda: Mesh(engine.resource.fileName("themes", themename, "key.dae")))
      else:
        engine.resource.load(self,  "keyMesh",  lambda: Mesh(engine.resource.fileName("key.dae")))
        defaultKey = True

      if self.engine.fileExists(os.path.join("themes", themename, "key_open.dae")):
        engine.resource.load(self,  "keyMeshOpen",  lambda: Mesh(engine.resource.fileName("themes", themename, "key_open.dae")))
      else:
        engine.resource.load(self,  "keyMeshOpen",  lambda: Mesh(engine.resource.fileName("key_open.dae")))
        defaultOpenKey = True

      if defaultKey:
        self.keytex = False
        self.keytexopen = None
      else:
        for i in range(5):
          if engine.loadImgDrawing(self,  "keytex"+chr(97+i),  os.path.join("themes", themename, "keytex_"+chr(97+i)+".png")):
            self.keytex = True
          else:
            self.keytex = False
            break

      if defaultOpenKey:
        self.keytexopen = None
      else:
        if not engine.loadImgDrawing(self, "keytexopen", os.path.join("themes",themename,"keytex_open.png")):
          self.keytexopen = None

    #Spinning starnotes or not?
    self.starspin = False

    if not engine.loadImgDrawing(self, "freestyle1", os.path.join("themes", themename, "freestyletail1.png"),  textureSize = (128, 128)):
      engine.loadImgDrawing(self, "freestyle1", "freestyletail1.png",  textureSize = (128, 128))
    if not engine.loadImgDrawing(self, "freestyle2", os.path.join("themes", themename, "freestyletail2.png"),  textureSize = (128, 128)):
      engine.loadImgDrawing(self, "freestyle2", "freestyletail2.png",  textureSize = (128, 128))


    #t'aint no tails in drums, yo.
    self.simpleTails = True
    self.tail1 = None
    self.tail2 = None
    self.bigTail1 = None
    self.bigTail2 = None  

    self.barsColor = self.engine.theme.barsColor

    self.neck = Neck(self.engine, self, playerObj)
  
  def loadNotes(self):      
    get = lambda file: self.checkPath("notes", file)
      
    if self.twoDnote == True:  
      engine.loadImgDrawing(self, "noteButtons", get("notes.png"))
    else:
      defaultNote = False
      #MFH - can't use IOError for fallback logic for a Mesh() call... 
      if self.engine.fileExists(os.path.join("themes", themename, "note_drum.dae")):
        engine.resource.load(self,  "noteMesh",  lambda: Mesh(engine.resource.fileName("themes", themename, "note_drum.dae")))
      elif self.engine.fileExists(os.path.join("themes", themename, "note.dae")):
        engine.resource.load(self,  "noteMesh",  lambda: Mesh(engine.resource.fileName("themes", themename, "note.dae")))
      else:
        engine.resource.load(self,  "noteMesh",  lambda: Mesh(engine.resource.fileName("note.dae")))
        defaultNote = True

      if defaultNote:
        self.notetex = False
        self.starMesh = None
        self.startex = False
        self.staratex = False
        self.spActTex = None
      else:
        for i in range(5):
          if engine.loadImgDrawing(self,  "notetex"+chr(97+i),  os.path.join("themes", themename, "notetex_"+chr(97+i)+".png")):
            self.notetex = True
          else:
            self.notetex = False
            break

        if self.engine.fileExists(os.path.join("themes", themename, "star_drum.dae")):  
          engine.resource.load(self,  "starMesh",  lambda: Mesh(engine.resource.fileName("themes", themename, "star_drum.dae")))
        elif self.engine.fileExists(os.path.join("themes", themename, "star.dae")):  
          engine.resource.load(self,  "starMesh",  lambda: Mesh(engine.resource.fileName("themes", themename, "star.dae")))
        else:  
          self.starMesh = None

        for i in range(5):
          if engine.loadImgDrawing(self,  "startex"+chr(97+i),  os.path.join("themes", themename, "startex_"+chr(97+i)+".png")):
            self.startex = True
          else:
            self.startex = False
            break

        for i in range(5):
          if engine.loadImgDrawing(self,  "staratex"+chr(97+i),  os.path.join("themes", themename, "staratex_"+chr(97+i)+".png")):
            self.staratex = True
          else:
            self.staratex = False
            break

        if not engine.loadImgDrawing(self, "spActTex", os.path.join("themes",themename,"spacttex.png")):
          self.spActTex = None
      
      if self.engine.fileExists(os.path.join("themes", themename, "open.dae")):
        engine.resource.load(self,  "openMesh",  lambda: Mesh(engine.resource.fileName("themes", themename, "open.dae")))
      else:  
        self.openMesh = None

      if engine.loadImgDrawing(self,  "opentexture",  os.path.join("themes", themename, "opentex.png")):
        self.opentex = True
      else:
        self.opentex = False

      if engine.loadImgDrawing(self,  "opentexture_star",  os.path.join("themes", themename, "opentex_star.png")):
        self.opentex_star = True
      else:
        self.opentex_star = False

      if engine.loadImgDrawing(self,  "opentexture_stara",  os.path.join("themes", themename, "opentex_stara.png")):
        self.opentex_stara = True
      else:
        self.opentex_stara = False
    
  def selectPreviousString(self):
    self.selectedString = (self.selectedString - 1) % self.strings

  def selectString(self, string):
    self.selectedString = string % self.strings

  def selectNextString(self):
    self.selectedString = (self.selectedString + 1) % self.strings

  def noteBeingHeld(self):
    noteHeld = False
    return noteHeld

  def isKillswitchPossible(self):
    possible = False
    return possible


  #volshebnyi
  def renderFreestyleLanes(self, visibility, song, pos, controls):
    if not song:
      return
    if not song.readyToGo:
      return


    #MFH - check for [section big_rock_ending] to set a flag to determine how to treat the last drum fill marker note:
    #for time, event in song.eventTracks[Song.TK_SECTIONS].getEvents(pos - self.lateMargin*2, pos):
    #  if event.text.find("big rock ending") > 0:
    if song.breMarkerTime and pos > song.breMarkerTime:
      self.bigRockEndingMarkerSeen = True




    #boardWindowMin = pos - self.currentPeriod * 2
    boardWindowMax = pos + self.currentPeriod * self.beatsPerBoard
    track = song.midiEventTrack[self.player]
    #self.currentPeriod = self.neckSpeed
    beatsPerUnit = self.beatsPerBoard / self.boardLength
    if self.freestyleEnabled:
      freestyleActive = False
      self.drumFillsActive = False
      #drumFillOnScreen = False
      drumFillEvents = []
      #for time, event in track.getEvents(boardWindowMin, boardWindowMax):
      for time, event in track.getEvents(pos - self.freestyleOffset, boardWindowMax + self.freestyleOffset):
        if isinstance(event, Song.MarkerNote):
          if event.number == Song.freestyleMarkingNote and (not event.happened or self.bigRockEndingMarkerSeen):  #MFH - don't kill the BRE!
            #drumFillOnScreen = True
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
                #if self.drumFillsCount <= self.drumFillsTotal and self.drumFillsReady:
                if self.drumFillsReady:
                  self.drumFillsActive = True
                  self.drumFillWasJustActive = True
                if self.drumFillsHits<0:
                  self.drumFillsCount += 1
                  self.drumFillsHits = 0

              if z < -1.5:
                length += z +1.5
                z =  -1.5

            #if time+event.length>pos and time+event.length-0.5>pos:
            #	if controls.getState(self.keys[4]) or controls.getState(self.keys[8]):
            #		self.starPowerActive = True

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
      #self.drumFillOnScreen = drumFillOnScreen
      self.drumFillEvents = drumFillEvents


  def renderTail(self, length, color, flat = False, fret = 0, freestyleTail = 0, pos = 0):

    #volshebnyi - if freestyleTail == 1, render an freestyle tail
    #  if freestyleTail == 2, render highlighted freestyle tail

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
    tex2 = self.freestyle2
    if freestyleTail == 1:
      #glColor4f(*color)
      c1, c2, c3, c4 = color
      tailGlow = 1 - (pos - self.freestyleLastFretHitTime[fret] ) / self.freestylePeriod
      if tailGlow < 0:
        tailGlow = 0
      color = (c1 + c1*2.0*tailGlow, c2 + c2*2.0*tailGlow, c3 + c3*2.0*tailGlow, c4*0.6 + c4*0.4*tailGlow)    #MFH - this fades inactive tails' color darker                   

    tailcol = (color)

    self.engine.draw3Dtex(tex1, vertex = (-size[0], 0, size[0], size[1]), texcoord = (0.0, 0.0, 1.0, 1.0),
                          scale = tailscale, color = tailcol)

    self.engine.draw3Dtex(tex2, vertex = (-size[0], size[1] - (.05), size[0], size[1] + (zsize)),
                          scale = tailscale, texcoord = (0.0, 0.05, 1.0, 0.95), color = tailcol)

    self.engine.draw3Dtex(tex2, vertex = (-size[0], 0-(zsize), size[0], 0 + (.05)),
                          scale = tailscale, texcoord = (0.0, 0.95, 1.0, 0.05), color = tailcol)


  #myfingershurt:
  def renderNote(self, length, sustain, color, flat = False, tailOnly = False, isTappable = False, big = False, fret = 0, spNote = False, isOpen = False, spAct = False):    

    if flat:
      glScalef(1, .1, 1)

    beatsPerUnit = self.beatsPerBoard / self.boardLength

    if tailOnly:
      return

    #myfingershurt: this should be retrieved once at init, not repeatedly in-game whenever tails are rendered.

    if self.twoDnote == True:

      if self.notedisappear == True:#Notes keep on going when missed
        notecol = (1,1,1,1)#capo
      else:
        if flat:#Notes disappear when missed
          notecol = (.1,.1,.1,1)
        else:
          notecol = (1,1,1,1)

      tailOnly == True

      #death_au: Adjusted for different image.
      if self.separateDrumNotes:
        if isOpen:
          size = (self.boardWidth/1.9, (self.boardWidth/self.strings)/3.0)
          texSize = (0,1)
          if spNote == True:
            texY = (3.0/6.0,4.0/6.0)
          elif self.starPowerActive == True: #death_au: drum sp active notes.
            texY = (5.0/6.0,1.0)
          else:
            texY = (1.0/6.0,2.0/6.0)

        else:
          size = (self.boardWidth/self.strings/2, self.boardWidth/self.strings/2)
          fret -= 1
          texSize = (fret/4.0,fret/4.0+0.25)
          if spNote == True:
            texY = (2.0/6.0,3.0/6.0)
          elif self.starPowerActive == True: #death_au: drum sp active notes.
            texY = (4.0/6.0,5.0/6.0)
          else:
            texY = (0.0,1.0/6.0)

      else:   #automatically generate drum notes from Notes.png

        #myfingershurt: swapping notes 0 and 4:
        if fret == 0:
          #fret = 4     #fret 4 is angled, get fret 2 :)
          fret = 2
        elif fret == 4:
          fret = 0


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

          #rock band fret 0 needs to be reversed just like the fret to match angles better 
          if fret == 0:
            texSize = (fret/5.0+0.2,fret/5.0)

          #myfingershurt: adding spNote==False conditional so that star notes can appear in overdrive
          if self.starPowerActive and spNote == False:
            if isTappable:
              texY = (5*0.166667, 1)
            else:
              texY = (4*0.166667, 5*0.166667)

        if isOpen:
          size = (self.boardWidth/2.0, (self.boardWidth/self.strings)/40.0)

      self.engine.draw3Dtex(self.noteButtons, vertex = (-size[0],size[1],size[0],-size[1]), texcoord = (texSize[0],texY[0],texSize[1],texY[1]),
                            scale = (1,1,0), rot = (30,1,0,0), multiples = True, color = color, vertscale = .27)

    else:  

      #mesh = outer ring (black) 
      #mesh_001 = main note (key color) 
      #mesh_002 = top (spot or hopo if no mesh_003) 
      #mesh_003 = hopo bump (hopo color)

      if fret == 0:
        fret = 4     #fret 4 is angled, get fret 2 :)
        #fret = 2    #compensating for this in drum.
      elif fret == 4:
        fret = 0

      if spNote == True and self.starMesh is not None and isOpen == False:
        meshObj = self.starMesh
      elif isOpen == True and self.openMesh is not None:
        meshObj = self.openMesh
      else:
        meshObj = self.noteMesh

      glPushMatrix()
      glEnable(GL_DEPTH_TEST)
      glDepthMask(1)
      glShadeModel(GL_SMOOTH)

      if spNote == True and self.threeDspin == True and isOpen == False:
        glRotate(90 + self.time/3, 0, 1, 0)
      if isOpen == False and spNote == False and self.noterotate == True:
        glRotatef(90, 0, 1, 0)
        glRotatef(-90, 1, 0, 0)

      if fret == 0: # green note
        glRotate(self.engine.theme.drumnoterot[0], 0, 0, 1), glTranslatef(0, self.engine.theme.drumnotepos[0], 0)
      elif fret == 1: # red note
        glRotate(self.engine.theme.drumnoterot[1], 0, 0, 1), glTranslatef(0, self.engine.theme.drumnotepos[1], 0)
      elif fret == 2: # yellow
        glRotate(self.engine.theme.drumnoterot[2], 0, 0, 1), glTranslatef(0, self.engine.theme.drumnotepos[2], 0)
      elif fret == 3:# blue note
        glRotate(self.engine.theme.drumnoterot[3], 0, 0, 1), glTranslatef(0, self.engine.theme.drumnotepos[3], 0)
      elif fret == 4: #open note
        glRotate(self.engine.theme.drumnoterot[4], 0, 0, 1), glTranslatef(0, self.engine.theme.drumnotepos[4], 0)

      if self.spActTex is not None and isOpen == False and spNote == False and spAct == True:
        glColor3f(1.5,1.5,1.5) #glow
        glEnable(GL_TEXTURE_2D)
        self.spActTex.texture.bind()
        glMatrixMode(GL_TEXTURE)
        glScalef(1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glScalef(self.boardScaleX, self.boardScaleY, 1)
        if isTappable:
          meshObj.render("Mesh_001")
        else:
          meshObj.render("Mesh")
        glMatrixMode(GL_TEXTURE)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_TEXTURE_2D)
      elif self.staratex == True and self.starPowerActive and isOpen==False and spNote == False:
        glColor3f(1,1,1)
        glEnable(GL_TEXTURE_2D)
        getattr(self,"staratex"+chr(97+fret)).texture.bind()
        glMatrixMode(GL_TEXTURE)
        glScalef(1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glScalef(self.boardScaleX, self.boardScaleY, 1)
        if isTappable:
          meshObj.render("Mesh_001")
        else:
          meshObj.render("Mesh")
        glMatrixMode(GL_TEXTURE)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_TEXTURE_2D)
        
      elif self.notetex == True and spNote == False and isOpen==False:

        glColor3f(1,1,1)
        glEnable(GL_TEXTURE_2D)
        getattr(self,"notetex"+chr(97+fret)).texture.bind()
        glMatrixMode(GL_TEXTURE)
        glScalef(1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glScalef(self.boardScaleX, self.boardScaleY, 1)
        if isTappable:
          meshObj.render("Mesh_001")
        else:
          meshObj.render("Mesh")
        glMatrixMode(GL_TEXTURE)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_TEXTURE_2D)

      elif self.startex == True and spNote == True and isOpen==False:
        glColor3f(1,1,1)
        glEnable(GL_TEXTURE_2D)
        getattr(self,"startex"+chr(97+fret)).texture.bind()
        glMatrixMode(GL_TEXTURE)
        glScalef(1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glScalef(self.boardScaleX, self.boardScaleY, 1)
        if isTappable:
          meshObj.render("Mesh_001")
        else:
          meshObj.render("Mesh")
        glMatrixMode(GL_TEXTURE)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_TEXTURE_2D)

      elif self.opentex_stara == True and isOpen==True and spNote==False and self.starPowerActive:
        glColor3f(1,1,1)
        glEnable(GL_TEXTURE_2D)

        self.opentexture_stara.texture.bind()

        glMatrixMode(GL_TEXTURE)
        glScalef(1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glScalef(self.boardScaleX, self.boardScaleY, 1)
        meshObj.render()
        glMatrixMode(GL_TEXTURE)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_TEXTURE_2D)
      
      elif self.opentex == True and isOpen==True and spNote==False:
        glColor3f(1,1,1)
        glEnable(GL_TEXTURE_2D)

        self.opentexture.texture.bind()

        glMatrixMode(GL_TEXTURE)
        glScalef(1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glScalef(self.boardScaleX, self.boardScaleY, 1)
        meshObj.render()
        glMatrixMode(GL_TEXTURE)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_TEXTURE_2D)
      
      elif self.opentex_star == True and isOpen==True and spNote==True:
        glColor3f(1,1,1)
        glEnable(GL_TEXTURE_2D)

        self.opentexture_star.texture.bind()

        glMatrixMode(GL_TEXTURE)
        glScalef(1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glScalef(self.boardScaleX, self.boardScaleY, 1)
        meshObj.render()
        glMatrixMode(GL_TEXTURE)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_TEXTURE_2D)
      else: 
        #death_au: fixed 3D note colours
        glColor4f(*color)
        if self.starPowerActive and self.theme != 2 and not color == (0,0,0,1):
          glColor4f(self.spColor[0],self.spColor[1],self.spColor[2],1)
          #glColor4f(.3,.7,.9, 1)
        if isOpen == True and self.starPowerActive == False:
          glColor4f(self.opencolor[0],self.opencolor[1],self.opencolor[2], 1)
        
        meshObj.render("Mesh_001")
        glColor3f(self.spotColor[0], self.spotColor[1], self.spotColor[2])
        meshObj.render("Mesh_002")
        glColor3f(self.meshColor[0], self.meshColor[1], self.meshColor[2])
        meshObj.render("Mesh")



      glDepthMask(0)
      glPopMatrix()


  def renderOpenNotes(self, visibility, song, pos):
    if not song:
      return
    if not song.readyToGo:
      return

    self.bigMax = 0

    self.currentPeriod = self.neckSpeed
    self.targetPeriod  = self.neckSpeed

    self.killPoints = False

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    w = self.boardWidth / self.strings
    track = song.track[self.player]

    num = 0
    enable = True

    self.openStarNotesInView = False
    #for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard):
    for time, event in reversed(track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard)):    #MFH - reverse order of note rendering
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

      if event.number != 0:   #skip all regular notes
        continue

      # c = self.fretColors[event.number]

      # isOpen = False
      # if event.number == 0: #treat open string note differently - also haven't we already ensured that event.number == 0?
      x  = (self.strings / 2 - .5 - 1.5) * w
      isOpen     = True
      c = self.openFretColor

      z  = ((time - pos) / self.currentPeriod) / beatsPerUnit
      z2 = ((time + event.length - pos) / self.currentPeriod) / beatsPerUnit

      if z > self.boardLength * .8:
        f = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        f = min(1, max(0, 1 + z2))
      else:
        f = 1.0

      #volshebnyi - hide open notes in BRE zone if BRE enabled  
      if self.freestyleEnabled and self.freestyleStart > 0:  
        if self.drumFillsReady or self.freestyleReady:
          if time > self.freestyleStart - self.freestyleOffset and time < self.freestyleStart + self.freestyleOffset + self.freestyleLength:
            z = -2.0

      if self.twoDnote == True and not self.useFretColors:
        color      = (1,1,1, 1 * visibility * f)
      else:
        color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1 * visibility * f)
      length = 0
      flat       = False
      tailOnly   = False
      spNote = False

      #myfingershurt: user setting for starpower refill / replenish notes
      #if self.starPowerActive and self.theme != 2:  #Rock Band theme allows SP notes in overdrive
      if self.starPowerActive:
        if self.spRefillMode == 0:    #mode 0 = no starpower / overdrive refill notes
          self.spEnabled = False
        elif self.spRefillMode == 1 and self.theme != 2:  #mode 1 = overdrive refill notes in RB themes only
          self.spEnabled = False
        elif self.spRefillMode == 2 and song.midiStyle != 1: #mode 2 = refill based on MIDI type
          self.spEnabled = False

      if event.star:
        #self.isStarPhrase = True
        self.openStarNotesInView = True
      if event.finalStar:
        self.finalStarSeen = True
        self.openStarNotesInView = True

      if event.star and self.spEnabled:
        spNote = True
      if event.finalStar and self.spEnabled:
        spNote = True
        if event.played or event.hopod:
          if event.flameCount < 1 and not self.starPowerGained:

            #if self.drumFillOnScreen:   #MFH - if there's a drum fill on the screen right now, skip it!
            if self.starPower < 50:   #not enough starpower to activate yet, kill existing drumfills
              for dfEvent in self.drumFillEvents:
                dfEvent.happened = True

            if self.starPower < 100:
              self.starPower += 25
            if self.starPower > 100:
              self.starPower = 100
            self.overdriveFlashCount = 0  #MFH - this triggers the oFlash strings & timer
            self.starPowerGained = True


      #if enable:
      #  self.spEnabled = True

      isTappable = False

      if self.notedisappear == True:#Notes keep on going when missed
        ###Capo###
        if event.played or event.hopod:
          tailOnly = True
          length += z
          z = 0
          if length <= 0:
            continue
        if z < 0 and not (event.played or event.hopod): 
          color = (.6, .6, .6, .5 * visibility * f)
          flat  = False
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
            color = (.6, .6, .6, .5 * visibility * f)
            flat  = False

      sustain = False


      glPushMatrix()
      glTranslatef(x, (1.0 - visibility) ** (event.number + 1), z)
      self.renderNote(length, sustain = sustain, color = color, flat = flat, tailOnly = tailOnly, isTappable = isTappable, fret = event.number, spNote = spNote, isOpen = isOpen)
      glPopMatrix()

    #myfingershurt: end FOR loop / note rendering loop       
    if (not self.openStarNotesInView) and (not self.starNotesInView) and self.finalStarSeen:
      self.spEnabled = True
      self.finalStarSeen = False
      self.isStarPhrase = False

  def renderNotes(self, visibility, song, pos):
    if not song:
      return
    if not song.readyToGo:
      return

    self.bigMax = 0

    self.currentPeriod = self.neckSpeed
    self.targetPeriod  = self.neckSpeed

    self.killPoints = False

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    w = self.boardWidth / self.strings
    track = song.track[self.player]

    num = 0
    enable = True
    self.starNotesInView = False

    #for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard):
    for time, event in reversed(track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard)):    #MFH - reverse order of note rendering
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
        #  self.setBPM(self.targetBpm) # glorandwarf: was setDynamicBPM(self.targetBpm)
        continue

      if not isinstance(event, Note):
        continue

      if (event.noteBpm == 0.0):
        event.noteBpm = self.tempoBpm

      #volshebnyi - removed
      if event.number == 0: #MFH - skip all open notes
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

      c = self.fretColors[event.number]

      if event.star:
        #self.isStarPhrase = True
        self.starNotesInView = True
      if event.finalStar:
        self.finalStarSeen = True
        self.starNotesInView = True

      isOpen = False
      
      x  = (self.strings / 2 - .5 - (event.number - 1)) * w
      if event.number == 4:
        c = self.fretColors[0]        #myfingershurt: need to swap note 0 and note 4 colors for drums:

      z  = ((time - pos) / self.currentPeriod) / beatsPerUnit
      z2 = ((time + event.length - pos) / self.currentPeriod) / beatsPerUnit

      if z > self.boardLength * .8:
        f = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        f = min(1, max(0, 1 + z2))
      else:
        f = 1.0

      #volshebnyi - hide notes in BRE zone if BRE enabled  
      if self.freestyleEnabled:
        if self.drumFillsReady or self.freestyleReady:  
          if time > self.freestyleStart - self.freestyleOffset and time < self.freestyleStart + self.freestyleOffset + self.freestyleLength:
            z = -2.0

      if self.twoDnote == True and not self.useFretColors:
        color      = (1,1,1, 1 * visibility * f)
      else:
        color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1 * visibility * f)
      length = 0
      flat       = False
      tailOnly   = False
      spNote = False

      #myfingershurt: user setting for starpower refill / replenish notes
      #if self.starPowerActive and self.theme != 2:  #Rock Band theme allows SP notes in overdrive
      if self.starPowerActive:
        if self.spRefillMode == 0:    #mode 0 = no starpower / overdrive refill notes
          self.spEnabled = False
        elif self.spRefillMode == 1 and self.theme != 2:  #mode 1 = overdrive refill notes in RB themes only
          self.spEnabled = False
        elif self.spRefillMode == 2 and song.midiStyle != 1: #mode 2 = refill based on MIDI type
          self.spEnabled = False


      if event.star and self.spEnabled:
        spNote = True
      if event.finalStar and self.spEnabled:
        spNote = True
        if event.played or event.hopod:
          if event.flameCount < 1 and not self.starPowerGained:

            #if self.drumFillOnScreen:   #MFH - if there's a drum fill on the screen right now, skip it!
            if self.starPower < 50:   #not enough starpower to activate yet, kill existing drumfills
              for dfEvent in self.drumFillEvents:
                dfEvent.happened = True

            if self.starPower < 100:
              self.starPower += 25
            if self.starPower > 100:
              self.starPower = 100
            self.overdriveFlashCount = 0  #MFH - this triggers the oFlash strings & timer
            self.starPowerGained = True
            self.neck.ocount = 0

      #if enable:
      #  self.spEnabled = True

      isTappable = False

      if self.notedisappear == True:#Notes keep on going when missed
        ###Capo###
        if event.played or event.hopod:
          tailOnly = True
          length += z
          z = 0
          if length <= 0:
            continue
        if z < 0 and not (event.played or event.hopod): 
          color = (.6, .6, .6, .5 * visibility * f)
          flat  = False
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
            color = (.6, .6, .6, .5 * visibility * f)
            flat  = False

      sustain = False


      glPushMatrix()
      glTranslatef(x, (1.0 - visibility) ** (event.number + 1), z)
      self.renderNote(length, sustain = sustain, color = color, flat = flat, tailOnly = tailOnly, isTappable = isTappable, fret = event.number, spNote = spNote, isOpen = isOpen)
      glPopMatrix()

    #myfingershurt: end FOR loop / note rendering loop       
    if (not self.openStarNotesInView) and (not self.starNotesInView) and self.finalStarSeen:
      self.spEnabled = True
      self.isStarPhrase = False
      self.finalStarSeen = False

  def renderFrets(self, visibility, song, controls):
    w = self.boardWidth / self.strings
    size = (.22, .22)
    v = 1.0 - visibility

    glEnable(GL_DEPTH_TEST)


    for n in range(self.strings):
      f = self.drumsHeldDown[n+1]/200.0
      pressed = self.drumsHeldDown[n+1]

      if n == 3:
        c = self.fretColors[0]
      else:
        c = self.fretColors[n + 1]

      glColor4f(.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, visibility)
      if self.fretPress:
        y = v + f / 6 #this allows the keys to "press"
      else:
        y = v / 6
      x = (self.strings / 2 - .5 - n) * w

      if self.twoDkeys == True: #death_au

        size = (self.boardWidth/self.strings/2, self.boardWidth/self.strings/2.4)
        whichFret = n

        #death_au: only with old-style drum fret images
        if self.drumFretButtons == None:
          whichFret = n+1
          if whichFret == 4:
            whichFret = 0
            #reversing fret 0 since it's angled in Rock Band
            texSize = (whichFret/5.0+0.2,whichFret/5.0)
          else:
            #texSize = (n/5.0,n/5.0+0.2)
            texSize = (whichFret/5.0,whichFret/5.0+0.2)

          texY = (0.0,1.0/3.0)
          if pressed:
            texY = (1.0/3.0,2.0/3.0)
          if self.hit[n]:
            texY = (2.0/3.0,1.0)
        #death_au: only with new drum fret images
        else:
          texSize = (whichFret/4.0,whichFret/4.0+0.25)

          texY = (0.0,1.0/6.0)
          if pressed:
            texY = (2.0/6.0,3.0/6.0)
          if self.hit[n]:
            texY = (4.0/6.0,5.0/6.0)
        if self.drumFretButtons == None:
          self.engine.draw3Dtex(self.fretButtons, vertex = (size[0],size[1],-size[0],-size[1]), texcoord = (texSize[0], texY[0], texSize[1], texY[1]),
                                coord = (x,v,0), multiples = True,color = (1,1,1), depth = True)
        else:
          self.engine.draw3Dtex(self.drumFretButtons, vertex = (size[0],size[1],-size[0],-size[1]), texcoord = (texSize[0], texY[0], texSize[1], texY[1]),
                                coord = (x,v,0), multiples = True,color = (1,1,1), depth = True)


      else: #death_au
        if n == 3:
          c = self.fretColors[0]
        else:
          c = self.fretColors[n + 1]

        if self.keyMesh:
          glPushMatrix()
          #glTranslatef(x, y + v * 6, 0)
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
          #glColor4f(.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, visibility)

          #Mesh - Main fret
          #Key_001 - Top of fret (key_color)
          #Key_002 - Bottom of fret (key2_color)
          #Glow_001 - Only rendered when a note is hit along with the glow.svg
		  
          if n == 0: #red fret button
            glRotate(self.engine.theme.drumkeyrot[0], 0, 1, 0), glTranslatef(0, 0, self.engine.theme.drumkeypos[0])
          elif n == 1:
            glRotate(self.engine.theme.drumkeyrot[1], 0, 1, 0), glTranslatef(0, 0, self.engine.theme.drumkeypos[1])
          elif n == 2:
            glRotate(self.engine.theme.drumkeyrot[2], 0, 1, 0), glTranslatef(0, 0, self.engine.theme.drumkeypos[2])
          elif n == 3: #green fret button
            glRotate(self.engine.theme.drumkeyrot[3], 0, 1, 0), glTranslatef(0, 0, self.engine.theme.drumkeypos[3])

          if self.keytex == True:
            glColor4f(1,1,1,visibility)
            glTranslatef(x, y, 0)
            glEnable(GL_TEXTURE_2D)
            if n == 0: 
              self.keytexb.texture.bind()
            elif n == 1:
              self.keytexc.texture.bind()
            elif n == 2:
              self.keytexd.texture.bind()
            elif n == 3:
              self.keytexa.texture.bind()
            glMatrixMode(GL_TEXTURE)
            glScalef(1, -1, 1)
            glMatrixMode(GL_MODELVIEW)
            glScalef(self.boardScaleX, self.boardScaleY, 1)
            if pressed and not self.hit[n]:
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

        self.engine.draw3Dtex(self.glowDrawing, coord = (x, y, 0.01), rot = (f * 90 + self.time, 0, 1, 0),
                              texcoord = (0.0, 0.0, 1.0, 1.0), vertex = (-size[0] * f, -size[1] * f, size[0] * f, size[1] * f),
                              multiples = True, alpha = True, color = glowcol)
      self.hit[n] = False

        ###############################################
    #death_au:
    #if we leave the depth test enabled, it thinks that the bass drum images
    #are under the other frets and openGL culls them. So I just leave it disabled
    if self.twoDkeys == False: #death_au
    
      f = self.drumsHeldDown[0]/200.0

      c = self.openFretColor

      glColor4f(.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, visibility)
      y = v + f / 6
      x = 0

      if self.keyMeshOpen:
        glPushMatrix()
        #glTranslatef(x, y + v * 6, 0)
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
        #glColor4f(.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, visibility)

        glRotate(self.engine.theme.drumkeyrot[4], 0, 1, 0), glTranslatef(0, 0, self.engine.theme.drumkeypos[4])

        if self.keytexopen is not None:
          glColor4f(1,1,1,visibility)
          glTranslatef(x, v, 0)
          glEnable(GL_TEXTURE_2D)
          self.keytexopen.texture.bind()
          glMatrixMode(GL_TEXTURE)
          glScalef(1, -1, 1)
          glMatrixMode(GL_MODELVIEW)
          glScalef(self.boardScaleX, self.boardScaleY, 1)
          if self.hit[0]:
            self.keyMeshOpen.render("Mesh_002")
          elif self.drumsHeldDown[0] > 0:
            self.keyMeshOpen.render("Mesh_001")
          else:
            self.keyMeshOpen.render("Mesh")
          glMatrixMode(GL_TEXTURE)
          glLoadIdentity()
          glMatrixMode(GL_MODELVIEW)
          glDisable(GL_TEXTURE_2D)
        else:
          glColor4f(.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, visibility)
          glTranslatef(x, y + v * 6, 0)
          key = self.keyMeshOpen

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
        glDisable(GL_DEPTH_TEST)
    
      ######################


    elif self.twoDkeys == True and self.drumFretButtons != None: #death_au
      glDisable(GL_DEPTH_TEST)
    
      x = 0.0#(self.boardWidth / 2 )

      size = (self.boardWidth/2, self.boardWidth/self.strings/2.4)

      texSize = (0.0,1.0)

      texY = (1.0/6.0,2.0/6.0)
      if self.drumsHeldDown[0] > 0:
        texY = (3.0/6.0,4.0/6.0)
      if self.hit[0]:
        texY = (5.0/6.0,1.0)

      self.engine.draw3Dtex(self.drumFretButtons, vertex = (size[0],size[1],-size[0],-size[1]), texcoord = (texSize[0], texY[0], texSize[1], texY[1]),
                            coord = (x,v,0), multiples = True,color = (1,1,1), depth = True)

    ###############################################
    else:
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
          #x  = (self.strings / 2 - event.number) * w

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




  def renderFreestyleFlames(self, visibility, controls):
    if self.flameColors[0][0][0] == -1:
      return

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    w = self.boardWidth / self.strings
    #track = song.track[self.player]

    size = (.22, .22)
    v = 1.0 - visibility

    if self.disableFlameSFX != True:
      flameLimit = 10.0
      flameLimitHalf = round(flameLimit/2.0)
      for fretNum in range(self.strings+1):   #need to add 1 to string count to check this correctly (bass drum doesnt count as a string)
        #MFH - must include secondary drum keys here
        #if controls.getState(self.keys[fretNum]):
        if controls.getState(self.keys[fretNum]) or controls.getState(self.keys[fretNum+5]):

          if self.freestyleHitFlameCounts[fretNum] < flameLimit:
            ms = math.sin(self.time) * .25 + 1

            if fretNum == 0:
              x  = (self.strings / 2 - 2) * w
            else:
              x  = (self.strings / 2 +.5 - fretNum) * w
            #x  = (self.strings / 2 - fretNum) * w

            xlightning = (self.strings / 2 - fretNum)*2.2*w
            ff = 1 + 0.25       
            y = v + ff / 6
            glBlendFunc(GL_ONE, GL_ONE)

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
      # if self.leftyMode:
        # glScalef(-1, 1, 1)

      if self.freestyleActive or self.drumFillsActive:
        self.renderOpenNotes(visibility, song, pos)
        self.renderNotes(visibility, song, pos)
        self.renderFreestyleLanes(visibility, song, pos, controls) #MFH - render the lanes on top of the notes.
        self.renderFrets(visibility, song, controls)

        if self.hitFlamesPresent: #MFH - only when present!
          self.renderFreestyleFlames(visibility, controls)    #MFH - freestyle hit flames

      else:

        self.renderFreestyleLanes(visibility, song, pos, controls)

    #if self.fretsUnderNotes:    #MFH
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

      # if self.leftyMode:
        # glScalef(-1, 1, 1)

  def getRequiredNotesMFH(self, song, pos):
    track   = song.track[self.player]
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


  def hitNote(self, time, note):
    self.pickStartPos = max(self.pickStartPos, time)
    self.playedNotes = [(time, note)]
    note.played       = True
    return True  

  def areNotesTappable(self, notes):
    if not notes:
      return
    #for time, note in notes:
    #  if note.tappable > 1:
    #    return True
    return False


  def playDrumSounds(self, controls, playBassDrumOnly = False):   #MFH - handles playing of drum sounds.  
    #Returns list of drums that were just hit (including logic for detecting a held bass pedal)
    #pass playBassDrumOnly = True (optional paramater) to only play the bass drum sound, but still
    #  return a list of drums just hit (intelligently play the bass drum if it's held down during gameplay)
    drumsJustHit = [False, False, False, False, False]

    for i in range (5):
      if controls.getState(self.keys[i]) or controls.getState(self.keys[5+i]):
        if i == 0:
          if self.playedSound[i] == False:  #MFH - gotta check if bass drum pedal is just held down!
            if self.engine.data.bassDrumSoundFound:
              self.engine.data.bassDrumSound.play()
            self.playedSound[i] = True
            drumsJustHit[0] = True
            if self.fretboardHop < 0.04:
              self.fretboardHop = 0.04  #stump
        if i == 1:
          if self.engine.data.T1DrumSoundFound and not playBassDrumOnly and self.playedSound[i] == False:
            self.engine.data.T1DrumSound.play()
          self.playedSound[i] = True
          drumsJustHit[i] = True
        if i == 2:
          if self.engine.data.T2DrumSoundFound and not playBassDrumOnly and self.playedSound[i] == False:
            self.engine.data.T2DrumSound.play()
          self.playedSound[i] = True
          drumsJustHit[i] = True
        if i == 3:
          if self.engine.data.T3DrumSoundFound and not playBassDrumOnly and self.playedSound[i] == False:
            self.engine.data.T3DrumSound.play()
          self.playedSound[i] = True
          drumsJustHit[i] = True
        if i == 4:   #MFH - must actually activate starpower!
          if self.engine.data.CDrumSoundFound and not playBassDrumOnly and self.playedSound[i] == False:
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



#-    if controls.getState(self.keys[0]):   
#-      if not self.bassDrumPedalDown:  #MFH - gotta check if bass drum pedal is just held down!
#-        numHits = 1
#-        if self.engine.data.bassDrumSoundFound:
#-          self.engine.data.bassDrumSound.play()
#-        self.bassDrumPedalDown = True
#-    for i in range (1,5):
#-      if controls.getState(self.keys[i]) or controls.getState(self.keys[4+i]):
#-        numHits += 1
#-        if i == 1:
#-          if self.engine.data.T1DrumSoundFound:
#-            self.engine.data.T1DrumSound.play()
#-        if i == 2:
#-          if self.engine.data.T2DrumSoundFound:
#-            self.engine.data.T2DrumSound.play()
#-        if i == 3:
#-          if self.engine.data.T3DrumSoundFound:
#-            self.engine.data.T3DrumSound.play()
#-        if i == 4:   #MFH - must actually activate starpower!
#-          if self.engine.data.CDrumSoundFound:
#-            self.engine.data.CDrumSound.play()
#-          if self.drumFillsActive and self.drumFillsHits >= 4 and not self.starPowerActive:
#-            drumFillCymbalPos = self.freestyleStart+self.freestyleLength
#-            minDrumFillCymbalHitTime = drumFillCymbalPos - self.earlyMargin
#-            maxDrumFillCymbalHitTime = drumFillCymbalPos + self.lateMargin
#-            if (pos >= minDrumFillCymbalHitTime) and (pos <= maxDrumFillCymbalHitTime):
#-              self.freestyleSP = True

    return numHits


  def startPick(self, song, pos, controls, hopo = False):
    if not song:
      return False
    if not song.readyToGo:
      return

    #self.matchingNotes = self.getRequiredNotes(song, pos)
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

  def startPick2(self, song, pos, controls, hopo = False):
    res = self.startPick(song, pos, controls, hopo)
    return res

  def startPick3(self, song, pos, controls, hopo = False):
    res = self.startPick(song, pos, controls, hopo)
    return res


  def endPick(self, pos):
    self.playedNotes = []
    return True

  def getPickLength(self, pos):
    return 0.0

  def coOpRescue(self, pos):
    self.coOpRestart = True #initializes Restart Timer
    self.coOpRescueTime  = pos
    self.starPower  = 0
    Log.debug("Rescued at " + str(pos))

  def run(self, ticks, pos, controls):
    if not self.paused:
      self.time += ticks
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


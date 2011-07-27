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
import Log

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
    super(Drum, self).__init__(engine, playerObj, player)

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
    self.strings2       = 5
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

    self.drumFretButtons = None

    #blazingamer
    self.opencolor = self.fretColors[5]
    self.rockLevel = 0.0

    self.bigMax = 1

    if self.engine.config.get("game", "large_drum_neck"):
      self.boardWidth     *= (4.0/3.0)
      self.boardLength    *= (4.0/3.0)
    
    #Get theme
    #now theme determination logic is only in data.py:
    self.theme = self.engine.data.theme

    self.tailsEnabled = False

    self.loadImages()

    self.barsColor = self.engine.theme.barsColor

    self.neck = Neck(self.engine, self, playerObj)

  def loadNotes(self):
    super(Drum, self).loadNotes()
    engine = self.engine

    get = lambda file: self.checkPath("tails", file)
    
    if self.twoDnote == True:
      if self.noteSpin:
        engine.loadImgDrawing(self, "noteOpenAnimatedPowerActive", get("animated_open_power_active.png"))
        engine.loadImgDrawing(self, "noteOpenAnimatedPower", get("animated_open_power.png"))
        engine.loadImgDrawing(self, "noteOpenAnimated", get("animated_open.png"))        

      size = (self.boardWidth/1.9, (self.boardWidth/self.strings)/3.0)
      self.openVtx = np.array([[-size[0],  .27, size[1]],
                               [size[0],  .27, size[1]],
                               [-size[0], -.27, -size[1]],
                               [size[0], -.27, -size[1]]], 
                               dtype=np.float32)

      self.noteTexCoord = [[np.array([[i/float(self.strings), s/6.0],
                                     [(i+1)/float(self.strings), s/6.0],
                                     [i/float(self.strings), (s+1)/6.0],
                                     [(i+1)/float(self.strings), (s+1)/6.0]], 
                                     dtype=np.float32)
                            for i in range(self.strings)] for s in range(0,5,2)]
      self.openTexCoord = [np.array([[0.0, s/6.0],
                                     [1.0, s/6.0],
                                     [0.0, (s+1)/6.0],
                                     [1.0, (s+1)/6.0]], dtype=np.float32) for s in range(1,6,2)]
                            
      self.animatedOpenTexCoord = [[np.array([[0.0, s/float(self.noteSpinFrames)],
                                     [1.0, s/float(self.noteSpinFrames)],
                                     [0.0, (s+1)/float(self.noteSpinFrames)],
                                     [1.0, (s+1)/float(self.noteSpinFrames)]], 
                                     dtype=np.float32)
                            for i in range(self.strings)] for s in range(self.noteSpinFrames)]  

    else:
      defaultOpenNote = False

      if self.engine.fileExists(get("open.dae")): #load from notes folder
        self.engine.resource.load(self,  "openMesh",  lambda: Mesh(self.engine.resource.fileName(get("open.dae"))))
      else: #fallback to the default in the data folder
        self.engine.resource.load(self,  "openMesh",  lambda: Mesh(self.engine.resource.fileName("open.dae")))
        defaultOpenNote = True
        
      engine.loadImgDrawing(self, "spActTex", get("spacttex.png"))

      if defaultOpenNote:
        self.opentexture = False
        self.opentexture_star = False
        self.opentexture_stara = False
      else:
        self.engine.loadImgDrawing(self, "opentexture", get("opentex.png"))
        self.engine.loadImgDrawing(self, "opentexture_star", get("opentex_star.png"))
        self.engine.loadImgDrawing(self, "opentexture_stara", get("opentex_stara.png"))

  def loadFrets(self):
    super(Drum, self).loadFrets()
    engine = self.engine
    themename = self.engine.data.themeLabel

    get = lambda file: self.checkPath("frets", file)
    
    if self.twoDkeys == True: #death_au
      if engine.loadImgDrawing(self, "fretButtons", os.path.join("themes",themename, "frets", "drum", "fretbuttons.png")):
        self.drumFretButtons = True
      elif engine.loadImgDrawing(self, "fretButtons", get("fretbuttons.png")):
        self.drumFretButtons = None

    else:
      defaultOpenKey = False

      if self.engine.fileExists(get("open.dae")): #look in the frets folder for files
        engine.resource.load(self,  "keyMeshOpen",  lambda: Mesh(engine.resource.fileName(get("open.dae"))))
      else: #default to files in data folder
        engine.resource.load(self,  "keyMeshOpen",  lambda: Mesh(engine.resource.fileName("key_open.dae")))
        defaultOpenKey = True

      if defaultOpenKey:
        self.keytexopen = False
      else:
        engine.loadImgDrawing(self, "keytexopen", get("keytex_open.png"))

  def renderNote(self, length, sustain, color, tailOnly = False, isTappable = False, fret = 0, spNote = False, isOpen = False, spAct = False):

    if tailOnly:
      return

    if self.twoDnote == True:
      tailOnly = True

      y = 0
      if spNote:
        y += 1
      elif self.starPowerActive:
        y += 2
        
      if isOpen:
        vtx = self.openVtx
        if self.noteSpin:
          texCoord = self.animatedOpenTexCoord[self.noteSpinFrameIndex]
          if spNote == True:
            noteImage = self.noteOpenAnimatedPower
          elif self.starPowerActive == True: #death_au: drum sp active notes.
            noteImage = self.noteOpenAnimatedPowerActive
          else:
            noteImage = self.noteOpenAnimated
          if not noteImage:
            noteImage = self.noteButtons
            texCoord = self.openTexCoord[y]
        else:
          if not noteImage:
            noteImage = self.noteButtons
            texCoord = self.noteTexCoord[y]
      else:
        fret -= 1
        vtx = self.noteVtx
        if self.noteSpin:
          texCoord = self.animatedNoteTexCoord[self.noteSpinFrameIndex][fret]
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
          
      self.engine.draw3Dtex(noteImage, vertex = vtx, texcoord = texCoord,
                            scale = (1,1,0), rot = (30,1,0,0), multiples = False, color = color)

    else: #3d Notes
      shaders.setVar("Material",color,"notes")

      self.notepos = self.engine.theme.drumnotepos
      self.noterot = self.engine.theme.drumnoterot
      
      if fret == 0:
        fret = 4     #fret 4 is angled, get fret 2 :)
        #fret = 2    #compensating for this in drum.
      elif fret == 4:
        fret = 0

      if isOpen and self.openMesh is not None:
        meshObj = self.openMesh
      elif spNote and self.starMesh is not None:
        meshObj = self.starMesh
      else:
        meshObj = self.noteMesh

      glPushMatrix()
      glEnable(GL_DEPTH_TEST)
      glDepthMask(1)
      glShadeModel(GL_SMOOTH)

      if not isOpen:
        if spNote and self.threeDspin:
          glRotate(90 + self.time/3, 0, 1, 0)
        elif not spNote and self.noterotate:
          glRotatef(90, 0, 1, 0)
          glRotatef(-90, 1, 0, 0)

      if fret >= 0 and fret <= 4:
        glRotate(self.noterot[fret], 0, 0, 1)
        glTranslatef(0, self.notepos[fret], 0)
      
      texture = None
      if self.notetex: 
      
        if isOpen:
          if self.opentexture_star:
            texture = self.opentexture_star
          elif self.opentexture_stara and self.starPowerActive:
            texture = self.opentexture_stara
          elif self.opentexture:
            texture = self.opentexture

        elif self.startex and spNote:
          texture = getattr(self,"startex"+chr(97+fret))

        elif self.spActTex and spAct:
          texture = self.spActTex        

        elif self.staratex and self.starPowerActive:
          texture = getattr(self,"staratex"+chr(97+fret))

        else:
          texture = getattr(self,"notetex"+chr(97+fret))

      self.render3DNote(texture, meshObj, color, isTappable)

      glDepthMask(0)
      glPopMatrix()
      glDisable(GL_DEPTH_TEST)

  
  def renderFrets(self, visibility, song, controls):
    w = self.boardWidth / self.strings
    size = (.22, .22)
    v = 1.0 - visibility
	
    glEnable(GL_DEPTH_TEST)
	
    for n in range(self.strings2):
      if n == 4:
        keyNumb = 0
      else:
        keyNumb = n + 1
      f = self.drumsHeldDown[keyNumb]/200.0
      pressed = self.drumsHeldDown[keyNumb]

      if n == 3: #Set colors of frets
        c = list(self.fretColors[0])
      elif not n == 4:
        c = list(self.fretColors[n + 1])
      
      if n == 4:
        y = v + f / 6
        x = 0
      else:
        y = v / 6
        x = (self.strings / 2 - .5 - n) * w

      if self.twoDkeys == True or not self.keyMesh:

        if n == 4: #Weirdpeople - so the drum bass fret can be seen with 2d frets
          glDisable(GL_DEPTH_TEST)
          size = (self.boardWidth/2, self.boardWidth/self.strings/2.4)
          texSize = (0.0,1.0)
        else:
          size = (self.boardWidth / self.strings / 2, self.boardWidth / self.strings / 2.4)
          texSize = (n / self.lanenumber, n / self.lanenumber + 1 / self.lanenumber)
          
        fretColor = (1,1,1,1)
  
        if self.drumFretButtons == None:
          if n == 4:
            continue
          whichFret = n+1
          if whichFret == 4:
            whichFret = 0
            #reversing fret 0 since it's angled in Rock Band
            texSize = (whichFret/5.0+0.2,whichFret/5.0)
          else:
            texSize = (whichFret/5.0,whichFret/5.0+0.2)

          texY = (0.0,1.0/3.0)
          if pressed:
            texY = (1.0/3.0,2.0/3.0)
          if self.hit[n]:
            texY = (2.0/3.0,1.0)

        elif self.battleStatus[3] and self.battleFrets != None and self.battleBreakString == n:
          texSize = (n/5.0+.042,n/5.0+0.158)
          size = (.30, .40)
          fretPos = 8 - round((self.battleBreakNow/self.battleBreakLimit) * 8)
          texY = (fretPos/8.0,(fretPos + 1.0)/8)

        else:
          if n == 4: 
            if pressed:  #drums bass fret press
              texY = (3.0 / self.fretImgColNumber, 4.0 / self.fretImgColNumber)
            else:        #fret normal bass drum
              texY = (1.0 / self.fretImgColNumber, 2.0 / self.fretImgColNumber)
          else: #fret normal
            texY = (0.0, 1.0 / self.fretImgColNumber)

          if controls.getState(self.keys[n]) or controls.getState(self.keys[n+5]) or pressed:#fret press
            texY = (2.0 / self.fretImgColNumber, 3.0 / self.fretImgColNumber)
            
          elif n == 4 and self.hit[0]:#drum bass hit fret
            texY = (5.0 / self.fretImgColNumber, 1.0)

          elif self.hit[n] or (self.battleStatus[3] and self.battleBreakString == n):#frets on note hit
            texY = (4.0 / self.fretImgColNumber, 5.0 / self.fretImgColNumber)
            
        self.engine.draw3Dtex(self.fretButtons, vertex = (size[0],size[1],-size[0],-size[1]), texcoord = (texSize[0], texY[0], texSize[1], texY[1]),
                                coord = (x,v,0), multiples = True,color = fretColor, depth = True)
  
      else:
        self.keypos = self.engine.theme.drumkeypos
        self.keyrot = self.engine.theme.drumkeyrot

        texture = None
        model = self.keyMesh
        if self.keytex:
          if n == 0:
            texture = self.keytexb.texture
          elif n == 1:
            texture = self.keytexc.texture
          elif n == 2:
            texture = self.keytexd.texture
          elif n == 3:
            texture = self.keytexa.texture
          elif n == 4 and self.keytexopen:
            texture = self.keytexopen.texture

        if n == 4:
          model = self.keyMeshOpen
              
        c = [.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, v]
        self.render3DKey(texture, model, x, y, c, n, f)
          
    glDisable(GL_DEPTH_TEST)      

  def renderFreestyleFlames(self, visibility, controls):
    if self.flameColors[0][0] == -1:
      return

    w = self.boardWidth / self.strings

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

          ff = 1 + 0.25       
          y = v + ff / 6
          glBlendFunc(GL_ONE, GL_ONE)

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

        self.renderFlames(song, pos, controls)    #MFH - only when freestyle inactive!
        

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

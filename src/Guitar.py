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

from Mesh import Mesh
from Neck import Neck
import random
from copy import deepcopy
from Shader import shaders

from Instrument import *
from OpenGL.GL import *
import Song

class Guitar(Instrument):
  def __init__(self, engine, playerObj, editorMode = False, player = 0, bass = False):
    Instrument.__init__(self, engine, playerObj, player)

    self.isDrum = False
    self.isBassGuitar = bass
    self.isVocal = False

    self.strings        = 5

    self.debugMode = False
    self.gameMode2p = self.engine.world.multiMode
    self.matchingNotes = []
    
    self.starSpinFrameIndex = 0

    self.starSpinFrames = 16
    
            
    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("Guitar class init...")
    
    self.lastPlayedNotes = []   #MFH - for reverting when game discovers it implied incorrectly
    
    self.missedNotes    = []
    self.missedNoteNums = []
    self.editorMode     = editorMode

    self.Animspeed      = 30#Lower value = Faster animations
    #For Animated Starnotes
    self.indexCount     = 0


    self.freestyleHitFlameCounts = [0 for n in range(self.strings+1)]    #MFH

    self.fretWeight     = [0.0] * self.strings
    self.fretActivity   = [0.0] * self.strings

    self.drumFretButtons = None

    #myfingershurt:
    self.hopoStyle        = self.engine.config.get("game", "hopo_system")
    self.gh2sloppy        = self.engine.config.get("game", "gh2_sloppy")
    if self.gh2sloppy == 1:
      self.hopoStyle = 4
    self.sfxVolume    = self.engine.config.get("audio", "SFX_volume")
    
    #blazingamer
    self.killfx = self.engine.config.get("performance", "killfx")
    self.killCount         = 0
    
    self.bigMax = 1
    
    #Get theme
    themename = self.engine.data.themeLabel
    #now theme determination logic is only in data.py:
    self.theme = self.engine.data.theme

    self.oFlash = None

    self.lanenumber     = float(5)
    self.fretImgColNumber = float(3)

    #myfingershurt:
    self.bassGrooveNeckMode = self.engine.config.get("game", "bass_groove_neck")

    self.loadNotes()
    
    if self.gameMode2p == 6:
      if not engine.loadImgDrawing(self, "battleFrets", os.path.join("themes", themename,"battle_frets.png")):
        self.battleFrets = None

    if self.twoDkeys == True:
      engine.loadImgDrawing(self, "fretButtons", os.path.join("themes",themename,"fretbuttons.png"))
    else:
      defaultKey = False
      #MFH - can't use IOError for fallback logic for a Mesh() call... 
      if self.engine.fileExists(os.path.join("themes", themename, "key.dae")):
        engine.resource.load(self,  "keyMesh",  lambda: Mesh(engine.resource.fileName("themes", themename, "key.dae")))
      else:
        engine.resource.load(self,  "keyMesh",  lambda: Mesh(engine.resource.fileName("key.dae")))
        defaultKey = True
      
      if defaultKey:
        self.keytex = False
      else:
        for i in range(5):
          if engine.loadImgDrawing(self,  "keytex"+chr(97+i),  os.path.join("themes", themename, "keytex_"+chr(97+i)+".png")):
            self.keytex = True
          else:
            self.keytex = False
            break
    
                                                           
    #inkk: loading theme-dependent tail images
    #myfingershurt: must ensure the new tails don't affect the Rock Band mod...
    self.simpleTails = False

    for i in range(0,7):
      if not engine.loadImgDrawing(self, "tail"+str(i), os.path.join("themes",themename,"tails","tail"+str(i)+".png"),  textureSize = (128, 128)):
        self.simpleTails = True
        break
      if not engine.loadImgDrawing(self, "taile"+str(i), os.path.join("themes",themename,"tails","taile"+str(i)+".png"),  textureSize = (128, 128)):
        self.simpleTails = True
        break
      if not engine.loadImgDrawing(self, "btail"+str(i), os.path.join("themes",themename,"tails","btail"+str(i)+".png"),  textureSize = (128, 128)):
        self.simpleTails = True
        break
      if not engine.loadImgDrawing(self, "btaile"+str(i), os.path.join("themes",themename,"tails","btaile"+str(i)+".png"),  textureSize = (128, 128)):
        self.simpleTails = True
        break
    
    if self.simpleTails:
      Log.debug("Simple tails used; complex tail loading error...")
      if not engine.loadImgDrawing(self, "tail1", os.path.join("themes",themename,"tail1.png"),  textureSize = (128, 128)):
        engine.loadImgDrawing(self, "tail1", "tail1.png",  textureSize = (128, 128))
      engine.loadImgDrawing(self, "tail2", os.path.join("themes",themename,"tail2.png"),  textureSize = (128, 128))
      if not engine.loadImgDrawing(self, "bigTail1", os.path.join("themes",themename,"bigtail1.png"),  textureSize = (128, 128)):
        engine.loadImgDrawing(self, "bigTail1", "bigtail1.png",  textureSize = (128, 128))
      engine.loadImgDrawing(self, "bigTail2", os.path.join("themes",themename,"bigtail2.png"),  textureSize = (128, 128))


    if not engine.loadImgDrawing(self, "kill1", os.path.join("themes", themename, "kill1.png"),  textureSize = (128, 128)):
      engine.loadImgDrawing(self, "kill1", "kill1.png",  textureSize = (128, 128))
    engine.loadImgDrawing(self, "kill2", os.path.join("themes", themename, "kill2.png"),  textureSize = (128, 128))

    #MFH - freestyle tails (for drum fills & BREs)
    if not engine.loadImgDrawing(self, "freestyle1", os.path.join("themes", themename, "freestyletail1.png"),  textureSize = (128, 128)):
      engine.loadImgDrawing(self, "freestyle1", "freestyletail1.png",  textureSize = (128, 128))
    engine.loadImgDrawing(self, "freestyle2", os.path.join("themes", themename, "freestyletail2.png"),  textureSize = (128, 128))
    
    
    self.twoChordMax = False

    self.rockLevel = 0.0

    self.neck = Neck(self.engine, self, playerObj)

  def loadNotes(self):
      
    get = lambda file: self.checkPath("notes", file)
	
    self.spActTex = None
	
    self.starspin = self.engine.config.get("performance", "starspin")
    if self.twoDnote:
      if self.starspin:
        if self.gameMode2p == 6: #battle multiplayer
          if self.engine.loadImgDrawing(self, "noteButtons", get("spinnotesbattle.png")):
            self.starSpinFrames = 8
          else:
            self.starspin = False
            if not self.engine.loadImgDrawing(self, "noteButtons", get("notesbattle.png")):
              self.engine.loadImgDrawing(self, "noteButtons", get("notes.png"))
        else: 
          if not self.engine.loadImgDrawing(self, "noteButtons", get("spinnotes.png")):
            self.starspin = False
            self.engine.loadImgDrawing(self, "noteButtons", get("notes.png"))
      else:
        if self.gameMode2p == 6: #battle multiplayer
          if not self.engine.loadImgDrawing(self, "noteButtons", get("notesbattle.png")):
            self.engine.loadImgDrawing(self, "noteButtons", get("notes.png"))
        else:
          self.engine.loadImgDrawing(self, "noteButtons", get("notes.png"))
    else:
      if self.engine.fileExists(get("note.dae")):
        self.engine.resource.load(self,  "noteMesh",  lambda: Mesh(self.engine.resource.fileName(get("note.dae"))))
      else: #fallback to the default in the data folder
        self.engine.resource.load(self,  "noteMesh",  lambda: Mesh(self.engine.resource.fileName("note.dae")))

      for i in range(5):
        if self.engine.loadImgDrawing(self,  "notetex"+chr(97+i),  get("notetex_"+chr(97+i)+".png")):
          self.notetex = True
        else:
          self.notetex = False
          break
        
      if self.engine.fileExists(get("star.dae")):  
        self.engine.resource.load(self,  "starMesh",  lambda: Mesh(self.engine.resource.fileName(get("star.dae"))))
      else:  
        self.starMesh = None

      for i in range(5):
        if self.engine.loadImgDrawing(self,  "startex"+chr(97+i),  get("startex_"+chr(97+i)+".png")):
          self.startex = True
        else:
          self.startex = False
          break

      for i in range(5):
        if self.engine.loadImgDrawing(self,  "staratex"+chr(97+i),  get("staratex_"+chr(97+i)+".png")):
          self.staratex = True
        else:
          self.staratex = False
          break
  
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

  def renderTail(self, length, sustain, kill, color, flat = False, tailOnly = False, isTappable = False, big = False, fret = 0, spNote = False, freestyleTail = 0, pos = 0):

    #volshebnyi - if freestyleTail == 0, act normally.
    #  if freestyleTail == 1, render an freestyle tail
    #  if freestyleTail == 2, render highlighted freestyle tail

    if not self.simpleTails:#Tail Colors
      tailcol = (1,1,1, color[3])
    else:
      if big == False and tailOnly == True:
        tailcol = (.6, .6, .6, color[3])
      else:
        tailcol = (color)
        #volshebnyi - tail color when sp is active
        if self.starPowerActive and self.theme != 2 and not color == (0,0,0,1):#8bit
          c = self.fretColors[5]
          tailcol = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], color[3]) 

    if flat:
      tailscale = (1, .1, 1)
    else:
      tailscale = None

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
                c = [self.killColor[0],self.killColor[1],self.killColor[2]]
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
              if kill:
                zsize = .25
                tex1 = self.kill1
                if self.kill2:
                  tex2 = self.kill2
                if not self.kill2:
                  tex2 = None
                #volshebnyi - killswitch tail width and color change
                kEffect = ( math.sin( pos / 50 ) + 1 ) /2
                size = (0.02+kEffect*0.15, s - zsize)
                c = [self.killColor[0],self.killColor[1],self.killColor[2]]
                if c != [0,0,0]:
                  for i in range(0,3):
                    c[i]=c[i]*kEffect+color[i]*(1-kEffect)
                  tailcol = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1) 
              else:
                zsize = .25
                size = (.11, s - zsize)
                tex1 = self.bigTail1
                if self.bigTail2:
                  tex2 = self.bigTail2
                if not self.bigTail2:
                  tex2 = None
            else:
              zsize = .15
              size = (.08, s - zsize)
              tex1 = self.tail1
              if self.tail2:
                tex2 = self.tail2
              if not self.tail2:
                tex2 = None
        
        else:   #freestyleTail > 0
          # render an inactive freestyle tail  (self.freestyle1 & self.freestyle2)
          zsize = .25  
          
          if self.freestyleActive:
            size = (.30, s - zsize)   #was .15
          else:
            size = (.15, s - zsize)   
          
          tex1 = self.freestyle1
          if self.freestyle2:
            tex2 = self.freestyle2
          if not self.freestyle2:
            tex2 = None
          if freestyleTail == 1:
            c1, c2, c3, c4 = color
            tailGlow = 1 - (pos - self.freestyleLastFretHitTime[fret] ) / self.freestylePeriod
            if tailGlow < 0:
              tailGlow = 0
            color = (c1 + c1*2.0*tailGlow, c2 + c2*2.0*tailGlow, c3 + c3*2.0*tailGlow, c4*0.6 + c4*0.4*tailGlow)    #MFH - this fades inactive tails' color darker                    
            
          tailcol = (color)
        if self.theme == 2 and freestyleTail == 0 and big and tailOnly and shaders.enable("tail"):
          color = (color[0]*1.5,color[1]*1.5,color[2]*1.5,1.0)
          shaders.setVar("color",color)
          if kill and self.killfx == 0:
            h = shaders.getVar("height")
            shaders.modVar("height",0.5,0.06/h-0.1)
          shaders.setVar("offset",(5.0-size[1],0.0))
          size=(size[0]*15,size[1])
          
          
        self.engine.draw3Dtex(tex1, vertex = (-size[0], 0, size[0], size[1]), texcoord = (0.0, 0.0, 1.0, 1.0),
                              scale = tailscale, color = tailcol)
        if tex2:
            self.engine.draw3Dtex(tex2, vertex = (-size[0], size[1], size[0], size[1] + (zsize)),
                                  scale = tailscale, texcoord = (0.0, 0.05, 1.0, 0.95), color = tailcol)

        shaders.disable()  

        #MFH - this block of code renders the tail "beginning" - before the note, for freestyle "lanes" only
        #volshebnyi
        if tex2:
          if freestyleTail > 0 and pos < self.freestyleStart + self.freestyleLength:
            self.engine.draw3Dtex(tex2, vertex = (-size[0], 0-(zsize), size[0], 0 + (.05)),
                                  scale = tailscale, texcoord = (0.0, 0.95, 1.0, 0.05), color = tailcol)
          

    if tailOnly:
      return

  def renderFreestyleLanes(self, visibility, song, pos):
    if not song:
      return
    if not song.readyToGo:
      return


    boardWindowMax = pos + self.currentPeriod * self.beatsPerBoard
    track = song.midiEventTrack[self.player]

    #MFH - render 5 freestyle tails when Song.freestyleMarkingNote comes up
    if self.freestyleEnabled:
      freestyleActive = False
      for time, event in track.getEvents(pos - self.freestyleOffset , boardWindowMax + self.freestyleOffset):
        if isinstance(event, Song.MarkerNote):
          if event.number == Song.freestyleMarkingNote:
            length     = (event.length - 50) / self.currentPeriod / self.beatsPerUnit
            w = self.boardWidth / self.strings
            self.freestyleLength = event.length #volshebnyi
            self.freestyleStart = time # volshebnyi
            z  = ((time - pos) / self.currentPeriod) / self.beatsPerUnit
            z2 = ((time + event.length - pos) / self.currentPeriod) / self.beatsPerUnit
      
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

  def renderTails(self, visibility, song, pos, killswitch):
    if not song:
      return
    if not song.readyToGo:
      return

    # Update dynamic period
    self.currentPeriod = self.neckSpeed

    self.killPoints = False

    w = self.boardWidth / self.strings
    
    track = song.track[self.player]

    num = 0
    enable = True
    renderedNotes = self.getRequiredNotesForRender(song,pos)
    for time, event in renderedNotes:
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
      z  = ((time - pos) / self.currentPeriod) / self.beatsPerUnit
      z2 = ((time + event.length - pos) / self.currentPeriod) / self.beatsPerUnit


      if z > self.boardLength * .8:
        f = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        f = min(1, max(0, 1 + z2))
      else:
        f = 1.0

      color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1 * visibility * f)
      if event.length > 120:
        length     = (event.length - 50) / self.currentPeriod / self.beatsPerUnit
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
            if self.gameMode2p == 6:
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
            self.neck.overdriveFlashCount = 0  #MFH - this triggers the oFlash strings & timer
            self.starPowerGained = True
            self.neck.ocount = 0

      if event.tappable < 2:
        isTappable = False
      else:
        isTappable = True
      
      # Clip the played notes to the origin
      #myfingershurt: this should be loaded once at init, not every render...
      if self.notedisappear == 0:#Notes keep on going when missed
        if event.played or event.hopod:#if the note isnt missed
          tailOnly = True
          length += z
          z = 0
          if length <= 0:
            continue
        if z < 0 and not (event.played or event.hopod):#if the note is missed 
          color = (.6, .6, .6, .5 * visibility * f)
          flat  = False 
      elif self.notedisappear == 1:#Notes disappear when missed
        if z < 0:#if note past frets
          if event.played or event.hopod:#if note was hit
            tailOnly = True
            length += z
            z = 0
            if length <= 0:
              continue
          else:#note missed
            color = (.6, .6, .6, .5 * visibility * f)
            flat  = False
      if self.notedisappear == 2:#turn red when missed
        if event.played or event.hopod:  #if the note isnt missed
          tailOnly = True
          length += z
          z = 0
          if length <= 0:
            continue
        if z < 0 and not (event.played or event.hopod): #if the note is missed 
          color = (1, 0, 0, 1)#turn note red
          flat  = False
          
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

      if self.battleStatus[8]:
        renderNote = random.randint(0,2)
      else:
        renderNote = 0
      if renderNote == 0:  
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
          proj  = 1.0 / self.currentPeriod / self.beatsPerUnit
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

  def renderFreestyleFlames(self, visibility, controls):
    if self.flameColors[0][0][0] == -1:
      return

    w = self.boardWidth / self.strings

    size = (.22, .22)
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
          
          flameSize = self.flameSizes[self.cappedScoreMult - 1][fretNum]
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
                self.engine.draw3Dtex(self.hitflames2Drawing, coord = (x+xOffset[step], y+yOffset[step], 0), rot = (90, 1, 0, 0),
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
                self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x+xOffset[step], y+yOffset[step], 0), rot = (90, 1, 0, 0),
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
      glEnable(GL_BLEND)
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
      glEnable(GL_COLOR_MATERIAL)

      if self.leftyMode:
        if not self.battleStatus[6]:
          glScalef(-1, 1, 1)
      elif self.battleStatus[6]:
        glScalef(-1, 1, 1)

      if self.freestyleActive:
        self.renderFreestyleLanes(visibility, song, pos) #MFH - render the lanes on top of the notes.
        self.renderFrets(visibility, song, controls)

        if self.hitFlamesPresent:   #MFH - only if present!
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

        self.renderFreestyleLanes(visibility, song, pos) #MFH - render the lanes on top of the notes.

        
        if self.hitFlamesPresent:   #MFH - only if present!
          self.renderHitTrails(visibility, song, pos, controls)
          self.renderFlames(visibility, song, pos, controls)    #MFH - only when freestyle inactive!
        
      if self.leftyMode:
        if not self.battleStatus[6]:
          glScalef(-1, 1, 1)
      elif self.battleStatus[6]:
        glScalef(-1, 1, 1)

  def getDoubleNotes(self, notes):
    if self.battleStatus[7] and notes != []:
      notes = sorted(notes, key=lambda x: x[0])
      curTime = 0
      tempnotes = []
      tempnumbers = []
      tempnote = None
      curNumbers = []
      noteCount = 0
      for time, note in notes:
        noteCount += 1
        if not isinstance(note, Note):
          if noteCount == len(notes) and len(curNumbers) < 3 and len(curNumbers) > 0:
            maxNote = curNumbers[0]
            minNote = curNumbers[0]
            for i in range(0, len(curNumbers)):
              if curNumbers[i] > maxNote:
                maxNote = curNumbers[i]
              if curNumbers[i] < minNote:
                minNote = curNumbers[i]
            curNumbers = []
            if maxNote < 4:
              tempnumbers.append(maxNote + 1)
            elif minNote > 0:
              tempnumbers.append(minNote - 1)
            else:
              tempnumbers.append(2)
          elif noteCount == len(notes) and len(curNumbers) > 2:
            tempnumbers.append(-1)
            curNumbers = []
          continue
        if time != curTime:
          if curTime != 0 and len(curNumbers) < 3:
            maxNote = curNumbers[0]
            minNote = curNumbers[0]
            for i in range(0, len(curNumbers)):
              if curNumbers[i] > maxNote:
                maxNote = curNumbers[i]
              if curNumbers[i] < minNote:
                minNote = curNumbers[i]
            curNumbers = []
            if maxNote < 4:
              tempnumbers.append(maxNote + 1)
            elif minNote > 0:
              tempnumbers.append(minNote - 1)
            else:
              tempnumbers.append(2)
          elif (curTime != 0 or noteCount == len(notes)) and len(curNumbers) > 2:
            tempnumbers.append(-1)
            curNumbers = []
          tempnotes.append((time,deepcopy(note)))
          curTime = time
          curNumbers.append(note.number)
          if noteCount == len(notes) and len(curNumbers) < 3:
            maxNote = curNumbers[0]
            minNote = curNumbers[0]
            for i in range(0, len(curNumbers)):
              if curNumbers[i] > maxNote:
                maxNote = curNumbers[i]
              if curNumbers[i] < minNote:
                minNote = curNumbers[i]
            curNumbers = []
            if maxNote < 4:
              tempnumbers.append(maxNote + 1)
            elif minNote > 0:
              tempnumbers.append(minNote - 1)
            else:
              tempnumbers.append(2)
          elif noteCount == len(notes) and len(curNumbers) > 2:
            tempnumbers.append(-1)
            curNumbers = []
        else:
          curNumbers.append(note.number)
          if noteCount == len(notes) and len(curNumbers) < 3:
            maxNote = curNumbers[0]
            minNote = curNumbers[0]
            for i in range(0, len(curNumbers)):
              if curNumbers[i] > maxNote:
                maxNote = curNumbers[i]
              if curNumbers[i] < minNote:
                minNote = curNumbers[i]
            curNumbers = []
            if maxNote < 4:
              tempnumbers.append(maxNote + 1)
            elif minNote > 0:
              tempnumbers.append(minNote - 1)
            else:
              tempnumbers.append(2)
          elif noteCount == len(notes) and len(curNumbers) > 2:
            tempnumbers.append(-1)
            curNumbers = []
      noteCount = 0
      for time, note in tempnotes:
        if tempnumbers[noteCount] != -1:
          note.number = tempnumbers[noteCount]
          noteCount += 1
          if time > self.battleStartTimes[7] + self.currentPeriod * self.beatsPerBoard and time < self.battleStartTimes[7] - self.currentPeriod * self.beatsPerBoard + self.battleDoubleLength:
            notes.append((time,note))
        else:
          noteCount += 1
    return sorted(notes, key=lambda x: x[0])


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
        self.playedNotes = []
        return True
      if not time in chords:
        chords[time] = []
      chords[time].append((time, note))

    #Make sure the notes are in the right time order
    chordlist = chords.values()
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
  
  def startPick(self, song, pos, controls, hopo = False):
    if hopo == True:
      res = startPick2(song, pos, controls, hopo)
      return res
    if not song:
      return False
    if not song.readyToGo:
      return False
    
    self.playedNotes = []
    
    self.matchingNotes = self.getRequiredNotesMFH(song, pos)

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
    
    self.matchingNotes = self.getRequiredNotesMFH(song, pos, hopo)

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
      
      if shaders.turnon:
        shaders.var["fret"][self.player][note.number]=shaders.time()
        shaders.var["fretpos"][self.player][note.number]=pos
        
      
      self.pickStartPos = pos
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

  def soloFreestylePick(self, song, pos, controls):
    numHits = 0
    for theFret in range(5):
      self.freestyleHit[theFret] = controls.getState(self.keys[theFret+5])
      if self.freestyleHit[theFret]:
        if shaders.turnon:
          shaders.var["fret"][self.player][theFret]=shaders.time()
          shaders.var["fretpos"][self.player][theFret]=pos
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
    
    # #MFH - Determine which frame to display for starpower notes
    # if self.starspin:
      # self.indexCount = self.indexCount + 1
      # if self.indexCount > self.Animspeed-1:
        # self.indexCount = 0
      # self.starSpinFrameIndex = (self.indexCount * self.starSpinFrames - (self.indexCount * self.starSpinFrames) % self.Animspeed) / self.Animspeed
      # if self.starSpinFrameIndex > self.starSpinFrames - 1:
        # self.starSpinFrameIndex = 0
        
    
    #myfingershurt: must not decrease SP if paused.
    if self.starPowerActive == True and self.paused == False:
      self.starPower -= ticks/self.starPowerDecreaseDivisor 
      if self.starPower <= 0:
        self.starPower = 0
        self.starPowerActive = False
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


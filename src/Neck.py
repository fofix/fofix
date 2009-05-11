#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2009 Team FoFiX                                     ##               2009 Blazingamer(n_hydock@comcast.net)              #
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


import Player
from Song import Note, Tempo, Bars
from Mesh import Mesh
import Theme
import random
from copy import deepcopy
import Shader

from OpenGL.GL import *
import math
from numpy import array, float32

#myfingershurt: needed for multi-OS file fetching
import os
import Log
import Song   #need the base song defines as well

class Neck:
  def __init__(self, engine, part, playerObj):

    self.engine         = engine
    self.player         = part.player
    self.part         = part

    self.isDrum = self.part.isDrum
    self.isBassGuitar = self.part.isBassGuitar
    self.isVocal = self.part.isVocal

    self.oNeckovr = None    #MFH - needs to be here to prevent crashes!    

    self.staticStrings  = self.engine.config.get("performance", "static_strings")

    self.indexFps       = self.engine.config.get("video", "fps") #QQstarS
    
    self.neckAlpha=[] # necks transparency
    self.neckAlpha.append( self.engine.config.get("game", "necks_alpha") ) # all necks
    self.neckAlpha.append( self.neckAlpha[0] * self.engine.config.get("game", "neck_alpha") ) # solo neck
    self.neckAlpha.append( self.neckAlpha[0] * self.engine.config.get("game", "solo_neck_alpha") ) # solo neck
    self.neckAlpha.append( self.neckAlpha[0] * self.engine.config.get("game", "bg_neck_alpha") ) # bass groove neck
    self.neckAlpha.append( self.neckAlpha[0] * self.engine.config.get("game", "overlay_neck_alpha") ) # overlay neck
    self.neckAlpha.append( self.neckAlpha[0] * self.engine.config.get("game", "fail_neck_alpha") ) # fail neck

    self.boardWidth     = Theme.neckWidth
    self.boardLength    = Theme.neckLength
    #death_au: fixed neck size
    if Theme.twoDnote == False or Theme.twoDkeys == False:
      self.boardWidth     = 3.6
      self.boardLength    = 9.0  

    self.beatsPerBoard  = 5.0
    self.beatsPerUnit   = self.beatsPerBoard / self.boardLength

    self.boardVtx       = array([[-self.boardWidth / 2, 0, -2],
                                 [self.boardWidth / 2, 0, -2],
                                 [-self.boardWidth / 2, 0, -1],
                                 [self.boardWidth / 2, 0, -1],
                                 [-self.boardWidth / 2, 0, self.boardLength * .7],
                                 [self.boardWidth / 2, 0, self.boardLength * .7],
                                 [-self.boardWidth / 2, 0, self.boardLength],
                                 [self.boardWidth / 2, 0, self.boardLength]], dtype=float32)

    self.neck = str(playerObj.neck)
    playerObj = None
    #Get theme
    themename = self.engine.data.themeLabel
    #now theme determination logic is only in data.py:
    self.theme = self.engine.data.theme

    self.incomingNeckMode = self.engine.config.get("game", "incoming_neck_mode")

    #blazingamer

    self.failcount = 0
    self.failcount2 = False
    self.spcount = 0
    self.spcount2 = 0
    self.bgcount = 0
    self.ovroverlay = self.engine.config.get("fretboard", "ovroverlay")
    self.ocount = 0

    self.currentBpm     = 120.0
    self.currentPeriod  = 60000.0 / self.currentBpm
    self.lastBpmChange  = -1.0
    self.baseBeat       = 0.0



    #racer: added RB beta frets option:
    self.rbnote = self.engine.config.get("game", "rbnote")

    #myfingershurt:
    self.bassGrooveNeckMode = self.engine.config.get("game", "bass_groove_neck")
    self.guitarSoloNeckMode = self.engine.config.get("game", "guitar_solo_neck")


    self.useMidiSoloMarkers = False

    if not engine.data.fileExists(os.path.join("necks", self.neck + ".png")) and not engine.data.fileExists(os.path.join("necks", "Neck_" + self.neck + ".png")):
      self.neck = str(engine.mainMenu.chosenNeck) #this neck is safe!

    # evilynux - Fixed random neck -- MFH: further fixing random neck
    if self.neck == "0" or self.neck == "Neck_0" or self.neck == "randomneck":
      self.neck = []
      # evilynux - improved loading logic to support arbitrary filenames
      for i in os.listdir(self.engine.resource.fileName("necks")):
        # evilynux - Special cases, ignore these...
        if( str(i) == "overdriveneck.png" or str(i) == "randomneck.png"  or str(i) == "Neck_0.png" or str(i)[-4:] != ".png" ):
          continue
        else:
          self.neck.append(str(i)[:-4]) # evilynux - filename w/o extension
      i = random.randint(1,len(self.neck))
      engine.loadImgDrawing(self, "neckDrawing", os.path.join("necks",self.neck[i]+".png"),  textureSize = (256, 256))
      Log.debug("Random neck chosen: " + self.neck[i])
    else:
      try:
        # evilynux - first assume the self.neck contains the full filename
        engine.loadImgDrawing(self, "neckDrawing", os.path.join("necks",self.neck+".png"),  textureSize = (256, 256))
      except IOError:
        engine.loadImgDrawing(self, "neckDrawing", os.path.join("necks","Neck_"+self.neck+".png"),  textureSize = (256, 256))



    if self.theme == 2:
      if self.rbnote == 1:
        #mfh - adding fallback for beta option
        try:
          engine.loadImgDrawing(self, "oSideBars", os.path.join("themes",themename,"overdrive side_barsbeta.png"),  textureSize = (256, 256))
          engine.loadImgDrawing(self, "oCenterLines", os.path.join("themes",themename,"overdrive center_linesbeta.png"),  textureSize = (256, 256))
          engine.loadImgDrawing(self, "oNeck", os.path.join("themes",themename,"overdriveneckbeta.png"),  textureSize = (256, 256))
        except IOError:
          try:
            engine.loadImgDrawing(self, "oSideBars", os.path.join("themes",themename,"overdrive side_bars.png"),  textureSize = (256, 256))
          except IOError:
            self.oSideBars = None
          try:
            engine.loadImgDrawing(self, "oCenterLines", os.path.join("themes",themename,"overdrive center_lines.png"),  textureSize = (256, 256))
          except IOError:
            self.oCenterLines = None
          try:
            engine.loadImgDrawing(self, "oNeck", os.path.join("themes",themename,"overdriveneck.png"),  textureSize = (256, 256))
          except IOError:
            self.oNeck = None
          try:
            engine.loadImgDrawing(self, "oNeckBass", os.path.join("themes",themename,"overdriveneck_bass.png"),  textureSize = (256, 256))
          except IOError:
            try:
              engine.loadImgDrawing(self, "oNeckBass", os.path.join("themes",themename,"overdriveneck.png"),  textureSize = (256, 256))
            except IOError:
              self.oNeckBass = None
          self.rbnote = 0
      else:
        if self.isDrum == True:
          try:
            engine.loadImgDrawing(self, "oSideBars", os.path.join("themes",themename,"drum_overdrive_side_bars.png"),  textureSize = (256, 256))
          except IOError:
            self.oSideBars = None
  
          try:
            engine.loadImgDrawing(self, "oCenterLines", os.path.join("themes",themename,"drum_overdrive_center_lines.png"))
          except IOError:
          #engine.loadImgDrawing(self, "centerLines", os.path.join("themes",themename,"center_lines.png"))
            self.oCenterLines = None

      
          #myfingershurt: the overdrive neck file should be in the theme folder... and also not required:
          try:
            engine.loadImgDrawing(self, "oNeck", os.path.join("themes",themename,"overdriveneck_drum.png"),  textureSize = (256, 256))
          except IOError:
            try:
              engine.loadImgDrawing(self, "oNeck", os.path.join("themes",themename,"overdriveneck.png"),  textureSize = (256, 256))
            except IOError:
              self.oNeck = None


        else:
          try:
            engine.loadImgDrawing(self, "oSideBars", os.path.join("themes",themename,"overdrive side_bars.png"),  textureSize = (256, 256))
          except IOError:
            self.oSideBars = None
          try:
            engine.loadImgDrawing(self, "oCenterLines", os.path.join("themes",themename,"overdrive center_lines.png"),  textureSize = (256, 256))
          except IOError:
            self.oCenterLines = None
          try:
            engine.loadImgDrawing(self, "oNeckBass", os.path.join("themes",themename,"overdriveneck_bass.png"),  textureSize = (256, 256))
          except IOError:
            try:
              engine.loadImgDrawing(self, "oNeckBass", os.path.join("themes",themename,"overdriveneck.png"),  textureSize = (256, 256))
            except IOError:
              self.oNeckBass = None
          try:
            engine.loadImgDrawing(self, "oNeck", os.path.join("themes",themename,"overdriveneck.png"),  textureSize = (256, 256))
          except IOError:
            self.oNeck = None
          
        try:
          engine.loadImgDrawing(self, "oNeckovr", os.path.join("themes",themename,"overdriveneckovr.png"),  textureSize = (256, 256))
        except IOError:
          self.oNeckovr = None

      #MFH: support for optional overdrive_string_flash.png
      self.overdriveFlashCounts = self.indexFps/4   #how many cycles to display the oFlash: self.indexFps/2 = 1/2 second

      if self.isDrum == True:
        try:
          engine.loadImgDrawing(self, "oFlash", os.path.join("themes",themename,"drum_overdrive_string_flash.png"),  textureSize = (256, 256))
        except IOError:
          self.oFlash = None
      else:
        try:
          engine.loadImgDrawing(self, "oFlash", os.path.join("themes",themename,"overdrive_string_flash.png"),  textureSize = (256, 256))
        except IOError:
          self.oFlash = None

      self.part.oFlash = self.oFlash

    if self.isDrum == True:
      try:
        engine.loadImgDrawing(self, "centerLines", os.path.join("themes",themename,"drumcenterlines.png"))
      except IOError:
        #engine.loadImgDrawing(self, "centerLines", os.path.join("themes",themename,"center_lines.png"))
        self.centerLines = None
    else:
      engine.loadImgDrawing(self, "centerLines", os.path.join("themes",themename,"center_lines.png"))

    engine.loadImgDrawing(self, "sideBars", os.path.join("themes",themename,"side_bars.png"))
    engine.loadImgDrawing(self, "bpm_halfbeat", os.path.join("themes",themename,"bpm_halfbeat.png"))
    engine.loadImgDrawing(self, "bpm_beat", os.path.join("themes",themename,"bpm_beat.png"))
    engine.loadImgDrawing(self, "bpm_measure", os.path.join("themes",themename,"bpm_measure.png"))

    if self.theme == 0 or self.theme == 1:

      self.oNeckovr = None #fixes GH theme crash

      if self.isDrum == True:
        #myfingershurt: the starpower neck file should be in the theme folder... and also not required:
        try:
          engine.loadImgDrawing(self, "oNeck", os.path.join("themes",themename,"starpowerneck_drum.png"),  textureSize = (256, 256))
        except IOError:
          try:
            engine.loadImgDrawing(self, "oNeck", os.path.join("themes",themename,"starpowerneck.png"),  textureSize = (256, 256))
          except IOError:
            self.oNeck = None
      else:
        #myfingershurt: the starpower neck file should be in the theme folder... and also not required:
        try:
          engine.loadImgDrawing(self, "oNeck", os.path.join("themes",themename,"starpowerneck.png"),  textureSize = (256, 256))
        except IOError:
          self.oNeck = None
        try:
          engine.loadImgDrawing(self, "oNeckBass", os.path.join("themes",themename,"starpowerneck_bass.png"),  textureSize = (256, 256))
        except IOError:
          try:
            engine.loadImgDrawing(self, "oNeckBass", os.path.join("themes",themename,"starpowerneck.png"),  textureSize = (256, 256))
          except IOError:
            self.oNeckBass = None


    #myfingershurt: Bass Groove neck:
    if self.isBassGuitar == True:
      if self.bassGrooveNeckMode > 0:
        if self.bassGrooveNeckMode == 1:  #replace neck
          try:
            engine.loadImgDrawing(self, "bassGrooveNeck", os.path.join("themes",themename,"bassgrooveneck.png"),  textureSize = (256, 256))
          except IOError:
            self.bassGrooveNeck = None
        elif self.bassGrooveNeckMode == 2:  #overlay neck
          try:
            engine.loadImgDrawing(self, "bassGrooveNeck", os.path.join("themes",themename,"bassgrooveneckovr.png"),  textureSize = (256, 256))
          except IOError:
            self.bassGrooveNeck = None
      else:
        self.bassGrooveNeck = None
    else:
      self.bassGrooveNeck = None



    #myfingershurt: Guitar Solo neck:
    if self.isBassGuitar == False and self.isVocal == False and self.isDrum == False:
      if self.guitarSoloNeckMode > 0:
        if self.guitarSoloNeckMode == 1:  #replace neck
          try:
            engine.loadImgDrawing(self, "guitarSoloNeck", os.path.join("themes",themename,"guitarsoloneck.png"),  textureSize = (256, 256))
          except IOError:
            self.guitarSoloNeck = None
        elif self.guitarSoloNeckMode == 2:  #overlay neck
          try:
            engine.loadImgDrawing(self, "guitarSoloNeck", os.path.join("themes",themename,"guitarsoloneckovr.png"),  textureSize = (256, 256))
          except IOError:
            self.guitarSoloNeck = None
      else:
        self.guitarSoloNeck = None
    else:
      self.guitarSoloNeck = None

    try:
      engine.loadImgDrawing(self, "failNeck", os.path.join("themes",themename,"failneck.png"))
    except IOError:
      engine.loadImgDrawing(self, "failNeck", os.path.join("failneck.png"))


    self.isFailing = False
    self.canGuitarSolo = False
    self.guitarSolo = False
    self.fretboardHop = 0.00  #stump
    self.scoreMultiplier = 1
    self.coOpFailed = False
    self.coOpRestart = False
    self.starPowerActive = False
    self.overdriveFlashCount = self.part.overdriveFlashCounts

  def updateGuitarSettings(self):
    self.fretboardHop = self.part.fretboardHop  #stump
    self.canGuitarSolo = self.part.canGuitarSolo
    self.guitarSolo = self.part.guitarSolo
    self.overdriveFlashCount = self.part.overdriveFlashCounts
    self.coOpFailed = self.part.coOpFailed
    self.coOpRestart = self.part.coOpRestart
    self.starPowerActive = self.part.starPowerActive
    self.isFailing = self.part.isFailing
    self.scoreMultiplier = self.part.scoreMultiplier
    self.currentBpm     = self.part.currentBpm
    self.currentPeriod  = self.part.currentPeriod
    self.lastBpmChange  = self.part.lastBpmChange

  def renderIncomingNeck(self, visibility, song, pos, time, neckTexture):   #MFH - attempt to "scroll" an incoming guitar solo neck towards the player
    if not song:
      return
    if not song.readyToGo:
      return
    
    def project(beat):
      return 0.125 * beat / self.beatsPerUnit    # glorandwarf: was 0.12

    v            = visibility
    w            = self.boardWidth
    l            = self.boardLength

    #offset       = (pos - self.lastBpmChange) / self.currentPeriod + self.baseBeat 
    offset = 0

    z  = ((time - pos) / self.currentPeriod) / self.beatsPerUnit

    color = (1,1,1)

    glEnable(GL_TEXTURE_2D)
    if neckTexture:
      neckTexture.texture.bind()


    glBegin(GL_TRIANGLE_STRIP)
    glColor4f(color[0],color[1],color[2], 0)
    glTexCoord2f(0.0, project(offset - 2 * self.beatsPerUnit))
    #glVertex3f(-w / 2, 0, -2)
    glVertex3f(-w / 2, 0, z)   #point A
    glTexCoord2f(1.0, project(offset - 2 * self.beatsPerUnit))
    #glVertex3f( w / 2, 0, -2)
    glVertex3f( w / 2, 0, z)   #point B

    
    glColor4f(color[0],color[1],color[2], v)
    glTexCoord2f(0.0, project(offset - 1 * self.beatsPerUnit))
    #glVertex3f(-w / 2, 0, -1)
    glVertex3f(-w / 2, 0, z+1)   #point C
    glTexCoord2f(1.0, project(offset - 1 * self.beatsPerUnit))
    #glVertex3f( w / 2, 0, -1)
    glVertex3f( w / 2, 0, z+1)   #point D
    
    glTexCoord2f(0.0, project(offset + l * self.beatsPerUnit * .7))
    #glVertex3f(-w / 2, 0, l * .7)
    glVertex3f(-w / 2, 0, z+2+l * .7) #point E
    glTexCoord2f(1.0, project(offset + l * self.beatsPerUnit * .7))
    #glVertex3f( w / 2, 0, l * .7)
    glVertex3f( w / 2, 0, z+2+l * .7) #point F
    
    glColor4f(color[0],color[1],color[2], 0)
    glTexCoord2f(0.0, project(offset + l * self.beatsPerUnit))
    #glVertex3f(-w / 2, 0, l)
    glVertex3f(-w / 2, 0, z+2+l)    #point G
    glTexCoord2f(1.0, project(offset + l * self.beatsPerUnit))
    #glVertex3f( w / 2, 0, l)
    glVertex3f( w / 2, 0, z+2+l)    #point H
    glEnd()
    
    glDisable(GL_TEXTURE_2D)


  def renderIncomingNecks(self, visibility, song, pos):
    if not song:
      return
    if not song.readyToGo:
      return

    boardWindowMin = pos - self.currentPeriod * 2
    boardWindowMax = pos + self.currentPeriod * self.beatsPerBoard
    track = song.midiEventTrack[self.player]


    if self.incomingNeckMode > 0:   #if enabled


      #if self.song.hasStarpowerPaths and self.song.midiStyle == Song.MIDI_TYPE_RB:  
      if self.useMidiSoloMarkers:
        for time, event in track.getEvents(boardWindowMin, boardWindowMax):
          if isinstance(event, Song.MarkerNote):
            if event.number == Song.starPowerMarkingNote:
              if self.guitarSoloNeck:
                if event.endMarker:   #solo end
                  if self.incomingNeckMode == 2:    #render both start and end incoming necks
                    if self.guitarSolo:   #only until the end of the guitar solo!
                      if self.starPowerActive and self.oNeck:
                        neckImg = self.oNeck
                      elif self.scoreMultiplier > 4 and self.bassGrooveNeck != None and self.bassGrooveNeckMode == 1:
                        neckImg = self.bassGrooveNeck
                      else:
                        neckImg = self.neckDrawing
                      self.renderIncomingNeck(visibility, song, pos, time, neckImg)
                else:   #solo start
                  if not self.guitarSolo:   #only until guitar solo starts!
                    neckImg = self.guitarSoloNeck
                    self.renderIncomingNeck(visibility, song, pos, time, neckImg)
              

      else:   #fall back on text-based guitar solo marking track
        for time, event in song.eventTracks[Song.TK_GUITAR_SOLOS].getEvents(boardWindowMin, boardWindowMax):
          if self.canGuitarSolo and self.guitarSoloNeck:
            if event.text.find("ON") >= 0:
              if not self.guitarSolo:   #only until guitar solo starts!
                neckImg = self.guitarSoloNeck
                self.renderIncomingNeck(visibility, song, pos, time, neckImg)
            #else: #event.text.find("OFF"):
            elif self.incomingNeckMode == 2:    #render both start and end incoming necks
              if self.guitarSolo:   #only until the end of the guitar solo!
                if self.starPowerActive and self.oNeck:
                  neckImg = self.oNeck
                elif self.scoreMultiplier > 4 and self.bassGrooveNeck != None and self.bassGrooveNeckMode == 1:
                  neckImg = self.bassGrooveNeck
                else:
                  neckImg = self.neckDrawing
                self.renderIncomingNeck(visibility, song, pos, time, neckImg)


  def renderNeckMethod(self, visibility, offset, neck, alpha = False): #blazingamer: New neck rendering method
    
    def project(beat):
      return 0.125 * beat / self.beatsPerUnit    # glorandwarf: was 0.12
      
    
    if self.starPowerActive and self.theme == 0:#8bit
      color = Theme.fretColors[5] #self.spColor #(.3,.7,.9)
    elif self.starPowerActive and self.theme == 1:
      color = Theme.fretColors[5] #self.spColor #(.3,.7,.9)
    else:
      color = (1,1,1)

    v            = visibility
    l            = self.boardLength

    glEnable(GL_TEXTURE_2D)

    if alpha == True:
      glBlendFunc(GL_ONE, GL_ONE)
    neck.texture.bind()
    neck_col  = array([[color[0],color[1],color[2], 0],
                       [color[0],color[1],color[2], 0],
                       [color[0],color[1],color[2], v],
                       [color[0],color[1],color[2], v],
                       [color[0],color[1],color[2], v],
                       [color[0],color[1],color[2], v],
                       [color[0],color[1],color[2], 0],
                       [color[0],color[1],color[2], 0]], dtype=float32)
    neck_tex  = array([[0.0, project(offset - 2 * self.beatsPerUnit)],
                       [1.0, project(offset - 2 * self.beatsPerUnit)],
                       [0.0, project(offset - 1 * self.beatsPerUnit)],
                       [1.0, project(offset - 1 * self.beatsPerUnit)],
                       [0.0, project(offset + l * self.beatsPerUnit * .7)],
                       [1.0, project(offset + l * self.beatsPerUnit * .7)],
                       [0.0, project(offset + l * self.beatsPerUnit)],
                       [1.0, project(offset + l * self.beatsPerUnit)]], dtype=float32)
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_COLOR_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY);
    glVertexPointerf(self.boardVtx)
    glColorPointerf(neck_col)
    glTexCoordPointerf(neck_tex)
    glDrawArrays(GL_TRIANGLE_STRIP, 0, self.boardVtx.shape[0])
    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_COLOR_ARRAY)
    glDisableClientState(GL_TEXTURE_COORD_ARRAY);

    if alpha == True:
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
      
    glDisable(GL_TEXTURE_2D)
    
  def renderNeck(self, visibility, song, pos):     
    if not song:
      return
    if not song.readyToGo:
      return
    
    v            = visibility
    w            = self.boardWidth
    l            = self.boardLength

    offset       = (pos - self.lastBpmChange) / self.currentPeriod + self.baseBeat 

    #myfingershurt: every theme can have oNeck:

    if self.guitarSolo and self.guitarSoloNeck != None and self.guitarSoloNeckMode == 1:
      neck = self.guitarSoloNeck
    elif self.scoreMultiplier > 4 and self.bassGrooveNeck != None and self.bassGrooveNeckMode == 1:
      neck = self.bassGrooveNeck
    elif self.starPowerActive and not (self.spcount2 != 0 and self.spcount < 1.2) and self.oNeck and self.scoreMultiplier <= 4:
      if self.isBassGuitar and self.oNeckBass:
        neck = self.oNeckBass
      else:
        neck = self.oNeck
    else:
      neck = self.neckDrawing

    
    if not (self.guitarSolo and self.guitarSoloNeck != None and self.guitarSoloNeckMode == 2):
      self.renderNeckMethod(v*self.neckAlpha[1], offset, neck)

    if self.bgcount > 0 and self.bassGrooveNeck != None and self.bassGrooveNeckMode == 2:   #static bass groove overlay
      self.renderNeckMethod(v*self.bgcount*self.neckAlpha[3], 0, self.bassGrooveNeck)
      
    elif self.guitarSolo and self.guitarSoloNeck != None and self.guitarSoloNeckMode == 2:   #static overlay
      self.renderNeckMethod(v*self.neckAlpha[2], 0, self.guitarSoloNeck)
      
    if self.spcount2 != 0 and self.spcount < 1.2 and self.oNeck:   #static overlay
      if self.oNeckovr != None and (self.scoreMultiplier > 4 or self.guitarSolo):
        neck = self.oNeckovr
      else:
        if self.isBassGuitar and self.oNeckBass:
          neck = self.oNeckBass
        else:
          neck = self.oNeck
          
      self.renderNeckMethod(self.spcount*self.neckAlpha[4], offset, neck)
      
    
      
    if self.starPowerActive and not (self.spcount2 != 0 and self.spcount < 1.2) and self.oNeck and (self.scoreMultiplier > 4 or self.guitarSolo):   #static overlay

      if self.oNeckovr != None:
        neck = self.oNeckovr
      else:
        if self.isBassGuitar and self.oNeckBass:
          neck = self.oNeckBass
        else:
          neck = self.oNeck
        alpha = True

      self.renderNeckMethod(v*self.neckAlpha[4], offset, neck, alpha)

    if Shader.list.enabled:
      posx = Shader.list.time()
      fret = []
      for i in range(5):
        fret.append(max(posx - Shader.list.var["fret"][i] + 0.7,0.01))
      r = 1.2 / fret[1] + 0.6 / fret[2] + 0.8 / fret[4]
      g = 1.2 / fret[0] + 0.6 / fret[2] + 0.4 / fret[4]
      b = 1.2 / fret[3]
      a = (r+g+b)/70.0
      Shader.list.var["color"]=(r,g,b,a*2.0)
      
    if Shader.list.enable("neck"):
      Shader.list.setVar("fretcol","color")
      Shader.list.setVar("fail",self.isFailing)
      Shader.list.update()
      glBegin(GL_TRIANGLE_STRIP)
      glVertex3f(-w / 2, 0.1, -2)
      glVertex3f(w / 2, 0.1, -2)
      glVertex3f(-w / 2, 0.1, l)
      glVertex3f(w / 2, 0.1, l)
      glEnd()
      Shader.list.disable()
    else:
      if self.isFailing:
        self.renderNeckMethod(self.failcount*self.neckAlpha[5], 0, self.failNeck)
        
    if (self.guitarSolo or self.starPowerActive) and self.theme == 1:
      Shader.list.var["solocolor"]=(0.3,0.7,0.9,0.6)
    else:
      Shader.list.var["solocolor"]=(0.0,)*4


  def drawTrack(self, visibility, song, pos):
    if not song:
      return
    if not song.readyToGo:
      return

    def project(beat):
      return 0.125 * beat / self.beatsPerUnit    # glorandwarf: was 0.12

    if self.theme == 0 or self.theme == 1:
      size = 2
    else:
      size = 0

    v            = visibility
    w            = self.boardWidth
    l            = self.boardLength

    offset       = (pos - self.lastBpmChange) / self.currentPeriod + self.baseBeat 

    glEnable(GL_TEXTURE_2D)
    
    #MFH - logic to briefly display oFlash
    if self.theme == 2 and self.overdriveFlashCount < self.overdriveFlashCounts and self.oFlash:
      self.overdriveFlashCount = self.overdriveFlashCount + 1
      self.oFlash.texture.bind()
    elif self.theme == 2 and self.starPowerActive and self.oCenterLines:
      self.oCenterLines.texture.bind()
    else:
      self.centerLines.texture.bind()

    if self.staticStrings:    #MFH
    
      glBegin(GL_TRIANGLE_STRIP)
      glColor4f(1, 1, 1, v)
      glTexCoord2f(0.0, project(-2 * self.beatsPerUnit))
      glVertex3f(-w / 2, 0, -2+size)
      glTexCoord2f(1.0, project(-2 * self.beatsPerUnit))
      glVertex3f( w / 2, 0, -2+size)
      
      glColor4f(1, 1, 1, v)
      glTexCoord2f(0.0, project(-1 * self.beatsPerUnit))
      glVertex3f(-w / 2, 0, -1+size)
      glTexCoord2f(1.0, project(-1 * self.beatsPerUnit))
      glVertex3f( w / 2, 0, -1+size)
      
      glTexCoord2f(0.0, project(l * self.beatsPerUnit * .7))
      glVertex3f(-w / 2, 0, l * .7)
      glTexCoord2f(1.0, project(1 * self.beatsPerUnit * .7))
      glVertex3f( w / 2, 0, l * .7)
      
      glColor4f(1, 1, 1, 0)
      glTexCoord2f(0.0, project(l * self.beatsPerUnit))
      glVertex3f(-w / 2, 0, l)
      glTexCoord2f(1.0, project(1 * self.beatsPerUnit))
      glVertex3f( w / 2, 0, l)

    else:   #MFH: original moving strings

      glBegin(GL_TRIANGLE_STRIP)
      glColor4f(1, 1, 1, v)
      glTexCoord2f(0.0, project(offset - 2 * self.beatsPerUnit))
      glVertex3f(-w / 2, 0, -2+size)
      glTexCoord2f(1.0, project(offset - 2 * self.beatsPerUnit))
      glVertex3f( w / 2, 0, -2+size)
      
      glColor4f(1, 1, 1, v)
      glTexCoord2f(0.0, project(offset - 1 * self.beatsPerUnit))
      glVertex3f(-w / 2, 0, -1+size)
      glTexCoord2f(1.0, project(offset - 1 * self.beatsPerUnit))
      glVertex3f( w / 2, 0, -1+size)
      
      glTexCoord2f(0.0, project(offset + l * self.beatsPerUnit * .7))
      glVertex3f(-w / 2, 0, l * .7)
      glTexCoord2f(1.0, project(offset + l * self.beatsPerUnit * .7))
      glVertex3f( w / 2, 0, l * .7)
      
      glColor4f(1, 1, 1, 0)
      glTexCoord2f(0.0, project(offset + l * self.beatsPerUnit))
      glVertex3f(-w / 2, 0, l)
      glTexCoord2f(1.0, project(offset + l * self.beatsPerUnit))
      glVertex3f( w / 2, 0, l)

    glEnd()

    glDisable(GL_TEXTURE_2D)

  def drawSideBars(self, visibility, song, pos):
    if not song:
      return
    if not song.readyToGo:
      return

    def project(beat):
      return 0.125 * beat / self.beatsPerUnit  # glorandwarf: was 0.12

    v            = visibility
    w            = self.boardWidth + 0.15
    l            = self.boardLength

    offset       = (pos - self.lastBpmChange) / self.currentPeriod + self.baseBeat 

    c = (1,1,1)

    glEnable(GL_TEXTURE_2D)
    if self.theme == 2 and self.starPowerActive and self.oSideBars:
      self.oSideBars.texture.bind()
    else:
      self.sideBars.texture.bind()
    
    glBegin(GL_TRIANGLE_STRIP)
    glColor4f(c[0], c[1], c[2], 0)
    glTexCoord2f(0.0, project(offset - 2 * self.beatsPerUnit))
    glVertex3f(-w / 2, 0, -2)
    glTexCoord2f(1.0, project(offset - 2 * self.beatsPerUnit))
    glVertex3f( w / 2, 0, -2)
    
    glColor4f(c[0], c[1], c[2], v)
    glTexCoord2f(0.0, project(offset - 1 * self.beatsPerUnit))
    glVertex3f(-w / 2, 0, -1)
    glTexCoord2f(1.0, project(offset - 1 * self.beatsPerUnit))
    glVertex3f( w / 2, 0, -1)
    
    glTexCoord2f(0.0, project(offset + l * self.beatsPerUnit * .7))
    glVertex3f(-w / 2, 0, l * .7)
    glTexCoord2f(1.0, project(offset + l * self.beatsPerUnit * .7))
    glVertex3f( w / 2, 0, l * .7)
    
    glColor4f(c[0], c[1], c[2], 0)
    glTexCoord2f(0.0, project(offset + l * self.beatsPerUnit))
    glVertex3f(-w / 2, 0, l)
    glTexCoord2f(1.0, project(offset + l * self.beatsPerUnit))
    glVertex3f( w / 2, 0, l)
    glEnd()

    glDisable(GL_TEXTURE_2D)
    
    if self.theme == 1:   
      if Shader.list.enable("sololight"):
        Shader.list.modVar("color",Shader.list.var["solocolor"])
        Shader.list.setVar("offset",(-3.5,-w/2))
        glBegin(GL_TRIANGLE_STRIP)
        glVertex3f(w / 2-1.0, 0.4, -2)
        glVertex3f(w / 2+1.0, 0.4, -2)
        glVertex3f(w / 2-1.0, 0.4, l)
        glVertex3f(w / 2+1.0, 0.4, l)
        glEnd()   
        Shader.list.setVar("offset",(-3.5,w/2))
        Shader.list.setVar("time",Shader.list.time()+0.5)
        glBegin(GL_TRIANGLE_STRIP)
        glVertex3f(-w / 2+1.0, 0.4, -2)
        glVertex3f(-w / 2-1.0, 0.4, -2)
        glVertex3f(-w / 2+1.0, 0.4, l)
        glVertex3f(-w / 2-1.0, 0.4, l)
        glEnd()  
        Shader.list.disable()

  def drawBPM(self, visibility, song, pos):
    if not song:
      return
    if not song.readyToGo:
      return


    v            = visibility
    w            = self.boardWidth

    track = song.track[self.player]

    glEnable(GL_TEXTURE_2D)

    for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard):
      if not isinstance(event, Bars):
        continue   

      glPushMatrix()

      z  = ((time - pos) / self.currentPeriod) / self.beatsPerUnit
      z2 = ((time + event.length - pos) / self.currentPeriod) / self.beatsPerUnit

      if z > self.boardLength:
        f = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        f = min(1, max(0, 1 + z2))
      else:
        f = 1.0
        
      if event.barType == 0: #half-beat
        sw  = 0.1 #width
        self.bpm_halfbeat.texture.bind()
      elif event.barType == 1: #beat
        sw  = 0.1 #width
        self.bpm_beat.texture.bind()
      elif event.barType == 2: #measure
        sw  = 0.1 #width
        self.bpm_measure.texture.bind()

      glColor4f(1, 1, 1, v)
      glBegin(GL_TRIANGLE_STRIP)
      glTexCoord2f(0.0, 1.0)
      glVertex3f(-(w / 2), 0, z + sw)
      glTexCoord2f(0.0, 0.0)
      glVertex3f(-(w / 2), 0, z - sw)
      glTexCoord2f(1.0, 1.0)
      glVertex3f(w / 2,    0, z + sw)
      glTexCoord2f(1.0, 0.0)
      glVertex3f(w / 2,    0, z - sw)
      glEnd()
      glPopMatrix()

    glDisable(GL_TEXTURE_2D)
    
  def renderTracks(self, visibility):
    if self.tracksColor[0] == -1:
      return
    w = self.boardWidth / self.strings
    v = 1.0 - visibility

    if self.editorMode:
      x = (self.strings / 2 - self.selectedString) * w
      s = 2 * w / self.strings
      z1 = -0.5 * visibility ** 2
      z2 = (self.boardLength - 0.5) * visibility ** 2
      
      glColor4f(1, 1, 1, .15)
      
      glBegin(GL_TRIANGLE_STRIP)
      glVertex3f(x - s, 0, z1)
      glVertex3f(x + s, 0, z1)
      glVertex3f(x - s, 0, z2)
      glVertex3f(x + s, 0, z2)
      glEnd()

    sw = 0.025
    for n in range(self.strings - 1, -1, -1):
      glBegin(GL_TRIANGLE_STRIP)
      glColor4f(self.tracksColor[0], self.tracksColor[1], self.tracksColor[2], 0)
      glVertex3f((n - self.strings / 2) * w - sw, -v, -2)
      glVertex3f((n - self.strings / 2) * w + sw, -v, -2)
      glColor4f(self.tracksColor[0], self.tracksColor[1], self.tracksColor[2], (1.0 - v) * .75)
      glVertex3f((n - self.strings / 2) * w - sw, -v, -1)
      glVertex3f((n - self.strings / 2) * w + sw, -v, -1)
      glColor4f(self.tracksColor[0], self.tracksColor[1], self.tracksColor[2], (1.0 - v) * .75)
      glVertex3f((n - self.strings / 2) * w - sw, -v, self.boardLength * .7)
      glVertex3f((n - self.strings / 2) * w + sw, -v, self.boardLength * .7)
      glColor4f(self.tracksColor[0], self.tracksColor[1], self.tracksColor[2], 0)
      glVertex3f((n - self.strings / 2) * w - sw, -v, self.boardLength)
      glVertex3f((n - self.strings / 2) * w + sw, -v, self.boardLength)
      glEnd()
      v *= 2
      
  def renderBars(self, visibility, song, pos):
    if not song or self.tracksColor[0] == -1:
      return
    
    w            = self.boardWidth
    v            = 1.0 - visibility
    sw           = 0.02
    pos         -= self.lastBpmChange
    offset       = pos / self.currentPeriod * self.beatsPerUnit
    currentBeat  = pos / self.currentPeriod
    beat         = int(currentBeat)

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    glPushMatrix()
    while beat < currentBeat + self.beatsPerBoard:
      z = (beat - currentBeat) / self.beatsPerUnit

      if z > self.boardLength * .8:
        c = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        c = max(0, 1 + z)
      else:
        c = 1.0
        
      glRotate(v * 90, 0, 0, 1)

      if (beat % 1.0) < 0.001:
        glColor4f(self.barsColor[0], self.barsColor[1], self.barsColor[2], visibility * c * .75)
      else:
        glColor4f(self.barsColor[0], self.barsColor[1], self.barsColor[2], visibility * c * .5)

      glBegin(GL_TRIANGLE_STRIP)
      glVertex3f(-(w / 2), -v, z + sw)
      glVertex3f(-(w / 2), -v, z - sw)
      glVertex3f(w / 2,    -v, z + sw)
      glVertex3f(w / 2,    -v, z - sw)
      glEnd()
      
      if self.editorMode:
        beat += 1.0 / 4.0
      else:
        beat += 1
    glPopMatrix()

    Theme.setSelectedColor(visibility * .5)
    glBegin(GL_TRIANGLE_STRIP)
    glVertex3f(-w / 2, 0,  sw)
    glVertex3f(-w / 2, 0, -sw)
    glVertex3f(w / 2,  0,  sw)
    glVertex3f(w / 2,  0, -sw)
    glEnd()

  def render(self, visibility, song, pos):

    if not (self.coOpFailed and not self.coOpRestart):

      self.updateGuitarSettings()
      if self.ocount <= 1:
        self.ocount = self.ocount + .1
      else:
        self.ocount = 1

      if self.isFailing == True:
        if self.failcount <= 1 and self.failcount2 == False:
          self.failcount += .05
        elif self.failcount >= 1 and self.failcount2 == False:
          self.failcount = 1
          self.failcount2 = True
        
        if self.failcount >= 0 and self.failcount2 == True:
          self.failcount -= .05
        elif self.failcount <= 0 and self.failcount2 == True:
          self.failcount = 0
          self.failcount2 = False

      if self.isFailing == False and self.failcount > 0:
        self.failcount -= .05
        self.failcount2 = False

      if self.starPowerActive:

        if self.spcount < 1.2:
          self.spcount += .05
          self.spcount2 = 1
        elif self.spcount >=1.2:
          self.spcount = 1.2
          self.spcount2 = 0
      else:
        if self.spcount > 0:
          self.spcount -= .05
          self.spcount2 = 2
        elif self.spcount <=0:
          self.spcount = 0
          self.spcount2 = 0

      self.renderNeck(visibility, song, pos)
      self.renderIncomingNecks(visibility, song, pos) #MFH
      if self.theme == 0 or self.theme == 1 or self.theme == 2:
        self.drawTrack(self.ocount, song, pos)
        self.drawBPM(visibility, song, pos)
        self.drawSideBars(visibility, song, pos)
      else:
        self.renderTracks(visibility)
        self.renderBars(visibility, song, pos)

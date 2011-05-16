#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2009 Team FoFiX                                     #
#               2009 Blazingamer(n_hydock@comcast.net)              #
#                                                                   #
# This program is free software; you can redistribute it and/or     #
# modify it under the terms of the GNU General Public License       #
# as published by the Free Software Foundation; either version 2    #++-
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

from Song import Bars
import random
from Shader import shaders, mixColors

from OpenGL.GL import *
import numpy as np
import cmgl

#myfingershurt: needed for multi-OS file fetching
import os
import Log
import Song   #need the base song defines as well

class Neck:
  def __init__(self, engine, instrument, playerObj):

    self.engine         = engine
    self.player         = instrument.player
    self.instrument     = instrument

    self.isDrum       = self.instrument.isDrum
    self.isBassGuitar = self.instrument.isBassGuitar
    self.isVocal      = self.instrument.isVocal

    self.oNeckovr = None    #MFH - needs to be here to prevent crashes!    

    self.staticStrings  = self.engine.config.get("performance", "static_strings")

    self.indexFps       = self.engine.config.get("video", "fps") #QQstarS
    
    self.neckAlpha=[] # necks transparency
    self.neckAlpha.append( self.engine.config.get("game", "necks_alpha") ) # all necks
    self.neckAlpha.append( self.neckAlpha[0] * self.engine.config.get("game", "neck_alpha") ) # normal neck
    self.neckAlpha.append( self.neckAlpha[0] * self.engine.config.get("game", "solo_neck_alpha") ) # solo neck
    self.neckAlpha.append( self.neckAlpha[0] * self.engine.config.get("game", "bg_neck_alpha") ) # bass groove neck
    self.neckAlpha.append( self.neckAlpha[0] * self.engine.config.get("game", "overlay_neck_alpha") ) # overlay neck
    self.neckAlpha.append( self.neckAlpha[0] * self.engine.config.get("game", "fail_neck_alpha") ) # fail neck
    self.neckAlpha.append( self.neckAlpha[0] * self.engine.config.get("game", "4x_neck_alpha") ) # 4x multi neck
	
    self.boardWidth     = self.engine.theme.neckWidth
    self.boardLength    = self.engine.theme.neckLength
    self.shaderSolocolor    = self.engine.theme.shaderSolocolor
	
    self.boardFadeAmount = self.engine.theme.boardFade

    self.doNecksRender = self.engine.theme.doNecksRender

    #death_au: fixed neck size
    
    if self.isDrum and self.engine.config.get("game", "large_drum_neck"):
      self.boardWidth     = 4.0
      self.boardLength    = 12.0

    self.beatsPerBoard  = 5.0
    self.beatsPerUnit   = self.beatsPerBoard / self.boardLength

    color = (1,1,1)
    self.vis = 1


    size = 0

    # evilynux - Neck color
    self.board_col  = np.array([[color[0],color[1],color[2], 0],
                             [color[0],color[1],color[2], 0],
                             [color[0],color[1],color[2], self.vis],
                             [color[0],color[1],color[2], self.vis],
                             [color[0],color[1],color[2], self.vis],
                             [color[0],color[1],color[2], self.vis],
                             [color[0],color[1],color[2], 0],
                             [color[0],color[1],color[2], 0]], dtype=np.float32)

    w            = self.boardWidth
    l            = self.boardLength

    # evilynux - Neck vertices
    self.board_vtx = np.array([[-w / 2, 0, -2],
                            [w / 2, 0, -2],
                            [-w/ 2, 0, -1],
                            [w / 2, 0, -1],
                            [-w / 2, 0, l * .7],
                            [w / 2, 0, l * .7],
                            [-w / 2, 0, l],
                            [w / 2, 0, l]], dtype=np.float32)

    self.shader_neck_vtx = np.array([[-w / 2, 0.1, -2],
                                  [w / 2, 0.1, -2],
                                  [-w / 2, 0.1, l],
                                  [w / 2, 0.1, l]], dtype=np.float32)

    self.track_vtx = np.array([[-w / 2, 0, -2+size],
                            [w / 2, 0, -2+size],
                            [-w / 2, 0, -1+size],
                            [w / 2, 0, -1+size],
                            [-w / 2, 0, l * .7],
                            [w / 2, 0, l * .7],
                            [-w / 2, 0, l],
                            [w / 2, 0, l]], dtype=np.float32)

    # evilynux - Sidebars vertices
    w += 0.15
    self.sidebars_vtx = np.array([[-w / 2, 0, -2],
                               [w / 2, 0, -2],
                               [-w/ 2, 0, -1],
                               [w / 2, 0, -1],
                               [-w / 2, 0, l * .7],
                               [w / 2, 0, l * .7],
                               [-w / 2, 0, l],
                               [w / 2, 0, l]], dtype=np.float32)

    self.bpm_tex  = np.array([[0.0, 1.0],
                           [0.0, 0.0],
                           [1.0, 1.0],
                           [1.0, 0.0]], dtype=np.float32)

    self.bpm_col  = np.array([[1, 1, 1, self.vis],
                           [1, 1, 1, self.vis],
                           [1, 1, 1, self.vis],
                           [1, 1, 1, self.vis]], dtype=np.float32)

    self.soloLightVtx1 = np.array([[w / 2-1.0, 0.4, -2],
                                [w / 2+1.0, 0.4, -2],
                                [w / 2-1.0, 0.4, l],
                                [w / 2+1.0, 0.4, l]], dtype=np.float32)

    self.soloLightVtx2 = np.array([[-w / 2+1.0, 0.4, -2],
                                [-w / 2-1.0, 0.4, -2],
                                [-w / 2+1.0, 0.4, l],
                                [-w / 2-1.0, 0.4, l]], dtype=np.float32)

    # evilynux - Just in case the type has became double, convert to float32
    self.board_col = self.board_col.astype(np.float32)
    self.board_vtx = self.board_vtx.astype(np.float32)
    self.sidebars_vtx = self.sidebars_vtx.astype(np.float32)
    self.bpm_tex = self.bpm_tex.astype(np.float32)
    self.bpm_col = self.bpm_col.astype(np.float32)
    self.soloLightVtx1 = self.soloLightVtx1.astype(np.float32)
    self.soloLightVtx2 = self.soloLightVtx2.astype(np.float32)
    self.shader_neck_vtx = self.shader_neck_vtx.astype(np.float32)
    self.track_vtx = self.track_vtx.astype(np.float32)
	
    self.neckType = playerObj.neckType
    if self.neckType == 0:
      self.neck = engine.mainMenu.chosenNeck
    else:
      self.neck = str(playerObj.neck)
    playerObj  = None
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
    self.fourXcount = 0
    self.ovrneckoverlay = self.engine.config.get("fretboard", "ovrneckoverlay")
    self.ocount = 0

    self.currentPeriod  = 60000.0 / self.instrument.currentBpm
    self.lastBpmChange  = -1.0
    self.baseBeat       = 0.0

    #myfingershurt:
    self.bassGrooveNeckMode = self.engine.config.get("game", "bass_groove_neck")
    self.guitarSoloNeckMode = self.engine.config.get("game", "guitar_solo_neck")
    self.fourxNeckMode = self.engine.config.get("game", "4x_neck")


    self.useMidiSoloMarkers = False
    self.markSolos = 0
    
    neckFind = True
    themeNeckPath = os.path.join(self.engine.resource.fileName("themes", themename, "necks"))
    if self.neckType == 1 and os.path.exists(themeNeckPath):
      themeNeck = []
      neckfiles = [ f for f in os.listdir(themeNeckPath) if os.path.isfile(os.path.join(themeNeckPath, f)) ] 
      neckfiles.sort()
      for i in neckfiles:
        themeNeck.append(str(i))
      if len(themeNeck) > 0:
        i = random.randint(0,len(themeNeck)-1)
        if engine.loadImgDrawing(self, "neckDrawing", os.path.join("themes", themename, "necks", themeNeck[i]), textureSize = (256, 256)):
          neckFind = False
          Log.debug("Random theme neck chosen: " + themeNeck[i])
        else:
          Log.error("Unable to load theme neck: " + themeNeck[i])
          # fall back to defaultneck
          self.neck = "defaultneck"
    if neckFind:
      # evilynux - Fixed random neck -- MFH: further fixing random neck
      if self.neck == "0" or self.neck == "Neck_0" or self.neck == "randomneck":
        self.neck = []
        # evilynux - improved loading logic to support arbitrary filenames
        path = self.engine.resource.fileName("necks")
        neckfiles = [ f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) ] 
        neckfiles.sort()
        for i in neckfiles:
          # evilynux - Special cases, ignore these...
          if( os.path.splitext(i)[0] == "randomneck" or os.path.splitext(i)[0] == "overdriveneck" ):
            continue
          else:
            self.neck.append(str(i)[:-4]) # evilynux - filename w/o extension

        i = random.randint(0,len(self.neck)-1)
        if engine.loadImgDrawing(self, "neckDrawing", os.path.join("necks",self.neck[i]+".png"),  textureSize = (256, 256)):
          Log.debug("Random neck chosen: " + self.neck[i])
        else:
          Log.error("Unable to load neck: " + self.neck[i])
          self.neck = "defaultneck"
          engine.loadImgDrawing(self, "neckDrawing", os.path.join("necks",self.neck+".png"),  textureSize = (256, 256))
      else:
        # evilynux - first assume the self.neck contains the full filename
        if not engine.loadImgDrawing(self, "neckDrawing", os.path.join("necks",self.neck+".png"),  textureSize = (256, 256)):
          if not engine.loadImgDrawing(self, "neckDrawing", os.path.join("necks","Neck_"+self.neck+".png"),  textureSize = (256, 256)):
            engine.loadImgDrawing(self, "neckDrawing", os.path.join("necks","defaultneck.png"),  textureSize = (256, 256))
    
    #blazingamer:    
    #this helps me clean up the code a bit
    #what it does is if you're using drums or bass
    #it checks that directory first, if it doesn't
    #exist, then it goes back to the default directory

    if self.isDrum:
      self.extension = "drums"
    elif self.isBassGuitar:
      self.extension = "bass"
    else:
      self.extension = None

    themepath = os.path.join("themes", themename, "board")

    def loadImage(name, file):
      if self.extension:
        if not engine.loadImgDrawing(self, name, os.path.join(themepath, self.extension, file)):
          engine.loadImgDrawing(self, name, os.path.join(themepath, file))
      else:
        engine.loadImgDrawing(self, name, os.path.join(themepath, file))
 
    loadImage("sideBars", "side_bars.png")
    loadImage("oSideBars", "overdrive_side_bars.png")
    loadImage("failSideBars", "fail_side_bars.png")
    loadImage("oCenterLines", "overdrive_center_lines.png")
    loadImage("centerLines", "center_lines.png")
    loadImage("oNeck", "overdriveneck.png")
    loadImage("oFlash", "overdrive_string_flash.png")
    loadImage("bpm_halfbeat", "bpm_halfbeat.png")
    loadImage("bpm_beat",     "bpm_beat.png")
    loadImage("bpm_measure",  "bpm_measure.png")
    loadImage("failNeck", "failneck.png")

    if not self.failNeck:
      engine.loadImgDrawing(self, "failNeck", os.path.join("failneck.png"))

    if self.ovrneckoverlay:
      loadImage("oNeckovr", "overdriveneckovr.png")

    #myfingershurt: Bass Groove neck:
    self.bassGrooveNeck = None

    if self.isBassGuitar and self.bassGrooveNeckMode > 0:
      if self.bassGrooveNeckMode == 2:  #overlay neck
        engine.loadImgDrawing(self, "bassGrooveNeck", os.path.join(themepath, "bass", "bassgrooveneckovr.png"))
      if self.bassGrooveNeckMode == 1 or not self.bassGrooveNeck:  #replace neck
        engine.loadImgDrawing(self, "bassGrooveNeck", os.path.join(themepath, "bass", "bassgrooveneck.png"))

    #myfingershurt: Guitar Solo neck:
    self.soloNeck = None
    if not self.isVocal:
      if self.guitarSoloNeckMode > 0:
        if self.guitarSoloNeckMode == 1 or not engine.loadImgDrawing(self, "soloNeck", os.path.join(themepath, "soloneckovr.png")):  #replace neck
          loadImage("soloNeck", "soloneck.png")
        elif self.guitarSoloNeckMode == 2 or not engine.loadImgDrawing(self, "soloNeck", os.path.join(themepath, "soloneck.png")):  #overlay neck
          loadImage("soloNeck", "soloneckovr.png")

    self.fourMultiNeck = None
    if not self.isBassGuitar and self.fourxNeckMode > 0:
      if self.fourxNeckMode == 1:  #replace neck
        engine.loadImgDrawing(self, "fourMultiNeck", os.path.join(themepath, "fourmultineck.png"))
      if self.fourxNeckMode == 2:  #overlay neck
        engine.loadImgDrawing(self, "fourMultiNeck", os.path.join(themepath, "fourmultineckovr.png"))

    self.isFailing = False
    self.canGuitarSolo = self.instrument.canGuitarSolo
    self.guitarSolo = False
    self.scoreMultiplier = 1
    self.overdriveFlashCounts = self.indexFps/4   #how many cycles to display the oFlash: self.indexFps/2 = 1/2 second
    self.overdriveFlashCount = self.overdriveFlashCounts
    self.ocount = 0
    self.paused = False

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

    offset = 0

    z  = ((time - pos) / self.currentPeriod) / self.beatsPerUnit

    color = (1,1,1)

    glEnable(GL_TEXTURE_2D)

    board_vtx = np.array([[-w / 2, 0, z],
                            [w / 2, 0, z],
                            [-w/ 2, 0, z + 1],
                            [w / 2, 0, z + 1],
                            [-w / 2, 0, z + 2 + l * .7],
                            [w / 2, 0, z + 2 + l * .7],
                            [-w / 2, 0, z + 2 + l],
                            [w / 2, 0, z + 2 + l]], dtype=np.float32)

    board_tex  = np.array([[0.0, project(offset - 2 * self.beatsPerUnit)],
                         [1.0, project(offset - 2 * self.beatsPerUnit)],
                         [0.0, project(offset - 1 * self.beatsPerUnit)],
                         [1.0, project(offset - 1 * self.beatsPerUnit)],
                         [0.0, project(offset + l * self.beatsPerUnit * .7)],
                         [1.0, project(offset + l * self.beatsPerUnit * .7)],
                         [0.0, project(offset + l * self.beatsPerUnit)],
                         [1.0, project(offset + l * self.beatsPerUnit)]], dtype=np.float32)

    if neckTexture:
      neckTexture.texture.bind()

    cmgl.drawArrays(GL_TRIANGLE_STRIP, vertices=board_vtx, colors=self.board_col, texcoords=board_tex)

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
      if self.useMidiSoloMarkers:
        for time, event in track.getEvents(boardWindowMin, boardWindowMax):
          if isinstance(event, Song.MarkerNote) and event.number == Song.starPowerMarkingNote and self.soloNeck: 
            if event.endMarker:   #solo end
              if self.incomingNeckMode == 2 and self.guitarSolo:    #render both start and end incoming necks and only until the end of the guitar solo
                if self.instrument.starPowerActive and self.oNeck and self.ovrneckoverlay == False:
                  neckImg = self.oNeck
                  alpha   = self.neckAlpha[4]
                elif self.scoreMultiplier > 4 and self.bassGrooveNeck != None and self.bassGrooveNeckMode == 1:
                  neckImg = self.bassGrooveNeck
                  alpha   = self.neckAlpha[3]
                elif self.fourMultiNeck and self.scoreMultiplier == 4 and self.fourxNeckMode == 1:
                  neckImg = self.fourMultiNeck
                  alpha   = self.neckAlpha[6]
                else:
                  neckImg = self.neckDrawing
                  alpha   = self.neckAlpha[1]
                self.renderIncomingNeck(visibility*alpha, song, pos, time, neckImg)

            else:    #solo start
              if not self.guitarSolo:   #only until guitar solo starts!
                neckImg = self.soloNeck
                alpha   = self.neckAlpha[2]
                self.renderIncomingNeck(visibility*alpha, song, pos, time, neckImg)
                if self.spcount2 != 0 and self.spcount < 1.2 and self.oNeck:
                  alpha = self.neckAlpha[4]
                  if self.oNeckovr != None and (self.scoreMultiplier > 4 or self.guitarSolo or self.ovrneckoverlay == True):
                    neck = self.oNeckovr
                  else:
                    neck = self.oNeck
                  self.renderIncomingNeck(visibility*alpha, song, pos, time, neckImg)

      elif self.markSolos == 1:   #fall back on text-based guitar solo marking track
        for time, event in song.eventTracks[Song.TK_GUITAR_SOLOS].getEvents(boardWindowMin, boardWindowMax):
          if self.canGuitarSolo and self.soloNeck:
            if event.text.find("ON") >= 0:
              if not self.guitarSolo:   #only until guitar solo starts!
                neckImg = self.soloNeck
                self.renderIncomingNeck(visibility, song, pos, time, neckImg)
            elif self.incomingNeckMode == 2:    #render both start and end incoming necks
              if self.guitarSolo:   #only until the end of the guitar solo!
                if self.instrument.starPowerActive and self.oNeck:
                  neckImg = self.oNeck
                elif self.scoreMultiplier > 4 and self.bassGrooveNeck != None and self.bassGrooveNeckMode == 1:
                  neckImg = self.bassGrooveNeck
                elif self.fourMultiNeck and self.scoreMultiplier == 4 and self.fourxNeckMode == 1:
                  neckImg = self.fourMultiNeck
                else:
                  neckImg = self.neckDrawing
                self.renderIncomingNeck(visibility, song, pos, time, neckImg)


  def renderNeckMethod(self, visibility, offset, neck, alpha = False): #blazingamer: New neck rendering method
    
    def project(beat):
      return 0.125 * beat / self.beatsPerUnit    # glorandwarf: was 0.12
    if self.instrument.starPowerActive and (self.theme == 0 or self.theme == 1):#8bit
      color = self.engine.theme.spNoteColor #self.spColor #(.3,.7,.9)
    else:
      color = (1,1,1)

    v            = visibility
    l            = self.boardLength

    glEnable(GL_TEXTURE_2D)

    board_tex  = np.array([[0.0, project(offset - 2 * self.beatsPerUnit)],
                         [1.0, project(offset - 2 * self.beatsPerUnit)],
                         [0.0, project(offset - 1 * self.beatsPerUnit)],
                         [1.0, project(offset - 1 * self.beatsPerUnit)],
                         [0.0, project(offset + l * self.beatsPerUnit * .7)],
                         [1.0, project(offset + l * self.beatsPerUnit * .7)],
                         [0.0, project(offset + l * self.beatsPerUnit)],
                         [1.0, project(offset + l * self.beatsPerUnit)]], dtype=np.float32)
    
    #must be separate for neck flashing.
    board_col  = np.array([[color[0],color[1],color[2], 0],
                             [color[0],color[1],color[2], 0],
                             [color[0],color[1],color[2], v],
                             [color[0],color[1],color[2], v],
                             [color[0],color[1],color[2], v],
                             [color[0],color[1],color[2], v],
                             [color[0],color[1],color[2], 0],
                             [color[0],color[1],color[2], 0]], dtype=np.float32)

    if alpha == True:
      glBlendFunc(GL_ONE, GL_ONE)
    if neck:
      neck.texture.bind()
    cmgl.drawArrays(GL_TRIANGLE_STRIP, vertices=self.board_vtx, colors=board_col, texcoords=board_tex)

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

    if self.guitarSolo and self.soloNeck and self.guitarSoloNeckMode == 1:
      neck = self.soloNeck
    elif self.scoreMultiplier > 4 and self.bassGrooveNeck and self.bassGrooveNeckMode == 1:
      neck = self.bassGrooveNeck
    elif self.fourxNeckMode == 1 and self.fourMultiNeck and self.scoreMultiplier == 4:
      neck = self.fourMultiNeck
    elif self.instrument.starPowerActive and not (self.spcount2 != 0 and self.spcount < 1.2) and self.oNeck and self.scoreMultiplier <= 4 and not self.ovrneckoverlay:
      neck = self.oNeck
    else:
      neck = self.neckDrawing

    
    self.renderNeckMethod(v*self.neckAlpha[1], offset, neck)
    
    if self.guitarSolo and self.soloNeck and self.guitarSoloNeckMode == 2:   #static overlay
      self.renderNeckMethod(v*self.neckAlpha[2], 0, self.soloNeck)
 
    if self.bgcount > 0 and self.bassGrooveNeck and self.bassGrooveNeckMode == 2:   #static bass groove overlay
      self.renderNeckMethod(v*self.bgcount*self.neckAlpha[3], 0, self.bassGrooveNeck)

    if self.fourXcount > 0 and self.fourMultiNeck and self.fourxNeckMode == 2:   #4x multi overlay neck
      self.renderNeckMethod(v*self.fourXcount*self.neckAlpha[6], offset, self.fourMultiNeck)

    if self.spcount2 != 0 and self.spcount < 1.2 and self.oNeck:   #static overlay
      if self.oNeckovr and (self.scoreMultiplier > 4 or self.guitarSolo or self.ovrneckoverlay):
        neck = self.oNeckovr
        alpha = False
      else:
        neck = self.oNeck
        alpha = True          

      self.renderNeckMethod(v*self.spcount*self.neckAlpha[4], offset, neck, alpha)
      
    if self.instrument.starPowerActive and not (self.spcount2 != 0 and self.spcount < 1.2) and self.oNeck and (self.scoreMultiplier > 4 or self.guitarSolo or self.ovrneckoverlay):   #static overlay
      if self.oNeckovr:
        neck = self.oNeckovr
        alpha = False
      else:
        neck = self.oNeck
        alpha = True

      self.renderNeckMethod(v*self.neckAlpha[4], offset, neck, alpha)

    if shaders.enabled:
      shaders.globals["basspos"] = shaders.var["fret"][self.player][0]
      shaders.globals["notepos"] = shaders.var["fret"][self.player][1:]
      shaders.globals["bpm"] = self.instrument.currentBpm
      shaders.globals["songpos"] = pos
      shaders.globals["spEnabled"] = self.instrument.starPowerActive
      shaders.globals["isFailing"] = self.isFailing
      shaders.globals["isMultChanged"] = (shaders.var["scoreMult"][self.player] != self.scoreMultiplier)
      if shaders.globals["isMultChanged"]:
        shaders.var["multChangePos"][self.player] = pos
      shaders.globals["scoreMult"] = self.scoreMultiplier
      shaders.var["scoreMult"][self.player] = self.scoreMultiplier
      shaders.globals["isDrum"] = self.isDrum
      shaders.globals["soloActive"] = self.guitarSolo
      
      posx = shaders.time()
      fret = []
      neckcol = (0,0,0)
      
      notecolors = list(self.engine.theme.noteColors)
      if self.isDrum:
        notecolors[4] = notecolors[0]
        notecolors[0] = self.engine.theme.noteColors[5]
        
        
      for i in range(5):
        blend = max(shaders.var["fret"][self.player][i] - posx + 1.5,0.01)
        neckcol = mixColors(neckcol, notecolors[i], blend)

      shaders.var["color"][self.player]=neckcol

    if shaders.enable("neck"):
      shaders.setVar("fretcol",neckcol)
      shaders.update()
      cmgl.drawArrays(GL_TRIANGLE_STRIP, vertices=self.shader_neck_vtx)
      shaders.disable()
    else:
      if self.isFailing:
        self.renderNeckMethod(self.failcount, 0, self.failNeck)
        
    if (self.guitarSolo or self.instrument.starPowerActive) and self.theme == 1:
      shaders.var["solocolor"]=self.shaderSolocolor
    else:
      shaders.var["solocolor"]=(0.0,)*4


  def drawTrack(self, visibility, song, pos):
    if not song:
      return
    if not song.readyToGo:
      return

    def project(beat):
      return 0.125 * beat / self.beatsPerUnit    # glorandwarf: was 0.12

    v            = visibility
    w            = self.boardWidth
    l            = self.boardLength

    if self.staticStrings:
      offset       = 0
    else:
      offset       = (pos - self.lastBpmChange) / self.currentPeriod + self.baseBeat 

    track_tex  = np.array([[0.0, project(offset - 2 * self.beatsPerUnit)],
                         [1.0, project(offset - 2 * self.beatsPerUnit)],
                         [0.0, project(offset - 1 * self.beatsPerUnit)],
                         [1.0, project(offset - 1 * self.beatsPerUnit)],
                         [0.0, project(offset + l * self.beatsPerUnit * .7)],
                         [1.0, project(offset + l * self.beatsPerUnit * .7)],
                         [0.0, project(offset + l * self.beatsPerUnit)],
                         [1.0, project(offset + l * self.beatsPerUnit)]], dtype=np.float32)

    glEnable(GL_TEXTURE_2D)
    
    #MFH - logic to briefly display oFlash
    if self.overdriveFlashCount < self.overdriveFlashCounts and self.oFlash:
      self.oFlash.texture.bind()
    elif self.instrument.starPowerActive and self.oCenterLines:
      self.oCenterLines.texture.bind()
    else:
      if self.centerLines:
        self.centerLines.texture.bind()
    
    if self.staticStrings:    #MFH
      cmgl.drawArrays(GL_TRIANGLE_STRIP, vertices=self.track_vtx, colors=self.board_col, texcoords=track_tex)
    else:   #MFH: original moving strings
      cmgl.drawArrays(GL_TRIANGLE_STRIP, vertices=self.track_vtx, colors=self.board_col, texcoords=track_tex)

    glDisable(GL_TEXTURE_2D)

  def drawSideBars(self, visibility, song, pos):
    if not song:
      return
    if not song.readyToGo:
      return

    def project(beat):
      return 0.125 * beat / self.beatsPerUnit  # glorandwarf: was 0.12

    color = (1,1,1)

    v            = visibility
    w            = self.boardWidth + 0.15
    l            = self.boardLength

    offset       = (pos - self.lastBpmChange) / self.currentPeriod + self.baseBeat 

    c = (1,1,1)

    board_tex  = np.array([[0.0, project(offset - 2 * self.beatsPerUnit)],
                         [1.0, project(offset - 2 * self.beatsPerUnit)],
                         [0.0, project(offset - 1 * self.beatsPerUnit)],
                         [1.0, project(offset - 1 * self.beatsPerUnit)],
                         [0.0, project(offset + l * self.beatsPerUnit * .7)],
                         [1.0, project(offset + l * self.beatsPerUnit * .7)],
                         [0.0, project(offset + l * self.beatsPerUnit)],
                         [1.0, project(offset + l * self.beatsPerUnit)]], dtype=np.float32)

    #must be separate for sidebar flashing.
    board_col  = np.array([[color[0],color[1],color[2], 0],
                             [color[0],color[1],color[2], 0],
                             [color[0],color[1],color[2], v],
                             [color[0],color[1],color[2], v],
                             [color[0],color[1],color[2], v],
                             [color[0],color[1],color[2], v],
                             [color[0],color[1],color[2], 0],
                             [color[0],color[1],color[2], 0]], dtype=np.float32)

    glEnable(GL_TEXTURE_2D)
    if self.instrument.starPowerActive and self.oSideBars:
      self.oSideBars.texture.bind()
    else:
      self.sideBars.texture.bind()
    if self.isFailing and self.failSideBars and v == self.failcount:
      self.failSideBars.texture.bind()
    else:
      self.sideBars.texture.bind()
    cmgl.drawArrays(GL_TRIANGLE_STRIP, vertices=self.sidebars_vtx, colors=board_col, texcoords=board_tex)
    glDisable(GL_TEXTURE_2D)
     
    if shaders.enable("sololight"):
      shaders.modVar("color",shaders.var["solocolor"])
      shaders.setVar("offset",(-3.5,-w/2))
      cmgl.drawArrays(GL_TRIANGLE_STRIP, vertices=self.soloLightVtx1)
      shaders.setVar("offset",(-3.5,w/2))
      shaders.setVar("time",shaders.time()+0.5)
      cmgl.drawArrays(GL_TRIANGLE_STRIP, vertices=self.soloLightVtx2) 
      shaders.disable()

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
      sw = 0.1 #width

      if z > self.boardLength:
        f = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        f = min(1, max(0, 1 + z2))
      else:
        f = 1.0


      bpm_vtx  = np.array([[-(w / 2), 0,  z + sw],
                         [-(w / 2), 0,  z - sw],
                         [(w / 2), 0,  z + sw],
                         [(w / 2), 0,  z - sw]], dtype=np.float32)


      if event.barType == 0: #half-beat
        self.bpm_halfbeat.texture.bind()
      elif event.barType == 1: #beat
        self.bpm_beat.texture.bind()
      elif event.barType == 2: #measure
        self.bpm_measure.texture.bind()

      cmgl.drawArrays(GL_TRIANGLE_STRIP, vertices=bpm_vtx, colors=self.bpm_col, texcoords=self.bpm_tex)

      glPopMatrix()

    glDisable(GL_TEXTURE_2D)
    
  def render(self, visibility, song, pos):
    self.currentPeriod = self.instrument.neckSpeed

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
    if self.instrument.starPowerActive == True:
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

    if self.scoreMultiplier > 4 and self.bgcount < 1:
      self.bgcount += .1
      if self.bgcount > 1:
        self.bgcount = 1
    if self.scoreMultiplier < 4 and self.bgcount > 0:
      self.bgcount -= .1
      if self.bgcount < 0:
        self.bgcount = 0

    if self.scoreMultiplier == 4 and self.fourXcount < 1:
      self.fourXcount += .1
      if self.fourXcount > 1:
        self.fourXcount = 1
    if not self.scoreMultiplier == 4 and self.fourXcount > 0:
      self.fourXcount -= .1
      if self.fourXcount < 0:
        self.fourXcount = 0

    if not (self.bpm_halfbeat and self.bpm_beat and self.bpm_measure):
      self.bpmLinesDisabled = True
    else:
	  self.bpmLinesDisabled = False

    if not (self.instrument.coOpFailed and not self.instrument.coOpRestart):

      if self.ocount < 1:
        self.ocount += .1
      else:
        self.ocount = 1

      self.vis = visibility
      if self.doNecksRender == True:
        self.renderNeck(visibility, song, pos)
      if self.soloNeck:
        self.renderIncomingNecks(visibility, song, pos) #MFH
      if self.centerLines or self.oCenterLines or self.oFlash:
        self.drawTrack(self.ocount, song, pos)
      if not self.bpmLinesDisabled:
        self.drawBPM(visibility, song, pos)
      if self.sideBars:
        if self.isFailing and self.failSideBars:
          self.drawSideBars(visibility, song, pos)
          self.drawSideBars(self.failcount, song, pos)
        else:
          self.drawSideBars(visibility, song, pos)

    if self.overdriveFlashCount < self.overdriveFlashCounts and self.oFlash:
      self.overdriveFlashCount = self.overdriveFlashCount + 1

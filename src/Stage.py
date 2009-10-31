#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
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

import Config
from OpenGL.GL import *
import math
import Log
from Shader import shaders
import Theme
import os
import random   #MFH - needed for new stage background handling
from Language import _

import Version # Provides dataPath
try:
  from VideoPlayer import VideoPlayer
  videoAvailable = True
except:
  videoAvailable = False
  
import Rockmeter #blazingamer - new 4.0 code for rendering rockmeters through stage.ini

class Stage(object):
  def __init__(self, guitarScene, configFileName):
    self.scene            = guitarScene
    self.engine           = guitarScene.engine
    self.config           = Config.MyConfigParser()
    self.layers = []
    self.reset()
    

    self.wFull = None   #MFH - needed for new stage background handling
    self.hFull = None
    
    # evilynux - imported myfingershurt stuff from GuitarScene
    self.mode = self.engine.config.get("game", "stage_mode")
    self.songStage = self.engine.config.get("game", "song_stage")
    self.animatedFolder = self.engine.config.get("game", "animated_stage_folder")

    # evilynux - imported myfingershurt stuff from GuitarScene w/ minor modifs
    #MFH TODO - alter logic to accomodate separated animation and slideshow
    #           settings based on seleted animated stage folder
    animationMode = self.engine.config.get("game", "stage_animate")
    slideShowMode = self.engine.config.get("game", "rotate_stages")

    if self.animatedFolder == _("None"):
      self.rotationMode = 0   #MFH: if no animated stage folders are available, disable rotation.
    elif self.animatedFolder == "Normal":
      self.rotationMode = slideShowMode
    else:
      self.rotationMode = animationMode
    
    self.imgArr = [] #QQstarS:random
    self.imgArrScaleFactors = []  #MFH - for precalculated scale factors
    self.rotateDelay = self.engine.config.get("game",  "stage_rotate_delay") #myfingershurt - user defined stage rotate delay
    self.animateDelay = self.engine.config.get("game",  "stage_animate_delay") #myfingershurt - user defined stage rotate delay
    self.animation = False

    self.indexCount = 0 #QQstarS:random time counter
    self.arrNum = 0 #QQstarS:random the array num
    self.arrDir = 1 #forwards

    self.config.read(configFileName)

    # evilynux - Improved stage error handling
    self.themename = self.engine.data.themeLabel
    self.path = os.path.join("themes",self.themename,"stages")
    self.pathfull = self.engine.getPath(self.path)
    if not os.path.exists(self.pathfull): # evilynux
      Log.warn("Stage folder does not exist: %s" % self.pathfull)
      self.mode = 1 # Fallback to song-specific stage
    suffix = ".jpg"

  def loadVideo(self, libraryName, songName):
    if not videoAvailable:
      raise NameError('Video (gstreamer) is not available!')
    if self.songStage == 1 and os.path.exists(os.path.join(libraryName, songName, "default.avi")):
      self.vidSource = os.path.join(libraryName, songName, "default.avi")
    else:
      self.vidSource = os.path.join(self.pathfull, "default.avi")
      if not os.path.exists(self.vidSource):
        Log.warn("No video found, fallbacking to default static image mode for now")
        self.mode = 1 # Fallback
        return
      
    try: # Catches invalid video files or unsupported formats
      self.vidPlayer = VideoPlayer(-1, self.vidSource, mute = True, loop = True)
      self.engine.view.pushLayer(self.vidPlayer)
      self.vidPlayer.paused = True
    except:
      self.mode = 1

  def restartVideo(self):
    if not videoAvailable or not self.mode == 3:
      return
    self.vidPlayer.loadVideo(self.vidSource)
    
  def load(self, libraryName, songName, practiceMode = False):
    rockmeter = self.engine.resource.fileName(os.path.join("themes", self.themename,"rockmeter.ini"))
    self.rockmeter        = Rockmeter.Rockmeter(self.scene, rockmeter)

    # evilynux - Fixes a self.background not defined crash
    self.background = None
    #MFH - new background stage logic:
    if self.mode == 2:   #blank / no stage
      self.songStage = 0
      self.rotationMode = 0
    elif practiceMode:   #check for existing practice stage; always disable stage rotation here
      self.songStage = 0
      self.rotationMode = 0
      self.mode = 1
      #separated practice stages for the instruments by k.i.d
      if self.scene.guitars[0].isDrum:
        background = "practicedrum"
      elif self.scene.guitars[0].isBassGuitar:
        background = "practicebass"
      else:
        background = "practice"
      if not self.engine.loadImgDrawing(self, "background", os.path.join("themes",self.themename,"stages",background)):
        #MFH - must first fall back on the old practice.png before forcing blank stage mode!
        if not self.engine.loadImgDrawing(self, "background", os.path.join("themes",self.themename,"stages","practice")):
          Log.warn("No practice stage, fallbacking on a forced Blank stage mode") # evilynux
          self.mode = 2    #if no practice stage, just fall back on a forced Blank stage mode
            
    elif self.songStage == 1:    #check for song-specific background
      test = True
      if not self.engine.loadImgDrawing(self, "background", os.path.join(libraryName, songName, "background")):
        Log.notice("No song-specific stage found") # evilynux
        test = False
      if test:  #does a song-specific background exist?
        self.rotationMode = 0
        self.mode = 1
      else:
        self.songStage = 0

    #MFH - now, after the above logic, we can run the normal stage mode logic
    #      only worrying about checking for Blank, song-specific and
    #      practice stage modes
    if self.mode != 2 and self.mode != 3 and self.songStage == 0 and not practiceMode: #still need to load stage(s)
      #myfingershurt: assign this first
      if self.mode == 1:   #just use Default.png
        if not self.engine.loadImgDrawing(self, "background", os.path.join(self.path, "default")):
          Log.warn("No default stage; falling back on a forced Blank stage mode") # evilynux
          self.mode = 2    #if no practice stage, just fall back on a forced Blank stage mode

      ##This checks how many Stage-background we have to select from
      if self.mode == 0 and self.rotationMode == 0:  #MFH: just display a random stage
        files = []
        fileIndex = 0
        allfiles = os.listdir(self.pathfull)
        for name in allfiles:
          if os.path.splitext(name)[0].lower() != "practice" and os.path.splitext(name)[0].lower() != "practicedrum" and os.path.splitext(name)[0].lower() != "practicebass" and name != ".svn":
            Log.debug("Valid background found, index (" + str(fileIndex) + "): " + name)
            files.append(name)
            fileIndex += 1
          else:
            Log.debug("Practice background filtered: " + name)
  
        # evilynux - improved error handling, fallback to blank background if no background are found
        if fileIndex == 0:
          Log.warn("No valid stage found!")
          self.mode = 2;
        else:
          i = random.randint(0,len(files)-1)
          filename = files[i]
      ##End check number of Stage-backgrounds
          if not self.engine.loadImgDrawing(self, "background", os.path.join(self.path, filename)):
            self.mode = 2;

      elif self.rotationMode > 0 and self.mode != 2:
        files = []
        fileIndex = 0
        
        if self.animatedFolder == "Random": #Select one of the subfolders under stages\ to animate randomly
          numAniStageFolders = len(self.engine.stageFolders)
          if numAniStageFolders > 0:
            self.animatedFolder = random.choice(self.engine.stageFolders)
          else:
            self.animatedFolder = "Normal"
          
        elif self.animatedFolder == "None":
          self.mode = 2
        
        if self.animatedFolder != "Normal" and self.mode != 2: #just use the base Stages folder for rotation
          self.path = os.path.join("themes",self.themename,"stages",self.animatedFolder)
          self.pathfull = self.engine.getPath(self.path)
          self.animation = True

        allfiles = os.listdir(self.pathfull)
        for name in allfiles:

          if os.path.splitext(name)[1].lower() == ".png" or os.path.splitext(name)[1].lower() == ".jpg" or os.path.splitext(name)[1].lower() == ".jpeg":
            if os.path.splitext(name)[0].lower() != "practice" and os.path.splitext(name)[0].lower() != "practicedrum" and os.path.splitext(name)[0].lower() != "practicebass":
              Log.debug("Valid background found, index (" + str(fileIndex) + "): " + name)
              files.append(name)
              fileIndex += 1
            else:
              Log.debug("Practice background filtered: " + name)
          files.sort()

      if self.rotationMode > 0 and self.mode != 2:   #alarian: blank stage option is not selected
      #myfingershurt: just populate the image array in order, they are pulled in whatever order requested:
        for j in range(len(files)):
          self.engine.loadImgDrawing(self, "backgroundA", os.path.join(self.path, files[j]))
          #MFH: also precalculate each image's scale factor and store in the array
          imgwidth = self.backgroundA.width1()
          wfactor = 640.000/imgwidth
          self.imgArr.append(getattr(self, "backgroundA", os.path.join(self.path, files[j])))
          self.imgArrScaleFactors.append(wfactor)
    
    if self.rotationMode > 0 and len(self.imgArr) == 0:
      self.rotationMode = 0

    if self.mode != 2 and self.background:   #MFH - precalculating scale factor
      imgwidth = self.background.width1()
      self.backgroundScaleFactor = 640.000/imgwidth

  #stage rotation
  def rotate(self):
    if self.animation:
      whichDelay = self.animateDelay
    else:
      whichDelay = self.rotateDelay
    self.indexCount = self.indexCount + 1
    if self.indexCount > whichDelay:   #myfingershurt - adding user setting for stage rotate delay
      self.indexCount = 0
      if self.rotationMode == 1: #QQstarS:random
        self.arrNum = random.randint(0,len(self.imgArr)-1)
      elif self.rotationMode == 2: #myfingershurt: in order display mode
        self.arrNum += 1
        if self.arrNum > (len(self.imgArr)-1):
          self.arrNum = 0
      elif self.rotationMode == 3: #myfingershurt: in order, back and forth display mode
        if self.arrDir == 1:  #forwards
          self.arrNum += 1
          if self.arrNum > (len(self.imgArr)-1):
            self.arrNum -= 2
            self.arrDir = 0
        else:
          self.arrNum -= 1
          if self.arrNum < 0:
            self.arrNum += 2
            self.arrDir = 1

  def renderBackground(self):
    #myfingershurt: multiple rotation modes
    if self.mode != 2:
      if self.rotationMode == 0:
        self.engine.drawImage(self.background, scale = (self.backgroundScaleFactor,-self.backgroundScaleFactor),
                              coord = (self.wFull/2,self.hFull/2))

      #myfingershurt:
      else:
        #MFH - use precalculated scale factors instead
        self.engine.drawImage(self.imgArr[self.arrNum], scale = (self.imgArrScaleFactors[self.arrNum],-self.imgArrScaleFactors[self.arrNum]),
                              coord = (self.wFull/2,self.hFull/2))

  def updateDelays(self):
    self.rotateDelay = self.engine.config.get("game",  "stage_rotate_delay") #myfingershurt - user defined stage rotate delay
    self.animateDelay = self.engine.config.get("game",  "stage_animate_delay") #myfingershurt - user defined stage rotate delay

  def reset(self):
    self.lastBeatPos        = None
    self.lastQuarterBeatPos = None
    self.lastMissPos        = None
    self.lastPickPos        = None
    self.beat               = 0
    self.quarterBeat        = 0
    self.pos                = 0.0
    self.playedNotes        = []
    self.averageNotes       = [0.0]
    self.beatPeriod         = 0.0

  def triggerPick(self, pos, notes):
    if notes:
      self.lastPickPos      = pos
      self.playedNotes      = self.playedNotes[-3:] + [sum(notes) / float(len(notes))]
      self.averageNotes[-1] = sum(self.playedNotes) / float(len(self.playedNotes))

  def triggerMiss(self, pos):
    self.lastMissPos = pos

  def triggerQuarterBeat(self, pos, quarterBeat):
    self.lastQuarterBeatPos = pos
    self.quarterBeat        = quarterBeat

  def triggerBeat(self, pos, beat):
    self.lastBeatPos  = pos
    self.beat         = beat
    self.averageNotes = self.averageNotes[-4:] + self.averageNotes[-1:]

  def renderLayers(self, layers, visibility):
    self.engine.view.setOrthogonalProjection(normalize = True)
    try:
      for layer in layers:
        layer.render(visibility)
    finally:
      self.engine.view.resetProjection()

  def run(self, pos, period):
    self.pos        = pos
    self.beatPeriod = period
    quarterBeat = int(4 * pos / period)

    if quarterBeat > self.quarterBeat:
      self.triggerQuarterBeat(pos, quarterBeat)

    beat = quarterBeat / 4

    if beat > self.beat:
      self.triggerBeat(pos, beat)

  def render(self, visibility):
    if self.mode != 3:
      self.renderBackground()
    self.renderLayers(self.layers, visibility)
    if shaders.enable("stage"):
      height = 0.0
      for i in shaders.var["color"].keys():
        shaders.modVar("color",shaders.var["color"][i],0.05,10.0)
        height += shaders.var["color"][i][3]/3.0
      height=height**2
      shaders.setVar("height",2*height)
      shaders.setVar("ambientGlow",height/1.5)

      shaders.setVar("glowStrength",60+height*80.0)
      glBegin(GL_TRIANGLE_STRIP)
      glVertex3f(-8.0, 1.0,7.0)
      glVertex3f(8.0, 1.0,7.0)
      glVertex3f(-8.0, 4.0,7.0)
      glVertex3f(8.0, 4.0,7.0)
      glEnd()    
      shaders.disable()
      
    self.scene.renderGuitar()
    self.rockmeter.render(visibility)
    
    

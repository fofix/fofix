#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
#               2008 Glorandwarf                                    #
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

from Font import Font
from Texture import Texture
from Svg import ImgDrawing, SvgContext
from Texture import Texture
from Audio import Sound
from Language import _
import random
import Language
import Config
#myfingershurt: needed for multi-OS file fetching
import os
import sys

import Log

# these constants define a few customized letters in the default font
STAR1 = unicode('\x10')
STAR2 = unicode('\x11')
LEFT  = unicode('\x12')
RIGHT = unicode('\x13')
STAR3 = unicode('\x14')  #Worldrave - Added new Star3
STAR4 = unicode('\x15')  #Worldrave - Added new Star4

class Data(object):
  """A collection of globally used data resources such as fonts and sound effects."""
  def __init__(self, resource, svg):

    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("Data class init (Data.py)...")
    
    self.resource = resource
    self.svg      = svg

    self.sfxVolume    = Config.get("audio", "SFX_volume")
    self.crowdVolume  = Config.get("audio", "crowd_volume")

    #Get theme
    themename = Config.get("coffee", "themename")
    self.themeLabel = themename
    self.themeCoOp  = False


    #myfingershurt: check for existance of theme path
    #evilynux/MFH - fixed themes when running from src folder
    themepath = os.path.join("data","themes")
    if not hasattr(sys,"frozen"):
      themepath = os.path.join("..",themepath)

    if not os.path.exists(os.path.join(themepath,themename,"notes.png")):
      #myfingershurt: here need to ensure an existing theme is selected
      #if not hasattr(sys,"frozen"):
      #  themepath = os.path.join("..",themepath)
      themes = []
      defaultTheme = None           #myfingershurt
      allthemes = os.listdir(themepath)
      for name in allthemes:
        if os.path.exists(os.path.join(themepath,name,"notes.png")):
          themes.append(name)
          if name == "MegaLight":         #myfingershurt
            defaultTheme = name     #myfingershurt
      i = len(themes)
      if defaultTheme != "MegaLight":     #myfingershurt
        defaultTheme = themes[0]    #myfingershurt
      #not a valid theme if notes.png isn't there!  Force default theme:
      Config.set("coffee", "themename",defaultTheme)
      #re-init Data with new default
      themename = defaultTheme
      self.themeLabel = themename



    if self.fileExists(os.path.join("themes",themename,"spfill.png")):
      self.theme = 0
    elif self.fileExists(os.path.join("themes",themename,"overdrive fill.png")):
      self.theme = 2
      self.themeCoOp = True
    else:
      self.theme = 1
      if self.fileExists(os.path.join("themes",themename,"coop_rockmeter.png")):
        self.themeCoOp = True

    #myfingershurt: multi-OS compatibility file access fixes using os.path.join()
    # load font customization images

    #Worldrave - Use new defined Star3 and star4. Using star1 and star2 as a fallback.

    self.loadImgDrawing(self, "star1",   os.path.join("themes",themename,"star1.png"), textureSize = (128, 128))
    self.loadImgDrawing(self, "star2",   os.path.join("themes",themename,"star2.png"), textureSize = (128, 128))
    try:
      self.loadImgDrawing(self, "star3",   os.path.join("themes",themename,"star3.png"), textureSize = (128, 128))
      self.loadImgDrawing(self, "star4",   os.path.join("themes",themename,"star4.png"), textureSize = (128, 128))
    except IOError:
      self.loadImgDrawing(self, "star3",   os.path.join("themes",themename,"star1.png"), textureSize = (128, 128))
      self.loadImgDrawing(self, "star4",   os.path.join("themes",themename,"star2.png"), textureSize = (128, 128))

 
    self.loadImgDrawing(self, "left",    "left.png",  textureSize = (128, 128))
    self.loadImgDrawing(self, "right",   "right.png", textureSize = (128, 128))

    # load misc images
    self.loadImgDrawing(self, "loadingImage", os.path.join("themes",themename,"loadingbg.png"), textureSize = (256,256))
    try:
      self.loadImgDrawing(self, "submenuSelect", os.path.join("themes",themename,"submenuselect.png"))
      subSelectImgW = self.submenuSelect.width1()
      self.submenuSelectFound = True
      self.subSelectWFactor = 640.000/subSelectImgW
      self.subSelectImgH = self.submenuSelect.height1()
    except IOError:
      self.submenuSelectFound = False
      self.loadImgDrawing(self, "submenuSelect", os.path.join("themes",themename,"menu","selected.png"))
      self.subSelectWFactor = 0

    # load all the data in parallel
    asciiOnly = not bool(Language.language) or Language.language == "Custom"
    reversed  = _("__lefttoright__") == "__righttoleft__" and True or False
    scale     = 1
    scale2    = .5
    # evilynux - Load bigger fonts so they're nicer when scaled, scaling readjusted
    fontSize  = [44, 108, 34, 32, 30]

    if asciiOnly:
      font    = resource.fileName("default.ttf")
      bigFont = resource.fileName("title.ttf")
    else:
      Log.debug("Main font International.ttf used!")
      font    = \
      bigFont = resource.fileName("international.ttf")

    # load fonts
    font1     = lambda: Font(font,    fontSize[0], scale = scale*.5, reversed = reversed, systemFont = not asciiOnly)
    font2     = lambda: Font(bigFont, fontSize[1], scale = 1, reversed = reversed, systemFont = not asciiOnly)
    if self.theme == 1: # evilynux - No outline for GH3
      font3     = lambda: Font(pauseFont, fontSize[2], scale = scale2, reversed = reversed, systemFont = not asciiOnly, outline = False)
    else:
      font3     = lambda: Font(pauseFont, fontSize[2], scale = scale2, reversed = reversed, systemFont = not asciiOnly)
    font4     = lambda: Font(scoreFont, fontSize[3], scale = scale2, reversed = reversed, systemFont = not asciiOnly, outline = False)
    font5     = lambda: Font(streakFont, fontSize[3], scale = scale2, reversed = reversed, systemFont = not asciiOnly, outline = False)
    if self.theme == 1:
      font6     = lambda: Font(loadingFont, fontSize[3], scale = scale2*1.4, reversed = reversed, systemFont = not asciiOnly, outline = False, shadow = True) #Worldrave - Added shadow to Loading Phrases in GH-Based Theme's
    else:
      font6     = lambda: Font(loadingFont, fontSize[3], scale = scale2, reversed = reversed, systemFont = not asciiOnly, outline = False)
    if self.theme == 2:
      font7     = lambda: Font(songFont, fontSize[4], scale = scale2, reversed = reversed, systemFont = not asciiOnly, outline = False)#kk69: loads font specific for song name in Guitar Scene =)
    else:
      font7     = lambda: Font(songFont, fontSize[0], scale = scale2, reversed = reversed, systemFont = not asciiOnly, outline = False)#kk69: loads font specific for song name in Guitar Scene =)
    font8     = lambda: Font(songListFont, fontSize[3], scale = scale2, reversed = reversed, systemFont = not asciiOnly, outline = False) #MFH
    font9     = lambda: Font(shadowfont, fontSize[3], scale = scale2, reversed = reversed, systemFont = not asciiOnly, outline = False, shadow = True) #blazingamer
    font10    = lambda: Font(streakFont2, fontSize[2], scale = scale2*1.08, reversed = reversed, systemFont = not asciiOnly, outline = False, shadow = True) #blazingamer - Worldrave modified size to accuracy.


    resource.load(self, "font",         font1, onLoad = self.customizeFont, synch = True)
    resource.load(self, "bigFont",      font2, onLoad = self.customizeFont, synch = True)


    #MFH - seems like these should be up here...
    menuFont = resource.fileName(os.path.join("themes",themename,"menu.ttf"))
    pauseFont = resource.fileName(os.path.join("themes",themename,"pause.ttf"))
    scoreFont = resource.fileName(os.path.join("themes",themename,"score.ttf"))

    if self.fileExists(os.path.join("themes",themename,"Streak.ttf")):
      streakFont = resource.fileName(os.path.join("themes",themename,"streak.ttf"))
    else:
      streakFont = resource.fileName(os.path.join("themes",themename,"score.ttf"))
    if self.fileExists(os.path.join("themes",themename,"Song.ttf")):
      songFont = resource.fileName(os.path.join("themes",themename,"song.ttf"))
    else:
      songFont = resource.fileName(os.path.join("themes",themename,"menu.ttf"))#kk69: use menu font when song font is not present

    if self.fileExists(os.path.join("themes",themename,"loading.ttf")):
      loadingFont = resource.fileName(os.path.join("themes",themename,"loading.ttf"))
    else:
      loadingFont = resource.fileName("default.ttf")

    if self.fileExists(os.path.join("themes",themename,"songlist.ttf")):
      songListFont = resource.fileName(os.path.join("themes",themename,"songlist.ttf"))
    else:
      songListFont = menuFont
    if self.fileExists(os.path.join("themes",themename,"songlist.ttf")):
      shadowfont = resource.fileName(os.path.join("themes",themename,"songlist.ttf"))
    else:
      shadowfont = menuFont

    #blazingamer
    if self.fileExists(os.path.join("themes",themename,"streakphrase.ttf")):
      streakFont2 = resource.fileName(os.path.join("themes",themename,"streakphrase.ttf"))
    else:
      streakFont2 = menuFont

    #blazingamer:Reorganized
    if self.theme == 0:
      font1     = lambda: Font(menuFont,  fontSize[2], scale = scale*.5, reversed = reversed, systemFont = not asciiOnly)
      font2     = lambda: Font(menuFont,  fontSize[2], scale = scale*.5, reversed = reversed, systemFont = not asciiOnly, outline = False)
      resource.load(self, "lfont",         font2, onLoad = self.customizeFont, synch = True)
      resource.load(self, "font",          font1, onLoad = self.customizeFont, synch = True)
    elif self.theme == 1:
      font1     = lambda: Font(menuFont,  fontSize[3], scale = scale*.5, reversed = reversed, systemFont = not asciiOnly, outline = False) #Worldrave - Removed outline from options text on GH-Based theme's. No other drawbacks noticed.
      font2     = lambda: Font(menuFont,  fontSize[3], scale = scale*.5, reversed = reversed, systemFont = not asciiOnly, outline = False)
      resource.load(self, "lfont",         font2, onLoad = self.customizeFont, synch = True)
      resource.load(self, "font",          font1, onLoad = self.customizeFont, synch = True)
    elif self.theme == 2:
      font1     = lambda: Font(menuFont,  fontSize[4], scale = scale*.5, reversed = reversed, systemFont = not asciiOnly, outline = False)
      resource.load(self, "font",          font1, onLoad = self.customizeFont, synch = True)


    resource.load(self, "pauseFont",     font3, onLoad = self.customizeFont, synch = True)
    resource.load(self, "scoreFont",     font4, onLoad = self.customizeFont, synch = True)
    resource.load(self, "streakFont",    font5, onLoad = self.customizeFont, synch = True)
    resource.load(self, "songFont",      font7, onLoad = self.customizeFont, synch = True)
    resource.load(self, "streakFont2",    font10, onLoad = self.customizeFont, synch = True)#blazingamer

    resource.load(self, "songListFont",      font8, onLoad = self.customizeFont, synch = True)
    resource.load(self, "shadowfont",      font9, onLoad = self.customizeFont, synch = True)
    resource.load(self, "loadingFont",    font6, onLoad = self.customizeFont, synch = True)


    if self.fileExists(os.path.join("themes",themename,"sounds","starding.ogg")):
      self.loadSoundEffect(self, "starDingSound", os.path.join("themes",themename,"sounds","starding.ogg"))
      self.starDingSoundFound = True
    else:
      Log.debug("Star ding sound not found, loading another sound.")
      self.loadSoundEffect(self, "starDingSound", os.path.join("sounds","clapsound.ogg"))
      self.starDingSoundFound = False

    if self.fileExists(os.path.join("themes",themename,"sounds","starlost.ogg")):
      self.loadSoundEffect(self, "starLostSound", os.path.join("themes",themename,"sounds","starlost.ogg"))
      self.starLostSoundFound = True
    else:
      if self.fileExists(os.path.join("sounds","starlost.ogg")):
        self.loadSoundEffect(self, "starLostSound", os.path.join("sounds","starlost.ogg"))
        self.starLostSoundFound = True
      else:
        Log.debug("Star lost sound not found, loading another sound.")
        self.loadSoundEffect(self, "starLostSound", os.path.join("sounds","clapsound.ogg"))
        self.starLostSoundFound = False

    if self.fileExists(os.path.join("sounds","bassdrum.ogg")):
      self.loadSoundEffect(self, "bassDrumSound", os.path.join("sounds","bassdrum.ogg"))
      self.bassDrumSoundFound = True
    else:
      Log.debug("Bass drum sound not found, loading another sound.")
      self.loadSoundEffect(self, "bassDrumSound", os.path.join("sounds","clapsound.ogg"))
      self.bassDrumSoundFound = False
     
#Faaa Drum sound
    if self.fileExists(os.path.join("sounds","tom01.ogg")):
      self.loadSoundEffect(self, "T1DrumSound", os.path.join("sounds","tom01.ogg"))
      self.T1DrumSoundFound = True
    else:
      Log.debug("Drum sound tom01 not found, loading another sound.")
      self.loadSoundEffect(self, "T1DrumSound", os.path.join("sounds","clapsound.ogg"))
      self.T1DrumSoundFound = False	 
    if self.fileExists(os.path.join("sounds","tom02.ogg")):
      self.loadSoundEffect(self, "T2DrumSound", os.path.join("sounds","tom02.ogg"))
      self.T2DrumSoundFound = True
    else:
      Log.debug("Drum sound tom02 not found, loading another sound.")
      self.loadSoundEffect(self, "T2DrumSound", os.path.join("sounds","clapsound.ogg"))
      self.T2DrumSoundFound = False	
    if self.fileExists(os.path.join("sounds","tom03.ogg")):
      self.loadSoundEffect(self, "T3DrumSound", os.path.join("sounds","tom03.ogg"))
      self.T3DrumSoundFound = True
    else:
      Log.debug("Drum sound tom03 not found, loading another sound.")
      self.loadSoundEffect(self, "T3DrumSound", os.path.join("sounds","clapsound.ogg"))
      self.T3DrumSoundFound = False
    if self.fileExists(os.path.join("sounds","crash.ogg")):
      self.loadSoundEffect(self, "CDrumSound", os.path.join("sounds","crash.ogg"))
      self.CDrumSoundFound = True
    else:
      Log.debug("Drum sound crash not found, loading another sound.")
      self.loadSoundEffect(self, "CDrumSound", os.path.join("sounds","clapsound.ogg"))
      self.CDrumSoundFound = False

    # load sounds
    resource.load(self, "screwUpsounds", self.loadScrewUpsounds)
    resource.load(self, "screwUpsoundsBass", self.loadScrewUpsoundsBass)
    resource.load(self, "screwUpsoundsDrums", self.loadScrewUpsoundsDrums)    #myfingershurt: drum screw up sounds
    
    resource.load(self, "acceptSounds", self.loadAcceptSounds)    #myfingershurt
    resource.load(self, "cancelSounds", self.loadBackSounds)    #myfingershurt
    
    resource.load(self, "symcsounds", self.loadScrewUpsounds)
    self.loadSoundEffect(self, "selectSound1", os.path.join("themes",themename,"sounds","select1.ogg"))
    self.loadSoundEffect(self, "selectSound2", os.path.join("themes",themename,"sounds","select2.ogg"))
    self.loadSoundEffect(self, "selectSound3", os.path.join("themes",themename,"sounds","select3.ogg"))
    self.loadSoundEffect(self, "startSound",   os.path.join("themes",themename,"sounds","start.ogg"))
    self.loadSoundEffect(self, "starSound", os.path.join("themes",themename,"sounds","starpower.ogg"))

    if self.fileExists(os.path.join("themes",themename,"sounds","failsound.ogg")):
      self.loadSoundEffect(self, "failSound", os.path.join("themes",themename,"sounds","failsound.ogg"))
    else: #MFH: Fallback on general failsound.ogg
      self.loadSoundEffect(self, "failSound", os.path.join("sounds","failsound.ogg"))
      Log.warn(themename + "\sounds\ failsound.ogg not found -- using general failsound.ogg instead.")
      
    #myfingershurt: integrating Capo's starpower clap sounds
    self.loadSoundEffect(self, "clapSound", os.path.join("sounds","clapsound.ogg"))

    if self.fileExists(os.path.join("themes",themename,"sounds","starpowerready.ogg")):
      self.loadSoundEffect(self, "starReadySound", os.path.join("themes",themename,"sounds","starpowerready.ogg"))
    else: #MFH: Fallback on starpower.ogg
      self.loadSoundEffect(self, "starReadySound", os.path.join("themes",themename,"sounds","starpower.ogg"))
      Log.warn(themename + "\sounds\starpowerready.ogg not found -- using starpower.ogg instead.")

    #MFH - fallback on sounds\crowdcheers.ogg, and then starpower.ogg.  Note if the fallback crowdcheers was used or not.    
    if self.fileExists(os.path.join("themes",themename,"sounds","crowdcheers.ogg")):
      self.loadSoundEffect(self, "crowdSound", os.path.join("themes",themename,"sounds","crowdcheers.ogg"))
      self.cheerSoundFound = 2
    elif self.fileExists(os.path.join("sounds","crowdcheers.ogg")):
      self.loadSoundEffect(self, "crowdSound", os.path.join("sounds","crowdcheers.ogg"))
      self.cheerSoundFound = 1
      Log.warn(themename + "\sounds\crowdcheers.ogg not found -- using data\sounds\crowdcheers.ogg instead.")
    else: #MFH: Fallback on starpower.ogg
      self.loadSoundEffect(self, "crowdSound", os.path.join("themes",themename,"sounds","starpower.ogg"))
      self.cheerSoundFound = 0
      Log.warn(themename + "\sounds\crowdcheers.ogg not found -- using starpower.ogg instead.")

    if self.fileExists(os.path.join("themes",themename,"sounds","staractivate.ogg")):
      self.loadSoundEffect(self, "starActivateSound", os.path.join("themes",themename,"sounds","staractivate.ogg"))
    else: #MFH: Fallback on starpower.ogg
      self.loadSoundEffect(self, "starActivateSound", os.path.join("themes",themename,"sounds","starpower.ogg"))
      Log.warn(themename + "\sounds\staractivate.ogg not found -- using starpower.ogg instead.")

    if self.fileExists(os.path.join("themes",themename,"sounds","stardeactivate.ogg")):
      self.loadSoundEffect(self, "starDeActivateSound", os.path.join("themes",themename,"sounds","stardeactivate.ogg"))
      self.starDeActivateSoundFound = True
    else: #MFH: Fallback on starpower.ogg - required to load, but will not be played.
      self.loadSoundEffect(self, "starDeActivateSound", os.path.join("themes",themename,"sounds","starpower.ogg"))
      self.starDeActivateSoundFound = False
      Log.warn(themename + "\sounds\stardeactivate.ogg not found -- sound disabled.")
    
    if self.fileExists(os.path.join("themes",themename,"sounds","rescue.ogg")):
      self.loadSoundEffect(self, "rescueSound", os.path.join("themes",themename,"sounds","rescue.ogg"))
    elif self.fileExists(os.path.join("themes",themename,"sounds","staractivate.ogg")):
      self.loadSoundEffect(self, "rescueSound", os.path.join("themes",themename,"sounds","staractivate.ogg"))
      Log.warn(themename + "\sounds\rescue.ogg not found -- using staractivate.ogg instead.")
    else:
      self.loadSoundEffect(self, "rescueSound", os.path.join("themes",themename,"sounds","starpower.ogg"))
      Log.warn(themename + "\sounds\rescue.ogg not found -- using starpower.ogg instead.")
    
    if self.fileExists(os.path.join("themes",themename,"sounds","coopfail.ogg")):
      self.loadSoundEffect(self, "coOpFailSound",os.path.join("themes",themename,"sounds","coopfail.ogg"))
    elif self.fileExists(os.path.join("themes",themename,"sounds","stardeactivate.ogg")):
      self.loadSoundEffect(self, "coOpFailSound",os.path.join("themes",themename,"sounds","stardeactivate.ogg"))
      Log.warn(themename + "\sounds\coopfail.ogg not found -- using stardeactivate.ogg instead")
    elif self.fileExists(os.path.join("themes",themename,"sounds","out.ogg")):  #MFH - not all themes have out.ogg!
      self.loadSoundEffect(self, "coOpFailSound",os.path.join("themes",themename,"sounds","out.ogg"))
      Log.warn(themename + "\sounds\coopfail.ogg not found -- using out.ogg instead")
    else:
      self.loadSoundEffect(self, "coOpFailSound",os.path.join("themes",themename,"sounds","back1.ogg"))
      Log.warn(themename + "\sounds\coopfail.ogg not found -- using back1.ogg instead")



    #myfingershurt: adding You Rock sound effect
    if self.fileExists(os.path.join("themes",themename,"sounds","rocksound.ogg")):
      self.loadSoundEffect(self, "rockSound", os.path.join("themes",themename,"sounds","rocksound.ogg"))
    else:
      self.loadSoundEffect(self, "rockSound", os.path.join("sounds","rocksound.ogg"))
    
    #if self.theme == 0 or self.theme == 1:#GH2 or GH3
    #  #self.loadSoundEffect(self, "acceptSound",  os.path.join("themes",themename,"sounds","in.ogg"))
    #  self.loadSoundEffect(self, "cancelSounds",  os.path.join("themes",themename,"sounds","out.ogg"))
    #elif self.theme == 2:
    #  #self.loadSoundEffect(self, "acceptSound",  os.path.join("themes",themename,"sounds","action.ogg"))
    #  self.loadSoundEffect(self, "cancelSounds",  os.path.join("themes",themename,"sounds","out.ogg"))

  
  def SetAllScrewUpSoundFxObjectVolumes(self, volume):   #MFH - single function to go through all screwup sound objects and set object volume to the given volume
    for s in self.screwUpsounds:
      s.setVolume(volume)
    for s in self.screwUpsoundsBass:
      s.setVolume(volume)
    for s in self.screwUpsoundsDrums:
      s.setVolume(volume)
  
  def SetAllSoundFxObjectVolumes(self, volume):   #MFH - single function to go through all sound objects (and iterate through all sound lists) and set object volume to the given volume
    #MFH TODO - set every sound object's volume here...
    self.starDingSound.setVolume(volume)
    self.bassDrumSound.setVolume(volume)
    self.T1DrumSound.setVolume(volume)
    self.T2DrumSound.setVolume(volume)
    self.T3DrumSound.setVolume(volume)
    self.CDrumSound.setVolume(volume)
    for s in self.acceptSounds:
      s.setVolume(volume)
    for s in self.cancelSounds:
      s.setVolume(volume)
    #self.cancelSounds.setVolume(volume)
    self.rockSound.setVolume(volume)
    self.starDeActivateSound.setVolume(volume)
    self.starActivateSound.setVolume(volume)
    self.rescueSound.setVolume(volume)
    self.coOpFailSound.setVolume(volume)
    self.crowdSound.setVolume(volume)
    self.starReadySound.setVolume(volume)
    self.clapSound.setVolume(volume)
    self.failSound.setVolume(volume)
    self.starSound.setVolume(volume)
    self.startSound.setVolume(volume)
    self.selectSound1.setVolume(volume)
    self.selectSound2.setVolume(volume)
    self.selectSound3.setVolume(volume)
    

  def loadSoundEffect(self, target, name, fileName):
    volume   = self.sfxVolume
    fileName = self.resource.fileName(fileName)
    self.resource.load(target, name, lambda: Sound(fileName), onLoad = lambda s: s.setVolume(volume))


  def determineNumSounds(self, soundPath, soundPrefix, soundExtension = ".ogg"):   #MFH - auto random sound enumeration
    soundNum = 1
    while self.fileExists(os.path.join(soundPath,"%s%d%s" % (soundPrefix, soundNum, soundExtension) ) ):
      soundNum += 1
    return soundNum-1

  def getSoundObjectList(self, soundPath, soundPrefix, numSounds, soundExtension = ".ogg"):   #MFH
    Log.debug( str(numSounds) + " " + soundPrefix + " sounds found in " + soundPath + ": " + soundPrefix + "1" + soundExtension + " - " + soundPrefix + str(numSounds) + soundExtension )
    return [Sound(self.resource.fileName(os.path.join(soundPath,"%s%d%s" % (soundPrefix, i, soundExtension) ))) for i in range(1, numSounds+1)]

  def loadBackSounds(self):   #MFH - adding optional support for random choice between two back sounds
    soundPathTheme = os.path.join("themes",self.themeLabel,"sounds")
    soundPathData = "sounds"
    soundPath = soundPathTheme
    soundPrefix = "back"
    numSounds = self.determineNumSounds(soundPath, soundPrefix)
    if numSounds > 0:
      return self.getSoundObjectList(soundPath, soundPrefix, numSounds)
    else:
      return [Sound(self.resource.fileName(os.path.join("themes",self.themeLabel,"sounds","out.ogg")))]

  def loadAcceptSounds(self):
    soundPathTheme = os.path.join("themes",self.themeLabel,"sounds")
    soundPathData = "sounds"
    soundPath = soundPathTheme
    soundPrefix = "accept"
    numSounds = self.determineNumSounds(soundPath, soundPrefix)
    if numSounds > 0:
      return self.getSoundObjectList(soundPath, soundPrefix, numSounds)
    else:
      if self.theme == 0 or self.theme == 1:#GH2 or GH3
        return [Sound(self.resource.fileName(os.path.join("themes",self.themeLabel,"sounds","in.ogg")))]
      elif self.theme == 2:
        return [Sound(self.resource.fileName(os.path.join("themes",self.themeLabel,"sounds","action.ogg")))]
    
  def loadScrewUpsounds(self):
    soundPathTheme = os.path.join("themes",self.themeLabel,"sounds")
    soundPathData = "sounds"
    soundPath = soundPathTheme
    soundPrefix = "guitscw"
    numSounds = self.determineNumSounds(soundPath, soundPrefix)
    if numSounds == 0:
      soundPath = soundPathData
      numSounds = self.determineNumSounds(soundPath, soundPrefix)
    return self.getSoundObjectList(soundPath, soundPrefix, numSounds)

  def loadScrewUpsoundsBass(self):
    soundPathTheme = os.path.join("themes",self.themeLabel,"sounds")
    soundPathData = "sounds"
    soundPath = soundPathTheme
    soundPrefix = "bassscw"
    numSounds = self.determineNumSounds(soundPath, soundPrefix)
    if numSounds == 0:
      soundPath = soundPathData
      numSounds = self.determineNumSounds(soundPath, soundPrefix)
    return self.getSoundObjectList(soundPath, soundPrefix, numSounds)

  def loadScrewUpsoundsDrums(self):
    soundPathTheme = os.path.join("themes",self.themeLabel,"sounds")
    soundPathData = "sounds"
    soundPath = soundPathTheme
    soundPrefix = "drumscw"
    numSounds = self.determineNumSounds(soundPath, soundPrefix)
    if numSounds == 0:
      soundPath = soundPathData
      numSounds = self.determineNumSounds(soundPath, soundPrefix)
    return self.getSoundObjectList(soundPath, soundPrefix, numSounds)
  
  def loadSyncsounds(self):
    return [Sound(self.resource.fileName("sync%d.ogg" % i)) for i in range(1, 2)]
  
  def loadImgDrawing(self, target, name, fileName, textureSize = None):
    """
    Load an SVG drawing synchronously.

    @param target:      An object that will own the drawing
    @param name:        The name of the attribute the drawing will be assigned to
    @param fileName:    The name of the file in the data directory
    @param textureSize  Either None or (x, y), in which case the file will
                        be rendered to an x by y texture
    @return:            L{ImgDrawing} instance
    """
    fileName = self.resource.fileName(fileName)
    drawing  = self.resource.load(target, name, lambda: ImgDrawing(self.svg, fileName), synch = True)
    if textureSize:
      drawing.convertToTexture(textureSize[0], textureSize[1])
    return drawing
  
  #glorandwarf: changed name to getPath
  def getPath(self, fileName):
    return self.resource.fileName(fileName)

  #myfingershurt: still need this fileexists function:
  def fileExists(self, fileName):
    fileName = self.resource.fileName(fileName)
    return os.path.exists(fileName)

      
  def customizeFont(self, font):
    # change some predefined characters to custom images
    font.setCustomGlyph(STAR1, self.star1.texture)
    font.setCustomGlyph(STAR2, self.star2.texture)
    font.setCustomGlyph(STAR3, self.star3.texture)
    font.setCustomGlyph(STAR4, self.star4.texture)
    font.setCustomGlyph(LEFT,  self.left.texture)
    font.setCustomGlyph(RIGHT, self.right.texture)
    # evilynux - Load cache to speedup rendering
    if Config.get("performance", "preload_glyph_cache"):
      font.loadCache()

#MFH - acceptSound and selectSound will now be merged into either 10 random sounds or just the acceptSound as a fallback:
  def getAcceptSound(self):
    """@return: A randomly chosen selection sound."""
    return random.choice(self.acceptSounds)

  acceptSound = property(getAcceptSound)

  def getBackSound(self):
    """@return: A randomly chosen selection sound."""
    return random.choice(self.cancelSounds)

  cancelSound = property(getBackSound)


  def getSelectSound(self):
    """@return: A randomly chosen selection sound."""
    return random.choice([self.selectSound1, self.selectSound2, self.selectSound3])

  selectSound = property(getSelectSound)

  def getScrewUpSound(self):
    """@return: A randomly chosen screw-up sound."""
    return random.choice(self.screwUpsounds)

  def getScrewUpSoundBass(self):
    """@return: A randomly chosen screw-up sound."""
    return random.choice(self.screwUpsoundsBass)

  #myfingershurt: drums screw up sounds
  def getScrewUpSoundDrums(self):
    """@return: A randomly chosen screw-up sound."""
    return random.choice(self.screwUpsoundsDrums)

  screwUpSound = property(getScrewUpSound)
  screwUpSoundBass = property(getScrewUpSoundBass)
  screwUpSoundDrums = property(getScrewUpSoundDrums)    #myfingershurt: drum screw up sounds
  
  def essentialResourcesLoaded(self):
    """return: True if essential resources such as the font have been loaded."""
    return bool(self.font and self.bigFont)

  def resourcesLoaded(self):
    """return: True if all the resources have been loaded."""
    return not None in self.__dict__.values()

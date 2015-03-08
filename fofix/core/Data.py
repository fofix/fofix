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

import os
import glob
import random

from fofix.core.Font import Font
from fofix.core.Image import ImgDrawing
from fofix.core.Audio import Sound
from fofix.core import Config
from fofix.core import Version
from fofix.core import Player
from fofix.core import Log

# these constants define a few customized letters in the default font
#MFH - with the new simplified Font.py, no more custom glyphs... let's do a simple replacement here for now...
STAR1 = ' '
STAR2 = '*'
LEFT  = '<'
RIGHT = '>'
STAR3 = STAR1
STAR4 = STAR2

#-STAR1 = unicode('\x10')
#-STAR2 = unicode('\x11')
#-LEFT  = unicode('\x12')
#-RIGHT = unicode('\x13')
#-STAR3 = unicode('\x14')  #Worldrave - Added new Star3
#-STAR4 = unicode('\x15')  #Worldrave - Added new Star4

class Data(object):
    """A collection of globally used data resources such as fonts and sound effects."""
    def __init__(self, resource, svg):

        self.logClassInits = Config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("Data class init (Data.py)...")
        self.logLoadings = Config.get("game", "log_loadings")

        self.logImageNotFound = Config.get("log", "log_image_not_found")

        self.resource = resource
        self.svg      = svg

        self.sfxVolume    = Config.get("audio", "SFX_volume")
        self.crowdVolume  = Config.get("audio", "crowd_volume")

        #Get theme
        themename = Config.get("coffee", "themename")
        self.themeLabel = themename
        self.themeCoOp  = False

        self.players = None
        self.players = Player.loadPlayers()

        #myfingershurt: check for existence of theme path
        themepath = os.path.join(Version.dataPath(), "themes")
        self.themepath = themepath
        self.path = Version.dataPath()

        if not self.checkImgDrawing(os.path.join("themes",themename,"notes","notes.png")):
            #myfingershurt: here need to ensure an existing theme is selected
            themes = []
            defaultTheme = None           #myfingershurt
            allthemes = os.listdir(themepath)
            for name in allthemes:
                if self.checkImgDrawing(os.path.join("themes",name,"notes","notes.png")):
                    themes.append(name)
                    if name == "MegaLight V4":         #myfingershurt
                        defaultTheme = name     #myfingershurt
            if defaultTheme != "MegaLight V4":     #myfingershurt
                defaultTheme = themes[0]    #myfingershurt
            #not a valid theme if notes.png isn't there!  Force default theme:
            Config.set("coffee", "themename",defaultTheme)
            #re-init Data with new default
            themename = defaultTheme
            self.themeLabel = themename


        if not os.path.exists(os.path.join(Version.dataPath(), "themes", themename, "vocals")):
            self.vocalPath = "vocals"
        else:
            self.vocalPath = os.path.join("themes",themename,"vocals")

        self.theme = 2
        self.themeCoOp = True

        self.fontScreenBottom = 0.75      #from our current viewport's constant 3:4 aspect ratio (which is always stretched to fill the video resolution)

        self.loadPartImages()
        #myfingershurt: multi-OS compatibility file access fixes using os.path.join()
        # load font customization images

        #Worldrave - Use new defined Star3 and star4. Using star1 and star2 as a fallback.

        #MFH - no more custom glyphs, these are wasting memory.
        #MFH - but we do need these star1-4 images anyway.  Leaving them loaded here in the Data object.
        self.loadImgDrawing(self, "star1",   os.path.join("themes",themename,"star1.png"), textureSize = (128, 128))
        self.loadImgDrawing(self, "star2",   os.path.join("themes",themename,"star2.png"), textureSize = (128, 128))

        #MFH - let's not rely on errors here if we don't have to...
        if not self.loadImgDrawing(self, "star3",   os.path.join("themes",themename,"star3.png"), textureSize = (128, 128)):
            self.star3 = self.star1
        if not self.loadImgDrawing(self, "star4",   os.path.join("themes",themename,"star4.png"), textureSize = (128, 128)):
            self.star4 = self.star2


        if self.loadImgDrawing(self, "starPerfect",   os.path.join("themes",themename,"starperfect.png"), textureSize = (128, 128)):
            self.perfectStars = True
            self.maskStars = False
        else:
            self.starPerfect = self.star2
            self.fcStars   = False
            self.starFC     = self.star2
            self.maskStars = True
            self.perfectStars = False

        if self.perfectStars:
            if self.loadImgDrawing(self, "starFC",   os.path.join("themes",themename,"starfc.png"), textureSize = (128, 128)):
                self.fcStars   = True
            else:
                self.starFC = self.starPerfect
                self.fcStars = False

        # load misc images
        self.loadImgDrawing(self, "loadingImage", os.path.join("themes",themename,"loadingbg.png"), textureSize = (256,256))
        self.loadImgDrawing(self, "optionsBG", os.path.join("themes",themename,"menu","optionsbg.png"))
        if self.loadImgDrawing(self, "submenuSelect", os.path.join("themes",themename,"submenuselect.png")):
            subSelectImgW = self.submenuSelect.width1()
            self.submenuSelectFound = True
            self.subSelectWFactor = 640.000/subSelectImgW
            self.subSelectImgH = self.submenuSelect.height1()
        else:
            self.submenuSelectFound = False
            self.loadImgDrawing(self, "submenuSelect", os.path.join("themes",themename,"menu","selected.png"))
            self.subSelectWFactor = 0
        # load all the data in parallel
        # asciiOnly = not bool(Language.language) or Language.language == "Custom"
        # reversed  = _("__lefttoright__") == "__righttoleft__" and True or False
        asciiOnly = True
        reversed  = False
        scale     = 1
        # evilynux - Load bigger fonts so they're nicer when scaled, scaling readjusted
        fontSize  = [44, 132, 34, 32, 30]
        w, h = [int(s) for s in Config.get("video", "resolution").split("x")]
        aspectRatio = float(w)/float(h)

        self.fontList = [
          ["font1","font","default.ttf",fontSize[4]],
          ["font2","bigFont","title.ttf",fontSize[1]],
          ["font3","pauseFont","pause.ttf",fontSize[2]],
          ["font4","scoreFont","score.ttf",fontSize[3]],
          ["font5","streakFont","streak.ttf",fontSize[3]],
          ["font6","loadingFont","loading.ttf",fontSize[3]],
          ["font7","songFont","song.ttf",fontSize[4]],
          ["font8","songListFont","songlist.ttf",fontSize[3]],
          ["font9","shadowFont","songlist.ttf",fontSize[3]],
          ["font10","streakFont2","streakphrase.ttf",fontSize[2]]
        ]
        for f in self.fontList:
            if self.fileExists(os.path.join("themes",themename,"fonts",f[2])):
                fn = resource.fileName(os.path.join("themes",themename,"fonts",f[2]))
                f[0] = lambda: Font(fn, f[3], scale = scale*.5, reversed = reversed, systemFont = not asciiOnly, outline = False, aspectRatio = aspectRatio)
                resource.load(self,f[1],f[0], synch = True)
            elif self.fileExists(os.path.join("themes",themename,"fonts","default.ttf")):
                Log.debug("Theme font not found: " + f[2])
                fn = resource.fileName(os.path.join("themes",themename,"fonts","default.ttf"))
                f[0] = lambda: Font(fn, f[3], scale = scale*.5, reversed = reversed, systemFont = not asciiOnly, outline = False, aspectRatio = aspectRatio)
                resource.load(self,f[1],f[0], synch = True)
            else:
                Log.debug("Default theme font not found: %s - using built-in default" % str(f[2]))
                fn = resource.fileName(os.path.join("fonts","default.ttf"))
                f[0] = lambda: Font(fn, f[3], scale = scale*.5, reversed = reversed, systemFont = not asciiOnly, outline = False, aspectRatio = aspectRatio)
                resource.load(self,f[1],f[0], synch = True)


        self.fontDict = {"font": self.font, "bigFont": self.bigFont, "pauseFont": self.pauseFont, "scoreFont": self.scoreFont, \
                         "streakFont": self.streakFont, "songFont": self.songFont, "streakFont2": self.streakFont2, \
                         "songListFont": self.songListFont, "shadowFont": self.shadowFont, "loadingFont": self.loadingFont}

        assert self.fontDict['font'] == self.font

        # load sounds asynchronously
        resource.load(self, "screwUpsounds", self.loadScrewUpsounds)
        resource.load(self, "screwUpsoundsBass", self.loadScrewUpsoundsBass)
        resource.load(self, "screwUpsoundsDrums", self.loadScrewUpsoundsDrums)
        resource.load(self, "acceptSounds", self.loadAcceptSounds)
        resource.load(self, "cancelSounds", self.loadBackSounds)

        # loadSoundEffect asynchronously
        self.syncSounds = [
          ["bassDrumSound","bassdrum.ogg"],
          ["battleUsedSound","battleused.ogg"],
          ["CDrumSound","crash.ogg"],
          ["clapSound","clapsound.ogg"],
          ["coOpFailSound","coopfail.ogg"],
          #["crowdSound","crowdcheers.ogg"],
          ["failSound","failsound.ogg"],
          ["rescueSound","rescue.ogg"],
          ["rockSound","rocksound.ogg"],
          ["selectSound1","select1.ogg"],
          ["selectSound2","select2.ogg"],
          ["selectSound3","select3.ogg"],
          ["starActivateSound","staractivate.ogg"],
          ["starDeActivateSound","stardeactivate.ogg"],
          ["starDingSound","starding.ogg"],
          ["starLostSound","starlost.ogg"],
          ["starReadySound","starpowerready.ogg"],
          ["starSound","starpower.ogg"],
          ["startSound","start.ogg"],
          ["HiHatDrumSound","hihatclosed.ogg"],
          ["SnareDrumSound","snare.ogg"],
          ["T1DrumSound","tom01.ogg"],
          ["T2DrumSound","tom02.ogg"],
          ["T3DrumSound","tom03.ogg"],
          ["RideDrumSound","ride.ogg"]
        ]
        for self.sounds in self.syncSounds:
            if self.fileExists(os.path.join("themes",themename,"sounds",self.sounds[1])):
                self.loadSoundEffect(self, self.sounds[0], os.path.join("themes",themename,"sounds",self.sounds[1]))
            elif self.fileExists(os.path.join("sounds", self.sounds[1])):
                Log.debug("Theme sound not found: " + self.sounds[1])
                self.loadSoundEffect(self, self.sounds[0], os.path.join("sounds",self.sounds[1]))
            else:
                Log.warn("File " + self.sounds[1] + " not found using default instead.")
                self.loadSoundEffect(self, self.sounds[0], os.path.join("sounds","default.ogg"))

        #TODO: Simplify crowdSound stuff so it can join the rest of us.
        #MFH - fallback on sounds/crowdcheers.ogg, and then starpower.ogg. Note if the fallback crowdcheers was used or not.
        if self.fileExists(os.path.join("themes",themename,"sounds","crowdcheers.ogg")):
            self.loadSoundEffect(self, "crowdSound", os.path.join("themes",themename,"sounds","crowdcheers.ogg"), crowd = True)
            self.cheerSoundFound = 2
        elif self.fileExists(os.path.join("sounds","crowdcheers.ogg")):
            self.loadSoundEffect(self, "crowdSound", os.path.join("sounds","crowdcheers.ogg"), crowd = True)
            self.cheerSoundFound = 1
            Log.warn(themename + "/sounds/crowdcheers.ogg not found -- using data/sounds/crowdcheers.ogg instead.")
        else:
            self.cheerSoundFound = 0
            Log.warn("crowdcheers.ogg not found -- no crowd cheering.")

    def loadPartImages(self):
        self.partImages = []
        self.partImages.append(self.loadImgDrawing(None, "guitar", os.path.join("themes",self.themeLabel,"common","guitar.png")))
        self.partImages.append(self.loadImgDrawing(None, "rhythm", os.path.join("themes",self.themeLabel,"common","rhythm.png")))
        self.partImages.append(self.loadImgDrawing(None, "bass", os.path.join("themes",self.themeLabel,"common","bass.png")))
        self.partImages.append(self.loadImgDrawing(None, "lead", os.path.join("themes",self.themeLabel,"common","lead.png")))
        self.partImages.append(self.loadImgDrawing(None, "drum", os.path.join("themes",self.themeLabel,"common","drum.png")))
        self.partImages.append(self.loadImgDrawing(None, "vocal", os.path.join("themes",self.themeLabel,"common","vocal.png")))

    def SetAllScrewUpSoundFxObjectVolumes(self, volume):   #MFH - single function to go through all screwup sound objects and set object volume to the given volume
        for s in self.screwUpsounds:
            s.setVolume(volume)
        for s in self.screwUpsoundsBass:
            s.setVolume(volume)
        for s in self.screwUpsoundsDrums:
            s.setVolume(volume)

    def SetAllSoundFxObjectVolumes(self, volume = None):   #MFH - single function to go through all sound objects (and iterate through all sound lists) and set object volume to the given volume
        #MFH TODO - set every sound object's volume here...
        if volume is None:
            self.sfxVolume = Config.get("audio", "SFX_volume")
            self.crowdVolume = Config.get("audio", "crowd_volume")
            volume = self.sfxVolume
        self.starDingSound.setVolume(volume)
        self.bassDrumSound.setVolume(volume)
        self.SnareDrumSound.setVolume(volume)
        self.HiHatDrumSound.setVolume(volume)
        self.RideDrumSound.setVolume(volume)
        self.T1DrumSound.setVolume(volume)
        self.T2DrumSound.setVolume(volume)
        self.T3DrumSound.setVolume(volume)
        self.CDrumSound.setVolume(volume)
        for s in self.acceptSounds:
            s.setVolume(volume)
        for s in self.cancelSounds:
            s.setVolume(volume)
        self.rockSound.setVolume(volume)
        self.starDeActivateSound.setVolume(volume)
        self.starActivateSound.setVolume(volume)
        self.battleUsedSound.setVolume(volume)
        self.rescueSound.setVolume(volume)
        self.coOpFailSound.setVolume(volume)
        self.crowdSound.setVolume(self.crowdVolume)
        self.starReadySound.setVolume(volume)
        self.clapSound.setVolume(volume)
        self.failSound.setVolume(volume)
        self.starSound.setVolume(volume)
        self.startSound.setVolume(volume)
        self.selectSound1.setVolume(volume)
        self.selectSound2.setVolume(volume)
        self.selectSound3.setVolume(volume)


    def loadSoundEffect(self, target, name, fileName, crowd = False):
        volume   = self.sfxVolume
        if crowd:
            volume = self.crowdVolume
        fileName = self.resource.fileName(fileName)
        self.resource.load(target, name, lambda: Sound(fileName), onLoad = lambda s: s.setVolume(volume))


    def determineNumSounds(self, soundPath, soundPrefix, soundExtension = ".ogg"):   #MFH - auto random sound enumeration
        soundNum = 1
        while self.fileExists(os.path.join(soundPath,"%s%d%s" % (soundPrefix, soundNum, soundExtension) ) ):
            soundNum += 1
        return soundNum-1

    def getSoundObjectList(self, soundPath, soundPrefix, numSounds, soundExtension = ".ogg"):   #MFH
        Log.debug("{0}1{2} - {0}{1}{2} found in {3}".format(soundPrefix, numSounds, soundExtension, soundPath))
        
        sounds = []
        for i in xrange(1, numSounds+1):
            filePath = os.path.join(soundPath, "%s%d%s" % (soundPrefix, i, soundExtension) )
            soundObject = Sound(self.resource.fileName(filePath))
            sounds.append(soundObject)
            
        return sounds

    def loadBackSounds(self):   #MFH - adding optional support for random choice between two back sounds
        soundPathTheme = os.path.join("themes",self.themeLabel,"sounds")
        soundPath = soundPathTheme
        soundPrefix = "back"
        numSounds = self.determineNumSounds(soundPath, soundPrefix)
        if numSounds > 0:
            return self.getSoundObjectList(soundPath, soundPrefix, numSounds)
        else:
            return [Sound(self.resource.fileName(os.path.join("themes",self.themeLabel,"sounds","out.ogg")))]

    def loadAcceptSounds(self):
        soundPathTheme = os.path.join("themes",self.themeLabel,"sounds")
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

    def checkImgDrawing(self, fileName):
        return self.getImgDrawing(fileName, False)

    def getImgDrawing(self, fileName, openImage=True):
        imgDrawing = None
        for dataPath in self.resource.dataPaths:
            fileName1 = os.path.join(dataPath, fileName)
            if self.logLoadings == 1:
                if openImage:
                    Log.notice("Trying to load image: %s" % fileName1)
                else:
                    Log.notice("Checking image: %s" % fileName1)
            #check if fileName1 exists (has extension)
            if os.path.exists(fileName1):
                if openImage == True:
                    try:
                        imgDrawing = ImgDrawing(self.svg, fileName1)
                        return imgDrawing
                    except IOError:
                        Log.warn("Unable to load image file: %s" % fileName1)
                    except OverflowError:
                        Log.warn("Unable to read image file: %s" % fileName1)
                else:
                    return True
            else:
                #find extension
                fileName1 = os.path.splitext(fileName1)[0]
                files = glob.glob('%s.*' % fileName1)
                if openImage == True:
                    for i in range(len(files)):
                        try:
                            imgDrawing = ImgDrawing(self.svg, files[i])
                            return imgDrawing
                        except IOError:
                            Log.warn("Unable to load image file: %s" % files[i])
                elif len(files) > 0:
                    return True
        #image not found
        if self.logImageNotFound:
            Log.debug("Image not found: %s" % fileName)
        return False

    def loadImgDrawing(self, target, name, fileName, textureSize = None):
        """
        Load an SVG drawing synchronously.

        @param target:      An object that will own the drawing
        @param name:        The name of the attribute the drawing will be assigned to
        @param fileName:    The name of the file in the data directory
        @param textureSize: Either None or (x, y), in which case the file will
                            be rendered to an x by y texture
        @return:            L{ImgDrawing} instance
        """
        imgDrawing = self.getImgDrawing(fileName)
        if not imgDrawing:
            if target and name:
                setattr(target, name, None)
            else:
                Log.error("Image not found: " + fileName)
                return None

        if target:
            drawing  = self.resource.load(target, name, lambda: imgDrawing, synch = True)
        else:
            drawing = imgDrawing
        return drawing

    def loadAllImages(self, target, directory, prefix = "img_", textureSize = None): #akedrou
        """
        Loads all images found in a folder to a given target.

        @param target:      An object that will own the drawings
        @param directory:   The directory that will be searched for image files.
        @param textureSize: Either None or (x, y), in which case the files will
                            be rendered to an x by y texture
        """
        if not os.path.isdir(os.path.join(self.path, directory)):
            return None
        imgDict = {}
        for file in os.listdir(os.path.join(self.path, directory)):
            if file == "thumbs.db" or file == "Thumbs.db":
                continue
            elif file[0] == ".":
                continue
            elif os.path.isdir(os.path.join(self.path, directory, file)):
                continue
            name = os.path.splitext(file)[0]
            name = prefix+name
            img = self.loadImgDrawing(target, name, os.path.join(directory, file), textureSize)
            if img and target is None:
                imgDict[name] = img
        if target is None and len(imgDict) > 0:
            return imgDict

    #glorandwarf: changed name to getPath
    def getPath(self, fileName):
        return self.resource.fileName(fileName)

    #myfingershurt: still need this fileexists function:
    def fileExists(self, fileName):
        fileName = self.resource.fileName(fileName)
        return os.path.exists(fileName)


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

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


from View import BackgroundLayer
from Menu import Menu
from Lobby import Lobby, ControlConfigError
from Language import _
import Dialogs
import Config
import Audio
import Settings
import Version
import VFS
from Shader import shaders
import sys
import os

#myfingershurt: needed for random menu music:
import random
import string

import Log

class MainMenu(BackgroundLayer):
  def __init__(self, engine):
    self.engine              = engine

    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("MainMenu class init (MainMenu.py)...")

    self.time                = 0.0
    self.nextLayer           = None
    self.visibility          = 0.0
    self.active              = False
    
    self.showStartupMessages = False

    self.gfxVersionTag = Config.get("game", "gfx_version_tag")
    
    self.chosenNeck = Config.get("game", "default_neck")
    exists = 0

    if engine.loadImgDrawing(self, "ok", os.path.join("necks",self.chosenNeck+".png")):
      exists = 1
    elif engine.loadImgDrawing(self, "ok", os.path.join("necks","Neck_"+self.chosenNeck+".png")):
      exists = 1

    #MFH - fallback logic now supports a couple valid default neck filenames
    #MFH - check for Neck_1
    if exists == 0:
      if engine.loadImgDrawing(self, "ok", os.path.join("necks","Neck_1.png")):
        Config.set("game", "default_neck", "1")
        Log.warn("Default chosen neck not valid; fallback Neck_1.png forced.")
        exists = 1

    #MFH - check for defaultneck
    if exists == 0:
      if engine.loadImgDrawing(self, "ok", os.path.join("necks","defaultneck.png")):
        Log.warn("Default chosen neck not valid; fallback defaultneck.png forced.")
        Config.set("game", "default_neck", "defaultneck")
        exists = 1
      else:
        Log.error("Default chosen neck not valid; fallbacks Neck_1.png and defaultneck.png also not valid!")

    #Get theme
    self.theme       = self.engine.data.theme
    self.themeCoOp   = self.engine.data.themeCoOp
    self.themename   = self.engine.data.themeLabel
    self.useSoloMenu = self.engine.theme.use_solo_submenu
    
    allowMic = True
    
    self.menux = self.engine.theme.menuPos[0]
    self.menuy = self.engine.theme.menuPos[1]

    self.rbmenu = self.engine.theme.menuRB
 
    #MFH
    self.main_menu_scale = self.engine.theme.main_menu_scaleVar
    self.main_menu_vspacing = self.engine.theme.main_menu_vspacingVar

    if not self.engine.loadImgDrawing(self, "background", os.path.join("themes",self.themename,"menu","mainbg.png")):
      self.background = None
    self.engine.loadImgDrawing(self, "BGText", os.path.join("themes",self.themename,"menu","maintext.png"))
    if not self.engine.loadImgDrawing(self, "optionsBG", os.path.join("themes",self.themename,"menu","optionsbg.png")):
      self.optionsBG = None
    self.engine.loadImgDrawing(self, "optionsPanel", os.path.join("themes",self.themename,"menu","optionspanel.png"))
      
    #racer: added version tag
    if self.gfxVersionTag or self.engine.theme.versiontag == True:
      if not self.engine.loadImgDrawing(self, "version", os.path.join("themes",self.themename,"menu","versiontag.png")):
        if not self.engine.loadImgDrawing(self, "version", "versiontag.png"): #falls back on default versiontag.png in data\ folder
          self.version = None
    else:
      self.version = None

    #myfingershurt: random main menu music function, menu.ogg and menuXX.ogg (any filename with "menu" as the first 4 letters)
    filepath = self.engine.getPath(os.path.join("themes",self.themename,"sounds"))
    self.files = []
    allfiles = os.listdir(filepath)
    for name in allfiles:
      if os.path.splitext(name)[1] == ".ogg":
        if string.find(name,"menu") > -1:
          self.files.append(name)
    

    if self.files:
      i = random.randint(0,len(self.files)-1)
      filename = self.files[i]
      sound = os.path.join("themes",self.themename,"sounds",filename)
      self.menumusic = True
      engine.menuMusic = True

      self.song = Audio.Music(self.engine.resource.fileName(sound))
      self.song.setVolume(self.engine.config.get("audio", "menu_volume"))
      self.song.play(0)  #no loop
    else:
      self.menumusic = False

   
 #####======= Racer: New Main Menu ======####

    self.opt_text_color     = self.engine.theme.opt_text_colorVar
    self.opt_selected_color = self.engine.theme.opt_selected_colorVar

    trainingMenu = [
      (_("Tutorials"), self.showTutorial),
      (_("Practice"), lambda: self.newLocalGame(mode1p = 1)),
    ]
    
    self.opt_bkg_size = [float(i) for i in self.engine.theme.opt_bkg_size]

    strCareer = ""
    strQuickplay = ""
    strSolo = ""
    strMultiplayer = ""
    strTraining = ""
    strSettings = ""
    strQuit = ""
    
    multPlayerMenu = [
        (_("Face-Off"),     lambda: self.newLocalGame(players = 2,             maxplayers = 4)),
        (_("Pro Face-Off"), lambda: self.newLocalGame(players = 2, mode2p = 1, maxplayers = 4)),
        (_("Party Mode"),   lambda: self.newLocalGame(             mode2p = 2)),
        (_("FoFiX Co-Op"),  lambda: self.newLocalGame(players = 2, mode2p = 3, maxplayers = 4, allowMic = allowMic)),
        (_("RB Co-Op"),     lambda: self.newLocalGame(players = 2, mode2p = 4, maxplayers = 4, allowMic = allowMic)),
        (_("GH Co-Op"),     lambda: self.newLocalGame(players = 2, mode2p = 5, maxplayers = 4)),
        (_("GH Battle"),    lambda: self.newLocalGame(players = 2, mode2p = 6, allowDrum = False)), #akedrou- so you can block drums
      ]
        
    if not self.useSoloMenu:

      mainMenu = [
        (strCareer, lambda:   self.newLocalGame(mode1p = 2, allowMic = allowMic)),
        (strQuickplay, lambda:        self.newLocalGame(allowMic = allowMic)),
        ((strMultiplayer,"multiplayer"), multPlayerMenu),
        ((strTraining,"training"),    trainingMenu),
        ((strSettings,"settings"),  self.settingsMenu),
        (strQuit,        self.quit),
      ]
      
    else:

      soloMenu = [
        (_("Solo Tour"), lambda: self.newLocalGame(mode1p = 2, allowMic = allowMic)),
        (_("Quickplay"), lambda: self.newLocalGame(allowMic = allowMic)),
      ]

      mainMenu = [
        ((strSolo,"solo"), soloMenu),
        ((strMultiplayer,"multiplayer"), multPlayerMenu),
        ((strTraining,"training"),    trainingMenu),
        ((strSettings,"settings"),  self.settingsMenu),
        (strQuit,        self.quit),
      ]


    
    self.menu = Menu(self.engine, mainMenu, onClose = lambda: self.engine.view.popLayer(self), pos = (12,12), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

    engine.mainMenu = self    #Points engine.mainMenu to the one and only MainMenu object instance

    ## whether the main menu has come into view at least once
    self.shownOnce = False

  def settingsMenu(self):
    if self.engine.advSettings:
      self.settingsMenuObject = Settings.SettingsMenu(self.engine)
    else:
      self.settingsMenuObject = Settings.BasicSettingsMenu(self.engine)
    return self.settingsMenuObject

  def shown(self):
    self.engine.view.pushLayer(self.menu)
    shaders.checkIfEnabled()
    if not self.shownOnce:
      self.shownOnce = True
      if hasattr(sys, 'frozen'):
        # Check whether this is a release binary being run from an svn/git
        # working copy or whether this is an svn/git binary not being run
        # from an corresponding working copy.
        currentVcs, buildVcs = None, None
        if VFS.isdir('/gameroot/.git'):
          currentVcs = 'git'
        elif VFS.isdir('/gameroot/src/.svn'):
          currentVcs = 'Subversion'
        if 'git' in Version.version():
          buildVcs = 'git'
        elif 'svn' in Version.version():
          buildVcs = 'Subversion'
        if currentVcs != buildVcs:
          if buildVcs is None:
            msg = _('This binary release is being run from a %(currentVcs)s working copy. This is not the correct way to run FoFiX from %(currentVcs)s. Please see one of the following web pages to set your %(currentVcs)s working copy up correctly:') + \
                  '\n\nhttp://code.google.com/p/fofix/wiki/RunningUnderPython26' + \
                  '\nhttp://code.google.com/p/fofix/wiki/RequiredSourceModules'
          else:
            msg = _('This binary was built from a %(buildVcs)s working copy but is not running from one. The FoFiX Team will not provide any support whatsoever for this binary. Please see the following site for official binary releases:') + \
                  '\n\nhttp://code.google.com/p/fofix/'
          Dialogs.showMessage(self.engine, msg % {'buildVcs': buildVcs, 'currentVcs': currentVcs})

  def runMusic(self):
    if not self.song.isPlaying():   #re-randomize
      if self.files:
        i = random.randint(0,len(self.files)-1)
        filename = self.files[i]
        sound = os.path.join("themes",self.themename,"sounds",filename)
        self.menumusic = True
        self.engine.menuMusic = True
    
        self.song = Audio.Music(self.engine.resource.fileName(sound))
        self.song.setVolume(self.engine.config.get("audio", "menu_volume"))
        self.song.play(0)
      else:
        self.menumusic = False
        self.engine.menuMusic = False
  
  def setMenuVolume(self):
    if self.menumusic and self.song.isPlaying():
      self.song.setVolume(self.engine.config.get("audio", "menu_volume"))
  
  def cutMusic(self):
    if self.menumusic:
      if self.song and not self.engine.menuMusic:
        self.song.fadeout(1400)
  
  def hidden(self):
    self.engine.view.popLayer(self.menu)
    self.cutMusic()
    if self.nextLayer:
      self.engine.view.pushLayer(self.nextLayer())
      self.nextLayer = None
    else:
      self.engine.quit()

  def quit(self):
    self.engine.view.popLayer(self.menu)

  def catchErrors(function):
    def harness(self, *args, **kwargs):
      try:
        try:
          function(self, *args, **kwargs)
        except:
          import traceback
          Log.error("Traceback:" + traceback.format_exc() )
          traceback.print_exc()
          raise
      except KeyboardInterrupt:
        pass
      except ControlConfigError:
        Dialogs.showMessage(self.engine, _("Your controls are not properly set up for this mode. Please check your settings."))
      except Exception, e:
        if e:
          Dialogs.showMessage(self.engine, unicode(e))
    return harness

  def launchLayer(self, layerFunc):
    if not self.nextLayer:
      self.nextLayer = layerFunc
      self.engine.view.popAllLayers()
  #launchLayer = catchErrors(launchLayer)    #MFH - trying to catch errors

  def showTutorial(self):
    # evilynux - Make sure tutorial exists before launching
    #tutorialpath = self.engine.getPath(os.path.join("songs","tutorial"))
    tutorialpath = self.engine.tutorialFolder
    if not os.path.isdir(self.engine.resource.fileName(tutorialpath)):
      Log.debug("No folder found: %s" % tutorialpath)
      Dialogs.showMessage(self.engine, _("No tutorials found!"))
      return
    
    self.engine.startWorld(1, None, 0, 0, tutorial = True)

    self.launchLayer(lambda: Lobby(self.engine))
  showTutorial = catchErrors(showTutorial)

  #MFH: adding deprecated support for EOF's method of quickstarting a song to test it
  def newSinglePlayerGame(self):
    self.newLocalGame()   #just call start function with default settings  = 1p quickplay
  
  def newLocalGame(self, players=1, mode1p=0, mode2p=0, maxplayers = None, allowGuitar = True, allowDrum = True, allowMic = False): #mode1p=0(quickplay),1(practice),2(career) / mode2p=0(faceoff),1(profaceoff)
    self.engine.data.acceptSound.play()

    self.engine.startWorld(players, maxplayers, mode1p, mode2p, allowGuitar, allowDrum, allowMic)
    
    self.launchLayer(lambda: Lobby(self.engine))
  newLocalGame = catchErrors(newLocalGame)
  
  def restartGame(self):
    splash = Dialogs.showLoadingSplashScreen(self.engine, "")
    self.engine.view.pushLayer(Lobby(self.engine))
    Dialogs.hideLoadingSplashScreen(self.engine, splash)
  
  def showMessages(self):
    msg = self.engine.startupMessages.pop()
    self.showStartupMessages = False
    Dialogs.showMessage(self.engine, msg)

  def run(self, ticks):
    self.time += ticks / 50.0
    if self.showStartupMessages:
      self.showMessages()
    if len(self.engine.startupMessages) > 0:
      self.showStartupMessages = True
    
    if self.engine.cmdPlay == 1:
      self.engine.cmdPlay = 4
    elif self.engine.cmdPlay == 4: #this frame runs the engine an extra loop to allow the font to load...
      #evilynux - improve cmdline support
      self.engine.cmdPlay = 2
      players, mode1p, mode2p = self.engine.cmdMode
      self.newLocalGame(players = players, mode1p = mode1p, mode2p = mode2p)
    elif self.engine.cmdPlay == 3:
      self.quit()
    
    if (not self.engine.world) or (not self.engine.world.scene):  #MFH 
      self.runMusic()
    
    
  def render(self, visibility, topMost):
    self.engine.view.setViewport(1,0)
    self.visibility = visibility
    if self.rbmenu:
      v = 1.0 - ((1 - visibility) ** 2)
    else:
      v = 1
    if v == 1:
      self.engine.view.transitionTime = 1 

    if self.menu.active and not self.active:
      self.active = True
    
    t = self.time / 100
    w, h, = self.engine.view.geometry[2:4]
    r = .5
    
    if self.active:
      if self.engine.view.topLayer() is not None:
        if self.optionsBG != None:
          self.engine.drawImage(self.optionsBG, (self.opt_bkg_size[2],-self.opt_bkg_size[3]), (w*self.opt_bkg_size[0],h*self.opt_bkg_size[1]), stretched = 3)
          
        self.engine.drawImage(self.optionsPanel, (0.5,-0.5), (w/1.7, h/2))
      else:
        self.engine.drawImage(self.engine.data.loadingImage, (1.0,-1.0), (w/2, h/2), stretched = 3)

    if self.menu.active and self.engine.cmdPlay == 0:
      if self.background != None:
        #MFH - auto-scaling
        self.engine.drawImage(self.background, (1.0,-1.0), (w/2, h/2), stretched = 3)

      numOfChoices = len(self.menu.choices)
      for i in range(numOfChoices):
        #Item selected
        if self.menu.currentIndex == i:
          xpos = (.5,1)
        #Item unselected
        else:
          xpos = (0,.5)
        #which item?
        ypos = (1/float(numOfChoices) * i, 1/float(numOfChoices) * (i + 1)) 

        textcoord = (w*self.menux,h*self.menuy-(h*self.main_menu_vspacing)*i)
        sFactor = self.main_menu_scale
        wFactor = xpos[1] - xpos[0]
        hFactor = ypos[1] - ypos[0]
        self.engine.drawImage(self.BGText, 
                              scale = (wFactor*sFactor,-hFactor*sFactor), 
                              coord = textcoord,
                              rect  = (xpos[0],xpos[1],ypos[0],ypos[1]))

#racer: added version tag to main menu:
    if self.version != None:
          wfactor = self.version.widthf(pixelw = 640.000)
          self.engine.drawImage(self.version, (0.5,-0.5),(w*self.engine.theme.versiontagposX, h*self.engine.theme.versiontagposY)) #worldrave - Added theme settings to control X+Y positions of versiontag.



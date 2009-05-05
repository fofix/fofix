####################################################################
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

from OpenGL.GL import *
import math
from FakeNetworking import socket

from View import BackgroundLayer
from Menu import Menu
from Lobby import Lobby
from Svg import ImgDrawing
from Language import _
import Dialogs
import Config
import Audio
import Settings
import datetime
import sys
import Theme
import Player

#myfingershurt: needed for multi-OS file fetching
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
    Player.practiceMode      = False    

    #myfingershurt: removing neck menu requirement:
    #self.neckMenuEnabled = False
    
    #self.neckMenuEnabled = Config.get("game", "neck_select_enabled")

    self.gfxVersionTag = Config.get("game", "gfx_version_tag")

    #self.tut = Config.get("game", "tut")
    self.chosenNeck = Config.get("game", "default_neck")
    exists = 0
    #neck fallback to random if doesn't exist.
    try:
      # evilynux - first assume the chosenNeck contains the full filename
      engine.loadImgDrawing(self, "ok", os.path.join("necks",self.chosenNeck+".png"))
    except IOError:
      try:
        engine.loadImgDrawing(self, "ok", os.path.join("necks","Neck_"+self.chosenNeck+".png"))
      except IOError:
        pass
      else:
        exists = 1
    else:
      exists = 1
    #MFH - fallback logic now supports a couple valid default neck filenames
    #MFH - check for Neck_1
    if exists == 0:
      try:
        engine.loadImgDrawing(self, "ok", os.path.join("necks","Neck_1.png"))
      except IOError:
        pass
      else:
        Config.set("game", "default_neck", "1")
        Log.warn("Default chosen neck not valid; fallback Neck_1.png forced.")
        exists = 1
    #MFH - check for defaultneck
    if exists == 0:
      try:
        engine.loadImgDrawing(self, "ok", os.path.join("necks","defaultneck.png"))
      except IOError: #we don't really need to be accepting this except... ...yea, sorry.
        raise IOError, "Default chosen neck not valid; fallbacks Neck_1.png and defaultneck.png also not valid!"
      else:
        Log.warn("Default chosen neck not valid; fallback defaultneck.png forced.")
        Config.set("game", "default_neck", "defaultneck")
        exists = 1
    dPlayerConfig = None
    #Get theme
    self.theme = self.engine.data.theme
    self.themeCoOp = self.engine.data.themeCoOp
    self.themename = self.engine.data.themeLabel
    self.useSoloMenu = Theme.use_solo_submenu

    try:
      #blazingamer
      self.menux = Theme.menuX
      self.menuy = Theme.menuY
    except Exception, e:
      Log.warn("Unable to load Theme menuX / Y positions: %s" % e) 
      self.menux = None
      self.menuy = None

    self.rbmenu = Theme.menuRB
 
    #MFH
    self.main_menu_scale = Theme.main_menu_scaleVar
    self.main_menu_vspacing = Theme.main_menu_vspacingVar

    if self.main_menu_scale == None:
      self.main_menu_scale = .5
    if self.main_menu_vspacing == None:
      self.main_menu_vspacing = 0.09


    
    
  

    try:
      self.engine.loadImgDrawing(self, "background", os.path.join("themes",self.themename,"menu","mainbg.png"))
    except IOError:
      self.background = None
    self.engine.loadImgDrawing(self, "BGText", os.path.join("themes",self.themename,"menu","maintext.png"))
    try:
      self.engine.loadImgDrawing(self, "optionsBG", os.path.join("themes",self.themename,"menu","optionsbg.png"))
    except IOError:
      self.optionsBG = None
    self.engine.loadImgDrawing(self, "optionsPanel", os.path.join("themes",self.themename,"menu","optionspanel.png"))
      
    #racer: added version tag
    if self.gfxVersionTag or Theme.versiontag == True:
      try:
        self.engine.loadImgDrawing(self, "version", os.path.join("themes",self.themename,"menu","versiontag.png"))
      except IOError:
        try:
          self.engine.loadImgDrawing(self, "version", "versiontag.png")   #falls back on default versiontag.png in data\ folder
        except IOError:
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
      self.song.setVolume(self.engine.config.get("audio", "songvol"))
      self.song.play(0)  #no loop
    else:
      self.menumusic = False

   
 #####======= Racer: New Main Menu ======####


    self.opt_text_color = Theme.hexToColor(Theme.opt_text_colorVar)
    self.opt_selected_color = Theme.hexToColor(Theme.opt_selected_colorVar)

    if self.opt_text_color == None:
      self.opt_text_color = (1,1,1)
    if self.opt_selected_color == None:
      self.opt_selected_color = (1,0.75,0)


    newMultiplayerMenu = [
      (_("Host Multiplayer Game"), self.hostMultiplayerGame),
      (_("Join Multiplayer Game"), self.joinMultiplayerGame),
    ]
    
    editorMenu = Menu(self.engine, [
      (_("Edit Existing Song"),            self.startEditor),
      (_("Import New Song"),               self.startImporter),
      (_("Import GH(tm) Songs"),  self.startGHImporter),
    ])

    trainingMenu = [
      (_("Tutorials"), self.showTutorial),
      (_("Practice"), lambda: self.newLocalGame(mode1p = 1)),
    ]
    
    self.opt_bkg_size = [float(i) for i in Theme.opt_bkg_size]

    strCareer = ""
    strQuickplay = ""
    strSolo = ""
    strMultiplayer = ""
    strTraining = ""
    strSettings = ""
    strQuit = ""
    
    if self.theme == 1 and self.themeCoOp: #Worldrave - Put GH Co-op ahead of FoFix co-op for GH based theme's. Made more sense.
      multPlayerMenu = [
        (_("Face-Off"), lambda: self.newLocalGame(players = 2, maxplayers = -1)),
        (_("Pro Face-Off"), lambda: self.newLocalGame(players = 2, mode2p = 1, maxplayers = -1)),
        (_("GH Battle"), lambda: self.newLocalGame(players = 2, mode2p = 6, maxplayers = 3, allowDrum = False)), #akedrou- so you can block drums
        (_("Party Mode"), lambda: self.newLocalGame(mode2p = 2)),
        (_("Co-Op"), lambda: self.newLocalGame(players = 2, mode2p = 5)),
        (_("FoFiX Co-Op"), lambda: self.newLocalGame(players = 2, mode2p = 3)),   #Worldrave - Re-added this option for now.
      ]
    elif self.theme == 1 and not self.themeCoOp:
      multPlayerMenu = [
        (_("Face-Off"), lambda: self.newLocalGame(players = 2, maxplayers = -1)),
        (_("Pro Face-Off"), lambda: self.newLocalGame(players = 2, mode2p = 1, maxplayers = -1)),
        (_("Party Mode"), lambda: self.newLocalGame(mode2p = 2)),
      ]
    elif self.theme == 2:
      multPlayerMenu = [
        (_("FoFiX Co-Op"), lambda: self.newLocalGame(players = 2, mode2p = 3, maxplayers = 4)),
        (_("RB Co-Op"), lambda: self.newLocalGame(players = 2, mode2p = 4, maxplayers = 4, allowMic = True)),
        (_("GH Co-Op"), lambda: self.newLocalGame(players = 2, mode2p = 5, maxplayers = 4)),
        (_("Face-Off"), lambda: self.newLocalGame(players = 2, maxplayers = -1)),
        (_("Pro Face-Off"), lambda: self.newLocalGame(players = 2, mode2p = 1, maxplayers = -1)),
        (_("Party Mode"), lambda: self.newLocalGame(mode2p = 2)),
      ]
    else:
      multPlayerMenu = [
        (_("FoFiX Co-Op"), lambda: self.newLocalGame(players = 2, mode2p = 3)),
        (_("Face-Off"), lambda: self.newLocalGame(players = 2, maxplayers = -1)),
        (_("Pro Face-Off"), lambda: self.newLocalGame(players = 2, mode2p = 1, maxplayers = -1)),
        (_("Party Mode"), lambda: self.newLocalGame(mode2p = 2)),
      ]
    
    if self.useSoloMenu is None:
      if self.theme == 0 or self.theme == 1:    #GH themes = 6 main menu selections
        self.useSoloMenu = False
      else:    #RB themes = 5 main menu selections
        self.useSoloMenu = True
    
    if not self.useSoloMenu:

      mainMenu = [
        (strCareer, lambda:   self.newLocalGame(mode1p = 2)),
        (strQuickplay, lambda:        self.newLocalGame()),
        ((strMultiplayer,"multiplayer"), multPlayerMenu),
        ((strTraining,"training"),    trainingMenu),
        ((strSettings,"settings"),  self.settingsMenu),
        (strQuit,        self.quit),
      ]
      
    else:

      soloMenu = [
        (_("Solo Tour"), lambda: self.newLocalGame(mode1p = 2)),
        (_("Quickplay"), lambda: self.newLocalGame()),
      ]

      mainMenu = [
        #( ( _(strSolo), 1, (0,0) ), soloMenu),
        ((strSolo,"solo"), soloMenu),
        ((strMultiplayer,"multiplayer"), multPlayerMenu),
        ((strTraining,"training"),    trainingMenu),
        ((strSettings,"settings"),  self.settingsMenu),
        (strQuit,        self.quit),
      ]


    
    self.menu = Menu(self.engine, mainMenu, onClose = lambda: self.engine.view.popLayer(self), pos = (12,12), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

    engine.mainMenu = self    #Points engine.mainMenu to the one and only MainMenu object instance

  def settingsMenu(self):
    if self.engine.advSettings:
      self.settingsMenuObject = Settings.SettingsMenu(self.engine)
    else:
      self.settingsMenuObject = Settings.BasicSettingsMenu(self.engine)
    return self.settingsMenuObject

  def shown(self):
    self.engine.view.pushLayer(self.menu)
    self.engine.stopServer()
  
  def runMusic(self):
    if not self.song.isPlaying():   #re-randomize
      if self.files:
        i = random.randint(0,len(self.files)-1)
        filename = self.files[i]
        sound = os.path.join("themes",self.themename,"sounds",filename)
        self.menumusic = True
        self.engine.menuMusic = True
    
        #self.song = Audio.Sound(self.engine.resource.fileName(sound))
        self.song = Audio.Music(self.engine.resource.fileName(sound))
        self.song.setVolume(self.engine.config.get("audio", "songvol"))
        #self.song.play(-1)
        self.song.play(0)  #no loop
      else:
        self.menumusic = False
        self.engine.menuMusic = False
        
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
      except socket.error, e:
        Dialogs.showMessage(self.engine, unicode(e[1]))
      except KeyboardInterrupt:
        pass
      except Exception, e:
        #MFH - enhancing error trapping and locating logic
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

    if self.engine.isServerRunning():
      return

    players = Dialogs.activateControllers(self.engine, 1) #akedrou
    if players == 0:
      return
    
    Config.set("game","game_mode", 0)    #MFH - ensure tutorial can work with new logic that depends on this mode variable
    Config.set("game","multiplayer_mode", 0)    #MFH - ensure tutorial can work with new logic that depends on this mode variable
    Config.set("game", "players", 1)
    Config.set("game", "tut", True)
    
    #Config.set("game","game_mode", 1) #MFH - don't force practice mode.... this is problematic.

    self.engine.startServer()
    self.engine.resource.load(self, "session", lambda: self.engine.connect("127.0.0.1"), synch = True)

    if Dialogs.showLoadingScreen(self.engine, lambda: self.session and self.session.isConnected):
      self.launchLayer(lambda: Lobby(self.engine, self.session, singlePlayer = True))
  showTutorial = catchErrors(showTutorial)

  #MFH: adding deprecated support for EOF's method of quickstarting a song to test it
  def newSinglePlayerGame(self):
    self.newLocalGame()   #just call start function with default settings  = 1p quickplay
  
  def newLocalGame(self, players=1, mode1p=0, mode2p=0, maxplayers = None, allowGuitar = True, allowDrum = True, allowMic = False): #mode1p=0(quickplay),1(practice),2(career) / mode2p=0(faceoff),1(profaceoff)
    self.engine.data.acceptSound.play()
    players = Dialogs.activateControllers(self.engine, players, maxplayers, allowGuitar, allowDrum, allowMic) #akedrou
    if players == 0:
      return
    Config.set("game", "players", players)
    Config.set("game","game_mode", mode1p)
    Config.set("game","multiplayer_mode", mode2p)
    if Config.get("game", "tut") == True:
      Config.set("game", "tut", False)
      #Config.set("game", "selected_library", "")
      #Config.set("game", "selected_song", "")

    #MFH - testing new traceback logging:
    #raise TypeError

    if self.engine.isServerRunning():
      return
    self.engine.startServer()
    self.engine.resource.load(self, "session", lambda: self.engine.connect("127.0.0.1"), synch = True)
    
    if Dialogs.showLoadingScreen(self.engine, lambda: self.session and self.session.isConnected):
      self.launchLayer(lambda: Lobby(self.engine, self.session, singlePlayer = True))
  newLocalGame = catchErrors(newLocalGame)

  def hostMultiplayerGame(self):
    self.engine.startServer()
    self.engine.resource.load(self, "session", lambda: self.engine.connect("127.0.0.1"))

    if Dialogs.showLoadingScreen(self.engine, lambda: self.session and self.session.isConnected):
      self.launchLayer(lambda: Lobby(self.engine, self.session))
  hostMultiplayerGame = catchErrors(hostMultiplayerGame)

  def joinMultiplayerGame(self, address = None):
    if not address:
      address = Dialogs.getText(self.engine, _("Enter the server address:"), "127.0.0.1")

    if not address:
      return
    
    self.engine.resource.load(self, "session", lambda: self.engine.connect(address))

    if Dialogs.showLoadingScreen(self.engine, lambda: self.session and self.session.isConnected, text = _("Connecting...")):
      self.launchLayer(lambda: Lobby(self.engine, self.session))
  joinMultiplayerGame = catchErrors(joinMultiplayerGame)

  def startEditor(self):
    self.launchLayer(lambda: Editor(self.engine))
  startEditor = catchErrors(startEditor)

  def startImporter(self):
    self.launchLayer(lambda: Importer(self.engine))
  startImporter = catchErrors(startImporter)

  def startGHImporter(self):
    self.launchLayer(lambda: GHImporter(self.engine))
  startGHImporter = catchErrors(startGHImporter)
    
  def run(self, ticks):
    self.time += ticks / 50.0
    if self.engine.cmdPlay == 1:
      #evilynux - improve cmdline support
      self.newLocalGame(players = Config.get("game", "players"), mode1p = Config.get("game","game_mode"), mode2p = Config.get("game","multiplayer_mode"))
    elif self.engine.cmdPlay == 2:
      self.quit()
    
    
    if self.menumusic:  #MFH 
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

    if not self.useSoloMenu:


      if self.active:
        if self.engine.view.topLayer() is not None:
          if self.optionsBG != None:
            self.engine.drawImage(self.optionsBG, (self.opt_bkg_size[2],-self.opt_bkg_size[3]), (w*self.opt_bkg_size[0],h*self.opt_bkg_size[1]), stretched = 3)
          
          self.engine.drawImage(self.optionsPanel, (0.5,-0.5), (w/1.7, h/2))
        else:
          self.engine.drawImage(self.engine.data.loadingImage, (1.0,-1.0), (w/2, h/2), stretched = 3)

      if self.menu.active:
        if self.background != None:
          #MFH - auto-scaling
          self.engine.drawImage(self.background, (1.0,-1.0), (w/2, h/2), stretched = 3)

        for i in range(0,6):
          #Item selected
          if self.menu.currentIndex == i:
            xpos = (.5,1)
          #Item unselected
          else:
            xpos = (0,.5)
          #which item?
          ypos = 1/6.0*i


#============blazingamer============
#if menux and/or menuy are not set it will use the default positions for the main text
          if self.menux == None or self.menuy == None:
            if self.theme == 0:
              textcoord = (w*0.5,h*0.45-(h*self.main_menu_vspacing)*i)
            elif self.theme == 1:
              textcoord = (w*0.7,h*0.8-(h*self.main_menu_vspacing)*i)
#if menux and menuy are set it will use those
          else:
            try:
              textcoord = (w*self.menux,h*self.menuy-(h*self.main_menu_vspacing)*i)
            except Exception, e:
              Log.warn("Unable to translate BGText: %s" % e) 
        
#===================================     

          self.engine.drawImage(self.BGText, (.5*self.main_menu_scale,-1/6.0*self.main_menu_scale), textcoord,
                                rect = (xpos[0],xpos[1],ypos,ypos+1/6.0))

    else:

      if self.active:
        if self.engine.view.topLayer() is not None:
          if self.optionsBG != None:
            self.engine.drawImage(self.optionsBG, (self.opt_bkg_size[2],-self.opt_bkg_size[3]), (w*self.opt_bkg_size[0],h*self.opt_bkg_size[1]), stretched = 3)
        
          self.engine.drawImage(self.optionsPanel, (0.5,-0.5), (w*0.4, h/2))
        else:
          self.engine.drawImage(self.engine.data.loadingImage, scale = (1.0,-1.0), coord = (w/2,h/2), stretched = 3)
        
      if self.menu.active:
        if self.background != None:
          self.engine.drawImage(self.background, (1.0,-1.0), (w/2, h/2), stretched = 3)

        for i in range(0,5):
          #Item selected
          if self.menu.currentIndex == i:
            xpos = (.5,1)
          #Item unselected
          else:
            xpos = (0,.5)
          #which item?
          ypos = 1/5.0*i
          

#============blazingamer============
#if menux and/or menuy are not set it will use the default positions for the main text
          if self.menux == None or self.menuy == None:
            textcoord = (w*0.2,(h*0.8-(h*self.main_menu_vspacing)*i)*v)
#if menux and menuy are set it will use those
          else:
            try:
              textcoord = (w*self.menux,(h*self.menuy-(h*self.main_menu_vspacing)*i)*v)
            except Exception, e:
              Log.warn("Unable to translate BGText: %s" % e) 
        
#===================================

          self.engine.drawImage(self.BGText, (.5*self.main_menu_scale,(-1/5.0*self.main_menu_scale)),
                                textcoord, rect = (xpos[0],xpos[1],ypos,ypos+1/5.0))

#racer: added version tag to main menu:
    if self.version != None:
          wfactor = self.version.widthf(pixelw = 640.000)
          self.engine.drawImage(self.version, (0.5,-0.5),(w*Theme.versiontagposX, h*Theme.versiontagposY)) #worldrave - Added theme settings to control X+Y positions of versiontag.



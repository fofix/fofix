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

    Config.define("coffee",   "max_neck", int, 1)      

    for playerNum in range(0,2):    #MFH - verify chosen necks and, if necessary, force appropriate defaults / fallbacks
      neckSettingName = "neck_choose_p%d" % (playerNum)
      self.chosenNeck = Config.get("coffee", neckSettingName )
      #neck fallback to random if doesn't exist.
      try:
        # evilynux - first assume the chosenNeck contains the full filename
        engine.loadImgDrawing(self, "ok", os.path.join("necks",self.chosenNeck+".png"))
      except IOError:
        try:
          engine.loadImgDrawing(self, "ok", os.path.join("necks","Neck_"+self.chosenNeck+".png"))
        except IOError:
          exists = 0
        else:
          exists = 1
      else:
        exists = 1
      if exists == 0: #MFH - fallback logic now supports a couple valid default neck filenames
        #MFH - check for Neck_1
        try:
          engine.loadImgDrawing(self, "ok", os.path.join("necks","Neck_1.png"))
          exists = 1
        except IOError:
          exists = 0
        if exists == 1:
          Config.set("coffee", neckSettingName, "1")
          Log.warn("P%d Chosen neck not valid, fallback Neck_1.png forced." % (playerNum) )
        else:
          #MFH - check for defaultneck
          try:
            engine.loadImgDrawing(self, "ok", os.path.join("necks","defaultneck.png"))
            exists = 1
          except IOError:
            exists = 0
          if exists == 1:
            Log.warn("P%d Chosen neck not valid, fallback defaultneck.png forced." % (playerNum) )
            Config.set("coffee", neckSettingName, "defaultneck")
          else:
            Log.warn("P%d Warning!  Chosen neck not valid, fallbacks Neck_1.png and defaultneck.png also not valid!  Crash imminent!" % (playerNum) )

    #Get theme
    self.theme = self.engine.data.theme
    self.themeCoOp = self.engine.data.themeCoOp
    self.themename = self.engine.data.themeLabel

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
    
    self.opt_bkg_x = Theme.opt_bkg_xPos
    self.opt_bkg_y = Theme.opt_bkg_yPos

    if self.opt_bkg_x == None:
      self.opt_bkg_x = 0

    if self.opt_bkg_y == None:
      self.opt_bkg_y = 0


    strCareer = ""
    strQuickplay = ""
    strSolo = ""
    strMultiplayer = ""
    strTraining = ""
    strSettings = ""
    strQuit = ""


    if self.theme == 0 or self.theme == 1:    #GH themes = 6 main menu selections
    
      if self.theme == 1 and self.themeCoOp: #Worldrave - Put GH Co-op ahead of FoFix co-op for GH based theme's. Made more sense.
        multPlayerMenu = [
          (_("GH Co-Op"), lambda: self.newLocalGame(players = 2, mode2p = 5)),
          (_("FoFiX Co-Op"), lambda: self.newLocalGame(players = 2, mode2p = 3)),
          (_("Face-Off"), lambda: self.newLocalGame(players = 2)),
          (_("Pro Face-Off"), lambda: self.newLocalGame(players = 2, mode2p = 1)),
          (_("Party Mode"), lambda: self.newLocalGame(mode2p = 2)),
        ]
      elif self.theme == 1 and not self.themeCoOp:
        multPlayerMenu = [
          (_("Face-Off"), lambda: self.newLocalGame(players = 2)),
          (_("Pro Face-Off"), lambda: self.newLocalGame(players = 2, mode2p = 1)),
          (_("Party Mode"), lambda: self.newLocalGame(mode2p = 2)),
        ]
      else:
        multPlayerMenu = [
          (_("FoFiX Co-Op"), lambda: self.newLocalGame(players = 2, mode2p = 3)),
          (_("Face-Off"), lambda: self.newLocalGame(players = 2)),
          (_("Pro Face-Off"), lambda: self.newLocalGame(players = 2, mode2p = 1)),
          (_("Party Mode"), lambda: self.newLocalGame(mode2p = 2)),
        ]

      mainMenu = [
        (_(strCareer), lambda:   self.newLocalGame(mode1p = 2)),
        (_(strQuickplay), lambda:        self.newLocalGame()),
        ((_(strMultiplayer),"multiplayer"), multPlayerMenu),
        ((_(strTraining),"training"),    trainingMenu),
        ((_(strSettings),"settings"),  self.settingsMenu),
        (_(strQuit),        self.quit),
      ]


    elif self.theme == 2:    #RB themes = 5 main menu selections

      soloMenu = [
        (_("Solo Tour"), lambda: self.newLocalGame(mode1p = 2)),
        (_("Quickplay"), lambda: self.newLocalGame()),
      ]

      multPlayerMenu = [
        (_("FoFiX Co-Op"), lambda: self.newLocalGame(players = 2, mode2p = 3)),
        (_("RB Co-Op"), lambda: self.newLocalGame(players = 2, mode2p = 4)),
        (_("GH Co-Op"), lambda: self.newLocalGame(players = 2, mode2p = 5)),
        (_("Face-Off"), lambda: self.newLocalGame(players = 2)),
        (_("Pro Face-Off"), lambda: self.newLocalGame(players = 2, mode2p = 1)),
        (_("Party Mode"), lambda: self.newLocalGame(mode2p = 2)),
      ]

      mainMenu = [
        #( ( _(strSolo), 1, (0,0) ), soloMenu),
        ((_(strSolo),"solo"), soloMenu),
        ((_(strMultiplayer),"multiplayer"), multPlayerMenu),
        ((_(strTraining),"training"),    trainingMenu),
        ((_(strSettings),"settings"),  self.settingsMenu),
        (_(strQuit),        self.quit),
      ]


    
    self.menu = Menu(self.engine, mainMenu, onClose = lambda: self.engine.view.popLayer(self), pos = (12,12), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

    engine.mainMenu = self    #Points engine.mainMenu to the one and only MainMenu object instance

  def settingsMenu(self):
    if self.engine.advSettings:
      return Settings.SettingsMenu(self.engine)
    else:
      return Settings.BasicSettingsMenu(self.engine)

  def shown(self):
    self.engine.view.pushLayer(self.menu)
    self.engine.stopServer()
        
  def hidden(self):
    self.engine.view.popLayer(self.menu)
    if self.menumusic:
      if self.song:
        self.song.fadeout(1400)
    
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

    Config.set("player0","mode_1p", 0)    #MFH - ensure tutorial can work with new logic that depends on this mode variable
    Config.set("player0","mode_2p", 0)    #MFH - ensure tutorial can work with new logic that depends on this mode variable
    Config.set("game", "players", 1)
    Config.set("game", "tut", True)
    
    #Config.set("player0","mode_1p", 1) #MFH - don't force practice mode.... this is problematic.

    self.engine.startServer()
    self.engine.resource.load(self, "session", lambda: self.engine.connect("127.0.0.1"), synch = True)

    if Dialogs.showLoadingScreen(self.engine, lambda: self.session and self.session.isConnected):
      self.launchLayer(lambda: Lobby(self.engine, self.session, singlePlayer = True))
  showTutorial = catchErrors(showTutorial)

  #MFH: adding deprecated support for EOF's method of quickstarting a song to test it
  def newSinglePlayerGame(self):
    self.newLocalGame()   #just call start function with default settings  = 1p quickplay
  
  def newLocalGame(self, players=1, mode1p=0, mode2p=0): #mode1p=0(quickplay),1(practice),2(career) / mode2p=0(faceoff),1(profaceoff)
    Config.set("game", "players", players)
    Config.set("player0","mode_1p", mode1p)
    Config.set("player1","mode_2p", mode2p)
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
      self.newLocalGame(players = Config.get("game", "players"), mode1p = Config.get("player0","mode_1p"), mode2p = Config.get("player1","mode_2p"))
    elif self.engine.cmdPlay == 2:
      self.quit()
    
    
    if self.menumusic:  #MFH 
      if not self.song.isPlaying():   #re-randomize
        if self.files:
          i = random.randint(0,len(self.files)-1)
          filename = self.files[i]
          sound = os.path.join("themes",self.themename,"sounds",filename)
          self.menumusic = True
    
          #self.song = Audio.Sound(self.engine.resource.fileName(sound))
          self.song = Audio.Music(self.engine.resource.fileName(sound))
          self.song.setVolume(self.engine.config.get("audio", "songvol"))
          #self.song.play(-1)
          self.song.play(0)  #no loop
        else:
          self.menumusic = False
    
    
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

    if self.theme == 0 or self.theme == 1:


      if self.active:
        if self.optionsBG != None:
          wfactor = self.optionsBG.widthf(pixelw = 640.000)
          self.optionsBG.transform.reset()
          self.optionsBG.transform.translate(w/2+self.opt_bkg_x,h/2+self.opt_bkg_y)
          self.optionsBG.transform.scale(wfactor,-wfactor)
          self.optionsBG.draw()
        
        self.optionsPanel.transform.reset()
        self.optionsPanel.transform.scale(0.5,-0.5)
        self.optionsPanel.transform.translate(w/1.7, h/2)
        self.optionsPanel.draw()

      if self.menu.active:
        if self.background != None:
          #MFH - auto-scaling
          imgwidth = self.background.width1()
          wfactor = 640.000/imgwidth
          self.background.transform.reset()
          self.background.transform.translate(w/2,h/2)
          self.background.transform.scale(wfactor,-wfactor)
          self.background.draw()  
          #wfactor = self.background.widthf(pixelw = 640.000)
          #self.background.transform.reset()
          #self.background.transform.translate(w/2,h/2)
          #self.background.transform.scale(wfactor,-wfactor)
          #self.background.draw()

        for i in range(0,6):
          #Item selected
          if self.menu.currentIndex == i:
            xpos = (.5,1)
          #Item unselected
          else:
            xpos = (0,.5)
          #which item?
          ypos = 1/6.0*i
          self.BGText.transform.reset()
          #self.BGText.transform.scale(.5*.5,-1/6.0*.5)
          self.BGText.transform.scale(.5*self.main_menu_scale,-1/6.0*self.main_menu_scale)
          





#============blazingamer============
#if menux and/or menuy are not set it will use the default positions for the main text
          if self.menux == None or self.menuy == None:
            if self.theme == 0:
              self.BGText.transform.translate(w*0.5,h*0.45-(h*self.main_menu_vspacing)*i)
            elif self.theme == 1:
              self.BGText.transform.translate(w*0.7,h*0.8-(h*self.main_menu_vspacing)*i)
#if menux and menuy are set it will use those
          else:
            try:
              self.BGText.transform.translate(w*self.menux,h*self.menuy-(h*self.main_menu_vspacing)*i)
            except Exception, e:
              Log.warn("Unable to translate BGText: %s" % e) 
        
#===================================     
          self.BGText.draw(rect = (xpos[0],xpos[1],ypos,ypos+1/6.0))

    elif self.theme == 2:

  


      if self.active:
        if self.optionsBG != None:
          wfactor = self.optionsBG.widthf(pixelw = 640.000)
          self.optionsBG.transform.reset()
          self.optionsBG.transform.translate(w/2+self.opt_bkg_x,h/2+self.opt_bkg_y)
          self.optionsBG.transform.scale(wfactor,-wfactor)
          self.optionsBG.draw()
        
        self.optionsPanel.transform.reset()
        self.optionsPanel.transform.scale(0.5,-0.5)
        self.optionsPanel.transform.translate(w*0.4, h/2)
        self.optionsPanel.draw()
      if self.menu.active:
        if self.background != None:
          wfactor = self.background.widthf(pixelw = 640.000)
          self.background.transform.reset()
          self.background.transform.translate(w/2,h/2)
          self.background.transform.scale(wfactor,-wfactor)
          self.background.draw()

        for i in range(0,5):
          #Item selected
          if self.menu.currentIndex == i:
            xpos = (.5,1)
          #Item unselected
          else:
            xpos = (0,.5)
          #which item?
          ypos = 1/5.0*i
          self.BGText.transform.reset()
          #self.BGText.transform.scale(.5*.5,-1/5.0*.5)
          self.BGText.transform.scale(.5*self.main_menu_scale,(-1/5.0*self.main_menu_scale))
          

#============blazingamer============
#if menux and/or menuy are not set it will use the default positions for the main text
          if self.menux == None or self.menuy == None:
            self.BGText.transform.translate(w*0.2,(h*0.8-(h*self.main_menu_vspacing)*i)*v)
#if menux and menuy are set it will use those
          else:
            try:
              self.BGText.transform.translate(w*self.menux,(h*self.menuy-(h*self.main_menu_vspacing)*i)*v)
            except Exception, e:
              Log.warn("Unable to translate BGText: %s" % e) 
        
#===================================
          self.BGText.draw(rect = (xpos[0],xpos[1],ypos,ypos+1/5.0))

#racer: added version tag to main menu:
    if self.version != None:
          wfactor = self.version.widthf(pixelw = 640.000)
          self.version.transform.reset()
          self.version.transform.translate(w/2,h/2)
          self.version.transform.scale(wfactor,-wfactor)
          self.version.draw()



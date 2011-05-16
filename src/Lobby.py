#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X                                                   #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 rchiav                                         #
#               2009 Team FoFiX                                     #
#               2009 akedrou                                        #
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

from __future__ import with_statement

import pygame
from OpenGL.GL import *
import os
import shutil

from View import Layer
from Input import KeyListener
from Language import _
from Player import GUITARTYPES, DRUMTYPES, MICTYPES
import Dialogs
import Player
import Song

class WorldNotStarted(Exception):
  def __str__(self):
    return _("World error. Please try again.")

class Lobby(Layer, KeyListener):
  def __init__(self, engine):
    if not engine.world:
     raise WorldNotStarted
    self.engine         = engine
    self.minPlayers     = self.engine.world.minPlayers
    self.maxPlayers     = self.engine.world.maxPlayers
    self.time           = 0.0
    self.keyControl     = 0
    self.keyGrab        = False
    self.scrolling      = [0,0,0,0]
    self.rate           = [0,0,0,0]
    self.delay          = [0,0,0,0]
    self.scroller       = [0, self.scrollUp, self.scrollDown]
    self.gameStarted    = False
    self.showLobby      = True  #give the Lobby visibility if it does not have it.
    self.inputInit      = False #has Lobby initialized its inputs?
    self.blockedItems   = [1] #items that cannot be selected - start with the separator.
    self.selectedItems  = []  #items that have been selected - so as to prevent repeats.
    self.blockedPlayers = []  #players that cannot select (ie, are not in the game)
    self.selectedPlayers = [] #players that have selected
    self.playerList     = [None for i in range(4)]
    self.fullView     = self.engine.view.geometry[2:4]
    self.music        = True
    self.creator      = CreateCharacter(self.engine)
    
    self.abort = False #Quit the Lobby for the MainMenu.
    
    #key vars
    self.fontDict         = self.engine.data.fontDict
    self.geometry         = self.engine.view.geometry[2:4]
    self.fontScreenBottom = self.engine.data.fontScreenBottom
    self.aspectRatio      = self.engine.view.aspectRatio
    self.drawImage        = self.engine.drawImage
    self.drawStarScore    = self.engine.drawStarScore
    
    self.gameModeText = self.engine.world.gameName
    
    #controllers are initialized; set the keys that will trigger menu actions.
    self.yes        = []
    self.no         = []
    self.conf       = []
    self.up         = []
    self.down       = []
    self.controls   = [j for j in self.engine.input.controls.controls]
    self.types      = []
    self.allowed    = [True for i in range(4)]
    for i, type in enumerate(self.engine.input.controls.type):
      self.types.append(type)
      if type in GUITARTYPES:
        self.yes.extend([Player.CONTROLS[i][Player.KEY1], Player.CONTROLS[i][Player.KEY1A], Player.CONTROLS[i][Player.START]])
        self.no.extend([Player.CONTROLS[i][Player.KEY2], Player.CONTROLS[i][Player.KEY2A], Player.CONTROLS[i][Player.CANCEL]])
        self.conf.extend([Player.CONTROLS[i][Player.KEY3], Player.CONTROLS[i][Player.KEY3A]])
        self.up.extend([Player.CONTROLS[i][Player.ACTION1], Player.CONTROLS[i][Player.UP]])
        self.down.extend([Player.CONTROLS[i][Player.ACTION2], Player.CONTROLS[i][Player.DOWN]])
      elif type in DRUMTYPES:
        self.yes.extend([Player.CONTROLS[i][Player.DRUM5], Player.CONTROLS[i][Player.DRUM5A], Player.CONTROLS[i][Player.START]])
        self.no.extend([Player.CONTROLS[i][Player.DRUM1], Player.CONTROLS[i][Player.DRUM1A], Player.CONTROLS[i][Player.CANCEL]])
        self.conf.extend([Player.CONTROLS[i][Player.DRUMBASS], Player.CONTROLS[i][Player.DRUMBASSA]])
        self.up.extend([Player.CONTROLS[i][Player.DRUM2], Player.CONTROLS[i][Player.DRUM2A], Player.CONTROLS[i][Player.UP]])
        self.down.extend([Player.CONTROLS[i][Player.DRUM3], Player.CONTROLS[i][Player.DRUM3A], Player.CONTROLS[i][Player.DOWN]])
      elif type in MICTYPES:
        self.yes.extend([Player.CONTROLS[i][Player.START]])
        self.no.extend([Player.CONTROLS[i][Player.CANCEL]])
        self.up.extend([Player.CONTROLS[i][Player.UP]])
        self.down.extend([Player.CONTROLS[i][Player.DOWN]])
    
    for i, control in enumerate(self.engine.input.controls.controls):
      if control == "None":
        self.controls[i] = _("No Controller")
        self.blockedPlayers.append(i)
      elif self.allowed[i] == False:
        self.controls[i] = _("Disabled Controller")
        self.blockedPlayers.append(i)
      elif control == "defaultg":
        self.controls[i] = _("Default Guitar")
      elif control == "defaultd":
        self.controls[i] = _("Default Drums")
      elif control == "defaultm":
        self.controls[i] = _("Default Microphone")
    
    if 4 - len(self.blockedPlayers) < self.minPlayers:
      Dialogs.showMessage(self.engine, _("Your controls are not properly set up for this mode. Please check your settings."))
      self.abort = True
    self.engine.input.activeGameControls = [i for i in range(4) if i not in self.blockedPlayers]
    self.engine.input.pluginControls()
    self.panelOrder = range(4)
    self.oldOrder   = range(4)
    
    themename  = self.engine.data.themeLabel
    self.theme = self.engine.theme

    self.engine.data.loadAllImages(self, os.path.join("themes",themename,"lobby"))
    self.partImages     = self.engine.data.partImages
    
    if not self.img_default_av:
      self.engine.data.loadImgDrawing(self, "img_default_av", os.path.join("users", "players", "default.png"))
    if not self.img_newchar_av:
      self.engine.data.loadImgDrawing(self, "img_newchar_av", os.path.join("users", "players", "newchar_av.png"))
    
    if self.img_default_av:
      imgheight = self.img_default_av.height1()
      imgwidth  = self.img_default_av.width1()
      hFactor = self.theme.lobbyPanelAvatarDimension[1]/imgheight
      wFactor = self.theme.lobbyPanelAvatarDimension[0]/imgwidth
      self.defaultAvScale = min(hFactor, wFactor)
    if self.img_newchar_av:
      imgheight = self.img_newchar_av.height1()
      imgwidth  = self.img_newchar_av.width1()
      hFactor = self.theme.lobbyPanelAvatarDimension[1]/imgheight
      wFactor = self.theme.lobbyPanelAvatarDimension[0]/imgwidth
      self.newCharAvScale = min(hFactor, wFactor)
    
    self.tsChooseChar = _("Choose Your Character")
    self.tsPlayerStr  = _("Player %d")
    self.playerNum  = 0
    self.tsDrumFlip = (_("Regular Drums"), _("Flipped Drums"))
    self.tsAutoKick = (_("Pedal-Using"), _("Footless"))
    self.tsAssist   = (_("Assist Mode Off"), _("Easy Assist"), _("Medium Assist"))
    self.tsTwoChord = (_("Chordmaster"), _("Two Notes Max"))
    self.tsInfo     = _("Information:")
    self.tsList     = [("0","1"), self.tsDrumFlip, self.tsAutoKick, self.tsAssist, self.tsTwoChord]
    
    self.controlDict = Player.controlDict
    self.selected = [0,0,0,0]
    self.panelMode = [0,0,0,0] #panel mode: 0 = select; 1 = create/edit
    self.screenOptions = self.engine.theme.lobbySelectLength
    self.pos = [(0, self.screenOptions), (0, self.screenOptions), (0, self.screenOptions), (0, self.screenOptions)]
    self.getPlayers()
      
    
  def getPlayers(self):
    self.playerNames = Player.playername
    self.playerPrefs = Player.playerpref
    self.options = [_("Create New Player"), _("Saved Characters")]
    self.options.extend(self.playerNames)
    for i in range(4):
      if self.selected[i] >= len(self.options):
        self.selected[i] = len(self.options) - 1
    self.blockedItems = [1]
    for i in self.selectedItems:
      self.blockedItems.append(self.options.index(i))
    self.avatars = [None for i in self.options]
    self.avatarScale = [None for i in self.options]
    self.getStartingSelected()

  def getStartingSelected(self):
    for num in range(4):
      if self.creator.updatedName and self.creator.playerNum == num:
        default = self.creator.updatedName
        self.creator.updatedName = None
      default = self.engine.config.get("game","player%d" % num)
      if len(self.options) > 2:
        for i, option in enumerate(self.options):
          if i < 2: #Just in case someone names their character "Create New Character" or something...
            continue
          if option == default:
            self.selected[num] = i
            break
        else:
          self.selected[num] = 2
      else:
        self.selected[num] = 0
      if self.selected[num] > self.pos[num][1]:
        self.pos[num] = (self.selected[num]-self.screenOptions, self.selected[num])
      elif self.selected[num] < self.pos[num][0]:
        self.pos[num] = (self.selected[num], self.selected[num]+self.screenOptions)
      self.loadAvatar(num)
      if self.selected[num] in self.blockedItems:
        self.scrollDown(num)
  
  def loadAvatar(self, num):
    if self.avatars[self.selected[num]] is not None:
      return
    if self.selected[num] > 1:
      avatar = self.engine.loadImgDrawing(None, "avatar", os.path.join("users", "players", self.options[self.selected[num]] + ".png"))
      if not avatar:
        return
    else:
      self.avatars[self.selected[num]] = False
      return
    self.avatars[self.selected[num]] = avatar
    imgheight = avatar.height1()
    imgwidth  = avatar.width1()
    hFactor = 110.00/imgheight
    wFactor = 200.00/imgwidth
    self.avatarScale[self.selected[num]] = min(hFactor, wFactor)
    
  def shown(self):
    self.engine.input.addKeyListener(self)

  def hidden(self):
    self.engine.input.removeKeyListener(self)
    if not self.gameStarted:
      self.engine.view.pushLayer(self.engine.mainMenu)    #rchiav: use already-existing MainMenu instance

  def preparePlayers(self):
    c = []
    n = []
    for i, name in enumerate(self.playerList):
      if name is None:
        continue
      c.append(name[0])
      n.append(name[1])
      self.engine.config.set("game", "player%d" % i, name[1])
    self.engine.input.activeGameControls = c
    self.engine.input.pluginControls()
    for name in n: #this needs to be done after pluginControls so controller assignments are handled properly.
      self.engine.world.createPlayer(name)
  
  def handleGameStarted(self):
    self.gameStarted = True
    self.engine.gameStarted = True
    self.engine.view.popLayer(self)

  def scrollUp(self, num):
    self.engine.data.selectSound.play()
    self.selected[num] -= 1
    if self.selected[num] < 0:
      self.selected[num] = len(self.options) - 1
    while self.selected[num] in self.blockedItems:
      self.selected[num] -= 1
    self.loadAvatar(num)
    if self.selected[num] > self.pos[num][1]:
      self.pos[num] = (self.selected[num] - self.screenOptions, self.selected[num])
    elif self.selected[num] < self.pos[num][0]:
        self.pos[num] = (self.selected[num], self.selected[num]+self.screenOptions)
    
  def scrollDown(self, num):
    self.engine.data.selectSound.play()
    self.selected[num] += 1
    while self.selected[num] in self.blockedItems:
      self.selected[num] += 1
    if self.selected[num] >= len(self.options):
      self.selected[num] = 0
    self.loadAvatar(num)
    if self.selected[num] > self.pos[num][1]:
      self.pos[num] = (self.selected[num] - self.screenOptions, self.selected[num])
    elif self.selected[num] < self.pos[num][0]:
        self.pos[num] = (self.selected[num], self.selected[num]+self.screenOptions)
  
  def keyPressed(self, key, unicode):
    if not self.inputInit:
      return
    if self.gameStarted:
      return True
    c = self.engine.input.controls.getMapping(key)
    for i in range(4):
      if key in [pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_UP, pygame.K_DOWN, pygame.K_RIGHT, pygame.K_LEFT, pygame.K_SPACE]:
        continue
      if c and c in Player.playerkeys[i]:
        break
    else:
      i = self.keyControl
      # if self.keyGrab:
        # if key not in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_RETURN]:
          # return True
        # elif key == pygame.K_RETURN or key == pygame.K_ESCAPE:
          # key = pygame.K_SPACE
        # elif key == pygame.K_ESCAPE:
          # self.panelOrder = self.oldOrder
          # self.engine.input.activeGameControls = self.panelOrder
          # self.engine.input.pluginControls()
          # print "Panel order cancelled: %s" % str(self.panelOrder)
    if c in Player.cancels + self.no or key == pygame.K_ESCAPE:
      if self.playerList[i] is None and (key==pygame.K_ESCAPE or self.engine.input.p2Nav or i == 0):
        self.engine.data.cancelSound.play()
        self.engine.view.popLayer(self)
      elif self.playerList[i] is not None:
        self.engine.data.cancelSound.play()
        self.playerList[i] = None
        self.blockedItems.remove(self.selected[i])
        self.blockedPlayers.remove(i)
        self.selectedItems.remove(self.options[self.selected[i]])
        self.selectedPlayers.remove(i)
      return True
    elif c in self.yes or key == pygame.K_RETURN:
      if self.playerList[i] is not None:
        if len([1 for p in self.playerList if p]) >= self.minPlayers and (key==pygame.K_RETURN or self.engine.input.p2Nav or i == 0):
          self.gameStarted = True
          self.engine.menuMusic = False
          self.music = False
          self.engine.mainMenu.cutMusic()
          self.preparePlayers()
          if self.engine.world.tutorial:
            self.engine.world.startGame(libraryName = Song.DEFAULT_LIBRARY, songName = "tutorial")
            self.handleGameStarted()
          else:
            self.engine.world.startGame()
            self.handleGameStarted()
        return True
      self.engine.data.acceptSound.play()
      self.scrolling[i] = 0
      if self.selected[i] == 0:
        self.showLobby = False
        self.creator.loadPlayer(i)
        self.engine.view.pushLayer(self.creator)
      elif self.selected > 1:
        self.playerList[i] = (i, self.options[self.selected[i]])
        self.blockedPlayers.append(i)
        self.blockedItems.append(self.selected[i])
        self.blockedItems.sort()
        for p in range(4):
          if p == i:
            continue
          if self.selected[p] in self.blockedItems:
            self.scrollDown(p)
        self.selectedItems.append(self.options[self.selected[i]])
        self.selectedPlayers.append(i)
      return True
    elif key == pygame.K_SPACE: #todo (allow space to alter the panel order)
      pass
    elif key == pygame.K_LEFT:
      if self.keyGrab:
        a = self.panelOrder[self.keyControl]
      self.scrolling[self.keyControl] = 0
      self.keyControl -= 1
      if self.keyControl < 0:
        self.keyControl = 3
      if self.keyGrab:
        self.panelOrder.remove(a)
        self.panelOrder.insert(self.keyControl, a)
        self.engine.input.activeGameControls = self.panelOrder
        self.engine.input.pluginControls()
    elif key == pygame.K_RIGHT:
      if self.keyGrab:
        a = self.panelOrder[self.keyControl]
      self.scrolling[self.keyControl] = 0
      self.keyControl += 1
      if self.keyControl > 3:
        self.keyControl = 0
      if self.keyGrab:
        self.panelOrder.remove(a)
        self.panelOrder.insert(self.keyControl, a)
        self.engine.input.activeGameControls = self.panelOrder
        self.engine.input.pluginControls()
    elif self.playerList[i] is not None or len([1 for p in self.playerList if p]) >= self.maxPlayers:
      return True
    elif i in self.blockedPlayers:
      return True
    elif (c in self.conf or key in [pygame.K_LCTRL, pygame.K_RCTRL]):
      self.engine.data.acceptSound.play()
      self.creator.loadPlayer(i, self.options[self.selected[i]])
      self.showLobby = False
      self.engine.view.pushLayer(self.creator)
      return True
    elif c in self.up + [Player.playerkeys[self.playerNum][Player.UP]] or key == pygame.K_UP:
      self.scrolling[i] = 1
      self.scrollUp(i)
      self.delay[i] = self.engine.scrollDelay
    elif c in self.down + [Player.playerkeys[self.playerNum][Player.DOWN]] or key == pygame.K_DOWN:
      self.scrolling[i] = 2
      self.scrollDown(i)
      self.delay[i] = self.engine.scrollDelay
    if self.selected[i] > self.pos[i][1]:
      self.pos[i] = (self.selected[i] - self.screenOptions, self.selected[i])
    elif self.selected[i] < self.pos[i][0]:
      self.pos[i] = (self.selected[i], self.selected[i]+self.screenOptions)
    return True

  def keyReleased(self, key):
    if self.gameStarted:
      return True
    c = self.engine.input.controls.getMapping(key)
    for i in range(4):
      if key in [pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_UP, pygame.K_DOWN, pygame.K_RIGHT, pygame.K_LEFT]:
        continue
      if c and c in Player.playerkeys[i]:
        break
    else:
      i = self.keyControl
    self.scrolling[i] = 0

  def run(self, ticks):
    self.time += ticks / 50.0
    if self.abort:
      self.engine.view.popLayer(self)
    for i in range(4):
      if self.scrolling[i] > 0:
        self.delay[i] -= ticks
        self.rate[i] += ticks
        if self.delay[i] <= 0 and self.rate[i] >= self.engine.scrollRate:
          self.rate[i] = 0
          self.scroller[self.scrolling[i]](i)
    if self.music:
      self.engine.mainMenu.runMusic()
    self.engine.theme.themeLobby.run(ticks, self)
  
  def render(self, visibility, topMost):
    if not visibility:
      self.inputInit = False
      return
    if not self.inputInit:
      self.getPlayers()
    self.inputInit = True
    self.showLobby = True
    if self.playerNum >= self.maxPlayers:
      return
    with self.engine.view.orthogonalProjection(normalize = True):
      try:
        font = self.engine.data.fontDict[self.engine.theme.lobbySelectFont]
        titleFont = self.engine.data.fontDict[self.engine.theme.lobbyTitleFont]
      except KeyError:
        font = self.engine.data.font
        titleFont = self.engine.data.loadingFont
      v = ((1 - visibility) **2)
      w, h = self.fullView
      if self.img_background:
        self.engine.drawImage(self.img_background, scale = (1.0, -1.0), coord = (w/2,h/2), stretched = 3)
      self.engine.theme.themeLobby.renderPanels(self)

class CreateCharacter(Layer, KeyListener):
  def __init__(self, engine):
    self.engine    = engine
    self.time      = 0.0
    self.blink     = 0
    self.cursor    = ""
    self.name      = ""
    self.active    = False
    self.oldValue  = None
    self.oldName   = None
    self.selected  = 0
    self.scrolling = 0
    self.scrollRate  = self.engine.scrollRate
    self.scrollDelay = self.engine.scrollDelay
    self.delay       = 0
    self.rate        = 0
    sfxVolume = self.engine.config.get("audio", "SFX_volume")
    self.engine.data.selectSound.setVolume(sfxVolume)
    self.engine.data.acceptSound.setVolume(sfxVolume)  #MFH
    self.engine.data.cancelSound.setVolume(sfxVolume)  #MFH
    self.fullView  = self.engine.view.geometry[2:4]
    self.invalidNames = []
    for i in Player.playername:
      self.invalidNames.append(i.lower())
    self.newChar   = True
    self.choices   = []
    self.avatar    = None
    self.player    = None
    self.playerNum = 0
    self.neck      = None
    self.updatedName = None
    self.loadPlayer(0)
    self.dictEnDisable = {0: _("Disabled"), 1: _("Enabled")}
    self.lefty     = {0: 1, 1: -1}
    neckDict       = {0: _("Default Neck"), 1: _("Theme Neck"), 2: _("Select a Neck")}
    self.values    = (self.dictEnDisable, self.dictEnDisable, self.dictEnDisable, {0: _("Disabled"), 1: _("Easy Assist"), 2: _("Medium Assist")}, self.dictEnDisable, neckDict)
    self.options   = [(_("Name"),             _("Name your character!")), \
                      (_("Lefty Mode"),       _("Flip the guitar frets for left-handed playing!")), \
                      (_("Drum Flip"),        _("Flip the drum sounds - snare becomes crash, and so on")), \
                      (_("Auto-Kick Bass"),   _("Feet uncooperative? Broke your pedal? Not to worry!")), \
                      (_("Assist Mode"),      _("Play hard and expert, even when you're not that good!")), \
                      (_("Two-Chord Max"),    _("For those still playing with uncooperative keyboards.")), \
                      (_("Neck"),             _("Give the endless procession of notes a bit of flair!")), \
                      (_("Upload Name"),      _("To the internet, you are GUITARGOD23047124!")), \
                      (_("Choose Avatar"),    _("A 256x256 window into your soul.")), \
                      (_("Delete Character"), _("Quitter.")), \
                      (_("Done"),             _("All finished? Let's do this thing!"))]
    themename = self.engine.data.themeLabel
    self.engine.data.loadAllImages(self, os.path.join("themes",themename,"lobby","creator"))

  def loadPlayer(self, playerNum, player = None):
    self.choices = []
    self.playerNum = playerNum
    if player is not None:
      try:
        #stump: Temporary use of private stuff in Player until the SQLite-vs.-inis issue for players is decided.
        pref = Player._playerDB.execute('SELECT * FROM `players` WHERE `name` = ?', [player]).fetchone()
        pref = [pref[0], pref[1], pref[2], pref[3], pref[4], pref[5], pref[6], pref[10]]
        self.neck = pref[7]
        self.newChar = False
        self.player = player
        self.oldName = pref[0]
      except: #not found
        pref = ['', 0, 0, 0, 0, 0, 0, '']
        self.neck = ''
        self.newChar = True
        self.player = None
    else:
      pref = ['', 0, 0, 0, 0, 0, 0, '']
      self.neck = ''
      self.newChar = True
      self.player = None
    for i in pref:
      self.choices.append(i)
    self.choices.extend(["", "", ""])
  def deleteCharacter(self):
    tsYes = _("Yes")
    q = Dialogs.chooseItem(self.engine, [tsYes, _("No")], _("Are you sure you want to delete this player?"))
    if q == tsYes:
      if self.player:
        Player.deletePlayer(self.player)
      self.engine.view.popLayer(self)
      self.engine.input.removeKeyListener(self)
  def saveCharacter(self):
    pref = self.choices[0:8]
    pref.insert(7, self.neck)
    if len(self.choices[0]) > 0:
      if self.choices[0].lower() == "default":
        Dialogs.showMessage(self.engine, _("That is a terrible name. Choose something not 'default'"))
      elif self.choices[0].lower() not in self.invalidNames or self.choices[0] == self.player:
        Player.updatePlayer(self.player, pref)
        self.updatedName  = self.choices[0]
        if self.avatar is not None:
          shutil.copy(self.engine.resource.fileName(self.avatar),os.path.join(self.engine.data.path,"users","players",self.choices[0]+".png"))
        if self.oldName:
          if os.path.exists(self.engine.resource.fileName(os.path.join("users","players",self.oldName+".png"))) and self.oldName != self.choices[0]:
            if self.avatar is None:
              os.rename(self.engine.resource.fileName(os.path.join("users","players",self.oldName+".png")), os.path.join(self.engine.data.path,"users","players",self.choices[0]+".png"))
            else:
              os.remove(self.engine.resource.fileName(os.path.join("users","players",self.oldName+".png")))
        self.engine.view.popLayer(self)
        self.engine.input.removeKeyListener(self)
      else:
        Dialogs.showMessage(self.engine, _("That name already exists!"))
    else:
      Dialogs.showMessage(self.engine, _("Please enter a name!"))
  def shown(self):
    self.engine.input.addKeyListener(self)
  def hidden(self):
    self.engine.input.removeKeyListener(self)
  def keyPressed(self, key, unicode):
    c = self.engine.input.controls.getMapping(key)
    if key == pygame.K_BACKSPACE and self.active:
      self.choices[self.selected] = self.choices[self.selected][:-1]
    elif unicode and ord(unicode) > 31 and self.active:
      if self.selected == 0 or self.selected == 7:
        if self.selected == 0 and (ord(unicode) in (34, 42, 47, 58, 60, 62, 63, 92, 124) or ord(unicode) > 126): #ascii only
          self.engine.data.cancelSound.play()
          return True
        if len(self.choices[self.selected]) > 24:
          self.choices[self.selected] = self.choices[self.selected][:-1]
        self.choices[self.selected] += unicode
        return
    if c and not (c in Player.playerkeys[self.playerNum]):
      if key not in [pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_DOWN, pygame.K_UP, pygame.K_LEFT, pygame.K_RIGHT]:
        return
    if c in Player.key1s or key == pygame.K_RETURN:
      self.scrolling = 0
      self.engine.data.acceptSound.play()
      if self.selected in (0, 7):
        if self.active:
          self.active = False
        else:
          self.blink  = 0
          self.active = True
          self.oldValue = self.choices[self.selected]
      elif self.selected == 6:
        if self.choices[6] == 2:
          self.engine.view.pushLayer(Dialogs.NeckChooser(self.engine, player = self.player, owner = self))
          self.keyActive = False
      elif self.selected == 8:
        self.avatar = Dialogs.chooseAvatar(self.engine)
      elif self.selected == 9:
        self.deleteCharacter()
      elif self.selected == 10:
        self.saveCharacter()
    elif c in Player.key2s + Player.cancels or key == pygame.K_ESCAPE:
      self.engine.data.cancelSound.play()
      if not self.active:
        if self.player:
          self.updatedName  = self.oldName
        self.engine.view.popLayer(self)
        self.engine.input.removeKeyListener(self)
      else:
        self.choices[self.selected] = self.oldValue
        self.active = False
    elif (c in Player.action1s + Player.ups or key == pygame.K_UP):
      self.scrolling = 1
      self.delay = self.scrollDelay
      self.scrollUp()
    elif (c in Player.action2s + Player.downs or key == pygame.K_DOWN):
      self.scrolling = 2
      self.delay = self.scrollDelay
      self.scrollDown()
    elif (c in Player.key3s + Player.rights or key == pygame.K_RIGHT) and self.active:
      if len(self.choices[self.selected]) > 0:
        self.choices[self.selected] += self.choices[self.selected][len(self.choices[self.selected]) - 1]
        if c in Player.key3s:
          self.engine.data.acceptSound.play()
    elif (c in Player.key4s + Player.lefts or key == pygame.K_LEFT) and self.active:
      self.choices[self.selected] = self.choices[self.selected][:-1]
      if c in Player.key4s:
        self.engine.data.cancelSound.play()
    elif c in Player.rights or key == pygame.K_RIGHT:
      if self.selected in (0, 7, 8, 9, 10):
        pass
      elif self.selected in [4, 6]:
        self.choices[self.selected]+=1
        if self.choices[self.selected] > 2:
          self.choices[self.selected] = 0
      else:
        self.choices[self.selected] = 1 and (self.choices[self.selected] == 0) or 0
    elif c in Player.lefts or key == pygame.K_LEFT:
      if self.selected in (0, 7, 8, 9, 10):
        pass
      elif self.selected in [4, 6]:
        self.choices[self.selected]-=1
        if self.choices[self.selected] < 0:
          self.choices[self.selected] = 2
      else:
        self.choices[self.selected] = 1 and (self.choices[self.selected] == 0) or 0
  def scrollUp(self):
    if self.active:
      if len(self.choices[self.selected]) == 0:
        self.choices[self.selected] = "A"
        return True
      letter = self.choices[self.selected][len(self.choices[self.selected])-1]
      letterNum = ord(letter)
      if letterNum == ord('A'):
        letterNum = ord(' ')
      elif letterNum == ord(' '):
        letterNum = ord('_')
      elif letterNum == ord('_'):
        letterNum = ord('-')
      elif letterNum == ord('-'):
        letterNum = ord('9')
      elif letterNum == ord('0'):
        letterNum = ord('z')
      elif letterNum == ord('a'):
        letterNum = ord('Z')        
      else:
        letterNum -= 1
      self.choices[self.selected] = self.choices[self.selected][:-1] + chr(letterNum)
      self.engine.data.selectSound.play()
    else:
      self.engine.data.selectSound.play()
      self.selected -= 1
      if self.selected < 0:
        self.selected = len(self.options) - 1
  def scrollDown(self):
    if self.active:
      if len(self.choices[self.selected]) == 0:
        self.choices[self.selected] = "A"
        return True
      letter = self.choices[self.selected][len(self.choices[self.selected])-1]
      letterNum = ord(letter)
      if letterNum == ord('Z'):
        letterNum = ord('a')
      elif letterNum == ord('z'):
        letterNum = ord('0')
      elif letterNum == ord('9'):
        letterNum = ord('-')
      elif letterNum == ord('-'):
        letterNum = ord('_')
      elif letterNum == ord('_'):
        letterNum = ord(' ')
      elif letterNum == ord(' '):
        letterNum = ord('A')
      else:
        letterNum += 1
      self.choices[self.selected] = self.choices[self.selected][:-1] + chr(letterNum)
      self.engine.data.selectSound.play()
    else:
      self.engine.data.selectSound.play()
      self.selected += 1
      if self.selected >= len(self.options):
        self.selected = 0
  def keyReleased(self, key):
    self.scrolling = 0
  def run(self, ticks):
    self.time += ticks/50.0
    if self.scrolling > 0:
      self.delay -= ticks
      self.rate += ticks
    self.blink = self.time%20
    if self.active and self.blink > 10:
      self.cursor = "|"
    else:
      self.cursor = ""
    if self.scrolling == 1 and self.delay <= 0 and self.rate >= self.scrollRate:
      self.rate = 0
      self.scrollUp()
    elif self.scrolling == 2 and self.delay <= 0 and self.rate >= self.scrollRate:
      self.rate = 0
      self.scrollDown()
  def render(self, visibility, topMost):
    try:
      font = self.engine.data.fontDict[self.engine.theme.characterCreateOptionFont]
      helpFont = self.engine.data.fontDict[self.engine.theme.characterCreateHelpFont]
    except KeyError:
      font = self.engine.data.font
      helpFont = self.engine.data.loadingFont
    with self.engine.view.orthogonalProjection(normalize = True):
      v = ((1 - visibility) **2)
      w, h = self.fullView
      if self.img_creator:
        self.engine.drawImage(self.img_creator, scale = (1.0, -1.0), coord = (w/2,h/2), stretched = 3)
      helpFont.render(_("Player %d") % (self.playerNum + 1), pos = (.5, .1), scale = self.engine.theme.characterCreateScale, align = 1)
      for i, option in enumerate(self.options):
        r, g, b = self.engine.theme.characterCreateHelpColor
        glColor3f(r, g, b)
        cursor = ""
        if self.selected == i:
          wText, hText = helpFont.getStringSize(option[1], scale = self.engine.theme.characterCreateScale)
          helpFont.render(option[1], (self.engine.theme.characterCreateHelpX-(wText/2), self.engine.theme.characterCreateHelpY-hText), scale = self.engine.theme.characterCreateHelpScale)
          r, g, b = self.engine.theme.characterCreateSelectColor
          glColor3f(r, g, b)
          cursor = self.cursor
        else:
          r, g, b = self.engine.theme.characterCreateFontColor
          glColor3f(r, g, b)
        wText, hText = font.getStringSize(option[0], scale = self.engine.theme.characterCreateScale)
        font.render(option[0], (self.engine.theme.characterCreateX, self.engine.theme.characterCreateY+self.engine.theme.characterCreateSpace*i), scale = self.engine.theme.characterCreateScale)
        if self.active and self.selected == i:
          self.engine.theme.setSelectedColor(1-v)
        if i == 0 or i > 6:
          wText, hText = font.getStringSize(self.choices[i], scale = self.engine.theme.characterCreateScale)
          font.render(self.choices[i]+cursor, (self.engine.theme.characterCreateOptionX-wText, self.engine.theme.characterCreateY+self.engine.theme.characterCreateSpace*i), scale = self.engine.theme.characterCreateScale)
        else:
          if i == self.selected:
            str = "< %s >" % self.values[i-1][self.choices[i]]
          else:
            str = self.values[i-1][self.choices[i]]
          wText, hText = font.getStringSize(str, scale = self.engine.theme.characterCreateScale)
          font.render(str, (self.engine.theme.characterCreateOptionX-wText, self.engine.theme.characterCreateY+self.engine.theme.characterCreateSpace*i), scale = self.engine.theme.characterCreateScale)
      if self.img_creator_top:
         self.engine.drawImage(self.img_creator_top, scale = (1.0, -1.0), coord = (w/2,h/2), stretched = 3)

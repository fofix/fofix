#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 rchiav                                         #
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

import pygame
from OpenGL.GL import *
import math
import colorsys
import os

from View import Layer
from Input import KeyListener
from GameTask import GameTask
from Session import MessageHandler
from Language import _
import Dialogs
import Player
import Menu
import Song
import Theme
import Config

class Lobby(Layer, KeyListener, MessageHandler):
  def __init__(self, engine, session, singlePlayer = False, tutorial = False):
    self.engine       = engine
    self.session      = session
    self.isRunning    = False
    self.time         = 0.0
    self.scrolling    = 0
    self.rate         = 0
    self.delay        = 0
    self.scroller     = [0, self.scrollUp, self.scrollDown]
    self.gameStarted  = False
    self.done         = True
    self.active       = False
    self.neckB        = 5.0/6.0
    self.neckT        = 1
    self.blockedItems  = [1]
    self.selectedItems = []
    self.singlePlayer = singlePlayer
    self.tutorial     = tutorial
    self.players      = Config.get("game", "players")
    self.mode1p       = Config.get("game","game_mode")
    self.mode2p       = Config.get("game","multiplayer_mode")
    self.lobbyMode    = Theme.lobbyMode
    sfxVolume = self.engine.config.get("audio", "SFX_volume")
    self.engine.data.selectSound.setVolume(sfxVolume)
    self.engine.data.acceptSound.setVolume(sfxVolume)  #MFH
    self.engine.data.cancelSound.setVolume(sfxVolume)  #MFH
    self.fullView     = self.engine.view.geometry[2:4]
    self.session.broker.addMessageHandler(self)
    self.music        = True
    self.creator      = CreateCharacter(self.engine)
    
    if self.singlePlayer:
      themename  = self.engine.data.themeLabel
      self.theme = self.engine.data.theme
      try:
        self.engine.loadImgDrawing(self, "background", os.path.join("themes", themename, "lobby", "lobby.png"))
      except IOError:
        self.engine.loadImgDrawing(self, "background", os.path.join("themes", themename, "menu", "optionsbg.png"))
      
      try:
        self.engine.loadImgDrawing(self, "itemSelect", os.path.join("themes", themename, "lobby", "select.png"))
      except IOError:
        self.itemSelect = None
      
      try:
        self.engine.loadImgDrawing(self, "infoImg", os.path.join("themes", themename, "lobby", "information.png"))
      except IOError:
        self.infoImg = None
      
      try:
        self.engine.loadImgDrawing(self, "chooseCharImg", os.path.join("themes", themename, "lobby", "choosechar.png"))
      except IOError:
        self.chooseCharImg = None
      
      self.engine.loadImgDrawing(self, "defaultAvatar", os.path.join("users", "players", "default.png"))
      self.engine.loadImgDrawing(self, "defaultNeck",   os.path.join("necks", self.engine.mainMenu.chosenNeck + ".png"))
      self.engine.loadImgDrawing(self, "randomNeck",    os.path.join("necks", "randomneck.png"))
      self.engine.loadImgDrawing(self, "buttons", os.path.join("themes", themename, "notes.png"))
      
      imgheight = self.buttons.height1()
      imgwidth  = self.buttons.width1()
      hFactor = (70.00/imgheight)*6
      wFactor = 200.00/imgwidth
      self.buttonScale = min(hFactor, wFactor)
      imgheight = self.defaultAvatar.height1()
      imgwidth  = self.defaultAvatar.width1()
      hFactor = 110.00/imgheight
      wFactor = 200.00/imgwidth
      self.defAvScale = min(hFactor, wFactor)
      imgheight = self.defaultNeck.height1()
      imgwidth  = self.defaultNeck.width1()
      hFactor = (68.00/imgheight)*6
      wFactor = 200.00/imgwidth
      self.defNeckScale = min(hFactor, wFactor)
      imgheight = self.randomNeck.height1()
      imgwidth  = self.randomNeck.width1()
      hFactor = (68.00/imgheight)*6
      wFactor = 200.00/imgwidth
      self.randNeckScale = min(hFactor, wFactor)
      
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
      self.selected = 0
      self.getPlayers()
      default = self.engine.config.get("game","player0")
      self.screenOptions = Theme.lobbySelectLength
      self.pos = (0, self.screenOptions)
      self.getStartingSelected(default)
      
    
  def getPlayers(self):
    self.playerNames = Player.playername
    self.playerPrefs = Player.playerpref
    self.options = [_("Create New Player"), _("Saved Characters")]
    self.options.extend(self.playerNames)
    if self.selected >= len(self.options):
      self.selected = len(self.options) - 1
    self.blockedItems = [1]
    for i in self.selectedItems:
      self.blockedItems.append(self.options.index(i))
    self.avatars = [None for i in self.options]
    self.avatarScale = [None for i in self.options]
    self.necks   = [None for i in self.options]
    self.neckScale = [None for i in self.options]

  def getStartingSelected(self, default):
    if self.engine.input.controls.type[self.engine.input.activeGameControls[self.playerNum]] > 1:
      self.yes  = [Player.playerkeys[self.playerNum][Player.DRUM5], Player.playerkeys[self.playerNum][Player.DRUM5A]]
      self.no   = [Player.playerkeys[self.playerNum][Player.DRUM1], Player.playerkeys[self.playerNum][Player.DRUM1A]]
      self.up   = [Player.playerkeys[self.playerNum][Player.DRUM2], Player.playerkeys[self.playerNum][Player.DRUM2A]]
      self.down = [Player.playerkeys[self.playerNum][Player.DRUM3], Player.playerkeys[self.playerNum][Player.DRUM3A]]
      self.conf = [Player.playerkeys[self.playerNum][Player.DRUMBASS], Player.playerkeys[self.playerNum][Player.DRUMBASSA], Player.playerkeys[self.playerNum][Player.START]]
    else:
      self.yes  = [Player.playerkeys[self.playerNum][Player.KEY1], Player.playerkeys[self.playerNum][Player.KEY1A]]
      self.no   = [Player.playerkeys[self.playerNum][Player.KEY2], Player.playerkeys[self.playerNum][Player.KEY2A]]
      self.up   = [Player.playerkeys[self.playerNum][Player.ACTION1]]
      self.down = [Player.playerkeys[self.playerNum][Player.ACTION2]]
      self.conf = [Player.playerkeys[self.playerNum][Player.KEY3], Player.playerkeys[self.playerNum][Player.KEY3A], Player.playerkeys[self.playerNum][Player.START]]
    if len(self.options) > 2:
      for i, option in enumerate(self.options):
        if i < 2: #Just in case someone names their character "Create New Character" or something...
          continue
        if option == default:
          self.selected = i
          break
      else:
        self.selected = 2
    else:
      self.selected = 0
    if self.selected > self.pos[1]:
      self.pos = (self.selected-self.screenOptions, self.selected)
    elif self.selected < self.pos[0]:
      self.pos = (self.selected, self.selected+self.screenOptions)
    self.loadAvatar()
    self.loadNeck()
    if self.selected in self.blockedItems:
      self.scrollDown()
  
  def loadAvatar(self):
    if self.avatars[self.selected] is not None:
      return
    if self.selected > 1:
      try:
        self.engine.loadImgDrawing(self, "avatar", os.path.join("users", "players", self.options[self.selected] + ".png"))
      except IOError:
        self.avatars[self.selected] = "Empty"
        return
    else:
      self.avatars[self.selected] = "Empty"
      return
    self.avatars[self.selected] = self.avatar
    imgheight = self.avatar.height1()
    imgwidth  = self.avatar.width1()
    hFactor = 110.00/imgheight
    wFactor = 200.00/imgwidth
    self.avatarScale[self.selected] = min(hFactor, wFactor)
    self.avatar = None
    
  def loadNeck(self):
    if self.necks[self.selected] is not None:
      return
    if self.selected > 1:
      chosenNeck = Player.playerpref[self.selected-2][5]
      if chosenNeck == "randomneck" or chosenNeck == "0" or chosenNeck.lower() == "neck_0":
        self.necks[self.selected] = "random"
        return
      elif chosenNeck == "" or chosenNeck.lower() == "default":
        self.necks[self.selected] = "Default"
        return
      try:
        self.engine.loadImgDrawing(self, "neck", os.path.join("necks",str(chosenNeck+".png")))
      except IOError:
        self.necks[self.selected] = "Default"
        return
    else:
      self.necks[self.selected] = "Default"
      return
    self.necks[self.selected] = self.neck
    imgheight = self.neck.height1()
    imgwidth  = self.neck.width1()
    hFactor = (68.00/imgheight)*6
    wFactor = 200.00/imgwidth
    self.neckScale[self.selected] = min(hFactor, wFactor)
    self.neck = None
    
  def shown(self):
    self.engine.input.addKeyListener(self)
    self.isRunning = True
    if not self.singlePlayer:
      n = self.session.id or 1
      name = Dialogs.getText(self.engine, _("Enter your name:"), _("Player #%d") % n)
      if name:
        self.session.world.createPlayer(name)
      else:
        self.engine.view.popLayer(self)

  def hidden(self):
    self.engine.input.removeKeyListener(self)
    self.session.broker.removeMessageHandler(self)
    if not self.gameStarted:
      self.session.close()
      self.engine.view.pushLayer(self.engine.mainMenu)    #rchiav: use already-existing MainMenu instance

  def handleGameStarted(self, sender):
    self.gameStarted = True
    self.engine.addTask(GameTask(self.engine, self.session), synchronized = False)
    self.engine.view.popLayer(self)

  def keyPressedSP(self, key, unicode):
    c = self.engine.input.controls.getMapping(key)
    i = self.playerNum
    if c in Player.cancels + self.no or key == pygame.K_ESCAPE:
#      if self.playerNum == 0: #akedrou - needs fixing.
      self.engine.data.cancelSound.play()
      self.engine.view.popLayer(self)
#      else:
#        self.playerNum -= 1
#        self.session.world.deletePlayer(self.session.world.players[self.playerNum])
#        self.blockedItems.remove(self.selectedItems.pop())
#        self.engine.data.cancelSound.play()
#        default = self.engine.config.get("game","player%d" % self.playerNum)
#        self.getStartingSelected(default)
      return True
    elif c in self.yes or key == pygame.K_RETURN:
      self.engine.data.acceptSound.play()
      self.scrolling = 0
      if self.selected == 0:
        self.done = False
        self.creator.loadPlayer()
        self.engine.view.pushLayer(self.creator)
      elif self.selected > 1:
        self.session.world.createPlayer(self.options[self.selected])
        self.engine.config.set("game", "player%d" % self.playerNum, self.options[self.selected])
        self.playerNum += 1
        self.blockedItems.append(self.selected)
        self.blockedItems.sort()
        self.selectedItems.append(self.options[self.selected])
        if self.playerNum >= self.players:
          self.gameStarted = True
          self.engine.menuMusic = False
          self.music = False
          self.engine.mainMenu.cutMusic()
          if self.tutorial:
            self.engine.config.set("game", "selected_library", "songs")
            self.session.world.startGame(libraryName = Song.DEFAULT_LIBRARY, songName = "tutorial")
          else:
            self.session.world.startGame()
        else:
          default = self.engine.config.get("game","player%d" % self.playerNum)
          self.getStartingSelected(default)
      return True
    elif (c in self.conf or key in [pygame.K_LCTRL, pygame.K_RCTRL]):
      self.engine.data.acceptSound.play()
      self.creator.loadPlayer(self.options[self.selected])
      self.done = False
      self.engine.view.pushLayer(self.creator)
      return True
    if self.playerNum >= self.players:
      return True
    if c in self.up + [Player.playerkeys[self.playerNum][Player.UP]] or key == pygame.K_UP:
      self.engine.data.selectSound.play()
      self.scrolling = 1
      self.scrollUp()
      self.delay = self.engine.scrollDelay
    elif c in self.down + [Player.playerkeys[self.playerNum][Player.DOWN]] or key == pygame.K_DOWN:
      self.engine.data.selectSound.play()
      self.scrolling = 2
      self.scrollDown()
      self.delay = self.engine.scrollDelay
    if self.selected > self.pos[1]:
      self.pos = (self.selected - self.screenOptions, self.selected)
    elif self.selected < self.pos[0]:
        self.pos = (self.selected, self.selected+self.screenOptions)
    return True
  
  def scrollUp(self):
    self.selected -= 1
    if self.selected < 0:
      self.selected = len(self.options) - 1
    while self.selected in self.blockedItems:
      self.selected -= 1
    self.loadAvatar()
    #self.loadNeck()
    if self.selected > self.pos[1]:
      self.pos = (self.selected - self.screenOptions, self.selected)
    elif self.selected < self.pos[0]:
        self.pos = (self.selected, self.selected+self.screenOptions)
    
  def scrollDown(self):
    self.selected += 1
    while self.selected in self.blockedItems:
      self.selected += 1
    if self.selected >= len(self.options):
      self.selected = 0
    self.loadAvatar()
    #self.loadNeck()
    if self.selected > self.pos[1]:
      self.pos = (self.selected - self.screenOptions, self.selected)
    elif self.selected < self.pos[0]:
        self.pos = (self.selected, self.selected+self.screenOptions)
  
  def keyPressed(self, key, unicode):
    if not self.active:
      return
    if self.singlePlayer:
      return self.keyPressedSP(key, unicode)
    
    c = self.engine.input.controls.getMapping(key)
    if c in Player.cancels + Player.key2s or key == pygame.K_ESCAPE:
      self.engine.view.popLayer(self)
    elif (c in [Player.key1s] or key == pygame.K_RETURN) and self.canStartGame():
      self.gameStarted = True
      self.session.world.startGame()      
    return True

  def keyReleased(self, key):
    self.scrolling = 0

  def run(self, ticks):
    self.time += ticks / 50.0
    self.neckT -= ticks/2000.0
    if self.neckT < 0.0:
      self.neckT = 1
    self.neckB = self.neckT - (1.0/6.0)
    if self.scrolling > 0:
      self.delay -= ticks
      self.rate += ticks
      if self.delay <= 0 and self.rate >= self.engine.scrollRate:
        self.rate = 0
        self.scroller[self.scrolling]()
    if self.music:
      self.engine.mainMenu.runMusic()

  def canStartGame(self):
    return len(self.session.world.players) >= self.players and self.session.isPrimary() and not self.gameStarted
  
  def drawNeck(self, w, h, i):
    twoNeck = False
    if self.neckB < 0:
      neckB = 1 - (self.neckB * -1)
      neckT = 1
      self.neckB = 0
      twoNeck = True
    if self.necks[i] == "Default" or self.necks[i] == None:
      neck = self.defaultNeck
      scale = self.defNeckScale
    elif self.necks[i] == "random":
      neck = self.randomNeck
      scale = self.randNeckScale
    else:
      neck = self.necks[i]
      scale = self.neckScale[i]
    hn = neck.height1()*scale*(self.neckT-self.neckB)
    self.engine.drawImage(neck, scale = (scale, scale*(self.neckT-self.neckB)), coord = (w*.7, h*.6-(hn/2)), rect = (0, 1, self.neckB, self.neckT))
    if twoNeck:
      h2 = neck.height1()*scale*(neckT-neckB)
      self.engine.drawImage(neck, scale = (scale, scale*(neckT-neckB)), coord = (w*.7, (h*.6)-hn-(h2/2)), rect = (0, 1, neckB, neckT))
  
  def renderLocalLobby(self, visibility, topMost):
    if self.playerNum >= self.players:
      return
    self.engine.view.setOrthogonalProjection(normalize = True)
    try:
      font = self.engine.data.fontDict[Theme.lobbySelectFont]
      titleFont = self.engine.data.fontDict[Theme.lobbyTitleFont]
    except KeyError:
      font = self.engine.data.font
      titleFont = self.engine.data.loadingFont
    v = ((1 - visibility) **2)
    w, h = self.fullView
    try:
      if self.background:
        wFactor = 640.000/self.background.width1()
        self.engine.drawImage(self.background, scale = (wFactor,-wFactor), coord = (w/2,h/2))
      r, g, b = Theme.lobbyTitleColor
      glColor3f(r, g, b)
      if self.chooseCharImg:
        self.engine.drawImage(self.chooseCharImg, scale = (Theme.lobbyTitleScale,-Theme.lobbyTitleScale), coord = (w*Theme.lobbyTitleX,h*Theme.lobbyTitleY))
      else:
        wText, hText = font.getStringSize(self.tsChooseChar, scale = Theme.lobbyTitleScale)
        titleFont.render(self.tsChooseChar, (Theme.lobbyTitleX-(wText),Theme.lobbyTitleY), scale = Theme.lobbyTitleScale)
      r, g, b = Theme.lobbyPlayerColor
      glColor3f(r, g, b)
      wText, hText = titleFont.getStringSize(self.tsPlayerStr % (self.playerNum+1), scale = Theme.lobbyTitleScale)
      titleFont.render(self.tsPlayerStr % (self.playerNum+1), (Theme.lobbyTitleCharacterX-wText/2, Theme.lobbyTitleCharacterY), scale = Theme.lobbyTitleScale)
      for i, name in enumerate(self.options):
        if i < self.pos[0] or i > self.pos[1]:
          continue
        if i == self.selected:
          if i > 1:
            #self.drawNeck(w, h, i)
            j = i-2 #player corresponding
            lefty = 1
            if self.playerPrefs[j][0] == 1:
              lefty = -1
            self.engine.drawImage(self.buttons, scale = (self.buttonScale*lefty, -self.buttonScale*(1.0/6.0)), coord = (w*Theme.lobbyPreviewX,h*(Theme.lobbyPreviewY+.45)), rect = (0, 1, 0, (1.0/6.0)))
            if self.lobbyMode == 1:
              avatarCoord = (w*Theme.lobbyAvatarX,h*Theme.lobbyAvatarY)
              avatarScale = Theme.lobbyAvatarScale
            else:
              avatarCoord = (w*Theme.lobbyPreviewX,h*(Theme.lobbyPreviewY+.75))
              avatarScale = 1
            if self.avatars[i] == "Empty" or self.avatars[i] == None:
              self.engine.drawImage(self.defaultAvatar, scale = (self.defAvScale*avatarScale,-self.defAvScale*avatarScale), coord = avatarCoord)
            else:
              self.engine.drawImage(self.avatars[i], scale = (self.avatarScale[i]*avatarScale,-self.avatarScale[i]*avatarScale), coord = avatarCoord)
            if self.infoImg:
              self.engine.drawImage(self.infoImg, scale = (.5,-.5), coord = (w*Theme.lobbyPreviewX,h*(Theme.lobbyPreviewY+.55)))
            else:
              wText, hText = titleFont.getStringSize(self.tsInfo, scale = .0025)
              titleFont.render(self.tsInfo, (Theme.lobbyPreviewX-wText/2, ((.45-Theme.lobbyPreviewY)*self.engine.data.fontScreenBottom)-hText/2), scale = .0025)
            r, g, b = Theme.lobbyInfoColor
            glColor3f(r, g, b)
            for k in range(1,5):
              text = self.tsList[k][self.playerPrefs[j][k]]
              wText, hText = font.getStringSize(text, scale = .0018)
              font.render(text, (Theme.lobbyPreviewX-wText/2,.4-(Theme.lobbyPreviewY*self.engine.data.fontScreenBottom)+(Theme.lobbyPreviewSpacing*k)), scale = .0018)
          if self.itemSelect:
            self.engine.drawImage(self.itemSelect, scale = (.5,-.5), coord = (w*Theme.lobbySelectImageX,h*(1-(Theme.lobbySelectImageY+Theme.lobbySelectSpace*(i-self.pos[0]))/self.engine.data.fontScreenBottom)))
          else:
            r, g, b = Theme.lobbySelectColor
            glColor3f(r, g, b)
        else:
          if i in self.blockedItems and i != 1:
            r, g, b = Theme.lobbyDisableColor
            glColor3f(r, g, b)
          else:
            r, g, b = Theme.lobbyFontColor
            glColor3f(r, g, b)
        if i == 1:
          wText, hText = titleFont.getStringSize(name, scale = Theme.lobbySelectScale)
          titleFont.render(name, (Theme.lobbySelectX-wText, Theme.lobbySelectY + (Theme.lobbySelectSpace*(i-self.pos[0]))), scale = Theme.lobbySelectScale)
        else:
          wText, hText = font.getStringSize(name, scale = Theme.lobbySelectScale)
          font.render(name, (Theme.lobbySelectX-wText, Theme.lobbySelectY + (Theme.lobbySelectSpace*(i-self.pos[0]))), scale = Theme.lobbySelectScale)
      
    finally:
      self.engine.view.resetProjection()
  
  def render(self, visibility, topMost):
    if not visibility:
      self.active = False
      return
    if not self.active:
      self.getPlayers()
    self.active = True
    self.done   = True
    if self.singlePlayer:
      self.renderLocalLobby(visibility, topMost)
      return
    
    self.engine.view.setOrthogonalProjection(normalize = True)
    font = self.engine.data.font

    try:
      v = 1.0 - ((1 - visibility) ** 2)
      
      glEnable(GL_BLEND)
      glBlendFunc(GL_SRC_ALPHA, GL_ONE)
      glEnable(GL_COLOR_MATERIAL)

      text = _("Lobby (%d players)") % len(self.session.world.players)
      w, h = font.getStringSize(text)

      x = .5 - w / 2
      d = 0.0
      c = 1 - .25 * v

      y = .1 - (1.0 - v) * .2
        
      for i, ch in enumerate(text):
        w, h = font.getStringSize(ch)
        c = i * .05
        glColor3f(*colorsys.hsv_to_rgb(.75, c, 1))
        glPushMatrix()
        s = .25 * (math.sin(i / 2 + self.time / 4) + 2)
        glTranslate(-s * w / 2, -s * h / 2, 0)
        font.render(ch, (x, y), scale = 0.002 * s)
        glPopMatrix()
        x += w

      x = .1
      y = .2 + (1 - v) / 4
      glColor4f(1, 1, 1, v)
      
      for player in self.session.world.players:
        font.render(player.name, (x, y))
        y += .08

      if self.canStartGame():
        s = _("Press Enter to Start Game")
        sz = 0.0013
        w, h = font.getStringSize(s, scale = sz)
        font.render(s, (.5 - w / 2, .65), scale = sz)
        
    finally:
      self.engine.view.resetProjection()

class CreateCharacter(Layer, KeyListener):
  def __init__(self, engine):
    self.engine    = engine
    self.time      = 0.0
    self.blink     = 0
    self.cursor    = ""
    self.name      = ""
    self.active    = False
    self.oldValue  = None
    self._cache    = None
    self.selected  = 0
    self.choice    = 0
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
    self.player    = None
    self.loadPlayer()
    self.dictEnDisable = {0: _("Disabled"), 1: _("Enabled")}
    self.lefty     = {0: 1, 1: -1}
    self.values    = (self.dictEnDisable, self.dictEnDisable, self.dictEnDisable, {0: _("Disabled"), 1: _("Easy Assist"), 2: _("Medium Assist")}, self.dictEnDisable)
    self.options   = [(_("Name"),             _("Name your character!")), \
                      (_("Lefty Mode"),       _("Flip the guitar frets for left-handed playing!")), \
                      (_("Drum Flip"),        _("Flip the drum sounds - red hits become green, and so on")), \
                      (_("Auto-Kick Bass"),   _("Feet uncooperative? Broke your pedal? Not to worry!")), \
                      (_("Assist Mode"),      _("Play hard and expert, even when you're not that good!")), \
                      (_("Two-Chord Max"),    _("Cut those jumbo chords down to a more manageable size!")), \
                      (_("Neck"),             _("Set a custom neck image just for you!")), \
                      (_("Upload Name"),      _("'Harry Potter' is all well and good, but...")), \
                      (_("Reset Stats"),      _("Sometimes it's better to start from scratch.")), \
                      (_("Delete Character"), _("Come on... I didn't mean it. Really, I promise!")), \
                      (_("Done"),             _("All finished? Let's do this thing!"))]
    themename = self.engine.data.themeLabel
    try:
      self.engine.loadImgDrawing(self, "background", os.path.join("themes", themename, "lobby", "creator.png"))
    except IOError:
      self.background = None
  def loadPlayer(self, player = None):
    self.choices = []
    if player is not None:
      try:
        pref = self.cache.execute('SELECT * FROM `players` WHERE `name` = ?', [player]).fetchone()
        pref = [pref[0], pref[1], pref[2], pref[3], pref[4], pref[5], pref[6], pref[9]]
        self.newChar = False
        self.player = player
      except: #not found
        pref = ['', 0, 0, 0, 0, 0, '', '']
        self.newChar = True
        self.player = None
    else:
      pref = ['', 0, 0, 0, 0, 0, '', '']
      self.newChar = True
      self.player = None
    for i in pref:
      self.choices.append(i)
    self.choices.extend(["", "", ""])
  def resetStats(self):
    if not self.player:
      return
    tsYes = _("Yes")
    q = Dialogs.chooseItem(self.engine, [tsYes, _("No")], _("Are you sure you want to reset all stats for this player?"))
    if q == tsYes:
      Dialogs.showMessage(self.engine, _("No stats saved."))
      #Player.resetStats(self.player)
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
    if len(self.choices[0]) > 0:
      if self.choices[0].lower() == "default":
        Dialogs.showMessage(self.engine, _("That is a terrible name. Choose something not 'default'"))
      elif self.choices[0].lower() not in self.invalidNames or self.choices[0] == self.player:
        Player.updatePlayer(self.player, pref)
        self.engine.view.popLayer(self)
        self.engine.input.removeKeyListener(self)
      else:
        Dialogs.showMessage(self.engine, _("That name already exists!"))
    else:
      Dialogs.showMessage(self.engine, _("Please enter a name!"))
  def getCache(self):
    if not self._cache:
      self._cache = Player.playerCacheManager.getCache()
    return self._cache
  cache = property(getCache) #to allow deleting.
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
        if self.selected == 0 and ord(unicode) in (34, 42, 47, 58, 60, 62, 63, 92, 124):
          self.engine.data.cancelSound.play()
          return True
        if len(self.choices[self.selected]) > 24:
          self.choices[self.selected] = self.choices[self.selected][:-1]
        self.choices[self.selected] += unicode
        return
    if c in Player.key1s or key == pygame.K_RETURN:
      self.scrolling = 0
      if self.selected in (0, 7):
        if self.active:
          self.active = False
        else:
          self.blink  = 0
          self.active = True
          self.oldValue = self.choices[self.selected]
      elif self.selected == 6:
        self.engine.view.pushLayer(Dialogs.NeckChooser(self.engine, player = self.player, owner = self))
        self.keyActive = False
      elif self.selected == 8:
        self.resetStats()
      elif self.selected == 9:
        self.deleteCharacter()
      elif self.selected == 10:
        self.saveCharacter()
      self.engine.data.acceptSound.play()
    elif c in Player.key2s + Player.cancels or key == pygame.K_ESCAPE:
      self.engine.data.cancelSound.play()
      if not self.active:
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
      if self.selected in (0, 6, 7, 8, 9, 10):
        pass
      elif self.selected == 4:
        self.choices[self.selected]+=1
        if self.choices[self.selected] > 2:
          self.choices[self.selected] = 0
      else:
        self.choices[self.selected] = 1 and (self.choices[self.selected] == 0) or 0
    elif c in Player.lefts or key == pygame.K_LEFT:
      if self.selected in (0, 6, 7, 8, 9, 10):
        pass
      elif self.selected == 4:
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
      font = self.engine.data.fontDict[Theme.characterCreateOptionFont]
      helpFont = self.engine.data.fontDict[Theme.characterCreateHelpFont]
    except KeyError:
      font = self.engine.data.font
      helpFont = self.engine.data.loadingFont
    self.engine.view.setOrthogonalProjection(normalize = True)
    v = ((1 - visibility) **2)
    w, h = self.fullView
    try:
      if self.background:
        wFactor = 640.000/self.background.width1()
        self.engine.drawImage(self.background, scale = (wFactor,-wFactor), coord = (w/2,h/2))
      for i, option in enumerate(self.options):
        r, g, b = Theme.characterCreateHelpColor
        glColor3f(r, g, b)
        cursor = ""
        if self.selected == i:
          wText, hText = helpFont.getStringSize(option[1], scale = Theme.characterCreateScale)
          helpFont.render(option[1], (Theme.characterCreateHelpX-(wText/2), Theme.characterCreateHelpY-hText), scale = Theme.characterCreateHelpScale)
          r, g, b = Theme.characterCreateSelectColor
          glColor3f(r, g, b)
          cursor = self.cursor
        else:
          r, g, b = Theme.characterCreateFontColor
          glColor3f(r, g, b)
        wText, hText = font.getStringSize(option[0], scale = Theme.characterCreateScale)
        font.render(option[0], (Theme.characterCreateX, Theme.characterCreateY+Theme.characterCreateSpace*i), scale = Theme.characterCreateScale)
        if self.active and self.selected == i:
          Theme.setSelectedColor(1-v)
        if i == 0 or i > 5:
          wText, hText = font.getStringSize(self.choices[i], scale = Theme.characterCreateScale)
          font.render(self.choices[i]+cursor, (Theme.characterCreateOptionX-wText, Theme.characterCreateY+Theme.characterCreateSpace*i), scale = Theme.characterCreateScale)
        else:
          wText, hText = font.getStringSize(self.values[i-1][self.choices[i]], scale = Theme.characterCreateScale)
          font.render(self.values[i-1][self.choices[i]], (Theme.characterCreateOptionX-wText, Theme.characterCreateY+Theme.characterCreateSpace*i), scale = Theme.characterCreateScale)
    finally:
      self.engine.view.resetProjection()

#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
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

from __future__ import with_statement

from Scene import Scene, SuppressScene
import os
import time
import Player
import Dialogs
import Song
import Config
import pygame
import Version
from Menu import Menu
from Settings import ConfigChoice, ActiveConfigChoice
from Language import _
from Camera import Camera
from Mesh import Mesh
from Texture import Texture

import Log    #MFH

PRACTICE = 1
CAREER = 2

instrumentDiff = {
  0 : (lambda a: a.diffGuitar),
  1 : (lambda a: a.diffGuitar),
  2 : (lambda a: a.diffBass),
  3 : (lambda a: a.diffGuitar),
  4 : (lambda a: a.diffDrums),
  5 : (lambda a: a.diffVocals)
}

class SongChoosingScene(Scene):
  def __init__(self, engine, libraryName = None, songName = None):
    Scene.__init__(self, engine)
    
    if self.engine.world.sceneName == "SongChoosingScene":  #MFH - dual / triple loading cycle fix
      Log.warn("Extra SongChoosingScene was instantiated, but detected and shut down.  Cause unknown.")
      raise SuppressScene  #stump
    else:
      self.engine.world.sceneName = "SongChoosingScene"

    if self.engine.config.get("debug", "use_new_song_database"):
      Song.updateSongDatabase(self.engine)

    self.wizardStarted = False
    self.libraryName   = libraryName
    self.songName      = songName
    if not self.libraryName:
      self.libraryName = self.engine.config.get("setlist", "selected_library")
      if not self.libraryName:
        self.libraryName = Song.DEFAULT_LIBRARY
    if not self.songName:
      self.songName = self.engine.config.get("setlist", "selected_song")
    self.gameMode = self.engine.world.gameMode
    self.careerMode = (self.gameMode == CAREER)
    self.practiceMode = (self.gameMode == PRACTICE)
    self.gameMode2p = self.engine.world.multiMode
    self.autoPreview = not self.engine.config.get("audio", "disable_preview")
    self.sortOrder   = self.engine.config.get("game", "sort_order")
    self.tut = self.engine.world.tutorial
    self.playerList  = self.players

    self.gameStarted = False
    
    self.gamePlayers = len(self.playerList)
    self.parts = [None for i in self.playerList]
    self.diffs = [None for i in self.playerList]
    
    self.time       = 0
    self.lastTime   = 0
    self.mode       = 0
    self.moreInfo   = False
    self.moreInfoTime = 0
    self.miniLobbyTime = 0
    self.selected   = 0
    self.camera     = Camera()
    self.cameraOffset = 0.0
    self.song       = None
    self.songLoader = None
    self.loaded     = False
    text            = _("Initializing Setlist...")
    if self.engine.cmdPlay == 2:
      text = _("Checking Command-Line Settings...")
    elif len(self.engine.world.songQueue) > 0:
      text = _("Checking Setlist Settings...")
    elif len(self.engine.world.songQueue) == 0:
      self.engine.world.playingQueue = False
    self.splash     = Dialogs.showLoadingSplashScreen(self.engine, text)
    self.items      = []
    self.cmdPlay    = False
    self.queued     = True
    
    self.loadStartTime = time.time()
    
    if self.tut == True:
      self.library = self.engine.tutorialFolder
    else:
      self.library    = os.path.join(self.engine.config.get("setlist", "base_library"), self.libraryName)
      if not os.path.isdir(self.engine.resource.fileName(self.library)):
        self.library = self.engine.resource.fileName(os.path.join(self.engine.config.get("setlist", "base_library"), Song.DEFAULT_LIBRARY))
    
    self.searchText = ""
    
    #user configurables and input management
    self.listingMode       = 0     #with libraries or List All
    self.preloadSongLabels = False
    self.showCareerTiers   = 1+(self.careerMode and 1 or 0) #0-Never; 1-Career Only; 2-Always
    self.scrolling        = 0
    self.scrollDelay      = self.engine.config.get("game", "scroll_delay")
    self.scrollRate       = self.engine.config.get("game", "scroll_rate")
    self.scrollTime       = 0
    self.scroller         = [lambda: None, self.scrollUp, self.scrollDown]
    self.scoreDifficulty  = Song.difficulties[self.engine.config.get("game", "songlist_difficulty")]
    self.scorePart        = Song.parts[self.engine.config.get("game", "songlist_instrument")]
    self.sortOrder        = self.engine.config.get("game", "sort_order")
    self.queueFormat      = self.engine.config.get("game", "queue_format")
    self.queueOrder       = self.engine.config.get("game", "queue_order")
    self.queueParts       = self.engine.config.get("game", "queue_parts")
    self.queueDiffs       = self.engine.config.get("game", "queue_diff")
    self.nilShowNextScore = self.engine.config.get("songlist",  "nil_show_next_score")
    
    #theme information
    self.themename = self.engine.data.themeLabel
    self.theme = self.engine.data.theme
    
    #theme configurables
    self.setlistStyle      = self.engine.theme.setlist.setlistStyle    #0 = Normal; 1 = List; 2 = Circular
    self.headerSkip        = self.engine.theme.setlist.headerSkip      #items taken up by header (non-static only)
    self.footerSkip        = self.engine.theme.setlist.footerSkip      #items taken up by footer (non-static only)
    self.itemSize          = self.engine.theme.setlist.itemSize        #delta (X, Y) (0..1) for each item (non-static only)
    self.labelType         = self.engine.theme.setlist.labelType       #Album covers (0) or CD labels (1)
    self.labelDistance     = self.engine.theme.setlist.labelDistance   #number of labels away to preload
    self.showMoreLabels    = self.engine.theme.setlist.showMoreLabels  #whether or not additional unselected labels are rendered on-screen
    self.texturedLabels    = self.engine.theme.setlist.texturedLabels  #render the art as a texture?
    self.itemsPerPage      = self.engine.theme.setlist.itemsPerPage    #number of items to show on screen
    self.followItemPos     = (self.itemsPerPage+1)/2
    self.showLockedSongs   = self.engine.theme.setlist.showLockedSongs #whether or not to even show locked songs
    self.showSortTiers     = self.engine.theme.setlist.showSortTiers   #whether or not to show sorting tiers - career tiers take precedence.
    self.selectTiers       = self.engine.theme.setlist.selectTiers     #whether or not tiers should be selectable as a quick setlist.
    
    if self.engine.cmdPlay == 2:
      self.songName = Config.get("setlist", "selected_song")
      self.libraryName = Config.get("setlist", "selected_library")
      self.cmdPlay = self.checkCmdPlay()
      if self.cmdPlay:
        Dialogs.hideLoadingSplashScreen(self.engine, self.splash)
        return
    elif len(self.engine.world.songQueue) > 0:
      Dialogs.hideLoadingSplashScreen(self.engine, self.splash)
      return
    
    #variables for setlist management (Not that this is necessary here - just to see what exists.)
    self.songLoader       = None #preview handling
    self.tiersPresent     = False
    self.startingSelected = self.songName
    self.selectedIndex    = 0
    self.selectedItem     = None
    self.selectedOffset   = 0.0
    self.previewDelay     = 1000
    self.previewLoaded    = False
    self.itemRenderAngles = [0.0]
    self.itemLabels       = [None]
    self.xPos             = 0
    self.yPos             = 0
    self.pos              = 0
    
    self.infoPage         = 0
    
    self.menu_force_reload   = False
    self.menu_text_color     = (1, 1, 1)
    self.menu_selected_color = (.66, .66, 0)
    self.menu_text_pos       = (.2, .31)
    self.menu = Menu(self.engine, [ConfigChoice(self.engine, self.engine.config, "game", "queue_format", autoApply = True),
                                   ConfigChoice(self.engine, self.engine.config, "game", "queue_order", autoApply = True),
                                   ConfigChoice(self.engine, self.engine.config, "game", "queue_parts", autoApply = True),
                                   ConfigChoice(self.engine, self.engine.config, "game", "queue_diff", autoApply = True),
                                   ActiveConfigChoice(self.engine, self.engine.config, "game", "sort_order", onChange = self.forceReload),
                                   ActiveConfigChoice(self.engine, self.engine.config, "game", "sort_direction", onChange = self.forceReload),
                                   ActiveConfigChoice(self.engine, self.engine.config, "game", "songlist_instrument", onChange = self.forceReload),
                                   ActiveConfigChoice(self.engine, self.engine.config, "game", "songlist_difficulty", onChange = self.forceReload),
                                   ], name = "setlist", fadeScreen = False, onClose = self.resetQueueVars, font = self.engine.data.pauseFont, \
                     pos = self.menu_text_pos, textColor = self.menu_text_color, selectedColor = self.menu_selected_color)
    
    #now, load the first library
    self.loadLibrary()

    #load the images
    self.loadImages()

  #blazingamer - by adding this method it makes it much easier for a person 
  #     to add custom images to the CustomSetlist.py
  #     
  def loadImages(self):
    
    self.loadIcons()

    #mesh...
    if os.path.exists(os.path.join(Version.dataPath(),"themes",self.themename,"setlist","item.dae")):
      self.engine.resource.load(self, "itemMesh", lambda: Mesh(self.engine.resource.fileName("themes",self.themename,"setlist","item.dae")), synch = True)
    else:
      self.itemMesh = None
    if os.path.exists(os.path.join(Version.dataPath(),"themes",self.themename,"setlist","library.dae")):
      self.engine.resource.load(self, "libraryMesh", lambda: Mesh(self.engine.resource.fileName("themes",self.themename,"setlist","library.dae")), synch = True)
    else:
      self.libraryMesh = None
    if os.path.exists(os.path.join(Version.dataPath(),"themes",self.themename,"setlist","label.dae")):
      self.engine.resource.load(self, "label", lambda: Mesh(self.engine.resource.fileName("themes",self.themename,"setlist","label.dae")), synch = True)
    else:
      self.label = None
    if os.path.exists(os.path.join(Version.dataPath(),"themes",self.themename,"setlist","library_label.dae")):
      self.engine.resource.load(self, "libraryLabel", lambda: Mesh(self.engine.resource.fileName("themes",self.themename,"setlist","library_label.dae")), synch = True)
    else:
      self.libraryLabel = None
    if os.path.exists(os.path.join(Version.dataPath(),"themes",self.themename,"setlist","tier.dae")):
      self.engine.resource.load(self, "tierMesh", lambda: Mesh(self.engine.resource.fileName("themes",self.themename,"setlist","tier.dae")), synch = True)
    else:
      self.tierMesh = self.libraryMesh
    if os.path.exists(os.path.join(Version.dataPath(),"themes",self.themename,"setlist","list.dae")):
      self.engine.resource.load(self, "listMesh", lambda: Mesh(self.engine.resource.fileName("themes",self.themename,"setlist","list.dae")), synch = True)
    else:
      self.listMesh = self.libraryMesh
    
  #blazingamer - if someone wishes to load the song icons to use in their setlist they do not have to
  #              rewrite it into the CustomSetlist.py if we make it a separate method
  def loadIcons(self):
    #begin to load images...
    self.itemIcons = {}
    if os.path.isdir(os.path.join(Version.dataPath(),"themes",self.themename,"setlist")):
      self.engine.data.loadAllImages(self, os.path.join("themes",self.themename,"setlist"))
      if os.path.isdir(os.path.join(Version.dataPath(),"themes",self.themename,"setlist","icon")):
        self.itemIcons = self.engine.data.loadAllImages(None, os.path.join("themes",self.themename,"setlist","icon"), prefix="")
  
  def forceReload(self):
    self.menu_force_reload = True
  
  def resetQueueVars(self):
    self.scoreDifficulty  = Song.difficulties[self.engine.config.get("game", "songlist_difficulty")]
    self.scorePart        = Song.parts[self.engine.config.get("game", "songlist_instrument")]
    self.sortOrder        = self.engine.config.get("game", "sort_order")
    self.queueFormat      = self.engine.config.get("game", "queue_format")
    self.queueOrder       = self.engine.config.get("game", "queue_order")
    self.queueParts       = self.engine.config.get("game", "queue_parts")
    self.queueDiffs       = self.engine.config.get("game", "queue_diff")
    if self.queueFormat == 0:
      self.engine.world.songQueue.reset()
    if self.menu_force_reload:
      self.menu_force_reload = False
      self.loadLibrary()
  
  def loadLibrary(self):
    Log.debug("Loading libraries in %s" % self.library)
    self.loaded = False
    self.tiersPresent = False
    if self.splash:
      Dialogs.changeLoadingSplashScreenText(self.engine, self.splash, _("Browsing Collection..."))
    else:
      self.splash = Dialogs.showLoadingSplashScreen(self.engine, _("Browsing Collection..."))
      self.loadStartTime = time.time()
    self.engine.resource.load(self, "libraries", lambda: Song.getAvailableLibraries(self.engine, self.library), onLoad = self.loadSongs, synch = True)
  
  def loadSongs(self, libraries):
    Log.debug("Loading songs in %s" % self.library)
    self.engine.resource.load(self, "songs", lambda: Song.getAvailableSongsAndTitles(self.engine, self.library, progressCallback=self.progressCallback), onLoad = self.prepareSetlist, synch = True)
  
  def progressCallback(self, percent):
    if time.time() - self.loadStartTime > 7:
      Dialogs.changeLoadingSplashScreenText(self.engine, self.splash, _("Browsing Collection...") + ' (%d%%)' % (percent*100))
  
  def prepareSetlist(self, songs):
    if self.songLoader:
      self.songLoader.cancel()
    msg = self.engine.setlistMsg
    self.engine.setlistMsg = None
    self.selectedIndex = 0
    if self.listingMode == 0 or self.careerMode:
      self.items = self.libraries + self.songs
    else:
      self.items = self.songs
    self.itemRenderAngles = [0.0]  * len(self.items)
    self.itemLabels       = [None] * len(self.items)
    self.searching        = False
    self.searchText       = ""
    
    shownItems = []
    for item in self.items: #remove things we don't want to see. Some redundancy, but that's okay.
      if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        if self.showCareerTiers == 2:
          if isinstance(item, Song.TitleInfo):
            if len(shownItems) > 0:
              if isinstance(shownItems[-1], Song.TitleInfo):
                shownItems.pop()
            shownItems.append(item)
          elif isinstance(item, Song.SortTitleInfo):
            continue
        else:
          if isinstance(item, Song.TitleInfo):
            continue
          elif isinstance(item, Song.SortTitleInfo):
            if not self.showSortTiers:
              continue
            if len(shownItems) > 0:
              if isinstance(shownItems[-1], Song.SortTitleInfo):
                shownItems.pop()
            shownItems.append(item)
      elif isinstance(item, Song.SongInfo):
        if self.careerMode and (not self.showLockedSongs) and item.getLocked():
          continue
        else:
          shownItems.append(item)
      else:
        shownItems.append(item)
    if len(shownItems) > 0:
      if isinstance(shownItems[-1], Song.TitleInfo) or isinstance(shownItems[-1], Song.SortTitleInfo):
        shownItems.pop()
    
    if len(self.items) > 0 and len(shownItems) == 0:
      msg = _("No songs in this setlist are available to play!")
      if self.careerMode:
        msg = msg + " " + _("Make sure you have a working career pack!")
      Dialogs.showMessage(self.engine, msg)
    elif len(shownItems) > 0:
      for item in shownItems:
        if isinstance(item, Song.SongInfo) or isinstance(item, Song.LibraryInfo):
          self.items = shownItems #make sure at least one item is selectable
          break
      else:
        msg = _("No songs in this setlist are available to play!")
        if self.careerMode:
          msg = msg + " " + _("Make sure you have a working career pack!")
        Dialogs.showMessage(self.engine, msg)
        self.items = []
    
    if self.items == []:    #MFH: Catch when there ain't a damn thing in the current folder - back out!
      if self.library != Song.DEFAULT_LIBRARY:
        Dialogs.hideLoadingSplashScreen(self.engine, self.splash)
        self.splash = None
        self.startingSelected = self.library
        self.library     = os.path.dirname(self.library)
        self.selectedItem = None
        self.loadLibrary()
        return
    
    Log.debug("Setlist loaded.")
    
    self.loaded           = True
    
    if self.setlistStyle == 1:
      for i in range(self.headerSkip):
        self.items.insert(0, Song.BlankSpaceInfo())
      for i in range(self.footerSkip):
        self.items.append(Song.BlankSpaceInfo())
    
    if self.startingSelected is not None:
      for i, item in enumerate(self.items):
        if isinstance(item, Song.SongInfo) and self.startingSelected == item.songName: #TODO: SongDB
          self.selectedIndex =  i
          break
        elif isinstance(item, Song.LibraryInfo) and self.startingSelected == item.libraryName:
          self.selectedIndex =  i
          break
    
    for item in self.items:
      if isinstance(item, Song.SongInfo):
        item.name = Song.removeSongOrderPrefixFromName(item.name) #TODO: I don't like this.
      elif not self.tiersPresent and (isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo)):
        self.tiersPresent = True
    
    while isinstance(self.items[self.selectedIndex], Song.BlankSpaceInfo) or ((isinstance(self.items[self.selectedIndex], Song.TitleInfo) or isinstance(self.items[self.selectedIndex], Song.SortTitleInfo)) and not self.selectTiers):
      self.selectedIndex += 1
      if self.selectedIndex >= len(self.items):
        self.selectedIndex = 0
    
    self.itemRenderAngles = [0.0]  * len(self.items)
    self.itemLabels       = [None] * len(self.items)
    
    if self.preloadSongLabels:
      for i in range(len(self.items)):
        self.loadStartTime = time.time()
        Dialogs.changeLoadingSplashScreenText(self.engine, self.splash, _("Loading Album Artwork..."))
        self.loadItemLabel(i, preload = True)
    
    self.updateSelection()
    Dialogs.hideLoadingSplashScreen(self.engine, self.splash)
    self.splash = None
  
  def checkCmdPlay(self):
    info = Song.loadSongInfo(self.engine, self.songName, library = self.libraryName)
    guitars = []
    drums = []
    vocals = []
    autoPart = None
    for part in info.parts:
      if part.id == 4:
        drums.append(part)
      elif part.id == 5:
        vocals.append(part)
      else:
        guitars.append(part)
      if self.engine.cmdPlay == 2 and self.engine.cmdPart is not None and len(self.playerList) == 1:
        if self.engine.cmdPart == part.id:
          Log.debug("Command-line mode: Part found!")
          if part.id == 4 and self.engine.input.gameDrums > 0:
            autoPart = part.id
          elif part.id == 5 and self.engine.input.gameMics > 0:
            autoPart = part.id
          elif self.engine.input.gameGuitars > 0:
            autoPart = part.id
    if autoPart is None:
      if len(drums) == 0 and self.engine.input.gameDrums > 0:
        if self.splash:
          Dialogs.hideLoadingSplashScreen(self.engine, self.splash)
          self.splash = None
        Dialogs.showMessage(self.engine, _("There are no drum parts in this song. Change your controllers to play."))
        if self.engine.cmdPlay == 2:
          self.engine.cmdPlay = 0
          return False
      if len(guitars) == 0 and self.engine.input.gameGuitars > 0:
        if self.splash:
          Dialogs.hideLoadingSplashScreen(self.engine, self.splash)
          self.splash = None
        Dialogs.showMessage(self.engine, _("There are no guitar parts in this song. Change your controllers to play."))
        if self.engine.cmdPlay == 2:
          self.engine.cmdPlay = 0
          return False
      if len(vocals) == 0 and self.engine.input.gameMics > 0:
        if self.splash:
          Dialogs.hideLoadingSplashScreen(self.engine, self.splash)
          self.splash = None
        Dialogs.showMessage(self.engine, _("There are no vocal parts in this song. Change your controllers to play."))
        if self.engine.cmdPlay == 2:
          self.engine.cmdPlay = 0
          return False
    # Make sure the difficulty we chose is available
    p = self.playerList[0].part
    player = self.playerList[0]
    if self.engine.cmdDiff is not None:
      diff = Song.difficulties[self.engine.cmdDiff]
      if diff in info.partDifficulties[p.id]:
        self.playerList[0].difficulty = diff
      else:
        self.playerList[0].difficulty = info.partDifficulties[p.id][0]
    else:
      if self.splash:
          Dialogs.hideLoadingSplashScreen(self.engine, self.splash)
          self.splash = None
      self.playerList[0].difficulty = Dialogs.chooseItem(self.engine, info.partDifficulties[p.id],
                            "%s \n %s" % (Song.removeSongOrderPrefixFromName(info.name), _("%s Choose a difficulty:") % player.name), selected = player.difficulty)
    return True
  
  def loadItemLabel(self, i, preload = False):
    # Load the item label if it isn't yet loaded
    themename = self.engine.data.themeLabel
    item = self.items[i]
    if self.itemLabels[i] is None:
      if isinstance(item, Song.SongInfo):
        if self.labelType == 1: #CD covers
          f = "label.png"
        else:
          f = "album.png"
        if self.texturedLabels:
          label = self.engine.resource.fileName(item.libraryNam, item.songName, f)
          if os.path.exists(label):
            self.itemLabels[i] = Texture(label)
          else:
            self.itemLabels[i] = False
        else:
          self.itemLabels[i] = self.engine.loadImgDrawing(None, "label", os.path.join(item.libraryNam, item.songName, f))

      elif isinstance(item, Song.LibraryInfo):
        if self.texturedLabels:
          label = self.engine.resource.fileName(item.libraryName, "label.png")
          if os.path.exists(label):
            self.itemLabels[i] = Texture(label)
          else:
            self.itemLabels[i] = False
        else:
          self.itemLabels[i] = self.engine.loadImgDrawing(None, "label", os.path.join(item.libraryName, "label.png"))
      elif isinstance(item, Song.RandomSongInfo):
        self.itemLabels[i] = "Random"
      else:
        return
      if preload:
        if time.time() - self.loadStartTime > 3:
          self.loadStartTime = time.time()
          percent = (i*100)/len(self.items)
          Dialogs.changeLoadingSplashScreenText(self.engine, self.splash, _("Loading Album Artwork...") + " %d%%" % percent)

  def addToQueue(self, selectedSong): #FIXME: Queue system
    self.engine.songQueue.addSong(selectedSong, library)
  
  def removeFromQueue(self, selectedSong):
    self.engine.songQueue.removeSong(selectedSong)
  
  def startGame(self, fromQueue = False): #note this is not refined.
    if len(self.engine.world.songQueue) == 0:
      return
    showDialog = True
    if not fromQueue and self.queueFormat == 1 and len(self.engine.world.songQueue) > 1:
      self.engine.world.songQueue.setFullQueue()
      self.engine.world.playingQueue = True
    if self.queueOrder == 1:
      self.songName, self.libraryName = self.engine.world.songQueue.getRandomSong()
    else:
      self.songName, self.libraryName = self.engine.world.songQueue.getSong()
    info = Song.loadSongInfo(self.engine, self.songName, library = self.libraryName)
    guitars = []
    drums = []
    vocals = []
    for part in info.parts:
      if part.id == 4:
        drums.append(part)
      elif part.id == 5:
        vocals.append(part)
      else:
        guitars.append(part)
    choose = [[] for i in self.players]
    for i, player in enumerate(self.players):
      j = self.engine.world.songQueue.getParts()[i]
      if player.controlType == 2 or player.controlType == 3:
        choose[i] = drums
      elif player.controlType == 5:
        choose[i] = vocals
      else:
        choose[i] = guitars
    if self.queued:
      showDialog = False
      for i, player in enumerate(self.players):
        if Song.parts[j] in choose[i]:
          p = Song.parts[j]
        elif self.queueParts == 0:
          if j == 0:
            for k in [3, 1, 2]:
              if Song.parts[k] in choose[i]:
                p = Song.parts[k]
                break
          elif j == 1:
            for k in [2, 0, 3]:
              if Song.parts[k] in choose[i]:
                p = Song.parts[k]
                break
          elif j == 2:
            for k in [1, 0, 3]:
              if Song.parts[k] in choose[i]:
                p = Song.parts[k]
                break
          elif j == 3:
            for k in [0, 1, 2]:
              if Song.parts[k] in choose[i]:
                p = Song.parts[k]
                break
        j = self.engine.world.songQueue.getDiffs()[i]
        if Song.difficulties[j] in info.partDifficulties[p.id]:
          d = Song.difficulties[j]
        elif self.queueDiffs == 0:
          if j == 0:
            for k in range(1,4):
              if Song.difficulties[k] in info.partDifficulties[p.id]:
                d = Song.difficulties[k]
          elif j == 1:
            for k in range(2,5):
              if Song.difficulties[k%4] in info.partDifficulties[p.id]:
                d = Song.difficulties[k%4]
          elif j == 2:
            if Song.difficulties[3] in info.partDifficulties[p.id]:
                d = Song.difficulties[3]
            else:
              for k in range(1, -1, -1):
                if Song.difficulties[k] in info.partDifficulties[p.id]:
                  d = Song.difficulties[k]
          else:
            for k in range(2, -1, -1):
              if Song.difficulties[k] in info.partDifficulties[p.id]:
                d = Song.difficulties[k]
        elif self.queueDiffs == 1:
          if j == 3:
            for k in range(2,-1, -1):
              if Song.difficulties[k] in info.partDifficulties[p.id]:
                d = Song.difficulties[k]
          elif j == 2:
            for k in range(1,-2,-1):
              if Song.difficulties[k%4] in info.partDifficulties[p.id]:
                d = Song.difficulties[k%4]
          elif j == 1:
            if Song.difficulties[0] in info.partDifficulties[p.id]:
                d = Song.difficulties[0]
            else:
              for k in range(2,4):
                if Song.difficulties[k] in info.partDifficulties[p.id]:
                  d = Song.difficulties[k]
          else:
            for k in range(1,4):
              if Song.difficulties[k] in info.partDifficulties[p.id]:
                d = Song.difficulties[k]
        if p and d:
          player.part = p
          player.difficulty = d
        else:
          showDialog = True
    if showDialog:
      ready = False
      while not ready:
        ready = Dialogs.choosePartDiffs(self.engine, choose, info, self.players)
        if not ready and not self.queued and not self.engine.cmdPlay:
          return False
    if self.engine.cmdPlay > 0:
      self.engine.cmdPlay = 3
    self.freeResources()
    self.engine.world.createScene("GuitarScene", libraryName = self.libraryName, songName = self.songName)
    self.gameStarted = True
  
  def checkParts(self):
    info = Song.loadSongInfo(self.engine, self.songName, library = self.libraryName)
    guitars = []
    drums = []
    vocals = []
    for part in info.parts:
      if part.id == 4:
        drums.append(part)
      elif part.id == 5:
        vocals.append(part)
      else:
        guitars.append(part)
    if len(drums) == 0 and self.engine.input.gameDrums > 0:
      Dialogs.showMessage(self.engine, _("There are no drum parts in this song. Change your controllers to play."))
      return False
    if len(guitars) == 0 and self.engine.input.gameGuitars > 0:
      Dialogs.showMessage(self.engine, _("There are no guitar parts in this song. Change your controllers to play."))
      return False
    if len(vocals) == 0 and self.engine.input.gameMics > 0:
      Dialogs.showMessage(self.engine, _("There are no vocal parts in this song. Change your controllers to play."))
      return False
    return True
  
  def checkQueueParts(self):
    parts = self.engine.world.songQueue.getParts()
    
  
  def freeResources(self):
    self.songs = None
    self.folder = None
    self.label = None
    self.song = None
    for img in dir(self):
      if img.startswith("img"):
        self.__dict__[img] = None
    self.itemMesh = None
    self.tierMesh = None
    self.libraryMesh = None
    self.listMesh = None
    self.itemLabels = None
    self.itemIcons = None
    
    if self.song:
      self.song.fadeout(1000)
      self.song = None
    self.selectedItem = None
    if self.songLoader:
      self.songLoader.cancel()
      self.songLoader = None
    
  def updateSelection(self):
    self.selectedItem  = self.items[self.selectedIndex]
    self.previewDelay  = 1000
    self.previewLoaded = False
    
    if self.setlistStyle == 2:
      self.pos = self.selectedIndex - self.itemsPerPage + self.followItemPos
    else:
      if len(self.items) < self.itemsPerPage:
        self.pos = 0
      else:
        self.pos = self.selectedIndex - self.itemsPerPage + self.followItemPos
        if self.pos + self.itemsPerPage > len(self.items):
          self.pos = len(self.items) - self.itemsPerPage
        elif self.pos < 0:
          self.pos = 0
    w, h = self.engine.view.geometry[2:4]
    self.xPos = self.pos*(self.itemSize[0]*w)
    self.yPos = self.pos*(self.itemSize[1]*h)
    
    self.loadItemLabel(self.selectedIndex)
    for i in range(1,1+self.labelDistance):
      if self.selectedIndex+i < len(self.items):
        self.loadItemLabel(self.selectedIndex+i)
      if self.selectedIndex-i >= 0:
        self.loadItemLabel(self.selectedIndex-i)
  
  def previewSong(self):
    self.previewLoaded = True
    if isinstance(self.selectedItem, Song.SongInfo):
      song = self.selectedItem.songName #TODO: SongDB
    else:
      return
    
    if self.careerMode and self.selectedItem.getLocked(): #TODO: SongDB
      if self.song:
        self.song.fadeout(1000)
      return
    if self.songLoader:
      try:
        self.songLoader.cancel()
      except:
        self.songLoader = None
    
    self.songLoader = self.engine.resource.load(self, None, lambda: Song.loadSong(self.engine, song, playbackOnly = True, library = self.library), synch = False, onLoad = self.songLoaded, onCancel = self.songCanceled)
  
  def songCanceled(self):
    self.songLoader = None
    if self.song:
      self.song.stop()
    self.song = None
  
  def songLoaded(self, song):
    self.songLoader = None

    if self.song:
      self.song.stop()
    
    song.crowdVolume = 0
    song.activeAudioTracks = [Song.GUITAR_TRACK, Song.RHYTHM_TRACK, Song.DRUM_TRACK]
    song.setAllTrackVolumes(1)
    song.play()
    self.song = song
  
  def quit(self):
    self.freeResources()
    self.engine.world.resetWorld()
  
  def keyPressed(self, key, unicode):
    self.lastTime = self.time
    c = self.engine.input.controls.getMapping(key)
    if key == pygame.K_SLASH and not self.searching:
      self.searching = True
    elif (key in range(30,123) or key == pygame.K_BACKSPACE) and not self.moreInfo:
      if self.searching:
        if key == pygame.K_BACKSPACE:
          self.searchText = self.searchText[:-1]
        else:
          self.searchText += unicode
        return
      else:
        if unicode:
          for i, item in enumerate(self.items):
            if isinstance(item, Song.SongInfo):
              if self.sortOrder in [0, 2, 5]:
                sort = item.name.lower()
              elif self.sortOrder == 1:
                sort = item.artist.lower()
              elif self.sortOrder == 3:
                sort = item.album.lower()
              elif self.sortOrder == 4:
                sort = item.genre.lower()
              elif self.sortOrder == 6:
                sort = str(item.diffSong)
              elif self.sortOrder == 7:
                sort = str(instrumentDiff[self.scorePart.id](item))
              elif self.sortOrder == 8:
                sort = item.icon.lower()
              else:
                sort = ""
              if sort.startswith(unicode):
                self.selectedIndex = i
                self.updateSelection()
                break
    elif (c in Player.menuNo and not c in Player.cancels) or key == pygame.K_ESCAPE:
      self.engine.data.cancelSound.play()
      if self.searching:
        self.searchText = ""
        self.searching = False
        return
      if self.moreInfo:
        self.moreInfo = False
        if self.moreInfoTime > 500:
          self.moreInfoTime = 500
        return
      if self.songLoader:
        self.songLoader.cancel()
      if self.song:
          self.song.fadeout(1000)
      if self.library != Song.DEFAULT_LIBRARY and not self.tut and (self.listingMode == 0 or self.careerMode):
        self.initialItem  = self.library
        self.library      = os.path.dirname(self.library)
        if self.library == os.path.join("..", self.engine.config.get("setlist", "base_library")):
          self.quit()
          return
        self.selectedItem = None
        self.loadLibrary()
      else:
        self.quit()
    elif (c in Player.menuYes and not c in Player.starts) or key == pygame.K_RETURN:
      if self.searching:
        self.searching = False
        text = self.searchText.lower()
        for i, item in enumerate(self.items):
          sort = item.name.lower()
          if sort.startswith(text):
            self.selectedIndex = i
            self.updateSelection()
            break
        self.searchText = ""
        return
      self.engine.data.acceptSound.play()
      if isinstance(self.selectedItem, Song.LibraryInfo):
        self.library = self.selectedItem.libraryName
        self.startingSelected = None
        Log.debug("New library selected: " + str(self.library) )
        self.loadLibrary()
      elif isinstance(self.selectedItem, Song.SongInfo) and not self.selectedItem.getLocked():
        if self.listingMode == 1 and not self.careerMode:
          self.library = self.selectedItem.libraryNam #TODO: SongDB
        self.libraryName = self.selectedItem.libraryNam
        self.songName = self.selectedItem.songName
        self.engine.config.set("setlist", "selected_library", self.libraryName)
        self.engine.config.set("setlist", "selected_song",    self.songName)
        if self.checkParts():
          if self.queueFormat == 0:
            self.engine.world.songQueue.addSong(self.songName, self.libraryName)
            self.startGame()
          elif self.queueFormat == 1:
            if self.engine.world.songQueue.addSongCheckReady(self.songName, self.libraryName):
              self.startGame()
    elif c in Player.menuYes and c in Player.starts:
      self.engine.data.acceptSound.play()
      if self.queueFormat == 0:
        self.engine.world.songQueue.addSong(self.songName, self.libraryName)
      self.startGame()
    elif c in Player.menuDown or key == pygame.K_DOWN:
      self.scrolling = 2
      self.scrollTime = self.scrollDelay
      self.scrollDown()
    elif c in Player.menuUp or key == pygame.K_UP:
      self.scrolling = 1
      self.scrollTime = self.scrollDelay
      self.scrollUp()
    elif c in Player.key3s or key == pygame.K_F3:
      self.previewDelay = 0
    elif c in Player.key4s or key == pygame.K_F12:
      if isinstance(self.selectedItem, Song.SongInfo):
        self.moreInfo = True
    elif c in Player.menuNo and c in Player.cancels:
      self.engine.view.pushLayer(self.menu)
  def scrollUp(self):
    if self.moreInfo:
      self.infoPage -= 1
      if self.infoPage < 0:
        self.infoPage = 2
      return
    self.selectedIndex -= 1
    if self.selectedIndex < 0:
      self.selectedIndex = len(self.items) - 1
    while isinstance(self.items[self.selectedIndex], Song.BlankSpaceInfo) or ((isinstance(self.items[self.selectedIndex], Song.TitleInfo) or isinstance(self.items[self.selectedIndex], Song.SortTitleInfo)) and not self.selectTiers):
      self.selectedIndex -= 1
      if self.selectedIndex < 0:
        self.selectedIndex = len(self.items) - 1
    self.updateSelection()
  
  def scrollDown(self):
    if self.moreInfo:
      self.infoPage += 1
      if self.infoPage > 2:
        self.infoPage = 0
      return
    self.selectedIndex += 1
    if self.selectedIndex >= len(self.items):
      self.selectedIndex = 0
    while isinstance(self.items[self.selectedIndex], Song.BlankSpaceInfo) or ((isinstance(self.items[self.selectedIndex], Song.TitleInfo) or isinstance(self.items[self.selectedIndex], Song.SortTitleInfo)) and not self.selectTiers):
      self.selectedIndex += 1
      if self.selectedIndex >= len(self.items):
        self.selectedIndex = 0
    self.updateSelection()
  
  def keyReleased(self, key):
    self.scrolling = 0
  
  def run(self, ticks):
    if self.cmdPlay:
      self.startGame()
      return
    if len(self.engine.world.songQueue) > 0 and self.queued:
      self.startGame(fromQueue = True)
      return
    if self.gameStarted or self.items == []:
      return
    
    Scene.run(self, ticks)
    if self.queued:
      self.queued = False
    if self.scrolling:
      self.scrollTime -= ticks
      if self.scrollTime < 0:
        self.scrollTime = self.scrollRate
        self.scroller[self.scrolling]()
    
    if self.mode == 0:
      if self.previewDelay > 0 and self.autoPreview:
        self.previewDelay -= ticks
        if self.previewDelay < 0:
          self.previewDelay = 0
      if not self.previewLoaded and self.previewDelay == 0:
        self.previewSong()
      
      d = self.cameraOffset - self.selectedOffset
      self.cameraOffset -= d * ticks / 192.0
      for i in range(len(self.itemRenderAngles)):
        if i == self.selectedIndex:
          self.itemRenderAngles[i] = min(90, self.itemRenderAngles[i] + ticks / 2.0)
        else:
          self.itemRenderAngles[i] = max(0,  self.itemRenderAngles[i] - ticks / 2.0)
      
      if self.moreInfo:
        self.moreInfoTime += ticks
      elif self.moreInfoTime > 0:
        self.moreInfoTime -= ticks
        if self.moreInfoTime < 0:
          self.moreInfoTime = 0
    
    self.engine.theme.setlist.run(ticks)
  
  def renderSetlist(self, visibility, topMost):
    w, h = self.engine.view.geometry[2:4]
    font = self.engine.data.font
    
    #render the background (including the header and footer)
    if self.setlistStyle == 1 and self.img_list_bg:
      self.engine.drawImage(self.img_list_bg, scale = (1.0, -1.0), coord = (w/2,h/2), stretched = 11)
    elif self.img_list_bg:
      self.engine.drawImage(self.img_list_bg, scale = (1.0, -1.0), coord = (w/2,h/2), stretched = 3)
    if self.img_list_head:
      o = 0
      if self.setlistStyle == 1:
        o = self.yPos
      self.engine.drawImage(self.img_list_head, scale = (1.0, -1.0), coord = (w/2,h+o), stretched = 11, fit = 1)
    if self.setlistStyle in [0, 2] and self.img_list_foot:
      self.engine.drawImage(self.img_list_foot, scale = (1.0, -1.0), coord = (w/2,0), stretched = 11, fit = 2)
    elif self.img_list_foot:
      maxPos = max(len(self.items) - self.itemsPerPage, 0)
      o = (-self.itemSize[1]*h*maxPos) + self.yPos
      self.engine.drawImage(self.img_list_foot, scale = (1.0, -1.0), coord = (w/2,o), stretched = 11, fit = 2)
    
    self.engine.theme.setlist.renderHeader(self)
    
    #render the artwork
    self.engine.theme.setlist.renderAlbumArt(self)
    
    #render the item list itself
    ns = 0   #the n value of the selectedItem
    if self.setlistStyle == 2:
      for n, i in enumerate(range(self.pos-self.itemsPerPage+self.followItemPos, self.pos+self.itemsPerPage)):
        if i == self.selectedIndex:
          ns = n
          continue
        i = i%len(self.items)
        self.engine.theme.setlist.renderUnselectedItem(self, i, n)
    else:
      for n, i in enumerate(range(self.pos, self.pos+self.itemsPerPage)):
        if i >= len(self.items):
          break
        if i == self.selectedIndex:
          ns = n
          continue
        if isinstance(self.items[i], Song.BlankSpaceInfo):
          continue
        self.engine.theme.setlist.renderUnselectedItem(self, i, n)
    self.engine.theme.setlist.renderSelectedItem(self, ns) #we render this last to allow overlapping effects.

    #render the additional information for the selected item
    self.engine.theme.setlist.renderSelectedInfo(self)
    
    #render the foreground stuff last
    self.engine.theme.setlist.renderForeground(self)
  
  def render(self, visibility, topMost):
    if self.gameStarted:
      return
    if self.items == []:
      return
    Scene.render(self, visibility, topMost)
    with self.engine.view.orthogonalProjection(normalize = True):
      self.engine.view.setViewport(1,0)
      w, h = self.engine.view.geometry[2:4]

      if self.img_background:
        self.engine.drawImage(self.img_background, scale = (1.0, -1.0), coord = (w/2,h/2), stretched = 3)

      if self.mode == 0:
        self.renderSetlist(visibility, topMost)
        if self.moreInfoTime > 0:
          self.engine.theme.setlist.renderMoreInfo(self)
        if self.miniLobbyTime > 0:
          self.engine.theme.setlist.renderMiniLobby(self)
      # I am unsure how I want to handle this for now. Perhaps as dialogs, perhaps in SCS.
      elif self.mode == 1:
        self.renderSpeedSelect(visibility, topMost)
      elif self.mode == 2:
        self.renderTimeSelect(visibility, topMost)

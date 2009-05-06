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

from Scene import SceneServer, SceneClient
from Song import SongQueue
import os
import Player
import Dialogs
import Song
import Config
import pygame
from Menu import Menu, Choice
from Language import _
from Input import KeyListener

import Log    #MFH

import Theme  #MFH

# save chosen song into config file
Config.define("game", "selected_library",  str, "")
Config.define("game", "selected_song",     str, "")




class SongChoosingScene:
  pass

class SongChoosingSceneServer(SongChoosingScene, SceneServer):
  pass

class SongChoosingSceneClient(SongChoosingScene, SceneClient):
  def createClient(self, libraryName = None, songName = None, songQueue = None):
    self.wizardStarted = False
    self.libraryName   = libraryName
    self.songName      = songName
    self.gamePlayers = self.engine.config.get("game", "players")
    self.playerList  = [self.player]
    if self.gamePlayers > 1:
      self.playerList.extend(self.multiplayers)

    for i, player in enumerate(self.playerList):
      player.controller  = self.engine.input.activeGameControls[i]
      player.controlType = self.engine.input.controls.type[player.controller]

    self.songSettings  = []
    self.gameStarted   = False
    if songQueue == None:
        self.songQueue     = SongQueue()
    else:
        self.songQueue     = songQueue
    self.dialog    = None
    self.mode      = 0

    self.tut = Config.get("game", "tut")

    self.songSelectSubmenuX = Theme.songSelectSubmenuX
    self.songSelectSubmenuY = Theme.songSelectSubmenuY
    
    self.subMenuPosTuple = None
    if self.songSelectSubmenuX != None and self.songSelectSubmenuY != None:
      self.subMenuPosTuple = (self.songSelectSubmenuX, self.songSelectSubmenuY)

    Log.debug("Song select submenu position tuple: " + str(self.subMenuPosTuple))    
    
  def addToQueue(self, value = None, selectedSong = None):
      players = Config.get("game", "selected_players")
      library = Config.get("game", "selected_library")
      if selectedSong:
          self.songQueue.addSong(selectedSong, library, players, 
                             self.player.difficulty,self.player2.difficulty,  self.player.part, self.player2.part)     
      else:
          self.songQueue.addSong(Config.get("game", "selected_song"), library, players, 
                             self.player.difficulty,self.player2.difficulty,  self.player.part, self.player2.part) 
          self.reset()
    
  def reset(self, value = ""):
    if not self.gameStarted:  
      self.dialog.close()
      self.session.world.deleteScene(self)
      self.freeResources()       
      self.session.world.createScene("SongChoosingScene", songName = None, songQueue = self.songQueue)   

  def changePart(self, num, value):
      self.playerList[num].part = self.songSettings[2].values[self.songSettings[2].valueIndex]
      
  def changeDiff(self, num, value):
      self.playerList[num].difficulty = self.songSettings[3].values[self.songSettings[3].valueIndex]
         
  def startGame(self, value = "", queueCounter = 0):
   if not self.gameStarted:
     self.gameStarted = True
     if not self.player.difficulty in self.info.difficulties:
        self.player.difficulty = self.info.difficulties[0]
     if not self.player.part in self.info.parts:
        self.player.part = self.info.parts[0]
     if not self.player2.difficulty in self.info.difficulties:
        self.player2.difficulty = self.info.difficulties[0]
     if not self.player2.part in self.info.parts:
        self.player2.part = self.info.parts[0]
     players = Config.get("game", "selected_players")
     if self.dialog:
       self.dialog.close()
     self.session.world.deleteScene(self)
     self.freeResources()       
     self.session.world.createScene("GuitarScene", songName = self.songName, Players = players, songQueue = self.songQueue, queueCounter = queueCounter)

  def startQueue(self):
     firstSong = self.songQueue.nextSong(0)
     Config.set("game", "selected_song", firstSong[0])
     Config.set("game", "selected_library", firstSong[1])
     Config.set("game", "selected_players", firstSong[2])
     self.player.difficulty = firstSong[3]
     self.player2.difficulty =  firstSong[4]
     self.player.part = firstSong[5]
     self.player2.part = firstSong[6]
     self.info = Song.loadSongInfo(self.engine, firstSong[0])
     self.songName = firstSong[0]
     self.startGame(queueCounter =  1)

  def freeResources(self):
    self.songs = None
    self.cassette = None
    self.folder = None
    self.label = None
    self.song = None
    self.background = None
    
  def run(self, ticks):
    SceneClient.run(self, ticks)
    players = 1

    if not self.wizardStarted:
      self.wizardStarted = True

      if self.engine.cmdPlay == 1:
        self.songName = Config.get("game", "selected_song")
        self.libraryName = Config.get("game", "selected_library")
        self.engine.cmdPlay = 2

      if not self.songName:
        while True:
          self.mode = 1
          self.libraryName, self.songName = \
            Dialogs.chooseSong(self.engine, \
                               selectedLibrary = Config.get("game", "selected_library"),
                               selectedSong    = Config.get("game", "selected_song"))

          if self.libraryName == None:
            newPath = Dialogs.chooseFile(self.engine, masks = ["*/songs"], prompt = _("Choose a new songs directory."), dirSelect = True)
            if newPath != None:
              Config.set("game", "base_library", os.path.dirname(newPath))
              Config.set("game", "selected_library", "songs")
              Config.set("game", "selected_song", "")
              self.engine.resource.refreshBaseLib()   #myfingershurt - to let user continue with new songpath without restart
            
          if not self.songName:
            self.session.world.finishGame()
            return

          if not self.tut:
            Config.set("game", "selected_library", self.libraryName)
            Config.set("game", "selected_song",    self.songName)
          self.mode = 2
          info = Song.loadSongInfo(self.engine, self.songName, library = self.libraryName)

          selected = False
          escape = False
          escaped = False
            
          #while True:    #this nesting is now useless
          #MFH - add "Practice" mode, which will activate a section selection menu before "part"
          #racer: main menu instead of second menu practice
          
          #self.player.practiceMode = Player.PracticeSet

            #MFH - parameters for newLocalGame:
            #players = -1 (party mode), 1, 2
            #mode1p = 0 (quickplay), 1 (practice), 2 (career)
            #mode2p = 0 (face-off), 1 (pro face-off)
              #Config.define("game",   "players",             int,   1)
              #Config.define("game","game_mode",           int,  0)
              #Config.define("game","multiplayer_mode",           int,  0)

          if Config.get("game","game_mode") == 1 and Config.get("game","players") == 1:    #practice mode
            self.player.practiceMode = True
          else:
            self.player.practiceMode = False
            
          slowDownDivisor = Config.get("audio",  "speed_factor")
           
          while True: #new nesting for Practice Mode - section / start time selection
            if self.player.practiceMode:
              values, options = Config.getOptions("audio", "speed_factor")
              if self.subMenuPosTuple:
                slowdown = Dialogs.chooseItem(self.engine, options, "%s \n %s" % (Dialogs.removeSongOrderPrefixFromName(info.name), _("Speed Select:")), pos = self.subMenuPosTuple)
              else:
                slowdown = Dialogs.chooseItem(self.engine, options, "%s \n %s" % (Dialogs.removeSongOrderPrefixFromName(info.name), _("Speed Select:")))
              for i in range(len(values)):
                if options[i] == slowdown:
                  Config.set("audio", "speed_factor", values[i])
                  slowDownDivisor = values[i]
                  break
              
            if self.player.practiceMode and slowDownDivisor == 1:
              #self.engine.resource.load(self, "song", lambda: Song.loadSong(self.engine, songName, library = self.libraryName, notesOnly = True, part = [player.part for player in self.playerList]), onLoad = self.songLoaded)

              
              #startTime = Dialogs.chooseItem(self.engine, info.sections, "%s \n %s" % (info.name, _("Start Section:")))
              
              sectionLabels = [sLabel for sLabel,sPos in info.sections]

              if self.subMenuPosTuple:
                startLabel = Dialogs.chooseItem(self.engine, sectionLabels, "%s \n %s" % (Dialogs.removeSongOrderPrefixFromName(info.name), _("Start Section:")), pos = self.subMenuPosTuple)
              else:
                startLabel = Dialogs.chooseItem(self.engine, sectionLabels, "%s \n %s" % (Dialogs.removeSongOrderPrefixFromName(info.name), _("Start Section:")))

              if startLabel:
                Log.debug("Practice start section selected: " + startLabel)
            else:
              startLabel = "Gig"
            if startLabel:
              self.player.practiceSection = startLabel
              
              #find start position in array:
              try:
                self.player.startPos = [sPos for sLabel,sPos in info.sections if sLabel == startLabel]
                Log.debug("Practice start position retrieved: " + str(self.player.startPos) )
              except:
                Log.error("Cannot retrieve start position!")
                self.player.startPos = [0]
                break
              
            else:
              
              #self.player.startPos = [0]
              
              break;
            #if not self.player.practiceMode:
              #selected = True  #this causes "gig" mode to start song with all defaults
              #escape = True  #this causes "gig" mode to exit out to the song selection
              #escaped = True  #this does nothing :(
              #break;

          
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
              escaped = True
              break
            if len(guitars) == 0 and self.engine.input.gameGuitars > 0:
              Dialogs.showMessage(self.engine, _("There are no guitar parts in this song. Change your controllers to play."))
              escaped = True
              break
            if len(vocals) == 0 and self.engine.input.gameMics > 0:
              Dialogs.showMessage(self.engine, _("There are no vocal parts in this song. Change your controllers to play."))
              escaped = True
              break
            
            for i, player in enumerate(self.playerList):
              
              while True: #new nesting for Practice Mode selection
                selectedPlayer = False
                choose = []
                if player.controlType == 2 or player.controlType == 3:
                  choose = drums
                elif player.controlType == 5:
                  choose = vocals
                else:
                  choose = guitars
                  
                if len(choose) > 1:

                  if self.subMenuPosTuple:
                    p = Dialogs.chooseItem(self.engine, choose, "%s \n %s" % (Dialogs.removeSongOrderPrefixFromName(info.name), _("%s Choose a part:") % player.name), selected = player.part, pos = self.subMenuPosTuple)
                  else:
                    p = Dialogs.chooseItem(self.engine, choose, "%s \n %s" % (Dialogs.removeSongOrderPrefixFromName(info.name), _("%s Choose a part:") % player.name), selected = player.part)

                else:
                  p = choose[0]
                if p:
                  player.part = p
                else:
                  if not player.practiceMode:
                    escaped = True
                  break;
                while True:
                  if len(info.difficulties) > 1:

                    if self.subMenuPosTuple:
                      d = Dialogs.chooseItem(self.engine, info.difficulties,
                                         "%s \n %s" % (Dialogs.removeSongOrderPrefixFromName(info.name), _("%s Choose a difficulty:") % player.name), selected = player.difficulty, pos = self.subMenuPosTuple)
                    else:
                      d = Dialogs.chooseItem(self.engine, info.difficulties,
                                         "%s \n %s" % (Dialogs.removeSongOrderPrefixFromName(info.name), _("%s Choose a difficulty:") % player.name), selected = player.difficulty)

                  else:
                    d = info.difficulties[0]
                  if d:
                    player.difficulty = d
                    selectedPlayer = True
                  else:
                    if len(choose) <= 1:
                      #escape = True
                      escaped = True
                    break
                  if selectedPlayer:
                    break
                if selectedPlayer or escaped:
                  break
            
              #if selected or escaped: #new nesting for Practice Mode selection
              if selected or escaped: #new nesting for Practice Mode selection
                break
            
            else:
              selected = True

            if selected or escaped: #new nesting for Practice Mode section selection
              break

          
          #useless practice mode nesting
          #if selected or escape:
          #  break

          if (not selected) or escape:
            continue
          break
      else:
        #evilynux - Fixes Practice Mode from the cmdline
        if Config.get("game","game_mode") == 1 and Config.get("game","players") == 1:
          self.player.practiceMode = True
        info = Song.loadSongInfo(self.engine, self.songName, library = self.libraryName)

      if self.engine.cmdPlay == 2:
        if len(info.difficulties) >= self.engine.cmdDiff:
          self.player.difficulty = info.difficulties[self.engine.cmdDiff]
        if len(info.parts) >= self.engine.cmdPart:
          self.player.part = info.parts[self.engine.cmdPart]
          
      # Make sure the difficulty we chose is available
      if not self.player.difficulty in info.difficulties:
        self.player.difficulty = info.difficulties[0]
      if not self.player.part in info.parts:
        self.player.part = info.parts[0]

      if not self.player.difficulty in info.difficulties:
        self.player.difficulty = info.difficulties[0]
      if not self.player.part in info.parts:
        self.player.part = info.parts[0]   
        
      if not self.engine.createdGuitarScene:
        #self.engine.createdGuitarScene = True
        self.session.world.deleteScene(self)
        self.session.world.createScene("GuitarScene", libraryName = self.libraryName, songName = self.songName, Players = players)

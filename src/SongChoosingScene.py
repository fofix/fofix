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

    #MFH - testing new traceback logging:
    #raise TypeError


    self.songSettings  = []
    self.gameStarted   = False
    if songQueue == None:
        self.songQueue     = SongQueue()
    else:
        self.songQueue     = songQueue
    self.dialog    = None
    
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

  def changePart1(self, value):
      self.player.part = self.songSettings[2].values[self.songSettings[2].valueIndex]
            
  def changePart2(self, value):   
      self.player2.part = self.songSettings[5].values[self.songSettings[5].valueIndex]
      
  def changeDiff1(self, value):
      self.player.difficulty = self.songSettings[3].values[self.songSettings[3].valueIndex]
      
  def changeDiff2(self, value):    
      self.player2.difficulty = self.songSettings[6].values[self.songSettings[6].valueIndex]

  def changeGameMode(self, value):
      mode = self.songSettings[4].values[self.songSettings[4].valueIndex]
      if mode == "Single Player":
          Config.set("game", "selected_players", 1)
      if mode == "2 Players Coop":
          Config.set("game", "selected_players", 2)
      if mode == "2 Players Versus":
          Config.set("game", "selected_players", 3)
      if mode == "Party Mode":
          Config.set("game", "selected_players", -1)
         
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

          Config.set("game", "selected_library", self.libraryName)
          Config.set("game", "selected_song",    self.songName)
          
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
              #Config.define("player0","mode_1p",           int,  0)
              #Config.define("player1","mode_2p",           int,  0)

          if Config.get("player0","mode_1p") == 1 and Config.get("game","players") == 1:    #practice mode
            self.player.practiceMode = True
          else:
            self.player.practiceMode = False
           
          while True: #new nesting for Practice Mode - section / start time selection
            if self.player.practiceMode:
              #self.engine.resource.load(self, "song", lambda: Song.loadSong(self.engine, songName, library = self.libraryName, notesOnly = True, part = [player.part for player in self.playerList]), onLoad = self.songLoaded)

              
              #startTime = Dialogs.chooseItem(self.engine, info.sections, "%s \n %s" % (info.name, _("Start Section:")))
              
              sectionLabels = [sLabel for sLabel,sPos in info.sections]
              startLabel = Dialogs.chooseItem(self.engine, sectionLabels, "%s \n %s" % (Dialogs.removeSongOrderPrefixFromName(info.name), _("Start Section:")))
              if startLabel:
                Log.debug("Practice start section selected: " + startLabel)
            else:
              startLabel = "Gig"
            if startLabel:
              self.player.practiceSection = startLabel
              
              #find start position in array:
              self.player.startPos = [sPos for sLabel,sPos in info.sections if sLabel == startLabel]
              Log.debug("Practice start position retrieved: " + str(self.player.startPos) )
              
            else:
              
              break;
            #if not self.player.practiceMode:
              #selected = True  #this causes "gig" mode to start song with all defaults
              #escape = True  #this causes "gig" mode to exit out to the song selection
              #escaped = True  #this does nothing :(
              #break;

          
          
          
            while True: #new nesting for Practice Mode selection
            
              if len(info.parts) > 1:
                p = Dialogs.chooseItem(self.engine, info.parts, "%s \n %s" % (Dialogs.removeSongOrderPrefixFromName(info.name), _("Player 1 Choose a part:")), selected = self.player.part)
              else:
                p = info.parts[0]
              if p:
                self.player.part = p
              else:
                if not self.player.practiceMode:
                  escaped = True
                break;
              while True:
                if len(info.difficulties) > 1:
                  d = Dialogs.chooseItem(self.engine, info.difficulties,
                                       "%s \n %s" % (Dialogs.removeSongOrderPrefixFromName(info.name), _("Player 1 Choose a difficulty:")), selected = self.player.difficulty)
                else:
                  d = info.difficulties[0]
                if d:
                  self.player.difficulty = d
                else:
                  if len(info.parts) <= 1:
                    #escape = True
                    escaped = True
                  break
                while True:
                  if self.engine.config.get("game", "players") > 1:               
                    #p = Dialogs.chooseItem(self.engine, info.parts + ["Party Mode"] + ["No Player 2"], "%s \n %s" % (info.name, _("Player 2 Choose a part:")), selected = self.player2.part)
                    p = Dialogs.chooseItem(self.engine, info.parts, "%s \n %s" % (Dialogs.removeSongOrderPrefixFromName(info.name), _("Player 2 Choose a part:")), selected = self.player2.part)
                    #if p and p == "No Player 2":
                    #  players = 1
                    #  selected = True
                    #  self.player2.part = p
                    #  break
                    #elif p and p == "Party Mode":
                    #  players = -1
                    #  selected = True
                    #  self.player2.part = p
                    #  break
                    #elif p and p != "No Player 2" and p != "Party Mode":
                    if p:
                      players = 2
                      self.player2.part = p
  
                    else:
                      if len(info.difficulties) <= 1:
                        escaped = True
                      if len(info.parts) <= 1:
                        escape = True
                      break
                    while True:                    
                      if len(info.difficulties) > 1:
                        d = Dialogs.chooseItem(self.engine, info.difficulties, "%s \n %s" % (Dialogs.removeSongOrderPrefixFromName(info.name), _("Player 2 Choose a difficulty:")), selected = self.player2.difficulty)
                      else:
                        d = info.difficulties[0]
                      if d:
                        self.player2.difficulty = d
                      else:
                        break
                      selected = True
                      break
                  else:
                    selected = True
                    break
                  if selected:
                    break
                if selected or escaped:
                  break
            
              #if selected or escaped: #new nesting for Practice Mode selection
              if selected or escaped: #new nesting for Practice Mode selection
                break

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
        if Config.get("player0","mode_1p") == 1 and Config.get("game","players") == 1:
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
        
      self.session.world.deleteScene(self)
      self.session.world.createScene("GuitarScene", libraryName = self.libraryName, songName = self.songName, Players = players)
